# scaffold-v1-server.sh

## Purpose

Create a minimal TypeScript MCP server project using `@modelcontextprotocol/sdk` v1 import paths and the current `McpServer` registration API.

## Usage

```bash
bash scripts/scaffold-v1-server.sh <target-dir> <server-name> [stdio|http-stateful|http-stateless]
```

The transport defaults to `stdio`. The target directory must not exist or must be empty.

## Output

The script creates:

- `package.json` with `@modelcontextprotocol/sdk`, `zod`, TypeScript scripts, and Express dependencies for HTTP modes
- `tsconfig.json` with Node16 module resolution
- `src/index.ts` containing one `echo` tool and the selected transport wiring

It exits with `FAIL ...` instead of overwriting existing files.

## Skill routing

Use this in `SKILL.md` Step 2B/3 for greenfield SDK v1 projects after choosing `stdio`, stateful Streamable HTTP, or stateless Streamable HTTP.
