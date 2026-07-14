# check-mcp-use-version.sh

Read-only package fact check for `mcp-use` agent projects.

## Usage

```bash
bash scripts/check-mcp-use-version.sh --target /path/to/project
```

## What it reports

- Current Node.js version
- Installed `mcp-use` version, if present
- Latest npm `mcp-use` version
- Latest npm `engines.node`
- Peer dependencies and optional peer metadata

The script does not inspect or print provider secrets.
