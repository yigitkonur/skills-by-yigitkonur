# check-zod-boundary.sh

## Purpose

Find likely Zod placement and boundary-validation violations in a TypeScript `mcp-use/server` project.

## Usage

```bash
scripts/check-zod-boundary.sh [project-root]
```

The project root defaults to `.`.

## What it checks

- Zod imports in `src/domain/**`.
- Zod imports in `src/application/**`.
- `z.any()` and `z.unknown()` in `src/handlers/**`.
- Handler files containing `z.object(` without any `.strict()` in the same file.

## Exit codes

- `0` — no findings.
- `1` — one or more findings were printed.
- `2` — usage or environment error.

## Limitations

This is a textual heuristic. It can find likely violations but cannot prove every external boundary is schema-covered. Handler schemas wrapped centrally by a local factory may require human review to confirm where `.strict()` is applied.
