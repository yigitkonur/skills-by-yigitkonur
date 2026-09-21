# Mission Brief Templates

When dispatching or receiving tasks, use this concise common authority block followed by role-specific additions. Link canonical report fields via [references/report-contract.md](report-contract.md) rather than duplicating schemas.

---

## 1. Common Authority Block (All Roles)

Every mission brief must include:

```markdown
# Mission Brief: <TASK_ID> (Attempt <ATTEMPT>)

## 1. Authority & Identity Coordinates
- MISSION_ID: "<MISSION_ID>"
- TASK_ID: "<TASK_ID>"
- ATTEMPT: <MANAGER_ASSIGNED_ATTEMPT>
- ASSIGNED_ROLE: "<ROLE>"  # Implementer | Fresh Reviewer | Integration Executor
- START_AUTHORITY: "authorized"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- EXECUTION_SKILL_PATH: "<PATH_TO_SKILL>/SKILL.md"
- EXECUTION_SKILL_REVISION: "<EXPECTED_REVISION>"
- EXPECTED_RUNTIME: "<RUNTIME>"  # agy | codex | claude
- EXPECTED_MODEL: "<MODEL_ID>"
- MANAGER_RETURN_ROUTE: "herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE>"" (no --wait)
- CTO_BOUNDARY: "<CTO_PANE_ID_OR_NULL>" (null if Root PTY / non-pane)

## 2. Objective & Delivery Authority
- OBJECTIVE: "<CONCISE_TASK_GOAL>"
- ACCEPTANCE_CRITERIA: "<CHECKABLE_CONDITIONS>"
- REQUIRED_CHECKS: "<COMMANDS_TO_RUN>"
- DELIVERY_PERMISSIONS: "unmerged_pr" | "authorized_merge" | "local_only"

## 3. Preflight & Registration Gate
- Discover live coordinates via `herdr pane current`.
- Verify runtime binary and model/effort tier against expected values.
- Preflight match: Proceed directly without waiting for explicit ACK.
- Mismatch, restart, or unclear authority: Register confirmed identity and await explicit manager acknowledgment before proceeding.
```

---

## 2. Implementer Additions

### Slash Command Selection & Team Structure Rules:
- **Prefix Syntax**: Slash commands must be placed at the **very start** of the prompt string with **strictly zero space** after the slash (`/teamwork-preview` or `/boost`).
- **Standard Implementation Tasks**: Dispatch with `/teamwork-preview /herdr`. The prompt **MUST** explicitly define how the sub-team will be created, even for small teams (e.g. assigning roles like Lead Implementer, TDD Specialist, QA Verifier).
- **Simple Tasks**: For minor 1-line typo fixes or doc links, skip `/teamwork-preview`.
- **Deep / High-Complexity Scenarios**: For extremely hard implementation cases (e.g. distributed locking, major engine refactors), substitute with `/boost /herdr`.

```bash
herdr agent prompt "$WORKER_PANE_ID" "/teamwork-preview /herdr
# Mission Brief: <TASK_ID> (Attempt <ATTEMPT>)
Assemble and guide a specialized sub-team:
- Role 1 (Lead Developer): Implements business logic and interfaces.
- Role 2 (TDD Specialist): Authors red/green test suites.
- Role 3 (QA Verifier): Validates gates and git commit cleanliness.
...
"
```

Append:

```markdown
## 4. Scope, Worktree & Execution Rules
- WORKTREE_PATH: "<ABSOLUTE_WORKTREE_PATH>"
- BASE_SHA: "<BASE_COMMIT_SHA>"
- OWNED_FILES: ["<PATH_1>", "<PATH_2>"]
- EXCLUSIONS: ["state.yaml", "<OTHER_UNOWNED_PATHS>"]
- TDD & Behavioral Checks: Changes to application code require appropriate behavioral tests. Documentation and metadata changes are exempt from mandatory red/green TDD.
- Handback: Publish immutable YAML report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-handback.yaml` via verified 4-step pipeline (see report-contract.md). Notify manager without `--wait`.
```

---

## 3. Fresh Reviewer Additions

For review tasks, append:

```markdown
## 4. Review Scope & Clean Context Rules
- CANDIDATE_HEAD: "<CANDIDATE_COMMIT_SHA>"
- BASE_SHA: "<BASE_COMMIT_SHA>"
- REVIEW_WORKTREE: "<ABSOLUTE_READONLY_WORKTREE_PATH>"
- Review Invariant: Reviewer audits specification conformance, code quality, diff, and check outputs at the exact candidate SHA in clean context.
- Checkout Safety: Verify candidate SHA in the assigned checkout. Unconditional `git checkout` is unsafe in a shared read-only worktree; allocate a separate exact-SHA checkout only if tests mutate state or the author must continue working simultaneously.
- Boundary: Reviewers never author production fixes or inherit EM dispatch authority. If changes are needed, issue a rejection verdict in the review report; the original implementer fixes in its own lane.
- Handback: Publish immutable review report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-review.yaml` and notify manager without `--wait`.
```

---

## 4. Integration Executor Additions

For integration and delivery tasks, append:

```markdown
## 4. Integration Scope & Pipeline
- INTEGRATION_WORKTREE: "<ABSOLUTE_INTEGRATION_PATH>"
- CANDIDATE_BRANCH: "<BRANCH_NAME>"
- VERIFIED_LANES: ["<LANE_1_SHA>", "<LANE_2_SHA>"]
- Pipeline:
  1. Serial rebase onto target baseline.
  2. Execute repository generator and validation suites.
  3. Verify exact integrated HEAD with full test suite.
  4. Perform authorized delivery mechanics (e.g. push draft PR unmerged, or authorized merge).
- Handback: Publish immutable integration report to `<RUN_ROOT>/integration-a<ATTEMPT>-handback.yaml` and notify manager without `--wait`.
```

---

## 5. Safe Submission Pattern

Always author and submit briefs safely using `apply_patch` for authoring and bracketed paste for submission:

```bash
herdr agent prompt "$TARGET_PANE_ID" "$(< /path/to/brief.md)"
```
