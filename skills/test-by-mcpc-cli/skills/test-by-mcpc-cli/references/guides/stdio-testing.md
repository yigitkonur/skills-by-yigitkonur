# stdio Testing

Use stdio when you control the local server process and want reproducible testing from config.

## Config shape

`mcpc` expects `mcpServers` in the config file.

```json
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

## Connect and inspect

```bash
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
mcpc @everything-stdio
mcpc @everything-stdio tools-list --full
mcpc @everything-stdio prompts-list
mcpc @everything-stdio resources-list
mcpc @everything-stdio ping
```

## Why `file:entry` matters

This is the released `0.2.x` surface.
Do not document `--config file entry connect @session` as the main path.

## Restart loop

```bash
mcpc restart @everything-stdio
mcpc @everything-stdio help
```

Use this after code changes or when the underlying stdio process crashed.
