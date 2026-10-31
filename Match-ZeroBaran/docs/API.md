# واجهة برمجة التطبيقات (HTTP API)

النظام يُستدعى كأمر سطر أو كخدمة صغيرة. ارفع خادماً بسطرين:

```bash
pip install fastapi uvicorn     # مجاني بالكامل
```

```python
# api.py
from fastapi import FastAPI
from matchzerobaran.store import open_store
from matchzerobaran.recommend import recommend_for_customer, recommend_for_product

app = FastAPI(title="Match-ZeroBaran", version="1.0.0")

@app.get("/recommend/{customer_id}")
def recommend(customer_id: str, k: int = 3, lang: str = "ar"):
    return recommend_for_customer(open_store(), customer_id=customer_id, k=k, lang=lang)

@app.get("/cross-sell/{product_id}")
def cross_sell(product_id: str, k: int = 3, lang: str = "ar"):
    return recommend_for_product(open_store(), product_id, k=k, lang=lang)
```

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
# http://localhost:8000/recommend/C001?k=3
```

## تكامل مع متجرك (أي منصة)

عند كل عملية شراء أو عرض منتج، اضغط نقطة الاستعلام:

```python
import requests
recos = requests.get(
    "http://127.0.0.1:8000/recommend", params={"customer_id": cid, "k": 3},
    timeout=5,
).json()
```

أو من داخل نفس المستودع بايثون مباشرة (دون خادم):

```python
from matchzerobaran.store import open_store
from matchzerobaran.recommend import recommend_for_customer

rows = recommend_for_customer(open_store(), customer_id="C001", k=3)
for r in rows:
    print(r["name"], "—", r["pitch"])
```

---
© 2026 Baran Avisat · baranavisat@gmail.com · WhatsApp 00905313263722