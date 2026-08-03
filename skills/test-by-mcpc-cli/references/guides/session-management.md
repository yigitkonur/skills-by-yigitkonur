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

**Recovery differs by process and command — verified live and against the shipped 0.6.0 source.**
Kill the *bridge* and the next command silently starts a fresh bridge and reconnects (exit 0, new
`pid`). Kill the *stdio server child* while the bridge stays up and ordinary read/list commands fail
with `Error: Failed to list tools: Not connected.` (exit 2), while status can remain misleadingly
`live` with the same `pid`. `ping` is the exception: it classifies the dead pipe as a network error
and triggers bridge restart/retry, so it can recover the bridge+child chain inside one invocation
(exit 0, slower response, new `pid`). Otherwise run `mcpc restart @session`; restart loses added
tools and async tasks but re-establishes resource subscriptions automatically. Use `pid` churn,
`ping`, and `mcpc @session logs` to distinguish these cases — not status alone.

## Stateful vs stateless connections

Protocol `2025-11-25` (and older) connections are **stateful** — the server assigns an MCP session id, and the tools cache is invalidated purely by `tools/list_changed` notifications with no fixed expiry. Protocol `2026-07-28` connections are **stateless** — no session handshake, so a fallback 60-second cache TTL applies to the tools list (or a server-sent `ttlMs` hint if lower). `mcpc @session` reports which mode is active on its `MCP: version ... / <transport> (stateful|stateless)` line; `--json` exposes the same as a tri-state `_mcpc.stateless` field (`true`/`false`/`null`) plus `_mcpc.transport`. For protocol negotiation, pinning with `--protocol-version`, and full 2026-07-28 behavior, see `references/guides/protocol-versions.md`.

## Useful inspection filters

```bash
mcpc --json | jq '.sessions[] | {name, status, createdAt, lastSeenAt, server}'
mcpc --json | jq '.sessions[] | select(.status != "live")'
```

## Restart fallback

If `mcpc restart @session` returns `Session not found`, treat that as a lost session record, not a signal to keep retrying (exit code 1 — a CLI usage error, no MCP round-trip was attempted).
Create a fresh named session instead.

`close` is not idempotent: closing an already-closed (or never-existent) session returns
`Error: Session not found` at exit code 1, the same error class as a bad `restart`. Scripts that
defensively `close` a session must tolerate that exit 1 rather than treat it as a hard failure.

## Logs for a session

`mcpc @session logs` shows or follows that session's bridge log — `-n/--tail <n>` (default 50), `--follow` to stream, `--since <30s|5m|2h|1d|ISO>` to time-window. Transparently spans rotated files (`.log.1`…`.log.5`); `--json` returns parsed `{time, level, context?, msg}` records. Prefer this over reading the raw log file directly when diagnosing a session-specific issue.

## Cleanup pairing

Use bare `mcpc clean` to remove stale records after you understand the failure.
Use named targets (`clean sessions`, `clean all`, and so on) only for an intentional full reset — they remove live records too.
