# Standalone Mission Briefs & Role-First Delegation

Read this reference before delegating or executing work in a Herdr-managed pane. The mission brief is the binding operational contract that enables cold agents to operate autonomously, execute rigorous engineering, and hand back verifiable results without cognitive drift or uncoordinated management.

---

## 1. Architectural Core: Role Authority, Runtime Decoupling & Brief Invariants

### 1.1 The Single Unified Reference Graph
The same `SKILL.md` and reference catalog serve all participants: the Codex CTO, the Codex Engineering Manager (EM), AGY implementers, fresh technical reviewers, integration executors, and recovery executors. Because all participants read the same repository instructions, every mission brief must **route by assigned role first**.

### 1.2 Runtime Is Not Role
Runtime identity (`codex`, `agy`, `claude`) designates an execution engine, not an organizational role. Role authority is explicitly granted by the brief:
- **CTO**: Owns repository strategy, architectural decisions, and candidate approval gates.
- **Engineering Manager (EM)**: Owns multi-agent topology, task graphs, capacity allocation, report intake, and checkpointing.
- **Implementer**: Owns code synthesis, unit tests, and local commits in an isolated worktree.
- **Fresh Reviewer**: Owns independent read-only audits of exact commit SHAs in clean context windows.
- **Integration Executor**: Owns baseline reconciliation, worktree provisioning, serial rebase, packaging validation, and clean teardown.
- **Recovery Executor**: Owns read-first diagnosis, targeted interruption, and state reconciliation for stalled agents.

> [!IMPORTANT]
> **Strict Boundary Invariant**: An assigned implementer, reviewer, or integration executor must **never** infer it is an orchestrator, spawn nested subagent hierarchies, or inherit CTO strategic duties. The brief bounds authority strictly to owned files and assigned verification checks.

### 1.3 The 5 Mandatory Brief Components
Every brief submitted via `herdr agent prompt` must carry five invariant components:
1. **Role Authority & Boundaries**: Explicit role title, narrow file ownership, strict exclusions, and no recursive agent spawning.
2. **Relevant Reference Selection**: Exact pointers to the specific references required for that role (e.g., [report-contract.md](report-contract.md) for reporting schemas, [parallel-capacity.md](parallel-capacity.md) for delivery mechanics). Cold workers load only what their assigned role requires.
3. **Mandatory Coordinates & Return Route**: Explicit origin and target identifiers (`CALLER_PANE_ID`, `CALLER_TAB_ID`, `WORKER_PANE_ID`, `WORKER_TAB_ID`), runtime, model, skill revision, `task_id`, `attempt`, and portable `report_root`. All coordinates use discovered values, never hard-coded host paths or live pane numbers.
4. **Measurable Outcomes & Acceptance Criteria**: Concrete shell verification commands (`npm test`, `cargo test`, `git diff --check`, `python3 scripts/validate-skills.py`), expected exit codes, and test-driven proof.
5. **Atomic Handback & Failure Boundaries**: Strict two-attempt rule before blocker reporting, 10-minute silent boundary checkpointing at the next safe tool boundary, and atomic report publication.

### 1.4 Stable Reporting Invariants
Briefs must **never duplicate YAML report schemas or publication commands**. All reporting requirements route directly to [report-contract.md](report-contract.md). Producers must uphold these cross-cutting invariants:
- **Exact Assigned Attempt & Producer**: Producers publish strictly against their assigned `task_id`, `attempt`, and registered producer identity. Manager alone owns attempt increments; producer revisions or checkpoints within an assigned attempt publish under unique report IDs (e.g. `<task_id>-a<attempt>-<purpose>2.yaml`).
- **All Reports Immutable**: All producers (including Codex managers and AGY workers) publish immutable reports. Only `state.yaml` is a mutable checkpoint maintained by the manager.
- **Portable Discovered Coordinates**: Briefs and notices use portable placeholders discovered from `herdr pane current` and manager assignments, not live session IDs or machine-specific paths.
- **No Undeclared PyYAML**: Verification procedures must not mandate third-party PyYAML dependencies (`import yaml`). Use standard syntax inspection and exit-code validation.
- **Session Metadata**: Record truthful verified terminal and session metadata; record session UUIDs as unavailable when unexposed by the runtime.

---

## 2. Standalone Implementer Mission Brief Template

Use this template when delegating code synthesis, test creation, or bug fixing to an implementer in an isolated Git worktree:

