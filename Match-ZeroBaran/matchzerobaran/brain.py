"""AI Matching Brain — persuasive copy for every recommendation.

Provider order: Gemini free tier -> Groq free tier -> deterministic template.
The template path needs **zero keys**, so the product keeps working offline.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import config

REASON_BASKET = "basket"
REASON_AFFINITY = "affinity"
REASON_SIMILAR = "similar"
REASON_POPULAR = "popular"

TEMPLATES: dict[str, dict[str, str]] = {
    "ar": {
        REASON_BASKET: "اشتريت {anchor} مؤخراً، و«{name}» هو الرفيق الذي يكمل التجربة فعلاً — يُختار عادةً معه. {price_line}",
        REASON_AFFINITY: "ذوقك في «{category}» واضح، ولهذا اخترنا لك «{name}»: {desc_line}",
        REASON_SIMILAR: "إذا أعجبك «{anchor}» فـ«{name}» أقرب شيء إليه — نفس الفئة، مواصفات أقرب لاحتياجك. {price_line}",
        REASON_POPULAR: "«{name}» من أكثر المنتجات مبيعاً في فئته ({category}) لدى عملائنا. {price_line}",
        "opening": "مقترح مخصص لك:",
        "suffix": "",
    },
    "en": {
        REASON_BASKET: "You bought {anchor} recently — «{name}» is the piece that completes the set. {price_line}",
        REASON_AFFINITY: "Your taste in {category} is clear, so we picked «{name}» for you{desc_line}.",
        REASON_SIMILAR: "If you liked «{anchor}», «{name}» is the closest match — same category, closer fit. {price_line}",
        REASON_POPULAR: "«{name}» is one of the best sellers in {category}. {price_line}",
        "opening": "Picked for you:",
        "suffix": "",
    },
}

PROMPTS = {
    "ar": (
        "أنت كاتب تسويق محترف لمتجر إلكتروني عربي. اكتب جملة تسويقية واحدة بالعربية الفصحى "
        "البسيطة (لا أكثر من 35 كلمة، بلا صياغات مبالغة أو وعود كاذبة ولا علامات ترقيم زائدة) "
        "تشرح لماذا يناسب العميل المنتج المطلوب.\n"
        "المنتج: {name} | الفئة: {category} | السبب: {reason}\n"
        "السياق: {context}\n"
        "أعد الجملة فقط."
    ),
    "en": (
        "You are a professional e-commerce copywriter. Write ONE sentence (max 25 words, "
        "no hype, no false scarcity, no quotes) explaining why this product fits the customer.\n"
        "Product: {name} | Category: {category} | Reason: {reason}\n"
        "Context: {context}\n"
        "Reply with the sentence only."
    ),
}


# --------------------------------------------------------------------------- #
# cache (file based — keeps free-tier quotas safe)
# --------------------------------------------------------------------------- #
# bump whenever templates/prompts change — invalidates every cached pitch
BRAIN_VERSION = "v2"


def _cache_load() -> dict[str, str]:
    path = config.CACHE_DIR / "pitches.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _cache_put(key: str, value: str) -> None:
    try:
        config.ensure_dirs()
        data = _cache_load()
        data[key] = value
        (config.CACHE_DIR / "pitches.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# providers
# --------------------------------------------------------------------------- #
def _post(url: str, *, headers: dict, payload: dict) -> dict | None:
    try:
        import requests
    except ImportError:
        return None
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=config.REQUEST_TIMEOUT)
        if r.status_code >= 300:
            return None
        return r.json()
    except Exception:
        return None


def _gemini(prompt: str) -> str | None:
    if not config.GEMINI_API_KEY:
        return None
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    data = _post(url, headers={"Content-Type": "application/json"}, payload={"contents": [{"parts": [{"text": prompt}]}]})
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def _groq(prompt: str) -> str | None:
    if not config.GROQ_API_KEY:
        return None
    data = _post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
        payload={
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 120,
        },
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def _price_line(product: dict[str, Any], lang: str | None = None) -> str:
    price = float(product.get("price") or 0)
    if price <= 0:
        return ""
    currency = str(product.get("currency") or "USD")
    symbol = {"USD": "$", "TRY": "₺", "EUR": "€"}.get(currency, currency + " ")
    if (lang or config.LANG) == "ar":
        return f"السعر: {symbol}{price:g}"
    return f"Price: {symbol}{price:g}"


def _template_pitch(product: dict[str, Any], reason: str, anchor: str | None, lang: str) -> str:
    table = TEMPLATES.get(lang) or TEMPLATES["ar"]
    desc = str(product.get("description") or "").strip()
    if len(desc) > 110:
        desc = desc[:107].rstrip() + "…"
    # catalogue copy may be Arabic even when the pitch language is English
    if lang != "ar" and any("\u0600" <= c <= "\u06ff" for c in desc):
        desc = ""
    values = {
        "name": str(product.get("name") or ""),
        "category": str(product.get("category") or ""),
        "anchor": anchor or "—",
        "desc_line": (desc or "—") if lang == "ar" else (f": {desc}" if desc else ""),
        "price_line": _price_line(product, lang),
    }
    try:
        text = table.get(reason) or table[REASON_POPULAR]
        return text.format(**values).replace("  ", " ").strip()
    except Exception:
        return values["name"]


def write_pitch(
    product: dict[str, Any],
    reason: str = REASON_POPULAR,
    lang: str | None = None,
    anchor: str | None = None,
    use_cache: bool = True,
) -> str:
    """Return one persuasive sentence for `product` — AI if keyed, template if not."""
    lang = (lang or config.LANG).lower()
    anchor = (anchor or "").strip() or None
    key_src = "|".join([BRAIN_VERSION, str(product.get("id")), reason, lang, anchor or ""])
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:20]

    if use_cache:
        cached = _cache_load().get(key)
        if cached:
            return cached

    context = f"مرتبط بـ: {anchor}" if lang == "ar" else f"linked to: {anchor}"
    prompt = PROMPTS.get(lang, PROMPTS["ar"]).format(
        name=product.get("name", ""), category=product.get("category", ""), reason=reason, context=context
    )

    text = None
    if lang == "ar":
        text = _gemini(prompt) or _groq(prompt)
    else:
        text = _groq(prompt) or _gemini(prompt)

    if not text:
        text = _template_pitch(product, reason, anchor, lang)
    text = " ".join(str(text).split()).strip().strip('"«»')
    if len(text) > 320:
        text = text[:317].rstrip() + "…"

    if use_cache and text:
        _cache_put(key, text)
    return text


def brain_status() -> dict[str, Any]:
    """Which brain is active — shown by `python -m matchzerobaran status`."""
    return {
        "provider": (
            "gemini"
            if config.GEMINI_API_KEY
            else ("groq" if config.GROQ_API_KEY else "template (offline, zero-key)")
        ),
        "gemini_model": config.GEMINI_MODEL if config.GEMINI_API_KEY else None,
        "groq_model": config.GROQ_MODEL if config.GROQ_API_KEY else None,
        "telegram": bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID),
        "supabase": bool(config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY),
        "lang": config.LANG,
        "top_k": config.TOP_K,
    }