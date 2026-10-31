# Stack decision log — why every piece is free

| Layer | Choice | Free allowance | Why not the paid alternative |
|---|---|---|---|
| Scheduler | GitHub Actions (public repo) | 2,000 min/month, unlimited cron on public repos | No need for a $5/mo VPS cron |
| Math core | Python + NumPy + scikit-learn | Apache-2.0, runs anywhere | No "AI recommender" SaaS at $99/mo |
| Persistence | Local JSON store (default) | ∞ | Zero setup; works offline & air-gapped |
| Cloud vector DB | Supabase (PostgreSQL + pgvector) | 500 MB free tier, REST API | SDK-free REST keeps dependencies thin |
| Copywriting | Gemini free tier → Groq free tier → templates | generous RPM free tiers | Template fallback = never blocked, never billed |
| Delivery | Telegram Bot API | free forever | Push infra would cost money |
| UI | Streamlit | free, local | No hosted dashboard bill |
| Storage of secrets | GitHub Actions Secrets / `.env` (git-ignored) | free | keys never touch the code |

## Cost math

* Paid recommendation suites: **$30–$500 / month** per store.
* Match-ZeroBaran: **$0 / month**, forever, including the AI copy.
* If you exceed free tiers, the system degrades gracefully (template brain,
  local store) instead of failing.

## Security posture

1. Secrets live only in `.env` (ignored) or GitHub Actions **Secrets**.
2. Service keys are server-side only; the dashboard and Telegram layer never see them.
3. `data/store/` and `data/cache/` are git-ignored — customer data never leaves your machine unless you opt into Supabase sync.

---
© 2026 Baran Avisat · baranavisat@gmail.com · WhatsApp 00905313263722