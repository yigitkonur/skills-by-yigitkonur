---
name: audit-ui-and-save-files
description: Use skill if you are auditing a running web app's UI across pages and viewports, saving per-bug findings to a dated tree, and dispatching approval-gated fix subagents.
---

# Audit UI and Save Files

Disciplined visual QA of a running web app, with a durable on-disk artifact and an explicit fix-dispatch step.

Dispatch parallel audit subagents that each drive the `run-agent-browser` skill across an owned slice of pages, capture screenshots at canonical viewports, and write one markdown finding per real bug into a **dated, context-scoped, device-scoped tree** under `css-issues/`. When the audit returns, cluster findings into themes, present a Markdown dispatch table, **ask the user to approve**, and only then spawn fix subagents that route to the pack's `build-*` and `extract-saas-design` skills as appropriate.

The skill owns three things: where files live, how findings are written, and how the fix-pass is dispatched. It does NOT own design taste (the subagents bring that) and does NOT perform the fixes itself (it dispatches them).

## When to Use

Trigger on phrases and contexts like:

- *"audit the UI and save findings"*, *"find CSS issues across the app and write them up"*
- *"do a visual QA and prepare fix tasks"*, *"do a design QA pass and queue the fixes"*
- *"screenshot every page across viewports and inventory the bugs by date"*
- *"check responsive breakpoints on the whole site, then plan the fixes for me to approve"*
- *"the site is feature-complete — audit, save findings, and ask before fixing"*
- *"go through every page at desktop and mobile, write bug files, and propose fix subagents"*

Do NOT use this skill for:

- *Single-page UI debugging.* If the user knows the bug is on one page and just wants it fixed, drive `run-agent-browser` directly inline. This skill's overhead pays back when there are ≥5 routes or when the bug count is unknown.
- *Functional / behavior testing.* Clicks, form submits, end-to-end flows belong with `run-playwright` or similar; this skill is layout/visual-first.
- *Accessibility-only audits.* Use specialized a11y tooling; this skill is visual-first.
- *Performance audits.* Lighthouse / Web Vitals belong elsewhere.
- *Direct fix execution without an audit pass.* If the user has already inventoried the bugs and just wants them fixed, skip the audit phases and use the dispatch step in isolation — but only if the inventory already follows this skill's tree layout.

## Headline Capabilities (read this section)

Two structural commitments separate this skill from a generic visual-audit run. Both are non-negotiable.

### 1. Findings live in a dated, context-scoped, device-scoped tree

Every finding markdown file is written to:

```
css-issues/[YY-MM-DD]/[context]/[device]/NN-short-slug.md
```

Concrete example (an audit run on 2026-05-19, of the dashboard page, at the iPhone-13 viewport):

```
css-issues/26-05-19/dashboard/mobile-375/03-overflow-on-table-headers.md
```

Each segment is mandatory and has a precise meaning. See "Output Tree" below for the full grammar, the canonical viewport slugs, and how to choose `[context]` slugs. Plant the spec into `css-issues/README.md` at Phase 2 so every subagent enforces the same layout.

### 2. Fixes are dispatched only after the user approves a Markdown plan

After every audit subagent returns, Claude does NOT silently spawn fix workers. The skill MUST:

1. Read every finding from disk.
2. Cluster findings into **themes** (coherent units of fix work — shared source files, shared design-token misuse, shared breakpoint, or shared component family).
3. Choose `N` (1 ≤ N ≤ 20) — the number of fix subagents — driven by theme count, NOT by finding count.
4. Build a Markdown table with the columns specified in "Approval-Gated Fix Dispatch" below.
5. **Stop and ask the user to approve.** Banned: spawning any fix subagent before an explicit "go" reply.
6. On approval, spawn the fix subagents; each works against its theme's finding list and routes to the appropriate `build-*` / `extract-saas-design` / direct-edit path.

The full clustering rubric, table template, approval grammar, and post-dispatch reconciliation steps live in `references/dispatch-fixes-plan.md` — read it in full before clustering.

