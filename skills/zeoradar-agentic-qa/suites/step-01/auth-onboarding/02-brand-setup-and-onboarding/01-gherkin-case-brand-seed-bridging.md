# Test Case: Brand Setup Seed Phase, Storage Bridging & Redirection

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-01-SEED-BRIDGING`
- **Purpose:** Validate the initial brand seed collection screen in the authentication flow (`auth.step === 'brand_setup'`), ensuring Brand Name and Website Domain inputs are captured, validated, persisted to `state.onboardingSeed`, and successfully forwarded to the guided onboarding wizard (`/#/onboarding`).

---

## 2. Tester Brief
The tester enters the brand setup seed step either after signing up as a user without existing workspaces or by calling `window.routeZeroWorkspaceToBrandSetup()`. The tester verifies that the submit button is disabled when the domain is empty, enters brand details (e.g. `"[BRAND]"`, `"https://www.[DOMAIN]"`), submits the form, and asserts that `state.onboardingSeed` is populated and the browser is routed to `/#/onboarding`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'brand_setup'`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[BRAND]`: Brand display name (e.g. `"[BRAND]"`)
  - `[WEBSITE_URL]`: Target website URL (`"https://www.[DOMAIN]"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Seed - Brand Setup Bridging from Auth

  Background:
    Given the user is on the brand setup screen at "[APP_URL]/#/auth"
    And the heading "h1.auth-title" displays "Start tracking your brand"
    And inputs "#auth-brand-name" and "#auth-brand-domain" are visible

  @negative @validation
  Scenario: Submit button remains disabled when website domain is empty
    When the user enters "[BRAND]" into "#auth-brand-name"
    And leaves "#auth-brand-domain" completely empty
    Then the continue button "button.auth-btn-primary.full-width" should be disabled

  @positive @submission @routing
  Scenario Outline: Providing brand name and domain creates seed and bridges to wizard
    When the user types "<brand>" into "#auth-brand-name"
    And types "<domain_url>" into "#auth-brand-domain"
    Then the continue button "button.auth-btn-primary.full-width" should become enabled
    When the user clicks the continue button or submits the form
    Then "window.state.onboardingSeed" should hold:
      | property | value        |
      | brand    | <brand>      |
      | domain   | <domain_url> |
    And the application should navigate to "[APP_URL]/#/onboarding"
    And the onboarding wizard should hydrate with the provided seed

    Examples:
      | brand       | domain_url                   |
      | [BRAND]  | https://www.[DOMAIN]   |
      | Ramp        | https://ramp.com             |
      | Linear      | https://linear.app           |
```

---

## 5. Visual Checks
- **Form Layout & Guidance Bullets:**
  - Title reads: `"Start tracking your brand"` (or `"Markanızı izlemeye başlayın"` in TR).
  - Guidance bullet list `.guidance-bullets` contains 3 checklist items with checkmark icon `"✓"`.
  - Input `#auth-brand-domain` shows placeholder `"https://company.com"`.
- **Button Styling:**
  - Full-width button with label `"Create workspace & continue →"`.

---

## 6. Data & Network Checks
- **State Persistence Assertion (`assets/auth.js:1331`):**
  ```javascript
  const seed = window.state.onboardingSeed;
  assert(seed !== null && typeof seed === 'object', "onboardingSeed must be populated in state");
  assert(seed.brand === '[BRAND]');
  assert(seed.domain === 'https://www.[DOMAIN]');
  ```
- **Router Event:**
  - Calls `window.location.hash = '#/onboarding'`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-brand-seed-bridging/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, navigation timing, seed object dump.
  - `evidence.json`: State snapshot of `window.state.onboardingSeed` and `window.state.auth`.
  - `screenshots/01-brand-setup-seed-empty.png`: Initial brand setup form.
  - `screenshots/02-brand-setup-seed-filled.png`: Populated brand name and domain.
  - `screenshots/03-onboarding-wizard-landed.png`: Successful landing on Step 1 of wizard.
- **MacBook Execution Protocol:** Ego Browser drives test on MacBook gateway host; evidence retrieved via SCP.
