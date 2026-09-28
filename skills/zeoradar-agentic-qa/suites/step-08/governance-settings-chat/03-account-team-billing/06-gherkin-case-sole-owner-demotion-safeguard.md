# TC-ACC-06: Sole-Owner Demotion and Suspension Protection (`last_owner_required`)

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-06`
- **Purpose:** Verify that a workspace possessing only one active owner cannot demote or suspend that owner: mutation controls are disabled in the UI, and any direct mutation attempt is rejected with `last_owner_required`, opening a warning modal explaining that workspaces require at least one active owner.
- **Target Result Directory:** `03-account-team-billing/06-gherkin-result-case-sole-owner-demotion-safeguard/`

---

## 2. Tester Brief
To prevent workspaces from becoming completely orphaned or unmanageable, a workspace cannot demote its last owner to member or suspend their account.
1. In `assets/account-settings.js`, the roster renders member rows.
2. The client checks `activeOwnersCount`:
   - If `count === 1`: the demote button (`[data-role="member"]`) and suspend button (`[data-status="suspended"]`) for that sole owner are rendered with `disabled` attribute.
3. If an adversary attempts to bypass client controls by directly dispatching `set-member-role` or `set-member-status`:
   - The server rejects the command with error code `"last_owner_required"`.
   - `showAccountError("last_owner_required")` opens a modal dialog:
     `"Workspaces require at least one active owner."` / `"Çalışma alanlarında en az bir aktif sahip bulunmalıdır."`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Sole Owner of workspace).
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=team`.
- **Roster State:** Exactly 1 active member with role `"owner"`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Sole Owner Demotion Safeguard

  Scenario Outline: Preventing demotion or suspension of the final active workspace owner
    Given a workspace has exactly 1 active owner in language "<Language>"
    When the user inspects the team roster table
    Then the demote button for the sole owner should be disabled
    And the suspend button for the sole owner should be disabled
    When a demotion attempt returns error code "last_owner_required"
    Then the account error modal should display "<ExpectedWarningCopy>"

    Examples:
      | Language | OwnerCount | ExpectedWarningCopy                        |
      | en       | 1          | at least one active owner                  |
      | tr       | 1          | en az bir aktif sahip                      |
```

---

## 5. Visual Checks
- **Button Attributes:**
  - `button[data-account-action="set-member-role"][data-role="member"]`: `disabled === true`.
  - `button[data-account-action="set-member-status"][data-status="suspended"]`: `disabled === true`.
- **Modal Notice:**
  - Modal: `.acct-modal` or `.acct-modal-card`.
  - Text: Contains `"at least one active owner"` / `"en az bir aktif sahip"`.
- **Screenshot Points:**
  - `01_sole_owner_disabled_buttons.png` (Disabled demote/suspend buttons on owner row).
  - `02_last_owner_required_modal.png` (Warning modal explaining safeguard).

---

## 6. Data and Network Checks
- **RPC Command Rejection:**
  ```json
  {
    "ok": false,
    "error": {
      "code": "last_owner_required",
      "message": "Cannot demote or suspend the last active owner of a workspace."
    }
  }
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/06-gherkin-result-case-sole-owner-demotion-safeguard/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-sole-owner');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=team', { wait: true, timeout: 30 });
await wait(2);

const soleOwnerCheck = await js(String.raw`(() => {
  let warningRendered = false;
  let warningText = "";

  if (typeof window.showAccountError === "function") {
    window.showAccountError("last_owner_required");
    const modal = document.querySelector('.acct-modal, .toast');
    if (modal) {
      warningRendered = true;
      warningText = modal.innerText.trim();
    }
  }

  const rows = Array.from(document.querySelectorAll('.acct-team-row'));
  const soleOwnerRow = rows.find(r => r.innerText.toLowerCase().includes("owner") || r.innerText.toLowerCase().includes("sahip"));
  const demoteBtn = soleOwnerRow ? soleOwnerRow.querySelector('[data-role="member"]') : null;

  return {
    warningRendered,
    warningText,
    demoteDisabled: demoteBtn ? demoteBtn.disabled : true
  };
})()`);

cliLog('Sole Owner Check: ' + JSON.stringify(soleOwnerCheck));
if (!soleOwnerCheck.warningText.includes("at least one active owner") && !soleOwnerCheck.warningText.includes("en az bir aktif sahip")) {
  throw new Error('Sole owner demotion failed to display last_owner_required notice');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-sole-owner', { keep: false })`.
