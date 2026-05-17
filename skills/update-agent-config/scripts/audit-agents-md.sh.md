# audit-agents-md.sh

Read-only audit for AGENTS-first repository instruction surfaces.

## Usage

```bash
sh scripts/audit-agents-md.sh [repo-root]
```

Run it during the initial audit before editing existing instruction files. It defaults to the current directory.

## Reports

- root and nested `AGENTS.md`
- root and nested `CLAUDE.md`
- whether `CLAUDE.md` files are symlinks, wrappers, or independent files
- root and nested `REVIEW.md`
- common native surfaces: `.claude/`, `GEMINI.md`, `.cursor/`, `.cursorrules`, Copilot, and Greptile files
- line counts for discovered instruction files
- likely stale duplicate source-of-truth risks

Wrapper detection treats symlinks, direct `@AGENTS.md` wrappers, and very small files that point to `AGENTS.md` as companions. Larger files that mention `AGENTS.md` are still reported as independent so they can be inspected for drift.

## Safety

The script does not write files, delete files, change git state, or follow any workflow beyond filesystem inspection.
