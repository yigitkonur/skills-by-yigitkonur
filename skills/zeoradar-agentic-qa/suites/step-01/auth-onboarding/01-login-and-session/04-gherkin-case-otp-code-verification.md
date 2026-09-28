# Test Case: 6-Digit OTP Grid, Keyboard Navigation & Dirty Paste Sanitization

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-04-OTP-VERIFICATION`
- **Purpose:** Validate the 6-digit one-time password (OTP) verification grid (`#otp-digit-grid`), auto-focus progression, backspace reversal, dirty clipboard paste sanitization (stripping non-numeric chars, spaces, and hyphens), and verified code submission (`DEMO_OTP_CODE = '246810'`).

---

## 2. Tester Brief
The tester enters the OTP verification step (`otp_verify`) by requesting an email code. The tester tests manual typing across the 6 discrete digit inputs (`[data-idx="0"]` to `[data-idx="5"]`), verifies backspace navigation, tests non-numeric key rejection, tests dirty clipboard paste auto-distribution (e.g. `"  24-68 10  "` mapped cleanly to individual boxes), verifies submit button gating (only enabled when all 6 digits are populated), and submits the code to assert success spinner and session activation.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** User email entered (`alexsmith@content-mobbin.com`), switched to `otp_verify` via `"Email me a one-time code instead"`
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Test user email
  - `[OTP_CODE]`: Valid 6-digit test code (`246810`)
  - `[DIRTY_PASTE_PAYLOAD]`: Unsanitized clipboard string (`" 24-68 10 "`)
  - `[INVALID_OTP_CODE]`: Mismatched code (`999999`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 4 - OTP Digit Grid and Input Sanitization

  Background:
    Given the user is on the OTP verification screen at "[APP_URL]/#/auth"
    And the heading displays "Verify your email"
    And the grid "#otp-digit-grid" contains 6 input boxes "[data-idx='0']" to "[data-idx='5']"

  @sanity @ui @keyboard
  Scenario: Individual digit typing auto-advances focus and handles backspace
    When the user types "2" into digit box "[data-idx='0']"
    Then the value of box "[data-idx='0']" should be "2"
    And focus should automatically jump to digit box "[data-idx='1']"
    When the user presses "Backspace" in digit box "[data-idx='1']"
    Then focus should return to digit box "[data-idx='0']"
    And box "[data-idx='0']" should be cleared

  @negative @sanitization
  Scenario: Non-numeric keystrokes are rejected
    When the user focuses digit box "[data-idx='0']"
    And types "A" or special character "#"
    Then the digit box "[data-idx='0']" should remain empty
    And focus should not advance to box "[data-idx='1']"

  @positive @paste @sanitization
  Scenario Outline: Dirty clipboard pastes are sanitized and distributed
    When the user pastes "<dirty_payload>" into any digit box in "#otp-digit-grid"
    Then the 6 digit boxes should contain "<expected_digits>"
    And the internal state "window.getAuthState().otpCode.join('')" should equal "<expected_digits>"
    And focus should advance to "[data-idx='5']"
    And the submit button "#btn-otp-submit" should be enabled

    Examples:
      | dirty_payload     | expected_digits |
      |   24-68 10        | 246810          |
      | 24 68 10          | 246810          |
      | OTP: 246810       | 246810          |
      | 2-4-6-8-1-0       | 246810          |

  @positive @submission
  Scenario: Valid OTP code submission authenticates session
    Given all 6 digit boxes hold "246810"
    When the user clicks the submit button "#btn-otp-submit"
    Then the button text should change to "Verifying..."
    And the spinner ".spinner-inline" should be visible
    And upon server response the session should transition to "signed_in"
    And the user should be routed to the main workspace

  @negative @submission
  Scenario: Invalid OTP code displays rejection error
    Given all 6 digit boxes hold "999999"
    When the user clicks the submit button "#btn-otp-submit"
    Then an error banner ".auth-error-msg" should be displayed
    And the error banner should contain "unauthenticated"
    And the entered digits should remain editable in the grid
```

---

## 5. Visual Checks
- **Grid Layout:**
  - Container `#otp-digit-grid` uses CSS Grid/Flex with 6 equal-width boxes (44px wide, 52px high, 8px gap).
  - Centered numbers, font size 20px, bold weight.
- **Active Focus Ring:**
  - The currently focused digit box displays a prominent focus border (`var(--color-primary, #0ea5e9)`).
- **Submit Button State:**
  - Disabled with reduced opacity when fewer than 6 digits are filled.
  - Active button shows inline CSS spinner `.spinner-inline` during verification flight.

---

## 6. Data & Network Checks
- **DOM & Value Verification:**
  ```javascript
  const boxes = Array.from(document.querySelectorAll('.otp-digit-box'));
  assert(boxes.length === 6, "Must render exactly 6 digit boxes");
  const code = boxes.map(b => b.value).join('');
  assert(code === '246810', "Sanitized code must match fixture code");
  ```
- **State Invariant:**
  ```javascript
  const auth = window.getAuthState();
  assert(auth.otpCode.length === 6);
  assert(auth.otpCode.join('') === '246810');
  ```
- **Network Call:**
  - Dispatches `verifyOtp({ email, purpose: 'signin', code: '246810' })`.
  - HTTP 200 / `ok: true` response on correct code; HTTP 401 on incorrect code.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `04-gherkin-result-case-otp-code-verification/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, paste test results, network payload timing.
  - `evidence.json`: Value of each digit box, `getAuthState().otpCode`.
  - `screenshots/01-otp-empty-grid.png`: Initial empty 6-digit grid.
  - `screenshots/02-otp-paste-populated.png`: Sanitized paste distributed across 6 boxes.
  - `screenshots/03-otp-verifying-spinner.png`: In-flight verification button with spinner.
- **MacBook Execution Protocol:** Tests run on MacBook; screenshots fetched via `scp macbook:/tmp/ego-shots/auth/case-04-*.png ./04-gherkin-result-case-otp-code-verification/screenshots/`.
