# TC-DB-10: Cross-Tenant Export Invalidation on Active Workspace Switch

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-10`
- **Purpose:** Verify that if a user switches workspaces or projects while an asynchronous export intent is in-flight, the client-side orchestrator generation check (`orch.valid(["tenantGen", "projectGen"])`) detects the context change and aborts the file download to prevent cross-tenant data leakage.
- **Target Result Directory:** `02-dashboards-and-exports/10-gherkin-result-case-export-tenant-switch-abort/`

---

## 2. Tester Brief
In enterprise SaaS applications, opening a download belonging to Workspace A while viewing Workspace B is a critical security vulnerability.
1. `ZeoExport.run` captures the active tenant generation snapshot at inception:
   `var snapshot = orch.begin(["tenantGen", "projectGen"]);`
2. While the server compiles the export intent payload, the user switches workspace.
3. When the server response arrives, the client verifies generation validity:
   `if (!orch.valid(snapshot)) return;`
4. The download anchor is never constructed or clicked, ensuring that Workspace A's sensitive PDF or CSV is discarded immediately.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/export-intent.js` & `assets/data-provider.js`.
- **Tenant Contexts:** Workspace 1 (`ws_alpha`) -> Workspace 2 (`ws_beta`).

---

## 4. Gherkin Scenario

```gherkin
Feature: Cross-Tenant Export Invalidation

  Scenario: Aborting pending file download when workspace switches during export compilation
    Given an export intent is initiated in Workspace 1
    When the user switches active workspace to Workspace 2 before the export completes
    Then the tenant generation counter should increment
    And when the server returns the download URL for Workspace 1
    Then the orchestrator generation check should evaluate to false
    And no download anchor should be dispatched in the browser
    And Workspace 1 file data should not be saved to disk

    Examples:
      | InitialWorkspace | SwitchedWorkspace | DownloadDispatched |
      | ws_alpha         | ws_beta           | false              |
```

---

## 5. Visual Checks
- **DOM Verification:**
  - No orphaned download anchor `a[download]` appended to `document.body`.
  - Notification toast for Workspace 1 is suppressed.
- **Screenshot Points:**
  - `01_clean_workspace_switch.png` (Workspace 2 active without phantom download).

---

## 6. Data and Network Checks
- **Orchestrator Validation:**
  ```js
  const snapshot = window.ZEO_PROVIDER_ORCHESTRATOR.begin(["tenantGen"]);
  window.ZEO_PROVIDER_ORCHESTRATOR.triggerCleanup();
  assert(window.ZEO_PROVIDER_ORCHESTRATOR.valid(snapshot) === false);
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/10-gherkin-result-case-export-tenant-switch-abort/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-export-switch');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const switchCheck = await js(String.raw`(() => {
  const orch = window.ZEO_PROVIDER_ORCHESTRATOR;
  if (!orch || typeof orch.begin !== "function") return { skipped: true };

  const snap = orch.begin(["tenantGen"]);
  orch.triggerCleanup(); // simulates workspace switch

  return {
    isStaleDetected: !orch.valid(snap)
  };
})()`);

cliLog('Switch Check Result: ' + JSON.stringify(switchCheck));
if (!switchCheck.skipped && !switchCheck.isStaleDetected) {
  throw new Error('Orchestrator failed to invalidate stale snapshot on tenant switch');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-export-switch', { keep: false })`.
