# output formatting reference

Source: `src/cli/output.ts` (1,205 lines), `src/cli/tool-result.ts`, `src/lib/errors.ts`

Critical syntax: `mcpc <target> connect @<session>`, `mcpc @session close`, `mcpc --json @session command`

---

## how formatOutput() routes between human and JSON modes

`formatOutput(data, mode, options?)` is the single entry point for all CLI output.

```
formatOutput(data, mode)
  ├── mode === 'json'  → formatJson(data)    // JSON.stringify, optional TTY highlight
  └── mode === 'human' → formatHuman(data)   // type-dispatched rendering + trailing \n
```

**Routing inside formatHuman — dispatch table:**

| Data shape | Handler |
|---|---|
| `null` / `undefined` | gray `(no data)` |
| object with `content: [{type:'text', text:...}]` (exactly one item) | quadruple-backtick fence via `extractSingleTextContent` |
| array where first element has `inputSchema` | `formatTools()` |
| array where first element has `uriTemplate` | `formatResourceTemplates()` |
| array where first element has `uri` | `formatResources()` |
| array where first element has `arguments` (and `name`) | `formatPrompts()` |
| object with `messages[].role` and `.content` | `formatPromptResult()` |
| generic object | `formatObject()` — `cyan(key):` value per line |
| primitive | `String(data)` |

**Trailing newline rule:** human mode appends `\n` unless output already ends with `\n` or ``````. This prevents double-blank-lines after fenced tool-call results.

---

## TTY detection and color stripping

`formatJson(data)` checks `process.stdout.isTTY` before applying syntax highlighting:

```
formatJson(data)
  ├── JSON.stringify(data, null, 2)
  └── if process.stdout.isTTY → highlightJson(json)   // colors in interactive terminal
      else                    → plain JSON string      // safe for pipes and files
```

Piping to `jq`, a file, or another process strips all ANSI codes automatically. No `--no-color` flag is needed. Human mode relies on `chalk` which does the same auto-detection.

---

## highlightJson() color scheme

Applies one regex pass. Only active when `process.stdout.isTTY`:

| Token | Color |
|---|---|
| Object key (including quotes; colon is unstyled) | `chalk.cyan` |
| String value | `chalk.green` |
| `true`, `false`, `null` | `chalk.magenta` |
| Number (integer, float, scientific) | `chalk.yellow` |

---

## JSON shapes for every command

All JSON is produced by `JSON.stringify(data, null, 2)` — no wrapper envelopes. What follows is the literal root of each response.

### tools-list — direct array (not `{tools:[...]}`)

```json
[
  {
    "name": "search-actors",
    "description": "Search for Apify actors",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": { "type": "string" },
        "limit": { "type": "number" }
      },
      "required": ["query"]
    },
    "annotations": { "readOnlyHint": true, "title": "Search actors" }
  }
]
```

The handler calls `formatOutput(result.tools, ...)` where `result.tools` is the raw array.

### tools-get — single tool object

Same shape as one element of tools-list.

### tools-call — raw MCP CallToolResult

mcpc passes through the raw MCP response via `JSON.stringify`. The base MCP spec defines `content` and `isError`, but servers may include additional fields.

**Base shape (MCP spec):**

```json
{
  "content": [{ "type": "text", "text": "result text" }],
  "isError": false
}
```

**Real-world servers often include extra fields:**

```json
{
  "_meta": { "mimeType": "text/markdown" },
  "content": [{ "type": "text", "text": "result text" }],
  "structuredContent": {
    "content": "same text",
    "metadata": { "execution_time_ms": 721, "total_results": 10 }
  }
}
```

- `_meta` — MIME type hint (server extension, not in base spec)
- `structuredContent` — server-specific structured data with execution metadata
- These extra fields are useful for monitoring (e.g., `jq '.structuredContent.metadata.execution_time_ms'`) but are not guaranteed across servers

**Error responses have a different shape** — no `_meta`, no `structuredContent`:

```json
{
  "content": [{ "type": "text", "text": "MCP error -32602: Tool not found" }],
  "isError": true
}
```

**Critical:** Error responses return **exit code 0**, not 2. Always check `isError` in JSON.

Multi-content / image:

```json
{
  "content": [
    { "type": "text", "text": "label" },
    { "type": "image", "mimeType": "image/png", "data": "<base64>" }
  ],
  "isError": false
}
```

