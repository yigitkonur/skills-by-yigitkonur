# Pagination and Caching

This guide is about discovery behavior, not about promising internal implementation details.

## Tool cache reality in `0.6.0`

`tools-list`, `resources-list`, `resources-templates-list`, and `prompts-list` each auto-paginate
internally via a shared `fetchAllPages()` helper — you always get the full collection in one call,
never a raw `nextCursor` to chase yourself. `fetchAllPages()` also guards against a misbehaving
server: if a `nextCursor` repeats (a pagination cycle) or the page count blows past a generous cap,
mcpc aborts with a server error instead of looping forever (fixed in v0.5.0, PR #303).

Caching differs by connection statefulness (see `references/patterns/data-model.md` for the full
`stateless` field semantics):
- **Stateful connections** (protocol `2025-11-25` and older) — no fixed TTL. The tools cache is
  invalidated purely by `tools/list_changed` notifications from the server.
- **Stateless connections** (protocol `2026-07-28`, no session handshake) — can't push
  notifications, so mcpc falls back to a 60-second cache TTL (`STATELESS_TOOLS_CACHE_TTL_MS`,
  landed v0.3.1). If the server sends a `ttlMs` cache hint, that wins over the 60s fallback.

`tools-list` always force-refetches from the server on every explicit invocation — a v0.6.0 fix:
previously the SDK's own response cache could serve a stale list against a server that sent caching
hints. The refreshed cache now also honors the server's `ttlMs` hint instead of always using mcpc's
own freshness window.

## Useful checks

```bash
mcpc connect research-mcp.yigitkonur.com/mcp @cache-test
mcpc @cache-test tools-list
mcpc --json @cache-test | jq '._mcpc'
```

## Pagination guidance

- trust the current CLI output, not old assumptions about manual page stepping — `tools-list`,
  `resources-list`, `resources-templates-list`, and `prompts-list` all return the complete,
  already-paginated collection
- do not add pagination folklore beyond what's measured against the released CLI; a raw
  `nextCursor` is never surfaced to the caller

## Log path reminder

Per-session logs live at `~/.mcpc/logs/bridge-@cache-test.log`, rotated to `.log.1`–`.log.5`.
Prefer `mcpc @cache-test logs [-n N] [--follow] [--since 1h]` over reading the file directly — it
transparently spans rotated files and supports `--json` for structured records.
