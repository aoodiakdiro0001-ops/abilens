# إعداد Supabase (اختياري — الطبقة السحابية)

النظام يعمل **كامل بلا Supabase** بالمخزن المحلي. أضف Supabase فقط إن أردت
متجهات سحابية واستعلامات فورية لأكثر من متجر.

## 1) أنشئ المشروع مجاناً

1. سجّل في <https://supabase.com> → **New project** (الخطة Free تكفي).
2. انسخ **Project URL** و **service_role key** (وليس anon key).

## 2) جهّز الجداول ومفتاح التشابه

```sql
-- جداول البيانات الأساسية
create table if not exists products (
  id text primary key,
  name text, category text, tags text,
  price numeric, currency text, description text, url text
);
create table if not exists customers (
  id text primary key, name text, city text, lang text, tier text
);
create table if not exists orders (
  id text primary key, customer_id text, ts timestamptz,
  items jsonb, total numeric
);
create table if not exists events (
  customer_id text, product_id text, type text, ts timestamptz
);

-- مصفوفة التوصيات المولّدة
create table if not exists recommendations (
  customer_id text, product_id text, name text, category text,
  price numeric, currency text, url text,
  score real, reason text, reason_text text, pitch text,
  anchor_id text, anchor_name text, generated_at timestamptz
);

-- pgvector: التضمينات الدلالية
create extension if not exists vector;
create table if not exists product_embeddings (
  product_id text primary key,
  embedding vector(384)   -- dim = طول متجه التضمين الذي تولّده
);
create index on product_embeddings
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);
```

## 3) ضبط متغيّرات البيئة

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...        (service_role — يبقى في السيرفر فقط)
```

في GitHub: **Settings → Secrets and variables → Actions → New repository secret**
لكل اسم. ومحلياً: ضعها في `.env` (مُهمل في git).

## 4) الإشعارات الفورية (Triggers)

```sql
create or replace function notify_recommendations() returns trigger as $$
begin
  perform pg_notify('recos', json_build_object(
    'customer_id', new.customer_id, 'product_id', new.product_id)::text);
  return new;
end; $$ language plpgsql;

create trigger trg_reco after insert on recommendations
for each row execute function notify_recommendations();
```

## 5) التحقق

```bash
python -m matchzerobaran refresh
python -m matchzerobaran status     # supabase: configured ✅
```

إن فشل الاتصال يبقى المخزن المحلي سليماً — لا يفشل التنفيذ أبداً بسبب السحابة.

---
© 2026 Baran Avisat · baranavisat@gmail.com · WhatsApp 00905313263722