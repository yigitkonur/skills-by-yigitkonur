# Test Case: Explicit Tri-Mode Theme Selection (Light/Dark/System) via Profile Popover

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-02-PROFILE-THEME-SUBMENU`
- **Purpose:** Verify granular theme selection via the user profile popover (`.profile-popover`), ensuring that selecting explicit options (`.theme-opt[data-action="set-theme"][data-theme="{mode}"]`) allows users to select between all three supported modes (`light`, `dark`, and `system`), updates active checkmark indicators (`.check-icon`), and persists the preference.

---

## 2. Tester Brief
The tester (human or AI agent) will click the profile trigger in the sidebar footer (`.profile-trigger`), assert that `.profile-popover` opens displaying the theme submenu with 3 options, click `.theme-opt[data-theme="dark"]`, verify that dark mode applies and the checkmark moves to dark, click `.theme-opt[data-theme="system"]`, and verify that `state.theme` switches to `"system"` with dynamic OS matching.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Profile popover opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[THEME_MODE]`: Selected theme option (`light`, `dark`, `system`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Preferences - Explicit Tri-Mode Theme Selection via Profile Submenu

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user clicks the profile trigger ".profile-trigger"
    Then the profile popover ".profile-popover" should be visible
    And the theme submenu ".theme-submenu" should display 3 options:
      | light  |
      | dark   |
      | system |

  @theme @profile @submenu @positive
  Scenario Outline: Clicking a theme option in profile popover applies mode and moves checkmark
    When the user clicks the theme option '.theme-opt[data-theme="<target_theme>"]'
    Then "window.state.theme" should equal "<target_theme>"
    And the element '.theme-opt[data-theme="<target_theme>"]' should have class "active"
    And the element '.theme-opt[data-theme="<target_theme>"] .check-icon' should be visible
    And localStorage item "zeo_theme" should equal "<target_theme>"

    Examples:
      | target_theme |
      | dark         |
      | light        |
      | system       |
```

---

## 5. Visual Checks
- **Submenu Presentation:**
  - Theme choices render horizontally or vertically in `.theme-submenu` with distinct icons (sun, moon, gear/monitor).
  - Selected theme displays checkmark icon `✓` (`.check-icon`).

---

## 6. Data & Network Checks
- **State & DOM Assertions:**
  ```javascript
  const activeOpt = document.querySelector('.theme-opt.active');
  assert(activeOpt !== null, "An active theme option must exist in profile popover");
  assert(activeOpt.getAttribute('data-theme') === window.state.theme, "Active opt must match state.theme");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-theme-selection-profile-submenu/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of profile theme submenu interactions.
  - `evidence.json`: Captured active options and state dumps.
  - `screenshots/02-profile-theme-submenu.png`: Profile popover showing active theme checkmark.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-02-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
