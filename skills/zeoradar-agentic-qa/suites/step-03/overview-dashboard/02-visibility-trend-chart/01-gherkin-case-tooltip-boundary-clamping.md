# Test Case: Floating Tooltip Coordinate Boundary Clamping

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-06`
- **Purpose**: Verify that the floating tooltip (`div.ov-tip`) boundary clamping algorithm prevents layout overflow and clipping by enforcing a minimum left offset ($x \ge 4\text{px}$) when hovering the far-left edge, and dynamically flipping orientation to the left of the crosshair ($lx = px - tw - 14$) when approaching the right container boundary.

---

## 2. Tester Brief
Tooltips positioned dynamically near chart boundaries often bleed outside their parent containers, generating horizontal scrollbars or getting clipped.
Zeo Geo-Radar uses an adaptive boundary clamping algorithm:
1. When hovering near the extreme left ($x \approx 0$), `tip.style.left` is clamped to at least `4px` (`Math.max(4, lx)`).
2. When hovering near the extreme right ($x \approx W$), `lx + tw > wr.width - 6` triggers a flip, positioning the tooltip to the left of the crosshair line rather than the right.
3. Tooltip dismissed cleanly on `mouseleave`.

The tester simulates mouse events at extreme left and right boundaries and inspects calculated CSS `style.left`.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Chart Mode**: `state.overviewChartMode = "line"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Tooltip Coordinate Boundary Clamping
  As a user interacting with edge data points
  I want the floating tooltip to remain fully visible within the chart container
  So that edge metrics are never clipped or hidden outside the viewport.

  Scenario: Hovering extreme left edge clamps tooltip to minimum offset
    Given the user is on the Overview Dashboard in "line" chart mode
    When the user moves the cursor to the extreme left edge of "rect.ov-hit"
    Then the floating tooltip ".ov-tip" should have class "show"
    And the CSS style "left" of ".ov-tip" should be greater than or equal to 4 pixels

  Scenario: Hovering extreme right edge flips tooltip orientation
    Given the user is on the Overview Dashboard in "line" chart mode
    When the user moves the cursor to the extreme right edge of "rect.ov-hit"
    Then the floating tooltip ".ov-tip" should have class "show"
    And the total offset (left plus tooltip width) should not exceed the container width
    When the cursor leaves the chart container
    Then the tooltip should be dismissed and lose class "show"
```

---

## 5. Visual Checks
- **Tooltip Card**: `div.ov-tip` displaying date label and series metric rows.
- **Left Position**: Adequate breathing room from the left container border ($\ge 4\text{px}$).
- **Right Position**: Flips gracefully to the left side of the vertical crosshair line.

---

## 6. Data and Network Checks
- **Boundary Clamping Assertion**:
  ```javascript
  const clampCheck = await js(String.raw`(() => {
    const wrap = document.querySelector('.ov-chart-wrap');
    const hit = wrap?.querySelector('.ov-hit');
    const tip = wrap?.querySelector('.ov-tip');
    if (!wrap || !hit || !tip) return { error: 'Missing elements' };

    const wr = wrap.getBoundingClientRect();
    const hr = hit.getBoundingClientRect();

    // 1. Far Left Edge
    hit.dispatchEvent(new MouseEvent('mousemove', { clientX: hr.left + 1, clientY: hr.top + 10, bubbles: true }));
    const leftVal = parseFloat(tip.style.left) || 0;
    const clampedMin = leftVal >= 4;

    // 2. Far Right Edge
    hit.dispatchEvent(new MouseEvent('mousemove', { clientX: hr.right - 1, clientY: hr.top + 10, bubbles: true }));
    const rightVal = parseFloat(tip.style.left) || 0;
    const tipWidth = tip.offsetWidth || 132;
    const clampedMax = (rightVal + tipWidth) <= (wr.width + 10);

    return {
      clampedMin,
      clampedMax,
      leftVal,
      rightVal,
      noError: !window.__lastError
    };
  })()`);
  if (!clampCheck.clampedMin || !clampCheck.clampedMax || !clampCheck.noError) {
    throw new Error('Tooltip coordinate boundary clamping violated');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-tooltip-boundary-clamping/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of left-clamped and right-flipped tooltip states captured in result directory.
  - SCP sync from MacBook to host before logging final test report.
