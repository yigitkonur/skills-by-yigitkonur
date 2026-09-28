# Test Case: Trigger.dev Asynchronous Polling, Idempotency & Poller Resurrection

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-09-POLLING-IDEMPOTENCY`
- **Purpose:** Validate the asynchronous suggestion generation lifecycle via Trigger.dev background tasks, persistence of the batch idempotency key (`zeo-onboarding-sugkey:v1`), automatic poller resurrection on route switches (`obResumePollIfStalled()`), and 5-minute budget timeout handling (`OB_POLL_BUDGET_MS = 300000`) with recovery empty-state card.

---

## 2. Tester Brief
The tester triggers suggestion generation on Step 4 or Step 5. First, verify that the request payload signature generates an idempotency key saved in `localStorage['zeo-onboarding-sugkey:v1']`. Second, simulate route switching away from onboarding to `/#/` during active polling, return to `/#/onboarding`, and verify that `obResumePollIfStalled()` automatically detects the unfinished batch and revives the poller without dispatching duplicate jobs. Third, test timeout simulation (advancing past 5 minutes / budget expiry) to assert transition to `phase: "timeout"`, appearance of the `"This is taking longer than usual"` warning card, and functionality of the `"Check again"` retry button.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 4 or 5, suggestions initiated (`live.sg.phase === 'polling'`)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[BATCH_ID]`: Background batch identifier (`batch_ob_...`)
  - `[POLL_BUDGET]`: 300,000 milliseconds (5 minutes)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Asynchronous Suggestions - Polling, Idempotency and Resurrection

  Background:
    Given the user is on the suggestion generation phase at "[APP_URL]/#/onboarding"
    And a background suggestion batch is in flight

  @sanity @idempotency @persistence
  Scenario: Idempotency key is stored and recovered across reloads
    Then localStorage key "zeo-onboarding-sugkey:v1" should contain a valid signature
    When the user refreshes the browser tab
    Then the wizard should read the cached key from localStorage
    And reconnect to the running batch without creating a new duplicate batch

  @positive @resilience @resurrection
  Scenario: Navigating away and returning revives stalled poller
    Given background polling is active on batch "[BATCH_ID]"
    When the user navigates away to "[APP_URL]/#/"
    Then the poller should pause gracefully without throwing errors
    When the user navigates back to "[APP_URL]/#/onboarding"
    Then "window.obResumePollIfStalled()" should automatically trigger
    And polling should resume on "[BATCH_ID]" until suggestions complete

  @adversarial @timeout @recovery
  Scenario: Polling exceeding 5-minute budget renders timeout recovery card
    Given the background worker encounters high queue latency
    When the polling duration exceeds 300,000 milliseconds ("OB_POLL_BUDGET_MS")
    Then the suggestion phase should transition to "timeout"
    And the empty state card ".ob-empty-state.card" should be displayed
    And the heading should read "This is taking longer than usual"
    And a retry button "button[data-action='ob-retry-suggest']" ("Check again") should be visible
    When the user clicks "Check again"
    Then "obRetrySuggest()" should re-probe the existing batch status
```

---

## 5. Visual Checks
- **Live Progress List:**
  - While polling, `.ob-live-progress-list` displays items for `"prompts"`, `"personas"`, and `"keywords"` with animated spinning indicators.
- **Timeout Warning Card:**
  - Card `.ob-empty-state.card` displays amber warning icon `icon('warning')`, explanatory copy, and outline CTA button `"Check again"`.

---

## 6. Data & Network Checks
- **Budget Constant Assertion (`assets/onboarding.js:841`):**
  ```javascript
  // assets/onboarding.js: OB_POLL_BUDGET_MS must equal 300000 (5 minutes)
  const lv = window.state.onboarding.live;
  assert(lv.sg.batchId !== null, "Active batch ID must be present");
  ```
- **Poller Status Check:**
  ```javascript
  assert(typeof window.obResumePollIfStalled === 'function');
  ```
- **Network Telemetry:**
  - Polling requests to `/functions/v1/onboarding-suggest-status` with exponential backoff interval (1s -> 1.5s -> 2.25s -> max 6s).

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `09-gherkin-result-case-suggestion-polling-and-idempotency/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, poller interval telemetry, resurrection trace.
  - `evidence.json`: Idempotency key contents, poller lifecycle state.
  - `screenshots/01-polling-progress-active.png`: Live progress indicators.
  - `screenshots/02-timeout-recovery-card.png`: 5-minute timeout warning and retry CTA.
- **MacBook Execution Protocol:** Ego Browser monitors background network events on MacBook; downloads network/screenshot logs via SCP.