## The Workflow (Five Phases)

### Phase 1 — Verify preconditions

Before dispatching any subagents, confirm:

1. **A dev or prod server is reachable.** Run `curl -s -o /dev/null -w "%{http_code}" <url>` — must return 200. If the user wants to audit `localhost:3000` and nothing is running, boot the dev server in the background and wait for "Ready in" before continuing. Don't dispatch audit subagents against a server that isn't up.
2. **The `run-agent-browser` skill is available.** Check the available-skills list. If it isn't there, surface this and stop — there is no graceful fallback that produces real screenshots.
3. **The page list is known.** Ask the user for the full route list if it's not obvious from context. For larger sites, enumerate routes from source (Next.js App Router pages, sitemap.xml, etc.) rather than guessing.
4. **The audit date is fixed.** Compute `YY-MM-DD` once at the start of the run (e.g. `26-05-19`) and pin it for every subagent. Do not let later subagents recompute — same audit, same date, even if it crosses midnight.
5. **The audit's context labels are known.** Decide upfront which `[context]` slugs the audit covers (e.g. `dashboard`, `signup-flow`, `pricing-page`, `tables-component`). One subagent typically owns one context; large contexts can be split. See "Choosing context slugs" under "Output Tree" for the rubric.

### Phase 2 — Plant the format spec

Write `css-issues/README.md` in the project root before dispatching anything. Every audit subagent reads this file as their format authority — pulling the format spec out of every subagent prompt and into one shared file keeps prompts lean and the format consistent.

Copy the spec verbatim from `references/audit-format-spec.md`. Do NOT paraphrase or recreate — the subagents are matched against this exact file.

Also create `css-issues/[YY-MM-DD]/screenshots/` so subagents have a known location to write PNGs. Screenshots are scoped to the audit date, not to context — they live in one flat per-date directory keyed by prefix to avoid collisions.

### Phase 3 — Split work and dispatch audit subagents

**Partition by `[context]`.** Each subagent owns one (or sometimes two) contexts under the date — a context is the unit of "what slice was audited" and maps cleanly to a subagent's mental model. Common partitions for a marketing-site audit:

- One subagent for the homepage (context = `homepage`)
- One subagent per major route family (`features`, `pricing`, `customers`)
- One subagent for stub / shallow pages (context = `stubs`)

A 21-route site fits cleanly into 3–4 subagents. A larger site can scale to 6–8.

**File ownership is the boundary.** Each subagent's "Hard constraints" section names exactly which paths under `css-issues/[YY-MM-DD]/<context>/**` they may touch. Sibling subagents do not write to each other's subtrees. Screenshots use a per-subagent prefix — see the screenshot-prefix rule below.

**Use the prompt template** in `references/subagent-prompt-template.md`. It follows the mission-protocol shape (context → mission gravity → hard constraints → research guidance → DoD → verification → failure protocol → handback). Fill the per-agent slots and dispatch. The template is calibrated against real subagent runs — do NOT compress it.

**Dispatch strategy — DO NOT fully parallelize browser-driven audits.** This is the single most important footgun. `run-agent-browser` uses a shared Chrome daemon with a SingletonLock; if you fire 4 audit subagents in the same message they will contend, steal each other's sessions, and most will return with 0 findings. The patterns that actually work:

- **Stagger:** dispatch 2 at a time, wait for one batch to return before dispatching the next.
- **Sequential single-instance:** one subagent does all the pages serially. Slower wall-clock, dramatically higher reliability.

See `references/footguns.md` §1 and §7 for the full failure analysis and recovery protocol.

### Phase 4 — Aggregate audit output

When all subagents return:

1. **Inventory the output:**
   ```bash
   find css-issues/<YY-MM-DD> -name "*.md" -not -name "README.md" | wc -l
   ls css-issues/<YY-MM-DD>/screenshots/ | wc -l
   find css-issues/<YY-MM-DD> -mindepth 3 -maxdepth 3 -type d | sort
   ```
   Track count by context, by device, and by severity (critical / major / minor).

