# check-v2-feasibility.sh

Read-only static audit for a TypeScript MCP server before an SDK v1 to v2 migration.

## Use when

- Choosing between full rewrite, verified meta-package shim, HTTP-layer auth transition, or staying on v1.
- Preparing the Step 1 inventory before touching source files.
- Looking for deterministic first-pass blockers: CommonJS, Node <20, OAuth router usage, SSE, raw schemas, handler context, and error rewrites.

## Avoid when

- The project is already confirmed as greenfield v2 work; use `build-mcp-server-sdk-v2` instead.
- You need a complete semantic migration plan. This script only finds static signals; read the references for the actual rewrite decisions.

## Usage

```bash
bash scripts/check-v2-feasibility.sh /path/to/project
```

The script does not modify files. It reports:

- detected server profile
- recommended strategy
- blockers
- files/imports requiring attention
- validation commands to run next

It prefers `rg` when available and falls back to `grep`.
