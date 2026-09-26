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
- WAKEUP_OWNER: "<ROOT_OR_SUPERVISOR_PANE_ID>"
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
- Discover live coordinates via `herdr pane current --current`.
- Verify runtime binary and model/effort tier against expected values.
- If verified: proceed directly without waiting for explicit ACK.
- If mismatched or ambiguous: report confirmed identity to supervisor and await clarification.
```

### Return Route Invariant:
Verify a live supervisor pane before dispatch. If the caller began outside Herdr, bootstrap that pane first. The assigned agent publishes its handback report at the run root, sends one short notice to the supervisor pane without `--wait`, and yields idle. The supervisor reads the report and reconciles the notice against pane scrollback.

---

## 2. Prompt Format & Plain Language Standards

- **Standalone Plain Language is the Default**:
  Clear, directive, plain-language mission briefs are fully valid, robust, and preferred across all agent harnesses.
- **Slash Commands Restriction**:
  Do NOT recommend `/teamwork-preview` or `/boost` generically. Slash skills are permitted ONLY when:
  1. The skill is verified installed in the local environment (`skills list` or plugin catalog).
  2. The task explicitly authorizes and requires that specific capability.
- **Syntax Rule**: When authorized, slash commands must be placed at the **very start** of the prompt string with **strictly zero space** after the slash (e.g. `/teamwork-preview ...`).

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
- Internal Subagents: Spawning native internal subagents is permitted ONLY if native runtime tools support them and an explicit scope grant is provided.
- Handback: Mode 3 Managed Missions publish immutable report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-handback.yaml`. Mode 1 and Mode 2 report concise native outcome and commit SHA. Yield idle after handback.
```

---

## 4. Independent Reviewer Role Additions

Append to the common block for reviewers:

```markdown
## 4. Review Scope & Clean Context Rules
- CANDIDATE_HEAD: "<EXACT_FULL_COMMIT_SHA>"
- BASE_SHA: "<BASE_COMMIT_SHA>"
- REVIEW_WORKTREE: "<ABSOLUTE_READONLY_WORKTREE_PATH_OR_SHARED_CHECKOUT>"
- Review Invariant: Audit specification conformance, code quality, diff, and check outputs at the exact candidate SHA in clean context.
- Read-Only Boundary: Reviewers are read-only hardening partners. They do not author production feature code or self-approve their own changes. Findings are delivered back to the author or supervisor.
- Handback: Mode 3 Managed Missions publish immutable review report to `<RUN_ROOT>/<TASK_ID>-a<ATTEMPT>-review.yaml`. Mode 2 Task Execution delivers a concise native text review verdict with finding disposition directly.
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
  2. Execute repository generator, validation, and targeted checks.
  3. Verify exact integrated HEAD with authorized check commands.
  4. Perform authorized delivery mechanics (push branch, open PR, or execute authorized merge).
- Handback: Mode 3 Managed Missions publish immutable integration report to `<RUN_ROOT>/integration-a<ATTEMPT>-handback.yaml` (or concise native notice for Mode 2) and yield idle without `--wait`.
```

---

## 6. Safe Submission Pattern

For long briefs containing special characters, quotes, or code fences:
- Author the brief into a temporary markdown file at `<RUN_ROOT>/briefs/<TASK_ID>.md`.
- `herdr agent prompt` takes `<TARGET>` and `<TEXT>` as positional arguments (no stdin or `--file` option exists in the CLI). Avoid shell command substitution (`"$(cat ...)"`), which is vulnerable to quoting hazards, word splitting, and shell escaping errors.
- Use an inline standard library Python command to read UTF-8 content directly and pass it via binary argv (`subprocess.run` without `shell=True` and without creating external helper scripts):
  ```python
  import subprocess
  from pathlib import Path

  target = "w33:p2"  # Explicit target pane or agent handle
  brief_path = Path("/path/to/run-root/briefs/task-1.md")
  prompt_text = brief_path.read_text(encoding="utf-8")

  # Submit via argv list without shell expansion (omit --wait for callback notices)
  subprocess.run(["herdr", "agent", "prompt", target, prompt_text], check=True)
  ```
- **Callback Notice Invariant**: Worker notices back to the supervisor must omit `--wait` to prevent callback deadlocks. Standalone plain-language prefixes remain the standard.
- **Startup Argv Distinction**: Note that `herdr agent start` constraints differ (`herdr agent start <NAME> --kind <KIND> --pane <PANE_ID> [--timeout <MS>] [-- <AGENT_ARGS>...]`); do not extrapolate prompt positional argument behavior to agent startup.
