# mcp-use Major Version Migrations

Breaking changes between mcp-use major versions. The library is currently 1.x; this file tracks the within-1.x breaking changes that materially affect existing servers and the migration paths for each. A v2.0 release has not shipped — when it does, it will get its own section here.

---

## 1. v1.25.0 — Built-in OAuth providers default to DCR-direct

**What changed:** Auth0, WorkOS, Supabase, Keycloak, and Better Auth providers no longer accept `clientId` / `clientSecret`. Clients now talk to the upstream AS directly using DCR. Proxy mode is opt-in via the new `oauthProxy()` helper. `verifyToken` is required on custom providers.

**Impact:** Existing servers using built-in providers in proxy mode break.

**Migration:** See `05-dcr-vs-proxy-mode-shift.md` for full migration path.

---

## 2. v1.21.5 — Zod is now a `peerDependency`

**What changed:** `zod` moved from `dependencies` to `peerDependencies`.

**Impact:**

- TypeScript errors on `z.object(...)` if Zod isn't in your own `package.json`.
- Runtime errors about Zod not found.
- If you previously had two Zod copies (your project + nested `mcp-use/zod`), you now have one — type alignment improves but you must declare Zod yourself.

**Migration:**

```bash
npm install zod@^4.0.0
rm -rf node_modules
npm install
```

Verify `package.json` includes `"zod": "^4.0.0"` in `dependencies`.

---

## 3. v1.21.4 — `ctx.auth` populated correctly

**What changed:** `mountMcp()` now wraps `transport.handleRequest()` in `runWithContext()`, so `AsyncLocalStorage` is populated for the MCP request lifecycle.

**Impact:** Servers on v1.21.1–v1.21.3 had `ctx.auth` as `undefined` even with OAuth configured.

**Migration:** Upgrade to `mcp-use@^1.21.4`. Always guard `if (!ctx.auth) return error(...)`.

---

## 4. v1.20.1 — `McpUseProvider` no longer wraps `BrowserRouter`

**What changed:** Breaking change in widget React provider.

**Impact:** Widgets using `react-router-dom` crash at runtime.

**Migration:** Wrap routed widgets explicitly:

```tsx
import { BrowserRouter } from "react-router-dom";
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <BrowserRouter>
        <RoutedContent />
      </BrowserRouter>
    </McpUseProvider>
  );
}
```

---

## 5. v1.17.0 — Default widget protocol is `mcpApps`

**What changed:** The default widget `type` is now `mcpApps` (dual-protocol) instead of `appsSdk`.

**Impact:** New widgets are dual-protocol by default; old widgets explicitly set to `appsSdk` continue to work but are deprecated.

**Migration:** See `04-appssdk-to-mcpapps.md` for the full widget protocol migration.

---

## 6. v1.18.0 — `allowedOrigins` for DNS rebinding protection

**What changed (additive):** New `allowedOrigins` option on `MCPServer`.

**Impact:** Not breaking, but recommended for production — without it, your server is open to DNS rebinding.

**Migration:** Add `allowedOrigins` to your `MCPServer` config:

```typescript
const server = new MCPServer({
  name: "...", version: "1.0.0",
  allowedOrigins: ["localhost", "myapp.example.com"],
});
```

---

## 7. v1.21.1 — Distributed SSE via Redis Pub/Sub

**What changed:** Multi-instance SSE now routes through Redis Pub/Sub when `RedisSessionStore` is configured.

**Impact:** Multi-replica servers no longer drop SSE messages when traffic shifts shards.

**Migration:** No code change. Configure `RedisSessionStore` (you should already have one for multi-replica). Sessions and SSE both flow through it.

---

## 8. v1.22.0 — `ctx.elicit()` result mapping

**What changed:** Spec compliance fix — `elicit()` maps `result.content` → `result.data` for Zod validation. Backward-compatible fallback to `data` retained.

**Impact:** Pre-v1.22.0 servers used the workaround `result.data ?? (result as any).content`. v1.22.0+ does this internally.

**Migration:** After upgrade to v1.22.0+, remove the workaround. Or keep it — it's harmless.

---

## 9. Test paths after any major upgrade

1. `npm install <new-version>` and run `npm ls mcp-use` — confirm tree.
2. `mcp-use build` — TypeScript errors surface.
3. `mcp-use start` (or `mcp-use dev`) and connect Inspector — every tool listed.
4. Call one tool — verify response shape.
5. If using widgets — open in Inspector with CSP mode on.
6. If using OAuth — exercise the full flow against a test client.
7. Run your own integration tests if you have them.

---

## 10. Pinning strategy

- **Production:** pin to a specific `1.x.y`. Upgrade deliberately.
- **Dev:** track `^1.x.0` (caret) — caret allows minor and patch.
- **Avoid `*` or no version pin.** Each minor brings real changes.

---

When v2.0 ships, this file gets a new top section with the v1 → v2 delta. Until then, the deltas above cover every breaking-or-near-breaking change in the 1.x line.
