# backend-host-validation — the 403-from-Funnel trap

The single most surprising failure when standing up Funnel for a dev server: local `curl http://127.0.0.1:<port>/` returns `200 OK`, but `curl https://<node>.<tailnet>.ts.net:<funnel-port>/` returns `403 Forbidden`. Everything below the application layer is fine. The application is rejecting the request because the `Host:` header doesn't match its allowlist.

This is not a bug. It's a deliberate dev-server defense against DNS rebinding attacks. Production servers behind a real reverse proxy don't see this because the proxy rewrites `Host:`. Funnel does not rewrite — it preserves `Host: <node>.<tailnet>.ts.net` end-to-end. The dev server sees an unfamiliar hostname and refuses.

## The mental fix

Bind interface and Host validation are at different OSI layers. Switching from `127.0.0.1` to `0.0.0.0` (or back) does nothing for Host validation — it changes which network interfaces accept TCP connections, not what the HTTP server does after accepting.

| Layer | Controlled by | Affects |
|---|---|---|
| TCP bind | `--host` flag on the dev server | Which interfaces accept connections |
| HTTP Host validation | Framework-specific config | Whether the app responds 200 or 403 |

If you see 403 from Funnel and 200 from loopback, the bind is fine and the Host allowlist is the problem.

## Two real fixes

### Fix A — Use a static server instead (recommended when possible)

Static servers (`python3 -m http.server`, `caddy file-server`, `npx serve`, `nginx`) do not validate `Host:`. If your app produces a static output directory (`dist/`, `out/`, `build/`, `public/`, `_site/`), serve that directory instead of running the dev server through Funnel.

```bash
# Build first
npm run build       # or: pnpm build, astro build, next build, etc.

# Then serve the static output (no Host check)
cd dist && python3 -m http.server <port> --bind 127.0.0.1
```

Trade-offs you give up by going static:
- No hot reload (rebuild manually or `npm run build -- --watch`)
- No server-side rendering, no API routes
- No backend behavior

For exposing a built site to an agent-browser or a stakeholder, that's almost always fine. Production builds are also faster and more realistic than dev builds. **Prefer this path unless the work specifically needs the dev-server behavior.**

### Fix B — Configure the framework's Host allowlist

When you need the dev server's behavior (hot reload, SSR, API routes), configure its allowlist. Each framework has a slightly different config surface — copy-pasteable snippets live in `../assets/allowed-hosts-snippets.md`.

**Astro v5 (`astro.config.mjs`)**:

```js
export default defineConfig({
  // ... your existing config
  vite: {
    preview: {
      allowedHosts: ['.ts.net'],   // accept any *.ts.net hostname
    },
    server: {
      allowedHosts: ['.ts.net'],   // for `astro dev`
    },
  },
});
```

The dot-prefix `'.ts.net'` is a Vite-specific wildcard that matches any subdomain. Use this rather than naming your specific FQDN — it survives node renames and tailnet changes.

**Vite 5.4+ (`vite.config.ts`)**:

```ts
export default defineConfig({
  server: { allowedHosts: ['.ts.net'] },
  preview: { allowedHosts: ['.ts.net'] },
});
```

For Vite versions before 5.4 the option is `server.host: true` (which has the side effect of binding to `0.0.0.0` — note the bind-vs-validation conflation that the framework's own docs introduced). Upgrade Vite if you can.

**Next.js 15+** does not validate Host headers by default — just bind `-H 127.0.0.1` and move on. If you have a custom middleware that validates Host, search the codebase for that.

**Express / Fastify / Koa** generally don't validate Host by default. If they do, it's via custom middleware — search for `req.headers.host` in the codebase.

**Webpack dev-server** uses `allowedHosts` similar to Vite:

```js
devServer: { allowedHosts: ['.ts.net'] }
```

If you don't recognize your framework's config surface, search "<framework name> allowedHosts" or "<framework name> Host header validation" — the symptom is well-known and the fix is consistent.

## How to verify the fix worked

After applying either fix, the rung-2 curl in the main workflow should return `200`:

```bash
curl --max-time 12 -sS -o /dev/null \
  -w "HTTP=%{http_code}\n" \
  --resolve <node>.<tailnet>.ts.net:<funnel-port>:208.111.34.11 \
  https://<node>.<tailnet>.ts.net:<funnel-port>/
```

If you still see 403:

1. Did you restart the dev server after editing the config? Most frameworks need a restart to pick up config changes.
2. Is the framework version old enough that `allowedHosts` is named differently? Check the framework's release notes.
3. Is there a custom middleware in the project that runs *before* the framework's own Host check? Search for `req.headers.host` in your project.

## Why the static-server path is usually better for agents

Browser-automation agents (the most common reason this skill exists) don't need hot reload. They navigate a built site, snapshot it, click links. The static-server path is:

- One less moving part (no framework config to maintain)
- Faster startup (no dev server cold start)
- More representative (production build, real bundling)
- Survives framework version bumps (no `allowedHosts` API churn)

When in doubt, build then serve. The dev-server route exists for cases where the work genuinely needs the dev behavior.
