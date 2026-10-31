"""Delivery layer — Telegram digests (free) for the merchant or the customer."""

from __future__ import annotations

from typing import Any

from . import config

FOOTER_AR = "— {author} · الدعم: {email} · واتساب {phone}"
FOOTER_EN = "— {author} · Support: {email} · WhatsApp {phone}"


def telegram_send(text: str, chat_id: str | None = None, token: str | None = None) -> bool:
    """Send a message. Returns False silently when not configured (no crash, no leak)."""
    token = token or config.TELEGRAM_BOT_TOKEN
    chat_id = chat_id or config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False
    try:
        import requests
    except ImportError:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text[:3900], "disable_web_page_preview": True},
            timeout=config.REQUEST_TIMEOUT,
        )
        return r.status_code < 300
    except Exception:
        return False


def build_digest(
    rows: list[dict[str, Any]],
    customer_name: str = "",
    lang: str | None = None,
    title: str = "",
) -> str:
    """Human-readable digest of a recommendation batch."""
    lang = (lang or config.LANG).lower()
    ar = lang == "ar"
    if not rows:
        return "لا توجد توصيات جديدة بعد. / No recommendations yet."

    if not title:
        title = f"🎯 توصيات مخصصة — {customer_name}" if ar else f"🎯 Personal picks — {customer_name}"
    lines = [title, ""]
    for i, r in enumerate(rows, 1):
        price = r.get("price") or 0
        symbol = {"USD": "$", "TRY": "₺"}.get(r.get("currency", "USD"), "")
        price_line = f" · {symbol}{price:g}" if price else ""
        lines.append(
            f"{i}. {r.get('name')} ({r.get('category')}){price_line}\n"
            f"   ↳ {r.get('reason_text') or ''}\n"
            f"   ↳ {r.get('pitch') or ''}"
        )
        if r.get("url"):
            lines.append(f"   🔗 {r['url']}")
        lines.append("")
    footer = FOOTER_AR if ar else FOOTER_EN
    lines.append(footer.format(author=config.AUTHOR, email=config.SUPPORT_EMAIL, phone=config.SUPPORT_PHONE))
    return "\n".join(lines)


def send_digest(rows: list[dict[str, Any]], customer_name: str = "", lang: str | None = None) -> bool:
    return telegram_send(build_digest(rows, customer_name=customer_name, lang=lang))