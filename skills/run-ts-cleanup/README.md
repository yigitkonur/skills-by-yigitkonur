# run-ts-cleanup

Clean up a TypeScript codebase — dead code, unused dependencies, AI slop, weak types, and tangled structure — across single packages and monorepos, through a disciplined six-phase, wave-based remediation protocol.

**Category:** ops

## Overview

A deterministic engineering protocol and automated toolkit for dead-code pruning, structural simplification, and TypeScript health work:

- **Multi-engine, not single-tool:** Knip drives module-graph dead code; Biome / Oxlint / ESLint / Ultracite drive file-level lint and autofix; `tsc` gates types and declaration emit; `type-coverage` scores `any`-creep; `madge` finds dependency cycles.
- **Disciplined wave execution:** Remediation across 5 isolated, sequential waves (Dependencies → Orphan Files → Barrels → In-File Exports → Types) with atomic commits and single-command rollback.
- **AI slop elimination:** Diagnosis and removal of the slop archetypes — useless try/catch rethrow wrappers, phantom null checks on non-nullable types, duplicate helper sprawl (`cn`, `formatDate`), and boolean theater.
- **Type safety and declaration-emit verification:** Compile-time guards against declaration emit crashes (`TS4023`, `TS4081`, `TS4060`, `TS2742`) before un-exporting anything.
- **Non-harmful lightweight refactoring:** Plan-first structural work for developer and agent navigability — inlining single-use micro-abstractions, untangling circular dependency webs, co-locating isolated helpers, dismantling bloated barrels.
- **Zero-dependency Python tooling:** Three Python 3 stdlib scripts for engine configuration, finding batching, and whole-codebase health auditing.

## Bundled Tools

- `scripts/init-knip-config.py`: Scans project architecture, detects frameworks and monorepo layouts, and emits an optimal `knip.jsonc` with a `$schema` matching the installed Knip major version.
- `scripts/batch-findings.py`: Parses dead-code JSON findings, groups them into 6 dependency-ordered batches mapped onto the 5 waves, assigns risk ratings, and renders verification gates for the detected package manager.
- `scripts/audit-ts-health.py`: Audits `tsconfig.json` compiler flags, detects linter/formatter configurations, finds circular import cycles, and flags AI slop markers.

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-ts-cleanup@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-ts-cleanup -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/run-ts-cleanup/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-ts-cleanup -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```
