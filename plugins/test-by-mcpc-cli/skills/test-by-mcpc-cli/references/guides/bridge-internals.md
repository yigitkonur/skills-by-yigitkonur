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

**Recovery differs by process and command — verified live and against the shipped 0.6.0 source.** Kill
the *bridge* and the next session command detects the dead socket, spawns a fresh bridge, reconnects,
and completes with exit 0; only the `pid` changes. Kill the *stdio server child* underneath a
still-running bridge and ordinary read/list commands fail repeatedly with `Error: Failed to list
tools: Not connected.` (exit 2), while status and bridge `pid` can remain misleadingly `live` and
unchanged. `ping` is the exception: it classifies the dead pipe as a network error, triggers the
bridge restart/retry path, and can recover the bridge+child chain inside that one invocation (exit
0, slower response, new `pid`). Otherwise run `mcpc restart @session`; restart loses added tools and
async tasks but re-establishes resource subscriptions. Detect the cases with `pid` churn, `ping`,
and the session log — not status alone.

For stdio configs like `npx -y <package>`, the real server sits three levels below the reported
`pid`: bridge → `npm exec` → `sh -c` → the actual server process. `mcpc --json`'s `pid` is always
the bridge, never the leaf — killing the leaf doesn't touch that pid, and the bridge can't see
past its own `npm exec` child to notice the leaf died until it next tries to talk to it.

Sessions resumed after a bridge restart also correctly restore their negotiated protocol
version, capabilities, and instructions (v0.6.0 fix — these could previously be lost, showing
`Protocol: unknown` and refusing `resources-subscribe`).

## Capability caveat

Since v0.5.0, `mcpc` deliberately does **not** advertise the `sampling` or `roots` MCP client
capabilities — it has no LLM to answer `sampling/createMessage` and registers no `roots/list`
handler. It also advertises no elicitation capability. Servers that gate demo tools on those
client capabilities therefore omit them from `tools-list`; absence is expected, not a server bug.
