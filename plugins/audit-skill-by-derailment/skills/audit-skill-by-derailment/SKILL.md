---
name: audit-skill-by-derailment
description: "Use if hardening a SKILL.md by running a fresh subagent on a real task or analyzing live Herdr agent pane execution scrollbacks across repositories."
---

# Enhance Skill by Derailment

Improve a skill by analyzing friction traces—either by launching a **fresh synthetic subagent** on a realistic task (Mode A) or by inspecting **live Herdr agent pane scrollbacks** across multi-repo fleets (Mode B)—diagnosing the root causes, and directly fixing the skill text where it broke.

## When to use

Use this skill if you are:

- *testing whether a SKILL.md actually holds up when an agent uses it* ("test my skill", "is this skill any good", "does this skill work")
- *evaluating live agent execution traces across Herdr panes* ("audit these herdr panes: wJ:p2, wH:p4, wK:p2", "why did the agents stop early?")
- *hardening an existing skill before publishing it or relying on it*
- *diagnosing why agents drift, guess, skip operational gates, or stall on a skill that 'should' work*
- *running a derailment / friction-trace pass on a draft skill*
- *post-edit verifying that a fix to a skill actually closed the friction it was meant to close*

Do NOT use this skill if you are:

- creating a new skill from scratch — use `build-skill`
- rewriting a one-off task prompt for an agent (not a skill)
- doing a tiny copy-edit where running an agent would not change the result

---

## Non-negotiable rules

1. **Fix the skill text, not the executor.** Every remedy is an edit to skill files. Never blame the model or say "use a smarter agent."
2. **Read the trace / scrollback; you diagnose.** The executor attempts to follow the skill. You read the raw trace, find the source defect or gating slack, and fix that text.
3. **No output files.** No separate errata, mistake notebooks, or post-mortem summaries. The fixed skill files ARE the deliverable.
4. **Different domain each test round.** Same task twice proves nothing about generalization.
5. **No fake constraints.** If the skill does not require a wrapper or shell ritual, do not add one in the test harness.
6. **Root-cause before fixing.** Cluster repeated symptoms. Three tags from one workflow step usually collapse into one bad paragraph or missing gate.

---

## Severity & Root-Cause Cheat Sheet

| Symptom in Trace / Scrollback | Severity | Typical Root Cause | Fix Family |
|---|---|---|---|
| `[STUCK]` — executor cannot continue | P0 | S1 missing prerequisite, S2 contradiction, M2 unstated location | Prerequisite Surfacing, Workflow Path Reconciliation, Output Location |
| `[BROKE]` — command from skill failed | P0 / P1 | O1 silent failure, O5 stale flag/version | Error Recovery Addition, Format Alignment |
| `[GUESSED]` — subagent invented a decision | P1 | M1 ambiguous threshold, M5 assumed knowledge | Threshold Concretization, Scaling Guidance |
| Premature completion — skipped remote/E2E gates | P1 | C1 premature completion illusion, C4 gate slack | Two-Tier Verification Enclosure, Rigid Phase Gating |
| Skipped existing CI cleanup or destructive step | P1 | C2 destructive mutation hesitation | Staged Deprecation & Safe Neutralization |
| Ran `--help` instead of real health probe | P1 | C3 missing tooling awareness, M4 missing method | Actionable Pre-Flight Probe Injection |
| Re-read same file 2+ times / path drift | P1 | S3 scattered info, M3 format inconsistency | Canonical Layout Enforcement, Schema Duplication |
| `[NICE]` — skill prevented a mistake | Keep | Load-bearing line | Do not weaken or rewrite this text |

---

## Dual Ingestion Routing

Determine the evaluation mode based on user intent and input handles:

```
Did the user provide Herdr pane IDs (e.g. wJ:p2, wH:p4) or point to active fleet sessions?
├── YES ──► MODE B: Live Herdr Multi-Pane Fleet Audit
│           (Inspect live scrollbacks, reverse-engineer mental models, prompt agents, fix skill)
│
└── NO  ──► MODE A: Synthetic Subagent Execution
            (Launch fresh subagent with [STUCK]/[GUESSED] markers, parse JSONL trace, fix skill)
```

---

## Mode A: Synthetic Subagent Execution

### 1. Get the target skill
Locate the skill directory (`skills/{name}/`, `~/.agents/skills/{name}/`, `~/.gemini/config/skills/{name}/`) and read all files.

### 2. Design the realistic task
Create a realistic prompt with everyday user energy, 2-3 implicit constraints, and a different domain from the skill's own examples.