```markdown
# Mission Brief: Implement <Task Title>

## 1. Role Authority & Boundaries
- **Assigned Role**: Implementer (AGY / Codex).
- **Authority**: You own code synthesis and unit testing strictly within your assigned files. Do NOT spawn subagents, do NOT edit manager state or decisions, and do NOT modify files outside your assigned ownership.
- **Owned Paths**:
  - `<path/to/owned/file_1>`
  - `<path/to/owned/file_2>`
- **Exclusions**: Any file not listed above is strictly read-only. Shared composition roots, packaging manifests, and foreign lane files are out of scope.

## 2. Relevant Reference Selection
Read only these references before writing code:
- `skills/herdr/references/report-contract.md`: Canonical immutable report schema, atomic publication pipeline, and notice syntax.
- `skills/herdr/references/parallel-capacity.md`: Worktree isolation, TDD flow, and delivery lifecycle.

## 3. Mandatory Coordinates & Return Route
- CALLER_PANE_ID: "<MANAGER_PANE_ID>"
- CALLER_TAB_ID: "<MANAGER_TAB_ID>"
- WORKER_PANE_ID: "<YOUR_PANE_ID>"
- WORKER_TAB_ID: "<YOUR_TAB_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- TASK_ID: "<TASK_NAME>"
- ATTEMPT: <ASSIGNED_ATTEMPT>
- WORKTREE: "<ABSOLUTE_WORKTREE_PATH>"
- BRANCH: "lane/<TASK_NAME>"

## 4. Implementation & Quality Protocol
- **TDD Mindset**: Write or identify a failing test first (Red). Implement the minimal production code to satisfy the test (Green). Refactor while preserving passing checks.
- **Interactive PTY**: Stay interactive and visible in your terminal pane. Never use headless hacks or hide progress.
- **File Editing**: Use `apply_patch` for file modifications; verify executable availability. Do not write code via shell redirection or cat hacks.
- **Direct Verification**: Execute exact check commands:
  - `<test_command>` (e.g. `cargo test` / `npm test`)
  - `git diff --check`

## 5. Delivery & Atomic Handback Protocol
When all acceptance criteria are verified:
1. Commit your changes locally to your branch with a conventional commit message:
   `git add <owned_files> && git commit -m "feat(<scope>): <description>"`
   *(Note: Lane writers commit locally; do not open individual PRs unless explicitly instructed. Integration executor combines lane commits).*
2. Publish your immutable report outside the worktree to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-handback.yaml` following the canonical atomic publication pipeline in `report-contract.md`.
3. Notify the manager immediately via `herdr agent prompt` WITHOUT `--wait`:
   `herdr agent prompt "$CALLER_PANE_ID" "REPORT NOTICE: mission_id=<MISSION_ID> task_id=<TASK_ID> attempt=<ATTEMPT> report_id=<TASK_ID>-a<ATTEMPT>-handback pane_id=$WORKER_PANE_ID tab_id=$WORKER_TAB_ID report_path=<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-handback.yaml status=completed requested_action=review_candidate"`

## 6. Failure & Checkpoint Boundaries
- **Two-Attempt Rule**: If a check fails twice, change angle or publish a blocker report with evidence. Do not attempt a third blind retry.
- **10-Minute Boundary**: If operating without a state transition for 10 minutes, publish a checkpoint report at your next safe tool boundary.
```

---

## 3. Standalone Clean-Context Technical Reviewer Brief Template

Use this template when dispatching a fresh independent reviewer in a dedicated pane to audit an exact commit candidate:

```markdown
# Mission Brief: Technical Review of Candidate <COMMIT_SHA>

## 1. Role Authority & Boundaries
- **Assigned Role**: Fresh Independent Technical Reviewer (AGY).
- **Authority**: You perform a read-only technical audit in a clean context window. Do NOT edit production files, do NOT advance Git branches, do NOT edit manager state, and do NOT spawn child subagents.
- **Candidate Under Review**: Commit `<CANDIDATE_HEAD_SHA>` over Base `<BASE_SHA>` on branch `<BRANCH>`.

## 2. Relevant Reference Selection
Read only these references:
- `skills/herdr/references/report-contract.md`: Canonical report format, reviewer question schema, and return notices.
- `skills/herdr/references/parallel-capacity.md`: Clean-context review rules and review invalidation protocol.
- Project specifications: `<path/to/spec_or_approved_brief.md>` and coding standards.

