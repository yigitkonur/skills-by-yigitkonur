# Step 08.1 — Brand Hub (Ground Truth) & Knowledge Base QA Suite

## 1. Overview & Architecture

The Brand Hub subsystem serves as the authoritative source of truth for Answer Engine Optimization (AEO) and Generative Engine Optimization (GEO). It manages brand voice positioning, verified factual statements, contradiction detection telemetry (Truth Vault), and corporate entity hierarchy DAGs.

This test suite provides granular, adversarial, code-grounded Gherkin test cases verifying:
- Brand voice guidelines and durable fact lifecycle (creation, verification, editing, disputing, and permanent archiving).
- Optimistic Concurrency Control (OCC) enforcing `expectedVersion` tracking with 409 conflict detection and recovery.
- Role-Based Access Control (RBAC) preventing non-owner mutation with read-only badge indicators.
- Truth Vault contradiction and hallucination detection telemetry with audit progress bars and severity filters.
- Entity hierarchy DAG cycle detection, quarantined back-edge isolation, and root resolution depth clamping at `MAX_TRAVERSAL_DEPTH = 10`.
- Context generation fencing (`bhContextGen`, `bhLastRequestedPid`) preventing cross-tenant state leakage during workspace and project switching.

---

## 2. Vocabulary & Placeholders

All test cases in this directory adhere to the standardized parameter vocabulary:

| Placeholder | Semantic Type | Description / Example Values |
| :--- | :--- | :--- |
| `[DOMAIN]` | Domain Name | Target brand domain under test (e.g., `zeo.org`, `acme.com`). |
| `[COUNTRY]` | Market Country Code | Primary market ISO alpha-2 code (e.g., `US`, `TR`, `UK`, `DE`). |
| `[LANGUAGE]` | Language Code | Application UI and content language (e.g., `en`, `tr`). |
| `[PROJECT_ID]` | UUID / String | Unique identifier of the active project (e.g., `proj_01j7xyz...`). |
| `[WORKSPACE_ID]` | UUID / String | Tenant workspace identifier (e.g., `ws_01j7abc...`). |
| `[FACT_ID]` | Fact Identifier | Unique durable identifier of a brand fact (e.g., `fact_1711200001`). |
| `[FACT_KEY]` | Machine Slug | Regex-compliant alphanumeric key (`/^[a-zA-Z0-9_-]{1,100}$/`, e.g., `founding_year_1926`). |
| `[EXPECTED_VERSION]` | Integer | Server version counter passed for optimistic concurrency (e.g., `1`, `2`, `4`). |
| `[DISPUTE_REASON]` | Text String | Rationale provided when contesting a hallucinated claim. |
| `[ROOT_ENTITY_ID]` | Entity Identifier | Top-level authoritative parent entity identifier in the hierarchy DAG. |

---

## 3. Ego Browser / MacBook Execution Model

Test execution runs within an isolated **Ego Browser** instance operating on a remote host (MacBook environment):
1. **Remote Execution:** Automated driver scripts are executed on the MacBook via SSH using the `ego-browser nodejs` CLI harness.
2. **Artifact Generation:** Visual snapshots and DOM states are captured directly in the remote browser context and saved to local paths on the MacBook (e.g., `/tmp/ego-artifacts/`).
3. **Evidence Ingestion (SCP):** The executor retrieves captured screenshots from the MacBook via SCP (`scp macbook:/tmp/ego-artifacts/*.png <case-result-dir>/`) before compiling the final execution report.
4. **Result Directories:** Each test case references its designated result directory following the convention:
   `01-brand-hub-ground-truth/01-gherkin-result-case-<short-slug>/`. Result directories are created exclusively upon test execution, never pre-populated with empty folders.

---

## 4. Test Case Inventory

