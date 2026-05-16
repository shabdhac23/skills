"""
Configuration management for the Daily Digest Assistant.

Loads environment variables and provides validated configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""

    # Claude API
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    if not CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY not found in .env")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Email delivery
    DIGEST_RECIPIENT_EMAIL = os.getenv("DIGEST_RECIPIENT_EMAIL")
    DIGEST_SENDER_NAME = os.getenv("DIGEST_SENDER_NAME", "Daily Digest Assistant")

    # Gmail settings
    GMAIL_LOOK_BACK_HOURS = int(os.getenv("GMAIL_LOOK_BACK_HOURS", "24"))
    GMAIL_MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "20"))

    # Calendar settings
    CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

    # Notes settings
    NOTES_TODO_NAME = os.getenv("NOTES_TODO_NAME", "TODOs")
    NOTES_PRIORITIES_NAME = os.getenv("NOTES_PRIORITIES_NAME", "Priorities")

    # Digest settings
    DIGEST_TIMEZONE = os.getenv("DIGEST_TIMEZONE", "America/Los_Angeles")
    INCLUDE_EMAILS = os.getenv("INCLUDE_EMAILS", "true").lower() == "true"
    INCLUDE_CALENDAR = os.getenv("INCLUDE_CALENDAR", "true").lower() == "true"
    INCLUDE_NOTES = os.getenv("INCLUDE_NOTES", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required = ["CLAUDE_API_KEY", "DIGEST_RECIPIENT_EMAIL"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    @classmethod
    def to_dict(cls):
        """Return config as dictionary (for logging, excluding sensitive values)."""
        return {
            "google_oauth_configured": bool(cls.GOOGLE_CLIENT_ID),
            "digest_recipient": cls.DIGEST_RECIPIENT_EMAIL,
            "include_emails": cls.INCLUDE_EMAILS,
            "include_calendar": cls.INCLUDE_CALENDAR,
            "include_notes": cls.INCLUDE_NOTES,
        }


# Validate on import
Config.validate()
