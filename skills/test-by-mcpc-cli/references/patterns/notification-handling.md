# Notification handling in mcpc

MCP notifications are server-push events — unsolicited messages sent by the server at any time
without a matching client request. The client never polls; the server fires and forgets these
messages over the open Streamable HTTP connection. mcpc's bridge process catches them all, persists
relevant metadata to `sessions.json`, and fans them out over IPC to every CLI process that is
currently listening.

---

## Notification types

The full set of `NotificationType` values recognised by mcpc (defined in `src/lib/types.ts`):

| Method | Trigger |
|---|---|
| `tools/list_changed` | Server's tool catalog changed |
| `resources/list_changed` | Resource catalog changed |
| `resources/updated` | A specific subscribed resource changed |
| `prompts/list_changed` | Prompt catalog changed |
| `progress` | Long-running operation progress update |
| `logging/message` | Server emitted a log entry |
| `tasks/status` | Internal task-related status update; not a public `mcpc 0.1.11` command surface |

---

## How notifications flow through the system

```
MCP server
  │  (Streamable HTTP, server-push)
  ▼
Bridge process (mcpc-bridge)
  │  broadcastNotification() over Unix socket
  ▼
Every connected CLI process (BridgeClient → SessionClient → caller)
```

The bridge registers handlers at connection time inside `connectToMcp()`:

- `tools/list_changed` — bridge also refreshes its in-memory tool cache via
  `client.listAllTools({ refreshCache: true })` before broadcasting, so the x402 proactive
  signer always has a current view.
- `resources/list_changed` — SDK `autoRefresh: true`; bridge broadcasts after SDK refreshes.
- `prompts/list_changed` — same pattern as resources.
- `logging/message` — registered via `setNotificationHandler(LoggingMessageNotificationSchema, …)`
  on the raw SDK client; params forwarded verbatim to IPC listeners.

For every list-change notification the bridge additionally writes an ISO 8601 timestamp to
`sessions.json` under `notifications.<type>.listChangedAt` using `updateNotificationTimestamp()`.

---

## Notifications in shell mode

Shell mode (`mcpc @session shell`) is the only interactive mode that displays notifications in
real time. Entry point: `src/cli/shell.ts`.

**How it works:**

`setupNotificationListener()` opens a second, dedicated IPC connection to the bridge (a
`SessionClient` stored as `ctx.notificationClient`). This connection exists purely to receive
broadcast notifications — it sends no requests. When the bridge calls `broadcastNotification()` for
any event, all open sockets get the message, including this dedicated listener.

The listener calls `displayNotification(notification)` which maps each method to a chalk-styled
line and prints it inline between shell prompts:

```
CRITICAL SYNTAX: mcpc @session shell
```

Color mapping in `displayNotification()` (actual code in `src/cli/shell.ts`):

| Notification method | Color |
|---|---|
| `tools/list_changed` | yellow |
| `resources/list_changed` | yellow |
| `prompts/list_changed` | yellow |
| `resources/updated` | yellow |
| `progress` | cyan |
| `logging/message` | gray |
| unknown methods | dim |

Example output during a shell session:

```
mcpc(@apify)> tools-list
... (tool list appears) ...
[10:42:17] Server tools list changed
[10:42:18] Server resources list changed
mcpc(@apify)>
```

The notification client is closed in the `finally` block of `startShell()`, so the extra connection
is always torn down when the shell exits — even on SIGINT or SIGTERM.

---

## Notifications in CLI mode (non-interactive)

When running one-shot commands (`mcpc @session tools-list`, scripts, etc.) there is no persistent
listener. Notifications are never displayed. Instead, the bridge silently updates `sessions.json`:

```jsonc
// ~/.mcpc/sessions.json (excerpt)
{
  "my-session": {
    "notifications": {
      "tools": {
        "listChangedAt": "2026-03-24T10:42:17.000Z"
      },
      "resources": {
        "listChangedAt": "2026-03-24T10:42:18.000Z"
      },
      "prompts": {
        "listChangedAt": "2026-03-24T10:42:19.000Z"
      }
    }
  }
}
```

Scripts can read these timestamps to detect whether the server catalog changed since the last run:

```bash
# Read notification timestamps from session JSON
mcpc --json @my-session 2>/dev/null | jq '.notifications'

# Or read sessions.json directly
cat ~/.mcpc/sessions.json | jq '.sessions["my-session"].notifications'
```

---

## Testing notification support

### Observe notifications in shell mode

