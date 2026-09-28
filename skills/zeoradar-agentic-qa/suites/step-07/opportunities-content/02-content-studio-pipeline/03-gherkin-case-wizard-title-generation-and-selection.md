# Test Case: TC-CS-03 - Wizard Step 2 Candidate Title Generation & Selection

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-03`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-03` (Candidate Title Generation & Selection)
- **Purpose:** Test Step 2 of the 4-Step Content Creation Wizard, validating that clicking "Generate Titles" yields 4 high-probability candidate title options, that the first candidate is flagged with the `Recommended ⚡` badge, that clicking a title card updates the active selection in state and DOM, and that clicking "⟳ Suggest new titles" cycles through fresh candidate variations.

---

## 2. Tester Brief
The tester will verify the candidate title generation and selection cycle:
1. With Step 1 populated with a topic, clicking the primary action button triggers `ContentStudio.wizardGenerateTitles()`.
2. The wizard transitions to Step 2 (`Titles`).
3. 4 candidate title cards (`.wiz-title-card-sidebar`) render in the left sidebar column.
4. The first candidate title automatically receives the `Recommended ⚡` badge (`.wiz-rec-badge`).
5. Clicking a different title card applies the `.active` class to that card, updates the radio input, and changes the selected title preview.
6. Clicking "⟳ Suggest new titles" (`button.wiz-suggest-btn`) re-invokes title generation, replacing the 4 cards with a new batch of candidate headlines.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Pre-Selected Topic:** `"Enterprise AI Search Optimization"`
- **Matching Result Directory:** `03-gherkin-result-case-wizard-title-generation-and-selection/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Wizard Step 2 Candidate Title Generation and Cycling

  Background:
    Given the user is on Step 1 of the Content Creation Wizard
    And a valid topic is selected
    When the user clicks "Generate Candidate Titles"
    Then the wizard should advance to Step 2
    And the title cards container should be visible

  Scenario: Candidate Title Generation and Recommended Badge Assertion
    Then exactly 4 title cards ".wiz-title-card-sidebar" should be rendered
    And the first title card should contain the badge ".wiz-rec-badge" with text "Recommended ⚡"
    And the first title card should have class "active"
    And the preview headline in the main pane should display the text of the first title

  Scenario: Interactive Title Selection and Suggestion Cycling
    When the user clicks the second title card ".wiz-title-card-sidebar:nth-child(2)"
    Then the second title card should receive class "active"
    And the first title card should lose class "active"
    And the wizard state "wizard.selectedTitleIndex" should update to 1
    
    When the user clicks the "Suggest new titles" button ".wiz-suggest-btn"
    Then the candidate title cards should refresh with a new batch of 4 titles
    And the first title card of the new batch should have the Recommended badge
```

---

## 5. Visual Checks
1. **Title Cards:** `.wiz-title-card-sidebar` has border, padding, and subtle radio indicator circle.
2. **Active Card Highlight:** `.wiz-title-card-sidebar.active` displays an accent border (e.g. `2px solid var(--accent)` or `var(--primary)`) and filled radio circle.
3. **Recommended Badge:** `.wiz-rec-badge` displays in gold/amber with lightning bolt icon (`⚡`).
4. **Suggest Button:** `.wiz-suggest-btn` displays cycling arrow icon (`⟳`).

---

## 6. Data and Network Checks
1. **State Assertions:**
   ```js
   const wiz = window.ContentStudioState.wizard;
   console.assert(wiz.generatedTitles.length === 4, "Expected 4 generated titles");
   console.assert(wiz.selectedTitleIndex === 1, "Selected title index mismatch");
   ```
2. Title Deduplication: Assert that titles in the 4-card batch are unique strings.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `03-gherkin-result-case-wizard-title-generation-and-selection/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `titles_step2_initial.png` showing 4 title cards with Recommended badge.
  2. Capture `title_card_selected.png` showing active second title card.
  3. Capture `titles_cycled_batch.png` showing refreshed titles after clicking suggest.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/wizard-step2/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/03-gherkin-result-case-wizard-title-generation-and-selection/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] 4 distinct candidate title cards render on Step 2.
- [ ] First card has the `Recommended ⚡` badge.
- [ ] Clicking different cards updates active radio selection.
- [ ] "Suggest new titles" generates a fresh batch of titles.
