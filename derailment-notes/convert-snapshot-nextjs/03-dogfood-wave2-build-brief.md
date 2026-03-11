# Derailment Test: convert-snapshot-nextjs — Wave 2 (Build Brief)

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs (section-template.md)
Test task: Generate build briefs for each Acme homepage section
Method: Follow section-template.md steps literally

---

## Friction points

### Template Application

**F-16 — Same `[^;]+` regex bug in section-template.md** (P0)
22 patterns affected. Same systemic issue.
Fix: Global `[^;]+` → `[^;}]+` replacement.

**F-17 — 5 grep patterns with `--` prefix missing `-e` flag** (P1)
Lines ~40-52 of section-template.md have unprotected `--` patterns.
Fix: Add `-e` flag.

**F-18 — Transform false positive in section-template.md** (P1)
Same `text-transform` contamination as F-10.
Fix: Add `grep -v 'uppercase\|capitalize\|lowercase'` filter.

**F-19 — No guidance on handling inline SVG icons** (P2)
Snapshot had inline SVGs in buttons and features. Template doesn't mention SVG extraction.
Fix: Acceptable for MVP; SVGs are typically extracted during Wave 0.

---

## What worked well

1. The template structure (layout → tokens → content → interactions) is well-ordered
2. Responsive variant documentation is thorough
3. The brief format is directly actionable by the build agent

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 1 | F-16 |
| P1 | 2 | F-17, F-18 |
| P2 | 1 | F-19 |
