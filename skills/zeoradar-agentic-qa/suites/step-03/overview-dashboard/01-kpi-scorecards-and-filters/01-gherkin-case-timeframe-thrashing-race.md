# Test Case: High-Frequency Date Range Thrashing Immunity

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-03`
- **Purpose**: Verify that rapid, asynchronous clicking of timeframe pills (`7d` -> `90d` -> `14d` -> `30d`) within $< 50\text{ms}$ does not cause render race conditions, desynchronized state, duplicated axis labels, or multi-button active states.

---

## 2. Tester Brief
In high-performance single-page applications, rapid sequential user clicks on filter buttons can cause asynchronous render races or leave multiple buttons marked `.active`.
The tester simulates rapid firing of click events across all 4 timeframe options in quick succession and verifies that:
1. The final state strictly resolves to the last clicked option (`30d`).
2. Exactly one button retains the `.active` CSS class.
3. The SVG trend chart does not render duplicate overlapping date ticks.
4. No unhandled JavaScript errors or client warnings (`window.__lastError`) occur.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Rapid Click Sequence**: `["7d", "90d", "14d", "30d"]` executed without artificial pauses.

---

## 4. Gherkin Scenario

```gherkin
Feature: High-Frequency Filter Thrashing Resilience
  As an impatient user clicking controls rapidly
  I want the Overview Dashboard to handle fast sequential clicks cleanly
  So that the interface remains synchronized and does not freeze or corrupt chart axes.

  Scenario: Rapid clicking across multiple timeframe buttons in under 50ms
    Given the user is on the Overview Dashboard
    When the user clicks the timeframe buttons "7d", "90d", "14d", and "30d" in rapid succession within 50 milliseconds
    Then the final "state.ov.range" must be "30d"
    And exactly 1 timeframe button should have the "active" class
    And the active timeframe button must have "data-v" equal to "30d"
    And the SVG X-axis should contain a non-duplicated set of date labels
    And no client exceptions should be logged in "window.__lastError"
```

---

## 5. Visual Checks
- **Single Active Button**: Only `button.ov-tf-btn[data-v="30d"]` has the `.active` styling.
- **Clean SVG Chart**: No duplicated text labels or overlapping X-axis tick lines.
- **No Flicker**: Interface stabilizes smoothly without layout jitter.

---

## 6. Data and Network Checks
- **Adversarial Thrashing Script**:
  ```javascript
  const thrashTest = await js(String.raw`(() => {
    const sequence = ['7d', '90d', '14d', '30d'];
    sequence.forEach(r => {
      const btn = document.querySelector('.ov-tf-btn[data-v="' + r + '"]');
      if (btn) btn.click();
    });

    const activeBtns = [...document.querySelectorAll('.ov-tf-btn.active')];
    const axisTicks = document.querySelectorAll('.ov-chart .ov-ax');
    return {
      finalRange: window.state?.ov?.range,
      activeCount: activeBtns.length,
      activeVal: activeBtns[0]?.getAttribute('data-v'),
      axisCount: axisTicks.length,
      noError: !window.__lastError
    };
  })()`);
  if (thrashTest.finalRange !== '30d' || thrashTest.activeVal !== '30d' || thrashTest.activeCount !== 1) {
    throw new Error('High-frequency thrashing caused state desynchronization');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-timeframe-thrashing-race/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux VM.
  - Final DOM screenshot and state dump stored in the result directory.
  - Remote MacBook screenshots retrieved via SCP before report publication.