Detached task start (`--detach`):

```json
{ "taskId": "task-abc123", "status": "working" }
```

### resources-list / resources-templates-list / prompts-list

All return **direct arrays** at the root (same pattern as tools-list).

### resources-read — raw ReadResourceResult

```json
{
  "contents": [
    { "uri": "file:///data/out.json", "mimeType": "application/json", "text": "{ ... }" }
  ]
}
```

Blob resources use `"blob"` (base64) instead of `"text"`.

### prompts-get — raw GetPromptResult

```json
{
  "description": "Summarize the following text",
  "messages": [
    { "role": "user", "content": { "type": "text", "text": "Please summarize: ..." } }
  ]
}
```

### session info — `mcpc --json @session`

Wraps MCP `InitializeResult` with an `_mcpc` block:

```json
{
  "_mcpc": {
    "sessionName": "@apify",
    "profileName": "default",
    "server": { "url": "https://mcp.apify.com", "headers": { "Authorization": "[REDACTED]" } }
  },
  "protocolVersion": "2025-11-25",
  "capabilities": { "tools": { "listChanged": true }, "resources": {}, "logging": {} },
  "serverInfo": { "name": "Apify MCP Server", "version": "1.0.0" },
  "instructions": "...",
  "tools": [ ... ]
}
```

Sensitive header values are replaced with `"[REDACTED]"` before output.

### top-level listing — `mcpc --json`

```json
{
  "sessions": [
    {
      "name": "apify",
      "server": { "url": "https://mcp.apify.com" },
      "profileName": "default",
      "pid": 12345,
      "createdAt": "2025-12-01T10:00:00Z",
      "lastSeenAt": "2025-12-01T10:05:00Z",
      "status": "live"
    }
  ],
  "profiles": [
    { "name": "default", "serverUrl": "https://mcp.apify.com", "authType": "oauth" }
  ]
}
```

`status` is computed at list time: `"live"`, `"disconnected"`, `"crashed"`, `"unauthorized"`, or `"expired"`.

### session close — `mcpc --json @session close`

Success: `{ "sessionName": "@apify", "closed": true }`

Failure (stderr): `{ "sessionName": "@apify", "closed": false, "error": "Session not found: @apify" }`

---

## error formatting in JSON mode

There are **two distinct error paths** with different JSON shapes:

### CLI errors (exit code 1-4) — written to stderr

`formatJsonError(error, code)` emits only two fields — the message string and the numeric code:

```json
{ "error": "Tool not found: search-actors", "code": 1 }
```

These are mcpc CLI-level errors, not MCP protocol errors.

| Code | Class | Cause |
|---|---|---|
| 1 | `ClientError` | Bad CLI args, unknown mcpc command, session not found |
| 2 | `ServerError` | Transport-level server failure (rare) |
| 3 | `NetworkError` | Connection failed, timeout |
| 4 | `AuthError` | Invalid credentials, 401/403 |

### MCP server errors (exit code 0!) — written to stdout

When the MCP server returns an error (validation failure, tool-not-found, tool execution error), mcpc treats the response as a successful CLI operation and writes it to **stdout** with **exit code 0**:

```json
{
  "content": [{ "type": "text", "text": "MCP error -32602: Input validation error: ..." }],
  "isError": true
}
```

**This is the most common mistake in scripted tests.** Checking `$?` alone will miss these. Always check `jq '.isError // false'` on the JSON output.

All CLI error output goes to **stderr**. All MCP responses (including MCP errors) go to **stdout**.

---

## human vs JSON side-by-side

### tools-list

**Human:**
```
[@apify → https://mcp.apify.com (HTTP)]

Tools (2):
* `search-actors(query: str, limit?: num)` [read-only]
* `run-actor(actorId: str, input?: obj, …)`

For full tool details and schema, run `mcpc @apify tools-list --full` or `mcpc @apify tools-get <name>`
```

**JSON:** bare array — see tools-list shape above.

### tools-call (single text result)

**Human:**
```
✓ Tool search-actors executed successfully
````
[{"id":"actor/123","name":"web-scraper"}]
````
```

**JSON:** `{ "content": [{ "type": "text", "text": "[...]" }], "isError": false }`

### error

