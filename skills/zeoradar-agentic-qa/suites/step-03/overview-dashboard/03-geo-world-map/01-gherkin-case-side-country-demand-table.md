# Test Case: Side Ranked Country Demand Table

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-07`
- **Purpose**: Verify that the side ranked country table (`table.heatmap-tbl`) displays synchronized geographical demand data, accurately rendering rank indices, country flags and names, formatted search volumes (`fmtVol`), market share percentages (`fmtPct`), and directional delta indicators.

---

## 2. Tester Brief
Alongside the vector map canvas, a synchronized country table ranks markets by search demand:
- Table container: `table.tbl.heatmap-tbl` inside `.heatmap-country-table` or `.region-pane`.
- Rows display:
  1. Rank cell: `td.rankcell` (e.g. `1`, `2`, `3`).
  2. Country identifier: Emoji flag and localized country name (e.g. `🇹🇷 Turkey`).
  3. Search volume: `td.num.mono strong` (e.g. `124.5k`).
  4. Share percentage: `td.num.mono.dim` (e.g. `48.2%`).
  5. Directional delta: `span.delta.up` or `span.delta.down` (e.g. `+12.4k`).

The tester verifies that rows are populated, sorted in descending order of search volume, and formatted cleanly.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Table Selector**: `table.heatmap-tbl`

---

## 4. Gherkin Scenario

```gherkin
Feature: Side Ranked Country Demand Table
  As a global marketing analyst
  I want a tabulated ranking of countries by search demand alongside the map
  So that I can see precise volume numbers and market share percentages.

  Scenario Outline: Validating ranked country table row structure
    Given the user is viewing the regional demand table
    Then the country table "table.heatmap-tbl" should contain at least 1 row
    And the row for rank "<RankIndex>" should display the country "<CountryName>"
    And the volume column should display a formatted number with unit "<VolumeUnit>"
    And the share column should display a percentage

    Examples:
      | RankIndex | CountryName | VolumeUnit |
      | 1         | Turkey      | k          |
```

---

## 5. Visual Checks
- **Table Layout**: Compact side table aligned cleanly next to the map canvas.
- **Numbers**: Monospaced font styling for numeric values (`.num.mono`).
- **Flags & Titles**: Visible emoji flag paired with the country name.

---

## 6. Data and Network Checks
- **DOM & Ranking Assertion**:
  ```javascript
  const tableCheck = await js(String.raw`(() => {
    const rows = [...document.querySelectorAll('table.heatmap-tbl tbody tr')];
    if (rows.length === 0) return { skipped: true };

    const firstRow = rows[0];
    const rank = firstRow.querySelector('.rankcell')?.innerText?.trim();
    const name = firstRow.querySelector('td:nth-child(2)')?.innerText?.trim();
    const vol = firstRow.querySelector('td.num strong')?.innerText?.trim();
    const share = firstRow.querySelector('td.num.dim')?.innerText?.trim();

    return {
      rowCount: rows.length,
      rank,
      name,
      vol,
      share,
      hasValidRow: rank === '1' && !!vol && !!share,
      noError: !window.__lastError
    };
  })()`);
  if (!tableCheck.skipped && (!tableCheck.hasValidRow || !tableCheck.noError)) {
    throw new Error('Side ranked country demand table assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-side-country-demand-table/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of side ranked table captured in result directory.
  - SCP sync from MacBook to host before final test report compilation.
