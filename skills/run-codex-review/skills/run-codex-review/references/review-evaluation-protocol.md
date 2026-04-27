# Review Evaluation Protocol

Single rule: **never apply review feedback as-is.** Every review item — from Codex inner-loop, Codex rescue, Copilot, Greptile, Devin, or any human — passes through a `/do-review` evaluator before any code change happens.

This file specifies why, where the rule applies, the decision taxonomy, the JSON schema for evaluator output, and the failure modes.

## Why

Reviewers (any reviewer) are valuable but imperfect:

- **False positives.** The reviewer flags code that's correct in this codebase's context.
- **Stale citations.** The review references a SHA, line, or function that's already been changed.
- **Wrong context.** The reviewer didn't read enough surrounding code; their suggested fix would break something else.
- **Scope creep.** The reviewer suggests refactors that expand the PR.
- **Subjective preference dressed as defect.** The reviewer states an idiom preference as if it were a bug.
- **Cross-reviewer contradictions.** Source A says "extract", source B says "inline".
- **Codex artifacts.** Codex sometimes loops on the same item it just told you to fix.

Direct-apply means every false positive goes into the diff. The 20-round inner-loop cap doesn't save you because Codex doesn't re-classify items it already mentioned.

The `/do-review` evaluator is the gate. It reads the actual code, evaluates each item against the codebase, and decides:

- **accepted** — real issue, valid fix, apply
- **rejected** — false positive or wrong context, skip with reason
- **ambiguous** — needs human decision, surface

## Where the rule applies

| Phase | Context | Evaluator |
|---|---|---|
| 3 | Per-round inner loop, after `classify-review-feedback.py` | Worker sub-agent uses `/do-review` on classifier's `major[]` |
| 7 | Post-PR window closes | Evaluator sub-agent uses `/do-review` on all gathered review streams |
| 8 | Apply step | Main agent uses `/do-review` directly in own context to apply Phase 7's accepted items |

Phase 8 is the only place where `/do-review` is used **without** a sub-agent — the answers come straight back from the Phase 7 evaluator's handback, so the main agent acts directly. This is the user's stated principle: "do-review is healthier when answers come straight back".

## Decision taxonomy

For every item:

### accepted

The item is a real issue. The fix (Codex's or evaluator's) is valid for this codebase. Apply it.

