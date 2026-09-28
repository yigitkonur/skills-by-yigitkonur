# Test Case: Enterprise SAML SSO Drawer, Domain Validation & IdP Routing

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-07-SAML-SSO`
- **Purpose:** Validate the expandable enterprise Single Sign-On (SAML/OIDC) drawer (`.auth-sso-drawer`), drawer toggle animation, autofocus on domain input, whitespace and empty domain button gating, and dispatch of `signInWithSSO({ domain })` for corporate identity providers.

---

## 2. Tester Brief
The tester starts at the initial email screen and clicks the "Sign in with SSO" button to expand the drawer. The tester asserts that the drawer opens dynamically, `#auth-sso-domain-input` receives focus, whitespace-only entries keep the SSO continue button disabled, entering a valid corporate domain (e.g. `acmecorp.com`) enables the button, and submitting the form calls the SSO authentication handler. The tester also tests collapsing the drawer.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** `window.getAuthState().step === 'email'`
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[CORP_DOMAIN]`: Enterprise corporate domain (`acmecorp.com`, `enterprise.com`)
  - `[WHITESPACE_DOMAIN]`: Invalid blank domain string (`"   "`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Step 1 - Enterprise SAML SSO Drawer and Domain Dispatch

  Background:
    Given the user is on the email step at "[APP_URL]/#/auth"
    And the SSO drawer ".auth-sso-drawer" is not present in the DOM

  @sanity @ui @drawer
  Scenario: Toggling SSO drawer dynamically mounts and dismisses the container
    When the user clicks the SSO button "button.auth-btn-sso"
    Then the drawer container ".auth-sso-drawer" should be rendered
    And the domain input "#auth-sso-domain-input" should have focus
    And the SSO continue button ".auth-sso-drawer button.auth-btn-primary" should be disabled
    When the user clicks the SSO button "button.auth-btn-sso" again
    Then the drawer container ".auth-sso-drawer" should be removed from the DOM

  @negative @validation
  Scenario Outline: Whitespace and empty domain inputs keep SSO submission disabled
    Given the SSO drawer is open
    When the user types "<invalid_domain>" into "#auth-sso-domain-input"
    Then the SSO continue button should be disabled

    Examples:
      | invalid_domain |
      |                |
      |      |
      |   \t           |

  @positive @submission
  Scenario: Valid corporate domain initiates SSO identity provider flow
    Given the SSO drawer is open
    When the user types "[CORP_DOMAIN]" into "#auth-sso-domain-input"
    Then the SSO continue button should become enabled
    When the user clicks the SSO continue button or presses Enter
    Then the auth client method "signInWithSSO" should be called with:
      """json
      { "domain": "[CORP_DOMAIN]" }
      """
    And the busy state "auth.busy" should become true during the IdP resolution
```

---

## 5. Visual Checks
- **SSO Button & Drawer Design:**
  - Button `button.auth-btn-sso` displays the custom keyhole/SSO SVG icon `iconSSO()`.
  - Drawer `.auth-sso-drawer` appears with smooth height expansion beneath the OAuth buttons.
  - Border and subtle inset shadow distinguishing the drawer from standard form inputs.
- **Input Placeholder:**
  - `#auth-sso-domain-input` displays placeholder `"company.com"`.

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const drawer = document.querySelector('.auth-sso-drawer');
  const domainInput = document.querySelector('#auth-sso-domain-input');
  const ssoBtn = drawer?.querySelector('button.auth-btn-primary');
  assert(drawer !== null, "Drawer must be mounted when ssoOpen is true");
  assert(ssoBtn.disabled === (!domainInput.value.trim()), "SSO submit button must be gated on trimmed domain");
  ```
- **State Property:**
  - `window.getAuthState().ssoOpen === true`.
  - `window.getAuthState().ssoDomain === '[CORP_DOMAIN]'`.
- **Network Call:**
  - Dispatches `signInWithSSO({ domain: '[CORP_DOMAIN]' })`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `07-gherkin-result-case-enterprise-saml-sso/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, DOM event logs, IdP redirect payload.
  - `evidence.json`: State of `ssoOpen`, `ssoDomain`, and button disabled attribute.
  - `screenshots/01-sso-drawer-closed.png`: Initial OAuth options.
  - `screenshots/02-sso-drawer-open-focused.png`: Expanded drawer with active focus.
  - `screenshots/03-sso-domain-filled.png`: Valid corporate domain entered and button active.
- **MacBook Execution Protocol:** Automated test run triggered on MacBook via Ego Browser; screenshots retrieved via SCP.
