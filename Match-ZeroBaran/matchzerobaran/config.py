"""Central configuration. Every knob is env-driven; no secret lives in code."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _s(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


def _i(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


# --- paths -------------------------------------------------------------------
DATA_DIR = Path(_s("MZB_DATA", str(ROOT / "data")))
STORE_DIR = Path(_s("MZB_STORE", str(DATA_DIR / "store")))
CACHE_DIR = DATA_DIR / "cache"

# --- behaviour ---------------------------------------------------------------
TOP_K = _i("MZB_TOP_K", 3)
LANG = _s("MZB_LANG", "ar").lower() or "ar"
REQUEST_TIMEOUT = _i("MZB_TIMEOUT", 12)

# --- providers (all optional — templates are used when empty) ----------------
GEMINI_API_KEY = _s("GEMINI_API_KEY")
GROQ_API_KEY = _s("GROQ_API_KEY")
GEMINI_MODEL = _s("GEMINI_MODEL", "gemini-1.5-flash")
GROQ_MODEL = _s("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- delivery ----------------------------------------------------------------
TELEGRAM_BOT_TOKEN = _s("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _s("TELEGRAM_CHAT_ID")

# --- optional cloud persistence ---------------------------------------------
SUPABASE_URL = _s("SUPABASE_URL").rstrip("/")
SUPABASE_SERVICE_KEY = _s("SUPABASE_SERVICE_KEY")

# --- author / support (shown in reports and digests) -------------------------
AUTHOR = "Baran Avisat"
SUPPORT_EMAIL = "baranavisat@gmail.com"
SUPPORT_PHONE = "+90 531 326 37 22"


def ensure_dirs() -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)