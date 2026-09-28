# Test Case: Choropleth Heatmap Quantile Buckets

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-04`
- **Purpose**: Verify that countries across the world map are dynamically classified into 4 choropleth quantile buckets (`.heat-q1` to `.heat-q4`) based on their regional search demand ratio ($\text{ratio} = \text{share} / \max(\text{share})$), mapping correctly to design tokens: `.heat-q4` ($\ge 0.66$), `.heat-q3` ($[0.33, 0.66)$), `.heat-q2` ($[0.12, 0.33)$), and `.heat-q1` ($< 0.12$).

---

## 2. Tester Brief
The regional map visualizes search demand distribution via a 4-tier quantile choropleth scale:
- `ratio >= 0.66`: Primary markets receive `.heat-q4` (`var(--accent)`).
- `0.33 <= ratio < 0.66`: Tier 2 markets receive `.heat-q3` (`var(--pink-400)`).
- `0.12 <= ratio < 0.33`: Tier 3 markets receive `.heat-q2` (`var(--pink-200)`).
- `ratio < 0.12`: Emerging markets receive `.heat-q1` (`var(--chip-bg)`).

The tester verifies that paths across the map possess appropriate `.heat-q*` classes matching their volume proportions in the country dataset.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Dataset**: Country volume distribution dataset.

---

## 4. Gherkin Scenario

```gherkin
Feature: Choropleth Heatmap Quantile Classification
  As an international expansion lead
  I want country paths on the world map to be color-coded into 4 quantile buckets based on demand
  So that I can immediately differentiate top-tier demand markets from emerging territories.

  Scenario Outline: Validating choropleth quantile bucket assignment
    Given the user is viewing the regional heatmap
    When the demand ratio for a country falls into the range "<RatioRange>"
    Then the corresponding SVG country path should have the class "<ExpectedClass>"
    And the fill color should match the token "<ColorToken>"

    Examples:
      | RatioRange     | ExpectedClass | ColorToken      |
      | ratio >= 0.66  | heat-q4       | var(--accent)   |
      | 0.33 to 0.66   | heat-q3       | var(--pink-400) |
      | 0.12 to 0.33   | heat-q2       | var(--pink-200) |
      | ratio < 0.12   | heat-q1       | var(--chip-bg)  |
```

---

## 5. Visual Checks
- **Choropleth Color Gradation**: Visual gradient across the map ranging from deep purple/pink (`.heat-q4`) to soft lavender (`.heat-q2`) and subtle background chip color (`.heat-q1`).
- **Legend**: Color bar or quantile indicators reflecting the 4 tiers.

---

## 6. Data and Network Checks
- **DOM & Class Assertion**:
  ```javascript
  const choroplethCheck = await js(String.raw`(() => {
    const svg = document.querySelector('#mapPane svg, #volHeatmapHost svg');
    if (!svg) return { error: 'Map SVG not found' };

    const q4 = svg.querySelectorAll('.heat-q4').length;
    const q3 = svg.querySelectorAll('.heat-q3').length;
    const q2 = svg.querySelectorAll('.heat-q2').length;
    const q1 = svg.querySelectorAll('.heat-q1').length;

    return {
      q4Count: q4,
      q3Count: q3,
      q2Count: q2,
      q1Count: q1,
      hasQuantiles: (q4 + q3 + q2 + q1) > 0,
      noError: !window.__lastError
    };
  })()`);
  if (!choroplethCheck.hasQuantiles || !choroplethCheck.noError) {
    throw new Error('Choropleth quantile classification assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-choropleth-quantile-classification/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of choropleth map color tiers saved in result directory.
  - SCP sync from MacBook to host before final test report assembly.
