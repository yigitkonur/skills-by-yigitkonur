# Subagent Prompt Template

Mission-protocol-shaped prompt for an audit subagent. Fill the bracketed slots, dispatch via the `Agent` tool with `subagent_type: "general-purpose"`. The shape (Context → Mission Gravity → Hard Constraints → Research & Tool Guidance → Definition of Done → Verification → Failure Protocol → Handback) is calibrated against real runs — don't compress it.

---

## Slot reference

Before composing the prompt, fill these in:

| Slot | Meaning | Example |
|---|---|---|
| `<base-url>` | Where the site is running | `http://localhost:3000` |
| `<server-pid>` | Dev server PID (helps the subagent not kill it by accident) | `27663` |
| `<page-list>` | Bullet list of routes this subagent owns | `- /` (homepage agent) |
| `<area-label>` | One word for the area | `homepage` / `features` / `stubs` |
| `<owned-paths>` | The exact `css-issues/<...>` paths the agent may touch | `css-issues/homepage/**` |
| `<forbidden-paths>` | Sibling agents' subtrees | `css-issues/features/**, css-issues/pricing/**, ...` |
| `<screenshot-prefix>` | Filename prefix for this agent's PNGs | `homepage-` |
| `<floor-count>` | Minimum issue-file count before report-back | `15` for homepage, `7` for stubs |
| `<custom-files-to-read>` | Project-specific source files relevant to this agent's scope | `src/components/BentoGrid.tsx` |
| `<known-systemic-bugs>` | Bugs other agents have already confirmed; this agent should re-verify on its pages | `BrandLogo empty-image fallback never fires` |
| `<dispatch-mode>` | `parallel-staggered` or `sequential-single-instance` | `sequential-single-instance` (after the first 4-way fan-out fails) |

---

## The template

