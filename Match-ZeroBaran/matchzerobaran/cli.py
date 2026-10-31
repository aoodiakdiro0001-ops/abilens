"""Command line interface — the same entry point used locally and in CI."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from typing import Any

from . import __version__, config
from .brain import brain_status
from .delivery import build_digest, send_digest
from .engine import MatchEngine
from .ingest import ingest, load_all
from .recommend import recommend_for_customer, recommend_for_product, refresh
from .store import open_store


def _print_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("لا توجد نتائج. / No results.")
        return
    for i, r in enumerate(rows, 1):
        price = r.get("price") or 0
        symbol = {"USD": "$", "TRY": "₺"}.get(r.get("currency", "USD"), "")
        price_line = f" {symbol}{price:g}" if price else ""
        print(f"{i:>2}. {r.get('name')} [{r.get('category')}]{price_line}  score={r.get('score')}")
        print(f"    ↳ {r.get('reason_text')}")
        print(f"    ↳ {r.get('pitch')}")
        if r.get("url"):
            print(f"    🔗 {r.get('url')}")


# --------------------------------------------------------------------------- #
def cmd_init(args: argparse.Namespace) -> int:
    store = open_store()
    counts = ingest(store, args.data)
    print("✅ Match-ZeroBaran initialised")
    for name, n in counts.items():
        print(f"   • {name}: {n}")
    print(f"   store → {config.STORE_DIR}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    store = open_store()
    counts = ingest(store, args.data)
    print(json.dumps(counts, ensure_ascii=False))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    store = open_store()
    data = load_all(store)
    if not data["products"]:
        print("⚠️ المتجر فارغ — شغّل: python -m matchzerobaran init", file=sys.stderr)
        return 2
    eng = MatchEngine(data["products"], data["orders"], data["events"])

    if args.product:
        rows = recommend_for_product(store, args.product, eng=eng, k=args.k, lang=args.lang, with_pitch=not args.raw)
        subject = args.product
    else:
        rows = recommend_for_customer(store, eng=eng, customer_id=args.customer, k=args.k, lang=args.lang, with_pitch=not args.raw)
        subject = args.customer or (data["customers"][0]["id"] if data["customers"] else "-")

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"🎯 {len(rows)} توصية · {subject}")
        _print_rows(rows)

    if args.notify:
        names = {c["id"]: c.get("name", c["id"]) for c in data["customers"]}
        ok = send_digest(rows, customer_name=names.get(subject, subject), lang=args.lang or config.LANG)
        print(f"📨 telegram: {'sent' if ok else 'skipped (no token configured)'}")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    store = open_store()
    if not load_all(store)["products"]:
        print("⚠️ no products in store", file=sys.stderr)
        return 2
    info = refresh(store, k=args.k, lang=args.lang)
    print(f"✅ refreshed {info['rows']} rows for {info['customers']} customers → {info['path']}")
    if args.notify:
        print(f"📨 telegram: {'sent' if send_digest(json.load(open(info['path'], encoding='utf-8'))) else 'skipped'}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    store = open_store()
    data = load_all(store)
    orders, products = data["orders"], {p["id"]: p for p in data["products"]}
    revenue = sum(float(o.get("total") or 0) for o in orders)
    aov = revenue / len(orders) if orders else 0
    units: Counter = Counter()
    money: Counter = Counter()
    for o in orders:
        for it in o.get("items", []):
            pid = it.get("product_id")
            units[pid] += int(it.get("qty", 1) or 1)
            money[pid] += float(it.get("qty", 1)) * float(it.get("price", 0) or 0)

    eng = MatchEngine(data["products"], data["orders"], data["events"])
    lines = [
        f"📊 تقرير المبيعات — {len(orders)} طلب · {len(data['customers'])} عميل · {len(products)} منتج",
        f"   الإيراد: {revenue:,.2f} USD · متوسط السلة (AOV): {aov:,.2f} USD",
        "",
        "🏆 الأعلى إيراداً:",
    ]
    for pid, amt in money.most_common(5):
        name = products.get(pid, {}).get("name", pid)
        lines.append(f"   • {name}: {amt:,.2f} USD ({units[pid]} وحدة)")
    lines.append("")
    lines.append("🔗 أكثر ثنائيات الشراء المتقاطع (lift):")
    for a, b, lift, times in eng.pair_table(5):
        lines.append(
            f"   • {products.get(a, {}).get('name', a)} + {products.get(b, {}).get('name', b)} "
            f"→ lift {lift} ({times} مرات)"
        )
    print("\n".join(lines))
    if args.json:
        print(
            json.dumps(
                {"orders": len(orders), "revenue": revenue, "aov": aov, "pairs": eng.pair_table(10)},
                ensure_ascii=False,
                indent=1,
            )
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    store = open_store()
    data = load_all(store)
    info = brain_status()
    print(f"Match-ZeroBaran v{__version__}")
    print(f"   brain provider : {info['provider']}")
    print(f"   language       : {info['lang']} · top_k={info['top_k']}")
    print(f"   telegram       : {'configured' if info['telegram'] else 'not configured'}")
    print(f"   supabase sync  : {'configured' if info['supabase'] else 'local JSON store'}")
    print(
        "   store          : "
        + ", ".join(f"{k}={len(v)}" for k, v in data.items())
    )
    print(f"   store path     : {config.STORE_DIR}")
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    store = open_store()
    rows = recommend_for_customer(store, customer_id=args.customer, k=args.k, lang=args.lang)
    print(build_digest(rows, customer_name=args.customer or "", lang=args.lang or config.LANG))
    return 0


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="matchzerobaran",
        description="Match-ZeroBaran — محرك التوصيات والتخصيص والبيع المتقاطع (موارد مجانية 100%)",
    )
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command")

    def common(sp):
        sp.add_argument("--lang", choices=["ar", "en"], default=None, help="ar | en (default from env)")
        sp.add_argument("-k", "--top-k", dest="k", type=int, default=None, help="number of recommendations")

    sp = sub.add_parser("init", help="(seed the local store from data/*.csv)")
    sp.add_argument("--data", default=None)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("ingest", help="reload CSV sources into the store")
    sp.add_argument("--data", default=None)
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("recommend", help="recommendations for a customer or a product")
    sp.add_argument("--customer", default=None, help="customer id (default: first customer)")
    sp.add_argument("--product", default=None, help="cross-sell from a product instead")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--raw", action="store_true", help="skip AI copywriting (template only)")
    sp.add_argument("--notify", action="store_true", help="send the digest to Telegram")
    common(sp)
    sp.set_defaults(func=cmd_recommend)

    sp = sub.add_parser("refresh", help="rebuild every customer's recommendation matrix (CI cron)")
    sp.add_argument("--notify", action="store_true")
    common(sp)
    sp.set_defaults(func=cmd_refresh)

    sp = sub.add_parser("report", help="sales, AOV and top cross-sell pairs")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("status", help="which brain/provider is active")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("digest", help="print a Telegram-ready digest")
    sp.add_argument("--customer", default=None)
    common(sp)
    sp.set_defaults(func=cmd_digest)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not getattr(args, "command", None):
        build_parser().print_help()
        return 0
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())