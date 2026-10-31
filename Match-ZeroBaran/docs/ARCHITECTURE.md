# البنية البرمجية — Software Architecture

```
                       ┌──────────────────────────────────────────┐
   عملية شراء / تصفح   │           data/*.csv  (المتجر)           │
   أو webhook          └───────────────┬──────────────────────────┘
                                       │  ingest()
                                       ▼
        ┌──────────────────────────────────────────────────────────────┐
        │ 1 · Ingestion & Similarity Core          matchzerobaran/     │
        │     pandas-grade normalization (csv)     ingest.py           │
        │     TF-IDF + Cosine similarity (سكايكرن) engine.py           │
        │     Market-basket lift  (سلال التسوق)                       │
        │     Category-affinity fallback (عند قلة البيانات)            │
        └───────────────┬──────────────────────────────┬───────────────┘
                        │ substitutes                  │ complements
                        ▼                              ▼
        ┌──────────────────────────────────────────────────────────────┐
        │ 2 · AI Matching Brain                        brain.py        │
        │     prompt ↔ Gemini (مجاني) ► Groq (مجاني) ► قوالب عربية     │
        │     كاش محلي يحمي الحصص المجانية · نص واحد لكل توصية         │
        └───────────────┬──────────────────────────────────────────────┘
                        │ rows
                        ▼
        ┌──────────────────────────────────────────────────────────────┐
        │ 3 · Persistence Layer                        store.py        │
        │     JSON store ذرّي (الافتراضي) · Supabase REST (اختياري)    │
        │     export → data/store/recommendations.json                │
        └───────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────────────────────────┐
        │ 4 · Delivery & Control     delivery.py · cli.py · dashboard/ │
        │     Telegram digest · Streamlit لوحة تحكم · GitHub Actions   │
        └──────────────────────────────────────────────────────────────┘
```

## الخوارزميات

### 1) التشابه (بدائل المنتجات — Substitutes)

يُبنى مستند لكل منتج من `name + name + category + tags + tags + description`
(التكرار يرفع وزن الحقول المفتاحية)، ثم `TfidfVectorizer` بـ `ngram_range=(1,2)`
والتقسيم الجذري `sublinear_tf`، ويحسب جيب التمام:

```
cos(u, v) = u·v / (‖u‖ ‖v‖)
```

الأعلى تشابهاً = البديل الأنسب: *«إذا أعجبك X فـ Y أقرب شيء إليه»*.

### 2) البيع المتقاطع (تكميل السلة — Complements)

```
lift(A,B) = P(A∩B) / (P(A)·P(B))        مُقصوص عند 6.0
```

تُرفض الأزواج الأقل من `MIN_CO_OCCURRENCE = 2` كضجيج إحصائي. سعر التكميل:

```
score = 0.45 · (lift/6) + 0.25 · affinity + 0.20 · cosine + 0.10 · popularity
```

### 3) دفء البدء (Cold start)

عميل بلا سجل → ترتيب بالشعبية (`popularity`). عميل بمشاهدة بلا شراء →
`affinity + cosine` فقط. لا يفشل التنفيذ أبداً.

### 4) سبب الاختيار (Reason code)

`basket | affinity | similar | popular` — يُختار بأكبر حدّ مرجّح، ويتحول إلى
جملة عربية/إنجليزية ثم يصاغ إعلانياً عبر العقل.

## قرارات التصميم

| القرار | السبب |
|---|---|
| REST بدل SDK لـ Supabase | تقليل الاعتماديات · قابلية النقل |
| مخزن JSON افتراضي | يعمل بلا إنترنت · سهل النسخ الاحتياطي · صفر إعداد |
| fallback قوالب | ضمان عمل النظام بلا مفاتيح وبلا اتصال |
| numpy fallback لـ scikit-learn | النظام لا يتعطل إن تعذّر تثبيت المكتبة |
| اختبارات بلا شبكة | أي مفتاح في بيئة الاختبار يُزال آلياً |
| أسرار خارج الكود | `.env` مُهمل · GitHub Secrets |

---
© 2026 Baran Avisat · baranavisat@gmail.com · WhatsApp 00905313263722