# Test Case: TC-SNT-11 - Theme Search Filtering, Segment Tabs & Full Response Modal

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-11`
- **Module:** Dedicated Sentiment Analysis Tab (`assets/radar.js`)
- **Parent Contract:** Spec 06 (Sentiment Analysis Architecture, Theme Discovery & Execution Inspection)
- **Traceability:** Maps to Source Scenarios `SNT-14`, `SNT-16`, and `SNT-26`
- **Purpose:** Verify that typing keywords into `input[data-action-input="sent-search"]` executes live, case-insensitive filtering across theme titles and individual attributes, that clicking segmentation tabs (`all`, `positive`, `negative`, `trending`) filters themes by polarity, and that clicking "View Full Response" (`button[data-action="sent-open-prompt"]`) on an example quote launches the prompt execution modal displaying complete response text.

---

## 2. Tester Brief
The tester or automated agent interacts with theme filtering controls and modal triggers:
1. Locate the filter toolbar above Section 2:
   - Segmentation tabs (`.seg-tabs button[data-action="sent-seg"]`).
   - Keyword search input (`input[data-action-input="sent-search"]`).
2. Test keyword search:
   - Type a keyword (e.g. `price` or `fiyat`).
   - Confirm only themes or attributes matching the query (case-insensitively) remain visible.
   - Clear the input and confirm all themes return.
3. Test segmentation tabs:
   - Click `Positive`: only themes with positive score $\ge 50\%$ remain.
   - Click `Negative`: only themes with negative claims or score $< 50\%$ remain.
   - Click `Trending`: only themes with $\ge 2$ claims remain.
4. Expand an attribute example quote and click `button[data-action="sent-open-prompt"]`:
   - Verify prompt execution modal mounts into `#modalHolder`.
   - Verify modal displays full AI answer text, engine metadata, and prompt query.
   - Verify modal can be dismissed cleanly.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/sentiment`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Search Keyword:** `price` or `quality`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `11-gherkin-result-case-theme-search-filtering-and-prompt-modal/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Theme Keyword Search, Polarity Segmentation, and Full Response Modal Trigger

  Background:
    Given the user is on the dedicated sentiment tab of Zeo Geo-Radar
    Then the theme control toolbar ".seg-tabs" should be visible

  Scenario Outline: Segment Tab Polarity Filtering
    When the user clicks the segment button "button[data-action='sent-seg'][data-k='<SegmentKey>']"
    Then the clicked button should have class "on"
    And all other segment buttons should not have class "on"
    And the theme list should strictly display themes matching "<SegmentKey>" criteria

    Examples:
      | SegmentKey | Expected Criteria                             |
      | all        | All extracted themes                         |
      | positive   | Themes with score >= 0.50                     |
      | negative   | Themes with negative claims or score < 0.50   |
      | trending   | Themes with 2 or more claims                  |

  Scenario: Live Keyword Search Across Themes and Attributes
    When the user types "price" into "input[data-action-input='sent-search']"
    Then only themes or attributes matching "price" case-insensitively should be visible
    And non-matching themes should be excluded from the view
    When the user clears the search input
    Then all themes should be restored to the view

  Scenario: Launching Prompt Execution Modal from Quote Card
    Given a theme row and attribute row are expanded with an example quote
    When the user clicks "button[data-action='sent-open-prompt']"
    Then the modal container "#modalHolder" should mount the prompt execution dialog
    And the modal should display the complete verbatim AI model response
    And the modal should display the engine platform badge
    When the user clicks the modal close button or presses "Escape"
    Then the modal dialog should be removed from "#modalHolder"
```

---

## 5. Visual Checks
1. **Toolbar Alignment:** Segment tabs on left, flex spacer, and compact search input on right (`width: 220px`).
2. **Active Segment Tab:** Highlighted with dark fill (`.on`) and crisp contrasting text.
3. **Modal Dialog Appearance:** Modal centered over viewport with markdown-formatted text, source badges, and close button.
4. **Empty Search Result:** If search query matches zero themes, renders a clean empty notice without page collapse.

---

## 6. Data and Network Checks
1. **Case-Insensitive Search Assertion:**
   ```js
   const q = "price";
   const match = t(th.en, th.tr).toLowerCase().indexOf(q) >= 0 ||
     (th.attributes || []).some(a => t(a.en, a.tr).toLowerCase().indexOf(q) >= 0);
   assert(match === true, "Theme must match search string");
   ```
2. **Modal Prompt ID Check:**
   - Confirm button carries `data-pid` pointing to valid prompt identifier.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `11-gherkin-result-case-theme-search-filtering-and-prompt-modal/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`segment_tabs_negative.png`, `theme_search_filtered.png`, `prompt_execution_modal.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-11-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/11-gherkin-result-case-theme-search-filtering-and-prompt-modal/screenshots/
     ```
  4. Write execution report `result.md` verifying segment filters, search matching, and modal DOM elements.

### Pass/Fail Criteria
- [ ] Segment buttons filter themes by polarity.
- [ ] Keyword search filters themes and attributes case-insensitively.
- [ ] Clicking "View Full Response" launches the prompt execution modal.
- [ ] Modal dismisses cleanly without errors.
