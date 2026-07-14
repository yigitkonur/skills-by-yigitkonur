# Config Resolution

Use `file:entry` for stdio targets in `mcpc 0.2.x`.

## Expected file shape

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

## Connect form

```bash
mcpc connect ~/.vscode/mcp.json:filesystem @fs
```

## What changed from `0.1.11`

- `file:entry` is the released public surface
- do not teach `--config file entry connect @session` as the normal syntax

## URL normalization

- non-local bare hosts get `https://`
- localhost-style targets keep `http://`
- the path still matters, so `research.yigitkonur.com/mcp` is not the same as `research.yigitkonur.com`

## Common mistakes

- using `servers` instead of `mcpServers`
- omitting the `:entry` suffix
- assuming root host URLs are enough when the server is mounted under `/mcp`
