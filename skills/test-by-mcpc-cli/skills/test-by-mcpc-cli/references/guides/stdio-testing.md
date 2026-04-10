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
mcpc @everything-stdio resources-templates-list
mcpc @everything-stdio ping
```

If the acceptance criteria explicitly mention prompts, resources, or templates, run those commands in the first inspection pass instead of widening the read set later.

## Why `file:entry` matters

This is the released `0.2.x` surface.
Do not document `--config file entry connect @session` as the main path.

## Restart loop

```bash
mcpc restart @everything-stdio
mcpc @everything-stdio help
```

Use this after code changes or when the underlying stdio process crashed.
If `mcpc restart @everything-stdio` returns `Session not found`, create a fresh session name instead of retrying the missing one.
