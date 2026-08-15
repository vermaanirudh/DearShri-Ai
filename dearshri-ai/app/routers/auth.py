"""Multi-user phone/passcode authentication for DearShri AI."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..sqlite_database import (
    current_daily_code,
    create_session,
    db_connection,
    normalize_phone,
    session_user,
    today_key,
    user_profile,
    validate_login_code,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    mobile_number: str = Field(min_length=8, max_length=20)
    passcode: str = Field(min_length=1, max_length=10)


class ProfileResponse(BaseModel):
    id: int
    phone_number: str
    age: str | None = None
    class_name: str | None = None
    school: str | None = None
    location_data: dict[str, Any] = {}
    gender: str | None = None
    languages: list[str] = []
    role: str


class LoginResponse(BaseModel):
    authenticated: bool
    session_token: str
    expires_at: str | None
    persistent: bool
    role: str
    profile: ProfileResponse
    message: str


class AdminAccessRequest(BaseModel):
    """Kept as a compatibility model; admin access is now session-based."""

    admin_secret: str = Field(min_length=1, max_length=256)


class AdminAccessResponse(BaseModel):
    authorized: bool
    message: str


def _profile_response(row: Any) -> ProfileResponse:
    try:
        location = json.loads(row["location_data"] or "{}")
    except (TypeError, json.JSONDecodeError):
        location = {}
    try:
        languages = json.loads(row["languages"] or "[]")
    except (TypeError, json.JSONDecodeError):
        languages = []
    return ProfileResponse(
        id=row["id"],
        phone_number=row["phone_number"],
        age=row["age"],
        class_name=row["class"],
        school=row["school"],
        location_data=location if isinstance(location, dict) else {},
        gender=row["gender"],
        languages=languages if isinstance(languages, list) else [],
        role=row["role"],
    )


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest) -> LoginResponse:
    """Validate a phone-specific code and persist a scoped session."""

    try:
        with db_connection() as connection:
            user = validate_login_code(
                connection,
                normalize_phone(credentials.mobile_number),
                credentials.passcode,
            )
            session_token, expires_at = create_session(connection, user)
            profile = user_profile(connection, user["id"])
            if not profile:
                raise HTTPException(status_code=500, detail="Profile could not be loaded.")
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    return LoginResponse(
        authenticated=True,
        session_token=session_token,
        expires_at=expires_at,
        persistent=expires_at is None,
        role=user["role"],
        profile=_profile_response(profile),
        message="You are signed in to DearShri AI.",
    )


def get_current_session(
    session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
) -> dict[str, Any]:
    """Require a live persisted session and return its user scope."""

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Session-Token is required.",
        )
    with db_connection() as connection:
        session = session_user(connection, session_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The session is invalid or expired.",
            )
        return dict(session)


def require_admin_session(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> dict[str, Any]:
    """Restrict admin routes to the authenticated admin account only."""

    if session.get("role") != "admin" or session.get("phone_number") != "9792836590":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account authorization is required.",
        )
    return session


def verify_admin_secret(
    session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> dict[str, Any]:
    """Compatibility dependency now backed by the authenticated admin session."""

    return session


@router.get("/me", response_model=ProfileResponse)
def current_profile(
    session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> ProfileResponse:
    with db_connection() as connection:
        profile = user_profile(connection, int(session["user_id"]))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        return _profile_response(profile)


@router.post("/logout", response_model=AdminAccessResponse)
def logout(
    session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
) -> AdminAccessResponse:
    if not session_token:
        return AdminAccessResponse(
            authorized=False,
            message="No session was supplied.",
        )
    with db_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token = ?",
            (session_token,),
        )
    return AdminAccessResponse(authorized=True, message="You are signed out.")


@router.get("/admin/daily-code")
def admin_daily_code(
    _session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> dict[str, str]:
    """Expose the current normal-user code only to the admin session."""

    with db_connection() as connection:
        return {"date": today_key(), "code": current_daily_code(connection)}


@router.post("/verify-admin", response_model=AdminAccessResponse)
def verify_admin_access(
    session: Annotated[dict[str, Any], Depends(require_admin_session)],
) -> AdminAccessResponse:
    """Compatibility endpoint that confirms the current admin session."""

    return AdminAccessResponse(
        authorized=True,
        message=f"Admin access verified for {session['phone_number']}.",
    )