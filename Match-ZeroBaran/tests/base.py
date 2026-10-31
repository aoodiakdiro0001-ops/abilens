"""Shared test bootstrap: isolate the store, force the offline (template) brain.

Import this module FIRST in every test module — it configures the environment
before `matchzerobaran.config` reads it.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="mzb-test-"))
os.environ["MZB_STORE"] = str(_TMP / "store")
os.environ["MZB_LANG"] = "ar"
os.environ["MZB_TOP_K"] = "3"

# never let CI/dev secrets leak into tests (would trigger real network calls)
for _key in (
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
):
    os.environ.pop(_key, None)

DATA = ROOT / "data"


def cleanup() -> None:
    shutil.rmtree(_TMP, ignore_errors=True)