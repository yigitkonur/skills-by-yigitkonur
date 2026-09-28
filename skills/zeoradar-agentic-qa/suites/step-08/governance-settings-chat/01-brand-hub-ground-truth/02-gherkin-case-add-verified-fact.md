# TC-BH-02: Verified Fact Creation and Provenance Note Enforcement

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-02`
- **Purpose:** Verify that a workspace owner can author a new brand fact, validate the machine fact key syntax (`/^[a-zA-Z0-9_-]{1,100}$/`), enforce a mandatory confirmation note for verified claims, and confirm the fact card and provenance metadata render correctly in the active facts list.
- **Target Result Directory:** `01-brand-hub-ground-truth/02-gherkin-result-case-add-verified-fact/`

---

## 2. Tester Brief
This test exercises the core Ground Truth mutation flow:
1. Opening the Add Fact drawer via `button[data-action="bh-open-fact-drawer"]`.
2. Validating input fields: Key, Statement, Sources (newline delimited URLs), and Status selector.
3. Enforcing business logic: If status is set to `"verified"`, `confirmationNote` cannot be empty.
4. Confirming optimistic locking payload: The mutation passes `expectedVersion: currentVersion`.
5. Verifying the resulting DOM: The new fact appears as `.card.bh-fact-card` with `.bh-status-pill.verified` and a `.bh-provenance-box` showing the confirmation note and timestamp.
6. **Execution Model:** Ego Browser operates on the remote MacBook. Captured screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb` -> Subtab `facts`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[FACT_KEY]`: `founding_year_1926`
  - `[FACT_STATEMENT]`: `Zeo was originally incorporated in 1926 in Istanbul.`
  - `[FACT_SOURCES]`: `https://registry.example.org/records/1926\nhttps://zeo.org/history`
  - `[CONFIRMATION_NOTE]`: `Verified against certified trade registry extract #9928.`

---

## 4. Gherkin Scenario

```gherkin
Feature: Verified Fact Creation Lifecycle

  Scenario Outline: Authoring a verified brand fact with mandatory confirmation note
    Given the test user is an authenticated workspace owner
    And the user is on the Brand Hub "facts" subtab
    When the user clicks the "Add Fact" button "button[data-action='bh-open-fact-drawer']"
    Then the fact drawer panel ".bh-live-drawer" should be open and visible
    When the user enters the fact key "<FactKey>" into "#bhFactKey"
    And the user enters the statement "<Statement>" into "#bhFactStatement"
    And the user enters sources "<Sources>" into "#bhFactSources"
    And the user selects status "<Status>" from "#bhFactStatus"
    And the user enters confirmation note "<ConfirmationNote>" into "#bhFactConfirmationNote"
    And the user clicks the drawer save button "button[data-action='bh-save-durable']"
    Then the drawer panel should close
    And a fact card containing "<FactKey>" should be visible in the facts list
    And the fact card should display status pill with class "<PillClass>"
    And the provenance box ".bh-provenance-box" should display "<ConfirmationNote>"

    Examples:
      | FactKey             | Statement                                         | Sources                            | Status    | ConfirmationNote                                | PillClass  |
      | founding_year_1926  | Zeo was originally incorporated in 1926.          | https://example.com/corporate-doc  | verified  | Verified against official trade registry.       | verified   |
      | global_headquarters | Global operations are managed from London, UK.    | https://example.com/press-release  | verified  | Certified by corporate legal counsel.           | verified   |
```

---

## 5. Visual Checks
- **Drawer Elements:**
  - Drawer panel: `.zr-drawer-panel.bh-live-drawer[role="dialog"]`.
  - Input Key: `#bhFactKey.pe-input`.
  - Input Statement: `#bhFactStatement.pe-input`.
  - Select Status: `#bhFactStatus.pe-input`.
  - Provenance Note: `#bhFactConfirmationNote.pe-input`.
- **Card Elements Post-Save:**
  - Container: `.card.bh-fact-card`.
  - Machine Key: `code.bh-fact-key`.
  - Status Pill: `.bh-status-pill.verified`.
  - Provenance Box: `.bh-provenance-box` containing confirmation note text and `(YYYY-MM-DD · user)`.
- **Screenshot Points:**
  - `01_fact_drawer_filled.png` (Fact drawer filled before submission).
  - `02_verified_fact_card_rendered.png` (Rendered fact card with provenance metadata).

---

## 6. Data and Network Checks
- **Command RPC:**
  - Call: `window.ZEO_DATA_PROVIDER.callCommand("update-brand-hub", payload)`.
  - Payload Inspection:
    ```json
    {
      "projectId": "[PROJECT_ID]",
      "expectedVersion": 1,
      "facts": [{
        "factKey": "founding_year_1926",
        "statement": "Zeo was originally incorporated in 1926.",
        "sources": ["https://example.com/corporate-doc"],
        "status": "verified",
        "confirmationNote": "Verified against official trade registry."
      }]
    }
    ```
- **Response Assertion:**
  - `res.ok === true`.
  - `res.data.brandHub.version === 2` (incremented).

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/02-gherkin-result-case-add-verified-fact/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-add-fact');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

// Switch to facts tab
await click('.brand-hub-tab-btn[data-tab="facts"]');
await wait(1);

// Open drawer
await click('button[data-action="bh-open-fact-drawer"]');
await wait(1);

const testKey = 'fact_test_' + Date.now().toString(36);
await fillInput('#bhFactKey', testKey);
await fillInput('#bhFactStatement', 'Automated Ground Truth fact statement.');
await fillInput('#bhFactSources', 'https://example.com/doc-1');

await js(String.raw`(() => {
  const sel = document.getElementById('bhFactStatus');
  if (sel) { sel.value = 'verified'; sel.dispatchEvent(new Event('change', { bubbles: true })); }
})()`);
await fillInput('#bhFactConfirmationNote', 'Confirmed by E2E automation harness.');

// Save
await click('button[data-action="bh-save-durable"]');
await wait(2);

const verifiedCard = await js(String.raw`(() => {
  const cards = Array.from(document.querySelectorAll('.bh-fact-card'));
  const found = cards.find(c => c.innerText.includes('${testKey}'));
  return {
    rendered: !!found,
    isVerifiedPill: found ? found.querySelector('.bh-status-pill.verified') !== null : false,
    provenanceFound: found ? found.querySelector('.bh-provenance-box') !== null : false
  };
})()`);

cliLog('Created Fact Check: ' + JSON.stringify(verifiedCard));
if (!verifiedCard.rendered || !verifiedCard.isVerifiedPill || !verifiedCard.provenanceFound) {
  throw new Error('Created verified fact failed visual or provenance assertions');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-add-fact', { keep: false })`.
