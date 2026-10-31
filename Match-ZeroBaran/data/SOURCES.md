# بيانات المتجر — Data sources

ضع هنا ملفاتك الحقيقية بنفس الأسماء والصيغة، وسيعمل النظام دون أي تعديل على الكود.

| الملف | الصيغة | مطلوب؟ |
|---|---|---|
| `products.csv` | `id,name,category,tags,price,currency,description,url` | ✅ نعم |
| `orders.csv` | `order_id,customer_id,ts,product_id,qty,price` (سطر لكل منتج داخل الطلب) | ✅ نعم |
| `customers.csv` | `id,name,city,lang,tier` | اختياري |
| `events.csv` | `customer_id,product_id,type,ts` حيث `type` ∈ `view\|cart\|purchase` | اختياري |

## ملاحظات مهمة

- **long format**: كل صنف داخل الطلب يأخذ سطراً مستقلاً بنفس `order_id` — هكذا يحسب المحرك سلال التسوق (market basket).
- **latin-only**: العمود `id` يجب أن يكون بالحروف اللاتينية/الأرقام.
- الملفات المرفقة هي **بيانات تجريبية** للعرض والاختبار؛ استبدلها ببيانات متجرك قبل التشغيل.
- النسخ الاحتياطي يتجاهل `data/store/` و`data/cache/` (مخرجات مولّدة).

## استيراد بياناتك مباشرة من GitHub Actions (بدون رفع ملفات)

يمكنك وضع نص CSV كامل داخل أسرار المستودع باسم `PRODUCTS_CSV` و`ORDERS_CSV`
فإن ملفات المصدر تُستبدل تلقائياً قبل كل تشغيل مجدول — دون أن تُرفع بياناتك إلى المستودع إطلاقاً.

---
© Baran Avisat · baranavisat@gmail.com · واتساب 00905313263722