# Test Case: TC-CS-12 - URL Slug Optimizer 6-Criteria Audit & Penalty Formulations

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-12`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenarios `TC-CS-11` (URL Slug 6-Criteria Audit) and `TC-CS-19` (URL Slug Optimizer 6-Criteria Boundary Suite & Exact Penalty Assertions)
- **Purpose:** Test the URL Slug & SEO Metadata Optimizer (`.slug-optimizer-container`), validating its 2-column interface, real-time deterministic evaluation across all 6 mathematical criteria (Ideal Length, Meaningful Entities, Keyword Natural Language, Format & Clean Chars, Stop Words Filter, Single Topic Intent), and verifying exact penalty calculations from base score 100.

---

## 2. Tester Brief
The tester will verify the slug evaluation heuristics (`auditSlug(raw)`):
1. Navigating to Workflows and clicking "Optimize Slug" (`.wf-quick-card.secondary`) mounts `ContentStudioState.view = "slug_optimizer"`.
2. **2-Column Layout:**
   - Left: Domain prefix, `.slug-input` field, "Audit Slug" button, and 6-point criteria card list (`.slug-criteria-list`).
   - Right: Overall Score tile (0–100), rating verdict (Excellent, Good, Needs Work), and suggested alternatives.
3. **6 Deterministic Criteria & Exact Deductions:**
   - **Length (25–45 chars):** If $<25$, deducts $\min(20, 25 - \text{len}) + 5$. If $>45$, deducts $\min(20, \text{len} - 45) + 5$.
   - **Entities ($\ge 2$ meaningful):** If $<2$, deducts 14 points.
   - **Natural Language ($3–6$ words, no `--`):** If $<3$ words, deducts 14 points. If $>6$, deducts $(\text{words} - 6) \times 6 + 8$.
   - **Format (lowercase, single `-`):** Uppercase deducts 8 points. Spaces or `_` deducts 10 points. Double hyphen `--` deducts 6 points.
   - **Stop Words:** Deducts 12 points per stop word (`best`, `cheap`, `top`, `vs`, `how`, `what`, `for`, `with`, etc.).
   - **Single Intent:** Multi-intent conjunctions (`-and-`, `-or-`, `-vs-`, `-plus-`, `-with-`) deduct 10 points.
   - Score clamped strictly to $[5, 100]$.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `12-gherkin-result-case-slug-optimizer-6-criteria-audit/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: URL Slug Optimizer 6-Point Deterministic Evaluation and Scoring

  Background:
    Given the user opens the URL Slug Optimizer in Content Studio
    Then the container ".slug-optimizer-container" should be visible
    And the slug input field ".slug-input" should be ready for input

  Scenario Outline: Validating Specific Criteria Deductions
    When the user enters the slug "<TestSlug>" into ".slug-input"
    And the user clicks the "Audit Slug" button
    Then the criteria card for "<CriteriaKey>" should display status "<ExpectedCardStatus>"
    And the overall slug score should be less than or equal to "<MaxAllowedScore>"

    Examples:
      | CriteriaKey     | TestSlug                                                       | ExpectedCardStatus | MaxAllowedScore |
      | length          | ai-tips                                                        | warn               | 75              |
      | descriptiveness | a-b-c-d                                                        | fail               | 70              |
      | naturalLanguage | ai-seo                                                         | warn               | 80              |
      | format          | Best_AI--Search-Optimization-Guide                             | fail               | 65              |
      | stopWords       | best-cheap-ai-search-engines-top-guide                         | warn               | 65              |
      | singleIntent    | generative-engine-optimization-and-ranking-factors-vs-search   | warn               | 60              |

  Scenario: Perfect Slug Scores High Tier
    When the user enters the slug "enterprise-generative-engine-optimization-guide" into ".slug-input"
    And the user clicks "Audit Slug"
    Then all 6 criteria cards in ".slug-criteria-list" should display status "pass"
    And the overall score in ".slug-score-num" should be greater than or equal to 90
    And the score badge verdict should display "Excellent"
```

---

## 5. Visual Checks
1. **2-Column Responsive Layout:** Left inputs, right results; stacks vertically on mobile viewports ($< 768\text{px}$).
2. **Criteria Cards:** `.slug-crit-card` displays icon, title, description, and status color:
   - Green with checkmark for `pass`.
   - Amber with alert icon for `warn`.
   - Red with cross icon for `fail`.
3. **Score Ring:** Large numeric display (`.slug-score-num`) with color matching verdict.

---

## 6. Data and Network Checks
1. **Mathematical Accuracy Assertion:**
   ```js
   const audit = window.ContentStudio.auditSlug("best-cheap-ai-engines-vs-google");
   console.assert(audit.stops.length >= 3, "Failed to detect all stop words");
   console.assert(audit.score <= 65, "Score calculation failed to apply stop word penalties");
   ```
2. **Regex Precision:** Check that `multiIntent` pattern (`/-(and|or|vs|plus|with)-/i`) triggers accurately.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `12-gherkin-result-case-slug-optimizer-6-criteria-audit/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `slug_audit_suboptimal.png` showing multiple failing criteria cards.
  2. Capture `slug_audit_perfect_score.png` showing 100/Excellent rating.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-slug/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/12-gherkin-result-case-slug-optimizer-6-criteria-audit/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Each of the 6 criteria flags its designated violation accurately.
- [ ] Base score 100 correctly subtracts calculated penalties.
- [ ] Perfect compliant slugs achieve $\ge 90$ Excellent score.
- [ ] Clamping prevents negative scores (minimum floor 5).
