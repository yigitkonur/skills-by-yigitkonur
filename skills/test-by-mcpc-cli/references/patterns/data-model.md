# mcpc data model reference

This document is the definitive type and data reference for `mcpc`. It covers every type, constant, file format, and utility relevant to reading and writing session/profile state, communicating over IPC, and handling errors.

Source files: `src/lib/types.ts`, `src/lib/sessions.ts`, `src/lib/utils.ts`, `src/lib/file-lock.ts`, `src/lib/errors.ts`.

---

## Critical command syntax

```bash
# Get session info as JSON (single session)
mcpc --json @session

# List all sessions as JSON
mcpc --json

# Human-readable equivalents
mcpc @session
mcpc
```

---

## Constants

| Constant | Value | Meaning |
|---|---|---|
| `KEEPALIVE_INTERVAL_MS` | `30000` | How often the bridge sends a ping to the MCP server (milliseconds) |
| `DISCONNECTED_THRESHOLD_MS` | `65000` | `2 × 30000 + 5000` — time without a ping response before a session is considered disconnected |
| `LOCK_TIMEOUT` | `5000` | Maximum time `withFileLock` will wait to acquire a lock (milliseconds) |
| `REDACTED_HEADER_VALUE` | `"<redacted>"` | Sentinel stored in sessions.json in place of actual header values |

`DISCONNECTED_THRESHOLD_MS` is derived as `2 * KEEPALIVE_INTERVAL_MS + 5000`, meaning approximately two missed pings plus a 5-second buffer.

### Session name regex

```
/^@[a-zA-Z0-9_-]{1,64}$/
```

- Must start with `@`
- Followed by 1–64 characters: letters, digits, hyphens, underscores
- No spaces, no dots, no slashes

### Profile name regex

```
/^[a-zA-Z0-9_-]{1,64}$/
```

- No `@` prefix (unlike session names)
- 1–64 alphanumeric characters with hyphens and underscores

---

## File path utilities

All paths live under `~/.mcpc/` by default. The root can be overridden with the `MCPC_HOME_DIR` environment variable.

| Function | Returns | Description |
|---|---|---|
| `getMcpcHome()` | `string` | Root directory, default `~/.mcpc`. Respects `MCPC_HOME_DIR` env var. Expands `~` and resolves to absolute path. |
| `getSessionsFilePath()` | `string` | `~/.mcpc/sessions.json` |
| `getAuthProfilesFilePath()` | `string` | `~/.mcpc/profiles.json` |
| `getSocketPath(sessionName)` | `string` | Unix: `~/.mcpc/bridges/<sessionName>.sock` · Windows: `\\.\pipe\mcpc-<homeHash>-<sessionName>` |
| `getLogsDir()` | `string` | `~/.mcpc/logs/` |
| `getBridgesDir()` | `string` | `~/.mcpc/bridges/` |
| `getWalletsFilePath()` | `string` | `~/.mcpc/wallets.json` |

### Windows named pipe naming

On Windows, named pipes are global (no per-user isolation), so `getSocketPath` includes an 8-character hex hash of `getMcpcHome()`:

```
\\.\pipe\mcpc-<sha256(mcpcHome)[0..8]>-@session-name
```

### Directory layout on disk

```
~/.mcpc/
├── sessions.json          # Active sessions (0600 perms)
├── profiles.json          # OAuth auth profiles (0600 perms)
├── wallets.json           # x402 wallet data
├── history                # Interactive shell command history (last 1000)
├── bridges/
│   ├── @my-session.sock   # Unix domain socket per session (macOS/Linux)
│   └── ...
└── logs/
    ├── bridge-@my-session.log  # Bridge process logs (max 10 MB, 5 rotated files)
    └── ...
```

---

## Type definitions

### `ServerConfig`

Used in both the Claude Desktop–compatible config file format and internally in `SessionData.server`.

```typescript
interface ServerConfig {
  url?: string;                      // HTTP transport — the MCP server URL (required for http)
  headers?: Record<string, string>;  // HTTP transport — custom request headers
  command?: string;                  // stdio transport — command to execute (required for stdio)
  args?: string[];                   // stdio transport — command arguments
  env?: Record<string, string>;      // stdio transport — environment variables
  timeout?: number;                  // Connection timeout in seconds
}
```

Transport is determined by which field is present:
- `url` present → Streamable HTTP transport
- `command` present → stdio transport

