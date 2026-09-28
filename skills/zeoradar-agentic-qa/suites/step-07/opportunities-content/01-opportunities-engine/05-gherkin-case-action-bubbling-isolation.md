# Test Case: TC-OPP-05 - Multi-Action Event Bubbling Isolation & Detail View Protection

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-05`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-08` (Card Click vs Card Action Event Bubbling) and `TC-OPP-15` (Multi-Action Button Bubbling Isolation under High-Velocity Clicks)
- **Purpose:** Rigorously verify the event bubbling isolation contract across opportunity cards (`.op-card`). The card root element has `data-action="opp-select-detail"`, but any click originating inside the action button container (`.op-card-actions`), its child buttons (`.op-draft-btn`, `.op-archive-btn`, `.op-dismiss-btn`, `.op-restore-btn`), the dismiss popover (`.opp-dismiss-pop`), action container margins/padding, or external entity link tags (`a.op-entity-tag`) MUST be isolated and NEVER trigger card detail selection or view transition.

---

## 2. Tester Brief
This is a critical UX regression guard test. In early builds, clicking "Archive", "Draft Brief", or opening the Dismiss menu inadvertently triggered the card's root click handler (`opp-select-detail`), causing an unwanted transition into the full-page Opportunity Detail View.
In `assets/opportunities.js`, the isolation is enforced at two levels:
1. `ev.target.closest(".op-card-actions")` check in `opp-select-detail` event delegation:
   ```js
   if (act === "opp-select-detail") {
     if (ev.target.closest(".op-card-actions")) return;
     // ...
   }
   ```
2. Inline `onclick="event.stopPropagation();"` on `a.op-entity-tag`.

The tester or automated agent will click each action element inside an opportunity card and assert that the application strictly remains in list view (`cfg.viewMode === "list"`), never mounting `.opp-detail-container`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** Active card in `.opps-list`
- **Matching Result Directory:** `05-gherkin-result-case-action-bubbling-isolation/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Event Bubbling Isolation on Opportunity Card Actions

  Background:
    Given the user is viewing the Opportunities backlog for "[DOMAIN]"
    And the application view mode is "list"
    And ".opp-detail-container" is not present in the DOM
    And at least 2 opportunity cards ".op-card" are rendered

  Scenario Outline: Action Button Clicks Must Not Trigger Detail View Transition
    When the user clicks the element "<ActionElementSelector>" inside card "[OPPORTUNITY_ID]"
    Then the action corresponding to "<ActionElementSelector>" should execute
    And the application view mode "window.state.oppsConfig.viewMode" should remain "list"
    And the container ".opp-detail-container" should NOT be mounted in the DOM
    And the opportunity list ".opps-list" should remain visible in the viewport

    Examples:
      | ActionElementSelector                                  |
      | .op-archive-btn                                        |
      | .op-dismiss-btn                                        |
      | .opp-dismiss-pop                                       |
      | .op-card-actions                                       |
      | a.op-entity-tag                                        |

  Scenario: Card Body Click Opens Detail View
    When the user clicks the neutral card body ".op-card-title" of card "[OPPORTUNITY_ID]"
    Then the application view mode should transition to "detail"
    And the container ".opp-detail-container" should be mounted in the DOM
    And the detail view title should match card "[OPPORTUNITY_ID]" title
    And the list container ".opps-list" should be hidden or replaced
```

---

## 5. Visual Checks
1. **Card Action Region:** `.op-card-actions` is positioned in `.op-card-footer` on the right side.
2. **Dismiss Menu Popover:** `.opp-dismiss-pop` renders floating above/below the dismiss button without expanding the card container or shifting layout.
3. **Cursor Pointer vs Default:**
   - Card body displays pointer cursor indicating clickable detail view.
   - Action buttons display button interaction states (hover background, active press).
4. **No Unexpected View Flash:** Clicking an action button must not momentarily flash the detail view before rendering toast or popovers.

---

## 6. Data and Network Checks
1. **View Mode State:**
   - Inspect `window.state.oppsConfig.viewMode`. Must strictly equal `"list"` after clicking any action button or child element of `.op-card-actions`.
2. **DOM Assertions:**
   ```js
   const inDetail = !!document.querySelector('.opp-detail-container');
   console.assert(!inDetail, "REGRESSION: Detail view container mounted after action click!");
   ```
3. **Entity Tag Link Isolation:**
   - Clicking `a.op-entity-tag` (e.g. reddit thread link or external publisher) opens link in new tab or handles navigation without changing local SPA route to detail.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `05-gherkin-result-case-action-bubbling-isolation/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `action_click_archive_remains_list.png` proving no detail view transition on archive.
  2. Capture `action_click_dismiss_popover_open.png` showing popover opened in list view.
  3. Capture `card_body_click_detail_mounted.png` proving detail view only opens on card body click.
  4. Transfer evidence from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-bubbling/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/05-gherkin-result-case-action-bubbling-isolation/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Clicks on `.op-archive-btn` never mount `.opp-detail-container`.
- [ ] Clicks on `.op-dismiss-btn` open popover without triggering detail view.
- [ ] Clicks on padding/empty space within `.op-card-actions` do not trigger detail view.
- [ ] Clicks on `.op-card-title` or neutral card background cleanly transition to detail view.
