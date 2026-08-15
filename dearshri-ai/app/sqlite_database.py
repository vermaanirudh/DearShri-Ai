"""SQLite persistence, schema creation, and user isolation for DearShri AI."""

from __future__ import annotations

import secrets
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from .config import (
    ADMIN_LOGIN_CODE,
    ADMIN_MOBILE_NUMBER,
    APP_TIMEZONE,
    DATABASE_FILE,
    SPECIAL_USER_ACCESS_CODE,
)


_DB_LOCK = RLock()
_TZ = ZoneInfo(APP_TIMEZONE)


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL UNIQUE,
    age TEXT,
    class TEXT,
    school TEXT,
    location_data TEXT NOT NULL DEFAULT '{}',
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS daily_codes (
    date TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'archived')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journey_set_id INTEGER NOT NULL REFERENCES journey_sets(id) ON DELETE CASCADE,
    story_id TEXT NOT NULL,
    question_num INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    UNIQUE (journey_set_id, question_num)
);

CREATE INDEX IF NOT EXISTS idx_journey_questions_set
    ON journey_questions(journey_set_id, question_num);

CREATE TABLE IF NOT EXISTS journey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    journey_set_id INTEGER NOT NULL REFERENCES journey_sets(id) ON DELETE RESTRICT,
    story_id TEXT NOT NULL,
    question_id INTEGER NOT NULL REFERENCES journey_questions(id) ON DELETE RESTRICT,
    answer_text TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_journey_responses_user
    ON journey_responses(user_id, journey_set_id, timestamp);

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    age TEXT,
    class TEXT,
    school TEXT,
    location_data TEXT NOT NULL DEFAULT '{}',
    gender TEXT,
    languages TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS personality_traits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trait_key TEXT NOT NULL,
    trait_value TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    source TEXT NOT NULL,
    last_updated TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traits_user ON personality_traits(user_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mode TEXT NOT NULL DEFAULT 'companion',
    sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
    text TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user
    ON chat_messages(user_id, timestamp);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme TEXT NOT NULL DEFAULT 'system',
    notifications INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS system_notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notice_dismissals (
    notice_id INTEGER NOT NULL REFERENCES system_notices(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dismissed_at TEXT NOT NULL,
    PRIMARY KEY (notice_id, user_id)
);
"""


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def today_key() -> str:
    return datetime.now(_TZ).date().isoformat()


def normalize_phone(phone_number: str) -> str:
    digits = "".join(character for character in phone_number if character.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits


def _connect() -> sqlite3.Connection:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _seed_journey(connection: sqlite3.Connection) -> None:
    existing = connection.execute(
        "SELECT id FROM journey_sets WHERE version = 1",
    ).fetchone()
    if existing:
        return

    created_at = now_iso()
    cursor = connection.execute(
        """
        INSERT INTO journey_sets (version, title, status, created_at)
        VALUES (?, ?, 'published', ?)
        """,
        (1, "The DearShri Journey", created_at),
    )
    set_id = cursor.lastrowid
    connection.executemany(
        """
        INSERT INTO journey_questions
            (journey_set_id, story_id, question_num, prompt_text)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                set_id,
                f"story-{((question_number - 1) // 10) + 1}",
                question_number,
                (
                    f"Question {question_number}: What feels most present "
                    "for you right now?"
                ),
            )
            for question_number in range(1, 251)
        ],
    )


