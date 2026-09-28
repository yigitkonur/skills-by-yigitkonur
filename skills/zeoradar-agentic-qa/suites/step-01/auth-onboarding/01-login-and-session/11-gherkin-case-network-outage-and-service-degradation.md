# Test Case: Network Outage, Service 500/Offline Handling & Non-Destructive Recovery

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-11-NETWORK-OUTAGE`
- **Purpose:** Validate client fault tolerance when authentication dependencies are offline (network dropped, HTTP 0, or HTTP 500+ / 503 / 504), ensuring the error message reflects `dependency_unavailable` copy, user-entered inputs are non-destructively preserved, and the busy lock is released for subsequent retries.

---

## 2. Tester Brief
The tester simulates a network failure or backend outage during credential submission (either by disabling network connectivity in the test runner or intercepting the auth endpoint with HTTP status 0 / 503). The tester asserts that the application does not crash or navigate to a blank error screen, renders `"The sign-in service is temporarily unavailable. (dependency_unavailable)"`, retains all typed inputs in `#auth-password-input` and `#auth-email-input`, and returns the submit button to an interactive state.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** Step `signin_password`, email and password populated
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Test user email (`alexsmith@content-mobbin.com`)
  - `[PASSWORD]`: Test user password (`zeo-demo-2026`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Fault Tolerance - Dependency Outage and Input Preservation

  Background:
    Given the user is on the password screen at "[APP_URL]/#/auth"
    And email is "[USER_EMAIL]"
    And password input holds "[PASSWORD]"

  @negative @network @fault-tolerance
  Scenario Outline: Backend network outage or 5xx server error triggers non-destructive recovery
    Given the network layer is configured to return error condition "<error_condition>"
    When the user clicks the submit button ".auth-btn-primary.full-width"
    Then the auth error banner ".auth-error-msg" should be displayed
    And the error banner text should contain "The sign-in service is temporarily unavailable. (dependency_unavailable)"
    And the entered password "[PASSWORD]" should remain intact in "#auth-password-input"
    And "window.getAuthState().busy" should be false
    And the submit button should be enabled to permit immediate retry

    Examples:
      | error_condition        |
      | HTTP 503 Service Unavail |
      | HTTP 500 Internal Error  |
      | Network Timeout / Status 0|
```

---

## 5. Visual Checks
- **Error Banner Layout:**
  - Banner `.auth-error-msg` displays prominently above the password input container.
  - Text reads: `"⚠️ The sign-in service is temporarily unavailable. (dependency_unavailable)"` in English (or Turkish equivalent: `"⚠️ Giriş servisi geçici olarak kullanılamıyor. (dependency_unavailable)"`).
- **Input Integrity:**
  - Password input does not reset to empty string upon failure.

---

## 6. Data & Network Checks
- **Code Translation Assertion (`assets/auth.js:151`):**
  ```javascript
  const copy = authErrorCopy('dependency_unavailable');
  assert(copy === 'The sign-in service is temporarily unavailable.');
  ```
- **State Integrity:**
  ```javascript
  const auth = window.getAuthState();
  assert(auth.busy === false, "Busy lock must be released on failure");
  assert(auth.password === '[PASSWORD]', "Password in state must be preserved");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `11-gherkin-result-case-network-outage-and-service-degradation/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, simulated error status, retry attempt logs.
  - `evidence.json`: State snapshot demonstrating input preservation.
  - `screenshots/01-dependency-unavailable-banner.png`: Error banner with retained form inputs.
- **MacBook Execution Protocol:** Ego Browser captures error banner on MacBook; evidence downloaded via SCP.