In `sessions.json`, header **values** are always replaced with `"<redacted>"`. The actual values live in the OS keychain.

**Config file example (HTTP):**

```json
{
  "url": "https://mcp.apify.com",
  "headers": { "Authorization": "Bearer ${APIFY_TOKEN}" },
  "timeout": 300
}
```

**Config file example (stdio):**

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
  "env": { "DEBUG": "mcp:*" }
}
```

---

### `ProxyConfig`

When a session is started with proxy mode, the bridge launches a local HTTP MCP server that forwards to the upstream server without exposing original auth tokens.

```typescript
interface ProxyConfig {
  host: string;  // Host to bind proxy server, typically "127.0.0.1"
  port: number;  // Port to bind proxy server
}
```

---

### `SessionStatus`

```typescript
type SessionStatus = 'active' | 'unauthorized' | 'expired' | 'crashed';
```

| Value | Meaning | Recovery |
|---|---|---|
| `'active'` | Session is healthy and responding | — |
| `'unauthorized'` | Server rejected auth (401/403) or token refresh failed | `mcpc login <server>`, then `mcpc @session restart` |
| `'expired'` | Server signalled session is no longer valid (typically 404) | `mcpc @session restart` |
| `'crashed'` | Bridge process died; auto-restarts on next command | Automatic |

Sessions with no `status` field are treated as `'active'`.

A session in `sessions.json` with no live bridge PID and not already in `expired`/`unauthorized` is automatically set to `'crashed'` by `consolidateSessions()`.

---

### `SessionNotifications`

Tracks the last time the bridge received a list-change notification from the server.

```typescript
interface SessionNotifications {
  tools?: {
    listChangedAt?: string;     // ISO 8601 — last tools/list_changed notification
  };
  prompts?: {
    listChangedAt?: string;     // ISO 8601 — last prompts/list_changed notification
  };
  resources?: {
    listChangedAt?: string;     // ISO 8601 — last resources/list_changed notification
  };
}
```

Used for cache invalidation: if `listChangedAt` is newer than the local cache entry's timestamp, the CLI re-fetches from the server.

---

### `ActiveTaskEntry`

An entry persisted in `SessionData.activeTasks` so that async tool calls can be recovered if the bridge crashes mid-flight.

```typescript
interface ActiveTaskEntry {
  taskId: string;    // Opaque task ID assigned by the server
  toolName: string;  // Tool that created this task
  createdAt: string; // ISO 8601 creation time
}
```

---

### `SessionData`

The core type stored per session in `sessions.json`.

```typescript
interface SessionData {
  name: string;                             // Session name including @ prefix, e.g. "@my-session"
  server: ServerConfig;                     // Transport config — header values replaced with "<redacted>"
  profileName?: string;                     // Auth profile name (OAuth sessions only)
  x402?: boolean;                           // x402 auto-payment enabled
  insecure?: boolean;                       // Skip TLS certificate verification
  pid?: number;                             // Bridge process PID (absent if not running)
  protocolVersion?: string;                 // Negotiated MCP protocol version, e.g. "2025-11-25"
  mcpSessionId?: string;                    // Server-assigned session ID for Streamable HTTP resumption
  serverInfo?: {
    name: string;
    version: string;
  };
  status?: SessionStatus;                   // Health status, defaults to "active" when absent
  proxy?: ProxyConfig;                      // Local proxy server config (if proxy mode enabled)
  notifications?: SessionNotifications;    // Last list-change notification timestamps
  activeTasks?: Record<string, ActiveTaskEntry>; // taskId -> task entry for crash recovery
  createdAt: string;                        // ISO 8601 — when the session was first created
  lastSeenAt?: string;                      // ISO 8601 — last successful server response
}
```

Field-by-field notes:

- `name` — stored redundantly inside the object even though it is also the map key in `sessions.json`. This makes the record self-describing when extracted individually.
- `server.headers` — values are always `"<redacted>"` at rest. Real values are retrieved from the OS keychain keyed as `mcpc:session:<name>:bearer-token`.
- `pid` — present only while a bridge process is alive. Cleared by `consolidateSessions()` when `isProcessAlive(pid)` returns false.
- `mcpSessionId` — the `MCP-Session-Id` header value provided by the server during initialization. Required by the client on all subsequent requests to that server.
- `lastSeenAt` — compared against `DISCONNECTED_THRESHOLD_MS` to determine whether a session is "live" or "disconnected" in the status display.
- `activeTasks` — keyed by `taskId`. Populated when a detached/async tool call is in progress so it can be polled after a bridge restart.

---

### `SessionsStorage`

The top-level shape of `sessions.json`.

```typescript
interface SessionsStorage {
  sessions: Record<string, SessionData>; // sessionName (with @) -> SessionData
}
```

---

### `AuthProfile`

Stored in `profiles.json`. Only OAuth authentication is supported. Tokens themselves are in the OS keychain, not here.

```typescript
interface AuthProfile {
  name: string;               // Profile name, e.g. "default", "personal", "work"
  serverUrl: string;          // Normalized server URL, e.g. "https://mcp.apify.com"
  authType: 'oauth';          // Always "oauth" (only type supported)
  oauthIssuer: string;        // OAuth issuer URL, e.g. "https://auth.apify.com"
  scopes?: string[];          // Requested OAuth scopes
  userEmail?: string;         // From OIDC id_token "email" claim (if available)
  userName?: string;          // From OIDC id_token "name" claim (if available)
  userSubject?: string;       // From OIDC id_token "sub" claim — stable unique user ID
  createdAt: string;          // ISO 8601 — when profile was first created
  authenticatedAt?: string;   // ISO 8601 — last successful token use
  refreshedAt?: string;       // ISO 8601 — last time the token was refreshed
}
```

OS keychain key for tokens: `mcpc:auth:<serverUrl>:<profileName>:tokens`

Value stored in keychain: `{"access_token": "...", "refresh_token": "...", "expires_at": <unix-timestamp>}`

---

### `AuthProfilesStorage`

The top-level shape of `profiles.json`.

```typescript
interface AuthProfilesStorage {
  profiles: Record<string, Record<string, AuthProfile>>;
  // Outer key: normalized serverUrl (e.g. "https://mcp.apify.com")
  // Inner key: profileName (e.g. "default", "personal")
}
```

---

### `WalletData` and `WalletsStorage`

Stored in `~/.mcpc/wallets.json`. Only a single wallet is supported.

```typescript
interface WalletData {
  address: string;    // Ethereum-style wallet address
  privateKey: string; // Hex string starting with 0x
  createdAt: string;  // ISO 8601
}

