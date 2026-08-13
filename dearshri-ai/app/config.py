"""Application configuration for DearShri-AI."""

from pathlib import Path


APP_NAME = "DearShri AI"
ALLOWED_MOBILE_NUMBER = "910000000000"
ADMIN_SECRET = "admin_access_key_2026"

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "app_data.json"
TOTAL_JOURNEY_QUESTIONS = 250