Mark accepted when:
- The cited code exhibits the behavior the reviewer describes.
- The suggested fix produces correct code that doesn't break anything else.
- Or the evaluator can produce a corrected fix that does (Codex's fix may be wrong even when the issue is real).

### rejected

The item is not a real issue OR the suggested fix would break something. Skip with a recorded reason.

Mark rejected when:
- The cited code doesn't exhibit the claimed behavior (the reviewer misread).
- The cited line/file no longer exists at that SHA (stale citation).
- The fix would break a documented contract or another caller.
- The item is purely subjective / scope creep / "while you're at it".
- The same item was raised in a prior round and the evaluator already decided it's not real (oscillation).

### ambiguous

The item might be real but the evaluator can't decide without human input. Surface — do not apply, do not silently reject.

Mark ambiguous when:
- Two reviewers contradict each other on the same line ("extract" vs "inline").
- The fix requires an architectural decision outside the branch's scope.
- The item touches an area the evaluator can't safely judge (legal/compliance, security boundaries, performance budgets).
- The same major item recurs after the evaluator told the worker to apply Codex's fix in a prior round (oscillation — the fix is wrong somehow).
- The reviewer's claim depends on context the evaluator can't verify (production telemetry, runtime data).

## Decision rubric

For each item, the evaluator should walk this checklist:

```
1. Does the cited code at the cited file/line still exist?
   No  → rejected (stale citation)
   Yes → continue

2. Does the cited code exhibit the behavior the reviewer claims?
   No  → rejected (misread / false positive)
   Yes → continue

3. Is the reviewer's suggested fix valid for this codebase?
   No  → can the evaluator propose a corrected fix?
         Yes → accepted with corrected fix
         No  → ambiguous (escalate)
   Yes → continue

4. Does another reviewer source contradict this item's recommendation?
   Yes → ambiguous (cross-source contradiction)
   No  → continue

5. Has the same item appeared in a prior round and been "fixed"?
   Yes → ambiguous (oscillation; the prior fix didn't satisfy)
   No  → accepted
```

The rubric is the evaluator's internal reasoning aid. It is not a script; the evaluator can shortcut steps when the answer is obvious.

## Output JSON schema

The `/do-review` evaluator (whether sub-agent or main-agent direct) produces:

```json
{
  "evaluated_at": "2026-04-26T11:30:00Z",
  "context": {
    "phase": "3" | "7",
    "branch": "feat/foo",
    "worktree": "/Users/.../wt-feat-foo",
    "round": 5,
    "pr_number": 42,
    "sources_evaluated": ["codex", "codex-rescue", "copilot", "greptile", "devin"]
  },
  "decisions": [
    {
      "item_id": "cdx-1",
      "source": "codex",
      "file": "src/foo.ts",
      "line": 42,
      "original_body": "Off-by-one in slice() — drops the last element.",
      "decision": "accepted",
      "rationale": "Confirmed: src/foo.ts:42 reads `arr.slice(0, n-1)` where n is the count, so the last element is dropped. The fix is correct.",
      "fix": "change `slice(0, n-1)` to `slice(0, n)`"
    },
    {
      "item_id": "cdx-2",
      "source": "codex",
      "file": "src/bar.ts",
      "line": 88,
      "original_body": "This might be racey under heavy load.",
      "decision": "rejected",
      "rationale": "src/bar.ts:88 is inside a transaction (lib/db.ts:120-145 wraps it in tx.run). No race possible. Codex didn't read the wrapper."
    },
    {
      "item_id": "cdx-3",
      "source": "copilot",
      "file": "src/baz.ts",
      "line": 1,
      "original_body": "Consider extracting parseConfig into its own module.",
      "decision": "ambiguous",
      "rationale": "Greptile's review on this PR says inline parseConfig (src #5). Cross-source contradiction — needs human."
    }
  ],
  "summary": {
    "total": 3,
    "accepted": 1,
    "rejected": 1,
    "ambiguous": 1,
    "by_source": {
      "codex": {"accepted": 1, "rejected": 1},
      "copilot": {"ambiguous": 1}
    }
  },
  "cross_source_contradictions": [
    {
      "file": "src/baz.ts",
      "line": 1,
      "sources": ["copilot", "greptile"],
      "summary": "copilot says extract, greptile says inline"
    }
  ]
}
```

The schema is the same for inner-loop (Phase 3) and post-PR (Phase 7) evaluators. Inner-loop sets `phase: "3"`, `round`, no `pr_number`. Post-PR sets `phase: "7"`, `pr_number`, no `round`.

## Inner-loop evaluator (Phase 3 worker)

The Phase 3 worker sub-agent's brief includes:
- Context: branch, worktree, round, classifier output (path), prior round summaries.
- Mission: evaluate `major[]` items via `/do-review`, apply accepted subset via diff-walk, push.
- DoD: every major item has a decision; accepted items are committed and pushed; round log updated.

The worker uses `/do-review` (Skill tool with `skill='do-review'`) to do the evaluation. The worker is then the actor that applies — same sub-agent, same context.

If the worker marks all items as rejected for the round, that's still progress: it pushes nothing, the round log records "all rejected", the coordinator increments and continues. **3 consecutive all-rejected rounds → coordinator marks branch DONE.** Codex is stuck on items the evaluator has decided are not real; further rounds won't change that.

## Post-PR evaluator (Phase 7)

After the Phase 6 wait window closes, all reviews are gathered. One evaluator sub-agent per PR is dispatched. Its brief includes:
- Context: PR number, URL, branch, worktree, gathered reviews JSON path.
- Mission: evaluate every item across all sources via `/do-review`, return structured JSON. **Do not modify the worktree.**
- DoD: every item has a decision; output JSON conforms to schema; cross-source contradictions flagged.

The evaluator is read-only on the worktree. It produces decisions; it does not commit. The main agent applies in Phase 8.

## Phase 8 apply (main agent direct)

The main agent reads the Phase 7 evaluator's output and:

```
For each accepted item:
  1. Read the cited code (Read tool).
  2. Compose the fix (use /do-review skill in own context for sanity check).
  3. Edit/Write the change.
  4. git diff (verify only intended hunks).
  5. git add <files>.
  6. git diff --cached.
  7. git commit -m "<emoji> <type>(<scope>): apply <source>'s <item-id>"
       (or: a single commit per source; one commit per item is finer)
For each ambiguous item:
  → do NOT apply.
  → record in BLOCKED list for the PR.
After all accepted items applied:
  git push origin <branch>
  Verify CI is green.
  If ambiguous list non-empty:
    Mark PR BLOCKED in manifest. Surface in deliverable. Do NOT merge.
  Else:
    gh pr merge <number> --repo <fork>/<repo> ...
```

Main agent uses `/do-review` skill (via Skill tool) during the apply to:
- Sanity-check each fix against the evaluator's rationale.
- Catch any edge case the evaluator might have missed.
- Validate the commit subject matches conventional + gitmoji.

This is "the answers come straight back" mode: the evaluator's structured output is in main agent's context, and main agent acts on it directly. No additional sub-agent dispatch needed.

## Failure modes

### Evaluator returns no decision for an item

The evaluator must classify every item. If the brief is followed, this can't happen — the DoD requires a decision per item. If it does happen (degenerate case), the missing item defaults to **ambiguous**. Never silently default to accepted or rejected.

### Evaluator's decisions disagree with classifier

Classifier said major; evaluator says rejected. The evaluator wins for the apply decision. If this happens often (≥ 30% of major items rejected), the classifier policy is too loose — edit `major-vs-minor-policy.md` to demote the recurring keyword.

### Evaluator's accepted fix is wrong

After Phase 8 apply, validation fails or CI breaks. Treat this as a worker-style failure: revert the bad commit, mark the item ambiguous in the manifest, surface for human. Do not auto-retry the same fix.

### Cross-source contradictions

If source A and source B contradict, both items become ambiguous. Surface in the deliverable. Human picks one or splits the branch.

### Oscillation

If the same major item recurs after the evaluator told the worker to apply Codex's fix in a prior round, the fix didn't satisfy Codex. Mark ambiguous; the brief loops back to "Codex sees something the evaluator missed; human decides".

### Evaluator sub-agent crashes (Phase 7)

Heartbeat detection (round-log mtime / manifest write timestamp). If stale, redispatch with the same brief. After 2 redispatches without progress, mark FAILED for that PR; surface for human.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| "I'll apply this one quickly without an evaluator." | Direct-apply violates the rule. Every item needs a decision. |
| "The evaluator is overhead." | The evaluator is the value. Without it, false positives ship. |
| "Codex is usually right; let's skip evaluation for high-confidence items." | "Usually" is not "always". The 5% failure rate is asymmetric (loose-major: a few rounds; missed-real: production incident). |
| Evaluator sub-agent that also commits. | Mixing evaluation and apply. Worker (Phase 3) is allowed; Evaluator (Phase 7) is NOT — Phase 8 apply is main-agent-only. |
| Apply ambiguous items "just in case". | They're ambiguous because they need human input. Applying them silently is worse than not applying. |
| Evaluator decides without reading the cited code. | Citing the rationale to the actual code is the evaluator's value. Without that, the decision is just classification. |

## When the rule does NOT apply

- **No reviews.** If a phase has no reviews to evaluate, no evaluator is dispatched. (Trivially.)
- **The classifier returned no major** (Phase 3, classifier exit 1). Worker is not dispatched; coordinator marks DONE.
- **Phase 8 apply itself.** The apply step uses `/do-review` skill in main agent's context but is not "evaluating a review" — it's executing the evaluator's already-made decisions.

## Bottom line

Every review item — from any source, in any phase — passes through a `/do-review` decision. Accepted gets applied. Rejected gets recorded. Ambiguous gets surfaced. Direct-apply is forbidden by invariant 11. The evaluator is the gate.