## 3. Mandatory Coordinates & Return Route
- CALLER_PANE_ID: "<MANAGER_PANE_ID>"
- CALLER_TAB_ID: "<MANAGER_TAB_ID>"
- REVIEWER_PANE_ID: "<YOUR_PANE_ID>"
- REVIEWER_TAB_ID: "<YOUR_TAB_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- TASK_ID: "review_<TASK_NAME>"
- ATTEMPT: <ASSIGNED_ATTEMPT>

## 4. Exact-SHA Checkout & Review Invariant
1. Review the candidate at its exact commit SHA:
   `git checkout <CANDIDATE_HEAD_SHA>`
2. If tests mutate files or the implementer continues working, execute your review in a separate isolated exact-SHA checkout.
3. **Review Invalidation Rule**: Any subsequent commit or branch rebase invalidates this review. Your verdict binds strictly to `<CANDIDATE_HEAD_SHA>`.

## 5. Review Axes & Verification Standards
Evaluate the candidate along two primary axes:
1. **Specification & Standards**:
   - Inspect full candidate diff: `git diff <BASE_SHA>...<CANDIDATE_HEAD_SHA>`
   - Verify all approved functional requirements and non-functional constraints are satisfied.
   - Check code against documented coding standards, progressive disclosure, and concise agent-writing rules.
2. **Executable Verification**:
   - Run verification checks directly: `<check_command_1>`, `<check_command_2>`.
   - Capture true observed exit codes and outputs. Never mask non-zero exits with `|| true`.
   - Classify findings into:
     - **Load-Bearing Findings**: Critical defects, broken requirements, or failing tests that block approval. Include path, line, observed behavior, requirement violated, and consequence.
     - **Non-Blocking Notes**: Minor cosmetic suggestions that do not block integration.

## 6. Structured Reviewer Q/A Protocol
If you require clarification from the author before rendering a verdict:
- Format inquiry as a structured question notice (see `report-contract.md` Section 7):
  `QUESTION NOTICE: question_id=rev-<TASK_NAME>-q1 target_pane=<AUTHOR_PANE> reply_pane=$REVIEWER_PANE_ID ...`
- Submit question to Manager pane `$CALLER_PANE_ID` so the inquiry and reply remain visible in the manager's action log.

## 7. Verdict Handback Protocol
1. Formulate explicit verdict: `approved` or `changes_requested`.
2. Publish immutable report to `<RUN_ROOT>/review_<TASK_NAME>-a<ATTEMPT>-handback.yaml` following the canonical atomic publication pipeline in `report-contract.md`.
3. Notify manager via `herdr agent prompt "$CALLER_PANE_ID"` without `--wait`:
   `herdr agent prompt "$CALLER_PANE_ID" "REPORT NOTICE: mission_id=<MISSION_ID> task_id=review_<TASK_NAME> attempt=<ATTEMPT> report_id=review_<TASK_NAME>-a<ATTEMPT>-handback pane_id=$REVIEWER_PANE_ID tab_id=$REVIEWER_TAB_ID report_path=<RUN_ROOT>/review_<TASK_NAME>-a<ATTEMPT>-handback.yaml status=completed requested_action=review_candidate"`
```

---

## 4. Standalone Serial Integration Executor Brief Template

Use this template when assigning an AGY executor to manage baseline preparation, serial integration, packaging checks, and safe cleanup:

```markdown
# Mission Brief: Serial Integration & Delivery

## 1. Role Authority & Boundaries
- **Assigned Role**: Integration Executor (AGY).
- **Authority**: You own Git repository operations, worktree provisioning, candidate branch reconciliation, serial rebase, packaging validation, PR mechanics, and resource teardown under EM supervision. Do not alter feature code logic.

## 2. Relevant Reference Selection
Read only these references:
- `skills/herdr/references/parallel-capacity.md`: Dynamic capacity, serial rebase, and safe teardown rules.
- `skills/herdr/references/report-contract.md`: Artifact recording and handback notices.

## 3. Mandatory Coordinates & Return Route
- CALLER_PANE_ID: "<MANAGER_PANE_ID>"
- CALLER_TAB_ID: "<MANAGER_TAB_ID>"
- EXECUTOR_PANE_ID: "<YOUR_PANE_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- TASK_ID: "integration"
- ATTEMPT: <ASSIGNED_ATTEMPT>

## 4. Execution Sequence & GitHub Mechanics
1. **Serial Rebase & Verification**:
   - Fetch latest baseline: `git fetch origin main`
   - Rebase candidate branch serially onto current `origin/main`:
     `git -C <WORKTREE_PATH> rebase origin/main`
   - Run complete test suite and linters on rebased code: `<test_command>`.
