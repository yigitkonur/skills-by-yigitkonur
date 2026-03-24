# Config file resolution

## Overview

mcpc supports two ways to identify a server target: a direct URL/hostname, and a reference into a config file. Config files use the standard MCP JSON format (same as Claude Desktop, VS Code, and Cursor), which makes it straightforward to share a single config across tools. This document covers how config files are parsed, how environment variables are substituted, and how mcpc resolves a target string into a usable server configuration.

---

## Config file format

Config files must contain a top-level `mcpServers` object. Each key is a logical server name; each value is a `ServerConfig` entry. The format is identical to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {
        "DEBUG": "mcp:*"
      }
    },
    "apify": {
      "url": "https://mcp.apify.com",
      "headers": {
        "Authorization": "Bearer ${APIFY_TOKEN}"
      },
      "timeout": 300
    }
  }
}
```

The file must be valid JSON. Comments are not supported. The `mcpServers` field is required; omitting it or setting it to a non-object causes a `ClientError`.

---

## ServerConfig fields

Each entry in `mcpServers` is a `ServerConfig` object. All fields are optional except the mutual requirement that exactly one of `url` or `command` is present.

| Field | Type | Applies to | Description |
|---|---|---|---|
| `url` | string | HTTP servers | Full URL of the MCP endpoint. Scheme is required after substitution. |
| `command` | string | stdio servers | Executable to launch (e.g., `npx`, `python`, `/usr/local/bin/my-server`). |
| `args` | string[] | stdio servers | Arguments passed to `command`. Each element is substituted independently. |
| `env` | object | stdio servers | Additional environment variables injected into the child process. Values are substituted. |
| `headers` | object | HTTP servers | HTTP headers sent on every request to the server. Values are substituted. |
| `timeout` | number | both | Request timeout in milliseconds. Not substituted (must be a literal number). |

---

## Validation: exactly one of `url` or `command`

`validateServerConfig()` enforces a strict mutual exclusion:

- **Neither `url` nor `command`** → `ClientError: must specify either "url" or "command"`
- **Both `url` and `command`** → `ClientError: cannot specify both "url" and "command"`
- `url` must be a non-empty string starting with `http://` or `https://` (checked after substitution).
- `command` must be a non-empty string.

This check runs after environment variable substitution, so a URL formed entirely from env vars is validated against the final substituted string.

---

## How `loadConfig()` works

`loadConfig(configPath: string): McpConfig` in `src/lib/config.ts`:

1. Resolves the path to an absolute path using `path.resolve()`. Relative paths are resolved from the current working directory.
2. Reads the file synchronously with `readFileSync(absolutePath, 'utf-8')`.
3. Parses with `JSON.parse()`.
4. Validates that `config.mcpServers` exists and is an object. If not, throws a `ClientError` with the expected format shown in the error message.
5. Returns the raw `McpConfig` object. Environment variable substitution does not happen here — it happens when a specific server entry is extracted.

Error handling:

| Condition | Error thrown |
|---|---|
| File not found (`ENOENT`) | `ClientError: Config file not found: <absolutePath>` |
| Invalid JSON (`SyntaxError`) | `ClientError: Invalid JSON in config file: <absolutePath>\n<parseError>` |
| Missing `mcpServers` field | `ClientError: Invalid config file format: missing or invalid "mcpServers" field.` |
| Other I/O error | `ClientError: Failed to load config file: <absolutePath>\n<message>` |

---

## How `getServerConfig()` works

`getServerConfig(config: McpConfig, serverName: string): ServerConfig`:

1. Looks up `config.mcpServers[serverName]`. If absent, throws:
   ```
   ClientError: Server "filesystem" not found in config file.
   Available servers: apify, staging
   ```
2. Calls `substituteEnvVars(serverConfig)` to produce a fully-substituted copy.
3. If `url` is present, the substituted string is also passed through `normalizeServerUrl()`, which enforces the scheme and strips username, password, and hash for security.
4. Returns the substituted `ServerConfig`.

---

## Environment variable substitution

Substitution uses the pattern `${VAR_NAME}` and applies to every string field in a `ServerConfig`. The regex is `/\$\{([^}]+)}/g`.

Fields that undergo substitution:

- `url` — the full URL string
- `command` — the executable path/name
- `args` — each element of the array individually
- `env` — each value (keys are never substituted)
- `headers` — each value (keys are never substituted)

`timeout` is a number, not a string, and is copied as-is without substitution.

### Missing variable handling

If a referenced variable is not set in `process.env`, mcpc logs a warning and substitutes an empty string — it does **not** throw an error:

```
warn [config] Environment variable not found: APIFY_TOKEN, using empty string
```

