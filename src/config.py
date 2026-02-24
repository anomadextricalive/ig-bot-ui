"""
Centralized configuration loaded from environment variables.
"""

import os
import sys
from dotenv import load_dotenv


def load_config() -> dict:
    """Load and validate configuration from .env file."""
    load_dotenv()

    config = {
        "username": os.getenv("IG_USERNAME", ""),
        "password": os.getenv("IG_PASSWORD", ""),
        "allowed_sender": os.getenv("ALLOWED_SENDER", ""),
        "poll_interval": int(os.getenv("POLL_INTERVAL_SECONDS", "60")),
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL", ""),
    }

    # Validate required fields
    missing = []
    if not config["username"]:
        missing.append("IG_USERNAME")
    if not config["password"]:
        missing.append("IG_PASSWORD")
    if not config["allowed_sender"]:
        missing.append("ALLOWED_SENDER")

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("   Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    return config
