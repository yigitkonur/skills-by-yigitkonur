# Test Case: Activity Twin Charts Comparative Switch Toggle

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-10`
- **Purpose**: Verify that clicking the comparative toggle switch (`span.ct-switch[data-action="ov-compare"]`) in an activity card toggles `state.ov.compare[chartKey]`, applies the active CSS class `.on`, and when historical data is available, renders a dashed comparison path (`stroke-dasharray="4 4"`) within the activity SVG.

---

## 2. Tester Brief
The Website Activity cards provide a toggle switch labeled "Compare bots" (or "Compare platforms"):
- Switch element: `span.ct-switch[data-action="ov-compare"][data-chart="<key>"]`
- When clicked, it mutates `state.ov.compare[key]` to `true` and receives `.ct-switch.on`.
- When comparative mode is active and comparison values (`s.prev`) exist, dashed secondary curves (`stroke-dasharray="4 4"`, `stroke-opacity=".45"`) are rendered in the SVG.

The tester verifies that clicking the switch toggles the visual `.on` state and updates the underlying comparison state.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Switch Element**: `.ct-switch[data-action="ov-compare"][data-chart="cit"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Website Activity Comparative Switch Toggle
  As a growth marketing specialist
  I want to toggle comparative overlays in activity charts
  So that I can directly compare current crawl frequency against previous periods.

  Scenario Outline: Toggling comparative switch in activity charts
    Given the user is on the Overview Dashboard
    When the user clicks the comparative switch in the "<ChartTitle>" card
    Then the switch element ".ct-switch[data-chart='<ChartKey>']" should gain class "on"
    And "state.ov.compare['<ChartKey>']" should be true
    When the user clicks the comparative switch again
    Then the switch element should lose class "on"
    And "state.ov.compare['<ChartKey>']" should be false

    Examples:
      | ChartTitle          | ChartKey |
      | AI Bot Citations    | cit      |
      | AI Referral Visits  | ref      |
```

---

## 5. Visual Checks
- **Switch Knob**: `.ct-switch` transforms to active color with sliding toggle knob.
- **Dashed Overlay**: Dashed reference curves rendered alongside primary series paths.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const switchCheck = await js(String.raw`(() => {
    const sw = document.querySelector('.ct-switch[data-action="ov-compare"][data-chart="cit"]');
    if (!sw) return { skipped: true };

    const initialOn = sw.classList.contains('on');
    sw.click();
    const toggledOn = sw.classList.contains('on');
    const stateVal = window.state?.ov?.compare?.cit;

    // Restore
    sw.click();

    return {
      initialOn,
      toggledOn,
      stateVal,
      toggledSuccessfully: initialOn !== toggledOn,
      noError: !window.__lastError
    };
  })()`);
  if (!switchCheck.skipped && (!switchCheck.toggledSuccessfully || !switchCheck.noError)) {
    throw new Error('Comparative switch toggle assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-activity-compare-switch-toggle/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of comparative switch toggled ON/OFF saved in result directory.
  - SCP sync from MacBook to host before final report logging.
