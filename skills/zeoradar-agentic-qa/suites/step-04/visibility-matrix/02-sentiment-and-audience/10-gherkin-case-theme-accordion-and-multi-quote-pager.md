# Test Case: TC-SNT-10 - Theme Attribute Accordion & Multi-Quote Carousel Pager

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-10`
- **Module:** Dedicated Sentiment Analysis Tab (`assets/radar.js`, `assets/radar.css`)
- **Parent Contract:** Spec 06 (Sentiment Analysis Architecture, Attribute Quote Carousel)
- **Traceability:** Maps to Source Scenarios `SNT-14`, `SNT-15`, and `SNT-25`
- **Purpose:** Verify that clicking a theme row (`.sent-theme`) expands the attribute list, clicking an attribute row (`.attr-row`) opens its example quote card (`.attr-ex`), verifies attribute polarity badges (`+`, `−`, `±`, `○`), and confirms that the multi-quote carousel pager (`button[data-action="theme-pager"]`) advances through examples, updates the indicator (`1 / N`, `2 / N`), and enforces boundary disabling on Previous and Next buttons.

---

## 2. Tester Brief
The tester or automated agent interacts with the Themes & Attributes accordion:
1. Locate Section 2 on the dedicated sentiment tab.
2. Click a theme row (e.g. `Product Quality` / `Ürün Kalitesi`) to expand its attributes list.
3. Click an attribute row (e.g. `Premium ingredients`):
   - Confirm the attribute row displays its polarity icon: `+` for positive, `−` for negative, `±` for mixed, or `○` for neutral.
   - Confirm `.attr-ex` container mounts below the attribute row.
4. Verify the quote carousel pager:
   - When an attribute contains $N > 1$ quotes:
     - The pager indicator displays `Example 1 / N`.
     - The Previous button (`data-dir="prev"`) is disabled (`disabled="true"`).
     - The Next button (`data-dir="next"`) is enabled.
5. Click Next button:
   - The pager indicator increments to `Example 2 / N`.
   - The verbatim quote text in `.ex-q` updates to the second quote.
   - The Previous button becomes enabled.
6. Cycle to the last quote ($N$):
   - The Next button becomes disabled.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/sentiment`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Multi-Quote Attribute:** An attribute with at least 2 recorded quote examples
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `10-gherkin-result-case-theme-accordion-and-multi-quote-pager/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Theme Attribute Accordion Expansion, Polarity Badges, and Quote Carousel Pager

  Background:
    Given the user is on the dedicated sentiment tab of Zeo Geo-Radar
    Then the "Themes & Attributes" section should be displayed

  Scenario: Expanding Theme Accordion and Attribute Polarity Badges
    When the user clicks the theme row ".sent-theme"
    Then the theme row should receive class "open"
    And the nested attributes container ".sent-attrs" should become visible
    And each attribute row ".attr-row" should display an indicator badge ".apol" matching its polarity:
      | Polarity Class | Symbol | Meaning     |
      | positive       | +      | Positive    |
      | negative       | −      | Negative    |
      | mixed          | ±      | Mixed       |
      | neutral        | ○      | Neutral     |

  Scenario: Expanding Attribute Row and Verifying Initial Pager State
    Given a theme row is open
    When the user clicks an attribute row ".attr-row" with multiple quote examples
    Then the example card ".attr-ex" should be displayed
    And the pager indicator ".attr-ex span b" should display "1 / "
    And the previous button "button[data-action='theme-pager'][data-dir='prev']" should be disabled
    And the next button "button[data-action='theme-pager'][data-dir='next']" should be enabled

  Scenario: Cycling Quote Carousel Pager Across Boundaries
    Given the attribute example card is displaying example "1 / N"
    When the user clicks "button[data-action='theme-pager'][data-dir='next']"
    Then the pager indicator should update to "2 / "
    And the previous button "button[data-action='theme-pager'][data-dir='prev']" should become enabled
    And the verbatim quote text in ".ex-q" should update to the second example
    When the user clicks next until the last example is reached
    Then the next button "button[data-action='theme-pager'][data-dir='next']" should become disabled
```

---

## 5. Visual Checks
1. **Accordion Chevron:** Chevron icon rotates (`.chev` transform) when `.sent-theme` and `.attr-row` expand.
2. **Polarity Icon Colors:**
   - `.apol.positive`: Green (`var(--green)`).
   - `.apol.negative`: Red (`var(--red)`).
   - `.apol.mixed`: Purple or amber.
   - `.apol.neutral`: Muted slate.
3. **Quote Card Layout:** Light card background (`var(--chip-bg)`), blockquote styling (`.ex-q`), and engine platform badge (`.plat`).
4. **Button Disabling:** Disabled pager buttons render with reduced opacity (`0.4`) and `cursor: not-allowed`.

---

## 6. Data and Network Checks
1. **Pager State Key:**
   - Confirm `state.expanded["theme-pager-" + exid]` tracks the active integer index.
2. **Boundary Index Enforcement:**
   - Assert page index cannot be negative (`pageIdx < 0` clamped to `0`).
   - Assert page index cannot exceed `exList.length - 1`.
3. **Quote Payload Integrity:** Confirm `.ex-q` text matches raw analyzer quote strings without JSON serialization escapes.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `10-gherkin-result-case-theme-accordion-and-multi-quote-pager/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`theme_accordion_expanded.png`, `quote_pager_page_1.png`, `quote_pager_page_2_next_enabled.png`, `quote_pager_last_disabled.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-10-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/10-gherkin-result-case-theme-accordion-and-multi-quote-pager/screenshots/
     ```
  4. Write execution report `result.md` verifying expanded classes, pager indices, and button disabled states.

### Pass/Fail Criteria
- [ ] Theme row expands attributes upon click.
- [ ] Attribute rows display valid polarity symbols (`+`, `−`, `±`, `○`).
- [ ] Pager index displays `1 / N` initially with Previous button disabled.
- [ ] Clicking Next increments index, updates quote text, and disables Next at the final quote.
