# Test Case: Single-Market Regional Filter Scoping Fallback

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-11`
- **Purpose**: Verify that when a brand dataset is measured for a single geographic market (e.g. `[COUNTRY] = "TR"`, location_code 2792), applying foreign or unrepresented regional filters does not crash the Overview Dashboard, but safely renders graceful em-dash `"–"` fallbacks and presents the single-market scope notice.

---

## 2. Tester Brief
Datasets collected under single-market research plans contain queries and citations tied to a specific location code (e.g. Turkey location_code 2792).
Filtering by a different region (e.g. `US` or `DE`) yields zero query answers.
The system must:
1. Handle zero matching regional queries without uncaught runtime exceptions.
2. Render em-dash `"–"` across KPI scorecards.
3. Keep the dashboard shell and navigation intact.
4. Display the informative market scope note in the regional overview: `"This snapshot was measured only for the Türkiye market with Turkish prompts (location_code 2792)..."`.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Profile Scope**: Single-market dataset (`p.market = "TR"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Single-Market Regional Filter Fallback
  As an international marketer
  I want the dashboard to handle unrepresented regional filter queries gracefully
  So that filtering for markets outside the current snapshot provides clear feedback without system errors.

  Scenario Outline: Scoping dashboard to unrepresented geographic markets
    Given the user is on the Overview Dashboard for a dataset measured for "<DefaultMarket>"
    When a regional filter for an unrepresented country "<ForeignMarket>" is applied
    Then the Overview dashboard should render without crashing
    And the KPI scorecard values should display "–"
    And no uncaught errors should appear in the browser console
    And a market scope notice mentioning "<DefaultMarket>" should inform the user of the single-market boundary

    Examples:
      | DefaultMarket | ForeignMarket |
      | TR            | US            |
      | TR            | DE            |
      | TR            | GB            |
```

---

## 5. Visual Checks
- **Overview Container**: `.overview-container` remains rendered without blank white screen.
- **Scorecards**: `.aei-kpi-card` values display `"–"`.
- **Scope Notice**: Notice text rendered in muted font: `This snapshot was measured only for the Türkiye market...`.

---

## 6. Data and Network Checks
- **DOM & Crash Assertion**:
  ```javascript
  const regionTest = await js(String.raw`(() => {
    const savedState = window.state?.activeProfileBundle;
    const dummyProfile = Object.assign({}, savedState, { answers: [] });
    
    let crashed = false;
    let html = '';
    try {
      html = window.renderOverviewPage(dummyProfile);
      crashed = !html || html.length < 100;
    } catch (e) {
      crashed = true;
    }

    return { crashed, htmlLength: html.length, noError: !window.__lastError };
  })()`);
  if (regionTest.crashed || !regionTest.noError) {
    throw new Error('Overview crashed on zero-answer regional scope');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-single-market-regional-filter/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux VM.
  - Screenshots of zero-answer regional scope and scope notice saved in result directory.
  - SCP sync from MacBook to host before final report delivery.
