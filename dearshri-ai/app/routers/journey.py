"""Routes for the sequential 250-question DearShri-AI journey."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import TOTAL_JOURNEY_QUESTIONS
from ..database import get_db, save_db
from ..services.ai_service import generate_ai_insight
from .auth import get_current_session, verify_admin_secret


router = APIRouter(prefix="/journey", tags=["journey"])


class JourneyStatusResponse(BaseModel):
    """Current visibility and progress state of the journey."""

    visible: bool
    locked: bool
    current_q: int
    completed: bool
    answered_count: int
    total_questions: int


class AnswerSubmission(BaseModel):
    """A single sequential answer submitted by the signed-in user."""

    question_number: int = Field(ge=1, le=TOTAL_JOURNEY_QUESTIONS)
    answer: str = Field(min_length=1, max_length=10_000)


class AnswerSubmissionResponse(BaseModel):
    """Result of processing one journey answer."""

    saved: bool
    question_number: int
    next_question: int | None
    ai_insight: str
    memories_added: list[str]
    journey_completed: bool
    journey_locked: bool


class AdminInboxResponse(BaseModel):
    """Admin-only view of the answers forwarded from the journey."""

    items: list[dict[str, Any]]


@router.get("/status", response_model=JourneyStatusResponse)
def journey_status(
    _session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> JourneyStatusResponse:
    """Return journey progress without revealing answers."""

    db = get_db()
    journey = db["journey"]
    answers = journey.get("answers", {})
    completed = bool(journey.get("completed", False))
    current_q = int(journey.get("current_q", 1))
    locked = completed or current_q > TOTAL_JOURNEY_QUESTIONS

    return JourneyStatusResponse(
        visible=not locked,
        locked=locked,
        current_q=current_q,
        completed=completed,
        answered_count=len(answers) if isinstance(answers, dict) else 0,
        total_questions=TOTAL_JOURNEY_QUESTIONS,
    )


@router.post("/answer", response_model=AnswerSubmissionResponse)
def submit_answer(
    submission: AnswerSubmission,
    _session: Annotated[dict[str, Any], Depends(get_current_session)],
) -> AnswerSubmissionResponse:
    """Save the next answer, generate insight, and forward it to the inbox."""

    db = get_db()
    journey = db["journey"]
    current_q = int(journey.get("current_q", 1))
    completed = bool(journey.get("completed", False))

    if completed or current_q > TOTAL_JOURNEY_QUESTIONS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The journey is complete and locked.",
        )

    if submission.question_number != current_q:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Please answer question {current_q} next.",
        )

    answers = journey.setdefault("answers", {})
    existing_memories = db.setdefault("memories", [])
    insight = generate_ai_insight(
        question_number=submission.question_number,
        answer=submission.answer,
        existing_memories=existing_memories,
    )

    answers[str(submission.question_number)] = submission.answer
    memory_texts: list[str] = []
    for memory in insight["memories"]:
        if not any(
            isinstance(existing, dict) and existing.get("text") == memory
            for existing in existing_memories
        ):
            existing_memories.append(
                {
                    "text": memory,
                    "source": "journey",
                    "question_number": submission.question_number,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
            memory_texts.append(memory)

    db.setdefault("admin_inbox", []).append(
        {
            "question_number": submission.question_number,
            "answer": submission.answer,
            "ai_insight": insight["insight"],
            "memories_added": memory_texts,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )

    journey_completed = submission.question_number == TOTAL_JOURNEY_QUESTIONS
    if journey_completed:
        journey["completed"] = True
        journey["current_q"] = TOTAL_JOURNEY_QUESTIONS
    else:
        journey["current_q"] = submission.question_number + 1

    save_db(db)

    return AnswerSubmissionResponse(
        saved=True,
        question_number=submission.question_number,
        next_question=None if journey_completed else journey["current_q"],
        ai_insight=insight["insight"],
        memories_added=memory_texts,
        journey_completed=journey_completed,
        journey_locked=journey_completed,
    )


@router.get(
    "/admin-inbox",
    response_model=AdminInboxResponse,
    dependencies=[Depends(verify_admin_secret)],
)
def admin_inbox() -> AdminInboxResponse:
    """Return journey submissions for an authorized administrator."""

    db = get_db()
    return AdminInboxResponse(items=db.get("admin_inbox", []))