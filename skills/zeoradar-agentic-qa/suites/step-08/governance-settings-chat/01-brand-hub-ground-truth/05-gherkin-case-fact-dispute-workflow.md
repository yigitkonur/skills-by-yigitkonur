# TC-BH-05: Brand Fact Contradiction Dispute Flow

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-05`
- **Purpose:** Verify that an owner can dispute an unverified or hallucinated fact, ensuring the mutation sets status to `"disputed"`, nullifies any prior verification note, locks in-flight duplicate clicks via `pendingDisputeFactId`, displays a confirmation toast, and reflects the updated status pill in the UI.
- **Target Result Directory:** `01-brand-hub-ground-truth/05-gherkin-result-case-fact-dispute-workflow/`

---

## 2. Tester Brief
When an answer engine or competitor citation asserts a questionable fact about the brand, an administrator flags the claim as disputed.
1. The user clicks `button[data-action="bh-dispute-fact"][data-fact-id="..."]`.
2. The client sets `bhs.pendingDisputeFactId` to prevent parallel mutations and shows a temporary spinner or disabled state.
3. The command `update-brand-hub` is called with `status: "disputed"` and `confirmationNote: null`.
4. Upon successful response, a toast `"Fact marked disputed"` (or `"Olguya itiraz edildi"`) is displayed.
5. The card status pill transitions to `.bh-status-pill.disputed` and renders the dispute icon `icon("x", 11)`.
6. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb` -> Subtab `facts`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[FACT_ID]`: `fact_dispute_target_01`
  - `[FACT_KEY]`: `headcount_2026`

---

## 4. Gherkin Scenario

```gherkin
Feature: Brand Fact Dispute Lifecycle

  Scenario Outline: Disputing a brand fact and nullifying previous verification notes
    Given the test user is an owner on the Brand Hub facts tab
    And a fact with key "<FactKey>" exists with status "<InitialStatus>"
    When the user clicks the dispute button "button[data-action='bh-dispute-fact']" for "<FactKey>"
    Then the fact should transition to pending dispute state
    And the mutation command "update-brand-hub" should be sent with status "disputed"
    And a toast notification containing "<ExpectedToast>" should be shown
    And the fact card should display status pill with class "disputed"
    And the fact provenance box should no longer display an active confirmation note

    Examples:
      | FactKey         | InitialStatus | ExpectedToast         |
      | headcount_2026  | unverified    | Fact marked disputed  |
      | valuation_round | verified      | Fact marked disputed  |
```

---

## 5. Visual Checks
- **Card Elements:**
  - Target Card: `.card.bh-fact-card` containing machine key code `code.bh-fact-key`.
  - Dispute Trigger: `button.btn.small[data-action="bh-dispute-fact"]`.
  - Post-Dispute Status Pill: `.bh-status-pill.disputed` (red pill with cross icon).
  - Provenance Box: `.bh-provenance-box` must be hidden or removed.
- **Filter Bar:**
  - Clicking `span.fchip[data-filter="disputed"]` includes the target fact.
- **Screenshot Points:**
  - `01_fact_before_dispute.png` (Fact card prior to dispute).
  - `02_fact_disputed_pill.png` (Fact card displaying Disputed status pill and toast).

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
        "id": "fact_dispute_target_01",
        "factKey": "headcount_2026",
        "status": "disputed",
        "confirmationNote": null
      }]
    }
    ```
- **Concurrency Guard:**
  - Clicking dispute while `bhs.pendingDisputeFactId !== null` is silently dropped to prevent duplicate network calls.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/05-gherkin-result-case-fact-dispute-workflow/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-dispute');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

await click('.brand-hub-tab-btn[data-tab="facts"]');
await wait(1);

// Locate an active fact card and click Dispute
const disputeResult = await js(String.raw`(() => {
  const bhs = window.state && window.state.brandHub;
  if (!bhs || !bhs.data || !bhs.data.facts || !bhs.data.facts.length) return { found: false };
  const target = bhs.data.facts[0];
  const btn = document.querySelector('button[data-action="bh-dispute-fact"][data-fact-id="' + target.id + '"]');
  if (btn) {
    btn.click();
    return { found: true, factId: target.id, factKey: target.factKey };
  }
  return { found: false };
})()`);

await wait(2);

const pillCheck = await js(String.raw`(() => {
  const cards = Array.from(document.querySelectorAll('.bh-fact-card'));
  const found = cards.find(c => c.innerText.includes('${disputeResult.factKey}'));
  const pill = found ? found.querySelector('.bh-status-pill.disputed') : null;
  return {
    rendered: !!found,
    isDisputedPill: !!pill,
    pillText: pill ? pill.innerText.trim() : null
  };
})()`);

cliLog('Dispute Assertions: ' + JSON.stringify(pillCheck));
if (!pillCheck.isDisputedPill) {
  throw new Error('Fact status pill failed to transition to Disputed');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-dispute', { keep: false })`.