interface WalletsStorage {
  version: 1;          // Schema version — always 1 currently
  wallet?: WalletData; // Absent if no wallet configured
}
```

---

## IPC message types

The CLI process and bridge process communicate over a Unix domain socket (or Windows named pipe) using `IpcMessage` objects serialized as newline-delimited JSON.

### `IpcMessageType`

```typescript
type IpcMessageType =
  | 'request'              // CLI → bridge: forward an MCP method call
  | 'response'             // bridge → CLI: result or error for a request
  | 'shutdown'             // CLI → bridge: graceful shutdown
  | 'notification'         // bridge → CLI: async notification from MCP server
  | 'task-update'          // bridge → CLI: progress update for an async task
  | 'set-auth-credentials' // CLI → bridge: push auth credentials after login
  | 'set-x402-wallet';     // CLI → bridge: push x402 wallet credentials
```

### `NotificationType`

```typescript
type NotificationType =
  | 'tools/list_changed'
  | 'resources/list_changed'
  | 'resources/updated'
  | 'prompts/list_changed'
  | 'progress'
  | 'logging/message'
  | 'tasks/status';
```

### `NotificationData`

```typescript
interface NotificationData {
  method: NotificationType;
  params?: unknown;
}
```

### `TaskUpdate`

Sent from bridge to CLI as in-flight progress for async tool calls.

```typescript
interface TaskUpdate {
  taskId: string;
  status: 'working' | 'input_required' | 'completed' | 'failed' | 'cancelled';
  statusMessage?: string;
  progressMessage?: string; // From notifications/progress
  progress?: number;        // Current progress value
  progressTotal?: number;   // Total progress value
  createdAt?: string;       // ISO 8601
  lastUpdatedAt?: string;   // ISO 8601
}
```

### `AuthCredentials`

Sent from CLI to bridge via `set-auth-credentials` IPC message.

```typescript
interface AuthCredentials {
  serverUrl: string;
  profileName: string;
  clientId?: string;      // OAuth client ID (for token refresh)
  refreshToken?: string;  // OAuth refresh token
  headers?: Record<string, string>; // HTTP headers from --header flags (from keychain)
}
```

### `X402WalletCredentials`

Sent from CLI to bridge via `set-x402-wallet` IPC message.

```typescript
interface X402WalletCredentials {
  address: string;
  privateKey: string; // Hex with 0x prefix
}
```

### `IpcMessage` — complete structure

```typescript
interface IpcMessage {
  type: IpcMessageType;
  id?: string;                       // Request ID for correlation (e.g. "req_1234567890_1")
  method?: string;                   // MCP method name (e.g. "tools/list", "tools/call")
  params?: unknown;                  // Method parameters
  timeout?: number;                  // Per-request timeout in seconds (overrides session default)
  result?: unknown;                  // Response result (present on type='response' success)
  notification?: NotificationData;   // Present on type='notification'
  taskUpdate?: TaskUpdate;           // Present on type='task-update'
  authCredentials?: AuthCredentials; // Present on type='set-auth-credentials'
  x402Wallet?: X402WalletCredentials; // Present on type='set-x402-wallet'
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}
```

Request IDs are generated as `req_<Date.now()>_<incrementingCounter>`, e.g. `req_1700000000000_1`.

---

## Error hierarchy and exit codes

### Class hierarchy

```
Error
└── McpError               (base, has .code and .details)
    ├── ClientError        (code: 1)
    ├── ServerError        (code: 2)
    ├── NetworkError       (code: 3)
    └── AuthError          (code: 4)
