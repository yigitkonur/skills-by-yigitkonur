# Bridge Internals

A named session in `mcpc` is backed by a detached bridge process.
That bridge owns the upstream MCP connection, local cache, and optional proxy.

## Why it matters operationally

- a session can keep running after the original terminal exits
- bridge logs are per session and live under `~/.mcpc/logs/bridge-@session.log`
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

`mcpc` can queue background reconnect attempts for broken sessions instead of leaving them permanently dead.
That is why `reconnecting` matters in `0.2.x` and why a stale session can recover without a fresh manual `connect`.

## Capability caveat

The bridge advertises more client capability than the CLI exposes directly.
That is why servers can expose roots-aware or sampling demo tools even though the CLI has no dedicated roots configuration or sampling command family.
