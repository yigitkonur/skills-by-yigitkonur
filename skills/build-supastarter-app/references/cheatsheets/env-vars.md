# Environment Variables Quick Reference

> Condensed table of all environment variables. For detailed descriptions, see `references/setup/environment-setup.md`.

## Required for Local Development

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/supastarter` |
| `BETTER_AUTH_SECRET` | Any 32+ char secret (`openssl rand -base64 32`) |
| `EMAIL_FROM` | `noreply@localhost` |
| `S3_ENDPOINT` | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | `minioadmin` |
| `NEXT_PUBLIC_AVATARS_BUCKET_NAME` | `avatars` |

## Required for Production

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_SITE_URL` | Your app's public URL |
| `DATABASE_URL` | Production PostgreSQL URL |
| `BETTER_AUTH_SECRET` | Production auth secret |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `NEXT_PUBLIC_PRICE_ID_PRO_MONTHLY` | Stripe price ID |
| `NEXT_PUBLIC_PRICE_ID_PRO_YEARLY` | Stripe price ID |
| `NEXT_PUBLIC_PRICE_ID_LIFETIME` | Stripe price ID |
| `EMAIL_FROM` | Production sender email |
| One mail provider key | e.g. `RESEND_API_KEY` |

## Optional: OAuth

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `GITHUB_CLIENT_ID` | GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth |

## Optional: Analytics

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_PIRSCH_CODE` | Pirsch |
| `NEXT_PUBLIC_PLAUSIBLE_URL` + `_DOMAIN` | Plausible |
| `NEXT_PUBLIC_MIXPANEL_TOKEN` | Mixpanel |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | Google Analytics |
| `NEXT_PUBLIC_UMAMI_URL` + `_WEBSITE_ID` | Umami |
| `NEXT_PUBLIC_POSTHOG_KEY` + `_HOST` | PostHog |

## Optional: AI

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API |

## Client vs Server

> ⚠️ **Steering:** Never put secrets in `NEXT_PUBLIC_*` variables. These are bundled into client JavaScript and visible in the browser source.

- **`NEXT_PUBLIC_*`** → Bundled in client JavaScript, visible in browser
- **No prefix** → Server-only, never exposed to client

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `undefined` in browser | Missing `NEXT_PUBLIC_` prefix |
| `undefined` on server | Not in `.env.local` or Vercel env vars |
| Works locally, fails in prod | Env var not set in deployment platform |
| Stale value after change | Restart `pnpm dev` or redeploy |

---

**Related references:**
- `references/setup/environment-setup.md` — Full env var documentation with descriptions
- `references/deployment/vercel.md` — Setting env vars on Vercel
