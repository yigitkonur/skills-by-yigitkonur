# Test Case: TC-OPP-09 - Opportunity Detail Citation References 2x3 Grid

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-09`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-11` (References 2x3 Grid Display)
- **Purpose:** Validate that in the Opportunity Detail View, the Citation References accordion expands to render a responsive 2x3 CSS grid (`.opp-references-grid`) displaying up to 6 authentic citation cards extracted from generative search engine answers, verifying that each reference card accurately presents the publication logo/emoji, page title, domain badge, snippet preview, and secure external link attributes (`target="_blank" rel="noopener"`).

---

## 2. Tester Brief
The tester will verify the citation references grid inside the detail view:
1. Expanding the "Citation References" accordion (`data-sec="references"`) mounts `.opp-references-grid`.
2. On desktop viewports ($\ge 768\text{px}$), the grid renders 2 columns with up to 6 reference cards (`a.opp-ref-card`). On mobile viewports, it adapts to 1 column.
3. Each reference card displays:
   - Source icon or publication emoji (e.g. `💬` for Reddit, `📰` for news publishers).
   - Publication title.
   - Clean domain badge (e.g. `reddit.com`, `techradar.com`).
   - Snippet summary explaining the citation context.
4. Each card is an anchor tag (`<a>`) with valid `href`, opening in a new browser tab with security attributes `target="_blank"` and `rel="noopener"`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** Opportunity with populated `references` array
- **Matching Result Directory:** `09-gherkin-result-case-detail-references-grid/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: 2x3 Citation References Grid in Opportunity Detail View

  Background:
    Given the user is on the detail view for opportunity "[OPPORTUNITY_ID]"
    When the user clicks the "Citation References" accordion header "[data-sec='references']"
    Then the accordion container should have class "opp-open"
    And the references grid container ".opp-references-grid" should be visible

  Scenario: Responsive Grid Layout and Reference Card Anatomy
    Then the grid ".opp-references-grid" should display between 1 and 6 reference cards "a.opp-ref-card"
    And each "a.opp-ref-card" must contain:
      | Child Element          | Purpose                                  |
      | .opp-ref-logo          | Publisher icon or platform emoji         |
      | .opp-ref-title         | Article or thread headline               |
      | .opp-ref-domain        | Clean domain badge (e.g. reddit.com)     |
      | .opp-ref-snippet       | Excerpt of citation context in AI answer |
    And each "a.opp-ref-card" must have attribute 'target="_blank"'
    And each "a.opp-ref-card" must have attribute 'rel="noopener"'
    And clicking a reference card must not trigger SPA route changes or detail view closure

  Scenario Outline: Domain Badge and Logo Mapping
    When a reference card points to a URL on "<Domain>"
    Then the card logo should display "<ExpectedEmoji>"
    And the domain badge should contain "<Domain>"

    Examples:
      | Domain         | ExpectedEmoji |
      | reddit.com     | 💬            |
      | techradar.com  | 📰            |
      | quora.com      | 🔴            |
```

---

## 5. Visual Checks
1. **Grid Geometry:** `.opp-references-grid` uses `display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;` on desktop.
2. **Card Styling:** `.opp-ref-card` has subtle border, rounded corners (`8px`), and interactive hover state (elevation or background highlight).
3. **Typography:** Domain badges use monospace or small caps text styling (`font-size: 11px; text-transform: lowercase`).
4. **Snippet Clamping:** `.opp-ref-snippet` truncates gracefully after 2–3 lines using `-webkit-line-clamp`.

---

## 6. Data and Network Checks
1. **Source References Array:**
   - Inspect `op.references` in memory. Verify that `url`, `title`, and `d` (domain) are well-formed strings.
2. **URL Sanitization:**
   - Verify all `href` attributes start with `http://` or `https://` (no `javascript:` execution or malformed URIs).

---

## 7. Evidence and Reporting
- **Target Result Directory:** `09-gherkin-result-case-detail-references-grid/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `references_grid_desktop.png` showing the 2x3 layout.
  2. Capture `references_card_hover.png` showing hover styling.
  3. Capture `references_grid_mobile.png` under 390px viewport showing single-column layout.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-refs/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/09-gherkin-result-case-detail-references-grid/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] References accordion opens and displays `.opp-references-grid`.
- [ ] Up to 6 source cards render with logos, titles, domain badges, and snippets.
- [ ] All external links feature `target="_blank"` and `rel="noopener"`.
- [ ] Grid adapts smoothly to single column on mobile screens without overflow.
