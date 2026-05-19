# Audit Subagent Prompt Template

Mission-protocol-shaped prompt for an **audit** subagent. Fill the bracketed slots, dispatch via the `Agent` tool with `subagent_type: "general-purpose"`. The shape (Context → Mission Gravity → Hard Constraints → Research & Tool Guidance → Definition of Done → Verification → Failure Protocol → Handback) is calibrated against real runs — don't compress it.

This template is for Phase 3 (audit). The Phase 5 fix-subagent prompt lives in `dispatch-fixes-plan.md`.

---

## Slot reference

Before composing the prompt, fill these in:

| Slot | Meaning | Example |
|---|---|---|
| `<audit-date>` | YY-MM-DD pinned at Phase 1 — same for every subagent in this run | `26-05-19` |
| `<base-url>` | Where the site is running | `http://localhost:3000` |
| `<server-pid>` | Dev server PID (helps the subagent not kill it by accident) | `27663` |
| `<page-list>` | Bullet list of routes this subagent owns | `- /dashboard` |
| `<context>` | The audit context slug for this subagent | `dashboard` / `homepage` / `features` / `stubs` |
| `<owned-paths>` | The exact `css-issues/<audit-date>/<context>/**` paths the agent may touch | `css-issues/26-05-19/dashboard/**` |
| `<forbidden-paths>` | Sibling agents' subtrees | `css-issues/26-05-19/features/**, css-issues/26-05-19/pricing/**, ...` |
| `<screenshot-prefix>` | Filename prefix for this agent's PNGs | `homepage-` / `feat-` / `stub-` |
| `<floor-count>` | Minimum issue-file count before report-back | `15` for homepage, `7` for stubs |
| `<custom-files-to-read>` | Project-specific source files relevant to this agent's scope | `src/components/BentoGrid.tsx` |
| `<known-systemic-bugs>` | Bugs other agents have already confirmed; this agent should re-verify on its pages | `BrandLogo empty-image fallback never fires` |
| `<dispatch-mode>` | `parallel-staggered` or `sequential-single-instance` | `sequential-single-instance` (after the first 4-way fan-out fails) |

---

## The template

```text
# Context Block

You are auditing the live UI of <context> on a running web app at <base-url> (dev server already running on PID <server-pid>). Your job: drive a real browser via the `/run-agent-browser` skill, navigate each of your assigned routes at multiple viewports, capture screenshots, and write structured findings under `css-issues/<audit-date>/<context>/<device>/NN-<slug>.md` with screenshots in `css-issues/<audit-date>/screenshots/`.

Your assigned routes:
<page-list>

**The audit date for this run is `<audit-date>`.** Do not recompute it. Every file you write goes under `css-issues/<audit-date>/`. Even if midnight passes during your run, keep using `<audit-date>`.

**Why this mission exists.** A coordinated audit pass is running across the whole site to inventory visual bugs before a fix pass. Each audit subagent owns a disjoint context under `css-issues/<audit-date>/` so the outputs merge cleanly. You are one of N subagents — the others own different `<context>/` subtrees and you must not write to theirs.

**Critical context inherited from prior audit batches** (verify whether these manifest on YOUR pages — they are likely systemic):

<known-systemic-bugs>

(If this is the first batch, this section may be empty; you discover the systemic bugs.)

**Files to read first:**
- `css-issues/README.md` — the format every issue file MUST follow. Read it in full before writing any finding. Do not improvise on format.
- <custom-files-to-read>
- Any shared component files you'll need to attribute "Likely cause" accurately. The "Likely cause" field requires a real `src/...` path; don't skip it.

**Mental model.** You are a designer-QA hybrid. You walk each page top-to-bottom at multiple viewports, screenshotting and noting every place the visual breaks the brief's intent. Describe what you SEE, not what you think caused it; the "Likely cause" field is where hypotheses go.

# Mission Objective

Produce a visual-bug inventory of your assigned routes at multiple viewports, written as individual markdown files under `css-issues/<audit-date>/<context>/<device>/NN-<slug>.md` with screenshots in `css-issues/<audit-date>/screenshots/`. Every issue gets one file. Each file follows the format in `css-issues/README.md` exactly, including the `## Fix tracking` block (which you leave with `Fixed by subagent #<TBD>` — the orchestrator fills this in at Phase 5).

The destination, observable when you're done:
- For each `<device>` slug where you found bugs, a subdirectory under `css-issues/<audit-date>/<context>/<device>/` exists with at least one numbered `.md`.
- Screenshots saved to `css-issues/<audit-date>/screenshots/<screenshot-prefix><slug>-<NN>-<short-slug>.png` — prefix `<screenshot-prefix>` is non-negotiable to avoid collisions with sibling agents.
- At least `<floor-count>` distinct issue markdown files exist across your assigned routes (the floor is a guideline; honest count if fewer with explanation in handback).

