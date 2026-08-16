"""User-isolated journey progress and authenticated admin response access."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.ai_service import generate_ai_insight
from ..services.journey_analysis import analyze_completed_journey
from ..sqlite_database import db_connection
from .auth import get_current_session, require_admin_session


router = APIRouter(prefix="/journey", tags=["journey"])


class JourneyStatusResponse(BaseModel):
    visible: bool
    locked: bool
    current_q: int
    completed: bool
    answered_count: int
    total_questions: int
    journey_set_id: int | None = None
    journey_set_version: int | None = None
    chat_paused: bool = False
    stories: list[dict[str, Any]] = []


class JourneyStoryProgress(BaseModel):
    story_id: str
    story_num: int
    emoji: str
    title: str
    answered_count: int
    total_questions: int
    unlocked: bool
    completed: bool


class AnswerSubmission(BaseModel):
    question_number: int = Field(ge=1)
    answer: str = Field(min_length=1, max_length=10_000)
    story_id: str | None = Field(default=None, max_length=120)
    question_id: int | None = Field(default=None, ge=1)


class AnswerSubmissionResponse(BaseModel):
    saved: bool
    question_number: int
    next_question: int | None
    ai_insight: str
    memories_added: list[str]
    journey_completed: bool
    journey_locked: bool
    traits_analyzed: list[dict[str, Any]] = []


class AdminInboxResponse(BaseModel):
    items: list[dict[str, Any]]


def _published_set(connection: Any) -> Any:
    return connection.execute(
        """
        SELECT * FROM journey_sets
        WHERE status = 'published'
        ORDER BY version DESC
        LIMIT 1
        """,
    ).fetchone()


def _story_progress(connection: Any, user_id: int, journey_set_id: int) -> list[dict[str, Any]]:
    stories = connection.execute(
        """
        SELECT js.story_id, js.story_num, js.emoji, js.title,
               COUNT(jq.id) AS total_questions,
               COUNT(r.id) AS answered_count
        FROM journey_stories js
        JOIN journey_questions jq
          ON jq.journey_set_id = js.journey_set_id
         AND jq.story_id = js.story_id
        LEFT JOIN journey_responses r
          ON r.question_id = jq.id AND r.user_id = ?
        WHERE js.journey_set_id = ?
        GROUP BY js.id
        ORDER BY js.story_num ASC
        """,
        (user_id, journey_set_id),
    ).fetchall()
    progress: list[dict[str, Any]] = []
    previous_completed = True
    for story in stories:
        completed = story["answered_count"] >= story["total_questions"]
        progress.append(
            {
                **dict(story),
                "unlocked": previous_completed,
                "completed": completed,
            },
        )
        previous_completed = completed
    return progress


@router.get("/status", response_model=JourneyStatusResponse)
def journey_status(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> JourneyStatusResponse:
    with db_connection() as connection:
        journey_set = _published_set(connection)
        if not journey_set:
            return JourneyStatusResponse(
                visible=False,
                locked=True,
                current_q=1,
                completed=False,
                answered_count=0,
                total_questions=0,
            )
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM journey_questions WHERE journey_set_id = ?",
            (journey_set["id"],),
        ).fetchone()["count"]
        answered = connection.execute(
            """
            SELECT COUNT(*) AS count FROM journey_responses
            WHERE user_id = ? AND journey_set_id = ?
            """,
            (session["user_id"], journey_set["id"]),
        ).fetchone()["count"]
        completed = answered >= total
        preferences = connection.execute(
            "SELECT chat_paused FROM user_preferences WHERE user_id = ?",
            (session["user_id"],),
        ).fetchone()
        return JourneyStatusResponse(
            visible=not completed,
            locked=completed,
            current_q=min(answered + 1, total or 1),
            completed=completed,
            answered_count=answered,
            total_questions=total,
            journey_set_id=journey_set["id"],
            journey_set_version=journey_set["version"],
            chat_paused=bool(preferences["chat_paused"]) if preferences else False,
            stories=_story_progress(connection, int(session["user_id"]), journey_set["id"]),
        )


@router.post("/start")
def start_journey(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> dict[str, Any]:
    """Pause standard AI chat while the user is actively completing Journey."""

    with db_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (user_id, theme, notifications, chat_paused)
            VALUES (?, 'system', 1, 1)
            ON CONFLICT(user_id) DO UPDATE SET chat_paused = 1
            """,
            (session["user_id"],),
        )
    return {"started": True, "chat_paused": True}


