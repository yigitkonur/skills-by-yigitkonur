# Argument parsing in mcpc

Source: `src/cli/parser.ts` (552 lines)

## Command syntax overview

```
mcpc <target> connect @<session>          # top-level connect command
mcpc @session tools-call tool key:=value  # session sub-command with args
mcpc @session tools-call tool '{"k":"v"}' # inline JSON
echo '{"k":"v"}' | mcpc @session tools-call tool  # stdin
```

The `@` prefix distinguishes a named session handle from a bare URL or config
file path. All MCP operations (`tools-call`, `resources-read`, etc.) are routed
through a named session.

---

## parseServerArg() — URL vs config file detection

```typescript
export function parseServerArg(
  arg: string
): { type: 'url'; url: string } | { type: 'config'; file: string; entry: string } | null
```

### Decision tree (executed in order)

1. **Try arg as-is via `URL` constructor** — if it produces a non-empty `.host`,
   return `{ type: 'url', url: arg }`. Covers explicit schemes: `https://…`,
   `http://…`, `ftp://…`.

2. **Bail on `://` without a valid host** — if arg contains `://` but step 1
   failed, return `null` (invalid full-URL syntax). This prevents
   `https://host:badport` from being misclassified as a config entry where
   `file = "https"`.

3. **Try `https://` prefix for bare hostnames** — prepend `https://` and
   re-run `URL` validation. Skipped when:
   - arg starts with `/`, `~`, `.` (filesystem paths)
   - arg is a Windows drive path (`C:\…`, `C:/…`)
   - arg ends with `:` (dangling colon is not a valid hostname)

   On success, return `{ type: 'url', url: arg }` (url is the *original* arg,
   not the prefixed string — callers add the scheme themselves).

