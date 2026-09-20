# Herdr Native Acceptance Scenarios & Forward-Test Specifications

## 1. Acceptance Criteria (K1–K7)

| Card | Condition | Pass | Fail |
|---|---|---|---|
| **K1 — Small coupled work** | A skill and its coupled references edited together | One AGY writer selected; task delivers as a unit | Opening five lanes or separate bootstrap/recovery agents solely because files differ |
| **K2 — Genuine independence** | Two tasks with separate outcomes, stable interface, distinct ownership | Ready work dispatched concurrently | "Always one writer" rule applied to genuinely disjoint work; fake two-worker calibration |
| **K3 — New HEAD / delta decision** | Approved H1 → material fix → H2 | H1 approval does NOT transfer to H2; same independent reviewer may issue a new delta decision for H2 | Auto-reset to full review or auto-approval on commit advance |
| **K4 — Low-noise communication** | One progress message, one handback report, same notice sent twice | Progress uses native message; handback consumed once; duplicate creates no second dispatch, Git effect, or ACK chain | Requiring an immutable YAML report for a plain progress update |
| **K5 — Honest evidence** | Validator exits 1; report claims "0"; or report digest has changed | Approval not granted; correction requested based on actual output | Covering two failures with more "passed" reports |
| **K6 — Selective checkpoint resume** | Checkpoint + old report + one new valid report | Current ownership and pending effects preserved; only relevant history opened | Re-dispatching all work or requiring all past reports re-read |
| **K7 — Bounded native full loop** | Verified candidate skill, two-pane leadership, small AGY doc task | Task/feedback/manager-decision/independent-review/CTO-handback observed from TUI | CTO taking over engineering, infinite wait after missed notice, using globally mounted skill as candidate |

*Evaluation Notes*:
- K4 duplicate behaviour is evaluated in a small native flow by resending one notice; no new fan-in fleet required.
- K5–K6 evidence is evaluated against read-only examples and fixtures first; **no live process termination, crash simulation, or real quota consumption**. Static K5/K6 checks are not live crash/quota tests.
- Recovery behaviour changes are validated only via relevant existing SCENs selected by risk.
- Scenario and test specifications in this document define procedures and acceptance bars; **they are not claimed execution evidence**.

## 2. Small Smoke Test

Prerequisite bindings (verify before running):
```bash
CANDIDATE_SKILL_PATH="/path/to/worktree/skills/herdr/SKILL.md"
test -f "$CANDIDATE_SKILL_PATH" || { echo "ERROR: Missing candidate skill"; exit 1; }
CANDIDATE_WORKTREE=$(git -C "$(dirname "$CANDIDATE_SKILL_PATH")" rev-parse --show-toplevel)
CANDIDATE_SKILL_SHA256=$(shasum -a 256 "$CANDIDATE_SKILL_PATH" | awk '{print $1}')
CANDIDATE_HEAD=$(git -C "$CANDIDATE_WORKTREE" rev-parse HEAD)
```

A globally mounted skill (`~/.codex/skills/herdr/SKILL.md`, `~/.agents/skills/herdr/SKILL.md`) **must never** be passed off as the tested candidate. Any run where the worker resolves to an unverified global skill is classified as `abort: unverified_global_skill_mounted`.

### Smoke Flow

1. **EM dispatches small AGY doc task** to a dedicated tab with the candidate path, HEAD, and SHA-256 bound above.
2. **Worker makes doc change**, commits locally, publishes handback report via verified 4-step pipeline, and sends notice to manager without `--wait`.
3. **EM applies identity/evidence gate**: Verifies producer identity matches registered assignment before advancing graph. Reads report from disk. Dispatches an independent reviewer in a dedicated pane.
4. **Independent reviewer** audits candidate in fresh pane at exact commit SHA in clean context. Publishes review report and notifies manager without `--wait`.
5. **EM relays review outcome** and publishes manager milestone report to CTO.
6. **Prompt Terminal Retirement & Bounded Resource Release**:
   - Upon verified handback and reconciled effects, EM promptly retires the completed owned worker pane (`herdr pane close "$WORKER_PANE_ID"`).
   - Verify the completed owned worker pane disappears from live inventory, while leadership panes (CTO, EM) and any active sibling panes persist.
   - Worktree cleanup gate: clean worker checkout is removed (`git worktree remove`); an intentional dirty checkout fixture is retained with a recorded reason (no default force removal).
