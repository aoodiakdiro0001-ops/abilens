# 🎯 Match-ZeroBaran — حزمة بيع Gumroad جاهزة للنشر

> الصق هذا النص كما هو داخل نموذج منتج Gumroad.
> السعر المقترح: **$29** (قيمة مقابل اشتراك أدوات تكلف 500$ سنوياً).

---

## Title (العنوان)

**Match-ZeroBaran — محرك توصيات وبيع متقاطع كامل بموارد مجانية 100%**

## Tagline (سطر واحد)

نظام مستقل لتحليل سلوك عملائك وتقديم توصيات مخصّصة ترفع متوسط قيمة السلة — دون دفع سنت واحد لأي أداة مدفوعة.

## Description (الوصف)

### 🔓 خلّص محرك توصياتك من اشتراكات شهرية مكلفة

كل شهر تدفعين/تدفع لمزوّد "توصيات ذكية" 30$… 500$… وأنت لا تملك بياناتك ولا تحكم بخوارزمياتك.
**Match-ZeroBaran** ينفّذ العمل نفسه — احترافياً — بصفر تكلفة تشغيل:

* **اشتريت X غالباً ما يناسبه Y** — سلال تسوق حقيقية (Market Basket + Lift)، لا تخمين.
* **بدائل دقيقة** — Cosine Similarity على TF‑IDF لوصف منتجاتك ووسومها.
* **صياغة تسويقية بالذكاء الاصطناعي** — Gemini/Groq مجاناً، ومعهما بديل قوالب عربي/إنجليزي يعمل بلا مفاتيح أبداً.
* **تسليم فوري** — خلاصة تليجرام لكل عميل أو تاجر + لوحة Streamlit لمراقبة AOV وأزواج الشراء.
* **جدولة ذاتية** — GitHub Actions يعيد بناء المصفوفة كل 6 ساعات ويرفع النتيجة Artifact.

### 📦 ما الذي تحصل عليه؟

```
matchzerobaran/     5 وحدات: config · ingest · engine · brain · recommend · delivery · cli
dashboard/app.py    لوحة تحكم Streamlit كاملة (KPIs · توصيات · أزواج الشراء)
.github/workflows/  جدولة CI مجانية كل 6 ساعات + اختبارات
data/               بيانات تجريبية جاهزة (12 منتج · 20 طلب · 8 عملاء) + دليل التنسيق
tests/              3 حزم اختبارات (unittest) تمر بلا إنترنت
docs/               ARCHITECTURE · STACK · SUPABASE · API · DEPLOY
cover/              صورة توثيقية + سكربت توليدها (PNG 1600×1000)
README · LICENSE · NOTICE
```

### ⚡ ابدأ خلال 60 ثانية

```bash
pip install -r requirements.txt
python -m matchzerobaran init
python -m matchzerobaran recommend --customer C001 -k 3
```

### 🛠️ الموارد المجانية المستخدمة (100%)

| الطبقة | المورد |
|---|---|
| الجدولة | GitHub Actions (مجاني) |
| الرياضيات | Python + NumPy + scikit-learn (مفتوح المصدر) |
| القاعدة السحابية | Supabase PostgreSQL + pgvector — خطة مجانية (اختياري) |
| الذكاء الاصطناعي | Google Gemini + Groq — طرفات مجانية + بديل قوالب |
| التسليم | Telegram Bot API |
| الواجهة | Streamlit |

### 🔒 خصوصيتك أولاً

سجلات مشتريات عملائك لا تغادر جهازك أبداً — المخزن المحلي JSON هو الافتراضي.
فعِّل Supabase فقط إن أردت، وبياناتك في قاعدتك أنت.

### 🧪 جاهز ومجتاز

اختبارات آلية (اختبار المحرك، التوصيات، الواجهة، التسليم) تمر قبل كل نشر في CI.

---

## Tags

```
recommendation-engine, cross-sell, upsell, ecommerce, python, scikit-learn, ai, telegram-bot, streamlit, supabase, free-tier, aov, market-basket, tfidf, arabic
```

## Category

`Software & Apps` → `Business & Marketing`

## Pricing

* **Regular license: $29**
* Suggested tier 2 (Team): **$79** — يشمل ملف تنسيق بيانات متجرك و3 تحديثات
* Suggested tier 3 (Commercial + Support): **$149** — دعم بريد أولوية + مكالمة تهيئة 45 دقيقة

## Cover image

استخدم `cover/cover.png` المرفق (1600×1000).

## Content warning / ⚖️ تنبيه

يُمنع إعادة بيع الكود كاملاً أو إعادة تسميته أو توزيعه كمنتج مستقل.
المشتري获得了 رخصة استخدام غير حصرية داخل مشاريعه الخاصة والتجارية، مع الاحتفاظ
ب حقوق المؤلف: © 2026 Baran Avisat.

## Support (قسم الدعم — اتركه كما هو)

* المؤلف: **Baran Avisat**
* البريد: **baranavisat@gmail.com**
* واتساب: **00905313263722**
* الرد خلال 48 ساعة · تحديثات مجانية مدى الحياة للإصدار 1.x

## Refund policy

بما أن المنتج رقمي فوري التسليم، لا استرجاع بعد التنزيل — لكن إن واجهت مشكلة
تقنية ولم تُحل خلال 7 أيام، راسلني وسأعيد المبلغ كاملاً.

---

### ✅ قائمة تحقق قبل النشر على Gumroad

- [ ] ارفع `cover/cover.png` كصورة الغلاف
- [ ] الصق الـ Description أعلاه
- [ ] أضف 15 وسم
- [ ] اضبط السعر $29 + تايرين إضافيين
- [ ] فعّل "Receive files by email" لتسليم ZIP
- [ ] اربط روابط الدعم (البريد + واتساب)
- [ ] اختبر الشراء بنفسك بمنتج مجاني (GUMROAD يسمح بـ "I want this" بسعر 0 للاختبار)