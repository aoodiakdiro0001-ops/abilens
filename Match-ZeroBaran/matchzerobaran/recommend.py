"""Recommendation orchestration — blends substitutes, complements and signals
into one ranked list per customer, then lets the Brain write the pitch."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import config, engine as engine_mod
from .brain import (
    REASON_AFFINITY,
    REASON_BASKET,
    REASON_POPULAR,
    REASON_SIMILAR,
    write_pitch,
)
from .store import Store

REASON_TEXT = {
    "ar": {
        REASON_BASKET: "يُشترى عادةً مع {anchor}",
        REASON_AFFINITY: "من نفس الفئة التي تتصف بها مشترياتك ({anchor})",
        REASON_SIMILAR: "قريب من {anchor} الذي اخترته مؤخراً",
        REASON_POPULAR: "الأكثر مبيعاً في {category}",
    },
    "en": {
        REASON_BASKET: "Usually bought together with {anchor}",
        REASON_AFFINITY: "Same family as your recent picks ({anchor})",
        REASON_SIMILAR: "Close match to {anchor}",
        REASON_POPULAR: "Best seller in {category}",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _reason_text(reason: str, lang: str, anchor: str | None, category: str) -> str:
    table = REASON_TEXT.get(lang) or REASON_TEXT["ar"]
    template = table.get(reason, table[REASON_POPULAR])
    return template.format(anchor=anchor or "—", category=category or "—")


# --------------------------------------------------------------------------- #
def _score_candidates(
    eng: engine_mod.MatchEngine,
    customer_id: str,
    k: int,
) -> list[tuple[dict[str, Any], float, str, dict[str, Any] | None]]:
    """Returns [(product, score, reason_code, anchor_product)]."""
    bought, signals = eng.customer_signals(customer_id)
    purchased = set(bought)
    history = purchased | set(signals)

    rows: list[tuple[dict[str, Any], float, str, dict[str, Any] | None]] = []
    for p in eng.products:
        pid = p["id"]
        if pid in purchased:
            continue

        basket, affinity, similar, anchor_basket, anchor_sim = 0.0, 0.0, 0.0, None, None
        for held in history:
            held_p = eng.by_id.get(held)
            if not held_p:
                continue
            if held in purchased:  # complements come from real orders only
                lift = eng.lift(held, pid) / engine_mod.LIFT_CLIP
                if lift > basket:
                    basket, anchor_basket = lift, held_p
            aff = engine_mod.category_affinity(held_p, p)
            if aff > affinity:
                affinity = aff
            if held != pid and held in signals:  # substitutes from behaviour
                i, j = eng._pos.get(held), eng._pos.get(pid)
                if i is not None and j is not None:
                    sim = float(eng.index.scores(i)[j])
                    if sim > similar:
                        similar, anchor_sim = sim, held_p

        pop = eng.popularity(pid)
        if not history:  # cold start — rank by popularity alone
            rows.append((p, round(pop, 4), REASON_POPULAR, None))
            continue
        else:
            basket_n = min(1.0, basket)
            score = 0.45 * basket_n + 0.25 * affinity + 0.20 * min(1.0, similar) + 0.10 * pop
            parts = {
                REASON_BASKET: basket_n,
                REASON_AFFINITY: affinity,
                REASON_SIMILAR: min(1.0, similar),
                REASON_POPULAR: pop,
            }
            reason = max(parts, key=parts.get)  # type: ignore[arg-type]
            anchor = anchor_basket if reason == REASON_BASKET else (anchor_sim if reason == REASON_SIMILAR else None)
            if anchor is None and anchor_basket is not None:
                anchor = anchor_basket
        rows.append((p, round(score, 4), reason, anchor))

    rows.sort(key=lambda t: -t[1])
    return rows[: max(1, k)]


def _build_row(
    product: dict[str, Any],
    score: float,
    reason: str,
    anchor: dict[str, Any] | None,
    lang: str,
    customer_id: str,
    with_pitch: bool,
) -> dict[str, Any]:
    anchor_name = anchor.get("name") if anchor else None
    row = {
        "customer_id": customer_id,
        "product_id": product.get("id"),
        "name": product.get("name"),
        "category": product.get("category"),
        "price": product.get("price"),
        "currency": product.get("currency", "USD"),
        "url": product.get("url") or "",
        "score": score,
        "reason": reason,
        "reason_text": _reason_text(reason, lang, anchor_name, str(product.get("category") or "")),
        "anchor_id": anchor.get("id") if anchor else None,
        "anchor_name": anchor_name,
        "generated_at": _now(),
    }
    if with_pitch:
        row["pitch"] = write_pitch(product, reason=reason, lang=lang, anchor=anchor_name)
    return row


def recommend_for_customer(
    store: Store,
    eng: engine_mod.MatchEngine | None = None,
    customer_id: str | None = None,
    k: int | None = None,
    lang: str | None = None,
    with_pitch: bool = True,
) -> list[dict[str, Any]]:
    from .ingest import load_all  # local import avoids cycles

    data = load_all(store)
    eng = eng or engine_mod.MatchEngine(data["products"], data["orders"], data["events"])
    lang = (lang or config.LANG).lower()
    k = k or config.TOP_K

    if not customer_id:
        customers = data["customers"]
        if not customers:
            return []
        customer_id = customers[0]["id"]

    out = []
    for p, score, reason, anchor in _score_candidates(eng, customer_id, k):
        out.append(_build_row(p, score, reason, anchor, lang, customer_id, with_pitch))
    return out


def recommend_for_product(
    store: Store,
    product_id: str,
    eng: engine_mod.MatchEngine | None = None,
    k: int | None = None,
    lang: str | None = None,
    with_pitch: bool = True,
) -> list[dict[str, Any]]:
    from .ingest import load_all

    data = load_all(store)
    eng = eng or engine_mod.MatchEngine(data["products"], data["orders"], data["events"])
    lang = (lang or config.LANG).lower()
    k = k or config.TOP_K

    rows = []
    for p, score, reason in eng.complements(product_id, k):
        rows.append(_build_row(p, score, reason, eng.by_id.get(product_id), lang, "", with_pitch))
    return rows


def refresh(store: Store, k: int | None = None, lang: str | None = None) -> dict[str, Any]:
    """Batch job (GitHub Actions cron): recommendations for every customer."""
    from .ingest import export_recommendations, load_all

    data = load_all(store)
    eng = engine_mod.MatchEngine(data["products"], data["orders"], data["events"])
    rows: list[dict[str, Any]] = []
    for c in data["customers"]:
        rows.extend(
            recommend_for_customer(store, eng=eng, customer_id=c["id"], k=k, lang=lang, with_pitch=True)
        )
    path = export_recommendations(store, rows)
    return {"customers": len(data["customers"]), "rows": len(rows), "path": str(path)}