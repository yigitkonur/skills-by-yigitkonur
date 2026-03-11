# Observation: F-03/F-04 Snapshot Output Mismatch

## What happened

**F-03:** SKILL.md step 3 shows `snapshot` as if it prints an accessibility tree to
stdout. In reality, it writes a YAML file to `.playwright-cli/page-<timestamp>.yml`
and prints only the file path. You must `cat` the file to see refs.

**F-04:** selectors.md shows an HTML-like tree with Unicode box-drawing characters
(with role markers). The actual output is a YAML list with role/name/ref keys. The
format is completely different from what's documented.

## Root cause

S3 — Incorrect output description. The documentation describes a format that doesn't
match the tool's actual behavior (likely changed in a tool update).

## Impact

P0 (F-03) — Cannot find refs without knowing to cat the YAML file.
P1 (F-04) — Wrong mental model of output structure.

## Fixes applied

1. SKILL.md step 3: Added YAML file comment + cat pattern to snapshot line
2. selectors.md "How refs work": Replaced HTML tree with YAML format example
3. selectors.md "Inline snapshot": Changed title to "YAML file", updated description
