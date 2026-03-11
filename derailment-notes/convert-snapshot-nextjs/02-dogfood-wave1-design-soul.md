# Derailment Test: convert-snapshot-nextjs — Wave 1 (Design Soul)

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs (sections-agent.md)
Test task: Extract per-section design tokens from Acme SaaS homepage
Method: Follow sections-agent.md steps literally

---

## Friction points

### Per-Section Token Extraction

**F-13 — Same `[^;]+` regex bug in sections-agent.md** (P0)
13 patterns in sections-agent.md have the same `[^;]+` issue as foundations-agent.md.
Fix: Global `[^;]+` → `[^;}]+` replacement.

**F-14 — `-e` flag missing on `--custom-prop` grep in sections-agent** (P1)
Same issue as F-11 but in different file.
Fix: Add `-e` flag to `--` prefixed patterns.

**F-15 — Section boundary detection ambiguous** (P1)
Instructions say "find where each section starts and ends" but don't explain how to determine
boundaries in minified CSS where class names are mangled.
Fix: Recommend using the snapshot HTML structure (`<section>`, `<header>`, landmark elements)
as the primary boundary source, CSS as secondary.

---

## What worked well

1. The per-section → global token mapping creates good design consistency
2. Responsive breakpoint extraction instructions were clear
3. The "design soul document" concept produces useful output

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 1 | F-13 |
| P1 | 2 | F-14, F-15 |
| P2 | 0 | — |
