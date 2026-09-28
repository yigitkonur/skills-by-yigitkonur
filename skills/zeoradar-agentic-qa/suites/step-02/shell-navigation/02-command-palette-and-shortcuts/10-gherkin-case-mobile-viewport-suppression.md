# Test Case: Mobile Breakpoint Topbar Trigger Suppression and External Keyboard Accessibility

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-10-MOBILE-VIEWPORT-SUPPRESSION`
- **Purpose:** Verify responsive layout behavior of the Command Palette topbar trigger across viewports, asserting that on narrow/mobile viewports (< 1024px) the `.cmd-trigger-btn` button is cleanly suppressed (`display: none`) to conserve header space, while the keyboard accelerator (`⌘K` / `Ctrl+K`) remains fully functional for tablet and mobile devices with external hardware keyboards.

---

## 2. Tester Brief
The tester (human or AI agent) will resize the browser viewport to a mobile breakpoint (`390x844`), assert that `.cmd-trigger-btn` is hidden via CSS computed style `display: none`, dispatch the keyboard shortcut `Meta+K`, assert that `#cmdPaletteModal` opens normally despite the hidden topbar button, and resize back to desktop (`1440x900`) to assert that the topbar button reappears.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Viewport Sizes:** Mobile (`390x844`), Desktop (`1440x900`)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[VIEWPORT_SIZE]`: Responsive screen size under test

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Responsive Suppression and Hardware Keyboard Accessibility

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"

  @responsive @mobile @suppression
  Scenario: Mobile viewport hides topbar trigger button to conserve header space
    When the user resizes the browser viewport to width 390 and height 844
    Then the computed display of the topbar trigger ".cmd-trigger-btn" should be "none"

  @responsive @mobile @keyboard @positive
  Scenario: Keyboard shortcut remains operational on mobile viewports for external keyboards
    Given the browser viewport width is 390
    When the user triggers the keyboard shortcut "Meta+K"
    Then the command palette modal "#cmdPaletteModal" should be mounted
    And "window.state.commandPalette.isOpen" should equal true
    And the input element "#cmdPaletteInput" should have focus

  @responsive @desktop @positive
  Scenario: Desktop viewport restores visibility of the topbar trigger button
    When the user resizes the browser viewport to width 1440 and height 900
    Then the computed display of the topbar trigger ".cmd-trigger-btn" should not be "none"
```

---

## 5. Visual Checks
- **Mobile Header:**
  - Hamburger menu, brand monogram, and mode badge occupy topbar cleanly without overflowing into multiple rows.
- **Palette on Mobile:**
  - When opened via keyboard on mobile, `.cmd-modal` resizes responsively to fit within the 390px viewport width with appropriate padding.

---

## 6. Data & Network Checks
- **Computed Style Assertions:**
  ```javascript
  const triggerBtn = document.querySelector('.cmd-trigger-btn');
  if (window.innerWidth < 1024) {
    assert(window.getComputedStyle(triggerBtn).display === 'none', "Trigger button must be hidden on mobile");
  } else {
    assert(window.getComputedStyle(triggerBtn).display !== 'none', "Trigger button must be visible on desktop");
  }
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-mobile-viewport-suppression/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of responsive visibility and mobile keyboard trigger verification.
  - `evidence.json`: Captured computed styles at different viewport breakpoints.
  - `screenshots/10-mobile-header-clean.png`: Mobile topbar showing trigger suppression.
  - `screenshots/10-mobile-palette-opened.png`: Responsive command palette open on mobile.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-10-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
