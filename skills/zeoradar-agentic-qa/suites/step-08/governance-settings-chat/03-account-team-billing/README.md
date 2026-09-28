# Step 08.3 — Account, Team Governance & Billing Engine QA Suite

## 1. Overview & Architecture

The Zeo Geo-Radar Account, Team Governance, and Billing subsystem provides tenant security, role-based access control (RBAC), multi-user team roster management, project tracking configurations, and Stripe billing lifecycle integrations.

This test suite provides granular, adversarial, code-grounded Gherkin test cases verifying:
- Atomic project settings persistence via a single unified `update-project-settings` RPC payload (brand name, brand domain, owned eTLD+1 domains, cadence, weekday), preventing partial-update drift.
- Competitor tracking and pinning (`[data-action="toggle-pin"]`) updating visual display priority without mutating ranking calculation denominators.
- Citation taxonomy tagging and entity alias disambiguation with duplicate mapping collision prevention.
- Team member invitation governance permanently enforcing the `"member"` role upon invite dispatch.
- Duplicate invitation shields rejecting existing members (`already_exists`) and pending invites (`invite_already_pending`).
- Sole active owner protection (`last_owner_required`) disabling demotion and suspension controls when `ownerCount === 1`.
- Non-destructive team member suspension (`status: "suspended"`) preserving historical authorship audit records while terminating session access.
- Unprovisioned Stripe customer detection routing to `openUnlinkedCustomerModal()` and subscription tier upgrade flows.
- Credit meter visualization and server-authoritative run authorization enforcing `1 credit = 1 execution cell`.
- Multi-tenant workspace memory cleanup (`orch.triggerCleanup()`) clearing module caches on context switch.

---

## 2. Vocabulary & Placeholders

All test cases in this directory adhere to the standardized parameter vocabulary:

| Placeholder | Semantic Type | Description / Example Values |
| :--- | :--- | :--- |
| `[DOMAIN]` | Domain Name | Workspace primary brand domain (e.g., `zeo.org`, `acme.com`). |
| `[COUNTRY]` | Market Country Code | Monitoring region ISO code (e.g., `US`, `TR`, `UK`). |
| `[LANGUAGE]` | Language Code | Application UI language (e.g., `en`, `tr`). |
| `[PROJECT_ID]` | UUID / String | Unique identifier of active project (e.g., `proj_01j7xyz...`). |
| `[WORKSPACE_ID]` | UUID / String | Tenant workspace identifier (e.g., `ws_01j7abc...`). |
| `[MEMBER_EMAIL]` | Email Address | Team member email (e.g., `analyst@zeo.org`, `agency@partner.com`). |
| `[MEMBER_ROLE]` | Role Enum | Workspace permission tier (`owner` or `member`). |
| `[MEMBER_STATUS]` | Status Enum | Team membership status (`active` or `suspended`). |
| `[CADENCE]` | Cadence Enum | Background run interval (`daily` or `weekly`). |
| `[CREDIT_USAGE]` | Integer | Consumed execution credits (1 credit = 1 prompt evaluated on 1 engine). |

---

## 3. Ego Browser / MacBook Execution Model

Test execution runs within an isolated **Ego Browser** instance operating on a remote host (MacBook environment):
1. **Remote Execution:** Automated driver scripts are executed on the MacBook via SSH using the `ego-browser nodejs` CLI harness.
2. **Artifact Generation:** Visual snapshots and DOM states are captured directly in the remote browser context and saved to local paths on the MacBook.
3. **Evidence Ingestion (SCP):** The executor retrieves captured screenshots from the MacBook via SCP (`scp macbook:/tmp/ego-artifacts/*.png <case-result-dir>/`) before compiling the final execution report.
4. **Result Directories:** Each test case references its designated result directory following the convention:
   `03-account-team-billing/01-gherkin-result-case-<short-slug>/`. Result directories are created exclusively upon test execution, never pre-populated with empty folders.

---

## 4. Test Case Inventory

