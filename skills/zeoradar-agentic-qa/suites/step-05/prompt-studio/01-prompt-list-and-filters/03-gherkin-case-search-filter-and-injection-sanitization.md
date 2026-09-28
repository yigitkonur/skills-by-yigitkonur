# Test Case 03: Query Search Substring Filter & Hostile XSS Injection Sanitization

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-03-SEARCH-INJECTION`
- **Purpose**: Verify that the prompt search input performs fast, case-insensitive substring filtering on active queries while strictly sanitizing hostile HTML and SQL injection vectors (`<script>`, `' OR 1=1 --`, `"><img onerror=...>`) via `esc()` string interpolation, ensuring zero code execution and proper empty state rendering.

---

## 2. Tester Brief
The tester will:
1. Navigate to the Prompt Designer Workbench for `[DOMAIN]`.
2. Enter standard keywords (e.g. `"[KEYWORD_TERM]"`, `"inverter"`) into `input[data-action-input="dg-search"]` and confirm real-time row filtering.
3. Inject hostile XSS payloads (`<script>alert('XSS')</script>`, `<img src=x onerror=alert(1)>`) and SQL injection sequences (`' OR 1=1 --`).
4. Assert that:
   - No script execution, browser alert dialogs, or unescaped HTML elements appear in the DOM.
   - The query is evaluated as a literal string.
   - If no literal match exists, the table renders `tr td.dg-empty-row` with `"No prompts match the current filters."`.
5. Clear the search input and verify that the full table row list is restored.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Data**: Master prompt table populated with standard English/Turkish prompts.
- **Search Payloads Under Test**:
  - Safe Query: `"[KEYWORD_TERM]"`, `"inverter"`
  - XSS Attack: `<script>alert('XSS-PROMPT-STUDIO')</script>`
  - Image Payload: `"><img src="x" onerror="window.__xss_fired=true">`
  - SQL Injection: `' OR 1=1 --`

---

## 4. Gherkin Scenario

```gherkin
Feature: Search Substring Filtering & Hostile Injection Escaping

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @search
  Scenario Outline: Standard query search performs case-insensitive substring filtering
    When the tester types "<SearchTerm>" into the search input ".dg-search-box input"
    Then all visible rows in "table.tbl.dg-tbl tbody tr.dg-row" should contain "<SearchTerm>" in their prompt text
    And non-matching rows should be hidden from view
    When the tester clears the search input
    Then all original active prompt rows should be visible

    Examples:
      | SearchTerm  |
      | klima       |
      | KLİMA       |
      | gift box    |
      | inverter    |

  @security @xss @adversarial
  Scenario Outline: Hostile injection strings are safely escaped and evaluated literally
    When the tester enters the hostile payload "<MaliciousPayload>" into ".dg-search-box input"
    Then the browser alert dialog should never trigger
    And no script or img tags should be injected into "table.tbl.dg-tbl"
    And the table should render the empty state notice "tr td.dg-empty-row"
    And the empty message text should be "No prompts match the current filters."
    When the tester clears the search input
    Then the prompt table should restore all active prompts without errors

    Examples:
      | MaliciousPayload                                       |
      | <script>alert('XSS-PROMPT-STUDIO')</script>            |
      | "><img src=x onerror="window.__xss_vulnerable=true">   |
      | <svg/onload=alert('XSS')>                              |
      | ' OR 1=1 --                                            |
      | '; DROP TABLE prompts; --                              |
```

---

## 5. Visual Checks
1. **Search Input Element**: `span.search-input.dg-search-box input` has search magnifying glass icon and clean placeholder text.
2. **Empty State Display**: When no match is found, `tr td.dg-empty-row` spans across all table columns with muted dim text styling.
3. **Escaped Text Safety**: In the DOM inspector, verify that prompt cells contain HTML entities (`&lt;script&gt;`) rather than executable HTML nodes.

---

## 6. Data and Network Checks
1. **DOM Injection Audit**:
   ```javascript
   assert.strictEqual(window.__xss_vulnerable, undefined, 'Hostile XSS payload must not execute');
   const tableScripts = document.querySelectorAll('.dg-tbl script, .dg-tbl img[onerror]');
   assert.strictEqual(tableScripts.length, 0, 'No raw script or executable img tags may exist in table DOM');
   ```
2. **Empty Row Assertion**:
   ```javascript
   const emptyRow = document.querySelector('.dg-tbl tbody tr td.dg-empty-row');
   assert.ok(emptyRow !== null, 'Empty state row must render when no matching rows exist');
   assert.ok(emptyRow.textContent.includes('No prompts match'), 'Proper empty notice message must be shown');
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-search-filter-and-injection-sanitization/`
- **Execution Model Notice**: Ego Browser drives automation on the macOS node. Screenshots of the search box and empty states are stored in `/tmp/shots/search-injection-[PAYLOAD_HASH].png` and transferred locally via SCP.
- **Report Contents**:
  - `status.json`: Test execution result.
  - `security-audit.json`: Log verifying `window.__xss_vulnerable` remained undefined.
  - `screenshot-standard-search.png`: Successful keyword filtering.
  - `screenshot-xss-empty-state.png`: Neutralized XSS string with empty row.
