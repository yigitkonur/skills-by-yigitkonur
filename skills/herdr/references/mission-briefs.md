# Mission Brief Templates & Dispatch Protocol

When dispatching tasks or receiving assignments in Herdr, use this concise common authority block followed by role-specific additions. Link canonical report fields via [report-contract.md](report-contract.md) rather than duplicating schemas.

---

## 1. Common Authority Block (All Roles)

Every structured mission brief must establish clear boundaries and coordinates:

```markdown
# Mission Brief: <TASK_ID> (Attempt <ATTEMPT>)

## 1. Authority & Identity Coordinates
- MISSION_ID: "<MISSION_ID>"
- TASK_ID: "<TASK_ID>"
- ATTEMPT: <ASSIGNED_ATTEMPT>
- ASSIGNED_ROLE: "<ROLE>"  # Implementer | Independent Reviewer | Integrator
- START_AUTHORITY: "authorized"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- EXECUTION_SKILL_PATH: "<PATH_TO_SKILL>/SKILL.md"
- EXPECTED_RUNTIME: "<RUNTIME>"  # agy | codex | claude
- EXPECTED_MODEL: "<MODEL_ID>"
- RETURN_ROUTE: "herdr agent prompt '<SUPERVISOR_PANE_ID>' '<NOTICE>'" (no --wait)

## 2. Objective & Delivery Authority
- OBJECTIVE: "<CONCISE_TASK_GOAL>"
- ACCEPTANCE_CRITERIA: "<CHECKABLE_CONDITIONS>"
- REQUIRED_CHECKS: "<COMMANDS_TO_RUN>"
- DELIVERY_PERMISSIONS: "local_only" | "draft_pr" | "authorized_merge"

## 3. Preflight & Registration Gate
- Discover live coordinates via `herdr pane current`.
- Verify runtime binary and model/effort tier against expected values.
- If verified: proceed directly without waiting for explicit ACK.
- If mismatched or ambiguous: report confirmed identity to supervisor and await clarification.
```

---

## 2. Prompt Prefix & Natural Language Rules

- **No Mandatory Slash Slop**:
  Do NOT blindly force `/teamwork-preview` or `/boost` on every prompt. Standalone plain-language mission briefs are fully valid, robust, and preferred across all harnesses.
- **When Slash Commands Are Appropriate**:
  - `/teamwork-preview /herdr`: Use when launching an agent that will explicitly coordinate a multi-agent subteam in its own pane.
  - `/boost /herdr`: Use for high-risk, security-critical, or complex tasks requiring deep reasoning and adversarial verification.
  - **Syntax Rule**: Slash commands must be placed at the **very start** of the prompt string with **strictly zero space** after the slash.

---

## 3. Implementer Role Additions

Append to the common block for implementers:

```markdown
## 4. Scope, Worktree & Execution Rules
- WORKTREE_PATH: "<ABSOLUTE_WORKTREE_PATH>"
- BASE_SHA: "<BASE_COMMIT_SHA>"
- OWNED_FILES: ["<PATH_1>", "<PATH_2>"]
- EXCLUSIONS: ["<UNOWNED_PATH_1>", "..."]
- Behavioral Checks: Changes to production code require appropriate behavioral test coverage (red-to-green TDD). Documentation and generated metadata changes are exempt from mandatory red/green tests.
- Handback: Publish immutable report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-handback.yaml` (or report concise outcome for Mode 1/2). Notify supervisor without `--wait`.
```

---

## 4. Independent Reviewer Role Additions

Append to the common block for reviewers:

```markdown
## 4. Review Scope & Clean Context Rules
- CANDIDATE_HEAD: "<EXACT_FULL_40_CHAR_COMMIT_SHA>"
- BASE_SHA: "<BASE_COMMIT_SHA>"
- REVIEW_WORKTREE: "<ABSOLUTE_READONLY_WORKTREE_PATH>"
- Review Invariant: Audit specification conformance, code quality, diff, and check outputs at the exact candidate SHA in clean context.
- Read-Only Boundary: Reviewers are read-only hardening partners. They do not author production feature code or self-approve their own changes. Findings are delivered in a formal review report back to the supervisor or author.
- Handback: Publish immutable review report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-review.yaml` and notify supervisor without `--wait`.
```

---

## 5. Integrator Role Additions

Append to the common block for integration tasks:

```markdown
## 4. Integration Scope & Pipeline
- INTEGRATION_WORKTREE: "<ABSOLUTE_INTEGRATION_PATH>"
- TARGET_BRANCH: "<MISSION_AUTHORIZED_TARGET_BRANCH>"
- VERIFIED_CANDIDATES: ["<SHA_1>", "<SHA_2>"]
- Pipeline:
  1. Serial rebase onto target branch baseline.
  2. Execute repository generator, validation, and test suites.
  3. Verify exact integrated HEAD with full check suite.
  4. Perform authorized delivery mechanics (push branch, open PR, or execute authorized merge).
- Handback: Publish immutable integration report to `<RUN_ROOT>/integration-a<ATTEMPT>-handback.yaml` and notify supervisor without `--wait`.
```

---

## 6. Safe Submission Pattern

Always submit large briefs safely via heredocs or files to prevent shell argument escaping issues:

```bash
herdr agent prompt "$TARGET_PANE" "$(< /path/to/brief.md)"
```
