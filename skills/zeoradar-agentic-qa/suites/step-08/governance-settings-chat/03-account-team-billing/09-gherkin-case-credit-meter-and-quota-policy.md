# TC-ACC-09: Credit Meter Visualization and Server-Authoritative Quota Enforcement

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-09`
- **Purpose:** Verify that the billing credit consumption meter accurately displays used vs total quota (`1 credit = 1 execution cell`), updates progress bar color tiers (green, amber, red), renders the mandatory server-authorization note, and handles `insufficient_credits` errors with upgrade guidance when quota is exhausted.
- **Target Result Directory:** `03-account-team-billing/09-gherkin-result-case-credit-meter-and-quota-policy/`

---

## 2. Tester Brief
In Zeo Geo-Radar, monitoring computation is metered:
1. `1 credit = 1 execution cell` (evaluating 1 prompt on 1 AI engine platform like ChatGPT).
2. The progress bar `.acct-billing-bar` reflects consumption:
   - `< 80%`: Neutral green.
   - `80% - 95%`: Warning amber.
   - `> 95%`: Critical red.
3. The surface displays the architectural authority note: run execution is authorized exclusively by the backend, not the browser client.
4. When credits are depleted, attempting a run returns `{ error: { code: "insufficient_credits" } }`, triggering `showAccountError("insufficient_credits")`.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=billing`.
- **Meter Quota Data:** `{ used: 9200, limit: 10000, cycleResetDate: "2026-10-01" }`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Credit Meter and Quota Authorization

  Scenario Outline: Visualizing credit consumption tier and handling quota exhaustion
    Given the workspace credit consumption is <UsedCredits> of <TotalLimit> credits
    When the user navigates to the Billing tab
    Then the credit meter bar should display fill percentage "<ExpectedPercent>"
    And the meter color tier should be "<ExpectedColorTier>"
    And the billing surface should render the authority note "1 credit = 1 execution cell"
    When an execution attempt returns error "insufficient_credits"
    Then the account error modal should prompt the user to buy additional credits

    Examples:
      | UsedCredits | TotalLimit | ExpectedPercent | ExpectedColorTier |
      | 5000        | 10000      | 50%             | green             |
      | 8500        | 10000      | 85%             | amber             |
      | 9800        | 10000      | 98%             | red               |
```

---

## 5. Visual Checks
- **Meter Elements:**
  - Progress Bar: `.acct-billing-bar` or `.billing-meter`.
  - Authority Note: `.acct-billing-authority-note` containing `"1 credit = 1 execution cell"` / `"1 kredi = 1 yürütme hücresi"`.
  - Action Button: `[data-account-action="billing-buy-more"]`.
- **Screenshot Points:**
  - `01_credit_meter_display.png` (Credit usage bar and authority note).
  - `02_insufficient_credits_modal.png` (Modal shown when credits are exhausted).

---

## 6. Data and Network Checks
- **Error Code Mapping:**
  - `insufficient_credits` -> Displays credit recharge prompt.
  - Calculation: `(used / limit) * 100`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/09-gherkin-result-case-credit-meter-and-quota-policy/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-credit-meter');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=billing', { wait: true, timeout: 30 });
await wait(2);

const meterCheck = await js(String.raw`(() => {
  const noteEl = document.querySelector('.acct-billing-authority-note');
  const barEl = document.querySelector('.acct-billing-bar, .billing-meter');
  const buyBtn = document.querySelector('[data-account-action="billing-buy-more"]');

  const authorityText = noteEl ? noteEl.innerText.trim() : "";
  const hasAuthorityNote = authorityText.includes("1 credit = 1 execution cell") || authorityText.includes("1 kredi = 1 yürütme hücresi");

  return {
    hasBar: !!barEl,
    hasBuyBtn: !!buyBtn,
    hasAuthorityNote
  };
})()`);

cliLog('Credit Meter Check: ' + JSON.stringify(meterCheck));
if (!meterCheck.hasAuthorityNote) {
  throw new Error('Billing surface missing mandatory server authority note');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-credit-meter', { keep: false })`.