@router.post("/answer", response_model=AnswerSubmissionResponse)
def submit_answer(
    submission: AnswerSubmission,
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> AnswerSubmissionResponse:
    with db_connection() as connection:
        journey_set = _published_set(connection)
        if not journey_set:
            raise HTTPException(status_code=503, detail="No published journey is available.")
        answered = connection.execute(
            """
            SELECT COUNT(*) AS count FROM journey_responses
            WHERE user_id = ? AND journey_set_id = ?
            """,
            (session["user_id"], journey_set["id"]),
        ).fetchone()["count"]
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM journey_questions WHERE journey_set_id = ?",
            (journey_set["id"],),
        ).fetchone()["count"]
        current_question = answered + 1
        if current_question > total:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The journey is complete and locked.",
            )
        if submission.question_number != current_question:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Please answer question {current_question} next.",
            )
        question = connection.execute(
            """
            SELECT * FROM journey_questions
            WHERE journey_set_id = ? AND question_num = ?
            """,
            (journey_set["id"], submission.question_number),
        ).fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Journey question not found.")
        if submission.story_id and submission.story_id != question["story_id"]:
            raise HTTPException(status_code=409, detail="Journey story does not match the question.")
        if submission.question_id and submission.question_id != question["id"]:
            raise HTTPException(status_code=409, detail="Journey question ID does not match.")

        existing_traits = [
            dict(row)
            for row in connection.execute(
                "SELECT trait_key AS text FROM personality_traits WHERE user_id = ?",
                (session["user_id"],),
            ).fetchall()
        ]
        insight = generate_ai_insight(
            question_number=submission.question_number,
            answer=submission.answer,
            existing_memories=existing_traits,
        )
        timestamp = datetime.now(UTC).isoformat()
        connection.execute(
            """
            INSERT INTO journey_responses
                (user_id, journey_set_id, story_id, question_id, answer_text, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                journey_set["id"],
                question["story_id"],
                question["id"],
                submission.answer.strip(),
                timestamp,
            ),
        )
        connection.execute(
            """
            INSERT INTO user_preferences (user_id, theme, notifications, chat_paused)
            VALUES (?, 'system', 1, 1)
            ON CONFLICT(user_id) DO UPDATE SET chat_paused = 1
            """,
            (session["user_id"],),
        )
        memories_added: list[str] = []
        for memory in insight["memories"]:
            connection.execute(
                """
                INSERT INTO personality_traits
                    (user_id, trait_key, trait_value, confidence, source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    f"journey_q_{submission.question_number}",
                    memory,
                    0.55,
                    "journey",
                    timestamp,
                ),
            )
            memories_added.append(memory)

        completed = submission.question_number >= total
        traits_analyzed: list[dict[str, Any]] = []
        if completed:
            traits_analyzed = analyze_completed_journey(
                connection,
                int(session["user_id"]),
                int(journey_set["id"]),
                int(journey_set["version"]),
            )
            connection.execute(
                "UPDATE user_preferences SET chat_paused = 0 WHERE user_id = ?",
                (session["user_id"],),
            )
        return AnswerSubmissionResponse(
            saved=True,
            question_number=submission.question_number,
            next_question=None if completed else submission.question_number + 1,
            ai_insight=insight["insight"],
            memories_added=memories_added,
            journey_completed=completed,
            journey_locked=completed,
            traits_analyzed=traits_analyzed,
        )


@router.get(
    "/admin-inbox",
    response_model=AdminInboxResponse,
)
def admin_inbox(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> AdminInboxResponse:
    """Return every user's responses in chronological order."""

    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT r.id, r.timestamp AS created_at, r.answer_text AS answer,
                   r.question_id, r.story_id, r.user_id,
                   u.phone_number, js.id AS journey_set_id,
                   js.version AS journey_set_version, js.title,
                   jq.question_num
            FROM journey_responses r
            JOIN users u ON u.id = r.user_id
            JOIN journey_sets js ON js.id = r.journey_set_id
            JOIN journey_questions jq ON jq.id = r.question_id
            ORDER BY r.timestamp ASC, r.id ASC
            """,
        ).fetchall()
        return AdminInboxResponse(
            items=[
                {
                    **dict(row),
                    "completion_timestamp": _completion_timestamp(
                        connection,
                        row["user_id"],
                        row["journey_set_id"],
                    ),
                }
                for row in rows
            ],
        )


def _completion_timestamp(connection: Any, user_id: int, journey_set_id: int) -> str | None:
    total = connection.execute(
        "SELECT COUNT(*) AS count FROM journey_questions WHERE journey_set_id = ?",
        (journey_set_id,),
    ).fetchone()["count"]
    if not total:
        return None
    row = connection.execute(
        """
        SELECT MAX(timestamp) AS completed_at
        FROM journey_responses
        WHERE user_id = ? AND journey_set_id = ?
        HAVING COUNT(*) >= ?
        """,
        (user_id, journey_set_id, total),
    ).fetchone()
    return row["completed_at"] if row else None