| Case File | Title & Core Verification | Scenarios Covered |
| :--- | :--- | :--- |
| [`01-gherkin-case-brand-voice-and-facts-read.md`](./01-gherkin-case-brand-voice-and-facts-read.md) | Brand Voice & Guidelines Inspection | Tone pills, value propositions, style rule tags, version badges. |
| [`02-gherkin-case-add-verified-fact.md`](./02-gherkin-case-add-verified-fact.md) | Verified Fact Creation & Confirmation Note | Key regex validation, statement entry, mandatory provenance note. |
| [`03-gherkin-case-optimistic-locking-conflict.md`](./03-gherkin-case-optimistic-locking-conflict.md) | Optimistic Concurrency Conflict (409) | Stale `expectedVersion` simulation, drawer alert, retry banner. |
| [`04-gherkin-case-non-owner-rbac-fencing.md`](./04-gherkin-case-non-owner-rbac-fencing.md) | Non-Owner Role Fencing & Read-Only UI | `Read-only (Member)` badge, suppression of Add/Edit/Archive buttons. |
| [`05-gherkin-case-fact-dispute-workflow.md`](./05-gherkin-case-fact-dispute-workflow.md) | Fact Contradiction Dispute Flow | Status change to `disputed`, confirmation note clearing, pending lock. |
| [`06-gherkin-case-fact-permanent-archiving.md`](./06-gherkin-case-fact-permanent-archiving.md) | Fact Archiving Cancel vs Permanent Confirm | Confirmation alertdialog, active view exclusion, terminal read-only. |
| [`07-gherkin-case-truth-vault-hallucinations.md`](./07-gherkin-case-truth-vault-hallucinations.md) | Truth Vault Hallucination Telemetry | KPI scorecard rail, segmented audit progress bar, filter toolbar. |
| [`08-gherkin-case-entity-graph-cycle-quarantine.md`](./08-gherkin-case-entity-graph-cycle-quarantine.md) | Entity DAG Cycle Quarantine | `detectCycles`, `sanitizeHierarchyDAG`, cyclic back-edge isolation. |
| [`09-gherkin-case-entity-graph-depth-clamping.md`](./09-gherkin-case-entity-graph-depth-clamping.md) | Entity Root Traversal Depth Clamping | `resolveRootEntity` depth clamp at `MAX_TRAVERSAL_DEPTH = 10`. |
| [`10-gherkin-case-context-fencing-project-switch.md`](./10-gherkin-case-context-fencing-project-switch.md) | Multi-Tenant Generation Fencing | `bhContextGen` tracking aborting out-of-order responses on switch. |

---

## 5. Traceability & Coverage Matrix

| Original Monolithic Section (`01-brand-hub-ground-truth.md`) | New Modular Case File | Coverage Status | Notes & Invariants Added |
| :--- | :--- | :---: | :--- |
| **Section 1.1 & 2.2**: Dual-Mode Model & Voice Tab | `01-gherkin-case-brand-voice-and-facts-read.md` | Full | Verifies tone pills, style tags, and version badge indicators. |
| **Section 2.3 & 4.1**: Fact Creation & Provenance | `02-gherkin-case-add-verified-fact.md` | Full | Enforces `/^[a-zA-Z0-9_-]{1,100}$/` regex and confirmation note for verified status. |
| **Section 3.2 & 4.2**: Stale `expectedVersion` 409 Conflict | `03-gherkin-case-optimistic-locking-conflict.md` | Full | Simulates stale read; asserts `.bh-conflict-alert` in drawer and main page banner. |
| **Section 1.1 & 4.3**: Non-Owner Member Read-Only Gate | `04-gherkin-case-non-owner-rbac-fencing.md` | Full | Validates `resolveBrandHubOwner() === false` suppresses all write triggers. |
| **Section 2.3 & 3.2**: Dispute Fact Workflow | `05-gherkin-case-fact-dispute-workflow.md` | Full | Validates `pendingDisputeFactId` lock and confirmation note nullification. |
| **Section 2.3 & 4.4**: Fact Archiving Cancel vs Confirm | `06-gherkin-case-fact-permanent-archiving.md` | Full | Asserts alertdialog modal, cancellation state preservation, and terminal archive state. |
| **Section 2.4**: Truth Vault & Hallucination Telemetry | `07-gherkin-case-truth-vault-hallucinations.md` | Full | Tests KPI scorecards, severity/verdict filters, and segmented audit progress bar. |
| **Section 2.5 & 4.5**: Entity Hierarchy DAG Cycle Quarantine | `08-gherkin-case-entity-graph-cycle-quarantine.md` | Full | Proves DFS back-edge detection (`detectCycles`) and quarantine partitioning. |
| **Section 2.5 & 4.5**: Hierarchy Traversal Depth Clamping | `09-gherkin-case-entity-graph-depth-clamping.md` | Full | Proves 15-hop hierarchy traversal clamps at entity 5 (depth 10). |
| **Section 1.1**: Context Generation Fencing | `10-gherkin-case-context-fencing-project-switch.md` | Full | Proves `bhContextGen` and `bhLastRequestedPid` discard stale async returns. |
