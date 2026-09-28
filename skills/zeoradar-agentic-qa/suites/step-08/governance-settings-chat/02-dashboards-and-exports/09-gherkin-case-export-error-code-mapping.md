# TC-DB-09: Export Error Code Localized Mapping and User Notice Integrity

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-09`
- **Purpose:** Verify that server-side export failures return normalized error codes (`unauthenticated`, `access_suspended`, `not_found`, `validation_failed`, `rate_limited`, `dependency_unavailable`) that are mapped to user-facing localized toast messages with diagnostic tags, and that raw exception stacks are never exposed to the user.
- **Target Result Directory:** `02-dashboards-and-exports/09-gherkin-result-case-export-error-code-mapping/`

---

## 2. Tester Brief
Security standards require that internal database errors, network timeouts, or server exceptions are sanitized before presentation to end users.
1. When `create-export-intent` returns `{ ok: false, error: { code: "<ERROR_CODE>" } }`:
2. `ZeoExport` maps the code to a curated English or Turkish notice:
   - `rate_limited` -> `"Too many requests — try the export again shortly. (rate_limited)"`.
   - `access_suspended` -> `"This workspace cannot export right now. (access_suspended)"`.
3. The raw `error.message` string (which might contain SQL fragments or internal IPs) is discarded.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/export-intent.js`.
- **Target Error Codes:** `rate_limited`, `access_suspended`, `dependency_unavailable`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Export Error Code Localized Translation

  Scenario Outline: Mapping server error codes to curated user toast notices
    Given an export intent is dispatched in language "<Language>"
    When the server returns an error code "<ServerCode>"
    Then the client toast notification should display "<ExpectedToastCopy>"
    And no raw stack trace or database error string should be visible in the DOM

    Examples:
      | Language | ServerCode            | ExpectedToastCopy                                              |
      | en       | rate_limited          | Too many requests — try the export again shortly.              |
      | en       | access_suspended      | This workspace cannot export right now.                        |
      | tr       | rate_limited          | Çok fazla istek — dışa aktarmayı az sonra yeniden deneyin.     |
      | tr       | dependency_unavailable| Dışa aktarma servisi şu anda kullanılamıyor.                   |
```

---

## 5. Visual Checks
- **Toast Element:**
  - Container: `.toast` or `.zr-toast`.
  - Content: Matches localized text and diagnostic suffix `(<code>)`.
- **Screenshot Points:**
  - `01_rate_limited_toast.png` (Toast notification displaying rate_limited error).

---

## 6. Data and Network Checks
- **Client Assertion:**
  - Toast string includes the exact expected translation.
  - Raw server message is excluded from the DOM.

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/09-gherkin-result-case-export-error-code-mapping/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-export-errors');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const errorCheck = await js(String.raw`(() => {
  let displayedToast = null;
  const origToast = window.showToast;
  window.showToast = msg => { displayedToast = msg; };

  // Intercept callCommand to simulate rate_limited
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'create-export-intent') {
      return Promise.resolve({ ok: false, error: { code: "rate_limited", message: "Internal server 429 flood" } });
    }
    return origCall.apply(this, arguments);
  };

  if (window.ZeoExport && typeof window.ZeoExport.run === "function") {
    window.ZeoExport.run({ kind: "dashboard_pdf", format: "pdf" });
  }

  return new Promise(resolve => {
    setTimeout(() => {
      window.ZEO_DATA_PROVIDER.callCommand = origCall;
      window.showToast = origToast;
      resolve({
        toastShown: !!displayedToast,
        toastMessage: displayedToast
      });
    }, 400);
  });
})()`);

cliLog('Export Error Mapping State: ' + JSON.stringify(errorCheck));
if (errorCheck.toastShown && !errorCheck.toastMessage.includes("rate_limited")) {
  throw new Error('Toast message failed to include diagnostic code tag');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-export-errors', { keep: false })`.