2. **Surface systemic findings.** The highest-value patterns are bugs that recur across contexts or devices — they collapse the fix pass from N edits to 1 edit. Read each subagent's "Observations" handback section and lift any "this manifests on N other pages" notes into the top of your summary.

3. **Verify tree shape.** Every finding file path should match `css-issues/<YY-MM-DD>/<context>/<device>/NN-<slug>.md`. Any file outside this shape is a subagent error — move it before continuing.

4. **Report a triage summary** to the user: total counts, severity breakdown, top 5–8 most critical individual bugs, the systemic patterns, and a path-to-everything. **Do not start fixing.** That is Phase 5.

### Phase 5 — Approval-gated fix dispatch

This phase is the headline new capability. Follow `references/dispatch-fixes-plan.md` in detail; the summary is:

1. **Cluster findings into themes.** A theme is a group whose findings share at least one of: the same source files, the same design-token misuse, the same viewport breakpoint, the same component family. If two candidate themes share more than ~70% of their target files, merge them.

2. **Choose `N` (1 ≤ N ≤ 20) fix subagents.** `N` is driven by **theme count**, NOT by finding count. A 60-finding audit can map cleanly to 4 themes and 4 subagents; an 18-finding audit might need 6 subagents if the themes are tightly file-disjoint. Cap at 20.

3. **Build the dispatch table** with these columns, in this order:

   | # | Theme | Findings (count + paths) | Files likely touched | Outcome | Suggested skill(s) |
   |---|---|---|---|---|---|

   - `#` — ordinal subagent number (1..N).
   - `Theme` — short name (3–6 words) for the cluster (`mobile-375 overflow cluster`, `dashboard contrast on dark surfaces`, `BrandLogo fallback`).
   - `Findings (count + paths)` — count and the full per-finding paths (relative to repo root). For >5 findings, list the first 5 and `…+N more`; the full list goes into the subagent prompt.
   - `Files likely touched` — best-guess `src/...` paths derived from each finding's `Likely cause` field. Deduplicated.
   - `Outcome` — one-line success criterion (`bug is invisible at 1440×900 and 375×812`, `BrandLogo renders correctly on every page`).
   - `Suggested skill(s) to invoke` — `frontend-design` is NOT a skill in this pack; route to canonical alternatives instead: `extract-saas-design` for token / system fixes, `build-tinacms-nextjs` / `build-macos-app` / `build-chrome-extension` for framework-specific edits, plain `Edit` / `Write` for vanilla CSS/component fixes, `review-self` for the post-fix self-review step. See `references/dispatch-fixes-plan.md` for the full routing matrix.

4. **Show the full table to the user** in the chat. Then ask, verbatim or close to it:

   > **Approve the plan above? Reply `go` to dispatch all, `go 1,3,5` to dispatch only those subagents, `change` to revise the plan, or `cancel` to stop here.**

5. **Block on the reply.** Do NOT spawn any fix subagent before the user has typed `go` (with optional subset) or an equivalent affirmative. If the reply is `change`, revise the table and re-ask. If `cancel`, stop — the audit artifact remains on disk for later.

6. **Spawn the approved fix subagents.** Each gets a tightly scoped prompt: (a) the list of finding files it owns (full paths), (b) the suggested skill to invoke, (c) the outcome criterion, (d) hard constraints on what it must NOT touch outside its theme. See `references/dispatch-fixes-plan.md` for the fix-subagent prompt template.

7. **Reconcile after fixes land.** When fix subagents return, each finding file gets its `## Fix tracking` block updated (`Fixed by subagent #N` checkbox flipped). The audit skill's job ends when (a) fixes are committed and (b) the audit tree reflects which findings are resolved. Re-running the audit verb is a separate session.

## Output Tree

The full grammar of the on-disk artifact:

