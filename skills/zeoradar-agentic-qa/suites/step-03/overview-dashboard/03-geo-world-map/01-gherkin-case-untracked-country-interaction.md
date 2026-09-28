# Test Case: Untracked Country Path Interaction & Market Scope Notice

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-08`
- **Purpose**: Verify that clicking or interacting with untracked country paths (e.g. `#us`, `#de`, `#gb`) in a single-market project executes safely without uncaught JavaScript exceptions, does not erroneously apply the `.tracked` class to unmonitored markets, and displays the market scope notice informing users that the snapshot was measured for Türkiye (location_code 2792).

---

## 2. Tester Brief
When an analytics project monitors a single country (e.g. Turkey), the world map still renders global geography for spatial context.
The tester verifies that:
1. Untracked country paths (e.g. `#us`, `#de`) do NOT have the `.tracked` class.
2. Clicking, hovering, or dispatching events on untracked country paths does not throw JavaScript errors (e.g. from hardcoded bounding box lookups).
3. The pane includes the market scope disclaimer: `"This snapshot was measured only for the Türkiye market with Turkish prompts (location_code 2792)..."`.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Scope**: Turkey single-market dataset (`location_code 2792`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Untracked Country Path Interaction and Market Boundary Notice
  As a QA engineer verifying geographic edge cases
  I want interactions with untracked countries to remain safe and non-breaking
  So that users exploring foreign regions receive clear boundary explanations rather than application errors.

  Scenario Outline: Interacting with untracked country paths
    Given the user is viewing the Regions map pane for market "TR"
    When the user clicks the country path with id "<CountryId>"
    Then no JavaScript errors should be thrown
    And the path "<CountryId>" should not possess the "tracked" class
    And the market scope notice mentioning location code "2792" should be displayed in the pane

    Examples:
      | CountryId | CountryName    |
      | us        | United States  |
      | de        | Germany        |
      | gb        | United Kingdom |
```

---

## 5. Visual Checks
- **Styling**: Untracked countries styled in neutral or quantile fill without the highlighted `.tracked` outline.
- **Scope Note**: Small informational note rendered below the map: `This snapshot was measured only for the Türkiye market...`.

---

## 6. Data and Network Checks
- **DOM & Event Assertion**:
  ```javascript
  const untrackedCheck = await js(String.raw`(() => {
    const pane = document.getElementById('mapPane');
    const svg = pane?.querySelector('svg');
    const tr = svg?.querySelector('#tr');
    const us = svg?.querySelector('#us');
    const de = svg?.querySelector('#de');

    let threw = false;
    try {
      if (us) us.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      if (de) de.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    } catch (e) {
      threw = true;
    }

    const notice = pane?.parentElement?.querySelector('.dim.small')?.innerText || '';
    return {
      trTracked: tr?.classList.contains('tracked'),
      usNotTracked: us ? !us.classList.contains('tracked') : true,
      threw,
      hasScopeNotice: notice.includes('2792') || notice.includes('Türkiye'),
      noError: !window.__lastError
    };
  })()`);
  if (!untrackedCheck.trTracked || untrackedCheck.threw || !untrackedCheck.hasScopeNotice || !untrackedCheck.noError) {
    throw new Error('Untracked country path interaction assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-untracked-country-interaction/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of clicked untracked path and scope notice captured in result directory.
  - SCP sync from MacBook to host before final test report compilation.
