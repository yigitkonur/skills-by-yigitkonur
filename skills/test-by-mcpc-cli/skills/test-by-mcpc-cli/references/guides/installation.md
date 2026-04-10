# Installation

## Install or upgrade

```bash
npm install -g @apify/mcpc
mcpc --version
mcpc --help
```

This skill targets `0.2.x` and was verified against `0.2.4`.
If your help output still shows target-first syntax like `mcpc <server> connect @session`, you are reading `0.1.11` material.

## Config format that matters now

Use `mcpServers` in JSON config files and connect through `file:entry`.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

```bash
mcpc connect ~/.vscode/mcp.json:filesystem @fs
```

Do not teach `mcpc --config file entry connect @session` as the main surface.

## Local state directory

By default `mcpc` uses `~/.mcpc`.
Override it with `MCPC_HOME_DIR` for CI or isolated test runs.

## Storage note

Credential and wallet storage prefer OS keychain integration when available, with JSON fallback files when it is not.
