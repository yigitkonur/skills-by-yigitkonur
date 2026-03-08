# MCP Server Config Patterns for mcp-use

## Overview

mcp-use uses a config dict to define MCP servers. The format matches the Claude Desktop / Cursor convention. Transport type is **auto-detected** based on which key is present in each server entry.

## Detection Logic

From `mcp_use/client/config.py`:

| Config Key | Connector Created | Transport |
|---|---|---|
| `"command"` present | `StdioConnector` | Stdio (subprocess) |
| `"url"` present | `HttpConnector` | HTTP — auto-negotiates Streamable HTTP → SSE fallback |
| `"ws_url"` present | `WebSocketConnector` | WebSocket |
| `"command"` + `sandbox=True` on client | `SandboxConnector` | E2B Sandbox |

## Config Structure

```python
config = {
    "mcpServers": {       # ← MUST be this exact key (not "servers", "mcp_servers", etc.)
        "server-name": {  # ← Arbitrary name, used with client.get_session("server-name")
            # ... transport-specific keys ...
        }
    }
}
```

## Stdio Transport (Command-Based)

For MCP servers that run as local subprocesses.

```python
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",                                              # Required: executable
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."], # Required: arguments
            "env": {                                                        # Optional: environment vars
                "HOME": "/home/user",
                "PATH": "/usr/bin"
            }
        }
    }
}
```

### Stdio Examples

```python
# Node.js MCP server via npx
"playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest"],
    "env": {"DISPLAY": ":1"}
}

# Python MCP server
"my-python-server": {
    "command": "python",
    "args": ["-m", "my_mcp_server"]
}

# uvx (Python tool runner)
"my-server": {
    "command": "uvx",
    "args": ["my-mcp-package"]
}

# Docker-based MCP server
"docker-server": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "my-mcp-image"]
}
```

## HTTP Transport (SSE / Streamable HTTP)

For remote MCP servers accessible over HTTP.

```python
{
    "mcpServers": {
        "remote-api": {
            "url": "http://localhost:3000/mcp",           # Required: server URL
            "headers": {                                    # Optional: HTTP headers
                "Authorization": "Bearer sk-xxx",
                "X-Custom-Header": "value"
            },
            "timeout": 5,                                  # Optional: HTTP timeout (seconds, default: 5)
            "sse_read_timeout": 300                         # Optional: SSE read timeout (seconds, default: 300)
        }
    }
}
```

### HTTP with OAuth Authentication

```python
"protected-server": {
    "url": "https://api.example.com/mcp",
    "auth": {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "scope": "read write"
    }
}
```

### HTTP with OAuth Provider

```python
"oauth-server": {
    "url": "https://api.example.com/mcp",
    "auth": {
        "oauth_provider": {
            "authorization_url": "https://auth.example.com/authorize",
            "token_url": "https://auth.example.com/token",
            "client_id": "your-client-id",
            "client_secret": "your-secret",
            "scope": "read write"
        }
    }
}
```

### HTTP Transport Auto-Negotiation

`HttpConnector` tries **Streamable HTTP** first. If the server doesn't support it, it falls back to **SSE**. Check which was used:

```python
session = client.get_session("remote-api")
connector = session.connector
print(connector.transport_type)  # "StreamableHTTP" or "SSE"
```

## WebSocket Transport

For WebSocket-based MCP servers.

```python
{
    "mcpServers": {
        "ws-server": {
            "ws_url": "ws://localhost:8080/mcp",    # Required: WebSocket URL
            "headers": {},                            # Optional: connection headers
            "auth": {}                                # Optional: auth config
        }
    }
}
```

## Multi-Server Configuration

```python
config = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        },
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
            "env": {"DISPLAY": ":1"}
        },
        "remote-api": {
            "url": "http://api.example.com/mcp",
            "headers": {"Authorization": "Bearer token"}
        },
        "ws-service": {
            "ws_url": "ws://localhost:8080/mcp"
        }
    }
}
```

All servers are accessible simultaneously. Tools from all servers are merged into a flat list.

## Loading Config

```python
from mcp_use import MCPClient, load_config_file

# From dict
client = MCPClient(config=config_dict)

# From JSON file (string path auto-detected)
client = MCPClient(config="./mcp-config.json")

# Factory methods
client = MCPClient.from_dict(config_dict)
client = MCPClient.from_config_file("./mcp-config.json")

# Load file manually
config = load_config_file("./mcp-config.json")
client = MCPClient(config=config)
```

## Restricting to Specific Servers

```python
# Only connect to specific servers from the config
client = MCPClient(config=config, allowed_servers=["filesystem", "playwright"])
```

## Common Config Mistakes

| Mistake | Error / Symptom | Fix |
|---|---|---|
| Using `"servers"` instead of `"mcpServers"` | No servers found / empty sessions | Use `"mcpServers"` (exact key) |
| Missing `"args"` in stdio config | Subprocess launch failure | Always include `"args"` (can be empty list) |
| Using `"endpoint"` instead of `"url"` | No HTTP connector created | Use `"url"` key |
| Using `"ws"` instead of `"ws_url"` | No WebSocket connector created | Use `"ws_url"` key |
| Using `"base_url"` instead of `"url"` | No HTTP connector created | Use `"url"` key |
| Mixing transport keys in one server | Undefined behavior | Use exactly one transport key per server |
