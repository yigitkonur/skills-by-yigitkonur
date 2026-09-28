# Test Case: TC-SNT-03 - Active Polarity Distribution & Multi-Engine Breakdown

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-03`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, Perception Workspace)
- **Traceability:** Maps to Source Scenarios `SNT-03` and `SNT-04`
- **Purpose:** Verify that when sufficient evaluative claims exist (total claims $\ge 3$), the system renders the active Sentiment Polarity Card (`.card.aei-sentiment-card`), displays the multi-segment polarity distribution bar (`.aei-sent-bar-wrap`) with positive (`.pos`), neutral (`.neu`), and negative (`.neg`) segments whose percentages sum exactly to 100%, and renders the per-engine sentiment breakdown list (`.aei-engine-sent-list`) with mini distribution bars for all 5 target AI platforms.

---

## 2. Tester Brief
The tester or automated agent verifies active sentiment polarity rendering:
1. Navigate to the Perception workspace with an active brand dataset (e.g. [BRAND]).
2. Inspect the main polarity bar inside `.aei-sentiment-summary`:
   - Verify green segment `.aei-sent-bar-fill.pos`.
   - Verify gray segment `.aei-sent-bar-fill.neu`.
   - Verify red segment `.aei-sent-bar-fill.neg`.
   - Assert mathematically that `posPct + neuPct + negPct === 100`.
3. Verify the metric text readouts in `.aei-sent-metrics`:
   - Positive percentage: `● [posPct]% Positive`.
   - Neutral percentage: `● [neuPct]% Neutral`.
   - Negative percentage: `● [negPct]% Negative`.
4. Inspect the per-engine breakdown list (`.aei-engine-sent-list`):
   - Exactly 5 platform rows (`.aei-eng-sent-row`) representing ChatGPT, Perplexity, Gemini, Claude, and Google AI Mode.
   - Each row displays platform label, mini distribution bar (`.aei-eng-mini-bar`), and formatted positive share (e.g. `85% pos` or `"–"` if unprobed).

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Engines `[ENGINE_NAME]`:** `chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode`
- **Matching Result Directory:** `03-gherkin-result-case-polarity-distribution-and-engine-breakdown/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Active Sentiment Polarity Distribution and Multi-Engine Breakdown

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    And the monitored brand has at least 3 verified evaluative claims
    Then the active sentiment card ".card.aei-sentiment-card:not(.aei-pending-card)" should be visible

  Scenario: Polarity Distribution Bar Segments and Mathematical Invariant
    When the polarity distribution bar ".aei-sent-bar-wrap" is rendered
    Then it should contain three visual fill segments:
      | Segment Class          | Purpose                        | Color Token   |
      | .aei-sent-bar-fill.pos  | Positive sentiment percentage  | var(--green)  |
      | .aei-sent-bar-fill.neu  | Neutral sentiment percentage   | var(--ink-4)  |
      | .aei-sent-bar-fill.neg  | Negative sentiment percentage  | var(--red)    |
    And the sum of width percentages across pos, neu, and neg must equal 100
    And the metric summary ".aei-sent-metrics" should display all 3 percentages with color bullets

  Scenario Outline: Per-Engine Breakdown Rows for All Five AI Platforms
    When the engine breakdown list ".aei-engine-sent-list" renders platform rows
    Then the list must contain a row ".aei-eng-sent-row" for platform "<PlatformLabel>"
    And the row should contain an engine label with "<PlatformLabel>"
    And the row should contain a mini distribution bar ".aei-eng-mini-bar"
    And the row readout ".mono.dim" should display a formatted percentage or "–"

    Examples:
      | PlatformKey | PlatformLabel  |
      | chat_gpt    | ChatGPT        |
      | perplexity  | Perplexity     |
      | gemini      | Gemini         |
      | claude      | Claude         |
      | aimode      | Google AI Mode |
```

---

## 5. Visual Checks
1. **Polarity Bar Wrap:** Height `10px` or `12px`, border-radius `6px`, with smooth adjacent color transitions.
2. **Segment Tooltips:** Hovering over each fill segment displays a tooltip with exact percentage (e.g. `Positive: 78%`).
3. **Engine Mini Bars:** Scaled mini distribution bars (`height: 6px`, `border-radius: 3px`) providing instant comparative density across platforms.
4. **Typography:** Monospaced, muted percentages in `.aei-eng-sent-row .mono.dim`.

---

## 6. Data and Network Checks
1. **Mathematical Sum Invariant Assertion:**
   ```js
   const posEl = document.querySelector(".aei-sent-bar-fill.pos");
   const neuEl = document.querySelector(".aei-sent-bar-fill.neu");
   const negEl = document.querySelector(".aei-sent-bar-fill.neg");
   const pos = parseFloat(posEl.style.width);
   const neu = parseFloat(neuEl.style.width);
   const neg = parseFloat(negEl.style.width);
   assert(Math.round(pos + neu + neg) === 100, "Segments must sum exactly to 100%");
   ```
2. **Platform Row Count:**
   ```js
   const rows = document.querySelectorAll(".aei-eng-sent-row");
   assert(rows.length === 5, "Must render exactly 5 engine breakdown rows");
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `03-gherkin-result-case-polarity-distribution-and-engine-breakdown/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`polarity_distribution_bar.png`, `metrics_readouts.png`, `five_engine_breakdown_rows.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-03-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/03-gherkin-result-case-polarity-distribution-and-engine-breakdown/screenshots/
     ```
  4. Write execution report `result.md` verifying percentage sums, DOM elements, and platform rows.

### Pass/Fail Criteria
- [ ] Active sentiment card mounts without `.aei-pending-card`.
- [ ] Polarity fill widths sum to 100%.
- [ ] Metrics readout displays positive, neutral, and negative figures.
- [ ] All 5 AI platforms render breakdown rows.
