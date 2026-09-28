# Test Case: Tracked Market Path Highlighting & Tooltip

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-03`
- **Purpose**: Verify that the primary tracked market country path (e.g. `svg path#tr` for Turkey) receives the active `.tracked` CSS class, renders a distinctive highlighted border stroke, and includes an embedded SVG `<title>` element displaying market volume and percentage share.

---

## 2. Tester Brief
The interactive world map highlights the brand's primary target market:
- In Turkey-scoped projects (`p.market = "TR"`), the SVG path with `id="tr"` is marked with `.tracked`.
- The `.tracked` CSS styling applies a distinct border stroke (`var(--accent)`).
- Hovering over the country path reveals an SVG `<title>` element formatted with country name, search volume, and share (e.g. `Turkey: 124.5k (48.2%)`).

The tester verifies that `#tr` has the `.tracked` class, valid coordinates, and an accessible `<title>` tag.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Active Market**: `[COUNTRY] = "TR"` (`[ISO_CODE] = "tr"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Tracked Market Country Path Highlight
  As a regional marketing manager
  I want our target market country path to be visibly highlighted on the world map
  So that I can immediately identify the geographic locus of our brand visibility.

  Scenario Outline: Validating tracked market country path styling
    Given the user is viewing the world map in the Regions pane for market "<CountryCode>"
    When the SVG map finishes rendering
    Then the country path with id "<IsoId>" should possess the class "tracked"
    And the country path should have an embedded "title" child element
    And the title text should contain "<CountryName>" and a formatted percentage

    Examples:
      | CountryCode | IsoId | CountryName |
      | TR          | tr    | Turkey      |
```

---

## 5. Visual Checks
- **Target Outline**: Path `#tr` highlighted with distinct high-contrast accent outline.
- **Native Tooltip**: Browser displays standard SVG `<title>` tooltip when hovering over Turkey.

---

## 6. Data and Network Checks
- **DOM & SVG Path Assertion**:
  ```javascript
  const trackedCheck = await js(String.raw`(() => {
    const pane = document.getElementById('mapPane');
    const svg = pane?.querySelector('svg');
    const tr = svg?.querySelector('#tr');
    const title = tr?.querySelector('title')?.textContent || '';

    return {
      hasSvg: !!svg,
      hasTr: !!tr,
      isTracked: tr ? tr.classList.contains('tracked') : false,
      titleText: title,
      titleValid: title.includes('Turkey') || title.includes('Türkiye'),
      noError: !window.__lastError
    };
  })()`);
  if (!trackedCheck.hasSvg || !trackedCheck.hasTr || !trackedCheck.isTracked || !trackedCheck.titleValid) {
    throw new Error('Tracked market path highlight assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-tracked-market-path-highlight/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of highlighted `#tr` path and tooltip captured in result directory.
  - SCP sync from MacBook to host before final test report delivery.