**Human:** `Error: Tool not found: bad-tool` (red, to stderr)

**JSON (stderr, exit 1):** `{ "error": "Tool not found: bad-tool", "code": 1 }`

---

## tool call result display (human mode)

`extractSingleTextContent(data)` is called first. It matches exactly:

```ts
data.content.length === 1
&& data.content[0].type === 'text'
&& typeof data.content[0].text === 'string'
```

When matched, the text is unwrapped and wrapped in quadruple backticks:

```
````
<raw text content>
````
```

The backticks are `chalk.gray('````')` — dim so they appear in the terminal but won't be misread as triple-backtick fences by Markdown renderers.

For any other content shape (multiple items, image, structured), `formatHuman` falls through to `formatObject`, rendering each key-value pair as `cyan(key): value`.

**Prompt message content blocks (human mode):**

| `type` | Rendered as |
|---|---|
| `text` | quadruple-backtick fence with raw text |
| `image` | `[Image: mime/type]` + first 50 chars of base64 + `...` |
| `audio` | `[Audio: mime/type]` |
| `resource_link` | `[Resource link: uri]` |
| `resource` | `[Embedded resource: uri]` + text if present |

---

## session listing format (human mode)

Each session line: `formatSessionLine(session)`:

```
@apify → https://mcp.apify.com (HTTP, OAuth: default) ● live
@fs → npx -y @modelcontextprotocol/server-filesystem /tmp (stdio) ● live
@broken → https://mcp.example.com (HTTP) ○ crashed, 3h ago
  ↳ run: mcpc login mcp.example.com && mcpc @broken restart
```

Status dot colors: green `●` = live, yellow `●` = disconnected, yellow `○` = crashed, red `○` = unauthorized or expired. Time-ago (dim) is appended for non-live states and for live sessions idle > 5 minutes. Target URL truncated at 80 chars. OAuth profile name in magenta. Proxy sessions append green `[proxy: host:port]`.

**logTarget prefix** (before each session command, human mode only):

```
[@apify → https://mcp.apify.com (HTTP, OAuth: default)]

```

Suppressed entirely in JSON mode and when `options.hide` is true.

---

## tips for parsing output in scripts

Always use `--json` or `MCPC_JSON=1`. Human output is unstable across versions.

```bash
# tools-list returns a direct array — use .[]
mcpc --json @apify tools-list | jq '.[].name'

# filter a specific tool
mcpc --json @apify tools-list | jq '.[] | select(.name == "search-actors")'

# tools-call: get text from first content block
mcpc --json @apify tools-call search-actors query:=hello | jq -r '.content[0].text'

# session listing
mcpc --json | jq '.sessions[] | select(.status == "live") | .name'

# CLI errors go to stderr (exit 1-4); MCP errors go to stdout (exit 0)
# Must check BOTH exit code AND isError:
result=$(mcpc --json @apify tools-call search-actors '{"query":"test"}' 2>/dev/null); ec=$?
if [ $ec -ne 0 ]; then
  echo "CLI error (exit $ec)"
elif echo "$result" | jq -e '.isError // false' 2>/dev/null | grep -q true; then
  echo "MCP error: $(echo "$result" | jq -r '.content[0].text')"
fi

# MCPC_JSON=1 is equivalent to --json on every invocation
export MCPC_JSON=1
mcpc @apify tools-list | jq '.[].name'
```

**Key facts:**

1. `tools-list`, `resources-list`, `resources-templates-list`, `prompts-list` — bare arrays at root.
2. `tools-call` returns `{content:[...]}` with optional `isError`, `_meta`, `structuredContent` — always `.content[0].text` for text.
3. **Two error paths:** CLI errors (exit 1-4) go to stderr as `{error, code}`. MCP server errors (exit 0) go to stdout as `{content, isError: true}`. Always check both.
4. CLI error JSON has exactly two fields: `{error: string, code: number}`. MCP error JSON has `{content: [...], isError: true}`.
5. Session info (`mcpc --json @session`) has `_mcpc` alongside MCP `InitializeResult` fields.
6. Top-level listing (`mcpc --json`) has `{sessions:[], profiles:[]}`.
7. `close` returns `{sessionName, closed: bool}` and optionally `error`.
8. Piped output strips ANSI automatically — no extra flags needed.
