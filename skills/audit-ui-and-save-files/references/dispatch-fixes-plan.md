# Phase 5 — Approval-Gated Fix Dispatch Plan

The new headline capability. After Phase 4 (audit aggregation) the orchestrator does NOT silently spawn fix workers. Build a Markdown plan, ask the user, block on the reply, then dispatch.

This file is the full playbook. SKILL.md carries the summary; this file carries the operational details.

## The non-negotiable contract

```
Phase 4 ends → Phase 5 begins → cluster → table → ASK → block → on `go`: dispatch → reconcile
```

Banned at every step:

- Spawning a fix subagent before the user has typed an explicit affirmative reply.
- Treating an ambiguous reply (`looks good`, `seems fine`, `?`) as approval. Re-ask explicitly.
- Skipping the table because "the audit is small and the fix is obvious". The table is the audit-trail artifact. Always build it.
- Letting `N` (the subagent count) be driven by finding count. `N` is driven by **theme count**. Cap at 20.

## Step 1 — Read every finding from disk

```bash
# Pin the date so we audit one run, not multiple
AUDIT_DATE="<YY-MM-DD>"

# Inventory
find "css-issues/${AUDIT_DATE}" -name "*.md" -not -name "README.md" | sort
```

Read each finding's frontmatter-equivalent fields (Page, Section, Viewport, Also affects, Severity, Likely cause). Note the `Likely cause` source file path — this is the primary clustering axis.

Build a quick in-memory table per finding:

```
path | severity | viewport | also_affects | likely_cause_src
```

## Step 2 — Cluster findings into themes

A **theme** is a coherent unit of fix work. A finding belongs to the same theme as another finding if they share at least one of:

1. **The same `src/...` file or sibling files in the same module.** Two findings citing `src/components/BentoGrid.tsx:118` and `src/components/BentoGrid.tsx:144` are the same theme.
2. **The same design-token misuse.** Two findings citing `text-white/40 on dark surface` across different pages are the same theme.
3. **The same breakpoint.** Multiple `mobile-375` overflow bugs across contexts may cluster — but only if they also share files or token misuse. Breakpoint alone is too coarse.
4. **The same component family.** All `<DataTable>` bugs across pages and devices cluster, because the fix is in `src/components/DataTable/*` regardless of where the table renders.

### Clustering rubric

Walk the in-memory table:

1. Group by `likely_cause_src` first — this is the strongest signal.
2. Within each `likely_cause_src` group, check whether the bugs are truly the same theme or two different bugs in the same file. Two bugs in `src/components/Nav.tsx` at lines 12 and 287 are likely different themes; two bugs at lines 12 and 18 are likely one theme.
3. Lift cross-file design-token themes: scan all findings for the same token misuse, even when `likely_cause_src` differs.
4. Lift cross-file viewport themes: if six findings across six files all reproduce only at `mobile-375` and all describe horizontal overflow, that's one theme (the page-level x-scroll bug usually traces to a single offending element).

### Merge rule — 70% file overlap

If two candidate themes share more than ~70% of their `likely_cause_src` files, MERGE them. Worked example:

- Candidate theme A: 5 findings citing `src/components/Nav.tsx` (3) and `src/components/MobileMenu.tsx` (2).
- Candidate theme B: 4 findings citing `src/components/Nav.tsx` (3) and `src/components/Header.tsx` (1).
- Overlap on `Nav.tsx`: 3/5 in A, 3/4 in B. Combined unique files: {`Nav.tsx`, `MobileMenu.tsx`, `Header.tsx`}. Overlap = 3 / 3 unique files-with-overlap = >70% of each theme's footprint.
- → Merge into theme C: 9 findings citing 3 files.

A single fix subagent that owns all three files together will produce a more coherent change than two subagents racing in the same file.

### Cap at 20

`N` (number of fix subagents) MUST be ≤ 20. If clustering produces more than 20 themes, merge the smallest two until you're at 20. A 21st subagent is almost always a fragment of an existing theme.

### Floor at 1

If the audit produced zero findings, there is no Phase 5. Tell the user "no findings — nothing to fix" and stop.

If the audit produced findings but they cluster into a single theme, that's fine — `N=1` is valid. One subagent doing one theme is the minimum cost.

## Step 3 — Build the dispatch table

