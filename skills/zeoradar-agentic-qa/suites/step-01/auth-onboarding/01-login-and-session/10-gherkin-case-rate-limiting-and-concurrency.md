# Test Case: Rate Limiting (429), Error Banners & In-Flight Double-Click Lock

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-10-RATE-LIMIT-CONCURRENCY`
- **Purpose:** Validate rate-limit rejection handling (`rate_limited` error code / HTTP 429), assertion of localized backoff error banners (`authErrorCopy('rate_limited')`), unlock of form submission (`auth.busy = false`), and rapid in-flight double-click concurrency guards preventing duplicate network requests.

---

## 2. Tester Brief
The tester evaluates client resilience under network strain and abuse prevention limits. First, simulate a rapid double-click on the submit button within 50ms to verify that `auth.busy` drops the secondary invocation and only one network call is dispatched. Second, trigger a rate-limited response (HTTP 429 / GoTrue `over_email_send_rate_limit`) to confirm that the `.auth-error-msg` banner displays `"Too many attempts — try again shortly. (rate_limited)"`, input values are retained, and the button becomes re-enabled once the flight completes.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'signin_password'`, email populated
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[TEST_EMAIL]`: Test user email (`test-ratelimit@zeogen.com`)
  - `[PASSWORD]`: Test user password (`ZeoTest2026!`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Resilience - Concurrency Locking and Rate-Limit Handling

  Background:
    Given the user is on the password screen at "[APP_URL]/#/auth"
    And email is populated as "[TEST_EMAIL]"
    And password is typed as "[PASSWORD]"

  @concurrency @race-condition
  Scenario: Rapid double-click on submit button dispatches only one request
    Given the submit button ".auth-btn-primary.full-width" is enabled
    When the user triggers two rapid click events within 30 milliseconds
    Then the first click should engage "auth.busy = true"
    And the second click should be ignored and dropped immediately
    And exactly 1 network request should be dispatched to the auth backend
    And when the network request resolves, "auth.busy" should revert to false

  @rate-limiting @error-banner
  Scenario: Server rate limit returns localized warning banner and releases busy lock
    Given the user submits credentials that trigger rate limiting
    When the server responds with status 429 or error code "rate_limited"
    Then the auth error banner ".auth-error-msg" should be rendered
    And the banner text should contain "Too many attempts — try again shortly. (rate_limited)"
    And the input container ".input-with-icon" should receive class "input-error"
    And "window.getAuthState().busy" should be false
    And the submit button should be enabled so the user can retry after the backoff window
    And the entered password in "#auth-password-input" should not be cleared
```

---

## 5. Visual Checks
- **Rate Limit Banner Styling:**
  - Element `.auth-error-msg` styled with amber/red border, warning icon `⚠️`, and standard alert background.
  - Form inputs remain highlighted with `.input-error` outline.
- **Button Disabled / Active State:**
  - Button shows loading state during the single in-flight call, then returns to interactive state when rate-limit error is received.

---

## 6. Data & Network Checks
- **Concurrency Guard Assertion (`assets/auth.js:133`):**
  ```javascript
  // assets/auth.js: handleSignInSubmit / handleAuthEmailSubmit
  if (auth.busy || !client) return; // Second click must abort here
  ```
- **Error Code Translation (`assets/auth.js:150`):**
  ```javascript
  const copyEn = authErrorCopy('rate_limited');
  assert(copyEn === 'Too many attempts — try again shortly.');
  ```
- **Network Telemetry:**
  - Verify network log contains exactly 1 POST request during double-click test.
  - Response status: 429 Too Many Requests.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `10-gherkin-result-case-rate-limiting-and-concurrency/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, request count verification, rate limit response headers.
  - `network/requests.json`: Recorded HTTP requests proving only 1 request dispatched.
  - `evidence.json`: State of `auth.busy` and `auth.errorMessage`.
  - `screenshots/01-rate-limit-banner.png`: Rendered UI showing rate limit warning banner.
- **MacBook Execution Protocol:** Ego Browser captures network HAR and screenshot on MacBook gateway; artifacts transferred via SCP.
