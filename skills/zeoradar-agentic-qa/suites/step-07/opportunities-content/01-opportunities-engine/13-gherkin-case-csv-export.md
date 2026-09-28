# Test Case: TC-OPP-13 - Opportunities Backlog CSV Export & Data Sanitization

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-13`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-14` (CSV Backlog Export)
- **Purpose:** Validate that clicking the "Export CSV" button (`button.opps-btn-export[data-action="opp-export"]`) generates a sanitized CSV document containing all active opportunity backlog items, formats column headers correctly, escapes quotes and commas to prevent spreadsheet injection, triggers client-side file download with the appropriate filename structure (`zeo-radar-[slug]-opportunities.csv`), and renders a confirmation toast upon successful generation.

---

## 2. Tester Brief
The tester will verify the CSV export mechanism:
1. Clicking `.opps-btn-export` in the Opportunities header triggers `downloadCSV()`.
2. The export script iterates over the current opportunities array, producing CSV lines with standard headers:
   `"Brand","Category","Title","ImpactScore","EntityTag","PerformanceScore","Status"`
3. Values containing commas, line breaks, or double quotes are wrapped in double quotes and inner quotes are escaped (`""`).
4. Formula injection protection: Fields beginning with formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are escaped with a leading single quote (`'`).
5. A `Blob` is generated with MIME type `text/csv;charset=utf-8;` (including UTF-8 BOM `\uFEFF` for international character support in Microsoft Excel).
6. A hidden download link is created and clicked, and an informative toast confirms: `"Opportunities CSV exported"` / `"Fırsatlar CSV olarak indirildi"`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `13-gherkin-result-case-csv-export/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Opportunity Backlog CSV Export and Formula Injection Defense

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the active backlog contains at least 3 opportunities
    And the "Export CSV" button ".opps-btn-export" is visible in the header

  Scenario: Triggering CSV Export and Verifying Download Link
    When the user clicks the "Export CSV" button
    Then a browser download should be initiated for "zeo-radar-[DOMAIN]-opportunities.csv"
    And a confirmation toast should appear with message "Opportunities CSV exported"
    And the generated CSV payload should contain header:
      """
      "Brand","Category","Title","ImpactScore","EntityTag","PerformanceScore","Status"
      """
    And every active opportunity should be represented as a data row in the CSV
    And any cell containing dangerous formula characters ("=", "+", "-", "@") should be prefixed with a single quote
```

---

## 5. Visual Checks
1. **Button Affordance:** `.opps-btn-export` renders with download icon or text `"Export CSV"` / `"CSV Dışa Aktar"`.
2. **Download Feedback:** Success toast `.toast` appears with checkmark icon and disappears automatically.
3. **No Page Disruptions:** The export executes entirely in memory without reloading the page or altering filter state.

---

## 6. Data and Network Checks
1. **Blob Construction & Encoding:**
   - Verify `UTF-8 BOM` (`\uFEFF`) is prepended to ensure special Turkish and Latin characters (`ç, ğ, ı, ö, ş, ü`) display correctly in Excel.
2. **Formula Injection Sanitization:**
   ```js
   function sanitizeCSVCell(str) {
     if (typeof str !== 'string') return str;
     if (/^[=\+\-@\t\r]/.test(str)) {
       str = "'" + str;
     }
     return '"' + str.replace(/"/g, '""') + '"';
   }
   ```
3. Verify that row count equals `activeOpps.length + 1` (header row).

---

## 7. Evidence and Reporting
- **Target Result Directory:** `13-gherkin-result-case-csv-export/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `export_button_clicked.png` showing export toast.
  2. Capture `csv_file_preview.png` showing the downloaded CSV contents in terminal or text viewer.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-export/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/13-gherkin-result-case-csv-export/
     ```
  4. Document verification in `result.md`.

### Pass/Fail Criteria
- [ ] Export CSV button generates a valid CSV file download.
- [ ] Header columns match schema specification.
- [ ] Formula injection triggers are sanitized with leading single quote.
- [ ] UTF-8 encoding preserves Turkish and Latin diacritics.
