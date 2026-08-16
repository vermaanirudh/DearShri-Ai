"""Safe, non-clinical whole-journey trait extraction."""

from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from typing import Any


TRAIT_RULES = (
    (
        "curiosity",
        "curious and exploratory",
        ("curious", "learn", "discover", "explore", "question", "interest"),
    ),
    (
        "connection",
        "relationship-oriented and attentive to trust",
        ("trust", "friend", "listen", "understood", "relationship", "people"),
    ),
    (
        "self_awareness",
        "reflective and interested in understanding themselves",
        ("myself", "understand", "authentic", "personality", "feel", "self"),
    ),
    (
        "resilience",
        "thoughtful about recovering and moving forward",
        ("hard", "mistake", "confidence", "forward", "support", "difficult"),
    ),
    (
        "values",
        "guided by clear personal values",
        ("respect", "principle", "belief", "important", "good person", "stand"),
    ),
    (
        "future_orientation",
        "motivated by meaningful future growth",
        ("future", "goal", "becoming", "progress", "motivat", "strength"),
    ),
)


def analyze_completed_journey(
    connection: sqlite3.Connection,
    user_id: int,
    journey_set_id: int,
    version: int,
) -> list[dict[str, Any]]:
    """Summarize all answers into supportive context, never a diagnosis."""

    rows = connection.execute(
        """
        SELECT answer_text FROM journey_responses
        WHERE user_id = ? AND journey_set_id = ?
        ORDER BY question_id ASC
        """,
        (user_id, journey_set_id),
    ).fetchall()
    corpus = " ".join(row["answer_text"] for row in rows).lower()
    timestamp = datetime.now(UTC).isoformat()
    source = f"journey_v{version}"
    connection.execute(
        """
        DELETE FROM personality_traits
        WHERE user_id = ? AND source = ?
        """,
        (user_id, source),
    )
    traits: list[dict[str, Any]] = []
    for key, label, keywords in TRAIT_RULES:
        hits = sum(len(re.findall(re.escape(keyword), corpus)) for keyword in keywords)
        confidence = min(0.95, 0.45 + (hits * 0.08)) if hits else 0.32
        trait = {
            "trait_key": key,
            "trait_value": label,
            "confidence": round(confidence, 2),
            "source": source,
            "last_updated": timestamp,
        }
        connection.execute(
            """
            INSERT INTO personality_traits
                (user_id, trait_key, trait_value, confidence, source, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                trait["trait_key"],
                trait["trait_value"],
                trait["confidence"],
                trait["source"],
                trait["last_updated"],
            ),
        )
        traits.append(trait)
    return traits