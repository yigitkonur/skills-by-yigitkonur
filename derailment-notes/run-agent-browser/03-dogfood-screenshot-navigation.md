# Derailment Test: run-agent-browser on "Screenshot + GitHub Trending Navigation"

Date: 2026-03-11
Skill under test: run-agent-browser
Test task: Navigate to github.com/trending, take a screenshot, extract top 5 repo names, click through to a repo, navigate back, verify page state.
Method: Follow SKILL.md steps 1–6 exactly as written, recording every friction point.

---

## Pre-scan summary

Same as run 01/02. This run tests the navigation + screenshot + data extraction path.
Focused on: how the skill handles complex page structures, screenshot commands, and back-navigation.

---

## Friction points

### Phase 1–2: Establish session and navigate

Clean pass. `open URL` and verify cycle worked perfectly.

### Phase 3: Inspect — data extraction from complex page

**F-01 — `snapshot -i` fails to surface GitHub's custom dropdown filters** (P1, M4)
GitHub trending has "Spoken Language", "Language", and "Date range" filter dropdowns. None appeared in `snapshot -i` output (110 elements, all links/buttons for repos and nav). The dropdowns are custom components that require a click to become interactive. SKILL.md says "If refs are scarce, try snapshot (full DOM)" but doesn't explain how to discover hidden UI components that only appear after an interaction.
Fix: Add to SKILL.md §3: "Some pages use custom components (dropdown menus, popovers, accordions) whose child elements only appear in snapshot after clicking the trigger. If expected UI elements are missing: click the likely trigger → re-snapshot → verify new elements appeared."

**F-02 — Recurring: flat snapshot makes repo identification ambiguous** (P1, M4)
Same as run 01 F-03. Repo links like `link "msitarzewski / agency-agents" [ref=e23]` are mixed with star counts (`link "star 29,644"`), fork counts, and contributor avatars. An executor unfamiliar with GitHub's DOM would struggle to identify which refs are repo names vs. metadata. The skill provides no strategy for this common pattern.
Fix: Same as run 01 F-03 — document eval-based extraction pattern.

### Phase 4: Interact — navigation

**F-03 — `back` command not mentioned in SKILL.md** (P1, M5)
After clicking into a repo page, the executor needs to return to the trending page. SKILL.md only mentions `open URL`, `tab new URL`, and `tab INDEX` for navigation. The `back` command exists in commands.md but is never mentioned or hinted at in SKILL.md. The executor guessed `go back` (failed) before trying `back` (succeeded). For a literal-following test, this is a clear gap.
Fix: Add to SKILL.md §4 navigation tools or §3: "Use `agent-browser back` to return to the previous page (browser back button equivalent). Prefer `back` over re-navigating with `open URL` when you need to preserve form state or scroll position."

### Phase 5: Verify + Screenshot

**F-04 — Screenshot command not mentioned in SKILL.md workflow** (P2, M4)
`agent-browser screenshot PATH` works perfectly but is never mentioned in SKILL.md. It's only in commands.md. For tasks that need visual verification or archival, the skill provides no guidance on when/how to use screenshots.
Fix: Add brief mention to SKILL.md §5 verification section: "For visual verification or archival: `agent-browser screenshot /tmp/descriptive-name.png`."

---

## What worked well

1. **Screenshot command is clean and intuitive.** `screenshot /tmp/file.png` → `✓ Screenshot saved to /tmp/file.png`. Zero friction in the command itself.

2. **`back` command works exactly like a browser back button.** Clean, fast, preserves page state. Once discovered, it's great.

3. **`click REF` navigation between pages was reliable.** Clicking `@e23` (repo link) navigated correctly, and the full page title confirmed we landed on the right repo.

4. **`eval` heredoc pattern continued to work perfectly** for extracting structured data from complex pages.

5. **GitHub's trending page loaded without auth barriers.** No CAPTCHAs, no login walls — the page was fully accessible to the browser automation.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | — |
| P1 | 3 | F-01, F-02, F-03 |
| P2 | 1 | F-04 |

## Metrics

| Metric | Value |
|---|---|
| Total steps attempted | 12 |
| Clean passes | 8 |
| P0 (blocks progress) | 0 |
| P1 (causes confusion) | 3 |
| P2 (minor annoyance) | 1 |
| Derailment density | 0.33 |
| Clean pass rate | 67% |

## Cross-run comparison

| Run | Date | Task | Steps | P0 | P1 | P2 | Total | Density | Clean % |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 2026-03-11 | HN data extraction + search | 19 | 1 | 6 | 1 | 8 | 0.42 | 58% |
| 02 | 2026-03-11 | Multi-tab form filling | 16 | 0 | 2 | 3 | 5 | 0.31 | 69% |
| 03 | 2026-03-11 | Screenshot + GH trending nav | 12 | 0 | 3 | 1 | 4 | 0.33 | 67% |

**Trajectory:** Consistent. Form-filling (run 02) is the cleanest path. Data extraction (run 01, 03) consistently surfaces more friction. The skill is well-optimized for interactive element manipulation but needs better guidance for read-only data extraction and hidden UI discovery.
