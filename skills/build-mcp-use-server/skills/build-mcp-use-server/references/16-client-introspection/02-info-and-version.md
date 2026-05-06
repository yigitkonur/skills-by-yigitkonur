# `ctx.client.info()` and Protocol Version

`ctx.client.info()` returns the client name and version reported during the MCP initialize handshake when the client supplied them. This is host application identity — useful for logging and diagnostics.

```typescript
const { name, version } = ctx.client.info();
// e.g. { name: "claude-desktop", version: "1.2.0" }
```

## Return shape

```typescript
interface ClientInfo {
  name?:    string;
  version?: string;
}
```

The package returns a shallow copy of the initialize `clientInfo` object. Both fields are optional in the published TypeScript declarations.

## Client identifiers

The exact `name` strings depend on the host and are not normalized by mcp-use. Log the value you actually receive before writing a host-specific workaround.

Avoid brittle exact-string equality. If you must branch on the name for a known host bug, keep the branch narrow and keep capability checks as the primary path.

```typescript
const { name } = ctx.client.info();
const isClaudeDesktop = name?.startsWith("claude") ?? false;
```

## Negotiated protocol version

mcp-use 1.26.0 does not expose the negotiated MCP protocol version on `ctx.client`. For feature behavior, check capabilities instead of protocol versions.

Protocol versions are coarse; capability flags are precise.

## Why prefer capabilities over names

Branching on `name` is fragile. Two builds of the same client may differ in capabilities; two different clients may share capabilities. Always prefer `ctx.client.can("capability")` and `ctx.client.supportsApps()` to feature-detect.

```typescript
// BAD — brittle name match
if (name === "chatgpt") {
  return widget({ /* ... */ });
}

// GOOD — feature detect
if (ctx.client.supportsApps()) {
  return widget({ /* ... */ });
}
```

`supportsApps()` is documented in `04-supports-apps.md`. `can()` is documented in `03-can-capabilities.md`.

## When name/version IS the right thing

Use `info()` for:

- Logging which client made a request (audit trails, debugging)
- Bug-shape mitigations for a specific known-broken client version
- Telemetry attribution

```typescript
import { Logger } from "mcp-use";
const log = Logger.get("tool");

server.tool({ name: "do-thing", schema: z.object({}) }, async (_a, ctx) => {
  const { name, version } = ctx.client.info();
  log.info("tool invoked", {
    client: name ?? "unknown",
    clientVersion: version ?? "unknown",
  });
  // ...
});
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Switching tool behavior on exact `name` | Feature-detect via `can()` / `supportsApps()` |
| Ignoring `version` when working around a known bug | Pin the workaround to the specific buggy version range |
| Trusting `info()` for security decisions | Client-reported and unverified — use OAuth (`ctx.auth`) for auth |
