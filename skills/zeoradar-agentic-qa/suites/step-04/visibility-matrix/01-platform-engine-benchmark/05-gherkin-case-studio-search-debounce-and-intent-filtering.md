# Test Case: TC-VIS-05 - Studio Search Debounce, Intent Filtering & Mini Engine Dots

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-05`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture)
- **Traceability:** Maps to Source Scenarios `VIS-08` and `VIS-09`
- **Purpose:** Verify that the Studio Master list (`.aei-studio-master.card`) filters prompts in real-time with a 150ms debounce upon typing into `#aeiStudioSearchInput`, filters prompt items by search intent chips (`all`, `info`, `comm`, `trans`, `nav`), accurately renders prompt outcome pills (`won`, `partial`, `lost`, `unmeasured`), displays mini engine indicator dots (`.aei-m-dots`), and updates the active selection in `aeiState.selectedPromptId` upon clicking a prompt item.

---

## 2. Tester Brief
The tester or automated agent interacts with the Studio left-hand master list:
1. Navigate to the Studio workspace (`?workspace=studio`).
2. Type a query string (e.g. `[PROMPT_QUERY]`, such as "klima" or "ısı pompası") into `#aeiStudioSearchInput` and assert:
   - Live filtering occurs after a 150ms debounce window.
   - Non-matching prompts are hidden; matching prompts are displayed.
   - Clearing the input restores the full prompt list.
3. Click an intent filter chip (e.g. `Commercial` or `Informational`) and verify:
   - The clicked chip gains `.active`.
   - `st.studioIntentFilter` updates to the target intent.
   - Rendered prompt items match the selected intent.
4. Verify prompt item anatomy:
   - `.aei-status-pill`: Shows outcome status (`won` for #1 rank, `partial` for mentions, `lost`, `unmeasured`).
   - `.aei-m-dots`: Shows 5 colored mini dots representing engine probe states.
5. Click a non-active prompt item and verify it gains `.active` and triggers detail pane re-rendering.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Search Query `[PROMPT_QUERY]`:** `[PROMPT_QUERY]`
- **Intent Filter `[INTENT_CATEGORY]`:** `all`, `info`, `comm`, `trans`, `nav`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `05-gherkin-result-case-studio-search-debounce-and-intent-filtering/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Studio Master List Live Search, Intent Filtering, and Prompt Selection

  Background:
    Given the user is on the "studio" workspace of Zeo Geo-Radar
    Then the master prompt pane ".aei-studio-master" should be visible

  Scenario: Live Search Input Debouncing and List Filtering
    When the user types "[PROMPT_QUERY]" into "#aeiStudioSearchInput"
    And the user waits 250 milliseconds for the 150ms debounce timer to fire
    Then the master list ".aei-master-list" should only display prompts matching "[PROMPT_QUERY]"
    When the user clears the search input "#aeiStudioSearchInput"
    And the user waits 250 milliseconds
    Then the master list should restore all visible prompt items

  Scenario Outline: Filtering Master List by Intent Chips
    When the user clicks the intent chip "button.aei-intent-chip[data-intent='<IntentKey>']"
    Then the clicked chip should have class "active"
    And all other intent chips should not have class "active"
    And "window.aeiState.studioIntentFilter" should equal "<IntentKey>"
    And all rendered prompt items should correspond to "<IntentKey>" intent or render empty notice if none match

    Examples:
      | IntentKey | IntentLabel (EN) | IntentLabel (TR) |
      | all       | All              | Tümü             |
      | info      | Informational    | Bilgi            |
      | comm      | Commercial       | Ticari           |
      | trans     | Transactional    | İşlem            |
      | nav       | Navigational     | Gezinme          |

  Scenario: Prompt Item Selection and Indicator Dot Anatomy
    Given the master list displays prompt items
    Then each ".aei-master-item" should contain:
      | Selector          | Purpose                                  |
      | .aei-status-pill  | Victory/retrieval status outcome         |
      | .aei-m-dots       | Mini engine status indicator dots (5 dots)|
      | .aei-m-row2       | Search volume count and metadata         |
    When the user clicks a prompt item with "data-pid='prompt_02'"
    Then the item should receive class "active"
    And "window.aeiState.selectedPromptId" should equal "prompt_02"
    And the right detail pane ".aei-studio-detail" should re-render for prompt "prompt_02"
```

---

## 5. Visual Checks
1. **Master Pane Layout:** `.aei-studio-master.card` takes up roughly 45% of the horizontal grid, containing a search bar, intent chips row, and scrollable list.
2. **Intent Chip Group:** Horizontal flex container with subtle pill buttons; active chip exhibits bold text and solid accent background.
3. **Mini Indicator Dots:** `.aei-m-dots` renders 5 circular 6px dots side-by-side with tooltips indicating engine names and outcome colors.
4. **Status Pill Colors:**
   - `won`: Green pill (`var(--green)`).
   - `partial`: Blue pill (`var(--blue)`).
   - `lost`: Red/amber pill (`var(--red)`).
   - `unmeasured`: Muted gray pill (`var(--ink-3)`).

---

## 6. Data and Network Checks
1. **Debounce Timer Check:**
   - Confirm input listener uses `debounce(..., 150)`.
   - Rapid keystrokes do not cause layout thrashing or stuttering.
2. **Intent Filter State:**
   ```js
   assert(window.aeiState.studioIntentFilter === "comm", "Intent filter must match clicked chip");
   ```
3. **Prompt Selection Sync:**
   - Confirm clicking updates `st.selectedPromptId` and triggers `syncUrlParams()`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `05-gherkin-result-case-studio-search-debounce-and-intent-filtering/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`studio_master_initial.png`, `debounced_search_filtered.png`, `intent_chip_active.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-05-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/05-gherkin-result-case-studio-search-debounce-and-intent-filtering/screenshots/
     ```
  4. Write execution report `result.md` verifying search counts, intent filtering, and prompt selection state.

### Pass/Fail Criteria
- [ ] Text search filters prompts with 150ms debounce.
- [ ] Intent chips filter prompts by intent category.
- [ ] Prompt items display status pills and 5 mini dots.
- [ ] Clicking a prompt item sets `st.selectedPromptId` and updates the detail pane.
