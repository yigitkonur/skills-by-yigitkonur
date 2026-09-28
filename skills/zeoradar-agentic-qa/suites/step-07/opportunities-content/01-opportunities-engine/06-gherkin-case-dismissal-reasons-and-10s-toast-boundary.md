# Test Case: TC-OPP-06 - Dismissal Reasons & 10-Second Toast Expiration Boundary

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-06`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-06` (Dismissal with Reason & Toast Undo) and `TC-OPP-16` (Dismissal Toast 10s Expiration Boundary: 9.5s Valid vs 10.5s Expired)
- **Purpose:** Validate that dismissing an opportunity requires choosing one of three standard strategic reasons (`out_of_scope`, `already_completed`, `irrelevant`), updates the card status and metadata, mounts a temporary toast notification with an "Undo" action, and rigorously respects the 10-second expiration lifecycle boundary: at $t = 9.5\text{s}$ the undo button remains valid and functional; after $t = 10.5\text{s}$ the toast is permanently settled, the undo action is destroyed, and the card remains immutably dismissed.

---

## 2. Tester Brief
The tester will verify both the functional dismissal workflow and the precise temporal boundary of the undo toast:
1. Clicking `.op-dismiss-btn` toggles the `.opp-dismiss-pop` popover containing 3 reasons:
   - `Out of scope` (`out_of_scope`)
   - `Already completed` (`already_completed`)
   - `Irrelevant` (`irrelevant`)
2. Clicking a reason marks the opportunity as `dismissed`, stores `dismissReason` and `dismissedAt`, removes it from the Active list, and triggers a toast with `duration: 10000`.
3. **Temporal Boundary Condition:**
   - **At $t = 9.5\text{s}$ ($< 10\text{s}$):** Toast element `.toast` remains mounted with `.show` class, and `button.toast-action[data-action="opp-undo"]` is active. Clicking it cancels dismissal and restores the card.
   - **At $t = 10.5\text{s}$ ($> 10\text{s}$):** Toast timer expires, `settleToast()` runs, `.show` is removed, and the Undo button is unmounted from DOM. The card remains safely in the Dismissed tab.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** E.g. `op-reddit-1`
- **Matching Result Directory:** `06-gherkin-result-case-dismissal-reasons-and-10s-toast-boundary/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Opportunity Dismissal Reasons and 10-Second Undo Expiration Boundary

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the active backlog contains card "[OPPORTUNITY_ID]"
    When the user clicks the dismiss button ".op-dismiss-btn" on card "[OPPORTUNITY_ID]"
    Then the dismiss reasons popover ".opp-dismiss-pop" should be displayed

  Scenario Outline: Dismissing Opportunity with Valid Strategic Reason
    When the user selects dismissal reason "<ReasonCode>" from the popover
    Then the card "[OPPORTUNITY_ID]" should be removed from the active backlog
    And the active count should decrease by 1
    And the dismissed count should increase by 1
    And a toast notification with class ".toast.show" should appear
    And the toast should contain an Undo button "button[data-action='opp-undo']"

    Examples:
      | ReasonCode        | LabelEn           | LabelTr           |
      | out_of_scope      | Out of scope      | Kapsam dışı       |
      | already_completed | Already completed | Zaten tamamlandı  |
      | irrelevant        | Irrelevant        | İlgisiz           |

  Scenario: Toast Expiration Boundary: Valid at 9.5s, Permanently Expired at 10.5s
    Given the user dismisses card "[OPPORTUNITY_ID]" with reason "already_completed"
    Then the dismissal toast should be immediately mounted with class ".toast.show"
    
    # Boundary Test Point 1: 9.5 Seconds Elapsed
    When the test executor waits 9.0 seconds (total elapsed time 9.5 seconds)
    Then the toast element ".toast" must still contain class ".show"
    And the Undo button "button[data-action='opp-undo']" must still exist in the DOM
    
    # Boundary Test Point 2: 10.5+ Seconds Elapsed
    When the test executor waits an additional 1.5 seconds (total elapsed time 11.0 seconds)
    Then the toast element ".toast" must not have class ".show"
    And the Undo button "button[data-action='opp-undo']" must be removed or destroyed
    And the opportunity "[OPPORTUNITY_ID]" must remain in dismissed status
```

---

## 5. Visual Checks
1. **Dismiss Popover:** `.opp-dismiss-pop` renders with border, shadow, and 3 clickable rows (`.opt`).
2. **Toast Mount:**
   - Toast displays dismiss confirmation message: `"Opportunity dismissed"` / `"Fırsat gizlendi"`.
   - Right side of toast houses action button: `<button class="toast-action" data-action="opp-undo">Undo / Geri Al</button>`.
3. **Toast Expiration:** After 10s, toast smoothly transitions out (opacity fades to 0) and is removed from the DOM.
4. **Dismissed Tab Appearance:**
   - The card in the Dismissed tab displays a gray/amber badge `.op-dismiss-badge` showing the chosen reason.

---

## 6. Data and Network Checks
1. **State Mutation:**
   ```js
   const op = window.state.opportunities.find(o => o.id === targetId);
   console.assert(op.status === "dismissed", "Status not set to dismissed");
   console.assert(op.dismissReason === "already_completed", "Dismiss reason missing");
   console.assert(typeof op.dismissedAt === "number", "Timestamp dismissedAt missing");
   ```
2. **Undo Action:**
   - If Undo is clicked before 10s: `window.state._lastDismissedOpp` is restored, `op.status` returns to `"active"`, and `op.dismissReason` is cleared.
3. **LocalStorage Sync:**
   - Inspect `localStorage.getItem("zeo-radar-opps-" + projKey)`; ensure dismissal reason and timestamp are saved in local storage.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `06-gherkin-result-case-dismissal-reasons-and-10s-toast-boundary/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `dismiss_menu.png` showing the 3 reason choices.
  2. Capture `toast_at_9_5s.png` proving toast is visible and undo button exists at 9.5s.
  3. Capture `toast_expired_at_11s.png` proving toast is gone at 11s.
  4. Capture `dismissed_tab_card.png` showing the card in Dismissed tab with its reason badge.
  5. Transfer screenshots:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-dismiss/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/06-gherkin-result-case-dismissal-reasons-and-10s-toast-boundary/
     ```
  6. Document verification report in `result.md`.

### Pass/Fail Criteria
- [ ] Popover renders all 3 strategic reasons without truncating text.
- [ ] Toast is displayed with Undo button immediately upon selecting a reason.
- [ ] At 9.5s, the toast is still visible and the Undo button successfully restores the card.
- [ ] At 10.5s+, the toast is expired, the Undo button is gone, and the card remains dismissed.