```bash
# 1. Connect to a session
mcpc https://mcp.example.com connect @test

# 2. Enter the interactive shell — notifications appear here
mcpc @test shell

# 3. Inside the shell, run any command and watch for notification lines
mcpc(@test)> tools-list

# 4. On the server side, add or remove a tool — you should see:
# [HH:MM:SS] Server tools list changed
```

The shell only receives notifications for session targets (names starting with `@`). Direct URL
targets (`mcpc https://... shell`) do not have a bridge and therefore receive no notifications.

### Check notification timestamps in session JSON

```bash
# After triggering server-side changes, inspect the persisted timestamps
cat ~/.mcpc/sessions.json | jq '.sessions["test"].notifications'

# Expected output when all three catalogs changed:
# {
#   "tools": { "listChangedAt": "2026-03-24T10:42:17.000Z" },
#   "resources": { "listChangedAt": "2026-03-24T10:42:18.000Z" },
#   "prompts": { "listChangedAt": "2026-03-24T10:42:19.000Z" }
# }
```

### Verify server declares notification capabilities

```bash
mcpc --json @test | jq '.capabilities'
# Look for:
# "tools": { "listChanged": true }
# "resources": { "listChanged": true, "subscribe": true }
# "prompts": { "listChanged": true }
```

---

## Subscribing to resource changes

`resources/updated` fires only for resources you have explicitly subscribed to. The server must
advertise `capabilities.resources.subscribe: true`.

```bash
# Subscribe — bridge sends resources/subscribe to server
mcpc @test resources-subscribe <uri>

# Now any server-side change to that resource URI triggers resources/updated
# In shell mode it prints: [HH:MM:SS] Resource updated

# Unsubscribe when done
mcpc @test resources-unsubscribe <uri>
```

Subscriptions live for the lifetime of the bridge process. They are not persisted across bridge
restarts. After a bridge restart you must re-subscribe.

---

## Progress notifications boundary

The MCP protocol may still carry `progress` or `tasks/status` notifications internally, but `mcpc 0.1.11` does not expose a public `--task`, `--detach`, `tasks-get`, or `tasks-list` workflow.

For operator-facing guidance:

- Do not instruct users to run `tools-call --task`
- Do not instruct users to poll `tasks-*` commands
- Use a higher `--timeout` for slow synchronous calls instead

---

## Building notification-aware test scripts

```bash
#!/usr/bin/env bash
# Test that server sends tools/list_changed when a tool is added.

SESSION="@test"

# Snapshot before
BEFORE=$(cat ~/.mcpc/sessions.json | jq -r ".sessions[\"test\"].notifications.tools.listChangedAt // \"none\"")

# Trigger server-side change here (server-specific, e.g. a REST call or config change)
# ...

# Wait briefly for notification to propagate and be written to disk
sleep 2

# Snapshot after
AFTER=$(cat ~/.mcpc/sessions.json | jq -r ".sessions[\"test\"].notifications.tools.listChangedAt // \"none\"")

if [ "$BEFORE" = "$AFTER" ]; then
  echo "FAIL: tools/list_changed was not received (timestamps match)"
  exit 1
else
  echo "PASS: tools/list_changed received at $AFTER"
fi
```

For resource subscription testing:

```bash
#!/usr/bin/env bash
# Subscribe, trigger a change, and check logs for resources/updated.

SESSION="@test"
URI="resource://my-server/config"

mcpc $SESSION resources-subscribe "$URI"

# Trigger server-side resource update here
# ...

sleep 2

# Check bridge log for the notification
LOG=$(ls ~/.mcpc/logs/bridge-test.log 2>/dev/null)
if [ -n "$LOG" ] && grep -q "resources/updated" "$LOG"; then
  echo "PASS: resources/updated notification received"
else
  echo "FAIL: no resources/updated in bridge log"
fi

mcpc $SESSION resources-unsubscribe "$URI"
```

---

## Key source locations

- `src/lib/types.ts` — `NotificationType`, `NotificationData`, `SessionNotifications`, `TaskUpdate`
- `src/bridge/index.ts` — `broadcastNotification()`, `updateNotificationTimestamp()`, `connectToMcp()` (handler registration)
- `src/cli/shell.ts` — `displayNotification()`, `setupNotificationListener()`
- `src/lib/session-client.ts` — `setupNotificationForwarding()` (IPC → EventEmitter)
- `src/cli/commands/tools.ts` — tool-call handling and any notification/progress wiring that still exists internally
