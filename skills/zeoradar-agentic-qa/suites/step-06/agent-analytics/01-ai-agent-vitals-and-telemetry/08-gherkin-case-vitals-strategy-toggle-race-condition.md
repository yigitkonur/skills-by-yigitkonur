# Case 08: Mid-Run Strategy Switching & Audit Re-entrancy Protection

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-08`
- **Purpose**: Verify that the Web Vitals audit runner enforces strict re-entrancy protection (`if (state.webVitalsLoading) return;`) preventing concurrent duplicate command dispatches when the user rapidly clicks the Run Audit button, that toggling the emulation strategy (`mobile` vs `desktop`) while an audit is in flight safely updates the UI state without corrupting the active audit envelope, and that subsequent dispatches accurately adopt the newly selected strategy.

## 2. Tester Brief
The tester triggers an audit with the default `mobile` strategy on the Pages tab. While the audit request is in flight (`webVitalsLoading === true`), the tester immediately clicks the `desktop` strategy toggle and attempts to click the Run Audit button a second time. The tester verifies that the disabled button prevents duplicate dispatch, confirms that the in-flight response records `strategy: 'mobile'`, and executes a follow-up audit to prove that the next dispatch transmits `strategy: 'desktop'`.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Initial Strategy: `mobile`
  - Mid-Flight Switched Strategy: `desktop`
- **Prerequisites**:
  - Pages tab active.

## 4. Gherkin Scenario

```gherkin
Feature: Web Vitals Runner In-Flight Race Condition & Re-entrancy Guard
  As an Automation Performance Engineer
  I want audit execution to be guarded against double-clicking and race conditions
  So that background workers are not flooded and state consistency is maintained

  Background:
    Given the user is on the Pages tab "button.aa-tab-item[data-tab='pages']"
    And the default strategy toggle is set to "mobile"
    And a valid target URL is present in "input[data-action-input='aa-vitals-url']"

  Scenario: Verify re-entrancy prevention during in-flight audit
    When the user clicks the Run Audit button "button[data-action='aa-run-vitals']"
    Then the audit command should be dispatched with strategy "mobile"
    And "window.AgentAnalyticsState.webVitalsLoading" should become true
    And the Run Audit button should be disabled
    When the user clicks the Run Audit button again while loading is true
    Then no duplicate command should be dispatched to the data provider

  Scenario: Switch strategy while audit is in-flight and verify payload integrity
    Given an audit with strategy "mobile" is currently in-flight
    When the user clicks the strategy toggle "button.aa-pill[data-strat='desktop']"
    Then "window.AgentAnalyticsState.webVitalsStrategy" should update to "desktop"
    And the desktop strategy pill should display active class ".good"
    When the in-flight mobile audit resolves successfully
    Then the recorded audit data should reflect the original dispatched strategy "mobile"
    And the loading lock should release cleanly

  Scenario: Execute subsequent audit with newly selected desktop strategy
    Given the previous mobile audit has resolved
    And the strategy remains set to "desktop"
    When the user clicks the Run Audit button "button[data-action='aa-run-vitals']"
    Then the new command dispatch should transmit strategy "desktop"
    And the audit response should register strategy "desktop"
```

## 5. Visual Checks
- **Strategy Pills**: Active pill displays `.good` with green border/tint; inactive pill displays neutral styling.
- **Button Disabled State**: Visual opacity drop and cursor `not-allowed` while in-flight.

## 6. Data and Network Checks
- **Call Counting Assertions**:
  ```javascript
  let dispatchCalls = 0;
  // Intercept dispatchCommand calls
  assert.strictEqual(dispatchCalls, 1, 'Only one command must be dispatched during loading');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-vitals-strategy-toggle-race-condition/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-08-midrun-toggle.png`
     - `/tmp/ego-shots/tc-aa-08-desktop-resolved.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-08-*.png ./01-gherkin-result-case-vitals-strategy-toggle-race-condition/
     ```
