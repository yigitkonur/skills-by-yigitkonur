---
name: audit-skill-by-derailment
description: "Use if hardening a SKILL.md by running a fresh subagent on a real task, orchestrating worker agents in Herdr tabs, or analyzing live agent execution scrollbacks across repositories."
---

# Audit Skill by Derailment: The Native Two-Tier Auditor

Harden and upgrade any skill by analyzing real execution friction traces. Diagnose root causes across Structural, Semantic, Operational, and Cognitive dimensions, and directly fix the skill text where it broke.

Supports three operational modes:
- **Mode A (Synthetic Subagent)**: Fast, single-agent simulated execution with standard friction markers.
- **Mode B (Live Herdr Fleet Audit)**: Inspecting terminal scrollbacks and thought traces across existing multi-repo Herdr panes.
- **Mode C (Native Two-Tier Loop)**: Provisioning a dedicated Herdr worker tab, monitoring completion, and dispatching an independent forensic auditor subagent to cross-reference terminal scrollback against physical disk evidence.

---

## When to Use

Use this skill when:
- Testing whether a `SKILL.md` holds up when an autonomous agent executes a non-trivial, multi-step task ("test my skill", "audit skill by derailment").
- Observing live agent execution in Herdr tabs and diagnosing why an agent drifted, guessed, or halted prematurely ("audit herdr pane w2N:pP", "why did the agent stop?").
- Orchestrating an end-to-end audit: spawning a worker agent in Herdr, toggling `Ctrl+O` verbose mode, waiting for completion, and delegating forensic analysis to an auditor subagent.
- Hardening an existing skill before release or integration into production fleets.
- Post-edit verifying that a fix to a skill closed the friction it was meant to resolve.

Do NOT use this skill when:
- Creating a brand new skill from scratch without an initial draft.
- Rewriting a one-off user prompt.
- Doing cosmetic copy-edits where running an agent would not change the execution outcome.

---

## The 5 Non-Negotiable Invariants

1. **Fix the Skill Text, Not the Executor:** Every remedy is an edit to skill documentation or accompanying scripts. If an agent drifts, stalls, or guesses, the defect lies in the skill text. Never blame the model or say "use a smarter agent."
2. **The Anti-Self-Report Law (Bits on Disk > Claims in Prose):** Autonomous LLM agents are prone to sycophancy and confirmation bias, often reporting "Task completed successfully" even when underlying CLI commands crashed or files are empty. Never accept an agent's self-generated report alone; verify raw exit codes and physical disk artifacts (`ls -lh`, `file`). Detailed in [`references/disk-evidence-and-anti-sycophancy.md`](references/disk-evidence-and-anti-sycophancy.md).
3. **The `Ctrl+O` Verbose Mode Invariant:** In Antigravity CLI (AGY), tool arguments, thoughts, and stdout/stderr are collapsed by default. Pressing `Ctrl+O` (or sending `herdr pane send-keys <pane-id> ctrl+o`) unfolds thoughts, exact command lines, and uncensored output into the terminal buffer for inspection via `herdr pane read --source recent-unwrapped`. Detailed in [`references/ctrl-o-verbose-physics.md`](references/ctrl-o-verbose-physics.md).
4. **Scaffold Up to 20–30 Friction Points:** Do not settle for superficial 2-bullet summaries. Exhaustively search across syntax, selector resilience, mental model drift, gating slack, and output paths. Detailed in [`references/forensic-subagent-briefs.md`](references/forensic-subagent-briefs.md).
5. **No Errata Files or Mistake Notebooks:** Never generate separate post-mortem summaries, errata docs, or mistake notebooks. The fixed skill files and executable scripts ARE the deliverable.

---

## Severity & Root-Cause Cheat Sheet

| Marker | Severity | Typical Root Cause | Fix Family | Reference |
|---|---|---|---|---|
| `[STUCK]` — executor cannot continue | P0 | S1 missing prerequisite, S2 contradiction, M2 unstated location | Prerequisite Surfacing, Path Reconciliation, Output Location | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| `[BROKE]` — command or selector threw error | P0 / P1 | O1 silent crash, O5 stale CLI flag, O3 unhandled edge case | Error Recovery Addition, Option Modernization | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| `[GUESSED]` — agent invented unstated decision | P1 | M1 ambiguous threshold, M5 assumed knowledge | Threshold Concretization, Scaling Guidance | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| Premature completion — skipped remote/E2E gates | P1 | C1 premature completion illusion, C4 gate slack | Two-Tier Verification Enclosure, Rigid Phase Gating | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| Skipped destructive cleanup / mutation | P1 | C2 destructive mutation hesitation | Staged Deprecation & Safe Neutralization | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| Ran `--help` instead of real execution probe | P1 | C3 missing tooling awareness, M4 missing method | Actionable Pre-Flight Probe Injection | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| Path drift or file recreation | P1 | S3 scattered info, M3 format inconsistency | Canonical Layout Enforcement | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |
| `[NICE]` — skill prevented an error | Keep | Load-bearing sentence or check | **Never weaken or delete lines tagged [NICE]** | [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) |

