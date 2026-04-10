# Session Management

`mcpc 0.2.x` is built around persistent named sessions.

## Create, inspect, restart, close

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
mcpc
mcpc --json
mcpc @research
mcpc restart @research
mcpc close @research
```

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
mcpc --json | jq '.sessions[] | {name, status, createdAt, lastSeenAt, server}'
mcpc --json | jq '.sessions[] | select(.status != "live")'
```

## Cleanup pairing

Use `mcpc clean sessions` to remove stale records after you understand the failure.
Use `mcpc clean all` only when you truly want to wipe local mcpc state.
