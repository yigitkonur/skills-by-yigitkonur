# Case 04: Projection Model Toggling & LocalStorage Persistence

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-04`
- **Purpose**: Verify that users can toggle between the 3 statistical projection curves (`conservative`, `median`, `aggressive`), that the selected model dynamically updates the projected AI prompt volume values displayed across the application (matching lower bound, base volume, or upper bound respectively), that the active model persists across browser reloads in `localStorage` under `zeo-radar-vol-projection-model`, and that invalid or corrupted storage inputs safely fall back to `'median'`.

## 2. Tester Brief
The tester opens the Methodology Modal via `a.vol-method-th-link`, switches between the radio buttons for `conservative`, `median`, and `aggressive`, and confirms that the projected volume values in the table immediately reflect the 5th percentile lower bound, median estimate, or 95th percentile upper bound. The tester inspects `localStorage`, simulates a browser reload, confirms that `volGetProjectionModel()` restores the preference, and invokes `volSetProjectionModel()` with invalid input to verify defensive fallback to `'median'`.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Storage Key: `"zeo-radar-vol-projection-model"`
  - Allowed Models: `median` (default), `conservative`, `aggressive`
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Statistical Projection Models & Browser Persistence
  As a Marketing Forecaster
  I want to switch between conservative, median, and aggressive volume projections
  So that I can plan budgets according to best-case or risk-averse demand scenarios

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the user opens the Methodology modal ".modal.vol-method-modal"

  Scenario Outline: Select projection model and verify projected value calculations
    When the user selects projection model radio button "<model_key>"
    Then "window.volumesState.projectionModel" should be "<model_key>"
    And "localStorage" item "zeo-radar-vol-projection-model" should equal "<model_key>"
    And the projected volume for base volume "10,000" should equal "<expected_projected>"

    Examples:
      | model_key    | expected_projected |
      | conservative | 8900               |
      | median       | 10000              |
      | aggressive   | 11100              |

  Scenario: Verify persistence across simulated page reload
    Given the projection model has been saved as "conservative" in "localStorage"
    When the application state re-initializes with null projectionModel
    Then the getter function "window.volGetProjectionModel()" should return "conservative"
    And the restored UI should display conservative lower bounds

  Scenario: Defend against corrupted or unrecognized projection model inputs
    When an invalid projection model "hyper-optimistic" is passed to "window.volSetProjectionModel"
    Then the setter should sanitize the input and default to "median"
    And "localStorage" should be updated to "median"
    And "window.volGetProjectionModel()" should return "median"
```

## 5. Visual Checks
- **Methodology Radios**: Radio inputs render with distinct labels indicating Conservative (Lower 95% Bound), Median (Standard), and Aggressive (Upper 95% Bound).
- **Table Volume Numbers**: Prompt table projected volume numbers `.vol-projected-val` update immediately upon modal dismissal without full-page reloads.

## 6. Data and Network Checks
- **Storage and Calculation Assertions**:
  ```javascript
  window.volSetProjectionModel("conservative");
  assert.strictEqual(localStorage.getItem("zeo-radar-vol-projection-model"), "conservative");
  const ci = window.volComputeConfidence(10000);
  assert.strictEqual(ci.projected, ci.lower);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-projection-models-localstorage-persistence/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-04-methodology-radios.png`
     - `/tmp/ego-shots/tc-vol-04-conservative-table.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-04-*.png ./02-gherkin-result-case-projection-models-localstorage-persistence/
     ```