---

## Tri-Modal Routing Decision Tree

```
How is the skill being evaluated?
├── Single-session synthetic test?
│   └──► MODE A: Synthetic Subagent Execution (fast in-process trace)
│
├── Inspecting existing multi-repo Herdr tabs?
│   └──► MODE B: Live Herdr Multi-Pane Fleet Audit (read existing scrollbacks)
│
└── End-to-end automated test in fresh Herdr tab?
    └──► MODE C: The Native Two-Tier Herdr Worker ➔ Auditor Subagent Loop
```

---

## Mode C: The Native Two-Tier Herdr Loop (Recommended)

Follow this complete operational workflow to execute an autonomous, evidence-backed audit without external dependencies. Operational details are in [`references/herdr-native-runner.md`](references/herdr-native-runner.md).

### Step 1: Provision a Dedicated Tab & Resolve Pane ID
```bash
# Verify Herdr environment
test "${HERDR_ENV:-}" = 1 || herdr status client

# Discover active workspace and target repository
WS_ID=$(herdr workspace current 2>/dev/null | jq -r '.result.workspace.id // empty' || true)
if [[ -z "$WS_ID" ]]; then
  WS_ID=$(herdr workspace list | jq -r '.result.workspaces[0].id')
fi
TARGET_REPO="${TARGET_REPO:-$(pwd)}"

# Create a tab in the target workspace without stealing user focus
PANE_JSON=$(herdr tab create --workspace "$WS_ID" --label "audit-worker" --cwd "$TARGET_REPO" --no-focus)
PANE_ID=$(echo "$PANE_JSON" | jq -r '.result.pane.id // .result.root_pane.id')
TAB_ID=$(echo "$PANE_JSON" | jq -r '.result.tab.id // empty')
```

### Step 2: Launch Worker Agent Engine
```bash
# Initialize Antigravity CLI (or claude / codex) in the newly created pane
herdr agent start "worker-agent" --kind agy --pane "$PANE_ID"
```

### Step 3: Discover Coordinator Return Route & Dispatch Prompt
> [!IMPORTANT]
> **The Return-Address & Inter-Agent Callback Law (`COORDINATOR_PANE_ID`)**:
> Never dispatch a prompt asking a worker to "report back" or "talk via Herdr" without explicitly providing your own Coordinator Pane ID and teaching the worker how to use Herdr CLI. Without an explicit return route, worker agents report to their own local pane rather than communicating back to the coordinator.

```bash
# Resolve coordinator's own pane ID for inter-agent callback
COORDINATOR_PANE_ID=$(herdr pane current 2>/dev/null | jq -r '.result.pane.id // empty' || true)
if [[ -z "$COORDINATOR_PANE_ID" ]]; then
  COORDINATOR_PANE_ID=$(herdr agent list | jq -r --arg cid "${CONVERSATION_ID:-}" '.result.agents[] | select(.agent_session.value == $cid) | .pane_id // empty' || true)
fi

# Dispatch task with explicit coordinator return address and Herdr command syntax
herdr agent prompt "$PANE_ID" "Execute the campaign workflow for a luxury perfume reel using the local flow-video-director skill. Ensure 9:16 vertical ratio and 720p download.

[Herdr Inter-Agent Callback]: Your coordinator is active at pane '$COORDINATOR_PANE_ID'.
When you complete your run or need to coordinate, communicate your findings back via Herdr:
  herdr agent prompt '$COORDINATOR_PANE_ID' '<Structured findings / status update>'"
```

### Step 4: Toggle `Ctrl+O` Verbose Mode
Immediately expand tool invocations, thoughts, and stdout in the worker pane:
```bash
herdr pane send-keys "$PANE_ID" ctrl+o
```

### Step 5: Await Worker Completion
Monitor the worker agent until it enters `idle`, `done`, or `blocked`:
```bash
# Wait up to 5 minutes for task completion
herdr agent wait "$PANE_ID" --timeout 300000
```

