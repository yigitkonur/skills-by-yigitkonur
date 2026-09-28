# Test Case: TC-VIS-03 - Matrix Cell Drilldown to Studio Workspace & Filter Scoping

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-03`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture)
- **Traceability:** Maps to Source Scenarios `VIS-05`, `VIS-19`, and `VIS-20`
- **Purpose:** Verify that clicking any cell within the Multi-Engine Benchmark Matrix (`td.aei-matrix-cell[data-action="aei-matrix-drilldown"]`) triggers an instant seamless transition from the Performance workspace to the Prompts & Citations Studio workspace (`st.workspace = "studio"`), scopes the active engine filter strictly to the clicked cell's platform (`st.filters.engines = [targetEngine]`), synchronizes URL search parameters, and safely executes even when drilling down from cells with `0%` visibility or unmeasured (`"–"`) states without throwing JavaScript runtime exceptions.

---

## 2. Tester Brief
The tester or automated agent interacts with the benchmark matrix cells:
1. Identify a cell for a measured platform (e.g. `Perplexity` with score `75%`), click the cell, and verify:
   - Workspace transitions from `performance` to `studio`.
   - The Studio split-pane container (`.aei-studio-workspace`) mounts.
   - The global engine filter is scoped strictly to `perplexity`.
   - URL updates to `workspace=studio&engines=perplexity`.
2. Return to Performance, click a cell with `0%` visibility (lost probe), and verify:
   - Studio mounts cleanly.
   - Prompt items in the left pane show lost status (`.aei-status-pill.lost`).
   - Stage 1 synthesized answers in the right pane do not fabricate own brand mentions.
3. Return to Performance, click an unmeasured cell with `"–"`, and verify:
   - Studio mounts cleanly without console errors.
   - Appropriate empty state or unmeasured indicators render gracefully.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=performance`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Engine `[ENGINE_NAME]`:** `perplexity`, `chat_gpt`, `gemini`, `claude`, `aimode`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `03-gherkin-result-case-matrix-cell-drilldown-to-studio/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Multi-Engine Benchmark Matrix Drilldown to Studio Workspace

  Background:
    Given the user is on the "performance" workspace of Zeo Geo-Radar
    And the benchmark matrix "table.tbl.aei-matrix-tbl" is fully rendered

  Scenario Outline: Drilldown from Matrix Cell Scoping Engine Filter in Studio
    When the user clicks the matrix cell for "<EngineKey>" with score value "<ScoreStatus>"
    Then the system should update "window.aeiState.workspace" to "studio"
    And "window.aeiState.filters.engines" should equal ["<EngineKey>"]
    And the URL hash should contain "workspace=studio" and "engines=<EngineKey>"
    And the studio split container ".aei-studio-workspace" should mount within 5 seconds
    And the left pane ".aei-studio-master" should display prompts filtered for "<EngineKey>"
    And no uncaught JavaScript exceptions should appear in the browser log

    Examples:
      | EngineKey   | ScoreStatus | Description                          |
      | perplexity  | >0%         | Active platform with brand mentions  |
      | gemini      | 0%          | Active platform with lost visibility |
      | aimode      | –           | Unmeasured platform probe state      |

  Scenario: Studio Detail Pane State Consistency Post-Drilldown
    Given the user drilled down from a "gemini" cell with "0%" visibility
    When the studio detail pane ".aei-studio-detail" renders the selected prompt
    Then the active engine in the detail view should be "gemini"
    And Stage 1 answer inspector should not highlight own brand mentions
    And the prompt outcome pill in the master list should display "lost"
```

---

## 5. Visual Checks
1. **Workspace Tab Switch:** The top workspace pill tab transitions from `Performance & SOV` to `Prompts & Citations Studio` (`button.aei-tab[data-ws="studio"].active`).
2. **Global Filter Bar Sync:** The engine chip matching `[ENGINE_NAME]` remains active while others become inactive.
3. **Studio Master-Detail Layout:**
   - Left master pane (`.aei-studio-master.card`, 45% width).
   - Right detail pane (`.aei-studio-detail.card`, 55% width).
4. **Transition Smoothness:** No layout shifts, blank white screens, or flash of unstyled content during workspace rerender.

---

## 6. Data and Network Checks
1. **State Mutation Verification:**
   ```js
   assert(window.aeiState.workspace === "studio", "Workspace must be studio");
   assert(window.aeiState.filters.engines.length === 1, "Must contain exactly 1 scoped engine");
   assert(window.aeiState.filters.engines[0] === targetEngine, "Scoped engine must match clicked cell");
   ```
2. **History State Update:**
   - Check `window.history.state` or `window.location.hash` reflects `workspace=studio&engines=[targetEngine]`.
3. **Safe Memory Cleanup:** Verify previous Performance chart canvases are unmounted without memory leaks.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `03-gherkin-result-case-matrix-cell-drilldown-to-studio/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`drilldown_click_cell.png`, `studio_mounted_scoped_engine.png`, `zero_percent_drilldown_detail.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-03-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/03-gherkin-result-case-matrix-cell-drilldown-to-studio/screenshots/
     ```
  4. Write execution report `result.md` verifying state parameters, URL hash updates, and DOM nodes.

### Pass/Fail Criteria
- [ ] Matrix cell click transitions workspace to `studio`.
- [ ] Engine filter is scoped exclusively to the clicked cell's platform.
- [ ] URL parameters synchronize accurately.
- [ ] Clicking `0%` and `"–"` cells executes cleanly with zero runtime exceptions.