### 3. Launch the subagent
Launch a fresh-context subagent with the standard friction markers:
- `[STUCK]` if unable to continue; name the missing/conflicting instruction.
- `[GUESSED]` if inventing a decision the skill should have made explicit.
- `[BROKE]` if a documented command failed.
- `[NICE]` if a specific sentence or routing cue saved from a mistake.

### 4. Parse the trace & diagnose
Extract markers with `bash scripts/parse-derailment-trace.sh <trace-path>` and tag root causes using [`references/root-cause-taxonomy.md`](references/root-cause-taxonomy.md).

---

## Mode B: Live Herdr Multi-Pane Fleet Audit

Read [`references/herdr-pane-audit.md`](references/herdr-pane-audit.md) for full Herdr CLI commands and coordination recipes.

### 1. Discover and resolve target panes
```bash
herdr workspace list
herdr agent list
```
Identify the target workspace IDs and pane handles (e.g. `wJ:p2`, `wH:p4`, `wK:p2`, `wV:p2`, `wG:p6`).

### 2. Extract scrollback and cognitive thought traces
Read raw terminal scrollback from target panes using `read-herdr-panes.sh` or direct Herdr commands:

```bash
# Read recent unwrapped scrollback (joins soft wraps for clean parsing)
bash scripts/read-herdr-panes.sh wJ:p2 wH:p4 wK:p2 wV:p2 --lines 400

# Or extract reasoning blocks directly
bash scripts/read-herdr-panes.sh wJ:p2 wH:p4 --thoughts
```

### 3. Reverse-engineer agent mental models
Analyze where and why agents derailed in real sessions:
- **C1 (Premature Completion)**: Did the agent stop after local edits because Step 9 felt like an optional recommendation? ➔ Apply **Two-Tier Verification Enclosure**.
- **C2 (Mutation Hesitation)**: Did the agent leave 30KB GitHub Actions workflows untouched out of fear of breaking required checks? ➔ Apply **Staged Deprecation Protocol**.
- **C3 (Tooling Ignorance)**: Did the agent run `--help` on a tunnel script to avoid blocking the session with a background daemon? ➔ Apply **Actionable Pre-Flight Probe Injection**.
- **C4 / S3 (Structural Drift)**: Did monorepos create scripts in mismatched folders? ➔ Apply **Canonical Layout Enforcement**.

### 4. Live agent fleet coordination (if sessions are active)
If agents are still active and waiting in idle states, dispatch specific corrective prompts to enforce 100% compliance:

```bash
herdr agent prompt <pane-id> "Please complete Golden Workflow compliance by implementing <missing-step> and running <verification-command>."
```

---

## Universal Hardening & Fix Workflow (Modes A & B)

### 1. Fix the skill text directly
Match root causes to fix patterns in [`references/fix-patterns.md`](references/fix-patterns.md):
- Highest severity first (P0 before P1).
- Rewrite or delete the source paragraph that caused the miss.
- Keep fixes in-place, self-contained, and minimal.
- **Never create errata or mistake summary docs.** The fixed skill text is the deliverable.

### 2. Validate skill integrity
```bash
# Verify no orphan reference files
for f in $(find references -name '*.md' -type f); do
  grep -q "$(basename "$f")" SKILL.md || echo "ORPHAN: $f"
done

# Ensure SKILL.md remains concise and router-driven
wc -l SKILL.md
```

### 3. Report findings
Report in chat:
1. Audited panes / traces and classification breakdown.
2. Root causes identified with taxonomy codes (S/M/O/C).
3. Skill files edited with one-line rationales.
4. Corrective actions dispatched to running agents.
5. Verification results.

---

## Available Scripts

| Script | Purpose |
|---|---|
| `scripts/read-herdr-panes.sh` | Read, format, and extract thought blocks and tool invocations from one or more Herdr panes. |
| `scripts/launch-derailment.sh` | Render Step 3 prompt and launch synthetic subagent trace. |
| `scripts/parse-derailment-trace.sh` | Parse JSONL traces into marker counts and snippets. |

---

## Reference Routing

| Reference | Read When |
|---|---|
| [`references/herdr-pane-audit.md`](references/herdr-pane-audit.md) | Mode B: Discovering Herdr panes, reading scrollback, and prompting active agents. |
| [`references/friction-classification.md`](references/friction-classification.md) | Classifying trace symptoms into P0/P1/P2 severities and compound P0s. |
| [`references/root-cause-taxonomy.md`](references/root-cause-taxonomy.md) | Tagging root causes across Structural (S), Semantic (M), Operational (O), and Cognitive (C) codes. |
| [`references/fix-patterns.md`](references/fix-patterns.md) | Applying proven fix patterns (Two-Tier Enclosure, Staged Deprecation, Pre-Flight Probes, Canonical Layouts). |
