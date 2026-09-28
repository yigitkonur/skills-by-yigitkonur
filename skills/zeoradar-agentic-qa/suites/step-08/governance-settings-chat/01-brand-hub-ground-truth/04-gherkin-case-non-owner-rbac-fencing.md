# TC-BH-04: Non-Owner Role Fencing and Read-Only Security Invariant

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-04`
- **Purpose:** Verify that a workspace member who does NOT possess the Owner role is strictly fenced into read-only Brand Hub mode: the header displays a `Read-only (Member)` badge, top-level mutation triggers (Edit Voice, Add Fact) are suppressed, and inline fact management actions (edit, quick verify, dispute, archive) are completely removed from the DOM.
- **Target Result Directory:** `01-brand-hub-ground-truth/04-gherkin-result-case-non-owner-rbac-fencing/`

---

## 2. Tester Brief
Security and governance require that only workspace owners define or mutate Ground Truth facts and brand voice guidelines.
1. The resolver `resolveBrandHubOwner(workspaceId)` determines write authority.
2. When evaluated as non-owner (`isOwner === false`):
   - The header displays `<span class="badge soft">Read-only (Member)</span>`.
   - Mutation action buttons in `.brand-hub-actions` are replaced with a quiet informational note: `"Owner role required to modify Brand Hub"`.
   - Fact card headers (`.bh-fact-head`) must NOT render any action buttons (`edit`, `verify`, `dispute`, `archive`).
3. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `team-member@zeogen.com` (Role: `"member"`).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb`
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[WORKSPACE_ID]`: `ws_01j7abc...`
  - `[MEMBER_ROLE]`: `"member"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Non-Owner Brand Hub RBAC Guardrails

  Scenario Outline: Read-only UI enforcement for non-owner workspace member
    Given the test user is signed in with role "<UserRole>"
    And the workspace owner resolver evaluates to <IsOwner>
    When the user navigates to the Brand Hub route
    Then the header should display the read-only badge containing "<BadgeText>"
    And the "Add Fact" button "button[data-action='bh-open-fact-drawer']" should not exist
    And the "Edit Voice" button "button[data-action='bh-open-voice-drawer']" should not exist
    And the fact cards should not render any mutation action buttons in ".bh-fact-head"

    Examples:
      | UserRole | IsOwner | BadgeText           |
      | member   | false   | Read-only (Member)  |
      | viewer   | false   | Read-only           |
```

---

## 5. Visual Checks
- **Header Elements:**
  - Role Status Badge: `<span class="badge soft"><svg>...</svg> Read-only (Member)</span>`.
  - Informational Copy: `.dim.small` with `"Owner role required to modify Brand Hub"` (or `"Marka Kiti'ni değiştirmek için Sahip rolü gereklidir"`).
- **Suppressed Elements:**
  - `button[data-action="bh-open-voice-drawer"]` must be ABSENT.
  - `button[data-action="bh-open-fact-drawer"]` must be ABSENT.
  - Fact card header buttons `.bh-fact-head button` count must equal 0.
- **Screenshot Points:**
  - `01_non_owner_header_badge.png` (Brand Hub header showing Read-only badge and missing action buttons).
  - `02_non_owner_fact_cards.png` (Fact cards rendered without action controls).

---

## 6. Data and Network Checks
- **Client State Assertion:**
  - `window.state.brandHub.isOwner === false`.
- **Command Security Guard:**
  - In the event of manual console injection of `dp.callCommand("update-brand-hub", payload)`, server returns `{ ok: false, error: { code: "forbidden", message: "Owner role required" } }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/04-gherkin-result-case-non-owner-rbac-fencing/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-rbac');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

// Impersonate non-owner member role
const setup = await js(String.raw`(() => {
  window.__origResolver = window.resolveBrandHubOwner;
  window.resolveBrandHubOwner = () => false;
  if (window.state && window.state.brandHub) {
    window.state.brandHub.isOwner = false;
  }
  if (typeof render === "function") render();
  return { simulated: true };
})()`);

await wait(1);

const rbacState = await js(String.raw`(() => {
  const badge = document.querySelector('.badge.soft');
  const addBtn = document.querySelector('button[data-action="bh-open-fact-drawer"]');
  const editVoiceBtn = document.querySelector('button[data-action="bh-open-voice-drawer"]');
  const factBtns = document.querySelectorAll('.bh-fact-head button');

  return {
    badgeText: badge ? badge.innerText.trim() : null,
    addBtnFound: !!addBtn,
    editVoiceBtnFound: !!editVoiceBtn,
    factActionBtnsCount: factBtns.length
  };
})()`);

// Restore resolver
await js(String.raw`(() => {
  if (window.__origResolver) window.resolveBrandHubOwner = window.__origResolver;
  if (window.state && window.state.brandHub) window.state.brandHub.isOwner = true;
  if (typeof render === "function") render();
})()`);

cliLog('RBAC State Assertions: ' + JSON.stringify(rbacState));
if (!rbacState.badgeText || !rbacState.badgeText.includes("Read-only") && !rbacState.badgeText.includes("Salt-okunur")) {
  throw new Error('Read-only badge missing for non-owner member');
}
if (rbacState.addBtnFound || rbacState.editVoiceBtnFound || rbacState.factActionBtnsCount > 0) {
  throw new Error('Mutation buttons leaked to non-owner member UI');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-rbac', { keep: false })`.
