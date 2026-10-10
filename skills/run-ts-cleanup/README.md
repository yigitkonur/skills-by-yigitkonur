# run-ts-cleanup

Clean up a TypeScript codebase — dead code, unused dependencies, AI slop, weak types, and tangled structure — across single packages and monorepos, through a disciplined six-phase, wave-based remediation protocol.

**Category:** ops

## Overview

A deterministic engineering protocol and automated toolkit for dead-code pruning, structural simplification, and TypeScript health work:

- **Multi-engine, not single-tool:** Knip drives module-graph dead code, native autofix (`--fix`), and native cycles (`--cycles`); Biome / Oxlint / ESLint / Ultracite drive file-level lint and autofix; `tsc` gates types and declaration emit; `type-coverage` scores `any`-creep; `dpdm`/`madge` provide cycle visualization and runtime vs type separation.
- **Disciplined causal wave execution:** Remediation across 5 isolated, causal waves (Orphan Files → Barrels & Cycles → Private Exports → Types → Dependencies) with atomic commits and single-command rollback.
- **The 4 Pillars & 8 Sins of Agent-Written TypeScript:** Systematic diagnosis across Reachability, Encapsulation, Type Soundness, and Architectural Deepening, eliminating the 8 core agent bloat patterns (type laundering, schema drift, defensive null paranoia, barrel smog, test utility bleed, speculative ghost interfaces, catch laundering, any-ified external boundaries).
- **Matt Pocock Architectural Deepening:** Integrates deep modules, locality/colocation, the seam test, and the deletion test to eliminate shallow wrappers and micro-file sprawl without HTML dashboards.
- **Type safety and declaration-emit verification:** Compile-time guards against declaration emit crashes (`TS4023`, `TS4081`, `TS4060`, `TS2742`) and flag collisions (never `tsc -b --noEmit`, which triggers `TS5094`; use `tsc -b --emitDeclarationOnly` or `--isolatedDeclarations`).
- **Non-harmful lightweight refactoring:** Plan-first structural work for developer and agent navigability — inlining single-use micro-abstractions, untangling circular dependency webs, co-locating isolated helpers, dismantling bloated barrels.
- **Zero-dependency Python tooling:** Three Python 3 stdlib scripts for engine configuration, finding batching across all 9 batches, and whole-codebase health auditing.

## Bundled Tools

- `scripts/init-knip-config.py`: Scans project architecture, detects frameworks and monorepo layouts, and emits an optimal `knip.jsonc` with a valid `$schema` URL (`https://unpkg.com/knip@5/schema-jsonc.json` or v6) and built-in compiler configurations.
- `scripts/batch-findings.py`: Parses dead-code and analysis JSON findings, groups them into 9 dependency-ordered batches mapped onto the 5 waves, assigns risk ratings, and renders verification gates for the detected package manager.
- `scripts/audit-ts-health.py`: Audits `tsconfig.json` compiler flags, detects linter/formatter configurations, finds circular import cycles, and flags AI slop markers and schema drift.

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
