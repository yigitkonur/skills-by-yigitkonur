# Test Case: Password Authentication, Visibility Toggles & Credential Rejection

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-02-PASSWORD-AUTH`
- **Purpose:** Validate password entry behavior in `step === 'signin_password'`, password visibility toggling (`type="password"` vs `type="text"`), length gating (minimum 6 characters), error handling with localized error banner on invalid credentials, and successful authentication transition on valid credentials.

---

## 2. Tester Brief
The tester starts from the password entry step (`signin_password`) with a valid email pre-populated. The tester will verify that the password input is masked by default, toggle the eye icon to unmask and re-mask the password, verify submit button disabled state for passwords under 6 characters, submit an invalid password to assert the `unauthenticated` error message banner, and finally submit valid credentials to assert successful authentication and workspace routing.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'signin_password'`, `window.getAuthState().email === '[USER_EMAIL]'`
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Test user email (`alexsmith@content-mobbin.com`)
  - `[VALID_PASSWORD]`: Valid fixture password (`zeo-demo-2026`)
  - `[INVALID_PASSWORD]`: Invalid password string (`WrongPassword999!`)
  - `[SHORT_PASSWORD]`: Password under 6 characters (`abc1`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 2 - Password Authentication and Error Recovery

  Background:
    Given the user is on the password screen at "[APP_URL]/#/auth"
    And the displayed email is "[USER_EMAIL]"
    And the current auth step is "signin_password"

  @sanity @ui @positive
  Scenario: Password visibility toggle operates seamlessly
    When the user types "[VALID_PASSWORD]" into "#auth-password-input"
    Then the input attribute "type" should be "password"
    When the user clicks the eye toggle button "button.eye-toggle-btn"
    Then the input attribute "type" should change to "text"
    And the eye icon should reflect the unmasked state
    When the user clicks the eye toggle button "button.eye-toggle-btn" again
    Then the input attribute "type" should revert to "password"

  @negative @validation
  Scenario Outline: Short passwords prevent form submission
    When the user types "<short_pwd>" into "#auth-password-input"
    Then the submit button ".auth-form button.auth-btn-primary.full-width" should be disabled

    Examples:
      | short_pwd |
      | 12345     |
      | abc       |
      | a         |
      |           |

  @negative @authentication
  Scenario: Invalid credentials display localized error banner
    When the user enters "[INVALID_PASSWORD]" into "#auth-password-input"
    And the user clicks the submit button ".auth-form button.auth-btn-primary.full-width"
    Then the auth error banner ".auth-error-msg" should become visible
    And the error banner text should contain "Email or password is incorrect. (unauthenticated)"
    And the password input container ".input-with-icon" should have class "input-error"
    And the submit button should be re-enabled for a retry
    And the password field value should be preserved

  @positive @authentication
  Scenario: Valid credentials successfully authenticate and route user
    When the user enters "[VALID_PASSWORD]" into "#auth-password-input"
    And the user clicks the submit button ".auth-form button.auth-btn-primary.full-width"
    Then the busy state "window.getAuthState().busy" should be briefly true during flight
    And the auth client should record session tokens in localStorage under "zeo-mock-auth:v1"
    And the application should route to the dashboard or onboarding
```

---

## 5. Visual Checks
- **Email Readout Box:**
  - Container `.readonly-email-box` displays the verified email string and an `"Edit"` button (`button.edit-link`) that returns to Step 1.
- **Input Error Highlighting:**
  - On 401 / `unauthenticated`, `.input-with-icon` receives border color `var(--color-danger, #ef4444)` and class `.input-error`.
  - Error banner `.auth-error-msg` displays warning icon `⚠️` and red-tinted alert background.
- **Loading State:**
  - Submit button shows disabled state and opacity reduction while `auth.busy === true`.

---

## 6. Data & Network Checks
- **DOM & Class Assertions:**
  ```javascript
  const input = document.querySelector('#auth-password-input');
  assert(input.getAttribute('type') === 'password', "Default password type must be password");
  const errorMsg = document.querySelector('.auth-error-msg');
  if (errorMsg) {
    assert(errorMsg.textContent.includes('unauthenticated'), "Error message must reflect code unauthenticated");
  }
  ```
- **Storage Assertions:**
  ```javascript
  const session = JSON.parse(localStorage.getItem('zeo-mock-auth:v1') || '{}');
  assert(session.authState === 'signed_in', "Successful login must write signed_in state");
  assert(session.user.email === 'alexsmith@content-mobbin.com');
  ```
- **Network Telemetry:**
  - POST to `/auth/v1/token?grant_type=password` (or mock equivalent `client.signInWithPassword`).
  - Response status: 400/401 on invalid credentials; 200 OK on valid credentials.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `02-gherkin-result-case-password-authentication/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, step execution duration, HTTP status codes.
  - `evidence.json`: Auth state dump before and after submission, storage key presence.
  - `screenshots/01-password-masked.png`: Password entered with bullets.
  - `screenshots/02-password-unmasked.png`: Eye toggled showing plain text.
  - `screenshots/03-password-error-banner.png`: Rejection banner on invalid password.
  - `screenshots/04-auth-success-redirect.png`: Successful dashboard landing.
- **MacBook Execution Protocol:** Ego Browser captures screenshots on the MacBook display; files are synchronized to `02-gherkin-result-case-password-authentication/screenshots/` via SCP.