```
css-issues/
├── README.md                                   (format spec — single source of truth, copy from references/audit-format-spec.md)
└── [YY-MM-DD]/                                  (audit date, e.g. 26-05-19; computed once at Phase 1)
    ├── screenshots/                             (flat per-date directory; per-subagent prefix avoids collisions)
    │   ├── homepage-bento-01-cards-overlap.png
    │   ├── feat-pricing-02-cta-cut-off.png
    │   └── stub-careers-01-page-x-scroll.png
    └── [context]/                                (the slice audited: dashboard / homepage / features / signup-flow / tables / ...)
        └── [device]/                             (viewport slug: mobile-375 / desktop-1440 / tablet-768 / ...)
            ├── 01-<short-slug>.md                (one finding per file; NN preserves discovery order within context/device)
            ├── 02-<short-slug>.md
            └── ...
```

### Segment definitions

**`YY-MM-DD`** — two-digit year, two-digit month, two-digit day of the audit. Computed at Phase 1 and pinned for every subagent. Same audit = same date even if it crosses midnight. Re-audits get a new date; old dates are durable history.

**`[context]`** — a hand-chosen short kebab-case name for the slice being audited. Choose one of these granularities depending on what makes sense for the codebase:

- **Page-level:** `dashboard`, `homepage`, `pricing`, `signup`, `settings-profile`. Best when each page has distinct visual concerns.
- **Flow-level:** `signup-flow`, `checkout-flow`, `onboarding`. Best when the audit spans 2–4 related pages with shared visual identity.
- **Component-family:** `tables`, `forms`, `modals`, `navigation`. Best when the bug class is component-shape across pages (a `<DataTable>` overflows on mobile *everywhere*).
- **Section:** `homepage-hero`, `homepage-bento`. Best when a single page is large enough to split across subagents.

Avoid mixing granularities in one audit — e.g. `dashboard/` and `tables/` overlap because tables appear on the dashboard; pick one. If the audit genuinely needs both, namespace them explicitly (`tables-component/` to clarify it's the standalone component, not the dashboard's tables).

**`[device]`** — canonical viewport slug. Choose from this list:

| Slug | Width × Height | Used for |
|---|---|---|
| `mobile-375` | 375 × 812 | iPhone-13 baseline; the brutal-truth viewport |
| `mobile-414` | 414 × 896 | iPhone Plus-class |
| `tablet-768` | 768 × 1024 | Where mega-menus collapse to slide-in panels |
| `tablet-1024` | 1024 × 768 | Where bento/feature grids go 2-col |
| `desktop-1280` | 1280 × 800 | Where 12-col grids often collapse to 8/4 |
| `desktop-1440` | 1440 × 900 | Primary design target on most modern sites |
| `desktop-1920` | 1920 × 1080 | Where max-width caps and white space appear |

Auditor MAY add more (e.g. `mobile-360` for Android baseline, `desktop-2560` for 4K) but MUST explain in the handback Observations why the canonical set was insufficient. The canonical set is the default; expansions are exceptions.

**`NN-short-slug.md`** — zero-padded ordinal (`01`, `02`, …, `99`) within `[context]/[device]/`, then a 3–6-word kebab-case slug describing the bug. Ordinal is per-`[context]/[device]/` (not global), preserves manual sort order, and gives the fix subagents a stable iteration order. Examples:

- `01-bento-cards-overlap-row2.md`
- `03-overflow-on-table-headers.md`
- `07-cta-button-clipped-by-cookie-banner.md`

### Canonical example

A finding for a table overflow on the dashboard, iPhone-13 viewport, third bug discovered for that context/device on 2026-05-19:

```
css-issues/26-05-19/dashboard/mobile-375/03-overflow-on-table-headers.md
```

That path is searchable, sortable, and locatable to a single subagent's worth of work. The fix dispatch step in Phase 5 reads these paths verbatim and assigns them to themes.

### Finding file format

