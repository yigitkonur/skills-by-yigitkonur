# Test Case: Email Pre-check, Syntax Validation & Case Normalization

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-01-EMAIL-PRECHECK`
- **Purpose:** Verify client-side email format validation, whitespace trimming, lowercase normalization, and dynamic button gating on the initial authentication screen (`step === 'email'`). Ensure invalid syntax prevents advance while valid emails transition to the password entry step.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to the root auth route (`/#/auth`), inspect the email input field, attempt submissions with invalid email formats to assert that the continue button remains strictly disabled, enter emails with mixed casing and leading/trailing whitespace, and verify that upon submission the string is properly sanitized and displayed cleanly in the readonly email box on the password view.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth` 
- **Initial State:** `window.getAuthState().step === 'email'`, clean session (unauthenticated)
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Test email string variants (valid, malformed, padded)
  - `[EXPECTED_CLEAN_EMAIL]`: Expected normalized email output
  - `[BUTTON_STATE]`: Expected disabled attribute state (`disabled` / `enabled`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 1 - Email Pre-check and Syntax Sanitization

  Background:
    Given the user navigates to "[APP_URL]/#/auth"
    And localStorage is cleared of all auth tokens
    And the auth state step is "email"

  @sanity @validation @positive
  Scenario Outline: Valid email formats enable submission and normalize properly
    When the user types "<input_email>" into the email field "#auth-email-input"
    Then the continue button ".auth-form button.auth-btn-primary" should be enabled
    When the user clicks the continue button or presses Enter
    Then the view should transition to step "signin_password"
    And the readonly email element ".readonly-email-box .email-text" should display "<normalized_email>"
    And the internal state "window.getAuthState().email" should equal "<normalized_email>"

    Examples:
      | input_email                       | normalized_email               |
      | alex.smith@company.com            | alex.smith@company.com         |
      |   Alex.Smith@Company.COM          | alex.smith@company.com         |
      | user+tag@domain.co.uk             | user+tag@domain.co.uk          |
      |   TEST.USER@ZEO-RADAR.IO          | test.user@zeo-radar.io         |

  @negative @validation
  Scenario Outline: Malformed and incomplete email formats remain gated
    When the user types "<malformed_email>" into the email field "#auth-email-input"
    Then the continue button ".auth-form button.auth-btn-primary" should remain disabled
    And no route change or step transition should occur

    Examples:
      | malformed_email                   |
      | invalid-email                     |
      | user@                             |
      | user@domain                       |
      | user@domain..com                  |
      | @nodomain.com                     |
      | user space@domain.com             |
      |                                   |
```

---

## 5. Visual Checks
- **Heading & Subtitle:**
  - Element `h1.auth-title` contains `"What's your email?"` (or `"E-postanız nedir?"` in TR).
  - Element `p.auth-subtitle` contains `"Enter your work email to sign in or create an account."`.
- **Form Layout:**
  - Container `.auth-container` is displayed in 50/50 split mode with `.auth-form-panel` on the left and `.auth-social-panel` on the right.
  - Input `input#auth-email-input` has standard focus outline and placeholder `"name@company.com"`.
- **Button Styling:**
  - Button `.auth-form button.auth-btn-primary` renders with opacity 0.5 and `cursor: not-allowed` when disabled.
  - Transitions to full opacity and interactive pointer once email regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` passes.

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const input = document.querySelector('#auth-email-input');
  const btn = document.querySelector('.auth-form button.auth-btn-primary');
  assert(input !== null, "Email input must exist");
  assert(btn.disabled === (input.value.trim() === '' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim())));
  ```
- **State Assertions:**
  ```javascript
  const auth = window.getAuthState();
  assert(auth.step === 'email' || auth.step === 'signin_password');
  assert(auth.busy === false);
  ```
- **Network Telemetry:**
  - No network RPC or GoTrue calls should be dispatched during step 1 typing or transition to `signin_password` (client-only gating).

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-email-precheck-and-validation/`
- **Required Artifacts:**
  - `result.md`: Test execution summary, execution timestamp, duration, status (PASS/FAIL).
  - `evidence.json`: Serialized output of `input.value`, button state, and `window.getAuthState()`.
  - `screenshots/01-email-empty-state.png`: Captured initial view with disabled button.
  - `screenshots/02-email-valid-enabled.png`: Captured valid email entry with enabled button.
  - `screenshots/03-email-transition-password.png`: Captured `signin_password` view with normalized email text.
- **MacBook Execution Protocol:** Ego Browser runs on the physical MacBook host. Screenshots captured on the MacBook display (`/tmp/ego-shots/auth/case-01-*.png`) are retrieved via SCP before compiling `result.md`.
