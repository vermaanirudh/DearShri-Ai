"""Small JSON-backed persistence layer for the DearShri-AI starter."""

from __future__ import annotations

import json
from copy import deepcopy
from threading import RLock
from typing import Any

from .config import DATA_FILE


_DB_LOCK = RLock()


def _initial_data() -> dict[str, Any]:
    """Return a fresh copy of the initial application data structure."""

    return {
        "active_passcode": "123456",
        "user_session": None,
        "journey": {
            "current_q": 1,
            "completed": False,
            "answers": {},
        },
        "admin_inbox": [],
        "memories": [],
        "reminders": [],
        "journal": [],
        "users": {},
        "notices": [],
    }


def _merge_with_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Keep older JSON files compatible when new top-level keys are added."""

    defaults = _initial_data()
    for key, default_value in defaults.items():
        if key not in data:
            data[key] = deepcopy(default_value)

    journey = data.get("journey")
    if not isinstance(journey, dict):
        data["journey"] = deepcopy(defaults["journey"])
    else:
        for key, default_value in defaults["journey"].items():
            journey.setdefault(key, deepcopy(default_value))

    return data


def get_user_data(db: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Return isolated persistent data for a Clerk user ID."""

    users = db.setdefault("users", {})
    if not isinstance(users, dict):
        db["users"] = {}
        users = db["users"]

    user_data = users.setdefault(
        user_id,
        {
            "chat_history": [],
            "preferences": {
                "theme": "system",
                "notifications": True,
            },
            "memories": [],
            "reminders": [],
        },
    )
    if not isinstance(user_data, dict):
        users[user_id] = {
            "chat_history": [],
            "preferences": {
                "theme": "system",
                "notifications": True,
            },
            "memories": [],
            "reminders": [],
        }
        user_data = users[user_id]

    user_data.setdefault("chat_history", [])
    user_data.setdefault(
        "preferences",
        {"theme": "system", "notifications": True},
    )
    user_data.setdefault("memories", [])
    user_data.setdefault("reminders", [])
    return user_data


def get_db() -> dict[str, Any]:
    """Load application data, creating the JSON file when necessary."""

    with _DB_LOCK:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            data = _initial_data()
            save_db(data)
            return data

        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            raise RuntimeError(f"Unable to read application data: {error}") from error

        if not isinstance(raw_data, dict):
            raise RuntimeError("Application data must contain a JSON object.")

        return _merge_with_defaults(raw_data)


def save_db(data: dict[str, Any]) -> None:
    """Persist application data atomically to app_data.json."""

    with _DB_LOCK:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = DATA_FILE.with_suffix(".json.tmp")
        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
                file.write("\n")
            temporary_file.replace(DATA_FILE)
        except OSError as error:
            raise RuntimeError(f"Unable to save application data: {error}") from error