4. **Config file entry** — look for a colon separating `file:entry`. The left
   side must pass `looksLikeFilePath()`:
   - starts with `/` or `~` (Unix absolute/home-relative)
   - starts with `./` or `../` (explicit relative)
   - matches `/^[A-Za-z]:[/\\]/` (Windows drive: `C:\`, `C:/`)
   - contains `/` or `\`
   - ends in `.json`, `.yaml`, or `.yml` (any case)

   **Windows drive letter special case** — drive paths have a colon at position 1
   (`C:`). To find the entry separator, the code uses `arg.lastIndexOf(':')` when
   the arg matches `/^[A-Za-z]:[/\\]/`, skipping the drive colon:
   `C:\Users\me\mcp.json:filesystem` → `file="C:\Users\me\mcp.json"`, `entry="filesystem"`.

5. **Return `null`** — unrecognised format; caller reports an error.

### Examples

| Input | Result |
|---|---|
| `https://mcp.apify.com` | `{ type: 'url', url: 'https://mcp.apify.com' }` |
| `mcp.apify.com` | `{ type: 'url', url: 'mcp.apify.com' }` |
| `mcp.apify.com:8080` | `{ type: 'url', url: 'mcp.apify.com:8080' }` |
| `localhost:3000` | `{ type: 'url', url: 'localhost:3000' }` |
| `~/.vscode/mcp.json:filesystem` | `{ type: 'config', file: '~/.vscode/mcp.json', entry: 'filesystem' }` |
| `./mcp.json:myserver` | `{ type: 'config', file: './mcp.json', entry: 'myserver' }` |
| `C:\tools\mcp.json:server` | `{ type: 'config', file: 'C:\tools\mcp.json', entry: 'server' }` |
| `https://bad:port` | `null` |
| `bareword` | `null` |

---

## extractOptions() — pre-Commander flag extraction

```typescript
export function extractOptions(args: string[]): {
  timeout?: number;
  profile?: string;
  x402?: boolean;
  insecure?: boolean;
  verbose: boolean;
  json: boolean;
}
```

### Why it exists

Some flags (`--verbose`, `--json`, `--timeout`, `--profile`) must be known
before Commander parses the full command tree — for output formatting and auth
profile selection. `extractOptions` does one linear scan of `process.argv`
independently of Commander.

### What it does

- `verbose` — `args.includes('--verbose')` OR env `MCPC_VERBOSE` is truthy
  (`'1'`, `'true'`, `'yes'`, case-insensitive).
- `json` — `args.includes('--json') || args.includes('-j')` OR env `MCPC_JSON`.
- `timeout` — finds index of `'--timeout'`, reads `args[index + 1]`, parses
  with `parseInt`. Absent → `undefined` (not included in return object).
- `profile` — same index+1 pattern. Absent or empty → `undefined`.
- `x402` / `insecure` — boolean presence flags; absent → key omitted from return object.

### Env variables as defaults

| Env var | Controls |
|---|---|
| `MCPC_VERBOSE` | verbose logging (`--verbose`) |
| `MCPC_JSON` | JSON output mode (`--json`) |
| `MCPC_HOME_DIR` | data directory (not in parser.ts) |

Truthy string check: `normalized === '1' || normalized === 'true' || normalized === 'yes'`

---

## parseCommandArgs() — tool argument processing

```typescript
export function parseCommandArgs(args: string[] | undefined): Record<string, unknown>
```

### Three input formats (checked in order)

#### 1. key:=value pairs

The primary format for passing typed arguments from the shell:

```bash
mcpc @session tools-call my-tool name:=hello count:=10 enabled:=true
```

- Splits only at the **first** `":="` (`pair.indexOf(':=')`) — values containing
  `:=` are safe.
- Key is everything before `":="`. Empty key throws `ClientError`.
- Value is everything after `":="` and is passed to `autoParseValue()`.
- Any arg that does not contain `":="` (and is not inline JSON) throws
  `ClientError` with an example message.

`autoParseValue(value: string): unknown`:

```typescript
function autoParseValue(value: string): unknown {
  try {
    return JSON.parse(value);   // succeed → typed value
  } catch {
    return value;               // fail → keep as string
  }
}
```

JSON.parse is the sole arbiter of type. No custom number/boolean detection.

#### 2. Inline JSON (first arg starts with `{` or `[`)

```bash
mcpc @session tools-call my-tool '{"query":"hello","limit":10}'
mcpc @session tools-call my-tool '[1,2,3]'
```

- Only triggered when `args[0].startsWith('{') || args[0].startsWith('[')`.
- `args.length > 1` throws `ClientError` — inline JSON is an all-or-nothing
  argument; you cannot mix it with key:=value pairs.
- Parsed value must be a non-null object/array; primitives throw `ClientError`.
- Cast to `Record<string, unknown>` for the return type (arrays pass through).

#### 3. Stdin (piped input)

Stdin is not handled inside `parseCommandArgs`. The caller detects
`!process.stdin.isTTY` and calls `readStdinArgs()` when `args` is empty:

```typescript
export function hasStdinData(): boolean {
  return !process.stdin.isTTY;
}

export async function readStdinArgs(): Promise<Record<string, unknown>>
```

`readStdinArgs()` collects chunks via `'data'` events, joins to a string, and
calls `JSON.parse`. Requirements:
- Stdin must be valid JSON.
- Parsed value must be a non-null object. Arrays are rejected.
- Empty or whitespace-only stdin resolves to `{}`.

---

## parseProxyArg() — [HOST:]PORT parsing

```typescript
export function parseProxyArg(value: string): { host: string; port: number }
```

Default host is `127.0.0.1`.

Uses `value.lastIndexOf(':')` (not `indexOf`) to support IPv6 literals like
`::1:8080`, where multiple colons are present.

| Input | Result |
|---|---|
| `"8080"` | `{ host: '127.0.0.1', port: 8080 }` |
| `"0.0.0.0:8080"` | `{ host: '0.0.0.0', port: 8080 }` |
| `"localhost:3000"` | `{ host: 'localhost', port: 3000 }` |
| `"notaport"` | throws `ClientError` |
| `":8080"` | throws `ClientError` (empty host) |
| `"8080000"` | throws `ClientError` (port > 65535) |

Port must satisfy `!isNaN(port) && port > 0 && port <= 65535`.

---

## URL normalization (bare hostname → https://)

This logic lives in `parseServerArg`, step 3. The caller that ultimately builds
a connection URL applies the `https://` prefix. The parser returns the *original*
arg string as `url` (not the prefixed version) so the caller can decide whether
to use HTTP or HTTPS and can perform additional normalization (strip credentials,
fragment, etc.).

Per the CLAUDE.md design notes: "HTTPS enforced (HTTP auto-upgraded when no
scheme provided)". There is no explicit `http://` auto-prefix path — only
`https://` is tried.

