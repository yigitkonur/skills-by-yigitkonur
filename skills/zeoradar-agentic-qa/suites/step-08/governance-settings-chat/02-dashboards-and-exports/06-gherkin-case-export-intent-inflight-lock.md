# TC-DB-06: Export Intent In-Flight Lock (`xpBusy`) and Concurrency Deduplication

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-06`
- **Purpose:** Verify that the asynchronous export intent engine (`assets/export-intent.js`) maintains an in-flight execution lock (`xpBusy[kind:format]`) that immediately suppresses parallel double-clicks of the same export kind/format by returning `{ ok: false, code: "busy" }`, preventing server-side compute thrashing and duplicate file downloads.
- **Target Result Directory:** `02-dashboards-and-exports/06-gherkin-result-case-export-intent-inflight-lock/`

---

## 2. Tester Brief
Heavy server-side export jobs (PDF rendering, large dataset CSVs) take several seconds to compile. Rapid double-clicking by users can trigger duplicate background worker runs.
1. `ZeoExport.run(opts)` checks `var busyKey = opts.kind + ":" + opts.format`.
2. If `xpBusy[busyKey]` is active, the second invocation is immediately short-circuited:
   `if (xpBusy[busyKey]) return Promise.resolve({ ok: false, code: "busy" });`
3. The first intent completes cleanly and triggers the hermetic file download anchor.
4. When the first promise settles, `delete xpBusy[busyKey]` unlocks the export channel.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/export-intent.js`.
- **Target Operation:** Parallel dispatch of `ZeoExport.run({ kind: "dashboard_pdf", format: "pdf" })`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Export Intent In-Flight Concurrency Deduplication

  Scenario: Rejecting simultaneous export requests of identical kind and format
    Given an export intent of kind "dashboard_pdf" and format "pdf" is in-flight
    When a duplicate export request for "dashboard_pdf:pdf" is triggered simultaneously
    Then the second request should immediately return status "busy"
    And only one server-side RPC command "create-export-intent" should be dispatched
    And upon settlement the in-flight lock should be released

    Examples:
      | ExportKind    | Format | ExpectedSecondResultCode |
      | dashboard_pdf | pdf    | busy                     |
      | viz_csv       | csv    | busy                     |
```

---

## 5. Visual Checks
- **Button Styling:**
  - Export trigger remains disabled while `xpBusy` is active.
- **Screenshot Points:**
  - `01_inflight_lock_state.png` (Disabled trigger during in-flight export).

---

## 6. Data and Network Checks
- **RPC Command Count:**
  - Exactly 1 invocation of `create-export-intent`.
- **Lock Verification:**
  - Result of second parallel promise returns `{ ok: false, code: "busy" }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/06-gherkin-result-case-export-intent-inflight-lock/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-export-lock');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const lockCheck = await js(String.raw`(() => {
  if (!window.ZeoExport || typeof window.ZeoExport.run !== "function") {
    return { skipped: true };
  }

  const p1 = window.ZeoExport.run({ kind: "dashboard_pdf", format: "pdf", filters: {} });
  const p2 = window.ZeoExport.run({ kind: "dashboard_pdf", format: "pdf", filters: {} });

  return Promise.all([p1, p2]).then(([r1, r2]) => {
    return {
      r1Ok: r1.ok,
      r2Code: r2.code,
      busyEnforced: r2.code === "busy"
    };
  }).catch(err => ({ error: err.message }));
})()`);

cliLog('Export Lock Result: ' + JSON.stringify(lockCheck));
if (!lockCheck.skipped && !lockCheck.busyEnforced) {
  throw new Error('Export intent in-flight lock failed to reject concurrent request');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-export-lock', { keep: false })`.
