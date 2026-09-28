# Test Case: TC-OPP-12 - Mathematical Golden Trophy Gating vs Honest Diagnostic Empty State

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-12`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-19` (Golden Trophy Gating vs Honest Diagnostic Empty State Assertion)
- **Purpose:** Rigorously verify that when the opportunity backlog contains zero items (`allOpps.length === 0`), the engine strictly gates the prestigious Golden Trophy achievement banner (`.opps-achievement-banner`) behind 5 deterministic mathematical qualification criteria, and that accounts with insufficient scan depth or sub-dominant visibility are honestly presented with an informative diagnostic state card (`.opps-diagnostic-state`) with actionable remediation CTAs, preventing false positive celebration.

---

## 2. Tester Brief
The tester will verify the mathematical gating function `isQualifiedForDominantPresence(prof, allOpps)`:
1. **5 Non-Negotiable Qualification Criteria:**
   1. `metrics.promptsCount >= 5` (Adequate query cluster sampling)
   2. `metrics.answersCount >= 20` (Sufficient AI engine responses audited)
   3. `metrics.visibility >= 0.85` (Monitored brand visibility $\ge 85\%$)
   4. `metrics.citationShare >= 0.60` (Brand citation share $\ge 60\%$)
   5. `metrics.visibility >= (metrics.topCompetitorVisibility || 0)` (Outranks top tracked competitor)
2. **Qualified Scenario:** If all 5 criteria evaluate to `true`, render the Golden Trophy banner (`.opps-achievement-banner`) with `🏆` and text `"Dominant AI Presence — No citation gaps detected"` / `"Baskın Yapay Zeka Varlığı"`.
3. **Unqualified Scenario (Insufficient data or low visibility):** If any criterion fails (e.g. only 2 prompts tracked, or visibility is $45\%$), the engine **must never show the trophy**. Instead, it renders the honest diagnostic card (`.opps-diagnostic-state`) with:
   - Header explaining that measurement data is still maturing or gaps are awaiting broader scan depth.
   - CTA 1: `button[data-action="opp-open-comp-modal"]` ("Track More Competitors").
   - CTA 2: `button[data-action="tab-prompts"]` ("Expand Prompt Clusters").

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `12-gherkin-result-case-golden-trophy-qualification-vs-diagnostic-state/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Mathematical Golden Trophy Gating vs Honest Diagnostic Empty State

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the opportunity discovery algorithm yields 0 active opportunities

  Scenario Outline: Mathematical Evaluation of Empty State Presentation
    Given the monitored brand profile has metrics:
      | Metric                 | Value           |
      | Prompts Count          | <PromptsCount>  |
      | Answers Count          | <AnswersCount>  |
      | Brand Visibility       | <Visibility>    |
      | Citation Share         | <CitationShare> |
      | Top Competitor Vis     | <CompVis>       |
    When the Opportunities page renders the empty backlog
    Then the DOM should display "<ExpectedContainer>"
    And the container "<ForbiddenContainer>" should NOT exist in the DOM
    And the page should render the message "<ExpectedMessageSnippet>"

    Examples:
      | PromptsCount | AnswersCount | Visibility | CitationShare | CompVis | ExpectedContainer        | ForbiddenContainer       | ExpectedMessageSnippet                 |
      | 10           | 45           | 0.92       | 0.75          | 0.40    | .opps-achievement-banner | .opps-diagnostic-state   | Dominant AI Presence                   |
      | 2            | 8            | 0.95       | 0.80          | 0.20    | .opps-diagnostic-state   | .opps-achievement-banner | Insufficient prompt measurement sample |
      | 15           | 60           | 0.45       | 0.30          | 0.70    | .opps-diagnostic-state   | .opps-achievement-banner | Expand Prompt Clusters                 |

  Scenario: Diagnostic State Interactive Remediations
    Given an unqualified empty state is rendered with class ".opps-diagnostic-state"
    Then it should provide button "[data-action='opp-open-comp-modal']" to map additional competitors
    And it should provide button "[data-action='tab-prompts']" to expand prompt clusters
    When the user clicks "[data-action='opp-open-comp-modal']"
    Then the competitor mapping modal "#modalHolder .modal" should open cleanly
```

---

## 5. Visual Checks
1. **Golden Trophy Banner:**
   - Container `.opps-achievement-banner` has green tinted background (`rgba(16,185,129,0.05)`), emerald border (`rgba(16,185,129,0.3)`), and gold trophy emoji `🏆`.
   - Title: `"Dominant AI Presence — No citation gaps detected"`.
   - Subtitle emphasizes that the brand dominates AI search results across all tracked engines.
2. **Honest Diagnostic State:**
   - Container `.opps-diagnostic-state` has neutral surface, sparkle icon (`✨`), and clear diagnostic message.
   - Dual action buttons: "Track More Competitors" (secondary) and "Expand Prompt Clusters" (primary).
3. **Zero False Celebrations:** An account with 0 or few scans must never be congratulated with a trophy.

---

## 6. Data and Network Checks
1. **Mathematical Function Inspection:**
   ```js
   function isQualifiedForDominantPresence(prof, opps) {
     if (opps && opps.length > 0) return false;
     var m = prof.metrics || {};
     return (
       (m.promptsCount || 0) >= 5 &&
       (m.answersCount || 0) >= 20 &&
       (m.visibility || 0) >= 0.85 &&
       (m.citationShare || 0) >= 0.60 &&
       (m.visibility || 0) >= (m.topCompetitorVisibility || 0)
     );
   }
   ```
2. Verify that changing any single metric below the threshold flips the boolean return from `true` to `false`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `12-gherkin-result-case-golden-trophy-qualification-vs-diagnostic-state/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `golden_trophy_qualified.png` showing the verified trophy banner.
  2. Capture `diagnostic_state_unqualified.png` showing the honest diagnostic empty state.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-trophy/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/12-gherkin-result-case-golden-trophy-qualification-vs-diagnostic-state/
     ```
  4. Document math assertions in `result.md`.

### Pass/Fail Criteria
- [ ] Golden Trophy displays only when all 5 mathematical thresholds are satisfied.
- [ ] Partial or low-visibility empty accounts display the honest diagnostic card.
- [ ] Diagnostic card provides working CTAs to map competitors and expand prompts.
- [ ] Zero false positive trophies appear under small sample conditions.
