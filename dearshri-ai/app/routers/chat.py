"""User-scoped chat and preferences endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..database import get_db, get_user_data, save_db
from ..services.ai_service import (
    classify_message,
    execute_command,
    generate_chat_response,
)


router = APIRouter(prefix="/chat", tags=["chat"])


class MessageRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=20_000)


class MessageResponse(BaseModel):
    user_message: dict[str, Any]
    assistant_message: dict[str, Any]
    kind: str
    command: dict[str, Any] | None = None


class HistoryResponse(BaseModel):
    messages: list[dict[str, Any]]


class PreferencesRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")
    notifications: bool | None = None


class PreferencesResponse(BaseModel):
    preferences: dict[str, Any]


def require_user_header(
    user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> str:
    """Require the Clerk user ID header on server requests."""

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A signed-in user ID is required.",
        )
    return user_id


@router.post("/message", response_model=MessageResponse)
def send_message(
    request: MessageRequest,
    header_user_id: Annotated[str, Header(alias="X-User-ID")],
) -> MessageResponse:
    """Store a user message and return a grounded assistant response."""

    if request.user_id != header_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User scope does not match the authenticated user.",
        )

    db = get_db()
    user_data = get_user_data(db, request.user_id)
    history = user_data["chat_history"]
    timestamp = datetime.now(UTC).isoformat()
    user_message = {
        "id": f"user-{len(history) + 1}",
        "role": "user",
        "content": request.content.strip(),
        "created_at": timestamp,
    }
    history.append(user_message)

    kind = classify_message(request.content)
    command_result: dict[str, Any] | None = None
    if kind == "command":
        command_result = execute_command(
            request.content,
            user_data["preferences"],
        )
        response_text = command_result["message"]
    else:
        response_text = generate_chat_response(request.content, history)

    assistant_message = {
        "id": f"assistant-{len(history) + 1}",
        "role": "assistant",
        "content": response_text,
        "created_at": datetime.now(UTC).isoformat(),
    }
    history.append(assistant_message)
    save_db(db)

    return MessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        kind=kind,
        command=command_result,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    user_id: Annotated[str, Header(alias="X-User-ID")] = "",
) -> HistoryResponse:
    """Return only the signed-in user's chat history."""

    if not user_id:
        raise HTTPException(status_code=401, detail="A signed-in user ID is required.")
    db = get_db()
    return HistoryResponse(messages=get_user_data(db, user_id)["chat_history"])


@router.delete("/history")
def clear_history(
    user_id: Annotated[str, Header(alias="X-User-ID")] = "",
) -> dict[str, Any]:
    """Clear only the signed-in user's chat history."""

    if not user_id:
        raise HTTPException(status_code=401, detail="A signed-in user ID is required.")
    db = get_db()
    get_user_data(db, user_id)["chat_history"] = []
    save_db(db)
    return {"cleared": True}


@router.patch("/preferences", response_model=PreferencesResponse)
def update_preferences(
    request: PreferencesRequest,
    header_user_id: Annotated[str, Header(alias="X-User-ID")],
) -> PreferencesResponse:
    """Update only the signed-in user's preferences."""

    if request.user_id != header_user_id:
        raise HTTPException(status_code=403, detail="User scope mismatch.")
    db = get_db()
    preferences = get_user_data(db, request.user_id)["preferences"]
    if request.theme is not None:
        preferences["theme"] = request.theme
    if request.notifications is not None:
        preferences["notifications"] = request.notifications
    save_db(db)
    return PreferencesResponse(preferences=preferences)