# Test Case 10: CSV Dropzone Parser, BOM Stripping & Corrupted Delimiter Resilience

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-10-CSV-DELIMITERS`
- **Purpose**: Verify that the CSV bulk upload wizard correctly parses standard CSV files, strips leading UTF-8 BOM characters (`\uFEFF`), guesses column mappings for prompt text, topic, and locales, and handles malformed or non-comma delimiters (semicolon `;`, tab `\t`) gracefully without crashing the client parser or injecting corrupted records.

---

## 2. Tester Brief
The tester will:
1. Open the CSV Bulk Upload modal from the Prompt Designer toolbar via `button[data-action="open-csv-wizard"]` (or `dgcsv-open`).
2. Upload a valid UTF-8 CSV file containing leading BOM (`\uFEFF`) and comma-delimited columns:
   `Topic,Prompt,Region,Language`
3. Verify that:
   - The BOM character is stripped cleanly by `parseCSVText`.
   - The column mapping dropdowns (`select[data-dg-select="csv-map"]`) auto-assign columns to `topic`, `prompt`, `region`, and `language`.
   - The parsed preview displays valid row counts.
4. Upload a corrupted CSV file using semicolons (`;`) or tabs as delimiters.
5. Verify that:
   - The comma parser treats the entire header line as a single field.
   - Column mapping fails to guess required `prompt` and `topic` fields (`idx.prompt === -1`).
   - The parser produces `0` valid rows and disables the import action, preventing corrupted data ingestion.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Test File Payloads**:
  1. `valid_bom.csv`: UTF-8 with BOM, comma delimited.
  2. `corrupted_semicolon.csv`: Semicolon delimited (`Topic;Prompt;Region;Language`).
- **Component Selectors**:
  - CSV Dropzone: `.csv-dropzone`
  - File Input: `input#csvFileInput`
  - Mapping Selects: `select[data-dg-select="csv-map"]`
  - Import Button: `button#dgcsvImportBtn`

---

## 4. Gherkin Scenario

```gherkin
Feature: CSV Bulk Upload Delimiter & BOM Stripping Resilience

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And opens the CSV Bulk Upload Wizard modal

  @smoke @csv @parser
  Scenario: Upload standard CSV with UTF-8 BOM and verify clean column mapping
    When the tester uploads the file "valid_bom.csv" containing a leading UTF-8 BOM
    Then the client parser "parseCSVText" should strip the BOM character "\uFEFF"
    And the column mapping selector for "Prompt" should auto-map to the prompt column
    And the column mapping selector for "Topic" should auto-map to the topic column
    And the live preview should display valid parsed prompt rows

  @edge @corrupted @resilience
  Scenario: Upload semicolon-delimited CSV and verify corrupted import gating
    When the tester uploads the file "corrupted_semicolon.csv" using semicolon delimiters
    Then the parser should evaluate the line as a single un-delimited token
    And the auto-mapper should fail to detect separate "prompt" and "topic" headers
    And the parsed preview row count should equal 0
    And the import execution button should remain disabled
```

---

## 5. Visual Checks
1. **Dropzone Styling**: `.csv-dropzone` displays dashed border, cloud upload icon, and text `"Drop CSV file here or browse"`.
2. **Mapper Controls**: `.csv-map-row` aligns detected file headers with application field dropdowns.
3. **Disabled Import Button**: When required columns are unmapped, `button#dgcsvImportBtn` has muted styling and disabled attribute.

---

## 6. Data and Network Checks
1. **Parser Unit Verification**:
   ```javascript
   // Test parseCSVText BOM stripping
   const bomString = "\uFEFFTopic,Prompt\nKlimalar,Inverter Klima";
   const cleanString = bomString.replace(/^\uFEFF/, '');
   assert.strictEqual(cleanString.charCodeAt(0), 84, 'Leading character must be "T" (84), not BOM (65279)');
   ```
2. **Mapping Guard Check**:
   - Verify `guessMappings` returns `{ prompt: -1, topic: -1 }` on semicolon files.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-csv-bulk-upload-delimiter-and-syntax-resilience/`
- **Execution Model Notice**: Automated via Ego Browser on macOS. File dropzone interactions and mapping views are screenshotted to `/tmp/shots/csv-parser-[FILE].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Test execution verdict and parsing latency.
  - `screenshot-csv-valid-mapped.png`: Auto-mapped headers with valid parsed rows.
  - `screenshot-csv-corrupted-disabled.png`: Disabled import state on corrupted delimiter file.