```

### Exit code table

| Code | Class | When used |
|---|---|---|
| `0` | — | Success |
| `1` | `ClientError` | Invalid arguments, unknown commands, validation errors, file lock conflicts |
| `2` | `ServerError` | MCP tool execution failures, resource not found, server-returned errors |
| `3` | `NetworkError` | Connection failures, timeouts, DNS errors |
| `4` | `AuthError` | Invalid credentials, 401/403 responses, token expiry |

### `McpError` fields

```typescript
class McpError extends Error {
  code: number;       // Exit code (1–4)
  details?: unknown;  // Arbitrary structured context
  name: string;       // Set to constructor name: "ClientError", "ServerError", etc.
}
```

### JSON representation (in `--json` mode)

When any `McpError` is caught and output mode is `--json`, `toJSON()` produces:

```json
{
  "error": "ClientError",
  "message": "Session not found: @my-session",
  "code": 1,
  "details": null
}
```

---

## File locking — `withFileLock()`

```typescript
async function withFileLock<T>(
  filePath: string,
  operation: () => Promise<T>,
  defaultContent: string = '{}'
): Promise<T>
```

Uses the `proper-lockfile` npm package. Behavior:

1. Ensures the directory exists (`mkdir -p`)
2. If the file does not exist, creates it with `defaultContent` at mode `0600`
3. Acquires an advisory lock on the file
   - Stale lock timeout: 10 seconds (handles crashed processes)
   - Retry: up to 10 attempts, 200ms–5000ms between retries, randomized
4. Runs `operation()` while holding the lock
5. Always releases the lock in a `finally` block
6. On `ELOCKED` error: throws `ClientError` with "File is locked by another process"

Default content for `sessions.json` lock calls: `'{"sessions":{}}'` (pretty-printed with 2 spaces).

The lock creates a `.lock` file adjacent to `filePath` (e.g., `sessions.json.lock`).

---

## Atomic writes

Sessions and profiles are never written directly to disk. The pattern is:

```
1. Compute target path:  ~/.mcpc/sessions.json
2. Generate temp path:   ~/.mcpc/.sessions-<timestamp>-<pid>.tmp
3. Write JSON to temp file (mode 0600, encoding utf-8)
4. Rename temp → target  (atomic on POSIX; same filesystem guaranteed)
5. On any error: unlink temp file, re-throw
```

The temp file is always placed in the same directory as the target to avoid `EXDEV` errors on Linux (rename fails across filesystem boundaries, e.g. `/tmp` vs `~/.mcpc`).

JSON serialization uses `JSON.stringify(storage, null, 2)` — 2-space indented, no trailing newline.

---

## URL normalization rules

`normalizeServerUrl(str)` in `utils.ts`:

1. **Scheme inference** — if `://` is absent:
   - Hostname is `localhost` or `127.0.0.1` → prepend `http://`
   - Any other hostname → prepend `https://`
