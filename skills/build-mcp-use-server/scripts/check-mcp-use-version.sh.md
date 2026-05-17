# `check-mcp-use-version.sh`

Read-only preflight for `mcp-use` server packages. Use it before setup, migration, version-claim edits, or debugging dependency drift.

## Run

```bash
bash scripts/check-mcp-use-version.sh .
bash scripts/check-mcp-use-version.sh packages/my-server
```

The script walks upward from the target directory until it finds `package.json`.

## Reports

- Node version.
- Declared and installed versions for `mcp-use`, `@mcp-use/cli`, `@mcp-use/react`, `zod`, and `typescript`.
- Warning when `zod` is not in `dependencies`.
- Warning that version-sensitive docs should be re-verified against installed declarations, binary help, and package metadata.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Package was readable; warnings may still be present. |
| `2` | Hard prerequisite failure: missing Node, missing target directory, missing/invalid `package.json`, or Node below 18. |

Missing `mcp-use` or `zod` is a warning, not a hard failure, because an implementation-capable run can add dependencies.

## Version drift

Read `references/00-version-drift.md` before changing hard-coded version claims. Run these when external package state matters:

```bash
npm view mcp-use version
npm view @mcp-use/cli version
npm view @mcp-use/react version
```
