---
name: build-cloudflare-email-sending
description: "Use if sending email via Cloudflare Email Service, replacing Resend/SES/Postmark or send_email."
---

# Build Cloudflare Email Sending

Cloudflare Email Service (open beta since 2026-04) sends transactional email
through three equivalent paths — a Workers `send_email` binding, a REST API,
and SMTP — all sharing one pipeline, one quota, and automatic DKIM/ARC
signing. This skill gets a sending domain onboarded, picks the right send
path for the caller's architecture, and executes migrations from other
providers without breaking email mid-cutover.

## When to use

Use this skill if you are:

- Migrating transactional email off Resend, SES, Postmark, or SendGrid onto
  Cloudflare.
- Fixing Supabase Auth's rate-limited built-in mailer, or fully rebranding
  its signup/reset/magic-link emails.
- Wiring a `send_email` Workers binding, `wrangler email sending`, or a
  Worker relay for a backend that runs outside Cloudflare (Railway, Fly,
  Vercel, a VPS).
- Architecting transactional email from scratch for a stack already on
  Workers.
- Debugging `cf-bounce` DNS, DKIM/SPF conflicts, or Email Service quota
  errors.

This is the sending product (open beta, 2026) — not Email Routing/receiving,
not the retired MailChannels path.

## First: three facts that shape every decision

1. **The sending domain's DNS zone must be on Cloudflare.** Onboarding
   auto-creates bounce MX + SPF + DKIM + DMARC records; it cannot do that on
   external DNS. If the target domain's nameservers point elsewhere, either
   move the zone first or onboard a different Cloudflare-hosted domain as an
   interim sender (working substitute now beats perfect sender later — swap
   `from` when the zone moves).
2. **API-token creation is dashboard-gated; the Worker binding needs no token
   at all.** For backends running outside Cloudflare, the highest-leverage
   pattern is a tiny Worker relay: the Worker holds the `send_email` binding
   ambiently, the backend calls it over HTTPS with a shared random secret.
   No Cloudflare credential ever touches the backend.
3. **Quota starts at ~1,000 sends/day and Cloudflare raises it reluctantly**
   (practitioner reports: a $20-30k/mo account fought to get 5,000/day).
   3,000 sends/month included on Workers Paid ($5/mo floor), then $0.35/1k.
   If projected volume exceeds 1,000/day, file the limit-increase form at the
   start of the migration, not the end — treat it as a blocking dependency.

## Workflow

### 1. Verify tooling and account

```bash
wrangler --version          # need >= 4.110; older versions 404 on sending endpoints
wrangler whoami             # confirms login; note available account IDs
```

Multi-account logins fail non-interactively — export
`CLOUDFLARE_ACCOUNT_ID=<id>` before every `wrangler email` command. Find the
account that owns the target zone by probing:

```bash
CLOUDFLARE_ACCOUNT_ID=<id> wrangler email sending settings <domain>
# "Could not find a zone" → wrong account; repeat with the next id
```

### 2. Onboard the sending domain

```bash
dig +short NS <domain>      # *.ns.cloudflare.com → zone is on Cloudflare; else see fact 1
CLOUDFLARE_ACCOUNT_ID=<id> wrangler email sending enable <domain>
CLOUDFLARE_ACCOUNT_ID=<id> wrangler email sending dns get <domain>   # inspect what was created
```

`enable` auto-creates, on the `cf-bounce` subdomain: three bounce MX records,
an SPF TXT, a DKIM key at `cf-bounce._domainkey`, plus `_dmarc.<domain>`.
Verify propagation before the first send:

```bash
dig +short MX cf-bounce.<domain>
dig +short TXT cf-bounce._domainkey.<domain> | head -c 40
dig +short TXT _dmarc.<domain>
```

**SPF conflict rule:** if the *root* domain already has an SPF record from
another sender, Cloudflare's `include:_spf.mx.cloudflare.net` must be merged
into that one record — a second SPF TXT is invalid and tanks deliverability.
The `cf-bounce` records are namespaced and never conflict. Subdomains
(`notifications.<domain>`) onboard independently — use one per traffic class
for reputation isolation.

### 3. Pick the send path