This means a missing `${APIFY_TOKEN}` in a `headers.Authorization` value produces `"Bearer "` — a malformed but non-fatal header. The downstream server will reject the request, not mcpc itself. This is intentional: it avoids breaking config loading when env vars are set later in the process lifecycle.

If strict validation is needed, set the variable before running mcpc or check for the warning in `--verbose` output.

### Substitution scope

Substitution is scoped to the specific server entry being extracted. Loading the config file with `loadConfig()` does not perform substitution — only `getServerConfig()` does. This means you can load a config, list server names with `listServers()`, and only pay the substitution cost for the entry you actually use.

---

## Config file entry syntax

To reference a specific entry from a config file, use the colon syntax:

```
<file-path>:<entry-name>
```

Examples:

```bash
mcpc ~/.vscode/mcp.json:filesystem connect @fs
mcpc ~/Library/Application\ Support/Claude/claude_desktop_config.json:apify connect @apify
mcpc ./mcp.json:staging connect @staging
```

The full session commands using this syntax:

```bash
mcpc ~/.vscode/mcp.json:filesystem connect @fs
mcpc @fs tools-list
mcpc @fs close
```

---

## How `parseServerArg()` detects config vs URL

`parseServerArg()` must distinguish between:

- `mcp.apify.com` — a direct URL target (no config file involved)
- `~/.vscode/mcp.json:filesystem` — a config file path with an entry name

The detection logic:

1. Check if the argument contains a colon (`:`).
2. If it does, split on the first colon to get a potential `[filePath, entryName]` pair.
3. Check whether the portion before the colon is an existing file path (`fileExists(filePath)`). Tilde expansion is applied.
4. If the file exists → treat the argument as a config file reference.
5. If the file does not exist but a colon is present → treat the full string as a URL (the colon is part of the scheme, e.g., `https://mcp.apify.com`).
6. If no colon → treat as a bare hostname, which gets normalized to `https://<hostname>`.

This means a config path must refer to an actually-existing file at parse time. A path typo will cause the argument to be interpreted as a URL and fail with a connection error rather than a "file not found" error.

---

## Common config scenarios

### HTTP server with bearer token from environment

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com",
      "headers": {
        "Authorization": "Bearer ${APIFY_TOKEN}"
      }
    }
  }
}
```

```bash
export APIFY_TOKEN=apify_api_xxxx
mcpc ~/mcp.json:apify connect @apify
mcpc @apify tools-list
```

### stdio server (local package via npx)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${FS_ROOT}"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

```bash
export FS_ROOT=/Users/me/projects
mcpc ~/mcp.json:filesystem connect @fs
mcpc @fs resources-list
```

### HTTP server with custom timeout

```json
{
  "mcpServers": {
    "slow-server": {
      "url": "https://internal.example.com/mcp",
      "timeout": 600000
    }
  }
}
```

Timeout is in milliseconds. `600000` = 10 minutes.

### Multiple servers in one file

```json
{
  "mcpServers": {
    "dev": {
      "url": "http://localhost:3000/mcp"
    },
    "staging": {
      "url": "https://staging.example.com/mcp",
      "headers": {
        "X-Api-Key": "${STAGING_KEY}"
      }
    },
    "prod": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "X-Api-Key": "${PROD_KEY}"
      }
    }
  }
}
```

```bash
mcpc ~/mcp.json:dev connect @dev
mcpc ~/mcp.json:staging connect @staging
```

### Python stdio server

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server", "--port", "${SERVER_PORT}"]
    }
  }
}
```

---

## Sharing configs across tools

The config format is identical to what Claude Desktop and VS Code Copilot use, so the same file works everywhere:

| Tool | Config file location |
|---|---|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| VS Code Copilot | `~/.vscode/mcp.json` or workspace `.vscode/mcp.json` |
| Cursor | `~/.cursor/mcp.json` |
| mcpc | Any path — specified explicitly on the command line |

To use your Claude Desktop config directly with mcpc:

```bash
mcpc "~/Library/Application Support/Claude/claude_desktop_config.json":filesystem connect @fs
```

Note: quote the path if it contains spaces.

Environment variable substitution in mcpc uses `process.env` at runtime. Claude Desktop and VS Code resolve variables differently (VS Code has its own `${env:VAR}` syntax), so entries designed for those tools may need adjustment if they use tool-specific syntax. The standard `${VAR}` form used by mcpc is compatible with all three tools.

---

## Listing servers in a config

To see what server names are available in a config file before connecting, use `listServers()` programmatically, or simply attempt a connection with an unknown name — mcpc will print the available server names in the error message:

```
ClientError: Server "typo" not found in config file.
Available servers: filesystem, apify, staging
```

There is no dedicated `mcpc config list` command — the error output is intentionally informative enough to guide correction.
