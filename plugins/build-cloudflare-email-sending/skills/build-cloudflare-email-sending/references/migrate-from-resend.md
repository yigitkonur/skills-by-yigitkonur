# Migrating from Resend (or SES / Postmark) to Cloudflare Email Service

The API shapes are close enough that migration is mostly a transport swap.
The work that actually takes time is DNS, the fallback window, and quota.

## Shape mapping

| Resend `POST /emails` | CF REST `POST /accounts/{id}/email/sending/send` | CF Worker binding `env.EMAIL.send()` |
|---|---|---|
| `from: "Name <a@d>"` (string) | `from: {address, name}` or string | `from: {email, name}` or string ← **different key** |
| `to: ["a@d"]` (array) | `to`: string, object, or array of either | `to`: string |
| `subject` | `subject` | `subject` |
| `html` / `text` | `html` / `text` (≥1 required) | `html` / `text` |
| `reply_to` | `reply_to` | `replyTo` |
| `attachments: [{filename, content}]` | `attachments: [{content(b64), filename, type, disposition}]` | same, max 32 |
| response `{id}` | response `result: {message_id, delivered[], queued[], permanent_bounces[]}` | returns `{messageId}` |

No idempotency-key support on the CF side (Resend has one) — if the caller
relied on it, dedupe at the application layer (e.g. a sent-log keyed on your
own message purpose + recipient).

## Migration sequence

1. **Onboard the CF sending domain first** (SKILL.md §2) while Resend keeps
   serving traffic. Nothing about onboarding disturbs existing senders —
   Cloudflare's records live on `cf-bounce.*`; only the root SPF needs a
   merge if the domain also sends via the old provider:
   `v=spf1 include:_spf.resend.com include:_spf.mx.cloudflare.net ~all`
   (one record, both includes — during the fallback window you legitimately
   send from both).
2. **Add config-routed sending** in the app: prefer CF when its vars are set
   (`EMAIL_SENDER_URL`/`EMAIL_SENDER_TOKEN` for the Worker relay, or the CF
   token for direct REST), else fall back to the existing Resend client.
   Extract the routing into one exported function so a unit test can pin it
   with a fake `fetch`: prefers CF, falls back, errors distinctly when
   neither is configured.
3. **Prove the negative**: after cutover, the old provider's send log
   (`GET https://api.resend.com/emails?limit=1`) must show *no new entries*
   while the app's sends succeed — that's the evidence traffic moved, not
   just that CF returns 200.
4. **Hold the fallback 2–4 weeks**, watching spam placement on Gmail/Outlook
   with real recipients. Then remove the old provider's key from the
   environment (leave the code path one more release before deleting).

## Gotchas specific to leaving Resend

- Resend's free tier allows 1 verified domain; a common migration driver is
  hitting that wall. Note the same class of ceiling exists on CF: ~1,000
  sends/day default, raised via form, slowly.
- Resend renders `"Name <a@d>"` from-strings; CF's Worker binding does too,
  but if you pass objects, remember the `{email}` vs `{address}` split.
- Resend delivers via Amazon SES infrastructure (message-ids show
  `amazonses.com`); CF is its own shared pool with no public reputation
  history — hence the fallback window rather than a hard cut.

## SES / Postmark deltas

- SES: replace SigV4 signing with the Worker-relay bearer or a CF token;
  SES configuration-set analytics have no CF equivalent yet (dashboard logs
  only, and the Email Routing panel miscounts Worker sends as "dropped").
- Postmark: server-token-per-stream maps naturally to one onboarded
  subdomain per traffic class (`notifications.*`, `marketing.*`) — CF's
  reputation isolation story.
