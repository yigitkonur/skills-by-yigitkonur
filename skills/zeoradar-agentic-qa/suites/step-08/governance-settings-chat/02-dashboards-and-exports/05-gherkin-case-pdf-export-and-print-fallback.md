# TC-DB-05: PDF Compilation Server Failure and Graceful Browser Print Fallback

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-05`
- **Purpose:** Verify that triggering "Export PDF" updates button state to compiling with a spinner, and if backend PDF compilation service is unavailable or rejected, gracefully falls back to invoking `window.print()`, applies the temporary `document.body.classList.add("printing")` print stylesheet, and restores the button to enabled status.
- **Target Result Directory:** `02-dashboards-and-exports/05-gherkin-result-case-pdf-export-and-print-fallback/`

---

## 2. Tester Brief
The dashboard offers one-click PDF generation for executive presentations.
1. When clicking `[data-action="dash-print"]`:
   - The button disables and shows `<span class="dash-spin">&#9696;</span> Compiling PDF...`.
   - `ZeoExport.run({ kind: "dashboard_pdf", format: "pdf" })` attempts server-side compilation.
2. If the backend fails (e.g. `dependency_unavailable` or offline mode):
   - A fallback toast is displayed: `"Offline mode: opened browser print preview"` / `"Çevrimdışı mod: tarayıcı yazdırma önizlemesi açıldı"`.
   - `body.classList.add("printing")` hides navigation sidebars and interactive buttons.
   - `window.print()` is triggered.
   - Upon return, `body.classList.remove("printing")` restores normal view.
   - Button text returns to `"Export PDF"` and `disabled` is set to `false`.
3. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/dashboards`.
- **Target Selector:** `button[data-action="dash-print"]`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Dashboard PDF Export and Print Fallback

  Scenario: Server compilation failure falling back to styled browser print
    Given the test user is viewing the executive dashboard
    When the user clicks the "Export PDF" button "[data-action='dash-print']"
    Then the button should show a loading spinner and become disabled
    When the backend PDF export service returns an error
    Then the client should display an informational toast regarding print preview
    And the CSS class "printing" should be added to the document body
    And "window.print()" should be invoked
    And upon completion the button should be restored to its enabled state

    Examples:
      | Environment | ErrorCode              | FallbackAction |
      | live        | dependency_unavailable | window.print   |
      | offline     | network_failure        | window.print   |
```

---

## 5. Visual Checks
- **Button State During Compilation:**
  - Spinner: `.dash-spin`.
  - Disabled: `disabled === true`.
- **Print Mode DOM:**
  - Body Class: `body.printing`.
  - Hidden in Print: `.side-wrap`, `.dash-actions`, `#modalHolder`.
- **Screenshot Points:**
  - `01_pdf_compiling_spinner.png` (Export button in compiling state).
  - `02_print_fallback_toast.png` (Toast notification during fallback).

---

## 6. Data and Network Checks
- **Intent Payload:**
  - Kind: `"dashboard_pdf"`.
  - Format: `"pdf"`.
  - Parameters: `{ dashboardId, dashboardName, vizzes }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/05-gherkin-result-case-pdf-export-and-print-fallback/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-pdf-fallback');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const fallbackResult = await js(String.raw`(() => {
  let printCalled = false;
  let printClassAdded = false;

  const origPrint = window.print;
  window.print = function () {
    printCalled = true;
    printClassAdded = document.body.classList.contains("printing");
  };

  const origExport = window.ZeoExport && window.ZeoExport.run;
  if (window.ZeoExport) {
    window.ZeoExport.run = () => Promise.reject(new Error("Service offline"));
  }

  const btn = document.querySelector('[data-action="dash-print"]');
  if (btn) btn.click();

  return new Promise(resolve => {
    setTimeout(() => {
      window.print = origPrint;
      if (window.ZeoExport && origExport) window.ZeoExport.run = origExport;
      const rBtn = document.querySelector('[data-action="dash-print"]');
      resolve({
        printCalled,
        printClassAdded,
        btnRestored: rBtn && !rBtn.disabled
      });
    }, 400);
  });
})()`);

cliLog('Print Fallback State: ' + JSON.stringify(fallbackResult));
if (!fallbackResult.printCalled || !fallbackResult.btnRestored) {
  throw new Error('PDF server failure fallback to window.print failed');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-pdf-fallback', { keep: false })`.
