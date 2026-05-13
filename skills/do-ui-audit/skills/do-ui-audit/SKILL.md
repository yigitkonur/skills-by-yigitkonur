---
name: do-ui-audit
description: Use skill if you are auditing a running web app's UI across pages and viewports, dispatching subagents that drive a real browser to capture screenshots and write structured visual-bug findings.
---

# Do UI Audit

Disciplined visual QA of a running web app. Dispatch parallel subagents that each drive the `run-agent-browser` skill across an owned slice of pages, capture screenshots at five canonical viewports, and write one markdown finding per real bug. The goal is a reviewable, durable audit artifact — `css-issues/` becomes a single source of truth that a follow-up fix pass can work through file-by-file.

This skill is opinionated about *how* the audit is conducted, not what counts as a bug — the subagents bring their own design eye. The opinions are: where files live, the format of every finding, viewport coverage, and the failure modes you have to design around.

## When To Use

Trigger on phrases and contexts like:

- *"audit the UI"*, *"check the site for visual bugs"*, *"find CSS issues"*, *"QA the design"*
- *"screenshot every page and find layout breaks"*, *"test all my pages at multiple viewports"*
- *"run agent-browser across the site and document what's broken"*
- *"do a visual sweep"*, *"do a frontend QA pass"*, *"do a design QA"*
- *"check responsive breakpoints across the whole site"*
- *"the site is feature-complete — find what's visually wrong before I ship"*
- *"go through every page at desktop and mobile and write me a bug list"*

Do **NOT** use this skill for:

- *Single-page UI debugging* — if the user knows the bug is on one page and just wants it fixed, drive `run-agent-browser` directly inline. This skill's overhead pays back when you have ≥5 routes.
- *Functional / behavior testing* — clicks, form submits, end-to-end flows. Use `run-playwright` or similar.
- *Accessibility-only audits* — use specialized a11y tooling; this skill is layout/visual-first.
- *Performance audits* — Lighthouse / Web Vitals belong elsewhere.
- *Authoring a fix pass* — this skill produces the bug inventory. The fix pass is a separate operation that reads the inventory and edits source.

## The Workflow (Four Phases)

### Phase 1 — Verify preconditions

Before dispatching any subagents, confirm:

1. **A dev or prod server is reachable**. `curl -s -o /dev/null -w "%{http_code}" <url>` should return 200. If the user wants to audit `localhost:3000` and nothing is running, boot the dev server first (in the background) and wait for "Ready in" before continuing. Don't dispatch audit subagents against a server that isn't up — they'll waste effort.
2. **`run-agent-browser` skill is available**. Check the available-skills list. If it isn't there, surface this and stop — there is no graceful fallback that produces real screenshots.
3. **You know every page that needs auditing**. Ask the user for the full route list if it's not obvious from context. For larger sites, enumerate routes from the source (App Router pages, sitemap.xml, etc.) rather than guessing.

### Phase 2 — Plant the format spec

Write `css-issues/README.md` in the project root before dispatching anything. Every audit subagent will read this file as their format authority — pulling it out of every subagent prompt and into one shared file keeps prompts lean and the format consistent.

