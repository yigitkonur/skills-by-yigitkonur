# `mcp-use serve` Tombstone

`mcp-use serve` is not a shipped command in the CLI dependency installed by `mcp-use@1.26.0` (`@mcp-use/cli@3.1.2`).

## Status

The canonical "run the built server" command is `mcp-use start` (`05-mcp-use-start.md`). If a future CLI adds `serve`, verify it from the installed binary before documenting it:

```bash
mcp-use --help
mcp-use serve --help
```

## What to run

`mcp-use start` is the supported, documented production command. Use it everywhere unless `mcp-use serve --help` proves otherwise on your installed version.

## Recommended posture

| You want to | Run |
|---|---|
| Run the built server | `mcp-use start` |
| Document a workflow for others | Use `mcp-use start` (canonical) |

## See also

- `05-mcp-use-start.md` — the canonical run command
- `01-overview.md` — full command list with one-line descriptions
