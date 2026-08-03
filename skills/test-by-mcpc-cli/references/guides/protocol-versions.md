# Protocol Versions

`mcpc 0.6.0` negotiates MCP protocol versions and can pin or probe them directly.
Verified against 0.6.0.

## Negotiation range

`mcpc` negotiates the newest version both sides support, from **2026-07-28** (newest)
down to **2024-10-07** (oldest).

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @s
mcpc @s
```

`mcpc @s` prints one line naming protocol and transport, e.g. `MCP: version 2025-11-25
/ Streamable HTTP (stateful)` — confirmed live against `research-mcp.yigitkonur.com/mcp`
(mcp-researchpowerpack 9.0.0). `--json` carries the same value as `protocolVersion`.

## Pinning with `--protocol-version`

```bash
mcpc connect https://mcp.example.com/mcp @pinned --protocol-version 2025-11-25
```

Forces one exact version instead of auto-negotiating. **The connection fails if the
server does not offer it** — not "prefer, then fall back." Use it to regression-test a
server against a spec revision it's supposed to keep supporting, or to confirm it
rejects one it never claimed. Skip it for ordinary smoke tests.

## `server-discover` — live probe, not connect-time cache

```bash
mcpc @s server-discover
```

Sends `server/discover`, a method MCP 2026-07-28 introduced. Reports what the server
supports **right now** — `supportedVersions`, capabilities, instructions, `_meta` — as
`DiscoverResult`. Unlike `mcpc @s` (settled at connect time), this is a fresh request.

Requires a 2026-07-28 connection; older connections get an educational error (exit 2),
confirmed live:

```
Error: server/discover is not available on this connection: it was introduced in MCP
2026-07-28, and this connection negotiated 2025-11-25, where the initialize handshake
carries the same information. Run "mcpc @s" to see it, or "mcpc @s ping" to check
liveness
```

Treat it as informative, not a bug — it names the gating version and points to working
alternatives. A server that only ever offers 2025-11-25 or older will always hit this;
that's a finding about the server, not a CLI failure.

## JSON-RPC method names as command aliases

0.6.0 silently accepts raw JSON-RPC method names as aliases for hyphenated commands. Only
two pairs are documented — `tools/list` → `tools-list`, `logging/setLevel` →
`logging-set-level` — don't assume a full alias table exists; confirmed live for those
plus `resources/list`, `resources/read`, `prompts/list`, byte-identical to the hyphenated
form.

Undocumented by design — absent from `--help` and "Did you mean?" — and does not extend
to `help`: `mcpc help tools/list` prints "Unknown command" in released 0.6.0 (confirmed
live; only `mcpc help tools-list` resolves). Only the first positional command token is
normalized; later `/`-containing args (URIs, tool names) are untouched.

`logging-set-level` is separately protocol-gated: MCP `2026-07-28` removed
`logging/setLevel`, so the command errors on connections that negotiated it and only
works on `2025-11-25` or older, where it succeeds but prints a deprecation warning
(suppressed under `--json`).

## Testing implications

- A server supporting only older protocol versions is a **finding to report**, not a
  broken test — a `server-discover` error or a rejected pin isn't tooling failure.
- Prefer negotiation for general coverage; pin only when the assertion targets one version.
- `server-discover` and `mcpc @s` can diverge on a long-lived session if capabilities
  changed since connect.