Copy the format spec verbatim from `references/audit-format-spec.md` (this skill's bundled reference). Do not paraphrase or recreate it — the subagents are matched against this exact file.

Also create `css-issues/screenshots/` so subagents have a known location to write PNGs.

### Phase 3 — Split work and dispatch

**Partition pages by disjoint directory ownership.** Each subagent owns a slice of `css-issues/` and nothing else. Common partitions for a marketing-site audit:

- One subagent for the homepage (almost always the most complex single page)
- One subagent per ~5 feature/inner pages
- One subagent for all stub / shallow pages

A 21-route site fits cleanly into 3–4 subagents. A larger site can scale to 6–8.

**File ownership is the boundary.** Each subagent's "Hard constraints" section names exactly which paths under `css-issues/` they may touch. Sibling subagents do not write to each other's subtrees. Screenshots collide if not prefixed — see the screenshot-prefix rule below.

**Use the prompt template** in `references/subagent-prompt-template.md` (bundled with this skill). It follows the mission-protocol shape (context → mission gravity → hard constraints → research guidance → BSV definition of done → verification → failure protocol → handback). Fill in the per-agent slots and dispatch. The template is calibrated against real subagent runs — don't compress it.

**Dispatch strategy — DO NOT fully parallelize browser-driven audits.** This is the single most important footgun in this skill. `run-agent-browser` uses a shared Chrome daemon with a SingletonLock; if you fire 4 audit subagents in the same message they will contend, steal each other's sessions, and most will return with 0 findings. The patterns that actually work:

- **Stagger**: dispatch 2 at a time, wait for one batch to return before dispatching the next, OR
- **Sequential single-instance**: one subagent does all the pages serially. Slower wall-clock, dramatically higher reliability.

The audit that produced 57 issues + 159 screenshots across 21 routes was the staggered model: homepage + stubs first batch (parallel-safe because they target different page surfaces and the browser sessions interleaved tolerably), then 10 feature pages in a single sequential subagent as a retry after the first 4-way fan-out lost two agents to contention.

### Phase 4 — Aggregate and report

When all subagents return:

1. **Inventory the output**:
   ```bash
   find css-issues -name "*.md" -not -name "README.md" | wc -l
   ls css-issues/screenshots/ | wc -l
   ```
   Track count by area (homepage / features / stubs) and by severity (critical / major / minor).

2. **Surface systemic findings**. The highest-value patterns are bugs that recur across pages — they collapse the fix pass from N edits to 1 edit. Read each subagent's "Observations" handback section and lift any "this manifests on N other pages" notes into the top of your summary.

3. **Report a triage table** to the user: total counts, severity breakdown, top 5–8 most critical individual bugs, the systemic patterns, and a path-to-everything. Do not start fixing without explicit authorization — fix passes are a separate operation.

4. **Optionally commit** the audit. The `css-issues/` directory is a durable artifact: future fix passes work from it, the user can browse it offline, and it survives session changes. Stage and commit only if the user asks.

## Canonical Viewports

Every audited page should be visited at minimum two viewports (desktop + mobile). The full canonical set, which is what the bundled prompt template asks for:

| Viewport | Width × Height | Reason |
|---|---|---|
| Desktop XL | 1440 × 900 | Primary design target |
| Desktop M | 1280 × 800 | Where 12-col grids often collapse to 8/4 |
| Tablet | 1024 × 768 | Where bento or feature grids go 2-col |
| Mobile L | 768 × 1024 | Where mega-menus collapse to slide-in panels |
| Mobile S | 375 × 812 | iPhone 13 standard, the brutal-truth viewport |

Subagents are told to be efficient: 1440 + 375 minimum for every page, intermediate viewports only when the desktop look is fine but the intermediate breakpoint is suspect. They are not expected to capture all five on every page — the goal is bug coverage, not exhaustive screenshot library.

## Severity Rubric

This is non-negotiable; every finding gets one of three labels:

- **critical** — content unreadable, broken layout blocks comprehension, overlap makes a card unclickable, hero/CTA not visible above the fold on a standard viewport.
- **major** — clearly broken visually (cards overlap, text cut off, misaligned grid) but the page is still usable and the message comes across.
- **minor** — polish issues, spacing slightly off, color contrast slightly weak, hover state missing, animation timing off.

The rubric matters because the fix-pass operator triages by severity. A subagent that files every minor spacing nit at "major" wastes the operator's attention budget.

## Screenshot Prefix Convention

All screenshots land in the flat `css-issues/screenshots/` directory. Filename collisions are inevitable without a convention. Use a per-subagent prefix:

- `homepage-<context>-<NN>-<slug>.png` for the homepage agent
- `feat-<slug>-<context>-<NN>-<slug>.png` for feature-page agents
- `stub-<route>-<context>-<NN>-<slug>.png` for stub-page agents
- Any other partition gets its own prefix

If you split the feature pages across two agents (e.g. first 5 / second 5), give each a distinct prefix (`feat1-`, `feat2-`) to keep their screenshots disjoint. The bundled prompt template names a specific prefix for each agent role.

## Footguns

The patterns that broke real runs:

1. **Fully parallel browser dispatch causes SingletonLock contention.** Chromium-based daemons (which is what `run-agent-browser` is built on) enforce one writer per profile. Four parallel agents will produce two casualties. **Use staggered or sequential dispatch.** This skill's bundled prompt template includes an explicit "sequential browsing only" line that the audit subagent must follow.
2. **Subagents that "investigate but don't file" run out their token budget.** Without an explicit floor in the Definition of Done ("at least N issue files before reporting"), subagents can spend their entire budget exploring the page and return zero artifacts. The bundled template encodes a sensible floor: ≥15 for the homepage, ≥15 across all 10 feature pages, ≥7 across stubs.
3. **No screenshot reference = invalid finding.** A `.md` file without a `![issue](../../screenshots/...)` reference is unverifiable. The format spec enforces this; the audit subagent's DoD enforces it; the fix-pass operator will reject findings without one.
4. **Subagents inventing bugs to hit a floor.** The floor is a guideline, not a quota. If a page is genuinely bug-free at all viewports, the subagent says so in the handback. Padding with non-issues poisons the inventory.
5. **Same bug across N pages filed N times.** Subagents are told: when a bug recurs (BrandLogo fallback failing on every page that uses it, for example), file the issue once where you first noticed it AND note in the body that it manifests on N other pages. Duplicates make the fix pass slower, not faster.
6. **Failing to plant the README.md before dispatching.** Subagents read the format spec on entry; if it's not there, they each invent their own format and the output is unmergeable. Always Phase 2 before Phase 3.

## Output Anatomy

After the skill completes, the project has:

```
css-issues/
├── README.md                                 (the format spec — single source of truth)
├── screenshots/
│   ├── homepage-<context>-NN-<slug>.png      (one per finding, plus context shots)
│   ├── feat-<slug>-<context>-NN-<slug>.png
│   └── stub-<route>-<context>-NN-<slug>.png
└── <area>/                                    (homepage / features/<slug> / pricing / customers / ...)
    └── <context>/                             (bento-grid / hero / nav / proof / capability-modules / ...)
        ├── 01-<short-slug>.md                 (one .md per real bug)
        ├── 02-<short-slug>.md
        └── ...
```

Every `.md` file follows the template in `references/audit-format-spec.md`. The README.md at the root explains the layout to anyone who opens the directory cold — including a future Claude session running a fix pass against it.

## Reference Files

- `references/audit-format-spec.md` — verbatim contents of the `css-issues/README.md` you plant in Phase 2. Includes the per-finding template, severity rubric, viewport table, and what-to-look-for list.
- `references/subagent-prompt-template.md` — mission-protocol-shaped subagent prompt with slots for `<page-list>`, `<owned-paths>`, `<screenshot-prefix>`, `<floor-count>`, etc. Fill the slots and dispatch.
- `references/footguns.md` — long-form explanations of the failure modes summarized above, with the exact symptoms each one produces (so you can recognize them mid-run and pivot).

## A Note on Tone

The audit produces files a human design lead will read in a triage meeting. Subagents are encouraged to describe what they SEE, not what they think the user wants to hear. "The card extends 40px past its container's right border" is useful. "The card looks broken" is not. The bundled template's "Observation" field instruction enforces this.

The goal isn't to make the site look bad. The goal is to make every fixable bug visible in one pass, severity-ranked, with a screenshot the operator can paste into chat when they ask "what does this look like?". That's it. That's the deliverable.
