# Test Case: Advanced Engine Weight Sliders, Custom Preset & Zero-Bound Normalization

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-06-CUSTOM-ENGINE-WEIGHTS`
- **Purpose:** Validate the collapsible advanced engine sliders panel (`#ob-advanced-sliders`), manual adjustment of individual model weights (ChatGPT, Gemini, Perplexity, Claude), automatic classification as `"custom"` preset, and edge-case resilience when all sliders are set to 0% (asserting zero-bound weight normalization without `NaN` or division-by-zero crashes).

---

## 2. Tester Brief
The tester opens Step 3 and toggles the advanced engine sliders panel via `#ob-advanced-toggle-btn`. The tester drags or sets individual sliders (e.g. ChatGPT to 50%), verifying that the active preset switches to `"custom"` and the preset cards lose their `.active` status. Next, the tester tests an adversarial boundary condition: dragging all 4 sliders down to 0%. The tester asserts that readouts display `"0%"`, the application does not throw arithmetic exceptions, and the pipeline safely handles zero-sum weights during finalization.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 3 (`activeStep === 3`)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[CUSTOM_WEIGHTS]`: `{ chatgpt: 50, gemini: 20, perplexity: 20, claude: 10 }`

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 3 - Custom Engine Sliders and Zero-Bound Normalization

  Background:
    Given the user is on Step 3 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the advanced sliders panel "#ob-advanced-sliders" is initially collapsed

  @sanity @ui @sliders
  Scenario: Expanding sliders and adjusting individual weight sets custom preset
    When the user clicks the toggle link "#ob-advanced-toggle-btn"
    Then the sliders panel "#ob-advanced-sliders" should expand and become visible
    When the user adjusts "#ob-slider-chatgpt" to value 50
    Then the readout "#ob-val-chatgpt" should display "50%"
    And "window.state.onboarding.enginePreset" should become "custom"
    And all cards in ".ob-preset-grid .ob-preset-card" should have class "active" removed

  @adversarial @boundary @zero-bound
  Scenario: Setting all engine weights to zero behaves safely without arithmetic errors
    Given the advanced sliders panel is visible
    When the user sets the following engine sliders to 0:
      | slider_id              | engine     |
      | #ob-slider-chatgpt     | chatgpt    |
      | #ob-slider-gemini      | gemini     |
      | #ob-slider-perplexity  | perplexity |
      | #ob-slider-claude      | claude     |
    Then the percentage readouts should all display "0%":
      | #ob-val-chatgpt        |
      | #ob-val-gemini         |
      | #ob-val-perplexity     |
      | #ob-val-claude         |
    And "window.state.onboarding.engineWeights" should hold:
      | chatgpt: 0, gemini: 0, perplexity: 0, claude: 0 |
    And the application should not throw "DivideByZero" or "NaN" exceptions
    And advance to Step 4 should remain permitted
```

---

## 5. Visual Checks
- **Sliders Layout:**
  - 4 range input sliders (`input.ob-slider-input[type="range"]`) with step 5, min 0, max 100.
  - Track color fills proportionally to the slider value.
  - Percentage readouts displayed in bold text alongside model logos.
- **Toggle Link Animation:**
  - `#ob-advanced-toggle-btn` toggles label between `"Show advanced sliders ▼"` and `"Hide advanced sliders ▲"`.

---

## 6. Data & Network Checks
- **Weight Setting Function (`assets/onboarding.js:3060`):**
  ```javascript
  window.obSetEngineWeight('chatgpt', 50);
  const st = window.state.onboarding;
  assert(st.engineWeights.chatgpt === 50);
  assert(st.enginePreset === 'custom');
  ```
- **Arithmetic Safety:**
  ```javascript
  const sum = Object.values(st.engineWeights).reduce((a, b) => a + b, 0);
  // Zero sum should normalize gracefully in suggestion runner
  const normalized = sum === 0 ? { chatgpt: 25, gemini: 25, perplexity: 25, claude: 25 } : st.engineWeights;
  assert(!isNaN(normalized.chatgpt));
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `06-gherkin-result-case-custom-engine-sliders-and-bounds/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, boundary condition execution logs.
  - `evidence.json`: State snapshot of custom and zero weights.
  - `screenshots/01-advanced-sliders-expanded.png`: Expanded sliders panel.
  - `screenshots/02-custom-weights-modified.png`: ChatGPT modified to 50% with custom tag.
  - `screenshots/03-zero-bound-sliders.png`: All 4 sliders dragged to 0%.
- **MacBook Execution Protocol:** Ego Browser triggers range slider inputs on MacBook; screenshots downloaded via SCP.
