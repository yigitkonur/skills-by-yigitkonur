# Test Case: TC-VIS-10 - Stage 3 Root Domain Authority Rollups & Co-Citation Overlap Bar

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-10`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, R3 Root Domain Rollup)
- **Traceability:** Maps to Source Scenario `VIS-25`
- **Purpose:** Verify that Stage 3 of the Generative Retrieval Pipeline aggregates publisher citations to root domains (eTLD+1) in `table.tbl.aei-domain-tbl`, assigns domain authority tiers (`high`, `med`, `low`), calculates co-citation share percentages between the monitored brand and competitors, renders the dual-color co-citation split bar (`.aei-cocitation-bar`: `.aei-co-my` vs `.aei-co-rival`), and opens the Citation Drawer upon clicking a domain row.

---

## 2. Tester Brief
The tester or automated agent inspects Stage 3 at the bottom of the Studio detail pane:
1. Locate `table.tbl.aei-domain-tbl` inside `.aei-pipe-section`.
2. Confirm the 4 table columns:
   - Root Domain (eTLD+1, e.g. `wikipedia.org`, `[DOMAIN]`, `[COMPETITOR_DOMAIN]`, `forbes.com`).
   - Authority Tier: Categorized badge (`.aei-tier-pill.high`, `.med`, `.low`).
   - Citations: Total occurrences citing this domain across active prompt executions.
   - Co-Citation Attribution: Visual split bar representing share of voice.
3. Validate Co-Citation Split Bar calculation:
   - Monitored brand's own domain receives `myShare = 100%` (`.aei-co-my` fills 100% width).
   - Competitor domain receives `myShare = 0%` (`.aei-co-rival` fills 100% width).
   - Co-cited neutral publisher receives:
     $$\text{myShare} = \text{round}\left(\frac{\text{ownMentions}}{\text{ownMentions} + \text{compMentions}} \times 100\right)$$
     with proportional widths for `.aei-co-my` (green) and `.aei-co-rival` (orange/gray).
4. Click any domain row and verify it carries `data-action="open-citation-drawer"`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Authority Tier `[AUTHORITY_TIER]`:** `high`, `med`, `low`
- **Matching Result Directory:** `10-gherkin-result-case-stage-3-root-domain-authority-and-cocitation-bar/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Stage 3 Root Domain Authority Rollups and Co-Citation Overlap Bar

  Background:
    Given the user is in the "studio" workspace of Zeo Geo-Radar
    And a prompt with multiple publisher citations is active in the detail pane
    Then Stage 3 section ".aei-pipe-section" should render "table.tbl.aei-domain-tbl"

  Scenario: Root Domain Table Columns and Authority Tiers
    Then the domain table header "thead tr" should contain 4 columns:
      | Column Index | Expected Header Text (EN)          | Expected Header Text (TR)                   |
      | 1            | Root Domain (eTLD+1)               | Kök Alan Adı                                |
      | 2            | Authority Tier                     | Otorite Seviyesi                            |
      | 3            | Citations                          | Atıf                                        |
      | 4            | Co-Citation Attribution            | Ortak Atıf Dağılımı                         |
    And each domain row should render an authority pill ".aei-tier-pill" with class "high", "med", or "low"

  Scenario Outline: Co-Citation Split Bar Proportional Widths
    When a domain row is rendered for "<DomainType>"
    Then the co-citation bar ".aei-cocitation-bar" should contain:
      | Bar Segment    | Expected Width Range | Segment Class |
      | Own Brand      | <MyWidthRange>       | aei-co-my     |
      | Competitors    | <RivalWidthRange>    | aei-co-rival  |

    Examples:
      | DomainType        | MyWidthRange | RivalWidthRange | Description                       |
      | Monitored Domain  | 100%         | 0%              | 100% brand citation attribution   |
      | Competitor Domain | 0%           | 100%            | 100% rival citation attribution   |
      | Co-Cited Neutral  | 1% - 99%     | 1% - 99%        | Proportional co-citation split bar|

  Scenario: Domain Row Click Interaction
    When the user clicks a row in "table.tbl.aei-domain-tbl tbody tr"
    Then the row must have attribute "data-action='open-citation-drawer'"
    And the row must have a non-empty "data-url" attribute
    And the slide-in Citation Drawer "#citationDrawerHolder" should mount
```

---

## 5. Visual Checks
1. **Table Typography & Layout:** Clean table with monospaced domain names (`font-family: var(--font-mono)`), right-aligned numeric citation counts, and proportional split bars.
2. **Co-Citation Bar Design:**
   - Container `.aei-cocitation-bar` has height `8px`, border-radius `4px`, and overflow hidden.
   - `.aei-co-my` segment is rendered with green fill (`var(--green)`).
   - `.aei-co-rival` segment is rendered with orange/slate fill (`var(--ink-4)` or `var(--red)`).
3. **Hover Row Affordance:** Table rows exhibit background highlight (`var(--panel-subtle)`) and pointer cursor indicating clickability.

---

## 6. Data and Network Checks
1. **eTLD+1 Domain Extraction:**
   - Confirm subdomains (`blog.[DOMAIN]`, `shop.[DOMAIN]`) rollup to `[DOMAIN]`.
   - Confirm multi-part TLDs (`.co.uk`, `.com.tr`) extract properly via `extractRootDomain`.
2. **Proportional Math Verification:**
   ```js
   const myBar = row.querySelector(".aei-co-my");
   const rivalBar = row.querySelector(".aei-co-rival");
   const myW = parseFloat(myBar ? myBar.style.width : "0");
   const rivalW = parseFloat(rivalBar ? rivalBar.style.width : "0");
   assert(Math.round(myW + rivalW) === 100, "Segments must sum to 100%");
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `10-gherkin-result-case-stage-3-root-domain-authority-and-cocitation-bar/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`stage3_domain_table.png`, `cocitation_split_bar.png`, `domain_row_drawer_trigger.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-10-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/10-gherkin-result-case-stage-3-root-domain-authority-and-cocitation-bar/screenshots/
     ```
  4. Write execution report `result.md` verifying table rows, split bar widths, and eTLD+1 rollups.

### Pass/Fail Criteria
- [ ] Table rolls up publisher URLs to eTLD+1 root domains.
- [ ] Authority tiers display valid classification pills (`high`, `med`, `low`).
- [ ] Co-citation bar segments sum to 100%.
- [ ] Clicking a domain row triggers `openCitationDrawer`.
