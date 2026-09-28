# Test Case: TC-OPP-07 - Opportunity Detail View Navigation, Stepper & Safe Fallback

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-07`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-09` (Detail View Navigation & Arrow Stepping) and `TC-OPP-20` (Safe Detail Navigation with Null / Out-of-Bounds Opportunity ID)
- **Purpose:** Test navigating into the Opportunity Detail View (`.opp-detail-container`), stepping sequentially forward and backward through the backlog using counter navigation arrows, returning to the list view via the back button, and ensuring safe fallback handling when navigating with an invalid, deleted, or out-of-bounds opportunity ID.

---

## 2. Tester Brief
The tester will verify the full detail view navigation lifecycle:
1. Clicking an opportunity card body transitions `cfg.viewMode` to `"detail"` and mounts `.opp-detail-container`.
2. The header displays an item counter (e.g. `1 / 8`) and navigation arrows: `button.opp-counter-btn[data-action="opp-nav-prev"]` and `button.opp-counter-btn[data-action="opp-nav-next"]`.
3. Clicking the Next arrow transitions to item `2 / 8`, updating the title, action banner, checklist, and references to match the next opportunity.
4. Clicking the Previous arrow returns to item `1 / 8`.
5. Clicking the Back button (`button.opp-back-btn[data-action="opp-back-list"]`) unmounts the detail container and returns to the full backlog list view without state loss.
6. **Boundary Resilience:** If `cfg.selectedId` is forced to a non-existent or deleted ID (`op-non-existent-999`), the engine safely defaults to `allOpps[0]` or reverts to `"list"` view without throwing an uncaught exception.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Backlog Items Count:** At least 3 active opportunities
- **Matching Result Directory:** `07-gherkin-result-case-detail-view-navigation-and-stepper/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Opportunity Detail View Stepper Navigation and Out-of-Bounds Error Handling

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the backlog contains "N" active opportunities where N >= 3
    When the user clicks the card body of the first opportunity in ".opps-list"
    Then the view mode should transition to "detail"
    And the container ".opp-detail-container" should be mounted in the viewport

  Scenario: Sequential Stepping via Next and Previous Arrows
    Given the detail view is displaying item "1 / N"
    When the user clicks the Next arrow "button.opp-counter-btn[data-action='opp-nav-next']"
    Then the counter text ".opp-counter-text" should update to "2 / N"
    And the detail view title ".opp-detail-title" should update to the title of the second opportunity
    
    When the user clicks the Previous arrow "button.opp-counter-btn[data-action='opp-nav-prev']"
    Then the counter text ".opp-counter-text" should return to "1 / N"
    And the detail view title should match the first opportunity again
    
    When the user clicks the Back button "button.opp-back-btn"
    Then the detail view should be unmounted
    And the list container ".opps-list" should be visible with all original cards intact

  Scenario: Safe Boundary Fallback for Out-of-Bounds or Null Opportunity ID
    Given the user attempts to view a non-existent opportunity ID "op-invalid-99999"
    When the application renders the detail view with the invalid ID
    Then the engine should safely fall back to the first available opportunity without throwing an error
    And ".opp-detail-container" should render with valid data from "allOpps[0]"
    Or gracefully revert to view mode "list"
```

---

## 5. Visual Checks
1. **Detail Header:**
   - Left side: Back button with left arrow icon and text `"All Opportunities"` / `"Tüm Fırsatlar"`.
   - Center/Right: Counter navigation containing `[ < ]`, `1 / N`, `[ > ]`.
2. **Action Banner:** Distinct colored callout box `.opp-action-banner` displaying the primary recommendation based on category (Outreach, Forum, Content).
3. **Accordions Present:** Detail view contains 3 accordion cards:
   - Implementation Guide (`implementation`)
   - Strategic Rationale (`rationale`)
   - Citation References (`references`)
4. **Disabled Stepper State:** At item `1 / N`, the Prev arrow is disabled or wraps around according to configuration; at item `N / N`, the Next arrow is disabled or wraps around.

---

## 6. Data and Network Checks
1. **State Synchronization:**
   - Inspect `window.state.oppsConfig.viewMode` (equals `"detail"` in detail view, `"list"` after clicking back).
   - Inspect `window.state.oppsConfig.selectedId` (tracks currently active opportunity ID).
2. **Crash-Free Evaluation:**
   ```js
   try {
     window.state.oppsConfig.selectedId = "op-bogus-uuid";
     window.state.oppsConfig.viewMode = "detail";
     if (typeof window.renderOpportunitiesPage === 'function') {
       window.renderOpportunitiesPage();
     }
   } catch (err) {
     console.error("CRASH: Detail view threw on invalid ID", err);
   }
   ```
   Assert zero console errors thrown.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `07-gherkin-result-case-detail-view-navigation-and-stepper/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `detail_view_item_1.png` showing detail header and counter `1 / N`.
  2. Capture `detail_view_item_2.png` showing transition to item `2 / N`.
  3. Capture `back_to_list.png` showing clean return to list view.
  4. Capture `invalid_id_fallback.png` confirming crash-free fallback handling.
  5. Transfer screenshots:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-detail/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/07-gherkin-result-case-detail-view-navigation-and-stepper/
     ```
  6. Document verification summary in `result.md`.

### Pass/Fail Criteria
- [ ] Detail view mounts cleanly upon clicking card body.
- [ ] Next and Previous counter buttons update title and accordions in lockstep.
- [ ] Back button returns to list view without resetting filters or active tab.
- [ ] Invalid or out-of-bounds opportunity ID gracefully falls back without throwing errors.
