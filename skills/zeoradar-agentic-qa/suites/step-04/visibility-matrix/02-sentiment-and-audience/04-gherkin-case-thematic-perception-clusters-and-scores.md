# Test Case: TC-SNT-04 - Thematic Perception Clusters Grid & 10-Theme Taxonomy

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-04`
- **Module:** Sentiment Analytics & Perception (`assets/aei.js`, `assets/sentiment-analytics.js`)
- **Parent Contract:** Spec 06 / Spec 11 (Thematic Attribute Taxonomy & Extraction Engine)
- **Traceability:** Maps to Source Scenario `SNT-05`
- **Purpose:** Verify that the Thematic Attribute Perception Clusters card (`.card.aei-attributes-card`) renders extracted brand perception pillars into a responsive grid (`.aei-attrs-grid`), maps theme keys strictly against the fixed 10-theme taxonomy (`THEME_LABELS`: pricing, quality, range, availability, brand, health, service, packaging, sustainability, other), renders localized theme names, displays positive score badges (`.text-green`), summarizes driving attributes in `.aei-attr-desc`, and animates progress bars (`.aei-attr-fill`) matching theme positive percentages.

---

## 2. Tester Brief
The tester or automated agent inspects Section 2 of the Perception workspace:
1. Locate `.card.aei-attributes-card` and verify header copy: *"Thematic Attribute Perception Clusters"*.
2. Confirm the card grid `.aei-attrs-grid` contains individual theme cards (`.aei-attr-card`).
3. For each rendered theme card, verify:
   - Header `.aei-attr-head` contains the localized theme name and positive score badge (e.g. `88% pos`).
   - Description `.aei-attr-desc` lists driving attributes (e.g. `"Premium positioning · Handcrafted heritage"`).
   - Progress bar `.aei-attr-bar .aei-attr-fill` has inline width matching the calculated percentage.
4. Validate taxonomy adherence: Verify theme names correspond to the 10 fixed dictionary categories in `assets/sentiment-analytics.js`.
5. Empty state check: If no themes exist in dataset, verify graceful fallback notice `.aei-empty-state`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Theme Taxonomy `[THEME_KEY]`:** `pricing`, `quality`, `range`, `availability`, `brand`, `health`, `service`, `packaging`, `sustainability`, `other`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `04-gherkin-result-case-thematic-perception-clusters-and-scores/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Thematic Perception Clusters Grid and Taxonomy Compliance

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    And the monitored brand has evaluated thematic sentiment claims
    Then the thematic attributes card ".card.aei-attributes-card" should be visible

  Scenario: Thematic Grid and Card Anatomy
    When the thematic attributes grid ".aei-attrs-grid" is rendered
    Then it should contain at least 1 theme card ".aei-attr-card"
    And each theme card should contain:
      | Element Selector            | Purpose                                            |
      | .aei-attr-head strong       | Localized theme title                              |
      | .aei-attr-head .text-green  | Positive score percentage badge                    |
      | .aei-attr-desc              | Driving attribute summary or claim counts          |
      | .aei-attr-bar .aei-attr-fill| Visual horizontal score progress bar               |

  Scenario Outline: Standard 10-Theme Taxonomy Localization and Progress Fills
    When a theme card is rendered for theme key "<ThemeKey>"
    Then the theme title text should match "<ExpectedTitleEN>" or "<ExpectedTitleTR>"
    And the progress bar fill width ".aei-attr-fill" should equal the calculated score percentage

    Examples:
      | ThemeKey       | ExpectedTitleEN                 | ExpectedTitleTR                   |
      | pricing        | Pricing & Value                 | Fiyat ve Değer                    |
      | quality        | Product Quality                 | Ürün Kalitesi                     |
      | range          | Product Range                   | Ürün Yelpazesi                    |
      | availability   | Availability & Distribution     | Erişim ve Dağıtım                 |
      | brand          | Brand & Reputation              | Marka ve İtibar                   |
      | health         | Health & Ingredients            | Sağlık ve İçerik                  |
      | service        | Customer Experience             | Müşteri Deneyimi                  |
      | packaging      | Packaging & Gifting             | Ambalaj ve Hediyelik              |
      | sustainability | Sustainability & Responsibility | Sürdürülebilirlik ve Sorumluluk   |
      | other          | Other                           | Diğer                             |

  Scenario: Zero Thematic Signal Graceful Empty State
    Given a brand project with zero extracted thematic claims
    When the perception workspace is rendered
    Then ".aei-attrs-grid" should not be attached to the DOM
    And the card should display ".aei-empty-state" with an informative message explaining missing claims
```

---

## 5. Visual Checks
1. **Grid Responsive Columns:** `.aei-attrs-grid` renders a 2-column layout on desktop viewports and 1 column on mobile.
2. **Theme Card Styling:** Border `1px solid var(--border-soft)`, background `var(--panel)`, padding `16px`, border-radius `8px`.
3. **Progress Bar Fill:** Height `6px`, background `var(--green)`, rounded edges (`border-radius: 3px`).
4. **Header Contrast:** Bold theme title with vibrant green score readout (`.text-green`).

---

## 6. Data and Network Checks
1. **Taxonomy Integrity Assertion:**
   ```js
   const knownKeys = ['pricing', 'quality', 'range', 'availability', 'brand', 'health', 'service', 'packaging', 'sustainability', 'other'];
   const themes = window.aeiState && s.themes;
   if (themes) {
     themes.forEach(th => {
       assert(knownKeys.includes(th.key), `Unknown theme key: ${th.key}`);
     });
   }
   ```
2. **Score Range Check:**
   - Confirm theme score is between 0% and 100% or rendered as `"No score"` / `"Puan yok"` when null.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `04-gherkin-result-case-thematic-perception-clusters-and-scores/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`thematic_grid_overview.png`, `theme_card_anatomy.png`, `taxonomy_localization.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-04-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/04-gherkin-result-case-thematic-perception-clusters-and-scores/screenshots/
     ```
  4. Write execution report `result.md` verifying theme keys, localized titles, and progress fills.

### Pass/Fail Criteria
- [ ] Thematic grid renders valid theme cards.
- [ ] Theme titles adhere to the 10-theme taxonomy.
- [ ] Score progress bars match theme positive percentages.
- [ ] Empty state renders cleanly when no themes exist.