**Hard constraints (true non-negotiables):**
- Touch only files under `<owned-paths>` and `css-issues/<audit-date>/screenshots/<screenshot-prefix>*`. Nothing else.
- Do NOT modify `<forbidden-paths>` (sibling agents' subtrees).
- Do NOT modify any source code (`src/**`). You are auditing, not fixing. Fix passes are separate (Phase 5).
- Do NOT restart, kill, or touch the dev server. It's already running on `<base-url>`.
- Do NOT modify `css-issues/README.md`. Follow it.
- Every issue file must include a screenshot reference. No screenshot = not a valid issue file.
- Severity tagging is required (critical/major/minor) per the README rubric.
- Every issue file must include the `## Fix tracking` block (with `Fixed by subagent #<TBD>` placeholder).
- Use the canonical device slugs from `css-issues/README.md` for the `<device>` directory. Do not invent new viewport slugs without surfacing it in your handback.
- `<dispatch-mode-clause>` (see below)

If `<dispatch-mode>` is `sequential-single-instance`:
- Sequential browsing only — use a single named agent-browser session (e.g. `--session-name audit-<context>`) reused across all your pages. Do not spawn additional browser instances.

If `<dispatch-mode>` is `parallel-staggered`:
- A small number of sibling audit subagents are running concurrently. Chromium-based daemons enforce one writer per profile (SingletonLock) — if you cannot acquire a fresh session, wait briefly and retry. Re-open and verify the current URL before each screenshot; sibling agents can steal your tab. If contention is unrelievable after 2–3 retries, fall back to file-based reading (`Detected via: code review (browser unavailable)`) and document the contention in your handback.

**Known risks and tradeoffs.** Visual bugs may be inherited from shared primitives — when you see the same bug recur on multiple pages, file it once with the first page as the example AND note in the `Also affects:` field that it manifests on N other pages (cite each). Duplicates make the fix pass slower, not faster.

**Priority signal.** Quality > volume. A precise file with one clear screenshot is worth ten vague files. If a custom visualisation has a visible bug, that's high-priority because it's the page's distinctness vector. Don't pad with non-issues to hit a floor.

> You own this mission end-to-end. Explore freely, trust your judgment, adapt your approach as you learn more. The destination is fixed; the path is yours.

# Research & Tool Guidance

**Begin by invoking `/run-agent-browser`** via the Skill tool. Use it to navigate, set viewport, scroll, hover, capture screenshots saved to disk.

**Viewports per page:** `desktop-1440` (1440×900), `desktop-1280`, `tablet-1024`, `tablet-768`, `mobile-414`, `mobile-375`. Be efficient — `desktop-1440` + `mobile-375` minimum for every page; intermediate viewports only when the desktop look is clean but the intermediate breakpoint is suspect.

**Things to check beyond raw layout:**
- Overlapping elements (cards on cards, text on visuals)
- Text truncation / overflow
- Misaligned grids, broken column counts
- Inconsistent section spacing
- Hover states missing or broken
- Z-index collisions (dropdowns behind content; sticky nav over headlines)
- Particle/canvas elements drawing outside their container
- Reduced-motion behavior at `prefers-reduced-motion: reduce`
- Mobile menu open/close transitions
- Image aspect ratios broken (placeholder images at wrong size)
- BrandLogo fallback tile showing instead of the real logo
- Contrast issues on dark surfaces
- Horizontal overflow at `mobile-375` (page-level x-scroll)
- Sticky elements (cookie banners, navbars) overlapping content on scroll
- Scroll-reveal elements stuck at opacity:0
- Placeholder-image debug text leaking through to the rendered visual

**Ceiling guidance:** your assigned scope probably has `<floor-count>` to `<floor-count × 3>` distinct visual issues across all viewports. You may find fewer or more — file what you actually see. Do not fabricate to hit a floor; do not stop early if real bugs remain.

# Definition of Done

You may not report completion until every criterion below is met:

- Every assigned route has at least one issue file OR a clean-pass note in your handback (verify at all listed viewports before declaring clean).
- At least `<floor-count>` distinct issue markdown files exist across your assigned routes (or fewer with explicit handback explanation per route).
- Every issue file:
  - Lives at `css-issues/<audit-date>/<context>/<device>/NN-<slug>.md` — no other tree shape is valid
  - References a screenshot saved in `css-issues/<audit-date>/screenshots/<screenshot-prefix>*.png`
  - Includes Page URL, Section/Context, Viewport, Also affects, Severity, Observation, Likely cause (with src file path), Suggested fix, and the `## Fix tracking` block (with the `Fixed by subagent #<TBD>` placeholder)
  - Follows the README.md format exactly
- Known systemic bugs from the inherited context have been verified on your pages (manifested or not, with a finding filed at the most representative manifestation if confirmed).
- All required viewport sizes have been visited at least once across your routes collectively (not per-page — collectively, with mobile and desktop guaranteed everywhere).
- `git status --short css-issues/<audit-date>` shows only new files in `<owned-paths>` and `css-issues/<audit-date>/screenshots/<screenshot-prefix>*` (no modifications elsewhere).

> **You must achieve 100% of every criterion above before reporting completion.**
> **If you believe a criterion is impossible to meet (e.g. the route is bug-free, the browser refuses to launch), report that finding with evidence — do not silently skip it.**

# Verification

Before reporting, include in your handback:
- `find css-issues/<audit-date>/<context> -name "*.md" | wc -l` — count of issue files
- `ls css-issues/<audit-date>/screenshots/<screenshot-prefix>* | wc -l` — count of screenshots
- `find css-issues/<audit-date>/<context> -mindepth 2 -maxdepth 2 -type d | sort` — list of created device subdirectories
- For each assigned route: 1-line summary (`/<route> — N issues, top severity major` or `/<route> — clean at all viewports`).

# Failure Protocol

If `/run-agent-browser` cannot be invoked (skill missing, browser fails to launch, base-url unreachable): stop, report the blocker precisely, list what you tried (skill invocation args, retry attempts, alternative approaches considered), and what you would try next. Never fabricate screenshots or invent issues you didn't observe.

As an explicit fallback if browser audit is genuinely impossible after exhausting retries, you may file issue files based on careful source-reading + curl-rendered-HTML inspection — but mark each such file `Detected via: code review (browser unavailable)` in the metadata line instead of `/run-agent-browser`. This is a last resort, not a shortcut.

# Handback Format

1. **Summary** — total issue count, severity breakdown (critical/major/minor), per-route 1-line summary, the top 3–5 most critical individual findings.
2. **Changes** — every `.md` file created (full path under `css-issues/<audit-date>/<context>/`) and every screenshot saved (full path under `css-issues/<audit-date>/screenshots/`).
3. **Evidence** — find/ls/wc outputs from the Verification section.
4. **Observations** — anything systemic (e.g. "the same `min-h-[280px]` bug manifests on 5 of my 10 routes"), anything that needs orchestrator attention before Phase 5 (e.g. "I suspect the BrandLogo issue spans every page in the project; recommend one fix subagent owning all BrandLogo findings across all contexts"), anything notable about browser-tool reliability during your run.
```

---

## Notes on filling the slots

**`<audit-date>` is pinned at Phase 1.** Compute it once with `date -u +"%y-%m-%d"` (or equivalent) and pass it into every subagent prompt. Subagents do NOT compute their own date. Mixing dates in one audit run produces a fragmented tree.

**`<page-list>` formatting.** Use a markdown bullet list, one route per line. Example:

```
- /dashboard
- /dashboard/insights
- /dashboard/settings
```

**`<context>` choice.** One subagent typically owns one context. Use page-level for most audits; switch to flow-level or component-family if the codebase is structured that way. Mixing granularities in one audit is a footgun — pick one.

**`<owned-paths>` formatting.** Use glob-readable paths scoped under the date. For a single-context agent: `css-issues/26-05-19/dashboard/**`. For a multi-context agent: `css-issues/26-05-19/features/**, css-issues/26-05-19/pricing/**`. The forbidden-paths list is the complement.

**`<floor-count>` calibration** (based on real runs):

- 1 large page (homepage with 19 sections): floor = 15
- 5 feature pages: floor = 5
- 10 feature pages: floor = 15
- 7 stub pages: floor = 7
- 20+ pages in one agent: floor = 20

These are floors, not targets. A genuinely clean page produces 0 findings — the floor exists to prevent agents from declaring "done" after a cursory scroll-through.

**`<known-systemic-bugs>` is iterative.** First-batch agents have empty `<known-systemic-bugs>` and discover them. Second-batch agents inherit findings from the first batch and verify whether they manifest on the new scope. This is what makes staggered dispatch productive — later agents are better-informed.

**`<dispatch-mode>` decision tree:**

- If `run-agent-browser` is known reliable in this environment and you have ≤2 agents → `parallel-staggered`
- If `run-agent-browser` has a shared-daemon model (Chrome SingletonLock) and you have >2 agents → `sequential-single-instance` (one agent per batch, batches run serially)
- If a previous parallel attempt stalled → fall back to `sequential-single-instance` for the retry
