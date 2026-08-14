"""Admin notices and per-user notice dismissal endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..config import ADMIN_SECRET
from ..database import get_db, get_user_data, save_db


router = APIRouter(prefix="/notices", tags=["notices"])


class NoticeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10_000)


class NoticeResponse(BaseModel):
    id: str
    title: str
    body: str
    created_at: str


def require_admin(
    admin_secret: Annotated[str | None, Header(alias="X-Admin-Secret")] = None,
) -> None:
    if not admin_secret or admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization is required.",
        )


@router.post(
    "",
    response_model=NoticeResponse,
    dependencies=[Depends(require_admin)],
)
def create_notice(request: NoticeRequest) -> NoticeResponse:
    """Broadcast a notice without interrupting active user sessions."""

    db = get_db()
    notice = {
        "id": uuid4().hex,
        "title": request.title.strip(),
        "body": request.body.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    db.setdefault("notices", []).append(notice)
    save_db(db)
    return NoticeResponse(**notice)


@router.get("/for-user", response_model=list[NoticeResponse])
def notices_for_user(
    user_id: Annotated[str, Header(alias="X-User-ID")] = "",
) -> list[NoticeResponse]:
    """Return notices not dismissed by this user."""

    if not user_id:
        raise HTTPException(status_code=401, detail="A signed-in user ID is required.")
    db = get_db()
    user_data = get_user_data(db, user_id)
    dismissed = set(user_data.setdefault("dismissed_notice_ids", []))
    return [
        NoticeResponse(**notice)
        for notice in db.get("notices", [])
        if notice.get("id") not in dismissed
    ]


@router.post("/{notice_id}/dismiss")
def dismiss_notice(
    notice_id: str,
    user_id: Annotated[str, Header(alias="X-User-ID")] = "",
) -> dict[str, Any]:
    """Dismiss a notice for one user without affecting anyone else."""

    if not user_id:
        raise HTTPException(status_code=401, detail="A signed-in user ID is required.")
    db = get_db()
    notice_exists = any(
        notice.get("id") == notice_id for notice in db.get("notices", [])
    )
    if not notice_exists:
        raise HTTPException(status_code=404, detail="Notice not found.")
    dismissed = get_user_data(db, user_id).setdefault("dismissed_notice_ids", [])
    if notice_id not in dismissed:
        dismissed.append(notice_id)
    save_db(db)
    return {"dismissed": True, "notice_id": notice_id}