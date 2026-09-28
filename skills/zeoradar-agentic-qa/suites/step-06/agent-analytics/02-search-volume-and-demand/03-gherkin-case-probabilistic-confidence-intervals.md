# Case 03: Probabilistic Volume Confidence Modeling & Statistical Sampling Tiers

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-03`
- **Purpose**: Verify that the Prompt Volume estimation engine (`volComputeConfidence`) calculates mathematically sound 95% Confidence Intervals across High, Moderate, and Modeled statistical sampling tiers based on sample counts and query volumes, clamps the minimum lower bound to 10 for long-tail queries, renders the appropriate CSS tier pills (`.vol-ci-tier-high`, `.vol-ci-tier-mod`, `.vol-ci-tier-low`), and opens the Poisson methodology explanation modal upon clicking the tier badge.

## 2. Tester Brief
The tester inspects the "AI Prompt Volume (95% CI)" column in the Top 25 detected prompts table. The tester validates the mathematical accuracy of the displayed interval bounds `[lower – upper]` against the base volume for queries across all 3 tiers (>= 10,000, 3,000–9,999, and < 3,000 AIV), verifies the minimum lower bound clamp (>= 10), and clicks a confidence pill to confirm that the statistical methodology modal (`.modal.vol-method-modal`) opens with detailed Poisson sampling explanations.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Test Volume Data Points:
    - `15,000` AIV (High Tier: `±11%`, 1,840 samples)
    - `5,000` AIV (Moderate Tier: `±15%`, 650 samples)
    - `1,200` AIV (Modeled Tier: `±22%`, 180 samples)
    - `8` AIV (Edge Floor Test: lower bound clamped to 10)
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: 95% Confidence Intervals & Probabilistic Demand Tiers
  As a Quantitative SEO Researcher
  I want prompt volume numbers to include calibrated statistical confidence intervals
  So that stakeholders understand sampling variance between high-frequency and long-tail AI queries

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the Top 25 Consumer Prompts table is rendered

  Scenario Outline: Verify statistical sampling tiers and confidence margins
    Given a prompt query has estimated monthly volume "<base_volume>"
    When the confidence interval is computed via "window.volComputeConfidence"
    Then the tier key should be "<expected_tier>"
    And the margin percentage should be "<expected_margin>"
    And the registered sample count should be "<expected_samples>"
    And the tier badge class should be "<expected_badge_class>"
    And the calculated lower bound should be "<expected_lower>"
    And the calculated upper bound should be "<expected_upper>"

    Examples:
      | base_volume | expected_tier | expected_margin | expected_samples | expected_badge_class | expected_lower | expected_upper |
      | 15000       | high          | 11              | 1840             | vol-ci-tier-high     | 13350          | 16650          |
      | 5000        | moderate      | 15              | 650              | vol-ci-tier-mod      | 4250           | 5750           |
      | 1200        | modeled       | 22              | 180              | vol-ci-tier-low      | 936            | 1464           |

  Scenario: Verify minimum lower bound clamping for extreme long-tail queries
    When the confidence interval is computed for an edge volume of "8"
    Then the calculated lower bound should clamp to a minimum value of "10"
    And the upper bound should be "10"

  Scenario: Launch statistical methodology modal from table confidence pill
    When the user clicks the confidence pill ".vol-ci-pill" on any prompt row
    Then the methodology modal ".modal.vol-method-modal" should be displayed
    And the modal should describe Poisson distribution variance and sampling sizes
    When the user clicks the close action ".close[data-action='vol-close-modal']"
    Then the methodology modal should dismiss cleanly
```

## 5. Visual Checks
- **Confidence Range**: Displays in monospaced muted font `[lower – upper]` beneath the projected volume.
- **Tier Pills**: Compact chip styling (`.vol-ci-pill`) with clear percentage text (`±11%`, `±15%`, `±22%`).
- **Methodology Modal**: Clean card modal with formatted equations and sample size descriptions.

## 6. Data and Network Checks
- **Function Contract Assertions**:
  ```javascript
  const ci = window.volComputeConfidence(15000);
  assert.strictEqual(ci.tierKey, 'high');
  assert.strictEqual(ci.marginPct, 11);
  assert.strictEqual(ci.lower, 13350);
  assert.strictEqual(ci.upper, 16650);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-probabilistic-confidence-intervals/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-03-table-confidence.png`
     - `/tmp/ego-shots/tc-vol-03-methodology-modal.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-03-*.png ./02-gherkin-result-case-probabilistic-confidence-intervals/
     ```
