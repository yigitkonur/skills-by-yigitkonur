# Session Management

`mcpc 0.2.x` is built around persistent named sessions.

## Create, inspect, restart, close

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
mcpc
mcpc --json | jq '.sessions[] | select(.name == "@research")'
mcpc @research
mcpc restart @research
mcpc close @research
```

Use human `mcpc` output or an exact-name JSON filter before a full global dump on machines with many saved sessions.

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

Current `mcpc` can queue reconnect work for sessions that are broken, unauthorized, or expired after cooldown checks.
Do not describe the runtime as only marking sessions dead.

## Useful inspection filters

```bash
mcpc --json | jq '.sessions[] | select(.name == "@research")'
mcpc --json | jq '.sessions[] | {name, status, createdAt, lastSeenAt, server}'
mcpc --json | jq '.sessions[] | select(.status != "live")'
```

## Restart fallback

If `mcpc restart @session` returns `Session not found`, treat that as a lost session record, not a signal to keep retrying.
Create a fresh named session instead.

## Cleanup pairing

Use `mcpc clean sessions` to remove stale records after you understand the failure.
Use `mcpc clean all` only when you truly want to wipe local mcpc state.
