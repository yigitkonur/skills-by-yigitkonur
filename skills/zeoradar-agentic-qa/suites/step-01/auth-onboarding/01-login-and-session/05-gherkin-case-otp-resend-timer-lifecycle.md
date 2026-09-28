# Test Case: 55-Second OTP Resend Cooldown, Timer Expiry & Re-dispatch

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-05-OTP-RESEND-TIMER`
- **Purpose:** Validate the 55-second OTP resend rate-limiting cooldown mechanism (`auth.resendTimer = 55`), ensure `#btn-otp-resend` remains strictly disabled during active countdown, assert that the timer element vanishes and the resend link becomes interactive upon reaching 00:00, and confirm that triggering resend dispatches a new code, displays a toast, and restarts the 55s cycle.

---

## 2. Tester Brief
The tester enters the OTP verification step and immediately inspects the resend controls. The tester verifies that the countdown displays `"00:55"` and decrements every second while the resend button is disabled. The tester then simulates timer completion (or advances time to 0 seconds), verifies that the resend button becomes clickable and the timer span is removed, clicks the resend button, and asserts that a toast notification is triggered and the timer resets to 55 seconds.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'otp_verify'`, `window.getAuthState().resendTimer === 55`
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[USER_EMAIL]`: Test user receiving the OTP code
  - `[INITIAL_TIMER]`: `"00:55"`
  - `[EXPIRED_TIMER]`: `0`

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 4 - OTP Resend Lockout and Timer Lifecycle

  Background:
    Given the user is on the OTP screen at "[APP_URL]/#/auth"
    And a fresh OTP verification code has just been dispatched to "[USER_EMAIL]"

  @sanity @timer @lockout
  Scenario: Resend button is locked during active 55-second countdown
    Then the countdown timer element "span#resend-timer" should be visible
    And the countdown timer should display "00:55"
    And the resend button "button#btn-otp-resend" should have attribute "disabled"
    When 5 seconds elapse
    Then the countdown timer text should reflect approximately "00:50"
    And the resend button should still be disabled

  @positive @cooldown @expiry
  Scenario: Timer expiry enables resend button and removes timer span
    When the countdown timer reaches 0 seconds
    Then the timer element "span#resend-timer" should no longer exist in the DOM
    And the resend button "button#btn-otp-resend" should have "disabled" equal to false
    And the resend button should have cursor "pointer"

  @positive @resend @dispatch
  Scenario: Clicking enabled resend resets timer and displays confirmation toast
    Given the resend button "button#btn-otp-resend" is enabled
    When the user clicks "button#btn-otp-resend"
    Then a new OTP code should be requested from the auth client
    And a toast notification should appear with text containing "New 6-digit verification code"
    And the resend timer "window.getAuthState().resendTimer" should reset to 55
    And the timer element "span#resend-timer" should reappear displaying "00:55"
    And the resend button should return to disabled state
```

---

## 5. Visual Checks
- **Timer Typography:**
  - Timer digits formatted in fixed-width tabular font (`font-variant-numeric: tabular-nums`) to prevent horizontal jitter during decrement.
  - Neutral muted color (`var(--color-text-muted, #94a3b8)`).
- **Interactive State Transitions:**
  - Disabled: Greyed-out text, `cursor: not-allowed`, no hover underline.
  - Enabled: Accent color (`var(--color-primary, #0ea5e9)`), underline on hover, `cursor: pointer`.

---

## 6. Data & Network Checks
- **Timer Interval Cleanup (`assets/auth.js:124`):**
  ```javascript
  const auth = window.getAuthState();
  assert(typeof auth.resendTimer === 'number');
  // When timer hits 0, timerInterval must be cleared to prevent memory leaks
  if (auth.resendTimer === 0) {
    assert(auth.timerInterval === null, "Interval must be cleared at zero");
  }
  ```
- **Network Call Assertion:**
  - Clicking resend dispatches POST to `requestOtp({ email, purpose: 'signin' })`.
  - HTTP 200 OK received.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `05-gherkin-result-case-otp-resend-timer-lifecycle/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, elapsed time measurement, interval clear proof.
  - `evidence.json`: State transitions of `resendTimer` (55 -> 0 -> 55).
  - `screenshots/01-timer-active-55s.png`: Initial countdown display with locked button.
  - `screenshots/02-timer-expired-clickable.png`: Expired timer with interactive resend link.
  - `screenshots/03-resend-toast-triggered.png`: Toast notification and reset timer.
- **MacBook Execution Protocol:** Ego Browser captures video/screenshots on the MacBook display; assets downloaded via SCP before test report generation.