| Case File | Title & Core Verification | Scenarios Covered |
| :--- | :--- | :--- |
| [`01-gherkin-case-project-settings-atomic-save.md`](./01-gherkin-case-project-settings-atomic-save.md) | Project Settings Atomic Persistence | Unified `update-project-settings` call for brand, domains, and cadence. |
| [`02-gherkin-case-competitor-pinning-order.md`](./02-gherkin-case-competitor-pinning-order.md) | Competitor Pinning Order vs Math Invariant | `toggle-pin` alters visual priority without altering ranking denominators. |
| [`03-gherkin-case-citation-tags-and-aliases.md`](./03-gherkin-case-citation-tags-and-aliases.md) | Citation Tags & Entity Alias Triage | 7-category taxonomy tagging, alias mapping, duplicate protection. |
| [`04-gherkin-case-team-invitation-member-role.md`](./04-gherkin-case-team-invitation-member-role.md) | Team Invitation Member Role Restriction | Forcing `role: "member"` on invitation dispatch; promotion flow. |
| [`05-gherkin-case-team-duplicate-invitation-shield.md`](./05-gherkin-case-team-duplicate-invitation-shield.md) | Duplicate Team Invitation Collision Shield | Rejection copy for `already_exists` and `invite_already_pending`. |
| [`06-gherkin-case-sole-owner-demotion-safeguard.md`](./06-gherkin-case-sole-owner-demotion-safeguard.md) | Sole-Owner Demotion Protection | Disabling controls and throwing `last_owner_required` on demotion attempt. |
| [`07-gherkin-case-non-destructive-member-suspension.md`](./07-gherkin-case-non-destructive-member-suspension.md) | Non-Destructive Member Suspension | Setting `status: "suspended"` while preserving audit log authorship. |
| [`08-gherkin-case-unprovisioned-stripe-customer.md`](./08-gherkin-case-unprovisioned-stripe-customer.md) | Unprovisioned Stripe Customer Handling | Handling `customer_unlinked` with `openUnlinkedCustomerModal()`. |
| [`09-gherkin-case-credit-meter-and-quota-policy.md`](./09-gherkin-case-credit-meter-and-quota-policy.md) | Credit Meter & Server-Authoritative Quota | 1 credit = 1 execution cell, visual progress, `insufficient_credits`. |
| [`10-gherkin-case-workspace-cleanup-state-flush.md`](./10-gherkin-case-workspace-cleanup-state-flush.md) | Workspace Context Cleanup & Cache Eviction | `triggerCleanup()` flushing billing and team memory caches on switch. |

---

## 5. Traceability & Coverage Matrix

| Original Monolithic Section (`03-account-team-billing.md`) | New Modular Case File | Coverage Status | Notes & Invariants Added |
| :--- | :--- | :---: | :--- |
| **Section 1 & 5.1**: Atomic Project Settings Persistence | `01-gherkin-case-project-settings-atomic-save.md` | Full | Unified `update-project-settings` call prevents partial state drift. |
| **Section 1 (Invariant 2) & 2.2**: Competitor Pinning | `02-gherkin-case-competitor-pinning-order.md` | Full | Asserts pinning alters visual order only; calculation denominators untouched. |
| **Section 2.3 & 2.4**: Citation Tags & Entity Aliases | `03-gherkin-case-citation-tags-and-aliases.md` | Full | Tests 7 taxonomy tags and duplicate alias assignment rejection. |
| **Section 1 (Invariant 3) & 3.2**: Team Invitation Role | `04-gherkin-case-team-invitation-member-role.md` | Full | Enforces permanently locked `role: "member"` at invitation time. |
| **Section 1 (Invariant 4) & 5.2**: Duplicate Invitation Shield | `05-gherkin-case-team-duplicate-invitation-shield.md` | Full | Asserts localized error notice on `already_exists` collision. |
| **Section 1 (Invariant 5) & 5.3**: Sole Owner Protection | `06-gherkin-case-sole-owner-demotion-safeguard.md` | Full | Disables demote/suspend buttons when `ownerCount === 1`; asserts warning modal. |
| **Section 1 (Invariant 6) & 3.2**: Non-Destructive Suspension | `07-gherkin-case-non-destructive-member-suspension.md` | Full | Validates `status: "suspended"` RPC preserves audit logs (no hard deletes). |
| **Section 1 (Invariant 7) & 5.4**: Unprovisioned Stripe Customer | `08-gherkin-case-unprovisioned-stripe-customer.md` | Full | Tests `customer_unlinked` triggering `openUnlinkedCustomerModal()`. |
| **Section 1 (Invariant 8) & 5.5**: Credit Meter & Quotas | `09-gherkin-case-credit-meter-and-quota-policy.md` | Full | Validates 1 credit = 1 cell note, meter bar, and `insufficient_credits` error. |
| **Section 1 (Invariant 9) & 5.6**: Tenant Context Cleanup | `10-gherkin-case-workspace-cleanup-state-flush.md` | Full | Validates `registerCleanup()` flushing `state.billing` and `state.team`. |
