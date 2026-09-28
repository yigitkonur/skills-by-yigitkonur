# Test Case: E2E Dev Bypass Login, Query Parameter & Corrupt Storage Fallback

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-08-DEV-BYPASS-STORAGE`
- **Purpose:** Validate automated E2E test bypass login capabilities (`#btn-bypass-test-login`, `window.zeoBypassLogin()`, and URL parameter `?auto_login=1`), and test application resilience against corrupted localStorage session data (graceful fallback to `signed_out` without unhandled runtime exceptions).

---

## 2. Tester Brief
The tester evaluates automated testing capabilities utilized by CI/CD and E2E agents. First, verify the presence and execution of `#btn-bypass-test-login` when bypass gates are active (`window.zeoIsBypassGates() === true`). Second, verify direct invocation via `window.zeoBypassLogin(email, password)`. Third, verify URL parameter `?auto_login=1` triggering auto-sign-in on boot. Fourth, inject corrupted / malformed JSON into `localStorage['zeo-mock-auth:v1']` to verify that the auth client catches the parse error, purges bad state, and falls back cleanly to `signed_out`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/?auto_login=1` or `[APP_URL]/#/auth`
- **Prerequisite State:** Bypass gate active (`window.zeoIsBypassGates() === true`)
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[BYPASS_EMAIL]`: Default agent email (`e2e-agent@zeogen.com`)
  - `[BYPASS_PASSWORD]`: Default agent password (`ZeoTest2026!`)
  - `[CORRUPT_JSON]`: Malformed string (`"{ invalid-json-payload-broken..."`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Resilience - Dev Bypass and Corrupt Storage Recovery

  @positive @bypass @e2e
  Scenario: Clicking the test bypass login button logs in instantly
    Given the user navigates to "[APP_URL]/#/auth"
    And bypass gates are active in the test environment
    Then the bypass login button "#btn-bypass-test-login" should be rendered
    When the user clicks "#btn-bypass-test-login"
    Then "window.zeoBypassLogin()" should execute
    And localStorage "zeo-mock-auth:v1" should contain an authenticated session
    And the application should route to the dashboard

  @positive @url-param @auto-login
  Scenario: Navigating with auto_login=1 automatically authenticates
    When the user navigates to "[APP_URL]/?auto_login=1"
    Then within 500ms the auto_login watcher should trigger "zeoBypassLogin"
    And the user should be automatically logged in without manual clicks
    And the current route should transition away from "auth"

  @negative @resilience @corruption
  Scenario: Corrupted localStorage session data falls back cleanly to signed_out
    Given the user is authenticated in the application
    When the tester corrupts localStorage with malformed JSON:
      """javascript
      localStorage.setItem('zeo-mock-auth:v1', '{corrupt json without closing brace...');
      """
    And the application requests session state via "window.ZEO_AUTH_CLIENT.getSession()"
    Then the auth client should not throw an uncaught exception
    And the returned authState should be "signed_out"
    And the corrupted storage entry should be cleared or rewritten with signedOutState
    And the user should be safely directed to the login screen
```

---

## 5. Visual Checks
- **Bypass Button Appearance:**
  - Button `#btn-bypass-test-login` renders with styling `btn-bypass-test-login` below the main form.
  - Visible only when `zeoIsBypassGates()` returns true (local development / test environments), hidden in production.
- **Corrupt Storage Recovery Display:**
  - The login view renders cleanly with no uncaught error popups or broken layouts.

---

## 6. Data & Network Checks
- **Bypass Execution Logic (`assets/auth.js:1341`):**
  ```javascript
  assert(typeof window.zeoBypassLogin === 'function', "zeoBypassLogin must be globally exposed");
  ```
- **Storage Resilience Logic (`assets/supabase-client.js:56`):**
  ```javascript
  try {
    const raw = localStorage.getItem('zeo-mock-auth:v1');
    const parsed = JSON.parse(raw);
  } catch (err) {
    // Must gracefully revert to signedOutState
    const state = signedOutState();
    localStorage.setItem('zeo-mock-auth:v1', JSON.stringify(state));
  }
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `08-gherkin-result-case-dev-bypass-and-auto-login/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, bypass login latency, storage recovery logs.
  - `evidence.json`: Storage keys before and after corruption injection.
  - `screenshots/01-bypass-button-visible.png`: Initial page showing bypass test button.
  - `screenshots/02-bypass-success-redirect.png`: Successful dashboard landing post-bypass.
  - `screenshots/03-corrupt-storage-graceful-auth.png`: Clean login page render after corruption reset.
- **MacBook Execution Protocol:** Automated session scripts executed via Ego Browser on MacBook gateway; screenshots fetched via SCP.
