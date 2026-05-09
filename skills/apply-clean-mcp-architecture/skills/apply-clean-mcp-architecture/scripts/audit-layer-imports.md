# audit-layer-imports.sh

## Purpose

Find grep-friendly violations of the `apply-clean-mcp-architecture` layer contract in a TypeScript `mcp-use/server` project.

## Usage

```bash
scripts/audit-layer-imports.sh [project-root]
```

The project root defaults to `.`.

## What it checks

- Forbidden protocol or outer-layer imports inside `src/domain/**` and `src/application/**`.
- `process.env` reads outside `src/infrastructure/config/runtime-config.ts`.
- `console.*` calls under `src/`.
- `index.ts` files under `src/`, except the package entrypoint `src/index.ts`.

## Exit codes

- `0` — no findings.
- `1` — one or more findings were printed.
- `2` — usage or environment error.

## Limitations

This is a fast textual audit, not a full dependency graph. It can miss aliased imports and can flag intentional entrypoint files that are not documented in the project. Use `dependency-cruiser` for the merge gate.
