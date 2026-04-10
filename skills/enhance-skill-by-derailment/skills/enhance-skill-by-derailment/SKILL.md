---
name: enhance-skill-by-derailment
description: >-
  Use skill if you are improving a skill's instructional quality by having a subagent use it on a real task, reading the execution trace to find breaks, and applying fixes.
---

# Enhance Skill by Using

Improve a skill by making a subagent use it on a real task, reading the execution trace to find where the instructions broke, and fixing the skill directly.

## Trigger boundary

**Use when:** testing, hardening, or improving any skill's instructional quality
**Do NOT use when:** building a new skill from scratch (use `build-skills`)

## Non-negotiable rules

1. **Fix the instructions, not the executor.** Every remedy is a text edit to skill files. Never "use a smarter agent."
2. **Subagent does the using. You do the detective work.** The executor follows the skill. You read the trace, find the source defect, and fix that text.
3. **No output files.** No notes, no reports, no errata. The fixed skill files ARE the deliverable.
4. **Real task, real user energy.** The subagent prompt should sound like an everyday user request — not a clinical test case.
5. **Different domain each round.** Same task twice proves nothing.
6. **Do not inject fake constraints.** If the skill does not require a wrapper, shell convention, or extra ritual, do not add one in the test harness.

## Workflow

### 1. Get the skill

**Local skill** (user says "test run-github-scout"):
```
Read ~/.claude/skills/{name}/SKILL.md
Tree ~/.claude/skills/{name}/references/
```

**Remote skill** (user provides `owner/repo` or GitHub URL):
```bash
gh api repos/{owner}/{repo}/contents/SKILL.md --jq '.content' | base64 -d > /tmp/skill-test/SKILL.md
gh api repos/{owner}/{repo}/contents/references --jq '.[].name' | while read f; do
  gh api repos/{owner}/{repo}/contents/references/$f --jq '.content' | base64 -d > /tmp/skill-test/references/$f
done
```

**No name given:** Ask the user which skill to test.

### 2. Read everything and think about the use case

Read SKILL.md and every reference file. While reading, think:

**What would a real user ask this skill to do?** Not "test case #1" — an actual request someone would type. Examples:

| Skill type | Bad test (clinical) | Good test (real user) |
|---|---|---|
| Code search skill | "Search for repos matching 'react'" | "Find me all the self-hosted Notion alternatives with real-time collab" |
| Code review skill | "Review file X" | "I just rewrote our auth middleware, can you check it before I merge?" |
| Deployment skill | "Deploy service A" | "Push this to staging, but our Redis is on a separate VPC so watch for that" |

**How to pick the nastiest realistic task:**
- Use a domain DIFFERENT from the skill's own examples (tests generalization)
- Include 2-3 implicit constraints a naive executor might miss
- Touch ALL branches in the workflow (if the skill has an "if >3 repos" path AND a "<=3 repos" path, pick a count that hits the more complex one)
- Require at least one reference file to be consulted (tests routing)

Read like an editor, not just an operator.
Look for the paragraph, example, missing precondition, or routing cue that would send the executor down the wrong path.

### 3. Launch the subagent

Spin up one capable subagent. The prompt should read like a real user request.

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

**Agent config:** use a capable general-purpose subagent, keep permissions aligned with the real task, and run it in the background if your platform supports that.

### 4. Read the execution trace

When the subagent completes, its output is at the path shown in the launch response (JSONL format).

**Quick extraction:**
```bash
python3 -c "
import json, sys
with open('AGENT_OUTPUT_PATH') as f:
    for line in f:
        if not line.strip(): continue
        obj = json.loads(line)
        if obj.get('type') != 'assistant': continue
        for c in obj.get('message',{}).get('content',[]):
            if c.get('type') == 'text':
                print(c['text'][:500])
                print('---')
            elif c.get('type') == 'tool_use':
                print(f'TOOL: {c[\"name\"]} | {str(c.get(\"input\",{}))[:120]}')
" 2>/dev/null | head -200
```

**What to look for:**

| Signal | What it means | Severity |
|---|---|---|
| `[STUCK]` tag | Subagent hit a wall | P0 |
| `[GUESSED]` tag | Skill didn't say, subagent improvised | P1 |
| `[BROKE]` tag | Command from the skill failed | P0 or P1 |
| `[NICE]` tag | Skill prevented a mistake — don't break this | Keep |
| Re-read same file multiple times | Instructions confusing | P1 |
| Tried command, error, different approach | Silent failure | P1 |
| Skipped a step entirely | Step unclear or seemed optional | P1 |

Cluster repeated symptoms before you edit.
Three tags from one workflow step often collapse into one bad paragraph, one misleading example, or one missing transition.

For each cluster, tag the root cause using `references/root-cause-taxonomy.md` and locate the exact text that caused it.

### 5. Fix the skill directly

For each root-cause cluster, highest severity first:

1. Match to a fix pattern from `references/fix-patterns.md`
2. Rewrite or delete the source text that caused the miss
3. Update the paired example, checklist item, or routing table if the old wording taught the same wrong move
4. Add a new note only when the root cause is genuinely missing context, not when the old sentence can simply be fixed
5. Keep fixes in-place, self-contained, and minimal

**No output files.** Edit the skill. That's the deliverable.

### 6. Verify

```bash
for f in $(find {SKILL_PATH}/references -name '*.md' -type f); do
  grep -q "$(basename $f)" {SKILL_PATH}/SKILL.md || echo "ORPHAN: $f"
done
wc -l {SKILL_PATH}/SKILL.md  # must be under 500
```

### 7. Re-test if P0s were found

If round 1 found any P0, launch another subagent with a **different task in a different domain**. Max 3 rounds. If friction isn't decreasing after 3, the skill needs architectural redesign.

### 8. Tell the user what happened

Brief summary: friction counts, files edited, what worked well, whether re-test passed.

## Reference routing

| File | Read when |
|---|---|
| `references/friction-classification.md` | Step 4 — assigning P0/P1/P2 severity |
| `references/root-cause-taxonomy.md` | Step 4 — understanding WHY something broke |
| `references/fix-patterns.md` | Step 5 — matching root cause to proven fix |

## Guardrails

- Read the full skill before generating the test case.
- Root-cause before fixing. Fixes without root cause analysis recur.
- No output files. Only the skill's own files get edited.
- The trace is disposable. Never preserve it as a summary, errata, or mistake notebook.
- Rewrite the controlling paragraph or example before you add warning bullets about it.
- Do not let test-harness constraints become product docs.
- Don't weaken `[NICE]` moments while fixing — they're load-bearing.
- Don't re-test with the same task.
