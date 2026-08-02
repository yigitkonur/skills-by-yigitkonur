# Session Management

`mcpc 0.6.0` is built around persistent named sessions.

## Create, inspect, restart, close

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @research
mcpc
mcpc --json | jq '.sessions[] | select(.name == "@research")'
mcpc @research
mcpc restart @research
mcpc close @research
```

For smoke tests, start from a fresh `connect`.
Use human `mcpc` output or an exact-name JSON filter only when reuse or cleanup is the actual question.

## Auto-naming and reuse — name-keyed, not URL-keyed

`@session` is optional on `connect`. Omit it and `mcpc` auto-generates a name from the server host (e.g. `mcp.apify.com` → `@apify`) or the config entry name, then reuses that auto-named session on later no-name connects to the same target — including transparently reconnecting it if its bridge had died.

Reuse is decided by three things matching an existing session: **server URL**, **profile**, and the **set of header keys** (not values). All three must match, or `connect` creates a new session.

Critical nuance: **reuse is keyed by session name, not by URL.** `connect <url> @existingName` reuses (if the other two criteria also match); `connect <url> @newName` always creates a second, independent session pointing at the same server — mcpc never dedupes by URL alone. Do not assume "I already connected to this URL" implies reuse; track your own session names.

The auto-derived name is not reliably predictable (a project with prior sessions against the same host can land on `@rp3` instead of `@research-mcp` if that family already exists) — always read the name back from `connect`'s own output before referencing the session again, rather than guessing it.

## Session states that matter operationally

In CLI-facing JSON you will commonly see:

- `live`
- `connecting`
- `reconnecting`
- `disconnected`
- `crashed`
- `unauthorized`
- `expired`

Persistent on-disk state uses a different internal vocabulary, including `active` instead of `live`.
Document the public JSON surface unless you are intentionally describing internals.

## Reconnect behavior

Every `mcpc` invocation consolidates session state first (flags dead bridges `crashed`, drops `expired` records) and then fire-and-forgets a background reconnect for sessions eligible for auto-restart: `crashed` sessions, and `unauthorized` sessions that carry an OAuth profile (their token may have been refreshed elsewhere). An `unauthorized` session authenticated via a static header (`-H`) is not retried automatically — it stays `unauthorized` until you `mcpc login` or reconnect explicitly, since retrying would just flip it back and forth and hide the real state.
Do not describe the runtime as only marking sessions dead.

A **dead child process** underneath a still-registered bridge self-heals silently: the next command that needs the connection (even a plain `ping`) detects the failure, tears down the old bridge, respawns a fresh one, and reconnects — all inside that one invocation, exit code 0. The only visible tell is a slower response and a changed `pid` in `mcpc --json`; nothing in stdout/exit code flags that a crash happened. To *detect* a crash (not just recover from it), watch `pid` churn in `mcpc --json` or grep the bridge log for `SIGTERM`/`Ping failed`.

## Stateful vs stateless connections

Protocol `2025-11-25` (and older) connections are **stateful** — the server assigns an MCP session id, and the tools cache is invalidated purely by `tools/list_changed` notifications with no fixed expiry. Protocol `2026-07-28` connections are **stateless** — no session handshake, so a fallback 60-second cache TTL applies to the tools list (or a server-sent `ttlMs` hint if lower). `mcpc @session` reports which mode is active on its `MCP: version ... / <transport> (stateful|stateless)` line; `--json` exposes the same as a tri-state `_mcpc.stateless` field (`true`/`false`/`null`) plus `_mcpc.transport`. For protocol negotiation, pinning with `--protocol-version`, and full 2026-07-28 behavior, see `references/guides/protocol-versions.md`.

## Useful inspection filters

```bash
mcpc --json | jq '.sessions[] | select(.name == "@research")'
mcpc --json | jq '.sessions[] | {name, status, createdAt, lastSeenAt, server}'
mcpc --json | jq '.sessions[] | select(.status != "live")'
```

## Restart fallback

If `mcpc restart @session` returns `Session not found`, treat that as a lost session record, not a signal to keep retrying (exit code 1 — a CLI usage error, no MCP round-trip was attempted).
Create a fresh named session instead.

## Logs for a session

`mcpc @session logs` shows or follows that session's bridge log — `-n/--tail <n>` (default 50), `--follow` to stream, `--since <30s|5m|2h|1d|ISO>` to time-window. Transparently spans rotated files (`.log.1`…`.log.5`); `--json` returns parsed `{time, level, context?, msg}` records. Prefer this over reading the raw log file directly when diagnosing a session-specific issue.

## Cleanup pairing

Use `mcpc clean sessions` to remove stale records after you understand the failure.
Use `mcpc clean all` only when you truly want to wipe local mcpc state.
