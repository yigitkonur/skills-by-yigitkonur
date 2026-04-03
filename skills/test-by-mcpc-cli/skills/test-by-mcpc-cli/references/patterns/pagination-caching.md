# Pagination and Tool Caching

mcpc hides all MCP pagination details from the caller and keeps a per-session in-memory cache of
tool listings to avoid redundant network round-trips. Understanding both mechanisms is essential for
writing reliable tests that interact with tool catalogs.

---

## Auto-pagination

The MCP protocol returns large catalogs in pages. Each response may carry a `nextCursor` field that
points to the next page. mcpc never exposes this complexity to the caller.

- `tools-list`, `resources-list`, `prompts-list`, and `resources-templates-list` all return the
  **complete list** — every item from every page, merged into a single array.
- The bridge's SDK method `listAllTools()` loops internally until no `nextCursor` is returned, then
  resolves with the full combined result.
- The same loop pattern applies to resources and prompts; the SDK exposes analogous `listAll*` helpers.
- Transparent to the user — no cursor flags, no offset parameters, no manual loop needed.

```bash
# Returns ALL tools, regardless of how many pages the server uses internally
mcpc --json @session tools-list | jq 'length'

# Same applies to resources and prompts
mcpc --json @session resources-list | jq 'length'
mcpc --json @session prompts-list   | jq 'length'
```

CRITICAL SYNTAX: `mcpc <target> connect @<session>`, `mcpc @session close`, `mcpc --json @session command`.

---

## Tool caching

The bridge process holds an in-memory cache of tool listings to avoid repeating the full paginated
fetch on every invocation.

- The cache is populated on the **first** `tools-list` call after the bridge connects (network fetch,
  all pages consumed).
- Subsequent `tools-list` calls return the cached result immediately — no network, significantly faster.
- `tools-list --full` (which fetches extended tool metadata) also reads from this cache.
- The cache lives for the lifetime of the bridge process. Restarting the session (or closing and
  reopening it) creates a fresh bridge and therefore an empty cache.

Resources and prompts are **not** cached by the bridge in the same way — they are fetched fresh on
each list call (the MCP SDK's own autoRefresh mechanism handles their updates instead).

---

## Cache invalidation

The cache is not stale-forever. Two mechanisms keep it current:

- **`tools/list_changed` notification** — when the server sends this, the bridge's notification
  handler calls `client.listAllTools({ refreshCache: true })` to bypass the cache, re-fetch all
  pages, and store the updated result. The refreshed data is then broadcast over IPC.
- **`autoRefresh` flag** — resources and prompts are registered with `autoRefresh: true` in the SDK,
  so the SDK itself re-fetches them when it receives `resources/list_changed` or
  `prompts/list_changed`. Tools use `autoRefresh: false` because the bridge manages their refresh
  manually to correctly handle pagination after every change notification.

---

## Testing implications

After modifying tools on the server side, the cache may be stale. Three options to get fresh data:

```bash
# Option 1: Restart the session (clears the bridge process and its cache)
mcpc @session restart
mcpc --json @session tools-list | jq 'length'

# Option 2: Wait for tools/list_changed notification
# (if the server sends it — verify in shell mode)
mcpc @session shell
# Server sends notification → cache auto-refreshes inside the bridge
# Type: tools-list

# Option 3: Close and reconnect (same effect as restart)
mcpc @session close
mcpc <server> connect @session
mcpc --json @session tools-list | jq 'length'
```

---

## Observing pagination

```bash
# Check total tool count — if surprisingly high, pagination worked correctly
mcpc --json @session tools-list | jq 'length'

# Bridge logs record each paginated request; look for cursor-related lines
cat ~/.mcpc/logs/bridge-session.log | grep -i "cursor\|pagina"

# Compare timing: first call fetches from network, second hits the cache
time mcpc --json @session tools-list > /dev/null   # First: network (slower)
time mcpc --json @session tools-list > /dev/null   # Second: cache (faster)
```

---

## Resource and prompt pagination

- `resources-list`, `resources-templates-list`, and `prompts-list` all auto-paginate using the same
  `nextCursor` loop.
- No separate bridge-level cache exists for resources or prompts — they rely on the SDK's
  `autoRefresh: true` setting to stay current.
- Fetching resources or prompts always reflects the latest server state after any
  `list_changed` notification, because the SDK refreshes them automatically.

---

## Key takeaways for testing

1. The first `tools-list` after connecting is always a network fetch (cache is cold).
2. Subsequent calls are served from cache until a `tools/list_changed` notification arrives or the
   session is restarted.
3. If you add or remove tools server-side and need to verify the change, restart the session or wait
   for the server to emit `tools/list_changed`.
4. Resources and prompts do not need manual restarts — they refresh automatically on `list_changed`.
5. Use `--verbose` to surface pagination loop details and cache hit/miss information in the logs.

---

## Key source locations

- `src/bridge/index.ts` — `listAllTools()` pagination loop, cache storage, `tools/list_changed`
  handler with `refreshCache: true`
- `src/lib/types.ts` — cache-related fields on the session state type
- `src/cli/commands/tools.ts` — `tools-list` command, `--full` flag
- `src/cli/commands/resources.ts` — `resources-list`, `resources-templates-list` commands
- `src/cli/commands/prompts.ts` — `prompts-list` command
