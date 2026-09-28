# Test Case: Profile Flyout Outside-Click Dismissal & Home Workspace Catalog Navigation

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-12-PROFILE-DISMISS-HOME-NAV`
- **Purpose:** Verify outside-click dismissal of the User Profile popover (`assets/radar.js` lines 5205–5210) ensuring clicks outside `.profile-popover` close the menu and reset `state.profileMenuOpen = false`, and assert that clicking the workspace catalog entry (`.menu-item[data-action="goto-home"]`) resets `state.slug = null`, closes the flyout, and navigates to the root Home catalog view (`/`).

---

## 2. Tester Brief
The tester (human or AI agent) will click `.profile-trigger` to open `.profile-popover`, click on `.main` outside the popover, assert that the popover closes and `#profileMenuHolder` is emptied, reopen the popover, click the workspace card row with `data-action="goto-home"`, assert that `window.state.slug` becomes `null`, verify navigation to `/`, and assert that `renderHome()` mounts the brand catalog.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, profile popover opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test

---

## 4. Gherkin Scenario

```gherkin
Feature: Profile Flyout - Outside-Click Dismissal and Workspace Catalog Navigation

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user clicks the profile trigger ".profile-trigger"
    Then the profile popover ".profile-popover" should be displayed

  @profile @dismissal @outside-click @positive
  Scenario: Clicking outside the profile popover dismisses the flyout
    When the user clicks the main viewport container ".main"
    Then the profile popover ".profile-popover" should be removed from the DOM
    And "window.state.profileMenuOpen" should equal false
    And "#profileMenuHolder" should have 0 children

  @profile @navigation @home @positive
  Scenario: Clicking the workspace catalog link navigates to the home index
    Given the profile popover is open
    When the user clicks the workspace link ".profile-popover .menu-item[data-action='goto-home']"
    Then "window.state.slug" should be null
    And "window.state.profileMenuOpen" should equal false
    And the URL path should equal "/"
    And the home catalog container ".home-grid" should be displayed in the viewport
```

---

## 5. Visual Checks
- **Dismissal Cleanliness:**
  - Clicking outside closes popover without lingering shadows or frozen menu borders.
- **Home Navigation:**
  - Transition to Home view renders the multi-workspace card grid.

---

## 6. Data & Network Checks
- **State Invariants:**
  ```javascript
  assert(window.state.profileMenuOpen === false, "profileMenuOpen must be false after dismissal");
  // After goto-home:
  assert(window.state.slug === null, "state.slug must be null for home catalog");
  assert(window.location.pathname === '/' || window.location.hash === '#/', "URL must be root");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-profile-flyout-dismissal-and-workspace-nav/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of outside-click dismissal and home catalog transition.
  - `evidence.json`: Captured `window.state` transitions.
  - `screenshots/12-profile-outside-click.png`: View after outside-click dismissal.
  - `screenshots/12-home-catalog-navigated.png`: Home catalog view displayed after navigation.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-12-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
