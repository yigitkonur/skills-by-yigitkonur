# Test Case 11: Server-Side CSV Pre-flight Validation & Itemized Defect Badges

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-11-CSV-SERVER-DEFECTS`
- **Purpose**: Verify that uploading a CSV file to the live server preview pipeline (`preview-prompts-csv`) executes comprehensive server-side schema and constraint validation, displays itemized defect tags (`duplicate_in_file`, `duplicate_existing`, `invalid`) in `.dgcsv-errlist` with line numbers, and gates bulk commit (`import-prompts-csv`) until valid rows are resolved.

---

## 2. Tester Brief
The tester will:
1. Open the CSV Upload modal in live mode for `[DOMAIN]`.
2. Prepare and upload a test CSV file `defective_prompts.csv` engineered with:
   - Line 2: Valid prompt query.
   - Line 3: Duplicate query within file (`duplicate_in_file`).
   - Line 4: Query matching an existing database prompt (`duplicate_existing`).
   - Line 5: Query with empty text and unsupported locale `xx` (`invalid`).
3. Assert that:
   - Command `preview-prompts-csv` executes and returns status details.
   - The preview pane renders `.dgcsv-errlist` containing line-by-line defect diagnostics.
   - Line 3 carries the badge `span.dgcsv-st.dup` (`"Duplicate in file"`).
   - Line 4 carries `span.dgcsv-st.dup` (`"Already exists"`).
   - Line 5 carries `span.dgcsv-st.err` (`"Invalid"`).
   - The totals line `span.dgcsv-tot` correctly summarizes inserted, duplicate, and invalid counts.
   - The import button `button#dgcsvImportBtn` permits importing only valid rows or remains gated according to project import policy.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Engineered Test File**: `defective_prompts.csv`
- **Component Selectors**:
  - Error List: `.dgcsv-errlist`
  - Duplicate Chip: `span.dgcsv-st.dup`
  - Error Chip: `span.dgcsv-st.err`
  - Totals Counter: `span.dgcsv-tot`
  - Import Button: `button#dgcsvImportBtn`

---

## 4. Gherkin Scenario

```gherkin
Feature: Server-Side CSV Pre-flight Validation & Defect Tagging

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the live CSV import modal at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"

  @smoke @csv @server-validation
  Scenario: Server pre-flight preview itemizes duplicate and schema defects
    When the tester uploads the engineered CSV file "defective_prompts.csv"
    Then the server command "preview-prompts-csv" should be executed
    And the preview pane should render the defect list ".dgcsv-errlist"
    And Line 3 should display the status chip "span.dgcsv-st.dup" with text "Duplicate in file"
    And Line 4 should display the status chip "span.dgcsv-st.dup" with text "Already exists"
    And Line 5 should display the error chip "span.dgcsv-st.err" with text "Invalid"
    And the totals readout "span.dgcsv-tot" should report:
      | Metric     | Count |
      | Valid      | 1     |
      | Duplicates | 2     |
      | Invalid    | 1     |

  @import @commit-gate
  Scenario: Commit import proceeds with valid rows while excluding defective rows
    Given the defect summary displays 1 valid prompt and 3 rejected rows
    When the tester clicks the import button "button#dgcsvImportBtn"
    Then the command "import-prompts-csv" should be dispatched for the 1 valid row
    And the modal should close upon completion
    And the master prompt table should reload reflecting the single imported prompt
```

---

## 5. Visual Checks
1. **Defect Item Styling**: Defect items render in `.dgcsv-errlist` with line numbers, field highlights, and red/amber chips.
2. **Totals Strip**: `span.dgcsv-tot` displays bold counts with green text for valid rows and red/amber for rejected rows.
3. **Commit Button Label**: Import button displays dynamic text: `"Import 1 Valid Prompt"` (or disabled if 0 valid).

---

## 6. Data and Network Checks
1. **Preview Network Contract**:
   - Inspect response from `preview-prompts-csv`:
     ```json
     {
       "ok": true,
       "data": {
         "validCount": 1,
         "duplicateInFileCount": 1,
         "duplicateExistingCount": 1,
         "invalidCount": 1,
         "defects": [
           { "line": 3, "code": "duplicate_in_file" },
           { "line": 4, "code": "duplicate_existing" },
           { "line": 5, "code": "invalid", "reason": "empty_text_and_invalid_locale" }
         ]
       }
     }
     ```
2. **Import Payload Gating**: Verify `import-prompts-csv` includes only the validated rows.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-csv-server-preview-validation-and-defect-chips/`
- **Execution Model Notice**: Automated via Ego Browser on macOS. Defect list and totals strip are captured to `/tmp/shots/csv-defects-[STEP].png` and transferred via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and server preview response.
  - `screenshot-csv-defect-list.png`: Visual defect report showing `.dgcsv-errlist`.
  - `screenshot-csv-import-summary.png`: Post-import master table with valid row.
