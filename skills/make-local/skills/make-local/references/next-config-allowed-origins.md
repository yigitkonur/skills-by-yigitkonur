# Next 16 `allowedDevOrigins` — exact-match CORS

Next.js 16 added strict cross-origin checks for dev/HMR resources. Without explicit allowlisting, Turbopack blocks `/_next/webpack-hmr` and similar from any host other than `localhost`/`127.0.0.1`.

## Symptom

Dev overlay flashes:

```
⚠ Blocked cross-origin request to Next.js dev resource /_next/webpack-hmr from "host.example.com".

To allow this host in development, add it to "allowedDevOrigins" in next.config.js and restart the dev server:

// next.config.js
module.exports = {
  allowedDevOrigins: ['host.example.com'],
}
```

HMR breaks silently. Page renders but no hot updates.

## Fix

`next.config.ts`:

```ts
const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "http://127.0.0.1:3107",
    "http://localhost:3107",
    "https://mc-poc.example.com",
    "mc-poc.example.com",
    // Tailscale Serve hostnames for `make tunnel`. Both forms (short
    // MagicDNS + FQDN). Must be listed verbatim — Next 16's CORS check
    // does exact-match (not suffix). If you `tailscale set --hostname=foo`,
    // add foo + foo.<tailnet>.ts.net here.
    "PROJECT_NAME",
    "PROJECT_NAME.<tailnet>.ts.net",
  ],
  // ...rest of config
};
```

## The exact-match rule

Next 16's CORS check is exact-match, not suffix-match. List every form the user might hit:

| Hostname form | Notes |
|---|---|
| `<short>` | Short MagicDNS — works on tailnet peers |
| `<short>.<tailnet>.ts.net` | FQDN — required for HTTPS cert |
| `<short>.localhost` | portless |
| `localhost:<port>` | classic local |
| `127.0.0.1:<port>` | classic local IP |
| `<lan-ip>:<port>` | for `make local-lan` cross-device |

Not listing each one → silent HMR breakage on that exact host.

## Append, don't replace

When automating this edit, ALWAYS append to the existing array — never replace. The user may have entries you don't know about (Tailscale node aliases, custom domains, staging tunnels):

```bash
# WRONG: clobbers existing entries
sed -i '' 's/allowedDevOrigins:.*$/allowedDevOrigins: ["new-host"],/' next.config.ts

# RIGHT: insert new entries into the existing array
# Use a proper TS-aware edit, not regex
```

In the build-skills context, edit the file with `Edit` tool's `old_string`/`new_string` mode, matching enough surrounding context to insert into the existing array literal.

## Hostname rename procedure

When the user runs `tailscale set --hostname=newname`, the URL changes from `oldname.ts.net` to `newname.ts.net`. The Makefile picks this up dynamically (it reads `tailscale status --json`), but `next.config.ts` won't.

Procedure:
1. Add `newname` and `newname.<tailnet>.ts.net` to `allowedDevOrigins`
2. Optionally remove `oldname` and `oldname.<tailnet>.ts.net` if no longer used
3. Restart dev (`make tunnel-stop && make tunnel`)

Document this in a code comment so future contributors know to update both:

```ts
allowedDevOrigins: [
  // ... existing entries
  // Tailscale Serve hostnames for `make tunnel`. If you rename via
  // `tailscale set --hostname=NAME`, add NAME + NAME.<tailnet>.ts.net here.
  "NAME",
  "NAME.<tailnet>.ts.net",
],
```

## Cross-origin server actions

Next 15+ has separate CORS for server actions (`experimental.serverActions.allowedOrigins`). If the project uses server actions called from a non-local host, that needs its own allowlist:

```ts
experimental: {
  serverActions: {
    allowedOrigins: ['my.tunnel.host', 'localhost:3000'],
  },
},
```

Same exact-match rule.

## Verification

After adding hostnames, hit the dev overlay manually:

```bash
# Open the URL in a real browser, look for the warning in console
# Or check the dev server log for "Blocked cross-origin request"
make tunnel
# Open https://host.in.allowedDevOrigins/ in browser, then check terminal
```

If the warning still appears, the hostname isn't matching exactly — check for trailing slashes, port numbers (Next 16 ignores port for matching), and protocol prefixes.
