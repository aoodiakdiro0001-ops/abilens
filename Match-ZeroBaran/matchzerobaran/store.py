"""Persistence layer.

Default: local JSON store (zero configuration, works offline, instant).
Optional: Supabase (PostgreSQL + pgvector) sync over its REST API — no SDK
required, so the project stays dependency-light.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

from . import config

TABLES = ("products", "customers", "orders", "events", "recommendations")


class Store:
    """Tiny atomic JSON document store: one file per table."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root or config.STORE_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- local ----------------------------------------------------------------
    def path(self, table: str) -> Path:
        return self.root / f"{table}.json"

    def load(self, table: str) -> list[dict[str, Any]]:
        p = self.path(table)
        if not p.exists():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def save(self, table: str, rows: Iterable[dict[str, Any]]) -> int:
        rows = list(rows)
        payload = json.dumps(rows, ensure_ascii=False, indent=1, default=str)
        fd, tmp = tempfile.mkstemp(dir=str(self.root), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
            os.replace(tmp, self.path(table))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return len(rows)

    def upsert(self, table: str, key: str, rows: Iterable[dict[str, Any]]) -> int:
        current = {r.get(key): r for r in self.load(table) if r.get(key) is not None}
        for row in rows:
            current[row.get(key)] = row
        merged = list(current.values())
        return self.save(table, merged)

    def append(self, table: str, row: dict[str, Any]) -> None:
        rows = self.load(table)
        rows.append(row)
        self.save(table, rows)

    def clear(self, table: str) -> None:
        self.save(table, [])

    # -- optional cloud sync ---------------------------------------------------
    def push_supabase(self, table: str, rows: list[dict[str, Any]]) -> bool:
        """Upsert rows into Supabase via REST. Returns False when not configured."""
        if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
            return False
        if not rows:
            return True
        try:
            import requests  # local import: optional dependency
        except ImportError:
            return False
        url = f"{config.SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey": config.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }
        try:
            r = requests.post(url, headers=headers, json=rows, timeout=config.REQUEST_TIMEOUT)
            return r.status_code < 300
        except Exception:
            return False

    def sync(self, table: str, rows: list[dict[str, Any]] | None = None) -> bool:
        return self.push_supabase(table, rows if rows is not None else self.load(table))


def open_store() -> Store:
    config.ensure_dirs()
    return Store()