---

## Type coercion table

All values go through `autoParseValue` → `JSON.parse` → fallback string.

| CLI input | Parsed type | Parsed value | Reason |
|---|---|---|---|
| `count:=10` | number | `10` | valid JSON number |
| `ratio:=3.14` | number | `3.14` | valid JSON float |
| `enabled:=true` | boolean | `true` | valid JSON keyword |
| `flag:=false` | boolean | `false` | valid JSON keyword |
| `ptr:=null` | null | `null` | valid JSON keyword |
| `name:=hello` | string | `"hello"` | not valid JSON → fallback |
| `id:='"123"'` | string | `"123"` | JSON string literal (quotes stripped by JSON.parse) |
| `config:='{"k":"v"}'` | object | `{ k: 'v' }` | valid JSON object |
| `items:='[1,2,3]'` | array | `[1, 2, 3]` | valid JSON array |
| `path:=/tmp/foo` | string | `"/tmp/foo"` | not valid JSON → fallback |
| `expr:=1+2` | string | `"1+2"` | not valid JSON → fallback |

---

## Edge cases and gotchas

### Strings that look like numbers

`id:=123` produces a **number** `123`. If the downstream tool expects a string ID,
use a JSON string literal with shell escaping:

```bash
# bash / zsh
id:='"123"'      # single-quoted shell string → JSON.parse sees "123" → string
```

### JSON in JSON

Nested objects work as long as the shell quoting wraps the whole value:

```bash
config:='{"key":"value","nested":{"a":1}}'
```

### Arrays

```bash
items:='[1,2,3]'        # → array [1,2,3]
tags:='["a","b","c"]'   # → array ["a","b","c"]
```

Arrays as a top-level argument can also use the inline JSON format:

```bash
mcpc @session tools-call tool '[1,2,3]'
```

### null and booleans

```bash
flag:=null     # → null (not the string "null")
active:=true   # → boolean true (not the string "true")
active:=false  # → boolean false
```

To pass the literal string `"null"` or `"true"`, quote them:

```bash
label:='"null"'   # → string "null"
label:='"true"'   # → string "true"
```

### Inline JSON requires exactly one arg

```bash
# WRONG — throws ClientError
mcpc @s tools-call tool '{"a":1}' extra:=2

# RIGHT — use key:=value pairs instead
mcpc @s tools-call tool a:=1 extra:=2
```

### := split is first-occurrence only

A value containing `:=` is safe:

```bash
expr:=a:=b   # key="expr", rawValue="a:=b" → string "a:=b"
```

### Empty args → empty object

`parseCommandArgs(undefined)` and `parseCommandArgs([])` both return `{}`.
Callers that check for required arguments must do so after this call.

---

## Shell quoting rules (bash / zsh)

| Goal | Shell syntax | What the process sees |
|---|---|---|
| String value with spaces | `name:="hello world"` or `'name:=hello world'` | `name:=hello world` |
| JSON object | `config:='{"k":"v"}'` | `config:={"k":"v"}` |
| JSON string (force string type) | `id:='"123"'` | `id:="123"` |
| Inline JSON | `'{"a":1}'` | `{"a":1}` |
| Value with double quotes inside | `msg:='"say \"hi\""'` | `msg:="say "hi""` — avoid; use key:=value with single quotes |

Single quotes prevent all shell interpolation — safest for JSON values.
Double quotes allow `$VAR` expansion: `query:="$SEARCH_TERM"`.

---

## validateOptions() and hasSubcommand()

`validateOptions(args)` scans from the start of `args`, stopping at the first
non-option token (the command word). Only `KNOWN_OPTIONS` are permitted before
that point; subcommand-specific flags are left to Commander. Options in
`OPTIONS_WITH_VALUES` consume the next token during scanning so their value
is never misidentified as an unknown option.

`hasSubcommand(args)` applies the same consume-next logic from index 2
(skipping `node` and the script path). Returns `true` on the first
non-option token. Used to decide between showing the session list (`mcpc` with
no subcommand) and routing to Commander (`mcpc tools-list`, etc.).
