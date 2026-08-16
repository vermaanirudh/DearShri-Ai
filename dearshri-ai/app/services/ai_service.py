"""Empathetic insight and memory extraction helpers.

This module intentionally keeps the first backend build self-contained. The
prompt builder is ready to be connected to an LLM later, while the local
insight generator provides useful behavior without requiring an API key.
"""

from __future__ import annotations

import re
from typing import Any


EMPATHETIC_SYSTEM_PROMPT = (
    "You are DearShri AI, an empathetic and attentive companion. "
    "Respond with warmth, patience, and emotional safety. Reflect what the "
    "person shared without judging, diagnosing, or pretending certainty. "
    "Offer one gentle observation and, when appropriate, one supportive "
    "follow-up thought. Keep the response concise and human."
)

COMMAND_PREFIXES = (
    "/",
    "command:",
    "settings ",
    "set theme ",
    "clear chat",
    "show notices",
)

COMPANION_MODES = {
    "friend": {
        "label": "Friend",
        "description": "Gentle, supportive, empathetic, and cooperative.",
    },
    "tutor": {
        "label": "Tutor",
        "description": "Strategy-focused, clear, and firm about study plans.",
    },
    "guardian": {
        "label": "Guardian",
        "description": "Protective, practical, and firm about safety and wellbeing.",
    },
    "admin": {
        "label": "Admin",
        "description": "A direct user-to-admin channel; AI generation is disabled.",
    },
}


def build_empathetic_prompt(question_number: int, answer: str) -> str:
    """Build the prompt used for an empathetic AI insight."""

    return (
        f"{EMPATHETIC_SYSTEM_PROMPT}\n\n"
        f"Journey question number: {question_number}\n"
        f"Person's answer:\n{answer.strip()}\n\n"
        "Write a short empathetic insight in the first person plural or "
        "second person, without inventing facts."
    )


def classify_message(message: str) -> str:
    """Classify input before responding so commands are not treated as chat."""

    normalized = message.strip().lower()
    if normalized.startswith(COMMAND_PREFIXES):
        return "command"
    return "conversation"


def execute_command(command: str, preferences: dict[str, Any]) -> dict[str, Any]:
    """Execute only supported deterministic commands."""

    normalized = command.strip().lower()
    if normalized in {"/clear", "/clear chat", "clear chat"}:
        return {
            "command": "clear_chat",
            "message": "Your chat history is ready to be cleared.",
            "action": "clear_chat",
        }
    if normalized in {"/notices", "show notices"}:
        return {
            "command": "show_notices",
            "message": "I’ll bring your latest notices into view.",
            "action": "show_notices",
        }
    if normalized.startswith("set theme "):
        theme = normalized.removeprefix("set theme ").strip()
        if theme not in {"light", "dark", "system"}:
            return {
                "command": "set_theme",
                "message": "Theme must be light, dark, or system.",
                "action": "none",
            }
        preferences["theme"] = theme
        return {
            "command": "set_theme",
            "message": f"Theme set to {theme}.",
            "action": "set_theme",
            "theme": theme,
        }
    return {
        "command": "unsupported",
        "message": "I can help with clear chat, show notices, or set theme.",
        "action": "none",
    }


def generate_chat_response(
    message: str,
    history: list[dict[str, Any]],
    mode: str = "friend",
) -> str:
    """Return a concise, grounded response for casual conversation."""

    normalized = message.lower()
    if "who are you" in normalized:
        return "I’m DearShri AI, a focused companion for clear, grounded conversations."
    if "thank" in normalized:
        return "You’re welcome. I’m here whenever you want to continue."
    if "help" in normalized:
        return "I can help you think through a question, make a plan, or take one clear next step."
    if len(history) > 20:
        return "There is a lot in this conversation. I’m keeping the thread focused on what you just shared."
    if mode == "tutor":
        return "Let’s make this practical: choose one clear task, give it a short time block, and start there."
    if mode == "guardian":
        return "Let’s keep this grounded and safe. Focus on the next practical step and reach out to a trusted person if you need support."
    return (
        "I hear you. I’ll stay with what you shared and keep the next step clear. "
        "What part feels most important right now?"
    )


def extract_memories(answer: str) -> list[str]:
    """Extract durable first-person facts from an answer.

    The patterns are intentionally conservative: only statements that look
    like preferences, identity, needs, goals, or relationships become memories.
    """

    normalized = " ".join(answer.strip().split())
    if not normalized:
        return []

    patterns = (
        r"\b(?:my name is|i am called)\s+([^.!?]+)",
        r"\b(?:i love|i like|i enjoy|i prefer|i value)\s+([^.!?]+)",
        r"\b(?:i want|i need|i hope to|i dream of|i am working toward)\s+([^.!?]+)",
        r"\b(?:i live in|i work in|i work at|i study at)\s+([^.!?]+)",
        r"\b(?:my partner is|my family is|my friend is)\s+([^.!?]+)",
    )

    memories: list[str] = []
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" ,")
            if value:
                memories.append(f"{normalized[: normalized.lower().find(value.lower()) + len(value)]}.")
                break

    return memories


def _local_empathetic_insight(answer: str) -> str:
    """Return a safe local insight while an external LLM is not configured."""

    words = len(answer.split())
    if words <= 4:
        return (
            "Thank you for sharing that. Even a few words can hold something "
            "important, and I’m listening."
        )
    return (
        "Thank you for trusting me with that. I hear the meaning in what you "
        "shared, and I’ll keep it in mind as we continue."
    )


def generate_ai_insight(
    question_number: int,
    answer: str,
    existing_memories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create an empathetic insight and identify new memories to persist."""

    prompt = build_empathetic_prompt(question_number, answer)
    extracted_memories = extract_memories(answer)
    known_texts = {
        memory.get("text")
        for memory in existing_memories
        if isinstance(memory, dict)
    }

    return {
        "prompt": prompt,
        "insight": _local_empathetic_insight(answer),
        "memories": [
            memory for memory in extracted_memories if memory not in known_texts
        ],
    }