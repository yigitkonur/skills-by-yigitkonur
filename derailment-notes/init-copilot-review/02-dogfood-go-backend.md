# Derailment Test: init-copilot-review on "pocketbase Go backend"

Date: 2025-07-18
Skill under test: init-copilot-review (post-fix version, 198 lines)
Test task: Create Copilot review instruction files for pocketbase/pocketbase
Method: Follow SKILL.md steps 1-6 exactly as written

---

## Target repository profile

| Attribute | Value |
|---|---|
| Repo | pocketbase/pocketbase |
| Structure | Single Go package (not a monorepo) with embedded Svelte SPA in ui/ |
| Primary language | Go (442 .go files, 180 test files) |
| Secondary language | Svelte (172 .svelte files in ui/src/) + JS (108) |
| Framework | Custom router (tools/router), no external HTTP framework |
| Linter | golangci-lint v2 with 17 linters + gofmt + goimports |
| CI | Only release.yaml (goreleaser) -- no CI test workflow |
| Test pattern | tests.ApiScenario table-driven tests |
| Auth/Security | JWT via tools/security, OAuth2 via tools/auth (30+ providers) |
| Existing copilot files | YES -- copilot-instructions.md + 3 scoped files already existed |
| Existing guidance | CONTRIBUTING.md, SECURITY.md |
| Key conventions | dangerous* prefix for raw SQL params, e.Next() middleware chain, routine.FireAndForget() for goroutines |

---

## Friction points

### F-01: No guidance for when copilot instruction files already exist (P1, O3)

**Step:** 1 (Ground on the repository)
**What happened:** The SKILL.md header says "Create or refine" but the 6-step workflow was written for greenfield creation. When I discovered pocketbase already has copilot instruction files, there was no guidance on whether to evaluate and improve, discard and recreate, or identify gaps.
**Impact:** Had to make an assumption. A less experienced agent would stall.
**Proposed fix:** Add decision branch in Step 1.

### F-02: Svelte/frontend scope not addressed by architecture guidance (P2, O3)

**Step:** 2 (Choose instruction architecture)
**What happened:** Pocketbase has a full Svelte SPA in ui/src/ (172 files). The placement table covers language, framework-or-path, and monorepo packages, but felt awkward for a repo with two fundamentally different stacks.
**Impact:** Low -- the steering rule resolved this correctly. Did not create a Svelte file because the ui/ directory is bundled output. But the decision required domain judgment.
**Proposed fix:** None needed -- steering rule was sufficient.

### F-03: applyTo glob syntax brace expansion not validated against Copilot platform (P2, M5)

**Step:** 5 (Validate)
**What happened:** Used applyTo: "tools/{auth,security}/**". The SKILL.md mentions brace expansion is valid. Used find to verify the glob matches real files. However, the SKILL.md doesn't specify whether GitHub Copilot's glob engine actually supports brace expansion.
**Impact:** Potential silent failure if Copilot doesn't support {auth,security}.
**Proposed fix:** Add note about Copilot glob support.

### F-04: No guidance on how deeply to verify rule deduplication across files (P2, M4)

**Step:** 5 (Validate)
**What happened:** The validation checklist says no contradictory rules. I caught that e.Next() appeared in both root and api-handlers files. But the rules are actually additive (root = hooks, scoped = middleware chain). The SKILL.md didn't help distinguish concept overlap from rule duplication.
**Impact:** Spent extra time analyzing. Ultimately concluded it was fine.
**Proposed fix:** Clarify that two files may mention the same concept if rules are additive.

---

## What worked well

