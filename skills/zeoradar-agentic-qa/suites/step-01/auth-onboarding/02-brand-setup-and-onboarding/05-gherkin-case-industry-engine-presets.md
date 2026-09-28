# Test Case: Industry Engine Presets Weight Allocation & Synchronized Cards

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-05-ENGINE-PRESETS`
- **Purpose:** Validate the industry engine preset card grid (`.ob-preset-grid`), verifying that selecting E-Commerce (🛍️), B2B SaaS (💻), or Finance (🏦) applies the exact model weighting distribution (across ChatGPT, Gemini, Perplexity, and Claude), synchronizes the slider values and visual readouts, and visually highlights the active card.

---

## 2. Tester Brief
The tester loads Step 3 of the onboarding wizard and locates the industry preset selection cards. The tester clicks each preset card in sequence (SaaS, Finance, E-Commerce), observing the transition of the `.active` CSS class. The tester verifies that the internal state (`state.onboarding.engineWeights`) and UI readouts (`#ob-val-chatgpt`, `#ob-val-gemini`, `#ob-val-perplexity`, `#ob-val-claude`) update instantaneously to the documented proportions.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 3 (`activeStep === 3`)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[INDUSTRY_PRESET]`: `ecommerce`, `saas`, `finance`

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 3 - Industry Engine Weighting Presets

  Background:
    Given the user is on Step 3 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the preset cards container ".ob-preset-grid" contains 3 preset cards

  @sanity @ui @presets
  Scenario Outline: Selecting an industry preset updates weights and highlights card
    When the user clicks the preset card ".ob-preset-card[data-preset='<preset_id>']"
    Then the card ".ob-preset-card[data-preset='<preset_id>']" should have class "active"
    And other preset cards should not have class "active"
    And "window.state.onboarding.enginePreset" should be "<preset_id>"
    And the engine weight state should match:
      | engine     | weight       |
      | chatgpt    | <w_chatgpt>  |
      | gemini     | <w_gemini>   |
      | perplexity | <w_ppx>      |
      | claude     | <w_claude>   |
    And the slider percentage readouts should display:
      | readout_selector        | expected_text  |
      | #ob-val-chatgpt         | <pct_chatgpt>  |
      | #ob-val-gemini          | <pct_gemini>   |
      | #ob-val-perplexity      | <pct_ppx>      |
      | #ob-val-claude          | <pct_claude>   |

    Examples:
      | preset_id  | w_chatgpt | w_gemini | w_ppx | w_claude | pct_chatgpt | pct_gemini | pct_ppx | pct_claude |
      | ecommerce  | 35        | 35       | 20    | 10       | 35%         | 35%        | 20%     | 10%        |
      | saas       | 30        | 10       | 40    | 20       | 30%         | 10%        | 40%     | 20%        |
      | finance    | 40        | 30       | 20    | 10       | 40%         | 30%        | 20%     | 10%        |
```

---

## 5. Visual Checks
- **Preset Card Highlights:**
  - Active card receives `.active` class with a distinctive brand accent outline, subtle scale transform, and check badge indicator.
  - Card titles include preset icons: E-Commerce 🛍️, B2B SaaS 💻, Finance 🏦.
- **Synchronized Slider Panel:**
  - Even if the advanced sliders panel is collapsed, its DOM values (`#ob-slider-{engine}`) and text readouts (`#ob-val-{engine}`) stay synchronized.

---

## 6. Data & Network Checks
- **Preset Switch Logic (`assets/onboarding.js:3049`):**
  ```javascript
  window.obSelectEnginePreset('saas');
  const weights = window.state.onboarding.engineWeights;
  assert(weights.perplexity === 40);
  assert(weights.chatgpt === 30);
  assert(weights.claude === 20);
  assert(weights.gemini === 10);
  ```
- **Sum Normalization:**
  - Invariants: `w_chatgpt + w_gemini + w_ppx + w_claude === 100%`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `05-gherkin-result-case-industry-engine-presets/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, preset switching performance metrics.
  - `evidence.json`: Snapshots of engine weights across all 3 presets.
  - `screenshots/01-preset-ecommerce-active.png`: E-Commerce preset selected.
  - `screenshots/02-preset-saas-active.png`: B2B SaaS preset selected with Perplexity emphasis.
  - `screenshots/03-preset-finance-active.png`: Finance preset selected.
- **MacBook Execution Protocol:** Automated test run via Ego Browser on MacBook gateway; screenshots captured and copied via SCP.
