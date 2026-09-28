# Test Case: New User Registration, Unicode Support & Consent Gating

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-03-SIGNUP-REGISTRATION`
- **Purpose:** Verify the multi-field new user registration flow (`step === 'signup_details'`), ensuring mandatory inputs (First Name, Last Name, Work Email, 8+ char Password, Terms Checkbox) are validated, full Unicode / Turkish character set support is functional, and server-side duplicate registration rejections are gracefully handled.

---

## 2. Tester Brief
The tester navigates to the account registration screen either directly or by clicking "Create an account" from the email step. The tester evaluates client-side form gating by omitting individual mandatory fields (asserting disabled submit button), enters Turkish characters (`Özgür`, `Çağlayan`, etc.) to confirm Unicode support, attempts signup with an existing registered email to assert error handling, and completes registration with an unused email to verify automatic session creation and onboarding redirection.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'signup_details'`
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[NEW_EMAIL]`: Unique non-registered email (`new-lead@zeogen.com`)
  - `[EXISTING_EMAIL]`: Pre-registered email (`alexsmith@content-mobbin.com`)
  - `[FIRST_NAME]`: User given name (Unicode: `Özgür`, `Çağan`, `Selin`)
  - `[LAST_NAME]`: User surname (Unicode: `Şahin`, `Gökçe`, `Öz`)
  - `[STRONG_PASSWORD]`: Registration password (`ZeoSignup2026!`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 3 - Account Registration and Consent Validation

  Background:
    Given the user navigates to "[APP_URL]/#/auth"
    And clicks the "Create an account" link to switch to "signup_details"
    Then the current auth step should be "signup_details"

  @negative @validation
  Scenario Outline: Incomplete registration fields keep submit button disabled
    When the user fills the signup form with:
      | Field                 | Value         |
      | #auth-signup-email    | <email>       |
      | #auth-fname-input     | <first_name>  |
      | #auth-lname-input     | <last_name>   |
      | #auth-password-signup | <password>    |
    And sets the terms checkbox "#auth-terms-cb" to "<terms_checked>"
    Then the submit button ".auth-btn-primary.full-width" should be disabled

    Examples:
      | email               | first_name | last_name | password     | terms_checked |
      | test@zeogen.com     | Selin      | Kaya      | Pass1234!    | false         |
      | test@zeogen.com     |            | Kaya      | Pass1234!    | true          |
      | test@zeogen.com     | Selin      |           | Pass1234!    | true          |
      | test@zeogen.com     | Selin      | Kaya      | short        | true          |
      | invalid-email       | Selin      | Kaya      | Pass1234!    | true          |

  @positive @i18n @unicode
  Scenario: Registration accepts Turkish and international characters
    When the user enters "[NEW_EMAIL]" into "#auth-signup-email"
    And enters "Özgür" into "#auth-fname-input"
    And enters "Çağlayan" into "#auth-lname-input"
    And enters "[STRONG_PASSWORD]" into "#auth-password-signup"
    And checks the terms checkbox "#auth-terms-cb"
    Then the submit button ".auth-btn-primary.full-width" should be enabled
    When the user clicks the submit button
    Then a new user record should be generated with names "Özgür" and "Çağlayan"
    And the session state should transition to "signed_in"
    And the user should be routed to the brand setup or onboarding wizard

  @negative @duplicate
  Scenario: Registering with an existing email displays field-level error
    When the user enters "[EXISTING_EMAIL]" into "#auth-signup-email"
    And enters "Alex" into "#auth-fname-input"
    And enters "Smith" into "#auth-lname-input"
    And enters "[STRONG_PASSWORD]" into "#auth-password-signup"
    And checks the terms checkbox "#auth-terms-cb"
    And clicks the submit button
    Then the error banner ".auth-error-msg" should be displayed
    And the error banner should contain "validation_failed" or "user_already_exists"
```

---

## 5. Visual Checks
- **Field Layout & Stepper:**
  - 4 input fields arranged vertically with consistent 16px margins.
  - Step indicator dots `.zr-step-dots` reflect progress (2 of 4 dots active).
- **Terms Checkbox Styling:**
  - Checkbox `#auth-terms-cb` custom styled with checkmark graphic.
  - Links to `"Terms of Service"` and `"Privacy Policy"` are clearly underlined and interactive.
- **Password Constraints Indicator:**
  - Placeholder or helper copy indicates minimum 8 characters requirement.

---

## 6. Data & Network Checks
- **Client Validation Logic (`assets/auth.js:212`):**
  ```javascript
  const isValid = validateEmail(auth.email) &&
                  auth.firstName.trim().length > 0 &&
                  auth.lastName.trim().length > 0 &&
                  auth.password.length >= 8 &&
                  auth.termsAccepted === true;
  assert(isValid === true, "All 5 registration gates must pass");
  ```
- **Storage & Identity Checks:**
  - User record created in `zeo-mock-auth-directory:v1` or Supabase `auth.users`.
  - Stored user metadata contains `{ firstName: "Özgür", lastName: "Çağlayan" }`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `03-gherkin-result-case-new-user-signup/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, registration payload metrics, duration.
  - `evidence.json`: Serialized auth state, created user ID (`usr_...`).
  - `screenshots/01-signup-empty-form.png`: Unfilled form with disabled CTA.
  - `screenshots/02-signup-unicode-filled.png`: Form with Turkish character entries.
  - `screenshots/03-signup-duplicate-error.png`: Error banner for pre-registered email.
- **MacBook Execution Protocol:** Screenshots taken on the MacBook gateway, then synced via `scp macbook:/tmp/ego-shots/auth/case-03-*.png ./03-gherkin-result-case-new-user-signup/screenshots/`.
