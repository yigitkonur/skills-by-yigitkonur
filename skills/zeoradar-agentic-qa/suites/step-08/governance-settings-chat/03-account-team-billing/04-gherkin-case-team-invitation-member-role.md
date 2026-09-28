# TC-ACC-04: Team Member Invitation Lifecycle and Mandatory Member Role Restriction

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-04`
- **Purpose:** Verify that inviting new team members strictly forces `role: "member"` in the invitation payload, preventing accidental or unauthorized invitation of external users with owner privileges, and requiring explicit post-acceptance promotion via `set-member-role`.
- **Target Result Directory:** `03-account-team-billing/04-gherkin-result-case-team-invitation-member-role/`

---

## 2. Tester Brief
Workspace security governance requires that external collaborators can never be onboarded directly into the owner role.
1. The user navigates to Account Settings -> Team (`#/[SLUG]/account?tab=team`).
2. Clicking `[data-account-action="send-invite"]` dispatches `invite-member`.
3. The client payload is hardcoded to `{ workspaceId, email, role: "member" }`.
4. The invitation appears in the Pending Invitations table with role badge `"Member"`.
5. Granting owner privileges can only occur after the invite is accepted, via explicit owner promotion.
6. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=team`.
- **Target Invite Email:** `new-colleague@zeo.org`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Team Invitation Role Restriction

  Scenario: Inviting a new team member with mandatory member role restriction
    Given the test user is an owner on the Team settings subtab
    When the user enters candidate email "new-colleague@zeo.org"
    And the user clicks the send invite button "[data-account-action='send-invite']"
    Then the RPC command "invite-member" should be called with role strictly set to "member"
    And the pending invitations table should list "new-colleague@zeo.org" with role "Member"
    And no option to invite directly as "Owner" should exist in the form

    Examples:
      | InviteEmail            | DispatchedRole | PendingBadge |
      | new-colleague@zeo.org  | member         | Member       |
      | external-qa@agency.com | member         | Member       |
```

---

## 5. Visual Checks
- **Form Controls:**
  - Email Input: `input[data-account-field="invite-email"]` or `#invite-member-email`.
  - Role Selector: Must be absent or locked to `"Member"`.
  - Submit Button: `button[data-account-action="send-invite"]`.
- **Pending Table:**
  - Table: `.acct-pending-table`.
  - Role Column: Displays `.badge` with `"Member"`.
- **Screenshot Points:**
  - `01_team_invite_form.png` (Invitation form with member role invariant).
  - `02_pending_invite_row.png` (Pending invitation row showing Member role).

---

## 6. Data and Network Checks
- **Command RPC:**
  ```json
  {
    "workspaceId": "[WORKSPACE_ID]",
    "email": "new-colleague@zeo.org",
    "role": "member"
  }
  ```
- **Server Invariant:** Any attempt to inject `role: "owner"` returns `validation_failed`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/04-gherkin-result-case-team-invitation-member-role/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-invite-role');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=team', { wait: true, timeout: 30 });
await wait(2);

const inviteCheck = await js(String.raw`(() => {
  let capturedRole = null;
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'invite-member') {
      capturedRole = payload.role;
      return Promise.resolve({ ok: true, data: { invite: { id: "inv_123", email: payload.email, role: "member" } } });
    }
    return origCall.apply(this, arguments);
  };

  const emailInp = document.querySelector('input[data-account-field="invite-email"]') || document.getElementById('invite-member-email');
  if (emailInp) emailInp.value = "test-invite@zeo.org";

  const btn = document.querySelector('[data-account-action="send-invite"]');
  if (btn) btn.click();

  window.ZEO_DATA_PROVIDER.callCommand = origCall;

  return {
    dispatchedRole: capturedRole,
    strictlyMember: capturedRole === "member"
  };
})()`);

cliLog('Invite Role Result: ' + JSON.stringify(inviteCheck));
if (!inviteCheck.strictlyMember) {
  throw new Error('Team invite failed to enforce mandatory role: "member"');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-invite-role', { keep: false })`.
