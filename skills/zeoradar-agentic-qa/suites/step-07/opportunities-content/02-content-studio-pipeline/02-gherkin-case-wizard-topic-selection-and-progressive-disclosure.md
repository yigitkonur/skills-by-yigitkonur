# Test Case: TC-CS-02 - Wizard Step 1 Topic Selection & Progressive Disclosure

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-02`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-02` (4-Step Wizard Topic Selection)
- **Purpose:** Test Step 1 (Configuration) of the 4-Step Content Creation Wizard, validating that dependent form fields (Prompts, Target Platforms, Top-Cited Pages) are progressively locked behind an informative disclosure banner until an authoritative topic is selected via the custom searchable rich dropdown, and verifying that selecting a topic cleanly unlocks downstream inputs and enables multi-page URL chips.

---

## 2. Tester Brief
The tester will verify progressive disclosure behavior in Wizard Step 1:
1. Navigating to Workflows and clicking "Generate Content via Wizard" (`.wf-quick-card.primary`) mounts `ContentStudioState.view = "wizard"`.
2. **Initial State (Locked):** `#wizTopic` has no selection. The form displays `.wiz-disabled-banner` informing the user that topic selection is required. Dependent inputs have class `.wiz-field-disabled`.
3. Clicking `.rich-select-trigger` opens the searchable option dropdown `.rich-select-panel`.
4. Typing into the search input filters candidate topics.
5. Selecting a topic:
   - Assigns `window.ContentStudioState.wizard.topic`.
   - Dismisses `.wiz-disabled-banner`.
   - Removes `.wiz-field-disabled` from Prompts, Audience, Brand Kit, and Top-Cited Pages.
6. The tester adds URLs into `#topPageInput` via the "+ Add" button, verifying chips render with remove buttons (`.top-page-chip`) up to the maximum limit of 20 URLs.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Topic Under Test `[TOPIC]`:** E.g. `"Enterprise AI Search Visibility & Brand Grounding"`
- **Matching Result Directory:** `02-gherkin-result-case-wizard-topic-selection-and-progressive-disclosure/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: 4-Step Wizard Step 1 Topic Selection and Progressive Disclosure

  Background:
    Given the user is on the Workflows page for "[DOMAIN]"
    When the user clicks the quick card "Generate Content via Wizard"
    Then the wizard layout ".wiz-layout" should be mounted
    And the current wizard step should be 1

  Scenario: Progressive Disclosure Locks Dependent Fields Prior to Topic Selection
    Given no topic is selected in "#wizTopic"
    Then the wizard should display the banner ".wiz-disabled-banner"
    And the banner text should explain that topic selection is required to proceed
    And the target platform and prompt selection fields should have class ".wiz-field-disabled"
    And the "Generate Titles" action button should be disabled

  Scenario: Selecting Topic Unlocks Downstream Configuration and URL Chips
    When the user clicks the topic dropdown trigger ".rich-select-trigger"
    Then the searchable panel ".rich-select-panel" should open
    When the user selects the topic "[TOPIC]"
    Then the dropdown should close
    And the banner ".wiz-disabled-banner" should disappear from the DOM
    And the dependent fields should no longer have class ".wiz-field-disabled"
    
    When the user enters "https://[DOMAIN]/products" into "#topPageInput"
    And the user clicks the "+ Add" button
    Then a URL chip with class ".top-page-chip" should be added to the list
    And the chip should display "[DOMAIN]/products" and a remove button
```

---

## 5. Visual Checks
1. **Wizard Stepper:** Header displays 4 numbered steps: `1. Config` (active), `2. Titles`, `3. Preview`, `4. Generation`.
2. **Disabled Visual State:** Fields with `.wiz-field-disabled` render with 40% opacity, pointer-events disabled, and cursor `not-allowed`.
3. **Rich Select Dropdown:** Search input at top with magnifying glass icon; scrollable list of categorized topic options with subtle hover effects.
4. **URL Chips:** Rendered as inline badges with close cross (`×`), wrapping neatly without horizontal layout blowout.

---

## 6. Data and Network Checks
1. **Wizard State:**
   ```js
   const wiz = window.ContentStudioState.wizard;
   console.assert(wiz.step === 1, "Wizard step is not 1");
   console.assert(wiz.topic === "[TOPIC]", "Topic not saved in state");
   console.assert(Array.isArray(wiz.topPages), "topPages is not an array");
   ```
2. Max Limit Guard: Verify that attempting to add more than 20 chips is ignored or triggers a warning toast.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `02-gherkin-result-case-wizard-topic-selection-and-progressive-disclosure/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `wizard_step1_locked.png` showing disabled banner.
  2. Capture `topic_search_dropdown.png` showing searchable options.
  3. Capture `wizard_step1_unlocked.png` showing unlocked fields and URL chips.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/wizard-step1/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/02-gherkin-result-case-wizard-topic-selection-and-progressive-disclosure/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] Wizard launches cleanly into Step 1.
- [ ] Dependent fields remain strictly disabled until topic is chosen.
- [ ] Searchable rich-select filters and sets the topic correctly.
- [ ] Top-cited pages chips render and can be added/removed interactively.
