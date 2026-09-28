# Test Case: Global WCAG Keyboard Accessibility Bridge for Enter and Spacebar Activation

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-06-KEYBOARD-BRIDGE`
- **Purpose:** Verify the global WCAG keyboard accessibility bridge in `assets/radar.js` lines 6380–6405, ensuring that non-button focusable elements (`tabindex="0"`) equipped with `data-action` attributes can be activated seamlessly using either the `Enter` key or the `Space` bar, triggering their corresponding click handlers without requiring a mouse.

---

## 2. Tester Brief
The tester (human or AI agent) will tab through the DOM or programmatically focus a keyboard-navigable sidebar element (`.side-item[data-key="kb"]`), press the `Space` key, assert that the route switches to `kb` (Brand Hub), focus the language toggle in the footer (`.foot-btn.lang-btn[data-action="lang-toggle"]`), press the `Enter` key, and assert that the language toggle executes and inverts `state.lang`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, tab `"overview"`, `state.lang === "en"`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[NAV_ITEM_SELECTOR]`: Target focusable element (`.side-item[data-key="kb"]`)
  - `[FOOT_BTN_SELECTOR]`: Target focusable button (`.foot-btn.lang-btn`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Accessibility - Global Keyboard Bridge for Enter and Space Activation

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And "window.state.tab" is "overview"

  @a11y @keyboard-bridge @space @positive
  Scenario: Focusing a sidebar navigation item and pressing Space activates the tab
    When the user sets focus to the sidebar item '.side-item[data-key="kb"]'
    And the user presses the "Space" key
    Then "window.state.tab" should equal "kb"
    And the sidebar item '.side-item[data-key="kb"]' should receive class "active"
    And the Brand Hub container should be mounted

  @a11y @keyboard-bridge @enter @positive
  Scenario: Focusing a footer control and pressing Enter executes its action
    Given "window.state.lang" is "en"
    When the user sets focus to the footer element '.foot-btn.lang-btn'
    And the user presses the "Enter" key
    Then "window.state.lang" should equal "tr"
    And the language badge text should reflect "TR"
```

---

## 5. Visual Checks
- **Focus Rings:**
  - Focused element exhibits standard high-contrast focus outline or ring.
- **Immediate Reaction:**
  - Pressing `Space` or `Enter` triggers visual activation state identically to a physical mouse click.

---

## 6. Data & Network Checks
- **Bridge Invariants:**
  ```javascript
  // Bridge excludes input, textarea, and native buttons to prevent double-firing
  assert(window.state.tab === 'kb', "Space activation must transition tab to kb");
  assert(window.state.lang === 'tr', "Enter activation must toggle language to tr");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-keyboard-accessibility-bridge/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of Enter and Space activations across non-button controls.
  - `evidence.json`: Captured state transitions before and after keyboard bridge events.
  - `screenshots/06-keyboard-activated-tab.png`: Brand Hub view mounted via Spacebar activation.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-06-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
