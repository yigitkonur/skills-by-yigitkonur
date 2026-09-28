# TC-BH-06: Brand Fact Archiving Lifecycle (Cancel vs Permanent Confirmation)

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-06`
- **Purpose:** Verify the two-stage permanent archiving workflow for brand facts: clicking Archive prompts a confirmation modal (`role="alertdialog"`). Cancelling preserves the active fact state. Confirming dispatches a permanent archive mutation, removes the fact from active views, excludes it from mutation controls, and makes it accessible solely in terminal read-only status under the `archived` filter.
- **Target Result Directory:** `01-brand-hub-ground-truth/06-gherkin-result-case-fact-permanent-archiving/`

---

## 2. Tester Brief
Archived facts cannot be re-activated, edited, or re-verified. Therefore, archiving requires explicit confirmation and cannot be triggered by an accidental click.
1. The user clicks `button[data-action="bh-prompt-archive"]`.
2. A modal dialog `.bh-confirm-modal[role="alertdialog"]` opens with a preview of the fact statement and a warning that archiving is irreversible.
3. Subcase A: Clicking Cancel (`[data-action="bh-close-drawer"]`) dismisses the modal without altering fact state.
4. Subcase B: Clicking `button[data-action="bh-confirm-archive"]` dispatches `update-brand-hub` with `archived: true`.
5. Post-confirmation:
   - Fact disappears from the active facts filter (`data-filter="all"`).
   - Switching to `data-filter="archived"` displays the archived card with `.bh-status-pill.archived`.
   - The archived card has ZERO action buttons in `.bh-fact-head`.
6. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb` -> Subtab `facts`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[FACT_ID]`: `fact_to_archive_01`
  - `[FACT_KEY]`: `deprecated_office_location`

---

## 4. Gherkin Scenario

```gherkin
Feature: Fact Permanent Archiving Lifecycle

  Scenario Outline: Archiving confirmation dialog handling and terminal read-only enforcement
    Given the test user is an owner inspecting an active fact "<FactKey>"
    When the user clicks the archive button "button[data-action='bh-prompt-archive']"
    Then the confirmation modal ".bh-confirm-modal" should be displayed
    When the user performs the confirmation action "<DialogAction>"
    Then the fact should reflect the expected status "<ExpectedOutcome>"
    And the fact should be visible in filter "<VisibleFilter>"
    And mutation buttons should be "<ActionButtonsState>"

    Examples:
      | FactKey                     | DialogAction    | ExpectedOutcome      | VisibleFilter | ActionButtonsState |
      | deprecated_office_location  | cancel          | remains active       | all           | enabled            |
      | deprecated_office_location  | confirm-archive | permanently archived | archived      | disabled/absent    |
```

---

## 5. Visual Checks
- **Modal Elements:**
  - Modal: `.bh-confirm-modal.card[role="alertdialog"]`.
  - Preview Box: `.bh-confirm-fact-preview`.
  - Action Buttons: `button.btn.danger[data-action="bh-confirm-archive"]` and `button.btn[data-action="bh-close-drawer"]`.
- **Card Elements Post-Archive:**
  - Status Pill: `.bh-status-pill.archived` (gray neutral styling).
  - Fact Head: `.bh-fact-head button` count must equal 0.
- **Screenshot Points:**
  - `01_archive_confirm_modal.png` (Confirmation alertdialog open).
  - `02_archived_facts_filter.png` (Archived facts view with disabled controls).

---

## 6. Data and Network Checks
- **Command RPC:**
  - Command: `update-brand-hub`.
  - Payload:
    ```json
    {
      "projectId": "[PROJECT_ID]",
      "expectedVersion": 1,
      "facts": [{
        "id": "fact_to_archive_01",
        "factKey": "deprecated_office_location",
        "archived": true
      }]
    }
    ```
- **State Assertion:**
  - Fact object contains non-null `archivedAt: "2026-09-25T..."`.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/06-gherkin-result-case-fact-permanent-archiving/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-archive');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

await click('.brand-hub-tab-btn[data-tab="facts"]');
await wait(1);

// Step 1: Open archive prompt
const target = await js(String.raw`(() => {
  const bhs = window.state.brandHub;
  if (!bhs || !bhs.data.facts.length) return null;
  const f = bhs.data.facts[0];
  const btn = document.querySelector('button[data-action="bh-prompt-archive"][data-fact-id="' + f.id + '"]');
  if (btn) btn.click();
  return { id: f.id, key: f.factKey };
})()`);

await wait(1);

// Step 2: Cancel check
await click('.bh-confirm-modal button[data-action="bh-close-drawer"]');
await wait(1);

// Step 3: Re-open and confirm
await js(String.raw`(() => {
  const btn = document.querySelector('button[data-action="bh-prompt-archive"][data-fact-id="${target.id}"]');
  if (btn) btn.click();
})()`);
await wait(1);

// Intercept command to return archived success
await js(String.raw`(() => {
  const orig = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = function (cmd, payload) {
    if (cmd === 'update-brand-hub') {
      window.ZEO_DATA_PROVIDER.callCommand = orig;
      const bhs = window.state.brandHub;
      bhs.data.facts = bhs.data.facts.map(f => f.id === payload.facts[0].id ? Object.assign({}, f, { archivedAt: new Date().toISOString() }) : f);
      return Promise.resolve({ ok: true, data: { brandHub: bhs.data } });
    }
    return orig.apply(this, arguments);
  };
  const confBtn = document.querySelector('button[data-action="bh-confirm-archive"]');
  if (confBtn) confBtn.click();
})()`);

await wait(2);

// Check filter archived
await click('span.fchip[data-filter="archived"]');
await wait(1);

const archiveState = await js(String.raw`(() => {
  const cards = Array.from(document.querySelectorAll('.bh-fact-card'));
  const found = cards.find(c => c.innerText.includes('${target.key}'));
  const btns = found ? found.querySelectorAll('.bh-fact-head button').length : -1;
  return {
    foundInArchived: !!found,
    actionButtonsCount: btns
  };
})()`);

cliLog('Archive State: ' + JSON.stringify(archiveState));
if (!archiveState.foundInArchived || archiveState.actionButtonsCount !== 0) {
  throw new Error('Fact archive lifecycle failed terminal read-only check');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-archive', { keep: false })`.
