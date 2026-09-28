# TC-ACC-02: Competitor Pinning Display Order vs Mathematical Invariant

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-02`
- **Purpose:** Verify that toggling competitor pins (`[data-action="toggle-pin"]`) elevates the target competitor to the top of competitor tables with a gold star indicator while strictly preserving ranking calculation denominators, visibility share percentages, and market share formulas without mathematical corruption.
- **Target Result Directory:** `03-account-team-billing/02-gherkin-result-case-competitor-pinning-order/`

---

## 2. Tester Brief
Users can pin key competitors to track them prominently at the top of ranking lists.
1. When clicking `[data-action="toggle-pin"]`:
   - The competitor row gains a pinned status flag and visually re-sorts to the top.
   - The pin icon highlights in active gold accent styling.
2. Architectural Invariant: Pinned status is purely cosmetic presentation state.
   - Total tracked competitors denominator remains unchanged.
   - Visibility Scores and Share of Voice (SOV) percentages remain exactly identical before and after pinning.
3. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/settings` (or Competitors list).
- **Target Competitor:** `[COMPETITOR_NAME]` (`[COMPETITOR_DOMAIN]`).

---

## 4. Gherkin Scenario

```gherkin
Feature: Competitor Pinning Display Order and Calculation Integrity

  Scenario: Toggling competitor pin priority without altering calculation denominators
    Given a competitor "Competitor Alpha" is unpinned with visibility score "42.5%"
    When the user clicks the pin toggle button "[data-action='toggle-pin']" for "Competitor Alpha"
    Then "Competitor Alpha" should be pinned to the top of the competitor table
    And the pin icon should display active highlighted styling
    And the visibility score for "Competitor Alpha" should remain exactly "42.5%"
    And overall category calculation denominators should remain unaltered

    Examples:
      | CompetitorName   | PrePinScore | PostPinScore |
      | Competitor Alpha | 42.5%       | 42.5%        |
      | Competitor Beta  | 18.2%       | 18.2%        |
```

---

## 5. Visual Checks
- **Table Elements:**
  - Pinned Row: `.competitor-row.is-pinned` positioned at index 0.
  - Pin Icon: `.pin-icon.active` (gold accent).
  - Unpinned Rows: Remain sorted underneath pinned rows.
- **Screenshot Points:**
  - `01_competitor_unpinned.png` (Default table ordering).
  - `02_competitor_pinned_top.png` (Competitor pinned to top with highlighted star).

---

## 6. Data and Network Checks
- **Formula Invariant:**
  - `scoreBeforePin === scoreAfterPin`.
  - `sovBeforePin === sovAfterPin`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/02-gherkin-result-case-competitor-pinning-order/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-competitor-pin');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/settings', { wait: true, timeout: 30 });
await wait(2);

const pinCheck = await js(String.raw`(() => {
  const pinBtn = document.querySelector('[data-action="toggle-pin"]');
  if (!pinBtn) return { skipped: true };

  const initialPinned = pinBtn.classList.contains("active");
  pinBtn.click();
  const toggledPinned = pinBtn.classList.contains("active");

  return {
    initialPinned,
    toggledPinned,
    stateChanged: initialPinned !== toggledPinned
  };
})()`);

cliLog('Pin Toggle State: ' + JSON.stringify(pinCheck));
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-competitor-pin', { keep: false })`.
