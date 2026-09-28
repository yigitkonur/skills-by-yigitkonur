# Test Case: TC-CS-13 - Slug Collision Filtering & "Apply Slug" Synchronization

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-13`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-20` (Duplicate / Identical Slug Collision & "Apply Slug" Input State Sync)
- **Purpose:** Test alternative slug suggestion generation and application in the URL Slug Optimizer. Assert that when generating suggested alternatives, the system cleanly filters out identical duplicate matches (`s === audit.slug.toLowerCase()`) so users are never recommended their existing input slug, and verify that clicking "Apply Slug" on a suggested alternative syncs the input DOM value, updates state, pushes to history, re-evaluates the audit, and renders a confirmation toast.

---

## 2. Tester Brief
The tester will verify duplicate filtering and application mechanics:
1. Entering an ideal slug (e.g. `enterprise-generative-engine-optimization-framework`) and clicking "Audit Slug".
2. **Duplicate Collision Invariant:** The right-hand alternatives list (`.slug-alt-item`) generates candidate variations based on meaningful entities, but **never includes the exact input slug string**.
3. **"Apply Slug" Synchronization:**
   - Clicking the "Apply Slug" button on an alternative:
     - Sets `state.slugOptimizer.inputSlug = alt.slug`.
     - Pushes the new slug into `slugOptimizer.history` for undo/redo support.
     - Synchronizes the `.slug-input` value in the DOM.
     - Recalculates the Overall Score and criteria cards.
     - Displays a confirmation toast: `"Local demo slug selected: [alt.slug]"` / `"Yerel demo slug seçildi"`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Target Slug Under Test `[TARGET_SLUG]`:** `"enterprise-generative-engine-optimization-framework"`
- **Matching Result Directory:** `13-gherkin-result-case-slug-collision-deduplication-and-apply-sync/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Slug Alternative Suggestions Deduplication and Input State Synchronization

  Background:
    Given the user is in the URL Slug Optimizer
    When the user enters "[TARGET_SLUG]" into the slug input field
    And the user clicks the "Audit Slug" button
    Then the suggested alternatives list ".slug-alt-list" should render candidate items

  Scenario: Duplicate Slug Collision Filtering
    Then none of the suggested alternative slugs in ".slug-alt-item" should equal "[TARGET_SLUG]"
    And all alternative slug suggestions must be unique non-identical variations

  Scenario: Applying Alternative Slug Syncs Input, Score, and Triggers Toast
    Given at least one alternative slug item is displayed in ".slug-alt-item"
    When the user clicks the "Apply Slug" button on the first alternative
    Then the text input ".slug-input" value should immediately update to match the alternative slug
    And global state "slugOptimizer.inputSlug" should equal the alternative slug
    And a confirmation toast should appear stating the slug was selected
    And the Overall Slug Score in ".slug-score-num" should recalculate
```

---

## 5. Visual Checks
1. **Alternatives List:** Rendered as cards with slug path, score delta indicator (e.g. `+15 pts`), and action button `button.btn[data-action="apply-slug"]`.
2. **Instant Value Update:** Input field `.slug-input` updates instantaneously upon button click without page scroll or jump.
3. **Toast Confirmation:** Transient toast notification mounts and dismisses automatically.

---

## 6. Data and Network Checks
1. **Deduplication Logic:**
   ```js
   const currentInput = document.querySelector('.slug-input').value.toLowerCase();
   const alts = Array.from(document.querySelectorAll('.slug-alt-item .slug-alt-text')).map(el => el.innerText.trim().toLowerCase());
   console.assert(!alts.includes(currentInput), "REGRESSION: Duplicate slug found in suggested alternatives!");
   ```
2. **History Stack:**
   - Inspect `ContentStudioState.slugOptimizer.history`.
   - Verify `historyIndex` increments by 1.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `13-gherkin-result-case-slug-collision-deduplication-and-apply-sync/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `slug_alternatives_deduplicated.png` proving no duplicate suggestions.
  2. Capture `slug_applied_input_synced.png` showing updated input and confirmation toast.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-slug-sync/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/13-gherkin-result-case-slug-collision-deduplication-and-apply-sync/
     ```
  4. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Alternative suggestions never contain the duplicate current input slug.
- [ ] Clicking "Apply Slug" synchronizes DOM input and internal state.
- [ ] Confirmation toast appears on selection.
- [ ] Slug history updates to enable undo/redo navigation.
