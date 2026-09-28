# Test Case: TC-VIS-02 - Multi-Engine Benchmark Matrix Rendering, Row Pinning & Cell Formats

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-02`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture)
- **Traceability:** Maps to Source Scenarios `VIS-04`, `VIS-18`, and `VIS-20`
- **Purpose:** Verify that the Multi-Engine Platform Benchmark Matrix (`table.tbl.aei-matrix-tbl`) accurately renders cross-engine competitive visibility percentages, pins the monitored brand in the top row with `.is-me-row` and `.aei-me-tag` ("You" / "Siz"), lists competitor brands below, displays all 5 AI engine columns (`chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode`), and correctly formats cells displaying measured percentages (`X%`), lost probes (`0%`), and unmeasured platform runs (`–` em-dash) without raising runtime exceptions.

---

## 2. Tester Brief
The tester or automated agent examines the Benchmark Matrix card (`.card.aei-matrix-card`):
1. Verify the table header renders `Brand / Competitor` as the first column, followed by 5 numeric columns for the AI platforms.
2. Confirm the first row in `tbody` is highlighted with class `.is-me-row` and displays the `.aei-me-tag` pill badge next to the brand name.
3. Validate that competitor rows are rendered below the pinned brand row.
4. Verify cell data formatting:
   - When answers exist and contain brand mentions: formats as integer percentage (e.g. `85%`).
   - When answers exist but contain zero brand mentions: formats as `0%`.
   - When no answers exist for a specific platform: formats as `–` (em-dash, Unicode `\u2013`).
5. Confirm that each cell houses `.aei-cell-score.mono` and hover drilldown icon `.aei-cell-drill`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=performance`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]` (`p.me = "[BRAND]"`)
- **Competitors:** Up to 4 competitor brands [COMPETITOR_BRANDS] (e.g. `Mitsubishi Electric`, `Samsung`, `Panasonic`, `Arçelik`)
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Engines `[ENGINE_NAME]`:** `chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode`
- **Matching Result Directory:** `02-gherkin-result-case-multi-engine-benchmark-matrix-rendering/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Multi-Engine Benchmark Matrix Rendering, Row Pinning, and Cell Edge Cases

  Background:
    Given the user is on the "performance" workspace of Zeo Geo-Radar
    And the monitored brand is "[DOMAIN]"
    Then the benchmark card ".card.aei-matrix-card" should be visible

  Scenario: Benchmark Matrix Table Structure and Header Columns
    Then the responsive container ".tbl-responsive-scroll" should wrap "table.tbl.aei-matrix-tbl"
    And the table header "thead tr" should contain 6 columns:
      | Column Index | Expected Header Text (EN) | Expected Header Text (TR) | Class  |
      | 1            | Brand / Competitor        | Marka / Rakip             |        |
      | 2            | ChatGPT                   | ChatGPT                   | num    |
      | 3            | Perplexity                | Perplexity                | num    |
      | 4            | Gemini                    | Gemini                    | num    |
      | 5            | Claude                    | Claude                    | num    |
      | 6            | Google AI Mode            | Google AI Mode            | num    |

  Scenario: Monitored Brand Row Pinning and Tagging
    When the table body "tbody" renders brand rows
    Then the first row "tbody tr:first-child" must have class "is-me-row"
    And the first row brand cell should contain a strong label with "[DOMAIN]"
    And the first row brand cell must contain ".aei-me-tag" with text "You" or "Siz"
    And all subsequent rows "tbody tr:not(.is-me-row)" should represent competitor brands without ".aei-me-tag"

  Scenario Outline: Cell Content Formatting and Edge-Case Handling
    When a cell "td.aei-matrix-cell" is rendered for "<Condition>"
    Then the cell score text in ".aei-cell-score" should match "<ExpectedDisplay>"
    And the cell should contain a drilldown indicator ".aei-cell-drill"
    And the cell data attributes "data-engine" and "data-brand" must be populated

    Examples:
      | Condition                          | ExpectedDisplay |
      | Platform with brand mentions       | ^[0-9]{1,3}%$   |
      | Platform with 0% brand visibility  | 0%              |
      | Platform with unmeasured probes    | –               |
```

---

## 5. Visual Checks
1. **Pinned Row Highlight:** `tr.is-me-row` has a distinctive background tint (e.g. `rgba(var(--accent-rgb), 0.04)`) and a bold brand name.
2. **"You / Siz" Pill:** `.aei-me-tag` is styled as a small, uppercase rounded badge with subtle borders (`font-size: 11px`, `padding: 2px 6px`).
3. **Numeric Alignment:** All engine score columns have class `.num`, ensuring right-aligned numbers and monospaced font alignment (`font-family: var(--font-mono)`).
4. **Drilldown Affordance:** `.aei-cell-drill` is visually subtle or revealed on cell hover, showing a 10px diagonal arrow (`arrowUpR`).
5. **Horizontal Overflow:** `.tbl-responsive-scroll` allows smooth touch and desktop horizontal scrolling on constrained viewports (<768px).

---

## 6. Data and Network Checks
1. **Matrix Row Generation Inspection:**
   ```js
   const rows = document.querySelectorAll("table.tbl.aei-matrix-tbl tbody tr");
   assert(rows.length >= 1, "At least own brand row must exist");
   assert(rows[0].classList.contains("is-me-row"), "First row must have is-me-row");
   ```
2. **Score Computation Check:**
   - Mentions calculation checks `a.brands[b]`, `a.directBrands[b]`, or `textMentionsBrand(a.text, b)`.
   - `scorePct = Math.round((mentions / platAnswers.length) * 100)`.
   - When `platAnswers.length === 0`, `cellScoreStr === "–"`.
3. **No Console Errors:** Inspect browser logs to ensure no `TypeError: Cannot read properties of undefined` during unprobed platform iterations.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `02-gherkin-result-case-multi-engine-benchmark-matrix-rendering/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`matrix_overview.png`, `pinned_row_badge.png`, `unmeasured_cell_emdash.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-02-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/02-gherkin-result-case-multi-engine-benchmark-matrix-rendering/screenshots/
     ```
  4. Write execution report `result.md` verifying table rows, column alignments, and cell format values.

### Pass/Fail Criteria
- [ ] Matrix renders all 5 platform columns and 1 brand column.
- [ ] Top row has `.is-me-row` and `.aei-me-tag` ("You" / "Siz").
- [ ] Cells format valid percentages, `0%`, or `–` em-dash without errors.
- [ ] Each matrix cell carries valid `data-engine` and `data-brand` attributes.