2. **Validation** — must parse as a valid URL with `http:` or `https:` protocol; throws on failure
3. **Normalization steps applied:**
   - `hostname` → lowercased
   - `username` → cleared
   - `password` → cleared
   - `hash` → cleared
4. **Trailing slash removal** — if `pathname === '/'` and no query string, the trailing slash is stripped

Examples:

| Input | Output |
|---|---|
| `mcp.apify.com` | `https://mcp.apify.com` |
| `localhost:3000` | `http://localhost:3000` |
| `127.0.0.1:8080/path` | `http://127.0.0.1:8080/path` |
| `https://Example.COM/` | `https://example.com` |
| `https://user:pass@example.com#frag` | `https://example.com` |
| `https://example.com/api/v1` | `https://example.com/api/v1` |

`getServerHost(urlString)` extracts the canonical host identifier:
- Standard ports (443 for https, 80 for http) → returns `hostname` only
- Non-standard ports → returns `hostname:port`

Examples: `https://mcp.apify.com` → `mcp.apify.com`, `http://localhost:3000` → `localhost:3000`

---

## JSON shapes for command output

### `mcpc --json` (session list)

The top-level array of session objects. Each entry mirrors `SessionData` with `sessionName` as the key field name.

```json
[
  {
    "sessionName": "@apify",
    "server": {
      "url": "https://mcp.apify.com",
      "headers": { "Authorization": "<redacted>" }
    },
    "status": "active",
    "pid": 12345,
    "protocolVersion": "2025-11-25",
    "mcpSessionId": "sess_abc123",
    "serverInfo": { "name": "Apify MCP Server", "version": "1.0.0" },
    "profileName": "default",
    "createdAt": "2025-12-14T10:00:00.000Z",
    "lastSeenAt": "2025-12-14T10:05:30.000Z"
  }
]
```

### `mcpc --json @session` (single session info)

```json
{
  "sessionName": "@apify",
  "server": {
    "url": "https://mcp.apify.com"
  },
  "status": "active",
  "pid": 12345,
  "protocolVersion": "2025-11-25",
  "serverInfo": { "name": "Apify MCP Server", "version": "1.0.0" },
  "createdAt": "2025-12-14T10:00:00.000Z",
  "lastSeenAt": "2025-12-14T10:05:30.000Z"
}
```

### `mcpc --json @session tools-list`

```json
{
  "tools": [
    {
      "name": "search-actors",
      "description": "Search for Actors in Apify Store",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": { "type": "string", "description": "Search query" }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### `mcpc --json @session tools-call <tool-name> [args]`

Success:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Found 5 actors matching 'web crawler'..."
    }
  ],
  "isError": false
}
```

Tool-level error (exit code 2):

```json
{
  "content": [
    {
      "type": "text",
      "text": "Tool execution failed: invalid argument"
    }
  ],
  "isError": true
}
```

### `mcpc --json @session resources-list`

```json
{
  "resources": [
    {
      "uri": "file:///tmp/data.json",
      "name": "data.json",
      "mimeType": "application/json",
      "description": "Runtime data file"
    }
  ]
}
```

### `mcpc --json @session resources-read <uri>`

```json
{
  "contents": [
    {
      "uri": "file:///tmp/data.json",
      "mimeType": "application/json",
      "text": "{\"key\": \"value\"}"
    }
  ]
}
```

### `mcpc --json @session prompts-list`

```json
{
  "prompts": [
    {
      "name": "summarize",
      "description": "Summarize a document",
      "arguments": [
        { "name": "document", "description": "Document text", "required": true }
      ]
    }
  ]
}
```

### `mcpc --json @session prompts-get <name> [args]`

```json
{
  "description": "Summarize a document",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Please summarize the following: ..."
      }
    }
  ]
}
```

### Error JSON output (any command)

```json
{
  "error": "NetworkError",
  "message": "Connection refused to https://mcp.apify.com",
  "code": 3,
  "details": null
}
```

Exit code of the process matches `code` field (1–4) or 0 on success.

---

## `sessions.json` on disk

Full example with two sessions — one HTTP with OAuth, one stdio:

