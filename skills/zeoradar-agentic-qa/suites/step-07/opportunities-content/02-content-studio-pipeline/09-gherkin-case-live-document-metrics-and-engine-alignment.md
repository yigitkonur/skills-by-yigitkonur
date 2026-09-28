# Test Case: TC-CS-09 - Live Document Metrics & AI Engine Alignment Meters

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-09`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-08` (Document Metrics & Engine Alignment)
- **Purpose:** Validate that as the user writes or edits content inside `#edContentBody`, the Content Studio real-time evaluator continuously computes document structural metrics (Words, Headings, Paragraphs, Readability Index) and updates the Overall AEO Score and 4 distinct AI Engine Alignment meters (Perplexity, ChatGPT, Claude, Gemini) in the Inspector sidebar's AEO Stats tab.

---

## 2. Tester Brief
The tester will verify real-time metric evaluation in the editor sidebar:
1. In the editor view, clicking the sidebar tab "AEO Stats" (`.ed-side-tab:nth-child(2)`) reveals document metrics.
2. The overall AEO Score (`.ed-score-num`) renders as an integer between 0 and 100.
3. Structural metrics are displayed:
   - Word count (`stats.words`)
   - Heading count (`stats.headings`)
   - Paragraph count (`stats.paragraphs`)
   - Readability index (`stats.readability`)
4. 4 AI Engine Alignment progress rows render:
   - **Perplexity:** $v = \min(98, \text{round}(\text{score} \times 1.02))$
   - **ChatGPT:** $v = \min(96, \text{round}(\text{score} \times 0.98))$
   - **Claude:** $v = \min(95, \text{round}(\text{score} \times 0.95))$
   - **Gemini:** $v = \min(97, \text{round}(\text{score} \times 1.01))$
5. Adding new paragraphs or headings into `#edContentBody` causes metrics and alignment meters to update dynamically without page refresh.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `09-gherkin-result-case-live-document-metrics-and-engine-alignment/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Live Document Metrics and 4-Engine Alignment Meters

  Background:
    Given the user is editing an article in Content Studio
    When the user clicks the "AEO Stats" tab in the editor sidebar
    Then the AEO stats panel should be visible

  Scenario: Initial AEO Score and Structural Metric Rendering
    Then the overall AEO score ".ed-score-num" should display a number between 0 and 100
    And the structural stats grid should display:
      | Stat Metric       | Selector                      |
      | Words Count       | .ed-stat-val:nth-child(1)     |
      | Headings Count    | .ed-stat-val:nth-child(2)     |
      | Paragraphs Count  | .ed-stat-val:nth-child(3)     |
      | Readability Index | .ed-stat-val:nth-child(4)     |

  Scenario Outline: AI Engine Alignment Meters Integrity
    Then the engine alignment row for "<EngineName>" should be rendered
    And its alignment score percentage should be formatted as "<ScoreFormula>"
    And its visual progress bar should have width style matching the alignment score

    Examples:
      | EngineName | ScoreFormula                         |
      | Perplexity | min(98, round(score * 1.02))%        |
      | ChatGPT    | min(96, round(score * 0.98))%        |
      | Claude     | min(95, round(score * 0.95))%        |
      | Gemini     | min(97, round(score * 1.01))%        |

  Scenario: Real-Time Dynamic Metric Recalculation on Canvas Edits
    Given the user notes the initial word count in the sidebar
    When the user types 50 additional words into "#edContentBody"
    Then the words count display in the sidebar should increment by 50
    And the engine alignment bars should update to reflect the new document length
```

---

## 5. Visual Checks
1. **Score Ring / Gauge:** Large numeric display (`.ed-score-num`) with color thresholding (Green $\ge 80$, Amber $50-79$, Red $< 50$).
2. **Alignment Bars:** 4 progress bars with brand-matched or subtle progress fill indicators.
3. **Stat Cards:** 2x2 grid of small metric cards showing numeric value and descriptive label.

---

## 6. Data and Network Checks
1. **Mathematical Formulations:**
   ```js
   var score = parseInt(document.querySelector('.ed-score-num').innerText, 10);
   var expectedPpx = Math.min(98, Math.round(score * 1.02));
   var expectedGpt = Math.min(96, Math.round(score * 0.98));
   var actualPpx = parseInt(document.querySelectorAll('.ed-engine-val')[0].innerText, 10);
   console.assert(actualPpx === expectedPpx, "Perplexity alignment score mismatch");
   ```
2. **Word Count Tokenizer:** Ensure words are split by whitespace (`/\s+/`) ignoring HTML tags.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `09-gherkin-result-case-live-document-metrics-and-engine-alignment/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `aeo_stats_sidebar_initial.png` showing score and 4 engine meters.
  2. Capture `metrics_updated_after_typing.png` showing live word count increase.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-stats/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/09-gherkin-result-case-live-document-metrics-and-engine-alignment/
     ```
  4. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] AEO score renders between 0 and 100.
- [ ] All 4 AI engines (Perplexity, ChatGPT, Claude, Gemini) have alignment meters.
- [ ] Typing in canvas immediately updates word count in sidebar.
- [ ] Formulas for engine alignment match mathematical specification.
