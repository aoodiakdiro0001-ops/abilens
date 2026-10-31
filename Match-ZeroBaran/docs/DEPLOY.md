# دليل النشر — Deploy Anywhere (100% free)

## 1) GitHub (المصدر الأساسي)

```bash
git init && git add . && git commit -m "Match-ZeroBaran v1.0"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

ثم: **Settings → Secrets and variables → Actions** وأضف الأسرار (لا تكتبها في الكود):

| السرّ | متى تحتاجه |
|---|---|
| `GEMINI_API_KEY` أو `GROQ_API_KEY` | لتفعيل صياغة الذكاء الاصطناعي |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | لاستقبال الخلاصات |
| `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` | لمزامنة سحابية |
| `PRODUCTS_CSV` + `ORDERS_CSV` | لإمداد بياناتك دون رفع ملفات |

## 2) GitHub Actions (الجدولة المجانية)

يُفعَّل تلقائياً: `.github/workflows/refresh.yml`

* الجدولة: كل 6 ساعات (مجانية بلا حد على المستودعات العامة)
* التشغuel اليدوي: **Actions → Refresh recommendation matrices → Run workflow**
  (وأختر `notify: true` لإرسال الخلاصة إلى تليجرام)
* المخرج: Artifact `recommendations.json` يُحفظ 14 يوماً

## 3) Supabase (قاعدة البيانات السحابية)

اتبع [docs/SUPABASE.md](SUPABASE.md) — 5 دقائق، الخطة مجانية.

## 4) Streamlit Community Cloud (لوحة تحكم عامة، مجاناً)

1. ارفع المستودع إلى GitHub
2. <https://share.streamlit.io> → **New app** → اختر المستودع والملف `dashboard/app.py`
3. أضف المتغيّرات في **App settings → Secrets**:

```toml
GEMINI_API_KEY = "..."
TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID = "..."
```

> لا ترفع `data/store/` — الشريط الجانبي يعيد الاستيراد من `data/*.csv`.

## 5) خادم خفيف للـ API (Fly.io / Render / أي VPS)

اتبع [docs/API.md](API.md) ثم:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

الخطة المجانية على Render/Fly تكفي لأن الحمل خفيف جداً (استعلامات آنية فقط).

## 6) تليجرام

1. تحدث مع `@BotFather` → `/newbot` → انسخ التوكن
2. افتح بوتك وابعت `/start`
3. افتح `https://api.telegram.org/bot<TOKEN>/getUpdates` وخذ `chat.id`
4. ضع `TELEGRAM_BOT_TOKEN` و `TELEGRAM_CHAT_ID` في الأسرار

## 7) النشر المختصر

```bash
pip install -r requirements.txt
python -m matchzerobaran init
python -m matchzerobaran refresh        # بناء المصفوفة
python -m matchzerobaran digest         # معاينة الخلاصة قبل الإرسال
```

---
© 2026 Baran Avisat · baranavisat@gmail.com · WhatsApp 00905313263722