The table columns are fixed; do not invent new columns. Print this in chat in Markdown:

| # | Theme | Findings (count + paths) | Files likely touched | Outcome | Suggested skill(s) |
|---|---|---|---|---|---|

### Column-by-column spec

**`#`** — ordinal subagent number, 1..N, sorted by theme severity (highest-severity theme first). Severity per theme is the max severity of its findings.

**`Theme`** — short name (3–6 words). The name should be self-describing — a reviewer who reads only the table column should know what the subagent owns. Bad: "Theme A". Good: "mobile-375 overflow cluster", "BrandLogo fallback across pages", "Dashboard contrast on dark surfaces".

**`Findings (count + paths)`** — exact count and the full per-finding paths (relative to repo root, e.g. `css-issues/26-05-19/dashboard/mobile-375/03-overflow-on-table-headers.md`). For >5 findings, list the first 5 and append `…+N more`; the full list goes into the subagent prompt verbatim, not the table.

**`Files likely touched`** — best-guess `src/...` paths derived from the union of each finding's `Likely cause` field. Deduplicated. Cap at ~6 in the table; if more, list 5 and `…+N more`. The full list goes into the subagent prompt.

**`Outcome`** — one-line success criterion that the subagent must meet to declare done. Phrase as an observable state. Good: *"BrandLogo renders correctly on every page at desktop-1440 and mobile-375"*. *"Dashboard table has no horizontal overflow at mobile-375"*. Bad: *"fix the table"* (not observable).

**`Suggested skill(s) to invoke`** — what skill the fix subagent should reach for. This pack does NOT have a `frontend-design` skill; route to canonical alternatives. The routing matrix:

### Theme → skill routing matrix

| Theme shape | Suggested skill(s) | Reason |
|---|---|---|
| Tailwind / vanilla CSS edits in framework-agnostic components | plain `Edit` / `Write` (no skill) — the fix is mechanical | These don't need framework guidance |
| TinaCMS-backed App Router page bugs | `build-tinacms-nextjs` | Tina's MDX + schema patterns are non-obvious |
| Chrome-extension popup or content-script UI bugs | `build-chrome-extension` | MV3 lifecycle constraints differ from regular web apps |
| Native macOS app SwiftUI/AppKit bugs | plain `Edit` / `Write` | route to your own SwiftUI patterns; no dedicated skill in this pack |
| Cross-page design-system / token-level fixes (a brand color, a spacing scale, a type ramp) | plain `Edit` on the token source | fix happens through normal code edits |
| Bug requires browser verification mid-fix (regression check after each edit) | `run-agent-browser` (called by the fix subagent itself) | Same browser tool the audit used |
| Convert a saved HTML page into a Next.js implementation | `convert-url-to-nextjs` | Owned, scoped, opinionated |
| Post-fix self-review before marking done | `run-review` Mode A | Mandatory for non-trivial changes (>~50 LOC) |

For a single theme, the `Suggested skill(s)` cell can list 1–3 skills (e.g. `build-tinacms-nextjs` + `run-review` Mode A). Most themes are single-skill. A theme that demands more than 3 skills is probably two themes — split it.

### Table example (12-finding audit on a TinaCMS site)

```markdown
| # | Theme | Findings (count + paths) | Files likely touched | Outcome | Suggested skill(s) |
|---|---|---|---|---|---|
| 1 | BrandLogo fallback across pages | 4 — homepage/desktop-1440/01-..., features/desktop-1440/02-..., pricing/desktop-1440/02-..., customers/desktop-1440/01-... | src/components/shared/BrandLogo.tsx | BrandLogo renders the real logo on every page at desktop-1440 and mobile-375 | Edit, run-review Mode A |
| 2 | Dashboard table mobile-375 overflow | 3 — dashboard/mobile-375/01-..., dashboard/mobile-375/03-..., dashboard/mobile-375/05-... | src/components/DataTable/DataTable.tsx, src/components/DataTable/Row.tsx | No horizontal overflow on /dashboard at mobile-375 | Edit, run-agent-browser, run-review Mode A |
| 3 | Pricing CTA clipped by cookie banner | 2 — pricing/desktop-1440/04-..., pricing/mobile-375/02-... | src/components/CookieBanner.tsx, src/app/pricing/page.tsx | Pricing CTA fully visible above CookieBanner at all viewports | Edit, run-review Mode A |
| 4 | Bento spacing tokens cross-page | 3 — homepage/desktop-1440/06-..., features/desktop-1440/03-..., features/desktop-1280/01-... | src/styles/tokens.css, src/components/Bento/*.tsx | Bento spacing matches design tokens on every page; no per-page overrides | Edit, run-review Mode A |
```