1. **Shell inspection recipe (fix from F-01):** Knew exactly what to look for and how.
2. **"Representative files" guidance (fix from F-02):** "2-3 files: typical, complex, boundary" worked perfectly for Go.
3. **3-question stopping criterion (fix from F-03):** All three answered confidently after first round.
4. **"Recurring review themes" look-for guidance (fix from F-04):** Found dangerous* prefix, e.Next() chains, ApiError types.
5. **SMSA acronym expansion (fix from F-08):** Clear and used as a filter for each rule.
6. **Frontmatter example (fix from F-10):** No guessing about format.
7. **Glob brace expansion mention (fix from F-11):** Knew {auth,security} was valid syntax.
8. **Linter cross-reference (fix from F-13):** Checked golangci.yml to avoid duplicating linter rules.
9. **wc -c and wc -m guidance (fix from F-15):** Used both. No confusion.
10. **"1-3 sentence" per-file explanation (fix from F-16):** Clear target length.
11. **find command for glob verification (fix from F-14):** Verified all applyTo patterns.
12. **Monorepo utility package threshold (fix from F-06):** Not applicable but criteria made skip decision clear.

---

## Previously-fixed friction points -- validation

| Original | Title | Fixed? | Notes |
|---|---|---|---|
| F-01 | No inspection commands | Yes | Shell recipe worked perfectly for Go repo |
| F-02 | "Representative files" undefined | Yes | Clear targets: typical, complex, boundary |
| F-03 | No stopping criterion | Yes | 3-question test answered confidently |
| F-04 | "Recurring review themes" no method | Yes | Found dangerous*, e.Next(), routine.FireAndForget() |
| F-05 | "High-signal" undefined | Yes | Helped prioritize rules |
| F-06 | Monorepo package threshold | Yes | N/A but criteria made decision clear |
| F-07 | No route group guidance | N/A | Next.js-specific |
| F-08 | SMSA not defined | Yes | Expanded inline, used as quality filter |
| F-09 | Reference triggers unclear | Yes | Clear triggers, did not need them |
| F-10 | No frontmatter example | Yes | Eliminated guessing |
| F-11 | Glob brace expansion | Yes | Known valid, minor platform gap |
| F-12 | Split directories | Yes | Broader wildcard guidance helped |
| F-13 | No linter cross-ref | Yes | Checked golangci.yml |
| F-14 | No glob verification | Yes | find command worked |
| F-15 | wc -c bytes vs chars | Yes | Used both |
| F-16 | "Brief" subjective | Yes | "1-3 sentence" clear |

**Summary:** 14 of 14 applicable fixes validated.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | -- |
| P1 | 1 | F-01 |
| P2 | 3 | F-02, F-03, F-04 |

## Metrics

| Metric | Value |
|---|---|
| Total friction points | 4 |
| P0 | 0 |
| P1 | 1 |
| P2 | 3 |
| Steps with friction | 3 of 6 (Steps 1, 2, 5) |
| Friction density | 0.67 per step |
| Steps with zero friction | 3 (Steps 3, 4, 6) |
| Files generated | 4 (1 root + 3 scoped) |
| References consulted | 0 (SKILL.md self-sufficient) |

## Derailment density map

| Step | Phase | P0 | P1 | P2 | Total |
|---|---|---|---|---|---|
| 1 | Ground on repository | 0 | 1 | 0 | 1 |
| 2 | Choose architecture | 0 | 0 | 1 | 1 |
| 3 | Select rules | 0 | 0 | 0 | 0 |
| 4 | Draft files | 0 | 0 | 0 | 0 |
| 5 | Validate | 0 | 0 | 2 | 2 |
| 6 | Present result | 0 | 0 | 0 | 0 |

## Cross-run comparison

| Metric | Run 1 (dub) | Run 2 (pocketbase) | Delta |
|---|---|---|---|
| Total friction | 16 | 4 | -12 (75% reduction) |
| P0 count | 0 | 0 | 0 |
| P1 count | 8 | 1 | -7 (87.5% reduction) |
| P2 count | 8 | 3 | -5 (62.5% reduction) |
| Friction density | 2.67 | 0.67 | -2.00 |
| Files generated | 4 | 4 | 0 |
| Steps with zero friction | 0 | 3 | +3 |
| References needed | 2 | 0 | -2 |
