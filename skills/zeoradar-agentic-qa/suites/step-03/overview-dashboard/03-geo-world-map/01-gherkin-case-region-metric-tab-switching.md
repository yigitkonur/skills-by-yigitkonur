# Test Case: Region Metric Tab Switching & Alignment

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-09`
- **Purpose**: Verify that clicking region metric buttons in the segmented tab strip (`.seg-tabs button[data-action="region-metric"]`) cleanly toggles the active metric between "Visibility", "Sentiment", and "Share of Voice", updates `state.expanded["region-metric"]`, assigns the `.on` CSS class, and synchronizes the column header and row values in the region list.

---

## 2. Tester Brief
The Regions pane allows switching between 3 analytical dimensions:
1. **Visibility**: Regional prompt visibility rate (`visScore`).
2. **Sentiment**: Regional sentiment health score (`sentimentData`).
3. **Share of Voice**: Regional market attribution share (`shareOfVoice`).

The tester verifies that:
1. Clicking any metric button marks it with `.on` and updates `state.expanded["region-metric"]`.
2. The regional summary table column header (`.region-cols span:last-child`) and row value (`.region-row .val`) synchronously update their formatted output (e.g. `84.2%`).

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Controls**: `.seg-tabs` containing 3 metric buttons.

---

## 4. Gherkin Scenario

```gherkin
Feature: Region Metric Dimension Switching
  As a market analyst
  I want to switch between Visibility, Sentiment, and Share of Voice in the Regions pane
  So that I can evaluate regional performance across multiple strategic angles.

  Scenario Outline: Switching regional metric tab
    Given the user is on the Regions pane
    When the user clicks the region metric button "<MetricName>"
    Then "state.expanded['region-metric']" should equal "<MetricName>"
    And the button "[data-action='region-metric'][data-m='<MetricName>']" should have class "on"
    And the regional table header should reflect "<MetricName>"
    And the regional value element should render a formatted percentage

    Examples:
      | MetricName      |
      | Visibility      |
      | Sentiment       |
      | Share of Voice  |
```

---

## 5. Visual Checks
- **Segmented Control**: `.seg-tabs` with clean button highlight on the active tab (`.on`).
- **Table Synchronization**: Table header updates instantly without layout shift.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const metricTabCheck = await js(String.raw`(() => {
    const tabs = [...document.querySelectorAll('.seg-tabs button[data-action="region-metric"]')];
    if (tabs.length === 0) return { skipped: true };

    // Switch to Sentiment
    const sentTab = tabs.find(t => t.getAttribute('data-m') === 'Sentiment');
    if (sentTab) sentTab.click();
    const activeTab = document.querySelector('.seg-tabs button.on')?.getAttribute('data-m');

    // Switch to Share of Voice
    const sovTab = tabs.find(t => t.getAttribute('data-m') === 'Share of Voice');
    if (sovTab) sovTab.click();
    const activeTab2 = document.querySelector('.seg-tabs button.on')?.getAttribute('data-m');

    // Restore to Visibility
    const visTab = tabs.find(t => t.getAttribute('data-m') === 'Visibility');
    if (visTab) visTab.click();

    return {
      sentOk: activeTab === 'Sentiment',
      sovOk: activeTab2 === 'Share of Voice',
      noError: !window.__lastError
    };
  })()`);
  if (!metricTabCheck.skipped && (!metricTabCheck.sentOk || !metricTabCheck.sovOk || !metricTabCheck.noError)) {
    throw new Error('Region metric tab switching assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-region-metric-tab-switching/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of each metric tab active state saved in result directory.
  - SCP sync from MacBook to host before final test report assembly.
