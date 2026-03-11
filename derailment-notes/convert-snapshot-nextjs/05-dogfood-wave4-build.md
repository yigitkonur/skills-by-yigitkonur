# Derailment Test: convert-snapshot-nextjs — Wave 4 (Build & Verify)

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs
Test task: Build all sections and verify Acme homepage Next.js project
Method: Follow remaining SKILL.md steps literally

---

## Friction points

### Build Process

**F-25 — No acceptance criteria specified** (P1)
SKILL.md doesn't list what "done" means. Is it `tsc`? `next build`? Visual match?
Fix: Add CLI-verifiable acceptance criteria section to SKILL.md.

**F-26 — `UNVERIFIED` marker convention not documented** (P1)
When an extracted value is uncertain, there's no standard marker to flag it for review.
Fix: Add `/* UNVERIFIED */` comment convention to SKILL.md and acceptance criteria
that greps for remaining markers.

**F-27 — External URLs may leak into components** (P1)
Snapshot image `src` attributes point to original CDN. No instruction to localize all URLs.
Fix: Add grep check for `https?://` in components to acceptance criteria.

**F-28 — No guidance on handling external JS (analytics, widgets)** (P2)
Snapshot may contain `<script>` tags for analytics, chat widgets, etc.
Fix: Add to missing-resource recovery section: do NOT embed, add TODO comment.

---

## What worked well

1. The wave-based workflow (extract → design → brief → scaffold → build) is intuitive
2. Once Tailwind was pinned to v3, `next build` succeeded cleanly
3. Component isolation (one file per section) makes the output maintainable
4. The skill produces a genuinely useful Next.js project from a snapshot

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | — |
| P1 | 3 | F-25, F-26, F-27 |
| P2 | 1 | F-28 |