Every `.md` file follows the template in `references/audit-format-spec.md`. The template includes a `## Fix tracking` block — Phase 5's dispatch step writes the assigned subagent number into that block, and the fix subagent flips its checkbox when done. See the format-spec file for the exact template.

## Canonical Viewports — full table

Every audited page should be visited at minimum two viewports (desktop + mobile). The full canonical set, which is what the bundled prompt template asks for, mirrors the device slugs above:

| Viewport slug | Width × Height | When to capture |
|---|---|---|
| `desktop-1440` | 1440 × 900 | Always (primary design target) |
| `desktop-1280` | 1280 × 800 | When the 1440 layout has any grid that compresses |
| `tablet-1024` | 1024 × 768 | When grid columns or sidebar visibility change at ≤1024 |
| `tablet-768` | 768 × 1024 | When mega-menu / sidebar collapse pattern applies |
| `mobile-414` | 414 × 896 | When a bug is suspected to differ between 375 and 414 |
| `mobile-375` | 375 × 812 | Always (iPhone-13 baseline) |

Subagents are told to be efficient: `desktop-1440` + `mobile-375` minimum for every page; intermediate viewports only when the desktop look is fine but the intermediate breakpoint is suspect. They are NOT expected to capture all six viewports on every page — the goal is bug coverage, not an exhaustive screenshot library.

## Severity Rubric

This is non-negotiable; every finding gets one of three labels:

- **critical** — content unreadable, broken layout blocks comprehension, overlap makes a card unclickable, hero/CTA not visible above the fold on a standard viewport.
- **major** — clearly broken visually (cards overlap, text cut off, misaligned grid) but the page is still usable and the message comes across.
- **minor** — polish issues, spacing slightly off, color contrast slightly weak, hover state missing, animation timing off.

The rubric matters because the fix-pass operator triages by severity. A subagent that files every minor spacing nit at "major" wastes the operator's attention budget. The format-spec file (`references/audit-format-spec.md`) carries the full rubric verbatim.

## Screenshot Prefix Convention

All screenshots land in the flat `css-issues/[YY-MM-DD]/screenshots/` directory. Filename collisions are inevitable without a convention. Use a per-subagent prefix:

- `homepage-<context>-NN-<slug>.png` for the homepage agent
- `feat-<slug>-<context>-NN-<slug>.png` for feature-page agents
- `stub-<route>-<context>-NN-<slug>.png` for stub-page agents
- Any other partition gets its own prefix

If you split feature pages across two agents (e.g. first 5 / second 5), give each a distinct prefix (`feat1-`, `feat2-`) to keep their screenshots disjoint. The bundled prompt template names a specific prefix for each agent role.

## Approval-Gated Fix Dispatch

