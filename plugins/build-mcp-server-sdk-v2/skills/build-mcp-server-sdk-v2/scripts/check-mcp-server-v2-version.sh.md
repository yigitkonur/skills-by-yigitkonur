# check-mcp-server-v2-version.sh

Run from an MCP project root that contains `package.json`:

```bash
bash scripts/check-mcp-server-v2-version.sh
```

When used from an installed skill, call the script by its skill path while the current working directory remains the target project root.

The script checks these packages across `dependencies`, `devDependencies`, `optionalDependencies`, and `peerDependencies`:

- `@modelcontextprotocol/server`
- `@modelcontextprotocol/node`
- `@modelcontextprotocol/express`
- `@modelcontextprotocol/hono`
- `@modelcontextprotocol/client`
- `@modelcontextprotocol/core`
- `@modelcontextprotocol/sdk`

It fails on unsafe v2 alpha ranges such as `^2.0.0-alpha.2`, `~2.0.0-alpha.2`, `latest`, `alpha`, wildcard/range alpha specs, or non-exact alpha tags. It warns when `@modelcontextprotocol/sdk` is present because npm currently publishes it as the v1 single-package SDK.

Exit codes:

- `0`: no unsafe v2 alpha ranges
- `1`: unsafe v2 alpha ranges found
- `2`: no `package.json` in the current directory
