# Pagination and Caching

This guide is about discovery behavior, not about promising internal implementation details.

## Tool cache reality in `0.2.x`

The tool cache is populated during startup and refreshed on `tools/list_changed`.
That means the first explicit `tools-list` after `connect` is not necessarily a fresh network fetch.

## Useful checks

```bash
mcpc connect https://research.yigitkonur.com/mcp @cache-test
mcpc @cache-test tools-list
mcpc --json | jq '.sessions[] | select(.name == "@cache-test") | .notifications.tools'
```

## Pagination guidance

- trust the current CLI output, not old assumptions about manual page stepping
- use `resources-templates-list` and other list commands normally; do not add pagination folklore unless you measured it against the released CLI

## Log path reminder

Per-session logs use names like `~/.mcpc/logs/bridge-@cache-test.log`.
