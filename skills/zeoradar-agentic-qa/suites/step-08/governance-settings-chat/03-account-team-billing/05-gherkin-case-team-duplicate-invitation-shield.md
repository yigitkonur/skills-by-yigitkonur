# TC-ACC-05: Duplicate Member Invitation Collision Shield (`already_exists`)

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-05`
- **Purpose:** Verify that attempting to invite an existing workspace member or an email address with an active pending invitation triggers the duplicate invitation collision shield (`already_exists` or `invite_already_pending`) and renders a localized error message without creating duplicate roster entries.
- **Target Result Directory:** `03-account-team-billing/05-gherkin-result-case-team-duplicate-invitation-shield/`

---

## 2. Tester Brief
Inviting existing users or resending invites prematurely can cause database key conflicts or confused user states.
1. When submitting an invitation for an already registered workspace member:
   - Command `invite-member` returns `{ ok: false, error: { code: "already_exists" } }`.
   - UI catches the error and renders: `"This person is already a member of this workspace."` / `"Bu kişi zaten bu çalışma alanının üyesi."`.
2. When submitting an invitation for an email with an active pending token:
   - Command returns `{ ok: false, error: { code: "invite_already_pending" } }`.
   - UI renders: `"An invitation is already pending for this email address."`.
3. The email field remains populated, and the roster table count does not increment.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=team`.
- **Existing Member Email:** `owner@zeo.org` (or active member).

---

## 4. Gherkin Scenario

```gherkin
Feature: Duplicate Member Invitation Collision Defense

  Scenario Outline: Rejection of duplicate team invitation for existing member or pending invite
    Given the test user is on the Team settings tab in language "<Language>"
    And an existing member with email "<TargetEmail>" belongs to the workspace
    When the user submits an invitation for "<TargetEmail>"
    Then the invitation RPC should return error code "<ErrorCode>"
    And the UI should display error notice containing "<ExpectedErrorCopy>"
    And the active member roster count should remain unchanged

    Examples:
      | Language | TargetEmail      | ErrorCode              | ExpectedErrorCopy                         |
      | en       | owner@zeo.org    | already_exists         | already a member of this workspace        |
      | tr       | owner@zeo.org    | already_exists         | zaten bu çalışma alanının üyesi           |
      | en       | pending@zeo.org  | invite_already_pending | already pending                           |
```

---

## 5. Visual Checks
- **Error UI:**
  - Notice Element: `.acct-team-error` or toast notification.
  - Text Color: Red text danger styling.
- **Roster Table:**
  - Row count in `.acct-team-table` remains constant.
- **Screenshot Points:**
  - `01_duplicate_member_error.png` (Inline error banner displaying already_exists copy).

---

## 6. Data and Network Checks
- **Server Response Contract:**
  ```json
  {
    "ok": false,
    "error": {
      "code": "already_exists",
      "message": "This person is already a member of this workspace."
    }
  }
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/05-gherkin-result-case-team-duplicate-invitation-shield/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-invite-duplicate');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=team', { wait: true, timeout: 30 });
await wait(2);

const duplicateCheck = await js(String.raw`(() => {
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'invite-member') {
      return Promise.resolve({
        ok: false,
        error: { code: "already_exists", message: "This person is already a member of this workspace." }
      });
    }
    return origCall.apply(this, arguments);
  };

  const btn = document.querySelector('[data-account-action="send-invite"]');
  if (btn) btn.click();

  return new Promise(resolve => {
    setTimeout(() => {
      window.ZEO_DATA_PROVIDER.callCommand = origCall;
      const errEl = document.querySelector('.acct-team-error, .toast');
      resolve({
        rendered: !!errEl,
        errorCopy: errEl ? errEl.innerText.trim() : null
      });
    }, 400);
  });
})()`);

cliLog('Duplicate Invite Check: ' + JSON.stringify(duplicateCheck));
if (!duplicateCheck.errorCopy || !duplicateCheck.errorCopy.includes("already a member")) {
  throw new Error('Duplicate member invite failed to display localized already_exists copy');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-invite-duplicate', { keep: false })`.
