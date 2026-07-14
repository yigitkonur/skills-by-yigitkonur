# measure-context-budget.sh

Read-only heuristic token-budget scan for MCP server surfaces. It estimates the context cost of tool definitions by looking for tool registrations, descriptions, schema blocks, and static response examples.

## Usage

```bash
bash scripts/measure-context-budget.sh
bash scripts/measure-context-budget.sh /path/server
bash scripts/measure-context-budget.sh /path/server --description-chars 280 --tool-threshold 15
bash scripts/measure-context-budget.sh --help
```

## Options

| Flag | Default | Effect |
|---|---:|---|
| `--description-chars N` | 400 | Flag description lines over `N` characters. |
| `--schema-chars N` | 2000 | Flag schema-ish lines over `N` characters. |
| `--response-chars N` | 4000 | Flag response/example-ish lines over `N` characters. |
| `--tool-threshold N` | 20 | Flag active tool candidate count over `N`. |

## What it reports

- Tool registration candidate count.
- Description, schema, and static response/example signal counts.
- Rough token estimates with `chars / 4`.
- Threshold flags for too many tools, long descriptions, large schemas, and large response examples.
- First likely tool definition matches.
- Assumptions that explain where the heuristic can be wrong.

## Design constraints

- Read-only by design. It never writes files.
- Dependency-light: uses `rg` when available, otherwise falls back to `grep`.
- Regex-based, not AST-based. Confirm findings in source before changing code.
- Deterministic Markdown output for easy paste into audits.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Scan completed or help printed. |
| 2 | Target path or option parsing error. |

## When to run

- During context/cost audits.
- Before and after trimming tool descriptions or splitting large tool surfaces.
- Before enabling prompt caching where tool-list stability matters.
