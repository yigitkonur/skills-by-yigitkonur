# Bridge Internals

A named session in `mcpc` is backed by a detached bridge process (`mcpc-bridge` executable).
That bridge owns the upstream MCP connection, local cache, and optional proxy; the CLI talks
to it over a Unix domain socket at `~/.mcpc/bridges/<name>`. Since v0.4.0 the bridge is spawned
under the CLI's own runtime (`process.execPath`), not a hardcoded `node` — a Bun-installed CLI
gets a Bun bridge, one keychain identity, and no cross-binary macOS Keychain hang (PR #266). As
of v0.6.0 the bridge speaks MCP through SDK v2 (`@modelcontextprotocol/client` 2.0.0), which
sends the `Mcp-Method` request header `2026-07-28` servers require and moves `serverInfo` into
response metadata.

## Why it matters operationally

- a session can keep running after the original terminal exits
- bridge logs are per session and live under `~/.mcpc/logs/bridge-@<session>.log`, rotated to
  `.log.1`…`.log.5`; read them with `mcpc @<session> logs [-n N] [--follow] [--since 1h]`
  (added v0.3.1) rather than tailing the file by hand
- `restart` replaces the bridge and reconnects the session
- `close` tears the session down cleanly

## Current lifecycle clues

You will commonly see these CLI-facing states:

- `live`
- `connecting`
- `reconnecting`
- `disconnected`
- `crashed`
- `unauthorized`
- `expired`

On-disk state uses a slightly different internal vocabulary.
Document the CLI JSON surface unless you are explicitly explaining internals.

## Reconnect behavior

`mcpc` queues background reconnect attempts for broken sessions instead of leaving them
permanently dead — that is why `reconnecting` matters and why a stale session can recover
without a fresh manual `connect`.

This goes further than a queued retry: a crashed bridge self-heals transparently on the next
command against that session. Killing the actual stdio child process underneath a bridge does
not surface as a caller-visible error — the next command (even a bare `ping`) detects the dead
connection, tears down the old bridge, respawns a brand-new bridge + child process chain,
reconnects, and completes, all inside one invocation, exit code 0. The only externally visible
tell is a slower response and a `pid` change in `sessions.json`/`mcpc --json` — to *detect* a
crash (not just survive it), watch `pid` churn or grep the bridge log for
`SIGTERM`/`Ping failed`, not exit codes.

Sessions resumed after a bridge restart also correctly restore their negotiated protocol
version, capabilities, and instructions (v0.6.0 fix — these could previously be lost, showing
`Protocol: unknown` and refusing `resources-subscribe`).

## Capability caveat

The opposite is now true from what older versions did: since v0.5.0, `mcpc` deliberately does
**not** advertise the `sampling` or `roots` MCP client capabilities, because it has no LLM to
answer `sampling/createMessage` and registers no `roots/list` handler — declaring them would
only invite server requests that can only fail. A server can still expose roots-aware or
sampling-flavored demo tools (those are ordinary tool calls), but the bridge no longer
over-advertises client-side capability it can't back.
