# email-sender Worker template

Bearer-authenticated relay in front of Cloudflare Email Service's
`send_email` binding, for backends that run outside Cloudflare.

Deploy (rename `name` in wrangler.jsonc to fit the project first):

```bash
CLOUDFLARE_ACCOUNT_ID=<account-id> npx wrangler deploy
openssl rand -hex 32 | CLOUDFLARE_ACCOUNT_ID=<account-id> npx wrangler secret put AUTH_TOKEN
```

Store the generated secret ONLY in the calling backend's secret store.

Contract — `POST /send`, `Authorization: Bearer <AUTH_TOKEN>`:

```json
{
  "from": {"address": "welcome@example.com", "name": "Product"},
  "to": "user@example.com",
  "subject": "Hello",
  "html": "<p>…</p>",
  "text": "…"
}
```

Responses: 200 `{message_id}` · 400 invalid body · 401 bad token ·
404 other routes · 502 `{error: "send_failed", detail}` provider failure ·
503 when AUTH_TOKEN is unset/short (refuses to run as an open relay).

The Worker translates `from.address` → the binding's `{email, name}` shape;
callers keep the REST-style `{address, name}` everywhere.
