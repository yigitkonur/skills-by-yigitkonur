# Decision Tree

A flowchart-as-prose. Walk down to the right cluster. For exhaustive symptom → fix rows, see `01-error-catalog.md`.

---

## Start: which layer is broken?

**Q1.** Does `curl -s {url}/health` return JSON?

- **No, HTTP error / connection refused** → server isn't running or unreachable. Go to **A. Connect / startup**.
- **No, returns HTML** → the catch-all Inspector is serving `/health`. Register an explicit `server.get("/health", ...)` before `listen()`. (`01-error-catalog.md` row "GET /health returns Inspector HTML".)
- **Yes** → server is up. Continue to Q2.

**Q2.** Does the Inspector connect?

- **No, handshake error** → go to **B. Handshake**.
- **Yes, but no tools listed** → go to **C. Tool registration**.
- **Yes, tools listed** → continue to Q3.

**Q3.** Does calling a tool succeed end-to-end?

- **No, schema error / validation** → go to **D. Schemas**.
- **No, auth error (401, 403)** → go to **E. Auth**.
- **No, timeout / 504** → go to **F. Timeouts and transports**.
- **No, response empty** → handler missing return. See `01-error-catalog.md` row "tool responses are empty".
- **Yes, tool runs** → continue to Q4.

**Q4.** Does the widget render?

- **No, plain HTML / blank / missing provider** → go to **G. Widgets**.
- **No, CSP violations** → go to `05-csp-violations.md`.
- **Yes** → you're shipping.

---

## A. Connect / startup

1. Process running? `ps aux | grep node` or `gcloud run services describe ...`.
2. Port? `lsof -i :3000` (local). Or platform's port logs.
3. URL correct? Should be `/mcp`, not `/` or `/sse`.
4. Server crashing on startup? Check logs for stack traces. Common: missing env var, bad import, port collision (`EADDRINUSE`).
5. Firewall / network? `curl` from the same network as the client.

→ Specific symptoms: `01-error-catalog.md` § "Server lifecycle".

---

## B. Handshake

1. Run `curl -i -X POST {url} -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'`.
2. Got HTML back? Wrong endpoint, proxy returning a redirect, or auth gate.
3. Got 401 / 403? Auth not set up correctly — go to **E. Auth**.
4. Got `protocol version mismatch`? Upgrade `mcp-use`. Capability negotiation handles compatible versions.
5. Got CORS preflight failure? `cors` not configured. Add explicit `cors` to `MCPServer`.

→ Specific symptoms: `01-error-catalog.md` §§ "Schemas" and "CORS and CSP".

---

## C. Tool registration

1. Tools registered **before** `server.listen()`?
2. Two `MCPServer` instances? Search for `new MCPServer` — should be exactly one.
3. Run `client.listTools()` — does it return `[]`? Then it's a registration order problem.
4. Tool name typo? Names are case-sensitive.

→ `01-error-catalog.md` §§ "Server lifecycle".

---

## D. Schemas

1. Read the Zod error — it names the failing field.
2. Use `.describe()` on every schema field.
3. Use `z.coerce.number()` / `.boolean()` for forgiving parsing.
4. `.default()` on optional fields where it makes sense.
5. Test in the Inspector — its tool form pre-validates.

→ `01-error-catalog.md` § "Schemas and validation".

---

## E. Auth

**Q.** Is this OAuth + Supabase?

- **Yes** → `03-oauth-and-supabase-issues.md`.
- **No, generic OAuth 401** → token expired or scopes wrong. Decode the JWT, compare claims.
- **`ctx.auth` undefined in handler** → upgrade to `mcp-use@^1.21.4`.
- **DCR-related** (`Incompatible auth server`, `registration_endpoint`) → `03-oauth-and-supabase-issues.md` and `28-migration/05-dcr-vs-proxy-mode-shift.md`.
- **DNS rebinding 403** → add domain to `allowedOrigins`.

---

## F. Timeouts and transports

1. **SSE drops at 60s** → proxy idle timeout. Or migrate to Streamable HTTP (`28-migration/03-sse-to-streamable-http.md`).
2. **Long tool timeouts** → use `ctx.reportProgress`. Or async job pattern.
3. **413 Payload Too Large** → switch to `resources` for large data. Adjust nginx `client_max_body_size`.
4. **Session lost between requests** → client not echoing `Mcp-Session-Id`. Use SDK's `StreamableHTTPClientTransport`. Configure `sessionStore`.
5. **404 after server restart** → in-memory session store. Use `RedisSessionStore`.

→ `01-error-catalog.md` §§ "Sessions" and "Transports and proxies".

---

## G. Widgets

1. **Plain HTML / no React** → host doesn't speak MCP Apps. Check the host. See `04-widget-rendering-issues.md`.
2. **Blank** → CSP violation. Open browser DevTools console. Map directive → `widgetMetadata.metadata.csp` field. See `05-csp-violations.md`.
3. **`useWidget` outside provider** → wrap in `<McpUseProvider>`.
4. **React Router broken** → wrap in `<BrowserRouter>` manually (v1.20.1+).
5. **Vite cold-start 504 on first render** → upgrade to v1.25.2+.

→ `04-widget-rendering-issues.md`.

---

## When the tree doesn't help

Open `01-error-catalog.md` and grep for the exact error string. Every known error in the catalog has a one-line cause and a one-line fix. If the error isn't there, the catalog isn't aware of it — search the mcp-use GitHub issues by the same string.
