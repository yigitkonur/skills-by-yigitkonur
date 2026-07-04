# allowed-hosts-snippets

Copy-pasteable framework configs for accepting `<node>.<tailnet>.ts.net` as a valid HTTP Host header.

Use these when you must run the framework's dev/preview server (not a static `dist/` via `python3 -m http.server`). If a built static directory exists, prefer serving that — no Host validation, no config to maintain.

## Astro v5+

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';

export default defineConfig({
  // ... existing config
  vite: {
    server: { allowedHosts: ['.ts.net'] },   // for `astro dev`
    preview: { allowedHosts: ['.ts.net'] },  // for `astro preview`
  },
});
```

`'.ts.net'` (with the leading dot) is a Vite wildcard that matches every `<anything>.ts.net` subdomain — your tailnet name lives in there, so this entry survives renames.

## Vite 5.4+

```ts
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  server:  { allowedHosts: ['.ts.net'] },
  preview: { allowedHosts: ['.ts.net'] },
});
```

For older Vite versions the equivalent is `server.host: true` — but that flag also binds to `0.0.0.0`. Prefer upgrading Vite.

## Next.js 15+

No Host-header validation by default. Just bind explicitly:

```bash
next start -p 4321 -H 127.0.0.1
# or
next dev   -p 4321 -H 127.0.0.1
```

If your project has custom middleware (`middleware.ts`) that checks `req.headers.host`, add `.ts.net` to that allowlist. Search the codebase for `req.headers.host` to find it.

## Webpack dev-server (CRA, older bundlers)

```js
// webpack.config.js
module.exports = {
  // ...
  devServer: {
    allowedHosts: ['.ts.net'],
    // or for everything (loose, dev-only): allowedHosts: 'all'
  },
};
```

## Express / Fastify / Koa / NestJS

These do not validate Host by default. If you've added a custom middleware that does, it lives in your project, not the framework. Search for `req.headers.host` or `request.headers.host`.

## Rails / Django / Flask

- **Rails**: `config.hosts << '.ts.net'` in `config/environments/development.rb`. Rails has `ActionDispatch::HostAuthorization` middleware enabled in dev — this is what produces the "Blocked host" page.
- **Django**: add `'.ts.net'` to `ALLOWED_HOSTS` in `settings.py` (or use `ALLOWED_HOSTS = ['*']` strictly for dev, never for prod).
- **Flask**: no built-in Host check. If you've added one via `before_request`, find and amend it.

## Caddy (file server or reverse proxy)

```caddyfile
:4321 {
  root * ./dist
  file_server
}
```

Caddy does not validate Host by default. If you've configured automatic HTTPS or matched on specific hostnames, you'll need to add `.ts.net` to the matcher block. Most projects don't need this.

## `python3 -m http.server`

No Host validation. The recommended path for static `dist/` directories:

```bash
cd dist && python3 -m http.server 4321 --bind 127.0.0.1
```

`--bind 127.0.0.1` is the correct security default — Funnel terminates externally and proxies to loopback; the static server should not be reachable any other way.

## `npx serve`

```bash
npx serve dist -p 4321 -l tcp://127.0.0.1:4321
```

`-l` (listen) controls bind. No Host validation. Useful when you want SPA fallback behavior (`/anything` → `index.html`).

## `caddy file-server`

```bash
caddy file-server --listen 127.0.0.1:4321 --root dist
```

Clean, fast, handles clean URLs and content-type detection sensibly.

## The fallback recipe (works for everything)

When the framework's allowlist surface is uncertain or you're in a hurry:

```bash
# Build static output
npm run build      # or pnpm build, astro build, next build, etc.

# Serve it without Host validation
cd dist && python3 -m http.server 4321 --bind 127.0.0.1
```

This bypasses the Host-header trap entirely. Trade-off: no hot reload, no dev-only features. For most browser-automation and demo use cases, this is the right call.
