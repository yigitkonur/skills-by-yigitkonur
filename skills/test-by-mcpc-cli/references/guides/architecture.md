# Architecture

`mcpc 0.6.0` is a session-oriented CLI layered over detached bridge processes.

## Mental model

1. `mcpc connect <server> @session` resolves the target and starts a bridge.
2. The bridge owns the live transport session to the MCP server.
3. Later commands reuse the named session instead of reconnecting from scratch — reuse is name-keyed, not URL-keyed: a new `@name` against the same URL always creates a second, independent session.
4. `mcpc --json` and `mcpc --json @session` read from session state plus live server calls.
5. The bridge runs under the CLI's own runtime (`process.execPath`, since v0.4.0) rather than a hardcoded `node` — a Bun-installed CLI spawns a Bun bridge, keeping one keychain identity and removing the old macOS+Bun hang.

## Transport model that matters for this skill

- `stdio` via `file:entry` config targets
- Streamable HTTP for remote and localhost URLs
- not SSE as a practical `mcpc 0.6.0` test target (unchanged since 0.2.x — no CHANGELOG entry has added HTTP+SSE support)

## Protocol negotiation

`mcpc` negotiates MCP protocol versions from `2024-10-07` (oldest) up to `2026-07-28` (newest), falling back automatically when a server doesn't support the newest one. `2026-07-28` connections are **stateless** (no session handshake, `server/discover` replaces parts of `initialize`); `2025-11-25` and older are **stateful**. Deep coverage: `references/guides/protocol-versions.md`.

## Capability model

Separate three layers when you document behavior:

1. what the server advertises
2. what `mcpc` advertises as a client during initialize
3. what the CLI actually exposes as commands

That distinction explains why you can see `completions`-related capability signals without getting a polished top-level CLI command for them. It does NOT extend to `sampling`/`roots`: since v0.5.0, `mcpc` deliberately does not advertise those two capabilities (it has no LLM to answer `sampling/createMessage` and registers no `roots/list` handler), specifically so servers won't send requests that can only fail. See `references/guides/bridge-internals.md` for the mechanism.

## Useful implementation details

- `tools-get` is a CLI convenience built from tool metadata rather than a native MCP `tools/get` request
- the bridge maintains cached discovery data and refreshes it when list-changed notifications arrive (stateless connections that can't push notifications instead fall back to a time-based cache, or honor a server-provided `ttlMs` hint)
- task support is first-class at the CLI layer through `tools-call --task`, `tools-call --detach`, and `tasks-*` — but the tasks extension is not yet supported on `2026-07-28` connections, only on `2025-11-25` and older
- recovery depends on both process and command (verified live on 0.6.0): a killed *bridge* respawns transparently; a killed *stdio server child* makes ordinary commands fail `Not connected` (exit 2), but `ping` triggers the network-error restart/retry path and can restore the chain. Otherwise use `mcpc restart @session`. See `references/guides/bridge-internals.md` for the process-tree detail.

Use live behavior over README prose when they conflict.
