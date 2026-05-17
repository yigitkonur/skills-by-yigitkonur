# check-folder-layout.sh

## Purpose

Check that a TypeScript `mcp-use/server` project exposes the canonical structural seams expected by `build-clean-mcp-architecture`.

## Usage

```bash
scripts/check-folder-layout.sh [project-root]
```

The project root defaults to `.`.

## What it checks

- Required top-level directories: `src/domain`, `src/application`, `src/handlers`, `src/gateways`, `src/presenters`, and `src/infrastructure`.
- The domain port seam: `src/domain/ports`.
- The runtime config seam: `src/infrastructure/config/runtime-config.ts`.
- A composition root candidate: `src/infrastructure/server/bootstrap.ts`, `src/bootstrap.ts`, `src/server.ts`, or `src/index.ts`.

## Exit codes

- `0` — all checked paths exist.
- `1` — missing paths were printed.
- `2` — usage or environment error.

## Limitations

The script checks presence only. It does not prove imports, bootstrap order, optional `resources/`, `prompts/`, or `shared/` usage, per-folder `AGENTS.md` quality, or whether a candidate composition root is actually the only root.
