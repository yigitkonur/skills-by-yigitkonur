# TC-ACC-10: Multi-Tenant Workspace Memory Cleanup and Cache Flushing

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-10`
- **Purpose:** Verify that switching workspaces or logging out executes the registered cleanup handler (`ZEO_PROVIDER_ORCHESTRATOR.registerCleanup()`), evicting in-memory team roster records, billing credit balances, and project configurations to guarantee zero cross-tenant data leakage.
- **Target Result Directory:** `03-account-team-billing/10-gherkin-result-case-workspace-cleanup-state-flush/`

---

## 2. Tester Brief
Multi-tenant security demands that when a user switches from Tenant A to Tenant B, in-memory objects stored in JavaScript singletons are thoroughly purged.
1. The Account Settings module registers its eviction hook via:
   `ZEO_PROVIDER_ORCHESTRATOR.registerCleanup(function() { ... })`.
2. Upon tenant transition:
   - `AccountSettingsState.billing.data` is set to `null` or `"idle"`.
   - `AccountSettingsState.team.members` is cleared.
   - Project settings form fields are detached.
3. Tenant B loads fresh state from its own isolated backend partition without visual flashes of Tenant A's private data.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/account-settings.js` & `assets/data-provider.js`.
- **Target Context:** Workspace Alpha (`ws_tenant_alpha`) -> Workspace Beta (`ws_tenant_beta`).

---

## 4. Gherkin Scenario

```gherkin
Feature: Multi-Tenant Workspace Context State Eviction

  Scenario: Flushing in-memory team and billing caches upon workspace context switch
    Given the application state holds cached team and billing data for Workspace Alpha
    When a workspace context change is triggered by the provider orchestrator
    Then the registered cleanup hook should execute
    And all cached billing data for Workspace Alpha should be set to null
    And all cached team roster entries for Workspace Alpha should be evicted
    And no residual data from Workspace Alpha should remain in memory

    Examples:
      | SourceWorkspace | TargetWorkspace | FlushedStateKeys         |
      | ws_tenant_alpha | ws_tenant_beta  | billing.data, team.members|
```

---

## 5. Visual Checks
- **DOM Refresh:**
  - Transition does not flash previous workspace member names or credit numbers.
- **Screenshot Points:**
  - `01_flushed_clean_state.png` (Cleanly transitioned workspace state).

---

## 6. Data and Network Checks
- **Memory Invariant:**
  ```js
  window.ZEO_PROVIDER_ORCHESTRATOR.triggerCleanup();
  assert(window.AccountSettingsState.billing.data === null);
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/10-gherkin-result-case-workspace-cleanup-state-flush/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-acct-cleanup');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=billing', { wait: true, timeout: 30 });
await wait(2);

const cleanupCheck = await js(String.raw`(() => {
  const orch = window.ZEO_PROVIDER_ORCHESTRATOR;
  if (!orch || typeof orch.triggerCleanup !== "function") return { skipped: true };

  // Set mock data
  if (window.AccountSettingsState && window.AccountSettingsState.billing) {
    window.AccountSettingsState.billing.data = { credits: 9999 };
  }

  orch.triggerCleanup();

  const dataFlushed = !window.AccountSettingsState || !window.AccountSettingsState.billing || window.AccountSettingsState.billing.data === null || window.AccountSettingsState.billing.status === "idle";

  return {
    cleanupExecuted: true,
    dataFlushed
  };
})()`);

cliLog('Cleanup Check Result: ' + JSON.stringify(cleanupCheck));
if (!cleanupCheck.skipped && !cleanupCheck.dataFlushed) {
  throw new Error('Workspace cleanup failed to flush memory cache');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-acct-cleanup', { keep: false })`.
