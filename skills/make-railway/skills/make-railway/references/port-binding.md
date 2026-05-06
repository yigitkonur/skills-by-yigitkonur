# Port binding on Railway

Railway sets `PORT` env at runtime. The app must:

1. **Read `process.env.PORT`** — never hard-code a port
2. **Bind `0.0.0.0`** — never bind `localhost`/`127.0.0.1`

## Why

Railway runs your container on a randomly-assigned host port and proxies. The container must:

- Listen on whatever `PORT` Railway gave it (varies per deploy)
- Listen on all interfaces (`0.0.0.0`), not just loopback (or the proxy can't reach you)

## Symptoms of wrong binding

| Wrong code | Result |
|---|---|
| `app.listen(3000)` | Railway tries to proxy to `PORT` (say, 8080) → connection refused → deploy fails health check |
| `app.listen(process.env.PORT, 'localhost')` | App binds 127.0.0.1 only → Railway proxy can't connect → 502 |
| `app.listen(process.env.PORT)` (Node default `0.0.0.0`) | ✓ Works |
| `next start` | Reads `PORT` env, binds `0.0.0.0` by default | ✓ Works |
| `next start --hostname localhost` | Binds 127.0.0.1 → Railway 502 | ✗ Don't pass `--hostname` |

## Right pattern for Next.js

```Dockerfile
# Don't pass --hostname; let Next bind 0.0.0.0 by default
CMD ["npm", "start"]
```

In `package.json`:

```json
{
  "scripts": {
    "start": "next start"
  }
}
```

Next.js reads `PORT` env automatically. No flag passing needed.

## Right pattern for Express/Hono/Fastify

```ts
const port = Number(process.env.PORT) || 3000;
app.listen(port, '0.0.0.0', () => console.log(`Listening on :${port}`));
```

Or shorter (Node defaults to `0.0.0.0` if you omit the host):

```ts
app.listen(Number(process.env.PORT) || 3000);
```

## Local dev binding (different concern)

For `make local-lan` (cross-device on Wi-Fi), bind `0.0.0.0` explicitly so phones can reach. Same rule as Railway.

For `make local` via portless or `make tunnel` via Tailscale, bind `127.0.0.1` or `localhost` — the proxy is local. Doesn't conflict with the Railway rule (different deploys, different env).

## Health checks

Railway sends GET `/` (or a configured path) to verify the app is responding. If your app:

- Doesn't respond on `/` (e.g., requires auth) → Railway will mark it as failed health
- Takes > 60s to start → Railway gives up, marks as failed

Configure health check via Railway dashboard → Service → Settings → Health Check Path. Set to a route that returns 200 without auth (`/api/health`, `/health`, `/_next/static/foo`).

## Multiple ports per service

Railway containers expose ONE port (the one mapped to `PORT` env). If your app needs a second port (admin UI, gRPC), you need a second service or proxy from the main one. Don't try to expose two ports from one container — Railway doesn't support it.
