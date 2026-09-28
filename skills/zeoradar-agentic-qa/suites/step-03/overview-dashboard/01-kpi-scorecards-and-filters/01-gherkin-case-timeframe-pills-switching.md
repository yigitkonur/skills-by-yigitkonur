# Test Case: In-Card Timeframe Segmented Pills & Dropdown

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-02`
- **Purpose**: Verify that switching timeframe filters using the in-card segmented pill buttons (`7d`, `14d`, `30d`, `90d`) and dropdown menu (`ovDD("range")`) updates `state.ov.range`, synchronously updates the active CSS class `.active`, and recalculates trend chart axis intervals.

---

## 2. Tester Brief
The Overview Dashboard provides in-card timeframe controls allowing users to analyze visibility over different historical horizons:
- `7d` (7 Days)
- `14d` (14 Days)
- `30d` (30 Days)
- `90d` (90 Days)

The tester verifies that clicking any segmented timeframe button (`.ov-tf-btn[data-v="<range>"]`):
1. Immediately updates `state.ov.range` to the selected timeframe.
2. Applies the `.active` class to the clicked button while removing it from peer buttons.
3. Rerenders the trend chart with updated X-axis tick intervals matching the range.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Active Workspace**: Authenticated session with an active profile bundle
- **Controls Present**: `.ov-timeframe-seg` container with 4 buttons

---

## 4. Gherkin Scenario

```gherkin
Feature: In-Card Overview Timeframe Switching
  As an analyst investigating trend patterns
  I want to switch between 7D, 14D, 30D, and 90D timeframes
  So that I can evaluate short-term volatility versus long-term visibility trajectories.

  Scenario Outline: Switching between timeframe segmented pills
    Given the user is on the Overview Dashboard
    When the user clicks the timeframe button with range "<Range>"
    Then the state property "state.ov.range" should equal "<Range>"
    And the button ".ov-tf-btn[data-v='<Range>']" should have class "active"
    And exactly 1 timeframe button should have class "active"
    And the trend chart X-axis should render date ticks corresponding to "<Range>"

    Examples:
      | Range | ExpectedTicksMin | ExpectedTicksMax |
      | 7d    | 4                | 7                |
      | 14d   | 4                | 14               |
      | 30d   | 4                | 30               |
      | 90d   | 4                | 15               |
```

---

## 5. Visual Checks
- **Segmented Strip**: `.ov-timeframe-seg` containing 4 buttons: `button.ov-tf-btn[data-action="ov-set-range"]`.
- **Active State**: The selected button receives `.ov-tf-btn.active` with high-contrast text and border.
- **Chart X-Axis Labels**: `.ov-chart .ov-ax` labels update their date strings to reflect the chosen range.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const tfCheck = await js(String.raw`(() => {
    const range = '90d';
    const btn = document.querySelector('.ov-tf-btn[data-v="' + range + '"]');
    if (btn) btn.click();
    
    const activeBtns = [...document.querySelectorAll('.ov-tf-btn.active')];
    const stateRange = window.state?.ov?.range;
    return {
      stateRange,
      activeCount: activeBtns.length,
      activeVal: activeBtns[0]?.getAttribute('data-v'),
      noError: !window.__lastError
    };
  })()`);
  if (tfCheck.stateRange !== '90d' || tfCheck.activeCount !== 1 || tfCheck.activeVal !== '90d') {
    throw new Error('Timeframe segmented switching assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-timeframe-pills-switching/`
- **Execution Model**:
  - Executed via `ego-browser nodejs` on MacBook or headless Linux runner.
  - Screenshots of each timeframe transition are captured into the result directory.
  - Remote artifacts retrieved via SCP prior to report aggregation.
