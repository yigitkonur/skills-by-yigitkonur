# audit-mcp-server.sh

Read-only static audit helper for `optimize-agentic-mcp`. It prints deterministic Markdown about likely MCP entrypoints, framework signals, tool registrations, legacy transport signals, stdout logging, and basic schema/annotation/error-handling gaps.

## Usage

```bash
bash scripts/audit-mcp-server.sh              # scan current directory
bash scripts/audit-mcp-server.sh /path/server # scan a target directory
bash scripts/audit-mcp-server.sh --help
```

## What it reports

- Target path.
- Likely MCP entrypoints.
- Framework signals: `mcp-use`, `@modelcontextprotocol/sdk`, `@modelcontextprotocol/server`, Python FastMCP.
- Tool registration candidate count and first matches.
- Schema, annotation, and error-handling signal counts.
- Deprecated SSE transport signals.
- stdout logging patterns that can break stdio transports.
- Heuristic gaps that need source confirmation.

## Design constraints

- Read-only by design. It never writes files.
- Dependency-light: uses `rg` when available, otherwise falls back to `grep`.
- Regex-based, not AST-based. It is a triage helper, not a source of truth.
- Excludes common dependency/build directories and lockfiles for stable output.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Scan completed or help printed. |
| 2 | Target path is not a directory. |

## When to run

- At the start of an existing-server quick audit.
- Before choosing the companion build skill.
- After a large refactor to re-check obvious static regressions.