def _seed_users(connection: sqlite3.Connection) -> None:
    created_at = now_iso()
    connection.execute(
        """
        INSERT OR IGNORE INTO users
            (phone_number, age, class, school, location_data, role, created_at)
        VALUES (?, ?, ?, ?, ?, 'user', ?)
        """,
        (
            "8303796575",
            "16-18",
            "11th",
            "The Elite Academy",
            '{"district":"Lakhimpur","sub_district":"Dhaurahra","village":"Baburi"}',
            created_at,
        ),
    )
    special_user = connection.execute(
        "SELECT id FROM users WHERE phone_number = ?",
        ("8303796575",),
    ).fetchone()
    if special_user:
        connection.execute(
            """
            INSERT OR IGNORE INTO user_profiles
                (user_id, age, class, school, location_data, gender,
                 languages, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                special_user["id"],
                "16-18",
                "11th",
                "The Elite Academy",
                '{"district":"Lakhimpur","sub_district":"Dhaurahra","village":"Baburi"}',
                "Female",
                '["Hindi","Awadhi","English"]',
                created_at,
                created_at,
            ),
        )

    connection.execute(
        """
        INSERT OR IGNORE INTO users
            (phone_number, role, created_at)
        VALUES (?, 'admin', ?)
        """,
        (ADMIN_MOBILE_NUMBER, created_at),
    )


def initialize_database() -> None:
    with _DB_LOCK, closing(_connect()) as connection:
        connection.executescript(SCHEMA)
        _seed_users(connection)
        _seed_journey(connection)
        connection.commit()


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection with schema guaranteed before first use."""

    initialize_database()
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_user(
    connection: sqlite3.Connection,
    phone_number: str,
) -> sqlite3.Row:
    normalized = normalize_phone(phone_number)
    existing = connection.execute(
        "SELECT * FROM users WHERE phone_number = ?",
        (normalized,),
    ).fetchone()
    if existing:
        return existing
    cursor = connection.execute(
        """
        INSERT INTO users (phone_number, role, created_at)
        VALUES (?, 'user', ?)
        """,
        (normalized, now_iso()),
    )
    return connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()


def get_user_by_id(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not user:
        raise ValueError("User not found.")
    return user


def current_daily_code(connection: sqlite3.Connection) -> str:
    date_key = today_key()
    row = connection.execute(
        "SELECT code FROM daily_codes WHERE date = ?",
        (date_key,),
    ).fetchone()
    if row:
        return row["code"]
    code = f"{secrets.randbelow(900000) + 100000:06d}"
    connection.execute(
        """
        INSERT INTO daily_codes (date, code, created_at)
        VALUES (?, ?, ?)
        """,
        (date_key, code, now_iso()),
    )
    return code


def validate_login_code(
    connection: sqlite3.Connection,
    phone_number: str,
    passcode: str,
) -> sqlite3.Row:
    normalized = normalize_phone(phone_number)
    user = connection.execute(
        "SELECT * FROM users WHERE phone_number = ?",
        (normalized,),
    ).fetchone()
    if not user:
        # Registering a normal user never inherits the seeded profile.
        user = ensure_user(connection, normalized)

    if normalized == ADMIN_MOBILE_NUMBER:
        expected = ADMIN_LOGIN_CODE
    elif normalized == "8303796575":
        expected = SPECIAL_USER_ACCESS_CODE
    else:
        expected = current_daily_code(connection)

    if not secrets.compare_digest(str(passcode), expected):
        raise PermissionError("The passcode is invalid or expired.")
    return user


def create_session(
    connection: sqlite3.Connection,
    user: sqlite3.Row,
) -> tuple[str, str | None]:
    # A persistent profile keeps one durable token until explicit logout.
    persistent = user["phone_number"] == "8303796575"
    connection.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    token = secrets.token_urlsafe(48)
    expires_at = None
    if not persistent:
        expires_at = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    connection.execute(
        """
        INSERT INTO sessions (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user["id"], token, expires_at, now_iso()),
    )
    return token, expires_at


def session_user(
    connection: sqlite3.Connection,
    token: str,
) -> sqlite3.Row | None:
    row = connection.execute(
        """
        SELECT s.*, u.phone_number, u.age, u.class, u.school,
               u.location_data, u.role, u.created_at AS user_created_at
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
        """,
        (token,),
    ).fetchone()
    if not row:
        return None
    if row["expires_at"]:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= datetime.now(UTC):
            connection.execute("DELETE FROM sessions WHERE id = ?", (row["id"],))
            return None
    return row


def user_profile(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT u.id, u.phone_number, u.age, u.class, u.school,
               u.location_data, u.role, u.created_at,
               p.gender, p.languages, p.updated_at
        FROM users u
        LEFT JOIN user_profiles p ON p.user_id = u.id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()