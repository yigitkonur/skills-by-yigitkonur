# Pre-Scan: develop-typescript

## Skill metadata

- **Skill name**: develop-typescript
- **SKILL.md**: 151 lines, 5 workflow steps, 10 reference routing categories
- **References**: 10 files
  - `anti-patterns.md` — 888 lines
  - `type-system.md` — 652 lines
  - `patterns.md` — 674 lines
  - `strict-config.md` — 529 lines
  - `modern-features.md` — 465 lines
  - `testing.md` — 428 lines
  - `tooling.md` — 413 lines
  - `error-handling.md` — 414 lines
  - `performance.md` — 397 lines
  - `migration.md` — 348 lines

## External dependencies

- `tsc` (required)
- ESLint / Biome (optional)
- tsup / tsx (optional)

## Trigger boundary

TS writing, reviewing, refactoring, config, migration

## Branching

Classification in Step 1 routes to different reference subsets via 10 categories.

## Cross-references

Heavy overlap between reference files:
- `satisfies` appears in 3 files (type-system, modern-features, anti-patterns)
- `Result` type pattern in 2 files (error-handling, patterns)
- Strict config flags referenced in both strict-config and anti-patterns
