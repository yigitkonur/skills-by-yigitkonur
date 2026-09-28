# Test Case: User Profile Popover Identity Display, Account & Settings Deep Navigation

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-06-PROFILE-FLYOUT-NAV`
- **Purpose:** Verify the User Profile flyout menu (`assets/radar.js` lines 5350–5365), ensuring that clicking the profile trigger (`.profile-trigger[data-action="profile-menu"]`) renders `.profile-popover` inside `#profileMenuHolder`, displays user identity details (name, email, role badge), and provides functional deep-navigation links to Account Settings (`[data-tab="account"]`) and App Settings (`[data-tab="settings"]`).

---

## 2. Tester Brief
The tester (human or AI agent) will click `.profile-trigger` in the sidebar footer, assert that `.profile-popover` opens, verify that user name (`"[USER_NAME]"`), email (`"[USER_EMAIL]"`), and role badge are rendered, click the `"Account Settings"` item, assert that the popover closes and the view navigates to `/[SLUG]/account`, and repeat for `"App Settings"`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, profile popover closed
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[USER_NAME]`: Expected display name (`Alex Smith`)
  - `[USER_EMAIL]`: Expected email address (`[USER_EMAIL]`)
  - `[TARGET_TAB]`: Navigation destination (`account`, `settings`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Profile Flyout - Identity Verification and Deep Navigation Links

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And "window.state.profileMenuOpen" is false

  @profile @identity @navigation @positive
  Scenario Outline: Opening profile popover displays identity and navigates to target tab
    When the user clicks the profile trigger ".profile-trigger"
    Then the profile popover ".profile-popover" should be displayed in "#profileMenuHolder"
    And the element ".profile-name" should contain "[USER_NAME]"
    And the element ".profile-email" should contain "[USER_EMAIL]"

    When the user clicks the profile menu item '.menu-item[data-tab="<target_tab>"]'
    Then "window.state.profileMenuOpen" should equal false
    And "window.state.tab" should equal "<target_tab>"
    And the URL path should update to "/[SLUG]/<target_tab>"
    And the view container for "<target_tab>" should be mounted

    Examples:
      | target_tab |
      | account    |
      | settings   |
```

---

## 5. Visual Checks
- **Profile Card Presentation:**
  - Initials monogram `"AS"` or avatar image is displayed.
  - Role badge `"Owner"` (or `"Sahip"`) renders with distinct border/pill style.
- **Link Hover & Focus:**
  - Menu items highlight with pointer cursor on hover.

---

## 6. Data & Network Checks
- **DOM & State Assertions:**
  ```javascript
  const pop = document.querySelector('.profile-popover');
  assert(pop !== null, "Profile popover must be mounted");
  assert(window.state.profileMenuOpen === true, "profileMenuOpen must be true");
  // After clicking link:
  assert(window.state.profileMenuOpen === false, "profileMenuOpen must reset to false");
  assert(window.state.tab === '<target_tab>', "Tab must match target");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-profile-flyout-navigation-links/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of identity data and link navigation.
  - `evidence.json`: Captured profile menu DOM tree and router transitions.
  - `screenshots/06-profile-popover-open.png`: View of opened profile popover.
  - `screenshots/06-account-settings-loaded.png`: Account settings view loaded from profile link.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-06-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
