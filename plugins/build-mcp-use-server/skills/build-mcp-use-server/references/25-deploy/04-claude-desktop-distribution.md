# Claude Desktop Distribution

How to ship your deployed MCP server config to Claude Desktop users.

---

## 1. Config file location

Claude Desktop reads `claude_desktop_config.json`:

| OS      | Path                                                      |
|---------|-----------------------------------------------------------|
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`             |
| Linux   | `~/.config/Claude/claude_desktop_config.json`             |

Restart Claude Desktop after edits.

---

## 2. HTTP server config

Local, remote, or Manufact Cloud — all use the same shape:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://your-subdomain.run.mcp-use.com/mcp"
    }
  }
}
```

For local development:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

---

## 3. HTTP server with authentication

Static bearer tokens (API keys):

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token"
      }
    }
  }
}
```

For OAuth-protected servers, omit `headers` — Claude Desktop performs the OAuth flow against the server's `/.well-known/oauth-authorization-server` and stores the resulting token. Your server must expose RFC 7591 DCR (see `11-auth/02-dcr-vs-proxy-mode.md`).

For Cloud Run with IAM, the `Authorization: Bearer $ID_TOKEN` shape works but the token expires hourly — consider the OAuth route or a long-lived service-account token issued at install time.

---

## 4. Distribution patterns

### a) Manual paste

The most common path. Document your server URL and config snippet in the README:

```markdown
## Install in Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

\`\`\`json
{
  "mcpServers": {
    "my-server": {
      "url": "https://your-subdomain.run.mcp-use.com/mcp"
    }
  }
}
\`\`\`

Restart Claude Desktop.
```

### b) `mcp install` CLI helper

Some package authors ship a postinstall step that prints the snippet:

```bash
npx -y @yourorg/mcp-server-mytools install
```

Inside that command, print the config block and the OS path. Do **not** mutate `claude_desktop_config.json` automatically — users may have other entries. Print and let them paste.

### c) Stdio servers

For Node packages distributed on npm with a `bin`:

```json
{
  "mcpServers": {
    "mytools": {
      "command": "npx",
      "args": ["-y", "@yourorg/mcp-server-mytools"]
    }
  }
}
```

The package needs a shebang on its entry (`#!/usr/bin/env node`) and `"bin"` in `package.json`. mcp-use is HTTP-first; stdio distribution is uncommon for mcp-use servers.

---

## 5. After deploy

When you ship a Manufact Cloud server, the deploy output already gives you the URL. Update your README's install snippet to match:

```
✓ Deployment successful!

🌐 MCP Server URL:
   https://your-subdomain.run.mcp-use.com/mcp
```

If the subdomain ever changes (lost `.mcp-use/project.json`, see `platforms/01-mcp-use-cloud.md`), every user with the old URL gets a connection failure. Track `project.json` in git and pin a custom domain.

---

## 6. Env var resolution in `headers`

Claude Desktop expands `${ENV_VAR}` inside the config file:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_TOKEN}"
      }
    }
  }
}
```

The user must have `MCP_TOKEN` exported in their shell environment when Claude Desktop launches. macOS GUI launches do **not** inherit shell env — set via `launchctl setenv MCP_TOKEN ...` or use a wrapper script.
