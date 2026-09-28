# Test Case: TC-VIS-01 - Navigation URL Sync, Default Workspace Boot & Engine Toggle Lock

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-01`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture)
- **Traceability:** Maps to Source Scenarios `VIS-01`, `VIS-02`, and `VIS-03`
- **Purpose:** Verify that navigating to `/#/app/:slug/visibility` without query parameters initializes `aeiState` to default values (`workspace = "performance"`, all 5 engines active, `time = "30d"`, `region = "all"`), reflects active engine chip UI states, synchronizes URL search parameters cleanly upon user interactions via `history.replaceState`, and enforces the engine deselection lock preventing the user from deselecting all active engines.

---

## 2. Tester Brief
The tester or AI execution agent validates the initialization lifecycle of the AEI module:
1. Upon initial load without parameters, the application selects the Performance workspace tab (`.aei-tab[data-ws="performance"]`), highlights all 5 engine chips (`.aei-engine-chip.active`), and leaves the URL clean or synchronized.
2. Clicking an active engine chip (e.g. `chat_gpt`) toggles its active status off, removes the `.active` class, updates `st.filters.engines`, and serializes the remaining engines into the URL search parameters (`?engines=perplexity,gemini,claude,aimode`).
3. If the user attempts to toggle off the last remaining active engine chip, the system intercepts the click, retains the engine in `st.filters.engines`, keeps the `.active` class, and prevents an empty state that would corrupt matrix calculations.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility` (or active live tunnel URL)
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `all` (or `TR`, `US`)
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Engine Filter `[ENGINE_NAME]`:** `chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode`
- **Matching Result Directory:** `01-gherkin-result-case-navigation-url-sync-and-initial-boot/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: AEI Workspace Boot, URL Synchronization, and Engine Deselection Guardrail

  Background:
    Given the user is authenticated in Zeo Geo-Radar
    And the current brand project is "[DOMAIN]"
    When the user navigates to "/#/app/[SLUG]/visibility" without search parameters
    Then the root page container ".aei-page" should mount within 10 seconds

  Scenario: Default Workspace and Global Filter Initialization
    Then the global state "window.aeiState.workspace" should equal "performance"
    And the performance tab button "button.aei-tab[data-ws='performance']" should have class "active"
    And the persistent filter bar ".aei-global-bar" should display 5 active engine chips
    And the time filter select "select[data-action-change='aei-select-time']" should have value "30d"
    And the region filter select "select[data-action-change='aei-select-region']" should have value "all"

  Scenario Outline: Toggling Engine Inclusion and URL Parameter Serialization
    Given all 5 AI engines are currently selected in the filter bar
    When the user clicks the engine chip "button.aei-engine-chip[data-engine='<EngineKey>']"
    Then the chip should lose class "active"
    And "window.aeiState.filters.engines" should not contain "<EngineKey>"
    And the browser URL search query should match "<ExpectedUrlParam>"
    When the user clicks the engine chip "button.aei-engine-chip[data-engine='<EngineKey>']" again
    Then the chip should regain class "active"
    And "window.aeiState.filters.engines" should contain "<EngineKey>"

    Examples:
      | EngineKey   | ExpectedUrlParam                                          |
      | chat_gpt    | engines=perplexity,gemini,claude,aimode                   |
      | perplexity  | engines=chat_gpt,gemini,claude,aimode                     |
      | gemini      | engines=chat_gpt,perplexity,claude,aimode                 |
      | claude      | engines=chat_gpt,perplexity,gemini,aimode                 |
      | aimode      | engines=chat_gpt,perplexity,gemini,claude                 |

  Scenario: Single Remaining Engine Deselection Lock
    Given only 1 engine chip "button.aei-engine-chip[data-engine='chat_gpt']" is active
    When the user clicks the engine chip "button.aei-engine-chip[data-engine='chat_gpt']"
    Then the chip should remain with class "active"
    And "window.aeiState.filters.engines" should strictly retain "chat_gpt"
    And the length of "window.aeiState.filters.engines" must equal 1
    And no JavaScript errors should be thrown in the developer console
```

---

## 5. Visual Checks
1. **Header Filter Bar Layout:** `.aei-global-bar.card` is sticky at top, containing `.aei-bar-brand`, `.aei-engine-chips`, and select dropdowns.
2. **Engine Chip Styling:**
   - Active chips have `.aei-engine-chip.active` with colored dot (`.sw`) matching platform palette.
   - Inactive chips lose `.active`, displaying opacity `0.55` and grayscale/subdued styling.
3. **Workspace Tab Navigation:** `.aei-tabs` renders 3 pill tabs (`performance`, `studio`, `perception`), with `performance` exhibiting the active bottom indicator or background fill.

---

## 6. Data and Network Checks
1. **State Evaluation:**
   ```js
   var st = window.aeiState;
   assert(st.workspace === "performance", "Default workspace must be performance");
   assert(Array.isArray(st.filters.engines) && st.filters.engines.length >= 1, "Engines must never be empty");
   ```
2. **URL Search Parameter Parsing:**
   - Confirm `window.location.hash` contains `?engines=...` when engines are toggled.
   - Confirm refreshing the page with `?workspace=performance&engines=chat_gpt` restores the single engine selection without resetting to 5.
3. **No Network Refetch Thrashing:** Toggling engine chips updates client-side filtering without issuing redundant HTTP requests.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `01-gherkin-result-case-navigation-url-sync-and-initial-boot/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`initial_boot.png`, `chip_toggled_off.png`, `deselection_lock_blocked.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-01-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/01-gherkin-result-case-navigation-url-sync-and-initial-boot/screenshots/
     ```
  4. Write execution report `result.md` verifying state parameters and test assertions.

### Pass/Fail Criteria
- [ ] Initial state defaults to `workspace: "performance"` and 5 active engines.
- [ ] Clicking an active chip removes it from `st.filters.engines` and syncs URL.
- [ ] Attempting to deselect the last remaining engine is blocked; at least 1 engine remains active.
- [ ] Reloading with deep-link query parameters restores specified filter state.
