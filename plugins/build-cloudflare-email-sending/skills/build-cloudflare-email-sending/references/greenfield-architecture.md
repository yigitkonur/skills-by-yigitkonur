# Greenfield: architecting transactional email on Cloudflare Email Service

Starting fresh (no provider to migrate from), design around three axes:
where the senders run, how traffic classes split, and what happens at the
quota ceiling.

## Topology decision

- **Everything on Workers** → use the `send_email` binding directly in the
  Worker that owns the flow. No relay, no secrets. Bind once:
  `"send_email": [{"name": "EMAIL"}]` in wrangler.jsonc.
- **Backend elsewhere (or mixed)** → deploy ONE email-sender Worker
  (`assets/email-sender-worker/`) as the org-wide send gateway. Every
  backend posts to it with its own bearer secret. Centralizes quota
  visibility, template-agnostic, and keeps Cloudflare credentials out of
  every backend.
- **Legacy/SMTP-only components** → point them at
  `smtp.mx.cloudflare.net:465` with an Email Sending: Edit token. Same
  pipeline, same quota.

## Domain layout

Onboard **subdomains per traffic class**, not one root sender:

```
transactional.example.com   → password resets, receipts, verification
notifications.example.com   → product activity digests
```

Each onboards independently (`wrangler email sending enable
notifications.example.com`) with its own DKIM/bounce records — reputation
damage in one class doesn't poison the others. Marketing/bulk mail does not
belong on Email Service at all (transactional-only product; use a bulk ESP).

Keep `_dmarc` at the root aligned (`p=none` to start, tighten to
`quarantine` once placement is proven). If any other sender shares the root
domain, merge all `include:` mechanisms into ONE root SPF record.

## Templates and rendering

Render templates in your application (or the sender Worker) — Email Service
is transport-only, no hosted templates. A pure-function template module
(input → `{subject, html, text}`) keeps rendering unit-testable and the
Worker dumb. Always send both `html` and `text` parts; spam filters weigh
their presence.

## Capacity plan (do this on day one)

- Default quota ≈ 1,000 sends/day; included volume 3,000/month on Workers
  Paid, then $0.35/1k. Poll `GET /accounts/{id}/email/sending/limits` for
  live `quota` + `usage`.
- Projected > 1,000/day → file the limit-increase form immediately;
  practitioner reports say raises are slow and grudging. If the answer is
  no, the fallback architecture is CF-first with an SES/Postmark overflow
  provider behind the same routing function.
- Sends return `{delivered[], queued[], permanent_bounces[]}` — treat
  `queued` as success, `permanent_bounces` as a signal to stop mailing that
  address (repeats trigger auto-suppression that only support can undo).

## Observability

- Log the returned `message_id` with your own correlation id on every send.
- The dashboard's Email Routing panel miscounts Worker sends as "dropped" —
  known false-negative; alert off your own logs, not that panel.
- Wire a daily quota check (usage vs quota) into whatever heartbeat
  monitoring exists; hitting the ceiling silently 429s every send.

## Beta posture

Email Service is open beta: no public deliverability history, API surface
may shift, DKIM rotation requires a support ticket. For a product where
email is mission-critical from day one, run CF as primary with a configured
fallback provider for the first quarter — the routing-function pattern makes
that a two-env-var switch, not a rewrite.
