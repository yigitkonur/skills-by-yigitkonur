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

K4's duplicate behaviour can be measured in a small native flow by resending one notice; no new fan-in fleet required. K5–K6 are evaluated against read-only examples/fixtures first; no live process killing or real quota consumption. Recovery-behaviour changes are validated only via relevant existing SCENs selected by risk.

## 2. Small Smoke Test

Prerequisite bindings (verify before running):
```bash
CANDIDATE_SKILL_PATH="/Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920/integration/skills/herdr/SKILL.md"
test -f "$CANDIDATE_SKILL_PATH" || { echo "ERROR: Missing candidate skill"; exit 1; }
CANDIDATE_WORKTREE=$(git -C "$(dirname "$CANDIDATE_SKILL_PATH")" rev-parse --show-toplevel)
CANDIDATE_SKILL_SHA256=$(shasum -a 256 "$CANDIDATE_SKILL_PATH" | awk '{print $1}')
CANDIDATE_HEAD=$(git -C "$CANDIDATE_WORKTREE" rev-parse HEAD)
```

A globally mounted skill (`~/.codex/skills/herdr/SKILL.md`, `~/.agents/skills/herdr/SKILL.md`) **must never** be passed off as the tested candidate. Any run where the worker resolves to an unverified global skill is classified as `abort: unverified_global_skill_mounted`.

### Smoke Flow

1. **EM dispatches a small AGY doc-change task** to a worker in a dedicated tab with the candidate path, HEAD, and SHA-256 bound above.
2. **Worker makes the doc change**, commits locally, publishes a handback report via the 4-step publication pipeline, and sends a notice to the manager without `--wait`.
3. **EM applies identity/evidence gate**: Verifies producer identity matches registered assignment before advancing the graph. Reads the report from disk (not from PTY scrape). Dispatches an independent reviewer.
4. **Independent reviewer** audits the candidate in a fresh pane at the exact commit SHA. Publishes a review report and notifies manager.
5. **EM relays the review outcome** and publishes a manager milestone report to the CTO.
6. **Fixture constraint**: No public PR or merge. The smoke task uses an isolated fixture that does not touch `main`.
7. **Idempotent duplicate check**: Resend the worker's original handback notice. Verify the manager records no second dispatch or Git effect (K4).

## 3. Optional Risk Catalogue — Original 14 SCEN Scenarios

These 14 scenarios are preserved as a risk catalogue for targeted selection. Do not execute all 14 as a mandatory campaign; activate individually by risk.

| ID | Name | Status |
|---|---|---|
| SCEN-01 | Agent Launch, Coordinate Discovery & Native Registration | `[SUPPORTED]` / `[PROPOSED]` |
| SCEN-02 | Explicit AGY → Idle Codex Handback | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-03 | Asynchronous Handback to Busy Codex (Enter at Tool Boundary) | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-04 | Multi-Sender Fan-In & Idempotent Intake | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-05 | Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated) | `[PROPOSED]` / `[UNVERIFIED]` |
| SCEN-06 | Deferred Follow-Up via Tab Keystroke (Exclusive Composer) | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-07 | Observer Wait Cancellation vs. Worker Survival | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-08 | Targeted Escape Interruption & Side-Effect Reconciliation | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-09 | Manager Relinquishment, Crash Recovery & State Resume | `[HISTORICAL]` / `[PROPOSED]` |
| SCEN-10 | Parallel Lane Allocation & Dynamic Capacity Refill | `[SUPPORTED]` / `[PROPOSED]` |
| SCEN-11 | Clean-Context Exact-SHA Review Gate & Invalidation | `[PROPOSED]` / `[UNVERIFIED]` |
| SCEN-12 | Safe Sequential Teardown & Evidence Preservation | `[SUPPORTED]` / `[PROPOSED]` |
| SCEN-13 | Cold Role Selection, Reference Routing & Authority Bounding | `[SUPPORTED]` / `[PROPOSED]` |
| SCEN-14 | Leadership Split-Tab Layout, Safe Pane Move & Dynamic Metadata Preservation | `[SUPPORTED]` / `[PROPOSED]` |

## 4. Forward-Test Controller Protocol

1. **Controller Supervisory Identity**: All Git operations, workspace inspections, test suite runs, and artifact verifications are performed by AGY executor agents, not by the Codex supervisory controller directly.
2. **Candidate Artifact Binding**: Bind to `CANDIDATE_SKILL_PATH` and verify matching `CANDIDATE_SKILL_SHA256` and `CANDIDATE_HEAD` before each scenario.
3. **Evidence Capture**: Every executed scenario logs actual command invocations, stdout/stderr, exit codes, candidate path/SHA-256, and generated file hashes into an immutable YAML report under the run root.
4. **Honest Attribution**: Scenarios that cannot be executed record `status: unverified` or `status: unsupported` with precise failure evidence. No simulated or fabricated pass results.
