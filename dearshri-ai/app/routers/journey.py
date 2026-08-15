"""User-isolated journey progress and authenticated admin response access."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.ai_service import generate_ai_insight
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


class AnswerSubmission(BaseModel):
    question_number: int = Field(ge=1)
    answer: str = Field(min_length=1, max_length=10_000)


class AnswerSubmissionResponse(BaseModel):
    saved: bool
    question_number: int
    next_question: int | None
    ai_insight: str
    memories_added: list[str]
    journey_completed: bool
    journey_locked: bool


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
        return JourneyStatusResponse(
            visible=not completed,
            locked=completed,
            current_q=min(answered + 1, total or 1),
            completed=completed,
            answered_count=answered,
            total_questions=total,
            journey_set_id=journey_set["id"],
            journey_set_version=journey_set["version"],
        )


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
        return AnswerSubmissionResponse(
            saved=True,
            question_number=submission.question_number,
            next_question=None if completed else submission.question_number + 1,
            ai_insight=insight["insight"],
            memories_added=memories_added,
            journey_completed=completed,
            journey_locked=completed,
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