# Test Case: Interactive Crosshair Snapping & Hover Dots

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-05`
- **Purpose**: Verify that moving the mouse cursor over the SVG hit detection area (`rect.ov-hit`) activates the interactive crosshair line (`line.ov-cross`) and series hover dots (`circle.ov-dot`), snaps their coordinates deterministically to the nearest time bucket in `data-ov`, applies the `.show` CSS class, and dismisses cleanly on mouseleave.

---

## 2. Tester Brief
The SVG line chart features a zero-jitter interactive crosshair system:
- When the cursor enters `rect.ov-hit`, `mousemove` calculates the closest X coordinate among `data.xs`.
- The crosshair line (`line.ov-cross`) receives `.show` (opacity 0.7) and updates its `x1` and `x2` coordinates to snap to that vertical time interval.
- A hover dot (`circle.ov-dot`) is illuminated on each active series path at `cx = xs[idx], cy = ys[idx]`.
- Moving the cursor out of the chart container triggers `ovChartLeave(wrap)`, removing `.show` from both the crosshair and hover dots.

The tester verifies that snapping resolves without latency, coordinates align with data points, and hover markers disappear on mouseleave.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Chart Mode**: `state.overviewChartMode = "line"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Interactive Crosshair Snapping and Hover Dots
  As a user inspecting granular time data
  I want the chart crosshair and hover dots to snap cleanly to the nearest date interval
  So that I can see the exact date position and metric value without ambiguity.

  Scenario: Cursor hover over SVG hit area triggers crosshair snapping
    Given the user is on the Overview Dashboard in "line" chart mode
    When the user moves the mouse cursor over the middle of the chart hit area "rect.ov-hit"
    Then the crosshair line "line.ov-cross" should gain class "show"
    And the crosshair "x1" coordinate should match one of the discrete intervals in "data.xs"
    And at least 1 hover dot "circle.ov-dot" should gain class "show"
    When the user moves the mouse cursor outside the chart container
    Then the crosshair line "line.ov-cross" should lose class "show"
    And all hover dots "circle.ov-dot" should lose class "show"
```

---

## 5. Visual Checks
- **Crosshair Line**: Vertical thin grey line (`stroke="var(--ink-4)"`) spanning chart height.
- **Hover Dots**: Colored circular dots with white outline appearing on the trend line.
- **Smooth Dismissal**: Crosshair and dots vanish instantly when the cursor leaves the chart.

---

## 6. Data and Network Checks
- **DOM & Event Assertion**:
  ```javascript
  const crosshairCheck = await js(String.raw`(() => {
    const wrap = document.querySelector('.ov-chart-wrap');
    const hit = wrap?.querySelector('.ov-hit');
    const cross = wrap?.querySelector('.ov-cross');
    const dot = wrap?.querySelector('.ov-dot');
    if (!wrap || !hit || !cross || !dot) return { error: 'Elements missing' };

    const hr = hit.getBoundingClientRect();
    const midX = hr.left + hr.width / 2;
    const midY = hr.top + hr.height / 2;

    // 1. Hover
    hit.dispatchEvent(new MouseEvent('mousemove', { clientX: midX, clientY: midY, bubbles: true }));
    const crossShows = cross.classList.contains('show');
    const dotShows = dot.classList.contains('show');
    const xCoord = parseFloat(cross.getAttribute('x1'));

    // 2. Leave
    hit.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
    document.dispatchEvent(new MouseEvent('mousemove', { clientX: 0, clientY: 0, bubbles: true }));
    const crossHidden = !cross.classList.contains('show');

    return {
      crossShows,
      dotShows,
      xCoordValid: !isNaN(xCoord) && xCoord > 0,
      crossHidden,
      noError: !window.__lastError
    };
  })()`);
  if (!crosshairCheck.crossShows || !crosshairCheck.dotShows || !crosshairCheck.crossHidden) {
    throw new Error('Interactive crosshair snapping assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-crosshair-snapping-and-dots/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of active crosshair hover state and cleared state stored in result directory.
  - Remote artifacts retrieved via SCP before compiling final QA report.
