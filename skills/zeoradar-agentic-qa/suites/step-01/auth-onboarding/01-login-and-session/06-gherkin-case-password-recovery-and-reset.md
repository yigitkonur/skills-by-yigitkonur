# Test Case: Full-Bleed Password Reset Flow, OTP Recovery & Eye Toggles

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-06-PASSWORD-RESET`
- **Purpose:** Validate the dedicated solo password recovery flow (`step === 'password_reset'`), including triggering via "Forgot password?", layout shift to full-bleed `.auth-solo-step` (hiding social proof panel), 6-digit recovery OTP verification, dual independent password visibility eye toggles, minimum 8-character and matching confirmation validation, and cancellation back to sign-in.

---

## 2. Tester Brief
The tester triggers password recovery from the password screen by clicking "Forgot password?". The tester observes the transition to `password_reset` and the full-bleed solo mode (`.auth-solo-step`). The tester verifies that the new password and confirm password inputs have independent eye toggle buttons, tests mismatched and short passwords (asserting that submit remains disabled), enters valid matching passwords with the recovery OTP, submits to update credentials, and verifies cancellation behavior.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'signin_password'`, email populated
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Target user email (`alexsmith@content-mobbin.com`)
  - `[RECOVERY_OTP]`: Recovery code (`246810`)
  - `[NEW_PASSWORD]`: New strong password (`BrandNewPass2026!`)
  - `[MISMATCHED_PASSWORD]`: Differing confirmation string (`DifferentPass2026!`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 5 - Password Recovery and Solo View Gating

  Background:
    Given the user is on the password screen at "[APP_URL]/#/auth"
    And the current auth step is "signin_password"

  @sanity @navigation @layout
  Scenario: Triggering recovery transitions to solo view and hides social panel
    When the user clicks the "Forgot password?" link "button.forgot-pwd-link"
    Then the auth step should change to "password_reset"
    And the page wrapper ".auth-page-wrapper" should acquire class "auth-solo-step"
    And the container ".auth-container" should have class "auth-solo"
    And the social proof panel ".auth-social-panel" should not be visible in the viewport
    And the heading "h1.auth-title" should display "Reset your password"

  @positive @ui @eye-toggles
  Scenario: Dual password fields feature independent visibility toggles
    Given the user is on step "password_reset"
    When the user enters "[NEW_PASSWORD]" into "#reset-pwd-input"
    And enters "[NEW_PASSWORD]" into "#reset-pwd-confirm"
    Then both password inputs should have attribute 'type="password"'
    When the user clicks the first eye toggle button
    Then "#reset-pwd-input" should have attribute 'type="text"'
    And "#reset-pwd-confirm" should remain 'type="password"'
    When the user clicks the second eye toggle button
    Then "#reset-pwd-confirm" should also change to 'type="text"'

  @negative @validation
  Scenario Outline: Incomplete or mismatched passwords keep submit disabled
    Given the user is on step "password_reset"
    And the recovery OTP boxes hold "<otp_digits>"
    When the user types "<new_pwd>" into "#reset-pwd-input"
    And types "<confirm_pwd>" into "#reset-pwd-confirm"
    Then the save button "button.auth-btn-primary.full-width" should be disabled

    Examples:
      | otp_digits | new_pwd            | confirm_pwd        | reason             |
      | 246810     | Pass2026!          | Mismatched2026!    | passwords mismatch |
      | 246810     | Short1!            | Short1!            | less than 8 chars  |
      | 12345      | BrandNewPass2026!  | BrandNewPass2026!  | incomplete OTP (5) |
      |            | BrandNewPass2026!  | BrandNewPass2026!  | missing OTP        |

  @positive @submission
  Scenario: Valid OTP and matching new passwords update credentials
    Given the user is on step "password_reset"
    When the user enters "246810" into the recovery OTP grid
    And enters "[NEW_PASSWORD]" into "#reset-pwd-input"
    And enters "[NEW_PASSWORD]" into "#reset-pwd-confirm"
    Then the save button "button.auth-btn-primary.full-width" should be enabled
    When the user clicks the save button
    Then the auth client should update the password
    And a success toast should appear
    And the user should be routed to the authenticated application

  @positive @cancellation
  Scenario: Cancel link returns cleanly to signin password step
    Given the user is on step "password_reset"
    When the user clicks "button.cancel-reset-link" or "button.auth-back-link"
    Then the view should revert to step "signin_password"
    And the solo view class "auth-solo-step" should be removed
    And the social proof panel should be restored
```

---

## 5. Visual Checks
- **Full-Bleed Center Card:**
  - In solo mode, `.auth-card-content` is horizontally centered with maximum width 470px.
  - Social testimonials panel `.auth-social-panel` has `display: none`.
- **Dual Password Inputs:**
  - Both `#reset-pwd-input` and `#reset-pwd-confirm` display their own interactive `.eye-toggle-btn`.
- **Cancellation Controls:**
  - Back arrow `.auth-back-link` at top left.
  - Sub-link `button.cancel-reset-link` at the bottom of the card.

---

## 6. Data & Network Checks
- **Validation Rule Verification (`assets/auth.js:219`):**
  ```javascript
  const auth = window.getAuthState();
  const valid = auth.otpCode.join('').length === 6 &&
                auth.resetPassword.length >= 8 &&
                auth.resetConfirmPassword.length >= 8 &&
                auth.resetPassword === auth.resetConfirmPassword;
  assert(valid === true);
  ```
- **Network Call:**
  - Dispatches `updateUser({ password: '[NEW_PASSWORD]' })` or mock equivalent.
  - Resolves with `ok: true`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `06-gherkin-result-case-password-recovery-and-reset/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, field validation matrix, submission latency.
  - `evidence.json`: State snapshot of reset fields and visibility flags.
  - `screenshots/01-reset-solo-layout.png`: Full-bleed centered layout with OTP and dual password fields.
  - `screenshots/02-reset-eye-toggles.png`: One field masked, one field unmasked.
  - `screenshots/03-reset-success-toast.png`: Password updated success notification.
- **MacBook Execution Protocol:** Ego Browser drives headless browser on MacBook host, downloading visual evidence via SCP.
