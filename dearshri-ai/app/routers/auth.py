"""Authentication routes for the single-user DearShri-AI journey."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..config import ADMIN_SECRET, ALLOWED_MOBILE_NUMBER
from ..database import get_db, save_db


router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Credentials accepted by the one-time passcode login."""

    mobile_number: str = Field(min_length=8, max_length=20)
    passcode: str = Field(min_length=1, max_length=64)


class LoginResponse(BaseModel):
    """Session details returned after a successful login."""

    authenticated: bool
    session_token: str
    message: str


class AdminAccessRequest(BaseModel):
    """Request model for validating the configured admin secret."""

    admin_secret: str = Field(min_length=1, max_length=256)


class AdminAccessResponse(BaseModel):
    """Response model for admin secret validation."""

    authorized: bool
    message: str


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest) -> LoginResponse:
    """Consume the active passcode and create a single user session."""

    if not secrets.compare_digest(credentials.mobile_number, ALLOWED_MOBILE_NUMBER):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This mobile number is not authorized.",
        )

    db = get_db()
    active_passcode = db.get("active_passcode")
    if (
        not isinstance(active_passcode, str)
        or not secrets.compare_digest(credentials.passcode, active_passcode)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The passcode is invalid or has already been used.",
        )

    session_token = secrets.token_urlsafe(32)
    db["active_passcode"] = None
    db["user_session"] = {
        "token": session_token,
        "mobile_number": credentials.mobile_number,
        "authenticated_at": datetime.now(UTC).isoformat(),
    }
    save_db(db)

    return LoginResponse(
        authenticated=True,
        session_token=session_token,
        message="You are signed in to DearShri AI.",
    )


def get_current_session(
    session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
) -> dict[str, Any]:
    """Require the session created by the one-time passcode login."""

    db = get_db()
    session = db.get("user_session")
    stored_token = session.get("token") if isinstance(session, dict) else None

    if (
        not session_token
        or not isinstance(stored_token, str)
        or not secrets.compare_digest(session_token, stored_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Session-Token is required.",
        )

    return session


def verify_admin_secret(
    admin_secret: Annotated[str | None, Header(alias="X-Admin-Secret")] = None,
) -> None:
    """Protect admin-only read access with the configured admin secret."""

    if (
        not admin_secret
        or not secrets.compare_digest(admin_secret, ADMIN_SECRET)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization is required.",
        )


@router.post("/verify-admin", response_model=AdminAccessResponse)
def verify_admin_access(request: AdminAccessRequest) -> AdminAccessResponse:
    """Validate the admin secret without exposing it in the response."""

    if not secrets.compare_digest(request.admin_secret, ADMIN_SECRET):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization is required.",
        )

    return AdminAccessResponse(
        authorized=True,
        message="Admin access verified.",
    )