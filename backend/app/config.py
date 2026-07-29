import os
from dotenv import load_dotenv

load_dotenv()

# Base URL of your already-running PasarGuard panel, e.g. https://panel.example.com
PASARGUARD_BASE_URL = os.environ.get("PASARGUARD_BASE_URL", "").rstrip("/")

# Name of the cookie used to track logged-in sessions
COOKIE_NAME = os.environ.get("COOKIE_NAME", "kryptex_session")

# How long a login session stays valid (seconds). Re-login required after this.
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(60 * 60 * 8)))  # 8 hours

# Set to "true" behind HTTPS in production so the cookie is marked Secure.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

# Where the local sqlite database (reseller metadata) is stored
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "kryptex.db"))

if not PASARGUARD_BASE_URL:
    raise RuntimeError(
        "PASARGUARD_BASE_URL is not set. Copy .env.example to .env and fill in your panel's URL."
    )
