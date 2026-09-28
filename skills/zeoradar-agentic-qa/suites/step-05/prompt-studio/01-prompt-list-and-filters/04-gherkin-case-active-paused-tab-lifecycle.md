# Test Case 04: Active vs Paused Tab Lifecycle & Offline Status Badges

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-04-TAB-LIFECYCLE`
- **Purpose**: Verify that the Prompt Designer Workbench strictly separates active generative prompts from paused/inactive prompts across `.designer-tabs`, ensuring that paused prompts render appropriate offline status badges (`.badge.dg-badge-off`), table counts partition cleanly, and tab state transitions occur without layout regressions.

---

## 2. Tester Brief
The tester will:
1. Open the Prompt Designer Workbench for `[DOMAIN]`.
2. Verify that the "Active" tab is selected by default (`.tab[data-t="active"].active`).
3. Verify that all displayed rows in the table are active (no `"Paused"` badges).
4. Click the "Paused" / "Inactive" tab (`.tab[data-t="inactive"]`).
5. Confirm that:
   - The inactive tab receives class `.active` and the active tab loses class `.active`.
   - The table renders strictly prompts whose `status === 'paused'`.
   - Every row displays a `.badge.dg-badge-off` with text `"Paused"` (or Turkish `"Duraklatıldı"`).
6. Switch back to "Active" and confirm that active prompts reappear.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Data**: Monitored project containing both active prompts and paused prompts.
- **Dynamic Elements**:
  - `span.tab[data-action="dg-tab"][data-t="active"]`
  - `span.tab[data-action="dg-tab"][data-t="inactive"]`
  - `span.badge.dg-badge-off`

---

## 4. Gherkin Scenario

```gherkin
Feature: Active vs Paused Prompt Lifecycle Tab Navigation

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @lifecycle @tabs
  Scenario: Active tab displays only active prompts without offline badges
    When the tester inspects the prompt tabs container ".designer-tabs"
    Then the tab with attribute "data-t='active'" should have class ".active"
    And no prompt row in "table.tbl.dg-tbl tbody" should contain the offline badge ".badge.dg-badge-off"
    And all rendered prompts should have status "active" in application state

  @lifecycle @tabs
  Scenario: Inactive tab displays exclusively paused prompts with offline badges
    When the tester clicks the tab "span.tab[data-t='inactive']"
    Then the inactive tab should receive class ".active"
    And the active tab should lose class ".active"
    And the prompt table "table.tbl.dg-tbl tbody" should update to show paused prompts
    And every visible row must display the badge ".badge.dg-badge-off" containing "Paused"
    When the tester clicks the tab "span.tab[data-t='active']"
    Then the active tab should regain class ".active"
    And the prompt table should restore the active prompts view
```

---

## 5. Visual Checks
1. **Tab Button Styling**: Active tab has distinct accent border or pill background (`.active`). Inactive tab has subtle muted styling.
2. **Offline Badges**: `.badge.dg-badge-off` renders with a muted neutral/grey background, subtle border, and text `"Paused"` or `"Duraklatıldı"`.
3. **Table Row Alignment**: Column widths and row heights remain stable when switching between Active and Inactive tabs.

---

## 6. Data and Network Checks
1. **State Consistency Assertion**:
   ```javascript
   const isInactiveTab = document.querySelector('.tab[data-t="inactive"]').classList.contains('active');
   const visibleRows = document.querySelectorAll('.dg-tbl tbody tr.dg-row');

   if (isInactiveTab) {
     visibleRows.forEach(row => {
       const badge = row.querySelector('.badge.dg-badge-off');
       assert.ok(badge !== null, 'Paused prompt row must display .badge.dg-badge-off');
       assert.ok(badge.textContent.includes('Paused') || badge.textContent.includes('Duraklatıldı'), 'Badge must indicate paused status');
     });
   }
   ```
2. **Tab State Persistence**: Verify `window.state.expanded['dg-tab']` matches the clicked tab name.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-active-paused-tab-lifecycle/`
- **Execution Model Notice**: Remote test execution runs via Ego Browser on macOS. Screenshots capturing active vs paused tabs are placed in `/tmp/shots/tab-lifecycle-[TAB].png` and retrieved via SCP.
- **Report Contents**:
  - `status.json`: Execution log and assertion status.
  - `screenshot-active-tab.png`: Table view in Active tab.
  - `screenshot-paused-tab.png`: Table view in Inactive/Paused tab.