### Step 6: Dispatch Tier 2 Forensic Auditor Subagent
Once the worker finishes, launch an independent auditor subagent (via `invoke_subagent`). Provide the complete Mission-Style prompt from [`references/forensic-subagent-briefs.md`](references/forensic-subagent-briefs.md) containing:
- Target Pane ID (`$PANE_ID`).
- Output directory path for physical disk verification.
- Target skill path to audit and patch.
- Explicit instructions to enforce the Anti-Self-Report Law and uncover up to 20–30 friction points.

### Step 7: Apply Verified Patches & Clean Up
Apply the auditor's line-by-line diffs to the target skill. Close the worker tab/pane after verification:
```bash
if [[ -n "${TAB_ID:-}" ]]; then
  herdr tab close "$TAB_ID" 2>/dev/null || herdr pane close "$PANE_ID"
else
  herdr pane close "$PANE_ID"
fi
```

---

## Mode B: Live Herdr Multi-Pane Fleet Audit

When auditing active or finished agents across existing workspaces, refer to [`references/herdr-pane-audit.md`](references/herdr-pane-audit.md):

1. **Discover Panes:** Run `herdr workspace list` and `herdr agent list`.
2. **Automated Pane Inspection:**
   ```bash
   bash scripts/audit-worker-pane.sh <pane-id> -d <output-dir> --thoughts --tools
   ```
3. **Analyze Mental Models:** Reverse-engineer where the agent hesitated, stalled, or guessed.
4. **Dispatch Corrective Prompts (if agent is active):**
   ```bash
   herdr agent prompt <pane-id> "Please complete compliance by running <missing-command>."
   ```

---

## Mode A: Synthetic Subagent Execution

For fast, lightweight in-process testing:
1. Formulate a prompt with everyday user energy and 2-3 implicit constraints.
2. Launch a subagent instructed to emit `[STUCK]`, `[BROKE]`, `[GUESSED]`, and `[NICE]` markers.
3. Parse the JSONL trace via `bash scripts/parse-derailment-trace.sh <trace-file>`.
4. Apply the corresponding fix patterns from [`references/fix-patterns.md`](references/fix-patterns.md).

---

## Available Scripts

| Script | Purpose |
|---|---|
| [`scripts/audit-worker-pane.sh`](scripts/audit-worker-pane.sh.md) | Automated forensic inspection of a Herdr agent pane (scrollback, exit codes, tools, thoughts, disk artifacts). |
| [`scripts/read-herdr-panes.sh`](scripts/read-herdr-panes.sh.md) | Read, format, and extract thought blocks and tool calls across multiple Herdr panes. |
| [`scripts/launch-derailment.sh`](scripts/launch-derailment.sh.md) | Render Step 3 prompt and launch synthetic subagent trace. |
| [`scripts/parse-derailment-trace.sh`](scripts/parse-derailment-trace.sh.md) | Parse JSONL traces into marker counts, severities, and error snippets. |

---

## Reference Routing

| Reference Document | Read When |
|---|---|
| [`references/herdr-native-runner.md`](references/herdr-native-runner.md) | Mode C: Managing tabs, starting agents, prompting, and waiting via native Herdr CLI. |
| [`references/ctrl-o-verbose-physics.md`](references/ctrl-o-verbose-physics.md) | Understanding AGY TUI folding, toggling `Ctrl+O`, and unwrapping scrollbacks. |
| [`references/forensic-subagent-briefs.md`](references/forensic-subagent-briefs.md) | Formatting Mission-Style subagent prompts with anti-sycophancy and 20–30 friction targets. |
| [`references/disk-evidence-and-anti-sycophancy.md`](references/disk-evidence-and-anti-sycophancy.md) | Performing independent physical artifact validations (magic headers, byte size, exit codes). |
| [`references/friction-taxonomy-guide.md`](references/friction-taxonomy-guide.md) | Unified comprehensive friction taxonomy: markers, severities, all 21 root-cause codes (`S/M/O/C`), compound P0s, and fix patterns. |
| [`references/herdr-pane-audit.md`](references/herdr-pane-audit.md) | Mode B: Fleet discovery, multi-pane reading, and active agent prompt coordination. |
| [`references/fix-patterns.md`](references/fix-patterns.md) | Applying verified fix patterns (Two-Tier Enclosure, Staged Deprecation, Pre-Flight Probes). |
