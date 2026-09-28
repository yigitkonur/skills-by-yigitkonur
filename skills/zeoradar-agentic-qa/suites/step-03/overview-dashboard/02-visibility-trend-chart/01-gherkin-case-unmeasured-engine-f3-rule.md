# Test Case: Unmeasured Engine Representation (F3 Rule)

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-04`
- **Purpose**: Verify that in Bar mode, an engine with zero responses in the current run (e.g. `Google AI Mode` unmeasured) adheres to the F3 Rule: rendering an em-dash `"–"` (`span.ov-bar-val.mono.dim`) with an explanatory tooltip (`unmeasuredEngineTitle()`) and omitting the vertical bar stick, preventing misleading conflation of "0% visibility" with "not measured".

---

## 2. Tester Brief
In AI search analytics, there is a fundamental distinction between:
1. **Measured with 0% visibility**: Prompts were evaluated on the engine, but the brand was never cited. (Renders `0%` and a minimal 4px bar stick).
2. **Unmeasured engine**: The engine was disabled, queued, or unsupported during the run. (Must render `"–"` without any bar stick).

The tester verifies that:
1. For an unmeasured engine, the bar column contains `span.ov-bar-val.mono.dim` with text `"–"`.
2. The column value has a `title` tooltip stating: `"<Engine> was not measured in this run"` / `"<Engine> bu koşuda ölçülmedi"`.
3. No `.ov-bar-stick` element is rendered inside that engine's column.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Dataset**: Run where at least one catalog engine (e.g. `Google AI Mode`) has 0 answers.

---

## 4. Gherkin Scenario

```gherkin
Feature: Unmeasured Engine Representation (F3 Rule)
  As an AI audit engineer
  I want unmeasured answer engines to be clearly distinguished from 0% visibility engines
  So that stakeholders understand when an engine was omitted from testing rather than failing to mention the brand.

  Scenario Outline: Validating F3 rule on unmeasured answer engine
    Given the user is on the Overview Dashboard in "bar" chart mode
    When the engine "<EngineName>" has 0 answered queries in the active run
    Then the bar column for "<EngineName>" should display the value "–"
    And the value element should possess class "dim"
    And the value element tooltip should state "<EngineName> was not measured in this run" or its localized equivalent
    And the bar column must not contain any ".ov-bar-stick" element

    Examples:
      | EngineName      |
      | Google AI Mode  |
```

---

## 5. Visual Checks
- **Value Element**: `<span class="ov-bar-val mono dim">–</span>` displayed in muted grey.
- **Empty Stick Slot**: Column space contains no colored vertical bar stick.
- **Tooltip**: Hovering over `"–"` reveals the explanatory unmeasured title.

---

## 6. Data and Network Checks
- **DOM & Invariant Assertion**:
  ```javascript
  const f3Check = await js(String.raw`(() => {
    // Switch to bar mode
    const barBtn = document.querySelector('[data-action="toggle-overview-mode"][data-mode="bar"]');
    if (barBtn) barBtn.click();

    const cols = [...document.querySelectorAll('.ov-bar-col')];
    const unmeasuredCols = cols.filter(c => {
      const val = c.querySelector('.ov-bar-val');
      return val && val.innerText.trim() === '–';
    });

    const violations = unmeasuredCols.filter(c => {
      const hasStick = !!c.querySelector('.ov-bar-stick');
      const title = c.querySelector('.ov-bar-val')?.getAttribute('title') || '';
      const hasValidTitle = title.includes('not measured') || title.includes('ölçülmedi');
      return hasStick || !hasValidTitle;
    });

    return {
      unmeasuredFound: unmeasuredCols.length > 0,
      violationsCount: violations.length,
      noError: !window.__lastError
    };
  })()`);
  if (f3Check.violationsCount > 0) {
    throw new Error('F3 Rule Violated: Unmeasured engine has bar stick or lacks tooltip');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-unmeasured-engine-f3-rule/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of unmeasured engine column captured into result directory.
  - Remote artifacts retrieved via SCP before compiling final QA report.
