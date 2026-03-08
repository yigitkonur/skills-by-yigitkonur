# Environment Setup

> Complete guide to every environment variable in the Supastarter project. Consult this when setting up a new environment, debugging missing config, or adding a new provider integration.

## Prerequisites

- **Node.js** ≥ 20
- **pnpm** 10.28.2 (enforced via `packageManager` in root `package.json`)
- **Docker** (for local PostgreSQL + MinIO)

## Quick Start

```bash
# 1. Install dependencies
pnpm install

# 2. Start database and S3 (PostgreSQL 16 + MinIO)
docker compose up -d

# 3. Copy environment template
cp .env.local.example .env.local

# 4. Generate Prisma client + push schema
pnpm generate
pnpm db:push

# 5. Start dev server
pnpm dev
```

## Docker Services

The `docker-compose.yml` provides two services:

```yaml
# PostgreSQL 16 Alpine
postgres:
  image: postgres:16-alpine
  ports: ["5432:5432"]
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: supastarter
  volumes: ["postgres-data:/var/lib/postgresql/data"]

# MinIO (S3-compatible storage)
minio:
  image: minio/minio
  ports: ["9000:9000", "9001:9001"]  # API + Console
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin

# Auto-creates "avatars" bucket with public download policy
minio-setup:
  image: minio/mc
  depends_on: [minio]
  # Sets alias, creates bucket, sets anonymous download policy
```

## Environment Variables Reference

### Core Application

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SITE_URL` | Production | Public URL of the app (e.g. `https://myapp.com`) |
| `NEXT_PUBLIC_VERCEL_URL` | Auto | Set by Vercel on preview deployments |
| `PORT` | No | Dev server port (defaults to 3000) |
| `NEXT_PUBLIC_DOCS_URL` | No | External documentation URL |

### Database

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |

Local default: `postgresql://postgres:postgres@localhost:5432/supastarter`

### Authentication

| Variable | Required | Description |
|----------|----------|-------------|
| `BETTER_AUTH_SECRET` | Yes | Secret for signing session cookies (generate with `openssl rand -base64 32`) |
| `GOOGLE_CLIENT_ID` | For OAuth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For OAuth | Google OAuth client secret |
| `GITHUB_CLIENT_ID` | For OAuth | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | For OAuth | GitHub OAuth client secret |

### Mail Providers (pick one)

| Variable | Required | Description |
|----------|----------|-------------|
| `RESEND_API_KEY` | For Resend | Resend API key |
| `POSTMARK_SERVER_TOKEN` | For Postmark | Postmark server token |
| `MAILGUN_API_KEY` | For Mailgun | Mailgun API key |
| `MAILGUN_DOMAIN` | For Mailgun | Mailgun sending domain |
| `PLUNK_API_KEY` | For Plunk | Plunk API key |
| `SMTP_HOST` | For Nodemailer | SMTP server host |
| `SMTP_PORT` | For Nodemailer | SMTP port |
| `SMTP_USER` | For Nodemailer | SMTP username |
| `SMTP_PASSWORD` | For Nodemailer | SMTP password |
| `EMAIL_FROM` | Yes | Sender email address |

### Payment Providers

**Stripe (default):**

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `NEXT_PUBLIC_PRICE_ID_PRO_MONTHLY` | Yes | Stripe price ID for Pro monthly |
| `NEXT_PUBLIC_PRICE_ID_PRO_YEARLY` | Yes | Stripe price ID for Pro yearly |
| `NEXT_PUBLIC_PRICE_ID_LIFETIME` | Yes | Stripe price ID for lifetime |

**Alternative providers:** Lemonsqueezy, Creem, Polar, DodoPayments each have their own API key and webhook secret variables. See `.env.local.example` for the full list.

### Storage (S3-Compatible)

| Variable | Required | Description |
|----------|----------|-------------|
| `S3_ENDPOINT` | Yes | S3 endpoint URL (e.g. `http://localhost:9000`) |
| `S3_ACCESS_KEY_ID` | Yes | S3 access key |
| `S3_SECRET_ACCESS_KEY` | Yes | S3 secret key |
| `S3_REGION` | No | S3 region (defaults to `"auto"`) |
| `NEXT_PUBLIC_AVATARS_BUCKET_NAME` | Yes | Bucket name for avatar uploads |

### Analytics (all optional, pick any)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_PIRSCH_CODE` | Pirsch analytics code |
| `NEXT_PUBLIC_PLAUSIBLE_URL` | Plausible instance URL |
| `NEXT_PUBLIC_PLAUSIBLE_DOMAIN` | Plausible domain |
| `NEXT_PUBLIC_MIXPANEL_TOKEN` | Mixpanel project token |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | Google Analytics measurement ID |
| `NEXT_PUBLIC_UMAMI_URL` | Umami instance URL |
| `NEXT_PUBLIC_UMAMI_WEBSITE_ID` | Umami website ID |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog project API key |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog instance URL |

### AI

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For AI features | OpenAI API key |

## Client vs Server Variables

- **`NEXT_PUBLIC_*`** — Bundled into the client, visible in browser JavaScript
- **No prefix** — Server-only, never exposed to the client

Never put secrets (API keys, database URLs) in `NEXT_PUBLIC_*` variables.

---

**Related references:**
- `references/setup/monorepo-structure.md` — Project structure and Turbo pipeline
- `references/cheatsheets/env-vars.md` — Condensed env var quick-reference
- `references/deployment/vercel.md` — Vercel deployment and env var setup
