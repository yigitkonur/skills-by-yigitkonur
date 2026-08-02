# Installation

## Install or upgrade

```bash
npm install -g @apify/mcpc
# or: bun install -g @apify/mcpc
# or (macOS/Linux, brings its own Node.js, since 0.6.0): brew install apify/tap/mcpc
mcpc --version
mcpc --help
```

Requires Node.js `>=22.12.0` (Node 20 support was dropped in `0.5.0`) unless installed via Homebrew.

This skill targets `0.6.x` and was verified against `0.6.0`.
If your help output still shows target-first syntax like `mcpc <server> connect @session`, you are reading `0.1.11` material.

Since `0.5.0` the npm install is ~70MB lighter and commands start ~5x faster (heavy deps like x402/OAuth/proxy are lazy-loaded) — don't expect old-version install weight or startup lag.

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

Credential and wallet storage prefer OS keychain integration when available, falling back to `~/.mcpc/credentials.json` (mode `0600`) on headless/CI systems where no keychain exists. Since `0.5.0` the "OS keychain unavailable" warning prints once, at the first fallback write, not on every command.
