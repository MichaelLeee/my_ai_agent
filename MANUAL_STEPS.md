# Manual setup steps for my_ai_agent

The generator created the code. These are the **one-time external setup steps**
that can't be automated — accounts to create, keys to copy, services to provision.

> Skip ahead to "After every deploy" at the bottom for things you'll re-do
> regularly. Items above are one-time per environment.

---

## Secrets

```bash
cp backend/.env.example backend/.env
```

Then in `backend/.env`:

- [ ] **`SECRET_KEY`** — replace with a fresh value: `openssl rand -hex 32`
- [ ] **`API_KEY`** — replace with a fresh value: `openssl rand -hex 32`

These are used to sign JWTs and authenticate service-to-service calls. Rotate at every environment promotion (dev → staging → prod each get their own).


## PostgreSQL

- [ ] Provision a PostgreSQL ≥ 14 instance (local: `docker compose up -d db`; managed: Neon / Supabase / RDS / Cloud SQL).
- [ ] Set `DATABASE_URL` in `.env` to the **async** connection string: `postgresql+asyncpg://user:pass@host:5432/dbname`.
- [ ] Run migrations: `cd backend && uv run alembic upgrade head`.

## Anthropic

- [ ] Create API key at https://console.anthropic.com/.
- [ ] Set `ANTHROPIC_API_KEY` in `.env`.

## RAG (pgvector)

- [ ] Run `CREATE EXTENSION vector;` against your Postgres database (already added to migration `0007`).

- [ ] (Optional) Ingest seed documents: `uv run my_ai_agent rag-ingest /path/to/file.pdf --collection docs`.

## Redis

- [ ] Local: `docker compose up -d redis` (already in compose file).
- [ ] Managed: Upstash / Redis Cloud / ElastiCache. Set `REDIS_URL` in `.env`.

## Stripe billing

- [ ] Create account at https://dashboard.stripe.com/.
- [ ] Get API keys (Developers → API keys): set `STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY` in `.env`.
- [ ] Create products + prices in Stripe Dashboard, then sync IDs to seed migration or your `plans` table.
- [ ] Set up webhook endpoint:
  - Endpoint URL: `https://your-backend/api/v1/billing/webhook`
  - Events: `checkout.session.completed`, `customer.subscription.{created,updated,deleted}`, `invoice.{paid,payment_failed}`, `payment_intent.succeeded`
  - Copy signing secret → set `STRIPE_WEBHOOK_SECRET` in `.env`.
- [ ] Test via Stripe CLI: `stripe listen --forward-to localhost:8080/api/v1/billing/webhook`.

## Logfire (Pydantic observability)

- [ ] Create account at https://logfire.pydantic.dev.
- [ ] Run `uv run logfire auth` once locally to bootstrap.
- [ ] Get write token → set `LOGFIRE_TOKEN` in `.env` for non-local environments.

---

## After every deploy

- [ ] Run database migrations: `alembic upgrade head` (CI step or post-deploy job).
- [ ] Smoke test `/api/v1/health` returns `{"status": "ok"}`.
- [ ] Frontend loads, login → dashboard flow works.
- [ ] Stripe webhook delivers (check Stripe Dashboard → Developers → Webhooks → recent deliveries).
- [ ] Logs flowing to your aggregator.

---

## Where to find more

- `ENV_VARS.md` — exhaustive env var reference
- `docs/deploy.md` — platform-specific deployment recipes
- `SECURITY.md` — security model + production hardening checklist
- `CONTRIBUTING.md` — dev environment setup
- `docs/architecture.md` — codebase layered architecture rules
