# Derailment Test Summary: convert-snapshot-nextjs

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs
Test task: Convert Acme SaaS dark-theme homepage (7 sections, 3 CSS files, inline SVGs) to Next.js

---

## Aggregate Metrics

| Metric | Value |
|---|---|
| Total steps attempted | ~45 |
| Clean passes | ~17 |
| P0 (blocks progress) | 5 |
| P1 (causes confusion) | 14 |
| P2 (minor annoyance) | 9 |
| **Total friction points** | **28** |

## Derailment Density Map

| Wave | File | P0 | P1 | P2 | Total | Density |
|---|---|---|---|---|---|---|
| 0 — Extraction | foundations-agent.md | 3 | 6 | 3 | 12 | **HIGH** |
| 1 — Design Soul | sections-agent.md | 1 | 2 | 0 | 3 | MEDIUM |
| 2 — Build Brief | section-template.md | 1 | 2 | 1 | 4 | MEDIUM |
| 3 — Scaffold | system-template.md | 1 | 1 | 3 | 5 | MEDIUM |
| 4 — Build | SKILL.md | 0 | 3 | 1 | 4 | LOW |

**Hotspot:** Wave 0 (foundations-agent.md) — 43% of all friction points.

## Root Cause Analysis

| Root Cause | Count | Friction Points |
|---|---|---|
| `REGEX_WRONG` — pattern doesn't match minified CSS | 18 | F-01,02,04,13,16 + 57 sub-patterns |
| `MISSING_ESCAPE` — shell interprets `--` as flag | 6 | F-11,14,17 |
| `MISSING_GUARD` — false positive not filtered | 2 | F-10,18 |
| `MISSING_SECTION` — entire topic not covered | 4 | F-03,07,25,28 |
| `MISSING_DEFAULT` — no default value/path specified | 3 | F-12,22,26 |
| `VERSION_DRIFT` — dependency version broke template | 1 | F-20 |
| `NICE_TO_HAVE` — acceptable for MVP | 4 | F-05,08,09,19 |

## Systemic Issue: `[^;]+` Regex

The single highest-impact bug. In minified CSS:
```css
:root{--color-bg:#0a0a0a;--color-text:#fff}
```
`[^;]+` matches past `}` because the last property has no `;`. This affected
**57 grep patterns** across 3 reference files and caused silent data corruption
(extracted values contained parts of the next CSS rule).

Fix: `[^;}]+` — adding `}` to the negated character class.

## Fixes Applied

| File | Fix | Friction Points |
|---|---|---|
| foundations-agent.md | 22× `[^;}]+`, block :root extraction, transform filter | F-01,02,04,10 |
| sections-agent.md | 13× `[^;}]+`, `-e` flag | F-13,14 |
| section-template.md | 22× `[^;}]+`, 5× `-e` flag, transform filter | F-16,17,18 |
| system-template.md | Tailwind `^3` pin | F-20 |
| SKILL.md | Setup section, font/JS recovery, acceptance criteria | F-03,07,12,25,26,27,28 |

## Verification Results

```
[^;]+ remaining (stale): 0 across all files ✓
[^;}]+ present (fixed): 57 total ✓
SKILL.md line count: 107 (under 500 limit) ✓
Tailwind version: ^3 ✓
No orphaned reference files ✓
```

## What Worked Well

1. **Wave architecture is sound** — the 5-wave progression is intuitive and produces real results
2. **Component isolation** — one file per section is maintainable
3. **Design soul concept** — extracting tokens before building creates consistency
4. **Reference routing** — each wave has its own reference file, easy to follow
5. **The skill produces working output** — once regex bugs were fixed, `tsc` and `next build` passed
