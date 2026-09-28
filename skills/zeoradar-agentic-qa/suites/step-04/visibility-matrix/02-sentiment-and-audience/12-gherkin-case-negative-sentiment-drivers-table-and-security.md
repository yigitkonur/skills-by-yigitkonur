# Test Case: TC-SNT-12 - Negative Sentiment Drivers Table, Quote Previews & Link Security

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-12`
- **Module:** Sentiment Analytics & Dedicated Tab (`assets/sentiment-analytics.js`, `assets/radar.js`)
- **Parent Contract:** Spec 06 (Sentiment Analysis Architecture, Negative Driver Intelligence)
- **Traceability:** Maps to Source Scenarios `SNT-17` and `SNT-27`
- **Purpose:** Verify that the Negative Sentiment Drivers table ranks external publisher URLs descending by negative claim count, categorizes each driver under its primary driving negative theme, renders verbatim quote previews truncated cleanly to 110 characters, and enforces strict link security standards (`target="_blank"` and `rel="noopener"`) on all outbound publisher URLs to prevent tab-nabbing attacks.

---

## 2. Tester Brief
The tester or automated agent verifies the Negative Sentiment Drivers section:
1. Locate Section 3 (Negative Drivers) on the dedicated sentiment tab.
2. Confirm the table structure:
   - Rank index.
   - Publisher Domain / URL.
   - Negative Claims count badge.
   - Primary Associated Theme badge (e.g. `Pricing & Value`, `Product Quality`).
   - Verbatim Claim Quote Preview.
3. Validate sorting order:
   - Confirm table rows are sorted strictly descending by negative claim volume ($b.\text{negative} - a.\text{negative}$).
4. Verify quote preview truncation:
   - Confirm long quotes are truncated cleanly to approximately 110 characters with trailing ellipsis (`…`) without breaking HTML tags or character entities.
5. Validate external link security contract:
   - Inspect every anchor tag (`<a href="...">`) linking to an external domain.
   - Confirm `target="_blank"` is present.
   - Confirm `rel="noopener"` is present (defending against `window.opener` reverse hijacking).

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/sentiment`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Negative Drivers Dataset:** Dataset with recorded negative claims and cited URLs
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `12-gherkin-result-case-negative-sentiment-drivers-table-and-security/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Negative Sentiment Drivers Ranked Table and External Link Security

  Background:
    Given the user is on the dedicated sentiment tab of Zeo Geo-Radar
    And the brand dataset contains negative evaluative claims associated with external citations
    Then the "Negative Sentiment Drivers" table should be rendered

  Scenario: Table Column Structure and Descending Volume Sorting
    Then the negative drivers table "table.tbl" should contain rows representing cited publisher URLs
    And the rows should be sorted descending by negative claim count:
      | Row Order | Condition                                               |
      | Top Row   | Highest number of associated negative claims             |
      | Next Rows | Equal or fewer negative claims than the preceding row   |
    And no more than 12 drivers should be rendered in the table

  Scenario: Driver Row Anatomy and Quote Truncation
    When a negative driver row is rendered
    Then it should display the publisher domain or URL
    And it should display an associated theme badge with class ".cat-badge" or ".chip"
    And it should display an example quote preview
    And quote previews exceeding 110 characters should be truncated with an ellipsis "…"

  Scenario: Outbound Publisher Anchor Link Security
    When the user inspects external publisher links within the negative drivers table
    Then every anchor tag pointing to an external domain must have attribute "target='_blank'"
    And every anchor tag pointing to an external domain must have attribute "rel='noopener'"
    And clicking an external link should open in a new browser tab without access to "window.opener"
```

---

## 5. Visual Checks
1. **Table Typography:** Clean layout with monospaced domains, favicon indicators, and bold negative claim count badges (`color: var(--red)`).
2. **Theme Badges:** Small thematic badges identifying the primary issue (e.g. `Pricing & Value` in amber or red).
3. **Quote Preview:** Italicized or muted quote excerpts (`font-size: 12px`, `color: var(--ink-2)`).
4. **External Link Icon:** Small diagonal arrow indicator (`↗`) accompanying external URLs.

---

## 6. Data and Network Checks
1. **Sort Order Invariant Assertion:**
   ```js
   const counts = Array.from(document.querySelectorAll(".sent-table ~ .section table.tbl td.neg-count"))
     .map(el => parseInt(el.textContent));
   for (let i = 0; i < counts.length - 1; i++) {
     assert(counts[i] >= counts[i + 1], "Drivers must be sorted descending by negative claim count");
   }
   ```
2. **Security Attribute Check:**
   ```js
   const links = document.querySelectorAll(".sent-table ~ .section table.tbl a[target]");
   links.forEach(a => {
     assert(a.getAttribute("target") === "_blank", "Must carry target='_blank'");
     assert(a.getAttribute("rel") === "noopener", "Must carry rel='noopener'");
   });
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `12-gherkin-result-case-negative-sentiment-drivers-table-and-security/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`negative_drivers_table.png`, `quote_truncation_preview.png`, `anchor_link_security_inspected.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-12-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/12-gherkin-result-case-negative-sentiment-drivers-table-and-security/screenshots/
     ```
  4. Write execution report `result.md` verifying sort order, truncation lengths, and security attributes.

### Pass/Fail Criteria
- [ ] Table renders ranked publisher URLs sorted descending by negative claims.
- [ ] Quotes truncate cleanly to ~110 characters.
- [ ] 100% of external links enforce `target="_blank"` and `rel="noopener"`.
- [ ] No layout glitches or broken URLs.