| Caller | Path | Why |
|---|---|---|
| Code already on Workers | `send_email` binding | Zero credentials, zero HTTP hop |
| Backend outside Cloudflare (Railway/Fly/VPS/Vercel functions) | **Worker relay** (this skill's template) | Token creation is dashboard-gated; a shared secret to your own Worker is the only credential |
| Legacy app that only speaks SMTP | `smtp.mx.cloudflare.net:465`, user `api_token`, password = a token with **Email Sending: Edit** | No code changes |
| One-off / CI / smoke test | `wrangler email sending send --from ... --to ... --subject ... --text ...` | Fastest proof |

For the Worker relay: copy `assets/email-sender-worker/` into the repo (e.g.
`workers/email-sender/`), deploy, set the secret, verify:

```bash
cd workers/email-sender
CLOUDFLARE_ACCOUNT_ID=<id> npx wrangler deploy
openssl rand -hex 32 | CLOUDFLARE_ACCOUNT_ID=<id> npx wrangler secret put AUTH_TOKEN
# keep the generated value ONLY in the backend's secret store (env var / vault) — never in git
```

**The #1 API landmine:** the Workers binding's address-object shape is
`{email, name}` while the REST API's is `{address, name}`. The bundled
Worker template translates; hand-rolled code that passes `{address}` to the
binding fails with "Incorrect type for the 'email' field". The wrangler CLI
smoke-send accepts display strings (`"Name <addr@dom>"`).

### 4. Wire the application with a fallback window

Never hard-cut from the old provider. Route by config: prefer Cloudflare when
its env vars are set, fall back to the old provider otherwise — either
provider alone keeps email alive, and rollback is unsetting two vars. Keep
the old provider's fallback for 2–4 weeks of observed deliverability (the
product is beta; no public inbox-placement history exists yet).

Provider-specific mappings, DNS specifics, and code-shape diffs:

- Migrating **from Resend** (or SES/Postmark — same shape): read
  `references/migrate-from-resend.md`
- Replacing **Supabase Auth's built-in mailer** (confirmation, magic link,
  recovery emails): read `references/supabase-auth-emails.md`
- **Greenfield** — architecting email for a new product on Cloudflare:
  read `references/greenfield-architecture.md`

### 5. Verify end-to-end, then clean up

Every leg gets a live probe — a green deploy is not a delivered email:

```bash
# 1 Worker auth gate: wrong token must 401, missing config must 503
curl -s -X POST https://<worker>/send -H "Authorization: Bearer wrong" -d '{}' -o /dev/null -w "%{http_code}\n"
# 2 Real send returns a message_id
curl -s -X POST https://<worker>/send -H "Authorization: Bearer $EMAIL_SENDER_TOKEN" \
  -H "content-type: application/json" \
  -d '{"from":{"address":"welcome@<domain>","name":"Product"},"to":"<real inbox you control>","subject":"cutover probe","text":"probe"}'
# 3 The email actually lands in that inbox (check spam folder too)
# 4 The OLD provider's send log shows nothing new → traffic really moved
# 5 Quota headroom: GET /accounts/<id>/email/sending/limits (or the dashboard)
```

Delete any test users/rows the probes created. If probes sent to fake
addresses, expect them in `permanent_bounces` — repeated hard bounces
auto-suppress recipients, and unsuppression requires a Cloudflare support
case, so always probe with a real inbox you control.

## Credential hygiene (non-negotiable)

- The Worker `AUTH_TOKEN` lives in exactly two places: `wrangler secret` and
  the backend's secret store. Never in git, wrangler.jsonc, docs, or chat.
- Rotation is a paired operation: `wrangler secret put AUTH_TOKEN` + update
  the backend var in the same change window.
- SMTP-path tokens are real Cloudflare API tokens — scope to **Email
  Sending: Edit** only, nothing broader.
- When writing examples or reports, show `openssl rand -hex 32` as the
  generation step, never a literal value.

## Failure quick-reference

| Symptom | Cause | Fix |
|---|---|---|
| wrangler `email sending` → 404 | wrangler < 4.110 | `npm i -g wrangler@latest` |
| "More than one account available" | multi-account login | `CLOUDFLARE_ACCOUNT_ID=<id>` |
| "Incorrect type for the 'email' field" | REST shape sent to the binding | `{email}` for binding, `{address}` for REST |
| `E_SENDER_NOT_VERIFIED` | domain/subdomain not onboarded | `wrangler email sending enable` + DNS check |
| 429 / `E_RATE_LIMIT_EXCEEDED` | daily quota (default ~1,000) | limit-increase form; queue + retry with backoff |
| Lands in spam | DMARC alignment missing | verify `_dmarc` TXT exists; merged SPF on root |
| Recipient silently gets nothing | auto-suppressed after hard bounces | Cloudflare support case; stop probing fake addresses |
| Dashboard shows sends as "dropped" | known Email Routing metrics false-negative | trust the send response's `message_id`, not that panel |
