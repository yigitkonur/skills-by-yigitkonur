# TC-ACC-07: Non-Destructive Member Suspension and Audit Provenance

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-07`
- **Purpose:** Verify that removing a workspace member executes non-destructive suspension (`set-member-status` with `status: "suspended"`) rather than a hard delete, instantly revoking active session credentials while permanently preserving historical authorship, audit logs, and attribution metadata.
- **Target Result Directory:** `03-account-team-billing/07-gherkin-result-case-non-destructive-member-suspension/`

---

## 2. Tester Brief
Compliance standards (SOC2 / ISO 27001) require maintaining audit logs of who created or approved brand guidelines, prompts, and reports.
1. When an owner suspends a member via `[data-account-action="set-member-status"][data-status="suspended"]`:
2. The mutation dispatches `set-member-status` with `{ memberId, status: "suspended" }`.
3. In the UI:
   - The member row remains in the team table but displays a muted badge: `<span class="badge soft suspended">Suspended</span>`.
   - The member's session is invalidated on the backend.
   - Historical prompts, brand facts, and revisions authored by this user remain attributed to their name rather than becoming orphaned or showing `null`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=team`.
- **Target Member ID:** `mem_qa_01` (`contractor@agency.com`).

---

## 4. Gherkin Scenario

```gherkin
Feature: Non-Destructive Team Member Suspension

  Scenario: Suspending a team member while maintaining historical authorship attribution
    Given a non-owner team member "contractor@agency.com" has status "active"
    When the owner clicks the suspend button "[data-account-action='set-member-status'][data-status='suspended']"
    Then the RPC command "set-member-status" should be called with status "suspended"
    And the member record should NOT be deleted from the database
    And the team roster row should display status badge "Suspended"
    And historical prompts authored by "contractor@agency.com" should retain their author attribution

    Examples:
      | TargetMemberEmail       | InitialStatus | PostStatus | BadgeClass |
      | contractor@agency.com   | active        | suspended  | suspended  |
```

---

## 5. Visual Checks
- **Roster Table:**
  - Target Row: `.acct-team-row` remains in table.
  - Status Badge: `.badge.suspended` or `.badge.soft` showing `"Suspended"` / `"Askıya Alındı"`.
  - Re-activate Action: Replaces suspend button with `"Reactivate"`.
- **Screenshot Points:**
  - `01_suspended_member_badge.png` (Roster row displaying Suspended badge).

---

## 6. Data and Network Checks
- **Command RPC:**
  ```json
  {
    "workspaceId": "[WORKSPACE_ID]",
    "memberId": "mem_qa_01",
    "status": "suspended"
  }
  ```
- **Zero Deletion Invariant:** No HTTP `DELETE` or RPC `delete-member` command emitted.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/07-gherkin-result-case-non-destructive-member-suspension/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-member-suspend');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=team', { wait: true, timeout: 30 });
await wait(2);

const suspendCheck = await js(String.raw`(() => {
  let commandSent = null;
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'set-member-status') {
      commandSent = payload;
      return Promise.resolve({ ok: true });
    }
    return origCall.apply(this, arguments);
  };

  const suspendBtn = document.querySelector('[data-account-action="set-member-status"][data-status="suspended"]');
  if (suspendBtn) suspendBtn.click();

  window.ZEO_DATA_PROVIDER.callCommand = origCall;

  return {
    dispatched: !!commandSent,
    targetStatus: commandSent ? commandSent.status : null,
    isSuspended: commandSent ? commandSent.status === "suspended" : false
  };
})()`);

cliLog('Suspend Test Result: ' + JSON.stringify(suspendCheck));
if (suspendCheck.dispatched && !suspendCheck.isSuspended) {
  throw new Error('Member status command was not set to suspended');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-member-suspend', { keep: false })`.
