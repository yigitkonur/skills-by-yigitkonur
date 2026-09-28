# Case 06: Non-Linear Square Root Scale Boundaries & Extreme Skew Defense

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-06`
- **Purpose**: Verify that the non-linear square root scaling algorithm (`MAXH * Math.sqrt(v / max)`) in the volume chart visualizer defends against division-by-zero errors when total volumes are zero, clamps negative inputs to prevent `NaN`, enforces a strict minimum 4px element size so low-volume bars remain visible and interactive, and prevents low-market-share platforms from collapsing into invisibility under extreme skew (e.g. 50,000 queries on ChatGPT vs 50 on Claude).

## 2. Tester Brief
The tester injects edge volume values into the chart rendering pipeline: all-zero volumes (`max = 0`), negative volumes, and an extreme volume skew scenario (ChatGPT = 50,000, Perplexity = 10,000, Claude = 50). The tester checks that `sqrtScale` returns `0` rather than `NaN` or `Infinity`, verifies that zero-volume bars render with a clamped minimum height of 4px, and proves that Claude's low-volume bar renders at >= 6px with an interactive hover tooltip rather than vanishing below 1px as it would under linear scaling.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Dimensions: `BASE = 218`, `TOP = 24`, `MAXH = 194`
  - Test Scenarios:
    1. Zero Volume: `v = 0, max = 0`
    2. Negative Volume: `v = -100`
    3. Extreme Skew: `v = 50, max = 50,000`
- **Prerequisites**:
  - Keyword Workspace active.

## 4. Gherkin Scenario

```gherkin
Feature: Non-Linear Square Root Scale & Extreme Skew Resilience
  As a Data Visualization Engineer
  I want non-linear scaling to maintain visual legibility across extreme platform skews
  So that long-tail or nascent AI engines remain visible alongside dominant market leaders

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the SVG volume chart "svg.vol-svg-chart" is rendered in Keyword Workspace

  Scenario: Defend against zero max volume without division-by-zero errors
    When the chart is provided with all zero platform volumes (maxTotal = 0)
    Then the square root scale function should return 0
    And the rendered SVG rect elements should clamp to minimum height "4px"
    And the DOM should not contain "NaN" or "Infinity" attribute values

  Scenario: Sanitize negative volume inputs to prevent NaN calculations
    When a negative volume value "-100" is processed by the volume sanitizer
    Then the sanitized output should be clamped to 0
    And "Math.sqrt" should not evaluate a negative number

  Scenario: Preserve visibility under extreme volume skew (50,000 vs 50)
    Given an extreme volume skew scenario with ChatGPT at 50,000 and Claude at 50
    When the square root scale is computed for Claude (50 out of 50,000)
    Then linear scaling would produce an invisible height below 1px
    And square root scaling should produce a visual height greater than or equal to 6px
    And the Claude SVG rect element should be interactive
    And hovering over the Claude bar should reveal tooltip "Claude: 50"
```

## 5. Visual Checks
- **Low-Volume Bar Visibility**: The smallest platform bar is easily spotted on the horizontal baseline without squinting.
- **Minimum Clamping**: Even 0-volume bars render as a subtle 4px pill/stub on the baseline.
- **SVG Integrity**: `y`, `height`, `d` attributes contain valid integers or rounded floats; no `NaN` strings.

## 6. Data and Network Checks
- **Mathematical Invariant Assertions**:
  ```javascript
  const MAXH = 194;
  const sqrtScale = (v, max) => max > 0 ? MAXH * Math.sqrt(v / max) : 0;
  assert.strictEqual(sqrtScale(0, 0), 0);
  const linearHeight = (50 / 50000) * MAXH; // 0.194px
  const sqrtHeight = Math.max(4, Math.round(sqrtScale(50, 50000))); // 6px
  assert.ok(linearHeight < 1, 'Linear height is invisible');
  assert.ok(sqrtHeight >= 6, 'Sqrt height preserves legibility');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-sqrt-scale-boundary-and-extreme-skew/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-06-extreme-skew-chart.png`
     - `/tmp/ego-shots/tc-vol-06-zero-clamped-bars.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-06-*.png ./02-gherkin-result-case-sqrt-scale-boundary-and-extreme-skew/
     ```