```json
{
  "sessions": {
    "@apify": {
      "name": "@apify",
      "server": {
        "url": "https://mcp.apify.com",
        "timeout": 300
      },
      "profileName": "default",
      "status": "active",
      "pid": 12345,
      "protocolVersion": "2025-11-25",
      "mcpSessionId": "sess_abc123xyz",
      "serverInfo": {
        "name": "Apify MCP Server",
        "version": "1.2.0"
      },
      "notifications": {
        "tools": { "listChangedAt": "2025-12-14T10:03:00.000Z" },
        "prompts": {},
        "resources": {}
      },
      "createdAt": "2025-12-14T09:00:00.000Z",
      "lastSeenAt": "2025-12-14T10:05:30.000Z"
    },
    "@fs": {
      "name": "@fs",
      "server": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {}
      },
      "status": "crashed",
      "protocolVersion": "2025-11-25",
      "serverInfo": {
        "name": "filesystem",
        "version": "0.6.2"
      },
      "createdAt": "2025-12-13T08:00:00.000Z",
      "lastSeenAt": "2025-12-13T12:00:00.000Z"
    }
  }
}
```

Notes:
- File permissions: `0600` (owner read/write only)
- Pretty-printed with 2-space indentation
- Sessions with `status: "expired"` or `status: "unauthorized"` are removed by `consolidateSessions(cleanExpired: true)` on the next command
- The `pid` field is absent when the bridge is not running

---

## `profiles.json` on disk

```json
{
  "profiles": {
    "https://mcp.apify.com": {
      "default": {
        "name": "default",
        "serverUrl": "https://mcp.apify.com",
        "authType": "oauth",
        "oauthIssuer": "https://auth.apify.com",
        "scopes": ["tools:read", "tools:write"],
        "userEmail": "user@example.com",
        "userName": "Alice",
        "userSubject": "auth0|abc123",
        "createdAt": "2025-12-01T09:00:00.000Z",
        "authenticatedAt": "2025-12-14T09:00:00.000Z",
        "refreshedAt": "2025-12-14T10:00:00.000Z"
      },
      "work": {
        "name": "work",
        "serverUrl": "https://mcp.apify.com",
        "authType": "oauth",
        "oauthIssuer": "https://auth.apify.com",
        "scopes": ["tools:read"],
        "userEmail": "alice@corp.example.com",
        "createdAt": "2025-12-10T14:00:00.000Z",
        "authenticatedAt": "2025-12-12T08:30:00.000Z"
      }
    }
  }
}
```

Notes:
- File permissions: `0600`
- Outer key is the **normalized** server URL (result of `normalizeServerUrl()`)
- Inner key is the profile name (validated by `isValidProfileName()`)
- Tokens are never stored here — they live in the OS keychain
- OS keychain key format: `mcpc:auth:<serverUrl>:<profileName>:tokens`

---

## `consolidateSessions()` logic

Called at the start of every `mcpc` command. Single file lock for efficiency.

```
For each session in sessions.json:
  if record is missing/null → delete it
  if cleanExpired && status is "expired" or "unauthorized":
    → delete session record
    → remove keychain headers and proxy bearer token
    → unlink socket file (Unix only)
  if pid is set && isProcessAlive(pid) returns false:
    → clear pid
    → if status is not "crashed"/"expired"/"unauthorized" → set status = "crashed"
  if pid is absent && status is not "crashed"/"expired"/"unauthorized":
    → set status = "crashed"

If any changes → write sessions.json atomically
Return: { crashedBridges, expiredSessions, sessions }
```

`isProcessAlive(pid)` sends signal 0 to the PID. Returns `true` if the process exists, `false` if it does not (ESRCH) or permission is denied (EPERM, which means it exists but is owned by another user — treated as alive).

---

## Session update merge semantics

`updateSession()` does a **shallow merge** of top-level fields, with one exception:

- `notifications` field → **deep merged** at two levels (top-level keys `tools`/`prompts`/`resources`, then their inner objects) to preserve existing timestamps while updating only the changed subkeys.

`name` and `createdAt` are always preserved from the existing record, regardless of what `updates` contains.

---

## `McpConfig` — config file format

Compatible with Claude Desktop's `mcp.json` format:

```typescript
interface McpConfig {
  mcpServers: Record<string, ServerConfig>;
}
```

Used with the `<file>:<entry>` server format: `mcpc ~/.vscode/mcp.json:filesystem connect @fs`

Environment variable substitution is supported in config files: `${VAR_NAME}` is expanded at load time.