(Detail in `references/dispatch-fixes-plan.md`. The summary lives here so it's impossible to miss while reading SKILL.md top-to-bottom.)

After Phase 4 lands and the user has the triage summary, **never proceed to fixes silently**. Always:

1. Build the Markdown dispatch table described in Phase 5.
2. Print the full table in chat.
3. Ask the explicit approval question (banned: starting to spawn workers before the user replies).
4. Block until the reply is `go` (full), `go <subset>` (selected #s), `change` (revise), or `cancel` (stop).
5. On `go`, spawn each approved subagent with: the full list of finding-file paths it owns, the `Suggested skill(s)` from the table, the `Outcome` success criterion, and Hard Constraints forbidding writes outside its theme's `src/` candidates and the assigned finding files.
6. On `change`, revise per the user's instructions and re-ask. On `cancel`, stop — the audit tree is durable.

When fix subagents return, each one updates the `## Fix tracking` block in every finding file it owned (flipping the checkbox to checked, recording its subagent #), commits its src changes in conventional-commit shape, and hands back. The audit skill's job is done when (a) every approved subagent has reported, (b) every finding it owned has a checked fix-tracking block or an explicit `wontfix` note, and (c) the orchestrator has surfaced any subagent that failed to land its outcome.

**If the user types `go` then immediately revises with new instructions — treat that as `change`, not partial approval.** Re-ask explicitly. Implicit approval is the failure mode this gate is designed to prevent.

See `references/dispatch-fixes-plan.md` for: the theme-clustering rubric, the full table-format reference, the routing matrix from theme-shape to skill, the fix-subagent prompt template, post-dispatch reconciliation steps, and worked examples (a 12-finding audit → 4 themes, a 60-finding audit → 8 themes, an audit where 70%-overlap merging collapses 6 candidate themes to 3).

## Footguns

The patterns that broke real runs are catalogued in `references/footguns.md`. The headline list:

1. **Fully parallel browser dispatch causes SingletonLock contention.** Use staggered or sequential dispatch.
2. **Subagents that "investigate but don't file" run out their budget.** The DoD enforces a floor count.
3. **Missing screenshot reference = invalid finding.** Format spec enforces; DoD enforces; fix-pass operator rejects.
4. **Subagents inventing bugs to hit a floor.** The floor is a guideline, not a quota.
5. **Same bug across N pages filed N times.** File once at the most representative manifestation; note where else it manifests.
6. **Failing to plant the README before dispatching.** Subagents invent their own format if there's no shared authority.
7. **Browser-daemon contention on the second wave.** Stale lock files; clear between batches.
8. **Dev server died mid-audit.** Re-verify liveness at batch boundaries.
9. **Subagent files findings outside owned-paths.** Hard Constraints must list both `<owned-paths>` and `<forbidden-paths>`.
10. **Findings without `Likely cause` source-file paths.** Push back in dispatch; re-audit.

New in this version:

11. **Spawning fix subagents without approval.** The single most likely Phase 5 failure. Banned. Always build the table, always ask, always block.
12. **`N` too high because findings were used as the unit instead of themes.** A 60-finding audit must NOT become 60 subagents. Cluster first; let `N` fall out of theme count. Cap at 20.
13. **Theme overlap >70% silently producing two redundant subagents.** Merge before dispatching; the routing matrix in `references/dispatch-fixes-plan.md` carries the merge rule.
14. **Date slug computed per-subagent rather than per-audit.** Findings end up in two date directories; aggregation breaks. Pin the date at Phase 1, pass it into every subagent prompt.

See `references/footguns.md` for the long-form recovery protocol for each.

## Reference Files

- `references/audit-format-spec.md` — verbatim contents of the `css-issues/README.md` you plant in Phase 2. Includes the per-finding template (with the `## Fix tracking` block for Phase 5), severity rubric, viewport table, what-to-look-for list, and the dated-tree path grammar.
- `references/subagent-prompt-template.md` — mission-protocol-shaped audit subagent prompt with slots for `<base-url>`, `<page-list>`, `<context>`, `<owned-paths>`, `<screenshot-prefix>`, `<floor-count>`, `<dispatch-mode>`, and the new `<audit-date>` slot. Fill the slots and dispatch.
- `references/dispatch-fixes-plan.md` — the Phase 5 playbook: theme-clustering rubric, dispatch-table column spec, theme→skill routing matrix, approval-gate phrasing, fix-subagent prompt template, post-dispatch reconciliation, and worked examples.
- `references/footguns.md` — long-form failure-mode catalogue with the exact symptoms each produces, including the new Phase 5 footguns (#11–#14).

## A Note on Tone

The audit produces files a human design lead will read in a triage meeting. Subagents are encouraged to describe what they SEE, not what they think the user wants to hear. *"The card extends 40px past its container's right border"* is useful. *"The card looks broken"* is not. The bundled template's "Observation" field instruction enforces this.

The goal isn't to make the site look bad. The goal is to make every fixable bug visible in one pass, severity-ranked, with a screenshot the operator can paste into chat — and then to convert that inventory into approved, scoped fix work that lands in `src/` without losing the audit's structure. That's it. That's the deliverable.
