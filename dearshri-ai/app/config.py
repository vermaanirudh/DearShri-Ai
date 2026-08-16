"""Application configuration for DearShri-AI."""

from pathlib import Path


APP_NAME = "DearShri AI"
ALLOWED_MOBILE_NUMBER = "8303796575"
ADMIN_MOBILE_NUMBER = "9792836590"
ADMIN_LOGIN_CODE = "2007"
SPECIAL_USER_ACCESS_CODE = "123456"
ADMIN_SECRET = "admin_access_key_2026"

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "app_data.json"
DATABASE_FILE = Path(__file__).resolve().parent.parent / "data" / "dearshri.sqlite3"
APP_TIMEZONE = "Asia/Kolkata"
TOTAL_JOURNEY_QUESTIONS = 100