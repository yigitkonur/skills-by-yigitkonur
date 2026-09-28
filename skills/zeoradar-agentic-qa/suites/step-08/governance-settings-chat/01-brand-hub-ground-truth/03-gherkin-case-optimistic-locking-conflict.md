# TC-BH-03: Optimistic Concurrency Locking Conflict and Stale Version Handling

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-03`
- **Purpose:** Verify that when a concurrent mutation increments the server-side Brand Hub version, any client attempt to save changes with a stale `expectedVersion` is rejected with a `stale_version` error, displaying the drawer conflict banner, main page alert, and reload retry trigger without silent data loss.
- **Target Result Directory:** `01-brand-hub-ground-truth/03-gherkin-result-case-optimistic-locking-conflict/`

---

## 2. Tester Brief
In distributed multi-user environments, two administrators might edit Brand Hub simultaneously.
1. The client maintains local `expectedVersion` matching the last loaded resource.
2. If another session saves first, the server increments `version` (e.g. from 1 to 2).
3. The slower client submits `expectedVersion: 1`.
4. The server rejects the mutation with `{ code: "validation_failed", details: { fields: [{ field: "expectedVersion", code: "stale_version" }] } }`.
5. The UI must catch this error, retain the user's uncommitted form draft, and prominently render `.bh-conflict-alert` with reload action `button[data-action="bh-retry"]`.
6. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb`
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[CURRENT_VERSION]`: Current server version (e.g., `2`).
  - `[STALE_VERSION]`: Stale expected version passed by client (e.g., `1`).

---

## 4. Gherkin Scenario

```gherkin
Feature: Optimistic Concurrency Control Conflict Resolution

  Scenario Outline: Stale expectedVersion conflict detection during concurrent mutation
    Given the test user is editing Brand Hub in language "<Language>"
    And the current server Brand Hub version is <ServerVersion>
    When a concurrent update modifies the server version to <NewServerVersion>
    And the user attempts to submit a Brand Hub change passing stale expectedVersion <StaleVersion>
    Then the mutation command should be rejected with code "stale_version"
    And the drawer should display conflict alert ".bh-conflict-alert.bh-drawer-alert"
    And the conflict alert text should contain "<ExpectedConflictText>"
    And the main surface should render reload button "button[data-action='bh-retry']"

    Examples:
      | Language | ServerVersion | NewServerVersion | StaleVersion | ExpectedConflictText                             |
      | en       | 1             | 2                | 1            | This Brand Hub was modified by another session.  |
      | tr       | 3             | 4                | 3            | başka bir oturum tarafından değiştirildi         |
```

---

## 5. Visual Checks
- **Conflict Elements:**
  - Drawer Conflict Card: `.bh-conflict-alert.bh-drawer-alert.card`.
  - Icon: SVG alert exclamation mark.
  - Page-Level Conflict Alert: `.bh-conflict-alert.card`.
  - Reload Action: `button.btn.small[data-action="bh-retry"]`.
- **Form State Preservation:**
  - Input values in `#bhFactStatement` or `#bhVoiceAbout` must NOT be cleared when conflict displays.
- **Screenshot Points:**
  - `01_drawer_conflict_banner.png` (Conflict alert inside the open drawer).
  - `02_main_conflict_reload_alert.png` (Main page conflict notice with reload button).

---

## 6. Data and Network Checks
- **Simulated Conflict Response:**
  ```json
  {
    "ok": false,
    "error": {
      "code": "validation_failed",
      "message": "Validation failed",
      "details": {
        "fields": [{
          "field": "expectedVersion",
          "code": "stale_version",
          "message": "Version mismatch: resource was updated concurrently"
        }]
      }
    }
  }
  ```
- **Client State Assertion:**
  - `window.state.brandHub.drawer.error` contains the localized conflict message.
  - Form retains dirty status without discarding user text.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/03-gherkin-result-case-optimistic-locking-conflict/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-conflict');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

// Intercept update-brand-hub to inject stale_version error
const conflictSim = await js(String.raw`(() => {
  const orig = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = function (cmd, payload) {
    if (cmd === 'update-brand-hub') {
      window.ZEO_DATA_PROVIDER.callCommand = orig;
      return Promise.resolve({
        ok: false,
        error: {
          code: "validation_failed",
          details: {
            fields: [{ field: "expectedVersion", code: "stale_version" }]
          }
        }
      });
    }
    return orig.apply(this, arguments);
  };

  const bhs = window.state.brandHub;
  bhs.drawer.open = true;
  bhs.drawer.type = "fact";
  bhs.drawer.data = { factKey: "conflict_test", statement: "Conflicting data" };
  if (typeof window.renderBrandHubDrawer === "function") window.renderBrandHubDrawer();

  const saveBtn = document.querySelector('button[data-action="bh-save-durable"]');
  if (saveBtn) saveBtn.click();
  return { triggered: true };
})()`);

await wait(2);

const bannerCheck = await js(String.raw`(() => {
  const drawerAlert = document.querySelector('.bh-conflict-alert.bh-drawer-alert');
  const retryBtn = document.querySelector('button[data-action="bh-retry"]');
  return {
    hasDrawerAlert: !!drawerAlert,
    alertText: drawerAlert ? drawerAlert.innerText.trim() : null,
    hasRetryBtn: !!retryBtn
  };
})()`);

cliLog('Conflict Banner Assertions: ' + JSON.stringify(bannerCheck));
if (!bannerCheck.hasDrawerAlert || !bannerCheck.alertText.includes("another session") && !bannerCheck.alertText.includes("başka bir oturum")) {
  throw new Error('Optimistic concurrency stale_version banner failed to render expected text');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-conflict', { keep: false })`.
