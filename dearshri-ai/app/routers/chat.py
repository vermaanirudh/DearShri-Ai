"""User-isolated chat and preference endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.ai_service import (
    classify_message,
    execute_command,
    generate_chat_response,
)
from ..sqlite_database import db_connection
from .auth import get_current_session


router = APIRouter(prefix="/chat", tags=["chat"])


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    mode: str = Field(default="companion", min_length=1, max_length=80)


class MessageResponse(BaseModel):
    user_message: dict[str, Any]
    assistant_message: dict[str, Any] | None
    kind: str
    command: dict[str, Any] | None = None


class HistoryResponse(BaseModel):
    messages: list[dict[str, Any]]


class PreferencesRequest(BaseModel):
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")
    notifications: bool | None = None


class PreferencesResponse(BaseModel):
    preferences: dict[str, Any]


def _preferences(connection: Any, user_id: int) -> dict[str, Any]:
    row = connection.execute(
        "SELECT theme, notifications FROM user_preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        connection.execute(
            """
            INSERT INTO user_preferences (user_id, theme, notifications)
            VALUES (?, 'system', 1)
            """,
            (user_id,),
        )
        return {"theme": "system", "notifications": True}
    return {
        "theme": row["theme"],
        "notifications": bool(row["notifications"]),
        "chat_paused": bool(row["chat_paused"]),
    }


@router.post("/message", response_model=MessageResponse)
def send_message(
    request: MessageRequest,
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> MessageResponse:
    """Store both sides of a response under the authenticated user only."""

    with db_connection() as connection:
        preferences = _preferences(connection, int(session["user_id"]))
        if request.mode not in {"friend", "tutor", "guardian", "admin"}:
            raise HTTPException(status_code=422, detail="Unknown companion mode.")
        if preferences["chat_paused"] and request.mode != "admin":
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Standard AI chat is paused while you complete Journey.",
            )
        previous_rows = connection.execute(
            """
            SELECT sender, text, timestamp FROM chat_messages
            WHERE user_id = ? AND mode = ?
            ORDER BY id ASC
            """,
            (session["user_id"], request.mode),
        ).fetchall()
        history = [dict(row) for row in previous_rows]
        timestamp = datetime.now(UTC).isoformat()
        connection.execute(
            """
            INSERT INTO chat_messages (user_id, mode, sender, text, timestamp)
            VALUES (?, ?, 'user', ?, ?)
            """,
            (session["user_id"], request.mode, request.content.strip(), timestamp),
        )
        kind = "admin_message" if request.mode == "admin" else classify_message(request.content)
        command_result: dict[str, Any] | None = None
        if request.mode == "admin":
            response_text = None
        elif kind == "command":
            command_result = execute_command(request.content, preferences)
            response_text = command_result["message"]
        else:
            response_text = generate_chat_response(request.content, history, request.mode)
        assistant_timestamp = datetime.now(UTC).isoformat() if response_text else None
        if response_text:
            connection.execute(
                """
                INSERT INTO chat_messages (user_id, mode, sender, text, timestamp)
                VALUES (?, ?, 'assistant', ?, ?)
                """,
                (session["user_id"], request.mode, response_text, assistant_timestamp),
            )
        connection.execute(
            """
            UPDATE user_preferences
            SET theme = ?, notifications = ?
            WHERE user_id = ?
            """,
            (
                preferences["theme"],
                int(preferences["notifications"]),
                session["user_id"],
            ),
        )
        return MessageResponse(
            user_message={
                "role": "user",
                "content": request.content.strip(),
                "created_at": timestamp,
            },
            assistant_message={
                "role": "assistant",
                "content": response_text,
                "created_at": assistant_timestamp,
            } if response_text else None,
            kind=kind,
            command=command_result,
        )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> HistoryResponse:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, sender AS role, text AS content, mode, timestamp AS created_at
            FROM chat_messages WHERE user_id = ?
            ORDER BY id ASC
            """,
            (session["user_id"],),
        ).fetchall()
        return HistoryResponse(messages=[dict(row) for row in rows])


@router.delete("/history")
def clear_history(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> dict[str, Any]:
    with db_connection() as connection:
        connection.execute(
            "DELETE FROM chat_messages WHERE user_id = ?",
            (session["user_id"],),
        )
    return {"cleared": True}


@router.patch("/preferences", response_model=PreferencesResponse)
def update_preferences(
    request: PreferencesRequest,
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> PreferencesResponse:
    with db_connection() as connection:
        preferences = _preferences(connection, int(session["user_id"]))
        if request.theme is not None:
            preferences["theme"] = request.theme
        if request.notifications is not None:
            preferences["notifications"] = request.notifications
        connection.execute(
            """
            UPDATE user_preferences
            SET theme = ?, notifications = ?
            WHERE user_id = ?
            """,
            (
                preferences["theme"],
                int(preferences["notifications"]),
                session["user_id"],
            ),
        )
        return PreferencesResponse(preferences=preferences)