`N=4` for a 12-finding audit. `N` is driven by theme count, not finding count.

### Worked example — 60-finding audit, 8 themes

The 57-issue real run from the legacy `audit-ui` skill clustered cleanly into 8 themes after the rubric:

1. Homepage hero overlap (12 findings, 1 source file)
2. Bento grid wide-hero clamp (8 findings, 3 source files)
3. BrandLogo fallback (11 findings, 1 source file — the canonical cross-page systemic)
4. Mobile menu overflow (6 findings, 2 source files)
5. Particle canvas escaping containers (4 findings, 2 source files)
6. Cookie banner sticky overlap (5 findings, 1 source file)
7. Stub-page `<HeroPlaceholder>` showing debug text (7 findings, 1 source file)
8. Dark-surface contrast cluster (4 findings, design-token level — fixed by editing the token source directly)

8 subagents, each tightly scoped. `N=8`, well under 20.

### Worked example — 70% overlap collapsing 6 candidates to 3

A 25-finding audit produced 6 candidate themes after initial clustering:

- A: 5 findings, files = {`Nav.tsx`, `MobileMenu.tsx`}
- B: 4 findings, files = {`Nav.tsx`, `Header.tsx`}
- C: 3 findings, files = {`Header.tsx`, `Nav.tsx`}
- D: 6 findings, files = {`DataTable.tsx`}
- E: 4 findings, files = {`DataTable.tsx`, `TableRow.tsx`}
- F: 3 findings, files = {`tokens.css`}

A↔B↔C all share `Nav.tsx` or `Header.tsx` with >70% file overlap. Merge into one theme of 12 findings covering `{Nav.tsx, MobileMenu.tsx, Header.tsx}`. D↔E share `DataTable.tsx` >70%; merge into one theme of 10 findings covering `{DataTable.tsx, TableRow.tsx}`. F stands alone.

Final: `N=3` subagents (navigation, table, tokens) instead of 6. The 3-subagent dispatch is more coherent and less likely to produce merge conflicts in `src/` because the fix subagents never touch the same files.

## Step 4 — Print the table and ASK

After printing the table, print this exact prompt to the user (or a close equivalent):

> **Approve the plan above?**
>
> Reply `go` to dispatch all subagents.
> Reply `go 1,3,5` to dispatch only specific subagents (comma-separated `#`s from the table).
> Reply `change` to revise the plan (then tell me what to adjust).
> Reply `cancel` to stop here — the audit artifact remains on disk for later.

## Step 5 — Block on the reply

Do NOT spawn any fix subagent before the reply arrives. If the user replies:

- **`go`** → dispatch all N subagents (see Step 6).
- **`go 1,3,5`** → dispatch only the listed subagents; leave the rest unassigned in the `## Fix tracking` block of their findings.
- **`change`** → ask: "What should change? E.g., split theme #2, merge themes #4 and #5, drop theme #6, change the outcome of theme #1, retarget the suggested skill for theme #3." Apply the change, re-print the table, re-ask.
- **`cancel`** → stop. Print "Audit artifact at `css-issues/<YY-MM-DD>/` is durable; re-invoke this skill's Phase 5 later or fix manually."
- **Ambiguous reply** (`looks good`, `?`, `maybe`) → re-ask the explicit prompt. Do not infer approval.

If the user starts with `go` and then in the same message adds new instructions ("go but also fix the footer issue"), treat the whole reply as `change` — not partial approval. Re-ask explicitly.

## Step 6 — Dispatch the approved fix subagents

For each approved subagent, dispatch via the `Agent` tool with `subagent_type: "general-purpose"`. Use this fix-subagent prompt template:

```text
# Context Block

You are fix subagent #<N> in a Phase 5 fix-dispatch pass following an audit of <project>. The audit produced findings under `css-issues/<audit-date>/`, clustered into themes; your theme is **<theme-name>**.

**Your assigned finding files** (read all of them in full before editing src/):
<finding-paths>

**Files likely touched** (best-guess from the audit's `Likely cause` fields — verify before editing):
<src-files>

**Your outcome criterion** (declare done only when this is observably true):
<outcome>

**Suggested skill(s) to invoke**: <suggested-skills>. If a `build-*` skill is suggested, invoke it via the Skill tool before editing — it carries framework patterns you need. If `run-review Mode A` is suggested, run it as your final step before reporting done.

# Mission Objective

Make the outcome true. Edit `src/...` files as needed. For each finding file you own, after the fix lands:

1. Flip the `## Fix tracking` checkbox to checked.
2. Replace `<TBD>` with `<N>` (your subagent number).
3. Append a one-line note to the `Notes:` field: `src changes in <file>:<lines>` (your actual change).
4. If you decide a finding is NOT actually a bug after closer inspection, write `wontfix — <reason>` in the `Notes:` field and leave the checkbox unchecked. Surface this in your handback.

# Hard constraints

- Touch only files under: <src-files-allowlist> AND the assigned finding files for `## Fix tracking` updates.
- Do NOT modify any finding file outside your assigned list.
- Do NOT modify `css-issues/README.md`.
- Do NOT modify findings under a DIFFERENT date directory.
- Do NOT spawn nested subagents. You are the leaf.
- Verify fixes by re-checking the screenshots referenced in your findings, or (if `run-agent-browser` is in your suggested-skills) by re-driving the browser at the same viewport(s) the original finding listed.
- Match the existing code style. Do NOT reformat adjacent code, refactor unrelated functions, or "improve" surrounding files.

# Definition of Done

- Outcome criterion is observably true.
- Every assigned finding file has `## Fix tracking` updated (checked + subagent #, or `wontfix` with reason).
- `git status --short` shows only your src/ changes and your finding-file updates.
- If `run-review Mode A` is in your suggested-skills, the self-review has run and any flagged issues have been addressed.

# Handback Format

1. **Summary** — what changed in src/ and which findings are now resolved (paths).
2. **Changes** — full list of src/ files modified with line ranges; full list of finding files updated.
3. **Verification** — how you verified the outcome (re-screenshot, browser re-check, manual visual inspection).
4. **Wontfix list** — any findings you marked wontfix, with reasons.
5. **Observations** — anything notable (a bug you found while fixing that wasn't in the audit; a finding whose `Likely cause` was wrong; a fix that revealed a deeper issue).
```

## Step 7 — Reconcile after fixes land

When all approved fix subagents have returned:

1. **Inventory the result:**
   ```bash
   grep -rn "Fixed by subagent #" "css-issues/<audit-date>" | wc -l
   grep -rn "wontfix" "css-issues/<audit-date>" | wc -l
   grep -rnL "Fixed by subagent #\|wontfix" "css-issues/<audit-date>" | wc -l   # still-unassigned findings
   ```

2. **Surface failures.** Any fix subagent that returned without meeting its outcome criterion is surfaced explicitly to the user with the failure reason. Do NOT silently re-dispatch — re-dispatch only on explicit user instruction.

3. **Commit (only if asked).** The fix subagents committed their src/ changes; the audit-finding updates can be committed in a single conventional commit (`refactor(audit): mark fixed findings from <audit-date> dispatch`). Only do this if the user asks.

4. **Done.** The audit skill's job ends here. A follow-up audit (re-running this skill with a new date) verifies the fixes landed visually.

## Anti-patterns specific to Phase 5

- **Spawning before approval.** The whole point of this phase. Banned.
- **Treating "fine" / "ok" as approval.** Re-ask.
- **Letting `N` track finding count.** A 60-finding audit must NOT be 60 subagents. Cluster first.
- **Theme overlap > 70% silently producing two subagents.** They'll race on shared files. Merge.
- **Mixing audit dates.** A fix subagent that touches `css-issues/26-05-19/` AND `css-issues/26-05-17/` is misdispatched — that's two separate audits. Keep them separate.
- **`Suggested skill(s)` = made-up names.** `frontend-design` is not in this pack. Use the routing matrix. If the right skill genuinely doesn't exist, list plain `Edit` and note in the handback that a skill gap exists.
- **Skipping the table because "the audit was tiny".** Always print the table. The 1-row table for a 1-theme audit is fine and serves as the audit-trail.