7. **Idempotent duplicate check (K4)**: Resend worker's original handback notice once. Verify manager records no second dispatch, no Git effect, and no terminal respawn.
8. **Fixture constraint**: No public PR or merge. The smoke flow runs on an isolated test fixture and does not push to `main`.

## 3. Optional Risk Catalogue — Original 14 SCEN Scenarios

These 14 scenarios are preserved as a risk catalogue for targeted selection. Do not execute all 14 as a mandatory campaign; activate individually by risk.

| ID | Name | Status | Key Risk Verification |
|---|---|---|---|
| SCEN-01 | Agent Launch, Coordinate Discovery & Native Registration | `[SUPPORTED]` / `[PROPOSED]` | Bind candidate path/digest/HEAD; JSON coordinate extraction; registration without wait |
| SCEN-02 | Explicit AGY → Idle Codex Handback | `[HISTORICAL]` / `[PROPOSED]` | Atomic report publication; turn activation via bracketed paste |
| SCEN-03 | Asynchronous Handback to Busy Codex (Enter at Tool Boundary) | `[HISTORICAL]` / `[PROPOSED]` | Input queued at turn boundary; qualified non-interrupting delivery |
| SCEN-04 | Multi-Sender Fan-In & Idempotent Intake | `[HISTORICAL]` / `[PROPOSED]` | Sequential ingestion; duplicate report ID / identical digest consumed as no-op |
| SCEN-05 | Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated) | `[PROPOSED]` / `[UNVERIFIED]` | Unnotified report discovered; partial, stale attempt, mutated digest quarantined |
| SCEN-06 | Deferred Follow-Up via Tab Keystroke (Exclusive Composer) | `[HISTORICAL]` / `[PROPOSED]` | Tab deferred input on dedicated empty composer; Enter remains default |
| SCEN-07 | Observer Wait Cancellation vs. Worker Survival | `[HISTORICAL]` / `[PROPOSED]` | Host wait exits cleanly; worker process continues undisturbed |
| SCEN-08 | Targeted Escape Interruption & Side-Effect Reconciliation | `[HISTORICAL]` / `[PROPOSED]` | Surgical Esc/Ctrl+C; process inventory and Git locks reconciled |
| SCEN-09 | Manager Relinquishment, Crash Recovery & State Resume | `[HISTORICAL]` / `[PROPOSED]` | Old manager relinquished; structural shape validation; selective report intake |
| SCEN-10 | Parallel Lane Allocation & Dynamic Capacity Refill | `[SUPPORTED]` / `[PROPOSED]` | Disjoint worktrees; zero Git lock collisions; capacity refill on handback |
| SCEN-11 | Clean-Context Exact-SHA Review Gate & Invalidation | `[PROPOSED]` / `[UNVERIFIED]` | Fresh audit at exact commit SHA; commit advance invalidates prior review |
| SCEN-12 | Safe Sequential Teardown, Resource Release & Evidence Preservation | `[SUPPORTED]` / `[PROPOSED]` | Prompt pane retirement; leadership/active siblings & dirty checkouts persist; no respawn on late notice |
| SCEN-13 | Cold Role Selection, Reference Routing & Authority Bounding | `[SUPPORTED]` / `[PROPOSED]` | Role matrix triage before reading; secondary manager bootstrapping refused |
| SCEN-14 | Leadership Split-Tab Layout, Safe Pane Move & Dynamic Metadata Preservation | `[SUPPORTED]` / `[PROPOSED]` | 2-pane leadership tab (CTO left, EM right); safe move preserves session; live metadata vs stale env |

## 4. Forward-Test Controller Protocol

1. **Controller Supervisory Identity**: All Git operations, workspace inspections, test suite runs, and artifact verifications are performed by AGY executor agents, not by the Codex supervisory controller directly.
2. **Candidate Artifact Binding**: Bind to `CANDIDATE_SKILL_PATH` and verify matching `CANDIDATE_SKILL_SHA256` and `CANDIDATE_HEAD` before each scenario.
3. **Evidence Capture**: Every executed scenario logs actual command invocations, stdout/stderr, exit codes, candidate path/SHA-256, and generated file hashes into an immutable YAML report under the run root.
4. **Honest Attribution**: Scenarios that cannot be executed record `status: unverified` or `status: unsupported` with precise failure evidence. No simulated or fabricated pass results.
