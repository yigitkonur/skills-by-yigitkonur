---
name: audit-skill-by-derailment
description: Use skill if you are testing or hardening an existing SKILL.md by running a fresh subagent on a real task and editing the skill where the trace shows friction.
---

# Enhance Skill by Derailment

Improve a skill by making a subagent use it on a real task, reading the execution trace for friction, and fixing the skill text where it broke.

## When to use

Use this skill if you are:

- *testing whether a SKILL.md actually holds up when an agent uses it* ("test my skill", "is this skill any good", "does this skill work")
- *hardening an existing skill before publishing it or relying on it*
- *diagnosing why an agent keeps drifting, guessing, or stalling on a skill that "should" work*
- *running a derailment / friction-trace pass on a draft skill*
- *post-edit verifying that a fix to a skill actually closed the friction it was meant to close*
- *deciding which lines, examples, or routing cues in a skill are load-bearing vs dead weight*

Do NOT use this skill if you are:

- creating a new skill from scratch — use `build-skill`
- rewriting a one-off task prompt for an agent (not a skill) — that is out of scope for this pack
- doing a tiny copy-edit where running a subagent would not change the result
- judging output quality of a skill, rather than the skill text itself

## Non-negotiable rules

1. **Fix the skill text, not the executor.** Every remedy is an edit to skill files. Never "use a smarter agent."
2. **Subagent uses; you diagnose.** The executor follows the skill. You read the trace, find the source defect, and fix that text.
3. **No output files.** No reports, errata, mistake notebooks. The fixed skill files ARE the deliverable.
4. **Real task, real user energy.** The subagent prompt sounds like an everyday user request, not a clinical test case.
5. **Different domain each round.** Same task twice proves nothing about generalization.
6. **No fake constraints.** If the skill does not require a wrapper, shell convention, or extra ritual, do not add one in the test harness.
7. **Root-cause before fixing.** Cluster repeated symptoms. Three tags from one workflow step usually collapse into one bad paragraph.

## Severity and root-cause cheat sheet

Use these inline tables for fast triage. Load the reference files for full criteria.

| Symptom in trace | Severity | Typical root cause | Fix family |
|---|---|---|---|
| `[STUCK]` — executor cannot continue | P0 | S1 missing prerequisite, S2 contradiction, M2 unstated location | Prerequisite Surfacing, Workflow Path Reconciliation, Output Location Specification |
| `[BROKE]` — command from skill failed | P0 / P1 | O1 silent failure, O5 stale flag/version | Error Recovery Addition, Format Alignment |
| `[GUESSED]` — subagent invented a decision | P1 | M1 ambiguous threshold, M5 assumed knowledge | Threshold Concretization, Scaling Guidance |
| Re-read same file 2+ times | P1 | S3 scattered info, M3 format inconsistency | Schema Duplication at Point of Use |
| Skipped a step | P1 | M4 missing execution method, M6 vague verb | Execution Method Specification |
| `[NICE]` — skill prevented a mistake | Keep | Load-bearing line | Do not weaken or rewrite this text |

3+ P1s in one workflow step = compound P0. Fix the source paragraph first; do not pile warnings beside bad text.

## Workflow

### 1. Get the skill

**Local skill** (user says "test run-github-scout"):
```bash
ls ~/.claude/skills/{name}/
cat ~/.claude/skills/{name}/SKILL.md
ls ~/.claude/skills/{name}/references/
```

**Remote skill** (user provides `owner/repo` or GitHub URL):
```bash
mkdir -p /tmp/skill-test/references
gh api repos/{owner}/{repo}/contents/SKILL.md --jq '.content' | base64 -d > /tmp/skill-test/SKILL.md
gh api repos/{owner}/{repo}/contents/references --jq '.[].name' | while read f; do
  gh api repos/{owner}/{repo}/contents/references/$f --jq '.content' | base64 -d > /tmp/skill-test/references/$f
done
```

**No name given:** Ask the user which skill to test before touching anything.

### 2. Read everything; design the realistic task

Read SKILL.md and every reference file. While reading, hold these in mind:

- **What would a real user actually ask this skill to do?** Not "test case #1" — a sentence someone would type at 4pm on a Tuesday.
- **Where will the executor trip?** Note ambiguous thresholds, missing prerequisites, scattered routing.
- **Which reference files are routed cleanly vs orphaned?**

| Skill type | Bad test (clinical) | Good test (real user energy) |
|---|---|---|
| Code search | "Search for repos matching 'react'" | "Find me all the self-hosted Notion alternatives with real-time collab" |
| Code review | "Review file X" | "I just rewrote our auth middleware, can you check it before I merge?" |
| Deployment | "Deploy service A" | "Push this to staging, but our Redis is on a separate VPC so watch for that" |

**Pick the nastiest realistic task:**

- Use a domain DIFFERENT from the skill's own examples (tests generalization, not memorization).
- Include 2-3 implicit constraints a naive executor might miss.
- Touch ALL workflow branches the skill defines (if there's an "if >3 repos" path AND a "<=3" path, hit the more complex one).
- Require at least one reference file to be consulted (tests routing).

Read like an editor, not just an operator. Find the paragraph, example, missing precondition, or routing cue that would send the executor down the wrong path.

### 3. Launch the subagent

Launch one fresh-context subagent. The prompt reads like a real user request, not an experiment.

**Prompt template:**

```
I need help with: {TASK_IN_PLAIN_LANGUAGE}

There's a skill for this at {SKILL_PATH}. Read the SKILL.md and the
reference files it points to, then follow the workflow to do what I asked.

As you work, only flag moments where the skill text changes your path:
- [STUCK] if the skill leaves you unable to continue; name the missing or conflicting instruction
- [GUESSED] if you had to invent a decision the skill should have made explicit; point to the section that should have answered it
- [BROKE] if following the skill led you to a command or pattern that failed; include the command and the instruction that led you there
- [NICE] if a specific sentence, example, or routing cue saved you from a mistake
```

**Valid marker shapes the subagent should produce:**

| Marker | Example shape |
|---|---|
| `[STUCK]` | `[STUCK] references/fix-patterns.md says to run X, but no install step or fallback exists.` |
| `[GUESSED]` | `[GUESSED] Step 2 says "large skill" but gives no threshold; I chose 10 files.` |
| `[BROKE]` | `[BROKE] Command from Step 4 failed: ...; the documented output path did not exist.` |
| `[NICE]` | `[NICE] The routing table sent me to friction-classification.md before editing.` |

**Dispatch protocol:**

- Use a fresh-context Sonnet-class or equivalent capable general-purpose subagent by default.
- Use a stronger model only when the target task itself is high-risk or repeated P0s remain after a normal pass.
- Do not "fix" a weak skill by escalating the model; fix the skill text.
- Keep subagent permissions aligned with the real task.
- Do not leak the expected answer, suspected bug, or intended fix into the prompt.
- Preserve the trace path before editing — it is the only evidence you have.

**Optional helper:** `scripts/launch-derailment.sh` renders this prompt, optionally pipes it to a runtime-neutral agent command, and tees output to a trace file. See `scripts/launch-derailment.sh.md` for arguments and exit codes.

### 4. Read the execution trace

When the subagent completes, its output is at the path shown in the launch response (typically JSONL).

**Preferred extraction:**

```bash
bash {SKILL_PATH}/scripts/parse-derailment-trace.sh AGENT_OUTPUT_PATH
```

See `scripts/parse-derailment-trace.sh.md` for output format and `--context N` flag.

**Fallback extraction (if the script is unavailable):**

```bash
python3 -c "
import json
with open('AGENT_OUTPUT_PATH') as f:
    for line in f:
        if not line.strip(): continue
        obj = json.loads(line)
        if obj.get('type') != 'assistant': continue
        for c in obj.get('message',{}).get('content',[]):
            if c.get('type') == 'text':
                print(c['text'][:500]); print('---')
            elif c.get('type') == 'tool_use':
                print(f'TOOL: {c[\"name\"]} | {str(c.get(\"input\",{}))[:120]}')
" 2>/dev/null | head -200
```

**What the trace shows:**

| Signal | What it means | Where to look |
|---|---|---|
| `[STUCK]` tag | Subagent hit a wall — P0 | Source paragraph the tag points to |
| `[GUESSED]` tag | Skill didn't say; subagent improvised — P1 | The decision the skill should have made |
| `[BROKE]` tag | Command from skill failed — P0/P1 | The exact command + the instruction that led there |
| `[NICE]` tag | Skill prevented a mistake | Mark as load-bearing — do not break |
| Re-read same file 2+ times | Confusing instructions — P1 | The file the executor kept reopening |
| Tried, errored, switched approach | Silent failure — P1 | The first command and what it returned |
| Skipped a step | Step seemed optional or unclear — P1 | Step heading, conditional gating |

For each cluster, use `references/friction-classification.md` to assign severity, then `references/root-cause-taxonomy.md` to tag the WHY (S/M/O code).

### 5. Fix the skill directly

For each root-cause cluster, highest severity first:

1. Match to a fix pattern from `references/fix-patterns.md`.
2. Rewrite or delete the source text that caused the miss.
3. Update the paired example, checklist item, or routing table if the old wording taught the same wrong move.
4. Add a new note only when the root cause is *genuinely missing context*, not when the old sentence can simply be fixed.
5. Keep fixes in-place, self-contained, and minimal.

**No output files.** Edit the skill. That is the deliverable.

**Do not** preserve bad text and add a warning beside it. **Do not** weaken `[NICE]` lines while fixing — they're load-bearing. **Do not** let test-harness constraints become product docs (see Harness Alignment in `references/fix-patterns.md`).

### 6. Verify

```bash
# Every reference file must be linked from SKILL.md
for f in $(find {SKILL_PATH}/references -name '*.md' -type f); do
  grep -q "$(basename $f)" {SKILL_PATH}/SKILL.md || echo "ORPHAN: $f"
done

# SKILL.md must stay under 500 lines
wc -l {SKILL_PATH}/SKILL.md
```

Run the repo's validator if the skill lives in this repo:

```bash
python3 scripts/validate-skills.py
```

### 7. Re-test if any P0 was found

If round 1 found any P0, launch another subagent with a **different task in a different domain**.

Decision rule:

- Round 2 is required after any P0.
- Round 3 is allowed only if friction decreased after round 2.
- Max 3 rounds. If friction does not decrease after 3 rounds, stop and route to `build-skill` for redesign — do not keep piling warnings into a structurally weak skill.

### 8. Tell the user what happened

The report is chat output, not a repo artifact. Report in this order:

1. Marker counts by severity: `[STUCK]`, `[GUESSED]`, `[BROKE]`, `[NICE]`.
2. Root-cause clusters and taxonomy codes used (S/M/O).
3. Skill files edited, with one-line rationale per change.
4. Validation run and result.
5. Re-test result if any P0 was found.
6. Any companion-skill issue intentionally left for a separate pass.

## Available scripts

Scripts are resolved relative to the skill directory root.

| Script | Use |
|---|---|
| `scripts/launch-derailment.sh` | Render the Step 3 prompt, optionally pipe it to a runtime-neutral agent command, and tee output to a trace. See `scripts/launch-derailment.sh.md`. |
| `scripts/parse-derailment-trace.sh` | Parse a saved JSONL or plain-text trace into marker counts, marker context, and tool/failure snippets. See `scripts/parse-derailment-trace.sh.md`. |

## Reference routing

Load only what the current step needs.

| File | Read when |
|---|---|
| `references/friction-classification.md` | Step 4 — assigning P0/P1/P2 severity to trace symptoms |
| `references/root-cause-taxonomy.md` | Step 4 — tagging WHY each cluster broke (S/M/O codes) |
| `references/fix-patterns.md` | Step 5 — matching root cause to a proven fix pattern |

## Guardrails

- Read the full skill before generating the test case.
- Root-cause before fixing. Fixes without root-cause analysis recur.
- No output files. Only the skill's own files get edited.
- The trace is disposable. Never preserve it as a summary, errata, or mistake notebook.
- Rewrite the controlling paragraph or example before adding warning bullets about it.
- Do not let test-harness constraints become product docs.
- Do not weaken `[NICE]` moments while fixing.
- Do not re-test with the same task — different domain each round.
