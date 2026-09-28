# Test Case: TC-OPP-02 - Status Tabs Navigation & Card Archival Lifecycle

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-02`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-03` (Status Tabs Switching) and `TC-OPP-07` (Card Archival & Restoration)
- **Purpose:** Validate that the Opportunities status tab bar (`active`, `archived`, `dismissed`) segregates backlog items accurately, maintains real-time item counts in each tab badge, moves an opportunity into archived state when clicking the Archive action, and enables instantaneous restoration back to the active working backlog via the Restore action without page reload or state corruption.

---

## 2. Tester Brief
The tester will verify the complete archival lifecycle of opportunities:
1. The three status tabs (`Active`, `Archived`, `Dismissed`) display correct dynamic counts in `.opps-status-count`.
2. Clicking a status tab applies `.active` class to the tab button and filters `.opps-list` cards accordingly.
3. On an active card, clicking `button.op-archive-btn` (`data-action="opp-archive"`) updates the opportunity's status to `"archived"`, immediately removes the card from the Active view, and increments the Archived counter.
4. Switching to the Archived tab displays the newly archived card with its archive status badge and a prominent Restore CTA (`button.op-restore-btn[data-action="opp-restore"]`).
5. Clicking "Restore" transitions the status back to `"active"`, removes it from the Archived tab, and returns it to the Active backlog.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** E.g. `op-outreach-1` or first available active card.
- **Matching Result Directory:** `02-gherkin-result-case-status-tabs-and-archival-lifecycle/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Status Tabs Segregation and Archival/Restoration State Transitions

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the active backlog contains at least 2 opportunity cards
    And the status tabs container ".opps-status-tabs" is visible

  Scenario Outline: Status Tab Switching and Count Synchronization
    When the user clicks the status tab with value "<TabValue>"
    Then the status tab button with data-val "<TabValue>" should have class "active"
    And all cards displayed in ".opps-list" should have state status "<ExpectedStatus>"
    And the count displayed in ".opps-status-count" on the tab should equal the number of rendered cards

    Examples:
      | TabValue  | ExpectedStatus |
      | active    | active         |
      | archived  | archived       |
      | dismissed | dismissed      |

  Scenario: Complete Card Archival and Restoration Cycle
    Given the user is viewing the "active" status tab
    And notes the active count as "N_active" and archived count as "N_archived"
    When the user clicks the Archive button "[data-action='opp-archive']" on card "[OPPORTUNITY_ID]"
    Then the card "[OPPORTUNITY_ID]" should be removed from the ".opps-list" container
    And the active tab count should decrease to "N_active - 1"
    And the archived tab count should increase to "N_archived + 1"
    
    When the user switches to the "archived" status tab
    Then the card "[OPPORTUNITY_ID]" should be present in the list
    And the card should display a Restore button "button.op-restore-btn" with data-action "opp-restore"
    
    When the user clicks the Restore button on card "[OPPORTUNITY_ID]"
    Then the card "[OPPORTUNITY_ID]" should disappear from the "archived" view
    And the archived count should decrement to "N_archived"
    
    When the user switches back to the "active" status tab
    Then the card "[OPPORTUNITY_ID]" should reappear in the active list
    And the active count should return to "N_active"
```

---

## 5. Visual Checks
1. **Tabs Container:** `.opps-status-tabs` renders with `role="tablist"` and border bottom.
2. **Active State Highlight:** The selected tab button has class `.active` with an accent underline or colored background pill.
3. **Count Chips:** Each tab contains `.opps-status-count` displaying a badge integer (e.g. `12`, `3`, `0`).
4. **Card Action Buttons in Different States:**
   - Active cards display: `Draft Brief` (`.op-draft-btn`), `Archive` (`.op-archive-btn`), `Dismiss` (`.op-dismiss-btn`).
   - Archived cards display: `Restore` (`.op-restore-btn`), and omitted or disabled draft buttons.
   - Dismissed cards display: Reason badge (`.op-dismiss-badge`), and `Restore` (`.op-restore-btn`).
5. **Smooth Transition:** Tab switching occurs instantly without flicker or unstyled flash of layout.

---

## 6. Data and Network Checks
1. **In-Memory State Mutation:**
   - Verify `window.state.opportunities.find(o => o.id === targetId).status` transitions from `"active"` to `"archived"` and back to `"active"`.
2. **Persistence Storage:**
   - Inspect `localStorage.getItem("zeo-radar-opps-" + projKey)`; ensure the updated status is persisted in the serialized JSON array.
3. **RPC Data Provider Synchronization:**
   - If connected to live Supabase backend, assert `ZEO_DATA_PROVIDER.callCommand("update-opportunity-status", { id: targetId, status: "archived" })` is dispatched and resolves with HTTP 200 / success.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `02-gherkin-result-case-status-tabs-and-archival-lifecycle/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `tabs_active.png` showing active backlog.
  2. Capture `card_archived.png` showing transition in the archived view with Restore CTA.
  3. Capture `card_restored.png` confirming return to active backlog.
  4. Transfer evidence from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-status/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/02-gherkin-result-case-status-tabs-and-archival-lifecycle/
     ```
  5. Log execution outcomes in `result.md`.

### Pass/Fail Criteria
- [ ] Status tab buttons correctly toggle active state and update DOM card list.
- [ ] Active tab count decreases by 1 and Archived tab count increases by 1 on archive click.
- [ ] Archived card displays Restore CTA and does not allow duplicate archival.
- [ ] Restored card returns to Active backlog with unchanged original metrics and score.
