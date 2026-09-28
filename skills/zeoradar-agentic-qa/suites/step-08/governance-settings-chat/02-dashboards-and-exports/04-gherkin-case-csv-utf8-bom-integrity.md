# TC-DB-04: CSV Export UTF-8 BOM (`\uFEFF`) Encoding Precision

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-04`
- **Purpose:** Verify that per-widget CSV exports prepend the binary UTF-8 Byte Order Mark (`\uFEFF` / character code `0xFEFF`) to the file payload and declare `charset=utf-8` in the Blob MIME type, guaranteeing flawless rendering of international diacritics (e.g., Turkish `Ğ, Ü, Ş, İ, Ö, Ç`) in Microsoft Excel.
- **Target Result Directory:** `02-dashboards-and-exports/04-gherkin-result-case-csv-utf8-bom-integrity/`

---

## 2. Tester Brief
Without a Byte Order Mark, Microsoft Excel defaults to legacy ANSI/Windows-1252 code pages on Windows, causing non-ASCII characters in brand names or prompt queries to display as garbled text (mojibake).
1. `dashExportVizCsv(p, viz)` compiles lines and formats the final string as:
   `var csvContent = "\uFEFF" + lines.join("\r\n");`
2. The payload is encapsulated into a `Blob([csvContent], { type: "text/csv;charset=utf-8;" })`.
3. Intercepting the `Blob` constructor in the browser session proves that:
   - Index 0 character code is `0xFEFF` (`65279`).
   - MIME type explicitly contains `charset=utf-8`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/dashboards.js` (`dashExportVizCsv`).
- **Target Route:** `[APP_URL]/#/[SLUG]/dashboards`.
- **Sample Non-ASCII String:** `"Şirket Gelirleri, İstanbul Ar-Ge Çözümleri, Çağrı Merkezi"`

---

## 4. Gherkin Scenario

```gherkin
Feature: CSV Export UTF-8 BOM Binary Encoding

  Scenario: Verifying BOM character code and charset declaration in exported CSV Blob
    Given the test user is viewing a dashboard widget containing international characters
    When the user triggers the CSV download action "[data-action='dash-viz-csv']"
    Then the generated CSV payload should start with the UTF-8 BOM character "\uFEFF"
    And the character code at index 0 should equal 65279 (0xFEFF)
    And the Blob MIME type should declare "charset=utf-8"

    Examples:
      | Locale | SampleDiacriticChar | ExpectedBomCode |
      | tr     | Ş                   | 65279           |
      | de     | Ü                   | 65279           |
```

---

## 5. Visual Checks
- **Download Action:**
  - Anchor dispatch: Ephemeral `<a download="...">` clicked and removed.
- **Screenshot Points:**
  - `01_bom_blob_intercept.png` (Console inspection of BOM prefix).

---

## 6. Data and Network Checks
- **Blob Payload Assertion:**
  ```js
  assert(capturedBlobContent.startsWith("\uFEFF"));
  assert(capturedBlobContent.charCodeAt(0) === 0xFEFF);
  assert(capturedBlobType.includes("charset=utf-8"));
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/04-gherkin-result-case-csv-utf8-bom-integrity/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-csv-bom');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const bomCheck = await js(String.raw`(() => {
  let blobText = null;
  let blobMime = null;

  const RealBlob = window.Blob;
  window.Blob = function (parts, options) {
    if (options && options.type && options.type.includes("text/csv")) {
      blobText = parts.join("");
      blobMime = options.type;
    }
    return new RealBlob(parts, options);
  };

  const sampleViz = { id: "test_bom", type: "vis-score", mode: "chart", name: "Score" };
  const sampleProfile = (window.profile && window.profile()) || { slug: "test", brand_name: "Zeo" };

  if (typeof window.dashExportVizCsv === "function") {
    window.dashExportVizCsv(sampleProfile, sampleViz);
  }

  window.Blob = RealBlob;

  return {
    blobCreated: !!blobText,
    hasBOM: blobText ? blobText.startsWith("\uFEFF") : false,
    bomCode: blobText ? blobText.charCodeAt(0) : null,
    mimeType: blobMime
  };
})()`);

cliLog('BOM Check Result: ' + JSON.stringify(bomCheck));
if (!bomCheck.hasBOM || bomCheck.bomCode !== 0xFEFF || !bomCheck.mimeType.includes("charset=utf-8")) {
  throw new Error('CSV Export UTF-8 BOM or charset declaration check failed');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-csv-bom', { keep: false })`.
