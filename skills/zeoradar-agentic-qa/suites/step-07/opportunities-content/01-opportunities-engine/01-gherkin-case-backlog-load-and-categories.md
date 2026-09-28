# Test Case: TC-OPP-01 - Opportunity Backlog Load & Category Classification

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-01`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-01` and `TC-OPP-02`
- **Purpose:** Verify that upon navigating to the Opportunities route, the dynamic backlog loads all detected citation and visibility gaps, classifies each item into its designated strategic taxonomy (`reddit`, `outreach`, `content`), renders distinct color indicator rails and badges, and accurately computes the composite Impact Score (0–100) assigning the proper tier (`high`, `medium`, `low`).

---

## 2. Tester Brief
The tester or AI execution agent will observe the initial render of the Opportunities backlog. Each card represents an unexploited generative engine visibility opportunity. The test verifies:
1. Each card receives the correct strategic category class (`.op-card-reddit`, `.op-card-outreach`, `.op-card-content`).
2. The visual category badge and left 3px indicator rail match the taxonomy color tokens.
3. The Opportunity Impact Score is mathematically computed as:
   $$\text{Composite Score} = \text{round}\Big(0.35 \times S_{\text{gap}} + 0.35 \times S_{\text{vol}} + 0.20 \times S_{\text{comp}} + 0.10 \times S_{\text{feasibility}}\Big)$$
4. The impact badge receives the appropriate tier styling (`.op-impact-high` for $\ge 75$, `.op-impact-medium` for $50-74$, `.op-impact-low` for $< 50$).
5. Card titles, teasers, entity link tags, and citation performance indicators render without data corruption or blank placeholders.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities` (or active tunnel URL)
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Profile Data:** Authenticated test user session with pre-scanned dataset (e.g. `RADAR_DATA.[SLUG]` with prompt answers and competitor citations).
- **Matching Result Directory:** `01-gherkin-result-case-backlog-load-and-categories/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Opportunities Backlog Loading, Strategy Classification, and Impact Scoring

  Background:
    Given the user is logged into Zeo Geo-Radar for "[DOMAIN]" in "[COUNTRY]"
    And the measurement dataset contains scanned prompt answers and competitor citations
    When the user navigates to the "/#/opportunities" route
    Then the main container ".opps-container" should be mounted in the viewport

  Scenario Outline: Opportunity Card Category Classification and Impact Tier Integrity
    When the opportunities backlog renders cards of type "<Category>"
    Then each card should have the container class "<CardClass>"
    And the card should display a category badge with class "<BadgeClass>" and text "<BadgeLabel>"
    And the card should display a left indicator rail with color token "<ColorToken>"
    And the card should display an entity link tag pointing to "<EntityPattern>"
    And the card impact score should be an integer between 0 and 100
    And when the calculated impact score is "<ScoreRange>", the impact badge should have class "<ImpactTierClass>"

    Examples:
      | Category | CardClass         | BadgeClass         | BadgeLabel        | ColorToken    | EntityPattern               | ScoreRange | ImpactTierClass    |
      | reddit   | op-card-reddit    | op-badge-reddit    | Forum / Reddit    | var(--chart-5)| reddit.com/r/ or forum link | >=75       | op-impact-high     |
      | outreach | op-card-outreach  | op-badge-outreach  | Outreach          | var(--chart-2)| External publisher domain   | 50-74      | op-impact-medium   |
      | content  | op-card-content   | op-badge-content   | Content Creation  | var(--chart-4)| Quoted prompt query         | <50        | op-impact-low      |

  Scenario: Backlog Card Anatomy and Performance Indicators
    Given the opportunities backlog is loaded
    Then each ".op-card" should contain a valid title in ".op-card-title"
    And each ".op-card" should contain an explanatory teaser in ".op-card-teaser"
    And each ".op-card" should contain a footer ".op-card-footer" housing:
      | Element Selector       | Purpose                                        |
      | .op-perf-group         | Citation or visibility performance indicator   |
      | .op-card-actions       | Isolated action button container               |
      | .op-card-chev          | Right chevron visual navigation affordance     |
    And cards with zero brand citations should display ".op-perf-not-mentioned"
    And cards with partial citation share should display ".op-perf-bar-fill" with width style matching percentage
```

---

## 5. Visual Checks
1. **Container Layout:** `.opps-container` is horizontally centered with maximum width of `920px`.
2. **Strategy Legend:** `.opps-strategy-legend` displays color dots for Outreach (Blue), Reddit (Amber), and Content Creation (Pink).
3. **Card Indicator Rails:**
   - `.op-card-reddit::before` renders a `3px` solid border using `var(--chart-5)`.
   - `.op-card-outreach::before` renders a `3px` solid border using `var(--chart-2)`.
   - `.op-card-content::before` renders a `3px` solid border using `var(--chart-4)`.
4. **Impact Badge:** Displays lightning bolt symbol `⚡ [Score] · [Tier Label]`.
   - High Impact: Green background/text (`var(--green)`).
   - Medium Impact: Amber background/text (`var(--amber)`).
   - Low Impact: Muted gray background/text (`var(--ink-3)`).
5. **Entity Links:** Tagged as `a.op-entity-tag` with trailing arrow icon (`↗`).

---

## 6. Data and Network Checks
1. **Profile Resolution:** Verify `window.resolveProfile` loads prompts and answers from `window.RADAR_DATA[slug]` or `ZEO_DATA_PROVIDER`.
2. **Impact Calculation Math:**
   ```js
   var currentScore = typeof op.performanceScore === 'number' ? op.performanceScore : 0;
   var gapScore = Math.max(0, Math.min(100, 100 - currentScore));
   var vol = (op.searchVolume != null) ? op.searchVolume : 1500;
   var volLog = (Math.log10(Math.max(10, vol)) - 1) / 3;
   var volScore = Math.min(100, Math.max(0, Math.round(volLog * 100)));
   var compShare = typeof op.competitorCitationShare === 'number' ? op.competitorCitationShare : 70;
   var compScore = Math.min(100, Math.max(0, Math.round(compShare * 1.25)));
   var feasScore = op.category === 'content' ? 95 : (op.category === 'reddit' ? 80 : 65);
   var expectedComposite = Math.round((0.35 * gapScore) + (0.35 * volScore) + (0.20 * compScore) + (0.10 * feasScore));
   ```
3. **Local Storage Key:** Check `localStorage.getItem("zeo-radar-opps-" + projKey)` exists or initializes safely as an array.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `01-gherkin-result-case-backlog-load-and-categories/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`initial_backlog.png`, `card_anatomy.png`, `impact_badges.png`) are stored in the test executor's task space.
  3. Transfer screenshots from MacBook to repository runner:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-backlog/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/01-gherkin-result-case-backlog-load-and-categories/
     ```
  4. Write execution report `result.md` referencing verified metrics and screenshot attachments.

### Pass/Fail Criteria
- [ ] Backlog renders at least 1 opportunity card without JavaScript exceptions.
- [ ] Every rendered card has a valid category (`reddit`, `outreach`, or `content`).
- [ ] Every card's impact score matches the 4-component weighted formula within $\pm 1$ rounding point.
- [ ] No card displays missing labels, `NaN`, or undefined placeholders.
