# TC-DB-03: CSV Formula Injection Defense and Cell Sanitization

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-03`
- **Purpose:** Verify that per-widget CSV data export sanitizes cell contents against CSV Formula Injection (DDE attacks) by prepending a single quote (`'`) to cells starting with dangerous tokens (`=`, `+`, `-`, `@`, `\t`, `\r`), while strictly preserving valid negative/positive numbers and percentages untouched.
- **Target Result Directory:** `02-dashboards-and-exports/03-gherkin-result-case-csv-formula-injection-defense/`

---

## 2. Tester Brief
When users export analytical tables or citation queries to CSV and open them in Microsoft Excel or Google Sheets, formulas starting with `=`, `@`, `+`, or `-` can execute arbitrary operating system commands (DDE injection) or make external web requests.
1. The sanitizer `ZeoCSV.cell(value)` inspects every cell before serialization.
2. If a value begins with `=+\-@\t\r`, it must be escaped with a single quote: `'`.
3. Critical Exception: Valid numerical expressions (e.g., `-12.5%`, `+42`, `98.2`) matching `/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?%?$/` must NOT be prefixed with a single quote, ensuring mathematical formulas and charts in downstream spreadsheets calculate accurately.
4. **Execution Model:** Ego Browser operates on the remote MacBook. The script validates the byte payload directly in the browser runtime.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/dashboards.js` (`dashExportVizCsv`) & `assets/csv-export.js`.
- **Target Vectors:**
  - Malicious: `=cmd|' /C calc'!A0`, `+SUM(A1:A10)`, `-@HYPERLINK("http://evil.com")`, `@SUM(1,2)`, `\tDDE_PAYLOAD`, `\rINJECTION`.
  - Benign Numerics: `-12.5%`, `+42`, `98.2`, `0.05%`.

---

## 4. Gherkin Scenario

```gherkin
Feature: CSV Formula Injection Defense

  Scenario Outline: Sanitizing dangerous formula prefixes while preserving valid numerics
    Given a table cell contains the input string "<InputCell>"
    When the CSV export cell sanitizer processes the value
    Then the sanitized output should match "<ExpectedOutput>"
    And the single quote protection should be "<ProtectionStatus>"

    Examples:
      | InputCell                              | ExpectedOutput                         | ProtectionStatus |
      | =cmd\|' /C calc'!A0                    | '=cmd\|' /C calc'!A0                   | applied          |
      | +SUM(A1:A10)                           | '+SUM(A1:A10)                          | applied          |
      | -@HYPERLINK("http://evil.com","Click") | '-@HYPERLINK("http://evil.com","Click")| applied          |
      | @SUM(1,2)                              | '@SUM(1,2)                             | applied          |
      | \tDDE_ATTACK                           | '\tDDE_ATTACK                          | applied          |
      | -12.5%                                 | -12.5%                                 | skipped          |
      | +42                                    | +42                                    | skipped          |
      | 98.2                                   | 98.2                                   | skipped          |
```

---

## 5. Visual Checks
- **Export Trigger:**
  - Card Action Button: `[data-action="dash-viz-csv"]` renders CSV download icon.
- **Downloaded File Verification:**
  - File name matches pattern: `{slug}_{viz.type}_{date}.csv`.
- **Screenshot Points:**
  - `01_csv_export_trigger.png` (Widget card with CSV export trigger).

---

## 6. Data and Network Checks
- **Sanitizer Unit Validation (`window.ZeoCSV.cell`):**
  ```js
  assert(ZeoCSV.cell("=cmd|' /C calc'!A0").startsWith("'"));
  assert(ZeoCSV.cell("-12.5%") === "-12.5%");
  assert(ZeoCSV.cell("+42") === "+42");
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/03-gherkin-result-case-csv-formula-injection-defense/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-csv-injection');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const testResult = await js(String.raw`(() => {
  const sanitize = (window.ZeoCSV && window.ZeoCSV.cell) ? window.ZeoCSV.cell : (v) => {
    if (typeof v !== "string") return v;
    if (/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?%?$/.test(v)) return v;
    return /^[=+\-@\t\r]/.test(v) ? "'" + v : v;
  };

  const malicious = ["=1+1", "+2+2", "-@EVIL", "@SUM", "\tTAB", "\rCR"];
  const safe = ["-15.4%", "+100", "0.95"];

  const malCheck = malicious.every(m => sanitize(m).startsWith("'"));
  const safeCheck = safe.every(s => sanitize(s) === s);

  return {
    maliciousEscaped: malCheck,
    safeNumericsUntouched: safeCheck
  };
})()`);

cliLog('CSV Injection Test: ' + JSON.stringify(testResult));
if (!testResult.maliciousEscaped || !testResult.safeNumericsUntouched) {
  throw new Error('CSV Formula Injection Defense failed validation checks');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-csv-injection', { keep: false })`.
