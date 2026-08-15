"""Authenticated system notices and per-user dismissal."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..sqlite_database import db_connection
from .auth import get_current_session, require_admin_session


router = APIRouter(prefix="/notices", tags=["notices"])


class NoticeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10_000)


class NoticeResponse(BaseModel):
    id: int
    title: str
    body: str
    created_at: str


@router.post("", response_model=NoticeResponse)
def create_notice(
    request: NoticeRequest,
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> NoticeResponse:
    with db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO system_notices (title, body, created_at)
            VALUES (?, ?, ?)
            """,
            (request.title.strip(), request.body.strip(), datetime.now(UTC).isoformat()),
        )
        notice = connection.execute(
            "SELECT * FROM system_notices WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return NoticeResponse(**dict(notice))


@router.get("/for-user", response_model=list[NoticeResponse])
def notices_for_user(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> list[NoticeResponse]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT n.*
            FROM system_notices n
            WHERE NOT EXISTS (
                SELECT 1 FROM notice_dismissals d
                WHERE d.notice_id = n.id AND d.user_id = ?
            )
            ORDER BY n.id DESC
            """,
            (session["user_id"],),
        ).fetchall()
        return [NoticeResponse(**dict(row)) for row in rows]


@router.post("/{notice_id}/dismiss")
def dismiss_notice(
    notice_id: int,
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> dict[str, Any]:
    with db_connection() as connection:
        notice = connection.execute(
            "SELECT id FROM system_notices WHERE id = ?",
            (notice_id,),
        ).fetchone()
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
        connection.execute(
            """
            INSERT OR IGNORE INTO notice_dismissals
                (notice_id, user_id, dismissed_at)
            VALUES (?, ?, ?)
            """,
            (notice_id, session["user_id"], datetime.now(UTC).isoformat()),
        )
    return {"dismissed": True, "notice_id": notice_id}