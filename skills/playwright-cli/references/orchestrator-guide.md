# Orchestrator Guide: Multi-Agent Browser Coordination

## Table of Contents

- [Session Architecture](#session-architecture)
- [What Every Sub-Agent Brief Must Include](#what-every-sub-agent-brief-must-include)
- [Verification Levels](#verification-levels)
- [Multi-Agent Tab Coordination](#multi-agent-tab-coordination)
- [Orchestrator Checklist](#orchestrator-checklist)
- [Verification Patterns (Building Blocks for Briefs)](#verification-patterns-building-blocks-for-briefs)

## Session Architecture

One browser process, shared by all agents. The orchestrator bootstraps it. Sub-agents are tenants — they get tabs.

### Bootstrap (orchestrator runs ONCE before dispatching any agent)
```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true npx playwright install chromium
playwright-cli session-stop 2>/dev/null    # kill stale sessions from previous runs
playwright-cli config --browser=chromium
```

### After ALL agents complete
```bash
playwright-cli session-stop-all
```

### Why this architecture
- 5 agents x 5 separate sessions = CPU death. 1 session x 5 tabs = negligible overhead.
- Tabs share cookies and localStorage — same as real users.
- If the session dies mid-run, re-run the bootstrap block above. Agents can resume.

## What Every Sub-Agent Brief Must Include

Paste this block into any agent brief that touches the browser:

> **PLAYWRIGHT OPERATING RULES — read fully before your first command:**
>
> **Session lifecycle — you are a tab tenant, not the session owner:**
> ```
> tab-new → open <url> → [your work] → tab-close <your-index>
> ```
> Never create sessions. Never run `close` (kills entire shared session for all agents).
> Only `tab-close <index>` to close YOUR tab when done.
>
> **The cardinal rule — refs die on ANY page change:**
> After `click`, `open`, `hover`, `reload`, `go-back`, `tab-select`, or ANY navigation:
> run `snapshot` to get fresh refs before interacting with elements.
> Stale refs either error or silently target the wrong element. No warnings.
> Pattern: `action → snapshot → use new refs`. Always.
>
> **The observe-act loop — this is how you work:**
> ```
> snapshot                    → read structure, get element refs
> screenshot --full-page --filename=step-N.png → read visual state
> [decide based on what you observed]
> [act: click/fill/navigate]
> snapshot                    → observe new state (mandatory)
> screenshot --filename=step-N+1.png           → confirm result
> [repeat until task is verified]
> ```
> Use `snapshot` for interaction (refs). Use `screenshot` for visual judgment. Both, always.
>
> **Navigation traps:**
> - `tab-new <url>` opens `about:blank`, NOT the URL. Always: `tab-new` then `open <url>`.
> - Multi-tab "Page URL" header lies. Use `eval "() => window.location.href"` for truth.
> - After `tab-close`, remaining tab indexes shift. Run `tab-list` to reorient.
>
> **Form interaction:**
> - Use `fill <ref> "text"` for setting values (replaces content, targets by ref).
> - `type "text"` appends to focused element — only for keyboard-specific testing.
> - Snapshots do NOT show form values. Verify with: `eval "(el) => el.value" <ref>`
> - `fill <ref> "text" --submit` fills then presses Enter — shortcut for search/login.
>
> **When things go wrong:**
> - "modal state" error → a dialog is blocking. Run `dialog-accept` or `dialog-dismiss`.
> - "ref not found" → refs are stale. Run `snapshot`, use new refs.
> - Blank page → you forgot `open <url>` after `tab-new`.
> - Unexpected behavior → `playwright-cli --help <command>` to verify syntax.
>
> **Data extraction:**
> - `console error` and `network` return FILE PATHS, not content. You must read the file.
> - `eval "() => expression"` runs JS in page context. Returns primitives and plain objects.
> - `eval "(el) => el.property" <ref>` runs JS against a specific element.
> - Don't return DOM nodes from eval — return extracted data (.map, .textContent, etc).
> - `run-code 'async (page) => { ... }'` for full Playwright API access. Single quotes outer, double inner.
>
> **Scrolling:** Playwright auto-scrolls to elements before click/fill/hover.
> Only scroll manually for: fold-by-fold inspection, lazy-load testing, infinite scroll, viewport screenshots.

## Verification Levels

Match verification depth to risk. Not every task needs the same scrutiny.

### Level 1 — Existence check (low risk, minor change)
```
open <url> → snapshot → confirm element exists in tree → screenshot → done
```
Use for: copy changes, icon swaps, adding a static element.

### Level 2 — Behavior check (medium risk, interactive change)
```
open <url> → snapshot → interact (click/fill) → snapshot again →
confirm state changed correctly → screenshot before + after → done
```
Use for: form fixes, button behavior, toggle states, navigation changes.

### Level 3 — Full visual matrix (high risk, layout/design change)
```
Desktop light  → screenshot
Desktop dark   → screenshot
Mobile light   → screenshot
Mobile dark    → screenshot
+ behavior checks at each viewport
```
Use for: new components, responsive redesigns, theme changes, anything visual.

### Level 4 — Regression suite (critical path, multi-flow)
```
Full Level 3 matrix
+ test all connected user flows (not just the changed one)
+ console error check + network failure check
+ before/after comparison screenshots
```
Use for: auth flows, checkout, onboarding, anything where breakage = lost users.

When writing briefs, specify the level: "This is a Level 3 verification task" or embed the specific commands directly in the Definition of Done.

## Multi-Agent Tab Coordination

### Each agent's lifecycle
```
tab-new → open <url> → resize (if needed) → work → screenshot evidence → tab-close <index>
```

### Orchestrator's job
1. Bootstrap the session before Wave 1
2. Tell each agent which sibling agents share the session
3. Tell each agent their viewport/theme if doing a visual matrix
4. After all agents in a wave complete: review their screenshots before next wave
5. After all waves: `session-stop-all`

### Parallel screenshot matrix (dispatch 4 agents simultaneously)

| Agent | Viewport | Theme | Filename Convention |
|-------|----------|-------|---------------------|
| A | `resize 1280 720` | light (default) | `*-desktop-light.png` |
| B | `resize 1280 720` | dark (emulateMedia) | `*-desktop-dark.png` |
| C | `resize 375 812` | light (default) | `*-mobile-light.png` |
| D | `resize 375 812` | dark (emulateMedia) | `*-mobile-dark.png` |

### If an agent's tab goes wrong
- Lost track of tab: `tab-list` + `eval "() => window.location.href"`
- Session died: orchestrator re-runs bootstrap, agent creates a new tab
- Another agent's tab interfering: tabs are isolated. If it happens, it's a page-level side effect (shared cookies/localStorage)

## Orchestrator Checklist

### Before dispatch
- [ ] Playwright session bootstrapped
- [ ] Dev server running and responding
- [ ] Baseline screenshots captured (if doing before/after comparison)
- [ ] Each agent's brief includes Playwright rules block
- [ ] Each agent's DoD includes specific screenshot filenames to produce
- [ ] Verification level selected per task (Level 1-4)

### During execution
- [ ] Agents creating tabs (not sessions)
- [ ] Agents naming screenshots descriptively
- [ ] Agents reading their own screenshots and reporting observations

### After completion
- [ ] All agent screenshots reviewed by orchestrator
- [ ] Console errors checked on final state
- [ ] Network failures checked on final state
- [ ] Mobile + desktop verified
- [ ] Dark mode verified (if applicable)
- [ ] `session-stop-all` executed

## Verification Patterns (Building Blocks for Briefs)

### Page health check (run after every open)
```bash
open <url>
console error              # get file path → read it → check for JS errors
network                    # get file path → read it → check for 4xx/5xx
```

### Visual baseline capture
```bash
screenshot --full-page --filename=<context>-<viewport>-<theme>.png
# Agent reads the screenshot and states what they observe.
# This is evidence. Name it well.
```

### Soft 404 detection (SPAs return 200 for everything)
```bash
eval "() => document.title"
eval "() => document.querySelector('h1')?.textContent"
```

### Before/after comparison (regression detection)
```bash
# BEFORE changes (orchestrator or dedicated agent captures these):
screenshot --full-page --filename=BEFORE-desktop.png
screenshot --full-page --filename=BEFORE-mobile.png

# AFTER changes (implementation agent captures these):
screenshot --full-page --filename=AFTER-desktop.png
screenshot --full-page --filename=AFTER-mobile.png

# Agent reads both pairs and reports differences.
```
