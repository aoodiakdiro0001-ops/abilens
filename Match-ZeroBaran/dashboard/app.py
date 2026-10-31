"""Match-ZeroBaran — Streamlit control room (free, runs locally).

    pip install streamlit && streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matchzerobaran import config  # noqa: E402
from matchzerobaran.brain import brain_status  # noqa: E402
from matchzerobaran.delivery import build_digest, telegram_send  # noqa: E402
from matchzerobaran.engine import MatchEngine  # noqa: E402
from matchzerobaran.ingest import load_all  # noqa: E402
from matchzerobaran.recommend import recommend_for_customer  # noqa: E402
from matchzerobaran.store import open_store  # noqa: E402

st.set_page_config(page_title="Match-ZeroBaran", page_icon="🎯", layout="wide")

AR = {"title": "🎯 Match-ZeroBaran — غرفة تحكم التوصيات", "pick": "اختر العميل", "go": "ولّد التوصيات", "send": "أرسل إلى تليجرام"}
EN = {"title": "🎯 Match-ZeroBaran — Recommendation Control Room", "pick": "Pick a customer", "go": "Generate", "send": "Send to Telegram"}


@st.cache_data(show_spinner=False)
def _data():
    store = open_store()
    return load_all(store)


data = _data()
lang = st.sidebar.radio("Language / اللغة", ["ar", "en"], index=0 if config.LANG == "ar" else 1)
ui = AR if lang == "ar" else EN
st.title(ui["title"])

if not data["products"]:
    st.warning("المخزن فارغ — شغّل أولاً: `python -m matchzerobaran init`" if lang == "ar" else "Store empty — run: `python -m matchzerobaran init`")
    st.stop()

products = {p["id"]: p for p in data["products"]}
eng = MatchEngine(data["products"], data["orders"], data["events"])

# --- KPIs ------------------------------------------------------------------ #
revenue = sum(float(o.get("total") or 0) for o in data["orders"])
aov = revenue / len(data["orders"]) if data["orders"] else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("الطلبات" if lang == "ar" else "Orders", len(data["orders"]))
c2.metric("العملاء" if lang == "ar" else "Customers", len(data["customers"]))
c3.metric("الإيراد $" if lang == "ar" else "Revenue $", f"{revenue:,.0f}")
c4.metric("متوسط السلة $" if lang == "ar" else "AOV $", f"{aov:,.0f}")

# --- recommendations -------------------------------------------------------- #
st.subheader("التوصيات الذكية" if lang == "ar" else "Smart recommendations")
customers = {c["id"]: f"{c.get('name', c['id'])} ({c['id']})" for c in data["customers"]}
if not customers:
    st.info("لا يوجد عملاء بعد." if lang == "ar" else "No customers yet.")
else:
    cid = st.selectbox(ui["pick"], list(customers), format_func=lambda i: customers[i])
    k = st.slider("عدد التوصيات" if lang == "ar" else "How many", 1, 8, config.TOP_K)
    if st.button(ui["go"], type="primary"):
        rows = recommend_for_customer(open_store(), eng=eng, customer_id=cid, k=k, lang=lang)
        for r in rows:
            with st.container(border=True):
                st.markdown(f"### {r['name']} · {r['currency']} {r.get('price') or 0:g}")
                st.caption(r.get("reason_text") or "")
                st.write(r.get("pitch") or "")
                if r.get("url"):
                    st.link_button("↗" if lang == "ar" else "Open", r["url"])
        digest = build_digest(rows, customer_name=customers[cid], lang=lang)
        with st.expander("معاينة رسالة تليجرام / Telegram preview"):
            st.code(digest, language="text")
        if st.button(ui["send"]):
            ok = telegram_send(digest)
            st.success("تم الإرسال ✅" if ok else "لم يُضبط TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")

# --- basket pairs ------------------------------------------------------------ #
st.subheader("أزواج الشراء المتقاطع" if lang == "ar" else "Top cross-sell pairs")
pairs = eng.pair_table(15)
if pairs:
    st.dataframe(
        [
            {
                "A": products.get(a, {}).get("name", a),
                "B": products.get(b, {}).get("name", b),
                "lift": lift,
                "together": c,
            }
            for a, b, lift, c in pairs
        ],
        use_container_width=True,
    )
else:
    st.info("لا توجد زوجيات كافية بعد (تحتاج طلبات مشتركة)." if lang == "ar" else "Not enough co-purchases yet.")

# --- status ------------------------------------------------------------------- #
status = brain_status()
st.caption(
    f"brain: {status['provider']} · lang: {status['lang']} · "
    f"telegram: {'✅' if status['telegram'] else '⛔'} · supabase: {'✅' if status['supabase'] else 'local'}"
)