"""Admin dashboard, journey-set authoring, and user reporting routes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..sqlite_database import current_daily_code, db_connection, today_key
from .auth import require_admin_session


router = APIRouter(prefix="/admin", tags=["admin"])


class JourneyQuestionInput(BaseModel):
    story_id: str = Field(min_length=1, max_length=120)
    question_num: int = Field(ge=1)
    prompt_text: str = Field(min_length=1, max_length=10_000)


class JourneySetDraftRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    version: int | None = Field(default=None, ge=1)
    questions: list[JourneyQuestionInput] = Field(min_length=1, max_length=1000)


class JourneySetPublishResponse(BaseModel):
    published: bool
    journey_set_id: int
    version: int
    title: str


@router.get("/dashboard")
def dashboard(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> dict[str, Any]:
    with db_connection() as connection:
        users = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        responses = connection.execute(
            "SELECT COUNT(*) AS count FROM journey_responses",
        ).fetchone()["count"]
        published = connection.execute(
            """
            SELECT id, version, title, status, created_at
            FROM journey_sets WHERE status = 'published'
            ORDER BY version DESC LIMIT 1
            """,
        ).fetchone()
        return {
            "user_count": users,
            "journey_response_count": responses,
            "current_daily_code": current_daily_code(connection),
            "daily_code_date": today_key(),
            "published_journey": dict(published) if published else None,
        }


@router.get("/users")
def users(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> list[dict[str, Any]]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT u.id, u.phone_number, u.role, u.created_at,
                   p.age, p.class, p.school, p.gender, p.languages,
                   p.location_data, COUNT(r.id) AS journey_answers,
                   MAX(r.timestamp) AS last_response_at
            FROM users u
            LEFT JOIN user_profiles p ON p.user_id = u.id
            LEFT JOIN journey_responses r ON r.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at ASC
            """,
        ).fetchall()
        return [_decode_profile(dict(row)) for row in rows]


@router.get("/journey-responses")
def journey_responses(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> list[dict[str, Any]]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT r.id, u.phone_number, r.user_id, r.journey_set_id,
                   js.version, js.title, r.story_id, r.question_id,
                   jq.question_num, jq.prompt_text, r.answer_text,
                   r.timestamp
            FROM journey_responses r
            JOIN users u ON u.id = r.user_id
            JOIN journey_sets js ON js.id = r.journey_set_id
            JOIN journey_questions jq ON jq.id = r.question_id
            ORDER BY u.phone_number ASC, r.timestamp ASC, r.id ASC
            """,
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/journey-sets")
def journey_sets(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> list[dict[str, Any]]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT js.id, js.version, js.title, js.status, js.created_at,
                   COUNT(jq.id) AS question_count
            FROM journey_sets js
            LEFT JOIN journey_questions jq ON jq.journey_set_id = js.id
            GROUP BY js.id
            ORDER BY js.version DESC
            """,
        ).fetchall()
        return [dict(row) for row in rows]


@router.post("/journey-sets/draft")
def draft_journey_set(
    request: JourneySetDraftRequest,
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> dict[str, Any]:
    question_numbers = [question.question_num for question in request.questions]
    if len(question_numbers) != len(set(question_numbers)):
        raise HTTPException(status_code=422, detail="Question numbers must be unique.")
    with db_connection() as connection:
        max_version = connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM journey_sets",
        ).fetchone()["version"]
        version = request.version or max_version + 1
        if connection.execute(
            "SELECT 1 FROM journey_sets WHERE version = ?",
            (version,),
        ).fetchone():
            raise HTTPException(status_code=409, detail="Journey version already exists.")
        created_at = datetime.now(UTC).isoformat()
        cursor = connection.execute(
            """
            INSERT INTO journey_sets (version, title, status, created_at)
            VALUES (?, ?, 'draft', ?)
            """,
            (version, request.title.strip(), created_at),
        )
        journey_set_id = cursor.lastrowid
        connection.executemany(
            """
            INSERT INTO journey_questions
                (journey_set_id, story_id, question_num, prompt_text)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    journey_set_id,
                    question.story_id,
                    question.question_num,
                    question.prompt_text.strip(),
                )
                for question in request.questions
            ],
        )
        return {
            "created": True,
            "journey_set_id": journey_set_id,
            "version": version,
            "status": "draft",
        }


@router.post(
    "/journey-sets/{journey_set_id}/publish",
    response_model=JourneySetPublishResponse,
)
def publish_journey_set(
    journey_set_id: int,
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> JourneySetPublishResponse:
    with db_connection() as connection:
        journey_set = connection.execute(
            "SELECT * FROM journey_sets WHERE id = ?",
            (journey_set_id,),
        ).fetchone()
        if not journey_set:
            raise HTTPException(status_code=404, detail="Journey set not found.")
        question_count = connection.execute(
            "SELECT COUNT(*) AS count FROM journey_questions WHERE journey_set_id = ?",
            (journey_set_id,),
        ).fetchone()["count"]
        if question_count == 0:
            raise HTTPException(status_code=409, detail="Cannot publish an empty journey.")
        connection.execute(
            """
            UPDATE journey_sets
            SET status = CASE WHEN id = ? THEN 'published' ELSE 'archived' END
            WHERE status = 'published' OR id = ?
            """,
            (journey_set_id, journey_set_id),
        )
        return JourneySetPublishResponse(
            published=True,
            journey_set_id=journey_set["id"],
            version=journey_set["version"],
            title=journey_set["title"],
        )


def _decode_profile(row: dict[str, Any]) -> dict[str, Any]:
    for key in ("languages", "location_data"):
        value = row.get(key)
        if isinstance(value, str):
            try:
                row[key] = json.loads(value)
            except json.JSONDecodeError:
                row[key] = [] if key == "languages" else {}
    return row