"""Ingestion layer: CSV/JSON sources -> normalised store tables.

Works with any shop export: one row per purchased item in `orders.csv`,
one row per behaviour signal in `events.csv`.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .store import Store

REQUIRED_PRODUCT = ("id", "name")


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"source not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").strip() or default)
    except (TypeError, ValueError):
        return default


def _norm_ts(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            continue
    return value


def load_products(path: Path) -> list[dict[str, Any]]:
    """Products CSV: id,name,category,tags,price,description[,url]"""
    rows = _read_csv(path)
    products = []
    for r in rows:
        pid = (r.get("id") or "").strip()
        name = (r.get("name") or "").strip()
        if not pid or not name:
            continue
        products.append(
            {
                "id": pid,
                "name": name,
                "category": (r.get("category") or "general").strip().lower(),
                "tags": (r.get("tags") or "").strip().lower(),
                "price": _num(r.get("price")),
                "currency": (r.get("currency") or "USD").strip(),
                "description": (r.get("description") or "").strip(),
                "url": (r.get("url") or "").strip(),
            }
        )
    return products


def load_customers(path: Path) -> list[dict[str, Any]]:
    """Customers CSV: id,name,city,lang,tier"""
    if not path.exists():
        return []
    customers = []
    for r in _read_csv(path):
        cid = (r.get("id") or "").strip()
        if not cid:
            continue
        customers.append(
            {
                "id": cid,
                "name": (r.get("name") or cid).strip(),
                "city": (r.get("city") or "").strip(),
                "lang": (r.get("lang") or config.LANG).strip().lower(),
                "tier": (r.get("tier") or "").strip(),
            }
        )
    return customers


def load_orders(path: Path) -> list[dict[str, Any]]:
    """Long-format orders CSV: order_id,customer_id,ts,product_id,qty,price"""
    rows = _read_csv(path)
    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        oid = (r.get("order_id") or "").strip()
        pid = (r.get("product_id") or "").strip()
        if not oid or not pid:
            continue
        order = grouped.setdefault(
            oid,
            {
                "id": oid,
                "customer_id": (r.get("customer_id") or "").strip(),
                "ts": _norm_ts(r.get("ts", "")),
                "items": [],
                "total": 0.0,
            },
        )
        qty = max(1, int(_num(r.get("qty"), 1)))
        price = _num(r.get("price"), 0.0)
        order["items"].append({"product_id": pid, "qty": qty, "price": price})
        order["total"] = round(order["total"] + qty * price, 2)
    orders = list(grouped.values())
    orders.sort(key=lambda o: o["ts"])
    return orders


def load_events(path: Path) -> list[dict[str, Any]]:
    """Behaviour CSV: customer_id,product_id,type,ts  (type = view|cart|purchase)"""
    if not path.exists():
        return []
    events = []
    for r in _read_csv(path):
        cid = (r.get("customer_id") or "").strip()
        pid = (r.get("product_id") or "").strip()
        if not cid or not pid:
            continue
        kind = (r.get("type") or "view").strip().lower()
        if kind not in ("view", "cart", "purchase"):
            kind = "view"
        events.append({"customer_id": cid, "product_id": pid, "type": kind, "ts": _norm_ts(r.get("ts", ""))})
    events.sort(key=lambda e: e["ts"])
    return events


def ingest(store: Store, data_dir: Path | str | None = None) -> dict[str, int]:
    """Read every CSV in `data_dir` and persist normalised tables. Returns counts."""
    data_dir = Path(data_dir or config.DATA_DIR)
    tables = {
        "products": load_products(data_dir / "products.csv"),
        "customers": load_customers(data_dir / "customers.csv"),
        "orders": load_orders(data_dir / "orders.csv"),
        "events": load_events(data_dir / "events.csv"),
    }
    counts = {name: store.save(name, rows) for name, rows in tables.items()}
    # optional cloud mirror (silent no-op when Supabase is not configured)
    for name, rows in tables.items():
        store.sync(name, rows)
    return counts


def export_recommendations(store: Store, rows: list[dict[str, Any]]) -> Path:
    config.ensure_dirs()
    out = config.STORE_DIR / "recommendations.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    store.save("recommendations", rows)
    store.sync("recommendations", rows)
    return out


def load_all(store: Store) -> dict[str, list[dict[str, Any]]]:
    return {name: store.load(name) for name in ("products", "customers", "orders", "events")}