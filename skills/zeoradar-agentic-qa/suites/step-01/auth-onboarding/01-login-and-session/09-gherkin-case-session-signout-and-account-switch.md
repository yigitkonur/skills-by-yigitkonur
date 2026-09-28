# Test Case: Session Termination, Account Switching & State Cleansing

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-09-SIGNOUT-SWITCH`
- **Purpose:** Validate complete session sign-out (`handleAuthSignOut()`), account switching (`handleAuthSwitchAccount()`), purging of session tokens in `localStorage` (`zeo-mock-auth:v1`), reset of sensitive form states in `window.state.auth`, and secure redirection to the initial `/#/auth` entry point.

---

## 2. Tester Brief
The tester starts from an authenticated application session (logged in as an active user). The tester triggers sign out via user menu / profile dropdown, asserts that session tokens are purged from client storage, asserts that `window.getAuthState()` is completely reset, and asserts redirection to `/#/auth`. Next, the tester tests "Switch account" (`handleAuthSwitchAccount()`) from the brand setup step to confirm that lingering credentials from previous attempts are wiped clean.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/` (authenticated)
- **Prerequisite State:** User logged in, `localStorage['zeo-mock-auth:v1']` contains valid session
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[CURRENT_USER]`: Active user email (`alexsmith@content-mobbin.com`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Lifecycle - Session Sign-out and Account Switching

  Background:
    Given the user is authenticated as "[CURRENT_USER]"
    And localStorage contains active session keys

  @positive @signout
  Scenario: User sign-out securely purges tokens and redirects to auth
    When the user triggers sign-out via "handleAuthSignOut()" or profile menu
    Then the auth client method "signOut()" should execute
    And localStorage key "zeo-mock-auth:v1" should reflect "authState: 'signed_out'"
    And the application router should redirect to "[APP_URL]/#/auth"
    And the auth form should reset to step "email" with empty email and password fields

  @positive @switch-account
  Scenario: Switch account resets form state and signs out
    Given the user is on the brand setup screen at "[APP_URL]/#/auth" (step: "brand_setup")
    When the user clicks the "Switch account" link ".wrong-account-row button.link-btn"
    Then "handleAuthSwitchAccount()" should execute
    And the OTP resend timer interval should be cleared
    And "window.state.auth" should be reset to null
    And the auth view should render afresh in step "email"
    And previous user credentials should not be autofilled
```

---

## 5. Visual Checks
- **Profile Popover / Sign Out Button:**
  - Profile menu `.profile-popover` contains a clear red-tinted or neutral `"Sign out"` button with icon `icon('logout')`.
- **Redirect Visual Transition:**
  - Fast, flicker-free transition from dashboard layout back to the two-column auth split view (`.auth-container`).
  - Input `#auth-email-input` is focused and completely blank.

---

## 6. Data & Network Checks
- **Storage & State Purge:**
  ```javascript
  const auth = window.getAuthState();
  assert(auth.email === '', "Email must be cleared");
  assert(auth.password === '', "Password must be cleared");
  assert(auth.step === 'email', "Step must reset to email");
  const rawSession = localStorage.getItem('zeo-mock-auth:v1');
  if (rawSession) {
    const session = JSON.parse(rawSession);
    assert(session.authState === 'signed_out', "Session must be marked signed_out");
    assert(session.session === null, "Session tokens must be null");
  }
  ```
- **Network Call:**
  - Dispatches sign-out request to `/auth/v1/logout` or mock client handler.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `09-gherkin-result-case-session-signout-and-account-switch/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, execution trace, storage purge verification.
  - `evidence.json`: State snapshot before and after sign-out.
  - `screenshots/01-authenticated-dashboard.png`: Pre-signout authenticated dashboard state.
  - `screenshots/02-signout-auth-screen.png`: Post-signout clean auth screen render.
- **MacBook Execution Protocol:** Ego Browser on MacBook executes navigation and signout commands; evidence downloaded via SCP.