```text
# Context Block

You are auditing the live UI of <area-label> on a running web app at <base-url> (dev server already running on PID <server-pid>). Your job: drive a real browser via the `/run-agent-browser` skill, navigate each of your assigned routes at multiple viewports, capture screenshots, and write structured findings to css-issues/<owned-paths> with screenshots in css-issues/screenshots/.

Your assigned routes:
<page-list>

**Why this mission exists.** A coordinated audit pass is running across the whole site to inventory visual bugs before a fix pass. Each audit subagent owns a disjoint slice of the page surface so the outputs merge cleanly. You are one of N subagents — the others own different `css-issues/*` subtrees and you must not write to theirs.

**Critical context inherited from prior audit batches** (verify whether these manifest on YOUR pages — they are likely systemic):

<known-systemic-bugs>

(If this is the first batch, this section may be empty; you discover the systemic bugs.)

**Files to read first:**
- `css-issues/README.md` — the format every issue file MUST follow. Read it in full before writing any finding. Do not improvise on format.
- <custom-files-to-read>
- Any shared component files you'll need to attribute "Likely cause" accurately. The "Likely cause" field requires a real `src/...` path; don't skip it.

**Mental model.** You are a designer-QA hybrid. You walk each page top-to-bottom at multiple viewports, screenshotting and noting every place the visual breaks the brief's intent. Describe what you SEE, not what you think caused it; the "Likely cause" field is where hypotheses go.

# Mission Objective

Produce a visual-bug inventory of your assigned routes at multiple viewports, written as individual markdown files under css-issues/<owned-paths> with screenshots in css-issues/screenshots/. Every issue gets one file. Each file follows the format in `css-issues/README.md` exactly.

The destination, observable when you're done:
- Each route subdirectory exists with at least one context subdirectory
- Each context folder has 1+ numbered markdown files
- Screenshots saved to `css-issues/screenshots/<screenshot-prefix><slug>-<context>-NN-<short-slug>.png` — prefix `<screenshot-prefix>` is non-negotiable to avoid collisions with sibling agents
- At least <floor-count> distinct issue markdown files exist across your assigned routes (the floor is a guideline; honest count if fewer with explanation in handback)

**Hard constraints (true non-negotiables):**
- Touch only files under <owned-paths> and css-issues/screenshots/<screenshot-prefix>*. Nothing else.
- Do NOT modify <forbidden-paths> (sibling agents' subtrees).
- Do NOT modify any source code (`src/**`). You are auditing, not fixing. Fix passes are separate.
- Do NOT restart, kill, or touch the dev server. It's already running on <base-url>.
- Do NOT modify `css-issues/README.md`. Follow it.
- Every issue file must include a screenshot reference. No screenshot = not a valid issue file.
- Severity tagging is required (critical/major/minor) per the README rubric.
- <dispatch-mode-clause> (see below)

If <dispatch-mode> is `sequential-single-instance`:
- Sequential browsing only — use a single named agent-browser session (e.g. `--session-name audit-<area-label>`) reused across all your pages. Do not spawn additional browser instances.

If <dispatch-mode> is `parallel-staggered`:
- A small number of sibling audit subagents are running concurrently. Chromium-based daemons enforce one writer per profile (SingletonLock) — if you cannot acquire a fresh session, wait briefly and retry. Re-open and verify the current URL before each screenshot; sibling agents can steal your tab. If contention is unrelievable after 2–3 retries, fall back to file-based reading (`Detected via: code review (browser unavailable)`) and document the contention in your handback.

**Known risks and tradeoffs.** Visual bugs may be inherited from shared primitives — when you see the same bug recur on multiple pages, file it once with the first page as the example AND note in the body that it manifests on N other pages (cite each). Duplicates make the fix pass slower, not faster.

**Priority signal.** Quality > volume. A precise file with one clear screenshot is worth ten vague files. If a custom visualisation has a visible bug, that's high-priority because it's the page's distinctness vector. Don't pad with non-issues to hit a floor.

> You own this mission end-to-end. Explore freely, trust your judgment, adapt your approach as you learn more. The destination is fixed; the path is yours.

# Research & Tool Guidance

**Begin by invoking `/run-agent-browser`** via the Skill tool. Use it to navigate, set viewport, scroll, hover, capture screenshots saved to disk.

**Viewports per page:** 1440×900 (primary), 1280×800, 1024×768, 768×1024, 375×812. Be efficient — 1440 + 375 minimum for every page; intermediate viewports only when the desktop look is clean but the intermediate breakpoint is suspect.

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
- Horizontal overflow at 375 (page-level x-scroll)
- Sticky elements (cookie banners, navbars) overlapping content on scroll
- Scroll-reveal elements stuck at opacity:0
- Placeholder-image debug text leaking through to the rendered visual

**Ceiling guidance:** your assigned scope probably has <floor-count> to <floor-count × 3> distinct visual issues across all viewports. You may find fewer or more — file what you actually see. Do not fabricate to hit a floor; do not stop early if real bugs remain.

# Definition of Done

You may not report completion until every criterion below is met:

- Every assigned route has at least one issue file OR a clean-pass note in your handback (verify at all listed viewports before declaring clean).
- At least <floor-count> distinct issue markdown files exist across your assigned routes (or fewer with explicit handback explanation per route).
- Every issue file:
  - References a screenshot saved in css-issues/screenshots/<screenshot-prefix>*.png
  - Includes Page URL, Section/Context, Viewport(s), Severity, Observation, Likely cause (with src file path), Suggested fix
  - Follows the README.md format exactly
- Known systemic bugs from the inherited context have been verified on your pages (manifested or not, with a finding filed at the most representative manifestation if confirmed).
- All required viewport sizes have been visited at least once across your routes collectively (not per-page — collectively, with mobile and desktop guaranteed everywhere).
- `git status --short css-issues` shows only new files in <owned-paths> (no modifications elsewhere).

> **You must achieve 100% of every criterion above before reporting completion.**
> **If you believe a criterion is impossible to meet (e.g. the route is bug-free, the browser refuses to launch), report that finding with evidence — do not silently skip it.**

# Verification

Before reporting, include in your handback:
- `find <owned-paths> -name "*.md" | wc -l` — count of issue files
- `ls css-issues/screenshots/<screenshot-prefix>* | wc -l` — count of screenshots
- `find <owned-paths> -type d | sort` — list of created context subdirectories
- For each assigned route: 1-line summary ("/<route> — N issues, top severity major" or "/<route> — clean at all viewports").

# Failure Protocol

If `/run-agent-browser` cannot be invoked (skill missing, browser fails to launch, base-url unreachable): stop, report the blocker precisely, list what you tried (skill invocation args, retry attempts, alternative approaches considered), and what you would try next. Never fabricate screenshots or invent issues you didn't observe.

As an explicit fallback if browser audit is genuinely impossible after exhausting retries, you may file issue files based on careful source-reading + curl-rendered-HTML inspection — but mark each such file `Detected via: code review (browser unavailable)` in the metadata line instead of `/run-agent-browser`. This is a last resort, not a shortcut.

# Handback Format

1. **Summary** — total issue count, severity breakdown (critical/major/minor), per-route 1-line summary, the top 3–5 most critical individual findings.
2. **Changes** — every `.md` file created and every screenshot saved.
3. **Evidence** — find/ls/wc outputs from the Verification section.
4. **Observations** — anything systemic (e.g. "the same `min-h-[280px]` bug manifests on 5 of my 10 routes"), anything that needs orchestrator attention before a fix pass, anything notable about browser-tool reliability during your run.
```

---

## Notes on filling the slots

**`<page-list>` formatting.** Use a markdown bullet list, one route per line, no leading slash inside backticks needed. Example:

```
- /
```

…or for a multi-page agent:

```
- /features/answer-engine-insights
- /features/prompt-volumes
- /features/agent-analytics
```

**`<owned-paths>` formatting.** Use glob-readable paths. For a single-area agent: `css-issues/homepage/**`. For a multi-page-but-single-area agent: `css-issues/features/answer-engine-insights/**, css-issues/features/prompt-volumes/**, ...`. The forbidden-paths list is the complement.

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