2. **Packaging & Marketplace Generation**:
   - Run repository generator: `python3 scripts/gen-marketplace.py`
   - Run validation suite: `python3 scripts/validate-skills.py`
   - Run diff hygiene check: `git diff --check`
   - Ensure zero unlinked references or packaging discrepancies.
3. **PR & Delivery Handling**:
   - **Unmerged PR Delivery** (for missions ending at unmerged draft PR):
     Push verified candidate branch: `git push origin <BRANCH_NAME>`
     Open single integrated draft PR: `gh pr create --draft --title "<TITLE>" --body "<BODY>"`
     Hand back draft PR URL to EM. Do NOT merge or push directly to main.
   - **Authorized Merge Delivery** (for general authorized missions):
     Observe GitHub branch protections and same-account approval restrictions.
     Promote PR to ready (`gh pr ready <PR_NUM>`) and merge serially (`gh pr merge <PR_NUM> --squash --delete-branch`).
4. **Safe Teardown Protocol**:
   - Verify worktree is clean: `git -C <WORKTREE_PATH> status --porcelain` (must be empty).
   - Unmount cleanly: `herdr tab close <TAB_ID>` and `git worktree remove <WORKTREE_PATH>`.
   - Never issue `--force` on a dirty worktree.

## 5. Handback Protocol
Publish integration handback report to `<RUN_ROOT>/integration-a<ATTEMPT>-handback.yaml` following `report-contract.md` and notify manager without `--wait`.
```

---

## 5. Standalone Recovery Executor Brief Template

Use this template when assigning a recovery executor to diagnose and unblock an interrupted or stalled agent:

```markdown
# Mission Brief: Diagnostic Recovery for Pane <STALLED_PANE_ID>

## 1. Role Authority & Boundaries
- **Assigned Role**: Recovery Executor (AGY).
- **Authority**: You perform non-destructive diagnostic inspection, targeted interruption, and environment reconciliation. Do not blindly terminate processes.

## 2. Relevant Reference Selection
- `skills/herdr/references/stopped-agent-recovery.md`: Inspection first, targeted continuation, and crash restart.
- `skills/herdr/references/event-monitoring.md`: Terminal read sources (`visible` vs `recent-unwrapped`).
- `skills/herdr/references/report-contract.md`: Checkpoint recording and pending operations.

## 3. Mandatory Coordinates
- CALLER_PANE_ID: "<MANAGER_PANE_ID>"
- TARGET_PANE_ID: "<STALLED_PANE_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- TASK_ID: "recovery"
- ATTEMPT: <ASSIGNED_ATTEMPT>

## 4. Diagnostic & Recovery Sequence
1. **Inspect First**:
   - Check visible screen for modals: `herdr agent read $TARGET_PANE_ID --source visible --lines 25`
   - Check unwrapped output: `herdr agent read $TARGET_PANE_ID --source recent-unwrapped --lines 50`
   - Check OS processes: `herdr pane process-info --pane $TARGET_PANE_ID`
2. **Targeted Resolution**:
   - If blocked on menu: Send surgical keys via `herdr agent send-keys $TARGET_PANE_ID <keys...>`.
   - If looping or hung: Send targeted `esc` or `ctrl+c`.
   - Check and clear stale Git locks: `ls -la <WORKTREE>/.git/index.lock`
3. **Handback**:
   Publish recovery diagnostic report to `<RUN_ROOT>/recovery-a<ATTEMPT>-handback.yaml` following `report-contract.md` detailing root cause, actions taken, and restored agent status. Prompt manager without `--wait`.
```

---

## 6. Safe Submission Pattern

Always submit mission briefs from a temporary file to prevent shell syntax interpolation or shell truncation:

```bash
# 1. Write structured brief to temporary file
cat << 'EOF' > /tmp/mission-brief-<TASK_NAME>.txt
# Mission Brief: ...
EOF

# 2. Submit atomically via bracketed paste
herdr agent prompt "$TARGET_PANE_ID" "$(cat /tmp/mission-brief-<TASK_NAME>.txt)"
```

> [!CAUTION]
> **No `--wait` on Worker Notices**: When workers notify the manager, they must omit `--wait` (`herdr agent prompt "$CALLER_PANE_ID" "<NOTICE>"`). Using `--wait` blocks the worker's PTY and creates callback deadlocks if the manager responds with a return prompt.
