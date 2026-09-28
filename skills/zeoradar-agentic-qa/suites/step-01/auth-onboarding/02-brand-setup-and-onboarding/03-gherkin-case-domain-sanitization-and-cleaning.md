# Test Case: Dirty Domain Sanitization (Protocols, Auth, Ports, Paths)

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-03-DOMAIN-SANITIZATION`
- **Purpose:** Validate the domain cleaning engine (`obCleanDomain(raw)`) in Step 3 (`#ob-domain-input`), verifying that complex, dirty URI inputs (schemes `http://`/`https://`, user authentication `user:pass@`, port numbers `:8080`, paths `/app/dashboard`, query strings `?ref=ad`, and trailing dots) are sanitized to a canonical host domain, the domain status badge switches to `.verified`, and the favicon probe updates.

---

## 2. Tester Brief
The tester navigates to Step 3 of the onboarding wizard and targets the primary domain input field (`#ob-domain-input`). The tester inputs a series of dirty, malformed, or fully-qualified URIs containing protocols, basic authentication credentials, port numbers, trailing paths, query strings, and trailing dots. The tester verifies that upon debounce (250ms), the internal state and UI reflection clean the domain to the bare hostname, the domain verification badge displays `.verified`, and Google S2 favicon service is triggered for the cleaned domain.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** `window.state.onboarding.activeStep === 3`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[DIRTY_URI]`: Input URI string with extra protocol/port/query elements
  - `[CLEAN_DOMAIN]`: Expected sanitized hostname output

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 3 - Domain Cleaning and Sanitization Engine

  Background:
    Given the user is on Step 3 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the domain input "#ob-domain-input" is visible

  @sanity @sanitization
  Scenario Outline: Dirty and fully-qualified URIs are sanitized to canonical hostnames
    When the user types "<raw_input>" into "#ob-domain-input"
    And waits 300 milliseconds for input debounce
    Then the cleaned domain in "window.obCleanDomain('<raw_input>')" should be "<expected_clean>"
    And the domain verification badge "#ob-domain-status-badge" should acquire class "verified"
    And the favicon image in "#ob-domain-favicon-slot" should point to Google S2 favicon service for "<expected_clean>"

    Examples:
      | raw_input                                                     | expected_clean   |
      | https://[DOMAIN]                                        | [DOMAIN]   |
      | http://www.[DOMAIN]/                                    | www.[DOMAIN] |
      | https://admin:secret123@[DOMAIN]:8443/search?q=hotel    | [DOMAIN]   |
      | [DOMAIN]:8080                                           | [DOMAIN]   |
      |   HTTPS://Ramp.COM:3000/app/dashboard#top                     | ramp.com         |
      | example.com.                                                  | example.com      |
```

---

## 5. Visual Checks
- **Domain Status Badge:**
  - Initially empty or displaying `.checking` spinner during typing.
  - Switches to `.verified` with green checkmark icon and text `"✓ Verified"` or `"✓ Valid Domain"`.
- **Favicon Slot:**
  - Displays 16x16 favicon image fetched from `https://www.google.com/s2/favicons?domain=<clean>&sz=32`.
  - Gracefully renders default globe icon if the favicon cannot be loaded.

---

## 6. Data & Network Checks
- **Sanitizer Function Assertion (`assets/onboarding.js:68`):**
  ```javascript
  assert(typeof window.obCleanDomain === 'function', "obCleanDomain must be available");
  assert(window.obCleanDomain('https://user:pass@[DOMAIN]:8080/path?q=1#top') === '[DOMAIN]');
  ```
- **State Property:**
  ```javascript
  const lv = window.state.onboarding.live;
  assert(lv.form.domain === '[DOMAIN]');
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `03-gherkin-result-case-domain-sanitization-and-cleaning/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, regex sanitization matrix, latency measurements.
  - `evidence.json`: Raw input strings vs sanitized output strings.
  - `screenshots/01-domain-dirty-input.png`: Dirty URI entered in `#ob-domain-input`.
  - `screenshots/02-domain-cleaned-badge.png`: Verified status badge and favicon rendered.
- **MacBook Execution Protocol:** Ego Browser captures field and badge state on MacBook; downloaded via SCP.
