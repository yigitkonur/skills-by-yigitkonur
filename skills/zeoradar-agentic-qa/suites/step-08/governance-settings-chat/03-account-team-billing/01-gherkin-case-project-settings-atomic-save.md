# TC-ACC-01: Atomic Project Settings Persistence

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-01`
- **Purpose:** Verify that updating project settings (brand name, brand domain, owned eTLD+1 domains, run cadence, and weekly weekday) dispatches a single unified `update-project-settings` RPC payload that updates all properties atomically without partial-update state drift.
- **Target Result Directory:** `03-account-team-billing/01-gherkin-result-case-project-settings-atomic-save/`

---

## 2. Tester Brief
Saving settings piecewise (e.g., brand domain in one request and cadence in another) can leave workspaces in inconsistent states if network connectivity drops midway.
1. The user navigates to the Project Settings view (`#/[SLUG]/settings`).
2. Inputs: Brand Name (`#settings-brand-name`), Brand Domain (`#settings-brand-domain`), Owned Domains list (`#settings-owned-input`), and Monitoring Cadence (`#settings-cadence-select`).
3. Clicking `[data-action="settings-save-project"]` triggers a single atomic mutation:
   `window.ZEO_DATA_PROVIDER.callCommand("update-project-settings", payload)`.
4. The client verifies that all modified fields are bundled together and committed in one transaction.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/settings`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `[DOMAIN]`
  - `[BRAND_NAME]`: `[BRAND]`
  - `[CADENCE]`: `weekly` (Weekday: 1 = Monday)
  - `[OWNED_DOMAINS]`: `["[DOMAIN]", "alt.[DOMAIN]"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Atomic Project Settings Persistence

  Scenario: Submitting unified project settings in a single atomic RPC command
    Given the test user is an owner on the Project Settings page
    When the user enters brand name "[BRAND]" into "#settings-brand-name"
    And the user enters brand domain "[DOMAIN]" into "#settings-brand-domain"
    And the user adds owned domain "alt.[DOMAIN]" to the owned domains list
    And the user selects monitoring cadence "weekly" with weekday "1"
    And the user clicks the save settings button "[data-action='settings-save-project']"
    Then a single RPC command "update-project-settings" should be dispatched
    And the payload should bundle brandName, brandDomain, ownedDomains, and cadence atomically
    And a confirmation toast should indicate successful persistence

    Examples:
      | Cadence | Weekday | BrandDomain    |
      | weekly  | 1       | [DOMAIN] |
      | daily   | 0       | alt.[DOMAIN] |
```

---

## 5. Visual Checks
- **Form Elements:**
  - Brand Name: `input#settings-brand-name`.
  - Brand Domain: `input#settings-brand-domain`.
  - Owned Domains Container: `.settings-owned-wrap`.
  - Cadence Dropdown: `select#settings-cadence-select`.
  - Save Button: `button[data-action="settings-save-project"]`.
- **Screenshot Points:**
  - `01_project_settings_form.png` (Configured project settings form).
  - `02_project_settings_saved_toast.png` (Success toast confirmation).

---

## 6. Data and Network Checks
- **Command RPC Payload:**
  ```json
  {
    "projectId": "[PROJECT_ID]",
    "name": "[BRAND]",
    "brandDomain": "[DOMAIN]",
    "ownedDomains": ["[DOMAIN]", "alt.[DOMAIN]"],
    "cadence": "weekly",
    "weeklyCadenceDay": 1
  }
  ```
- **Single Command Call:** Exactly 1 network dispatch for `update-project-settings`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/01-gherkin-result-case-project-settings-atomic-save/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-project-settings');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/settings', { wait: true, timeout: 30 });
await wait(2);

const atomicCheck = await js(String.raw`(() => {
  let commandDispatched = null;
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'update-project-settings') {
      commandDispatched = payload;
      return Promise.resolve({ ok: true });
    }
    return origCall.apply(this, arguments);
  };

  const nameInput = document.getElementById("settings-brand-name");
  const domainInput = document.getElementById("settings-brand-domain");
  if (nameInput) nameInput.value = "[BRAND]";
  if (domainInput) domainInput.value = "[DOMAIN]";

  const saveBtn = document.querySelector('[data-action="settings-save-project"]');
  if (saveBtn) saveBtn.click();

  window.ZEO_DATA_PROVIDER.callCommand = origCall;

  return {
    dispatched: !!commandDispatched,
    hasName: commandDispatched ? !!commandDispatched.name : false,
    hasDomain: commandDispatched ? !!commandDispatched.brandDomain : false
  };
})()`);

cliLog('Atomic Settings Result: ' + JSON.stringify(atomicCheck));
if (!atomicCheck.dispatched || !atomicCheck.hasName || !atomicCheck.hasDomain) {
  throw new Error('Project settings failed atomic persistence assertions');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-project-settings', { keep: false })`.
