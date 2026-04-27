# Major vs Minor Feedback Policy

The classifier (`scripts/classify-review-feedback.py`) partitions Codex's review items into `major[]`, `minor[]`, and `unclassified_treated_as_major[]`. This file is its policy.

**Important framing:** the classifier's `major[]` is a **candidate list for evaluation**, not an "apply-immediately" list. The Phase 3 worker sub-agent runs `/do-review` on each major candidate and decides accepted / rejected / ambiguous. Direct-apply of any classifier output is forbidden by skill invariant 11. See `review-evaluation-protocol.md`.

The classifier is the **first gate** (does this look major?). The evaluator is the **second gate** (is this actually a real issue worth applying?). Both gates are needed — the classifier is fast-and-dumb keyword matching; the evaluator is slow-and-smart code reading.

## Trigger lists

### Major (loop on these — these are CANDIDATES, evaluator decides applies)

Codex feedback that mentions any of these triggers is classified as **major** by `classify-review-feedback.py`. The worker evaluator then decides accepted / rejected / ambiguous.

| Category | Trigger keywords (case-insensitive) |
|---|---|
| Correctness | `correctness`, `wrong`, `incorrect`, `bug`, `off[- ]?by[- ]?one`, `does not handle`, `returns wrong` |
| Runtime stability | `crash`, `panic`, `infinite loop`, `deadlock`, `leak`, `unbounded`, `oom`, `stack overflow` |
| Data integrity | `data loss`, `data corruption`, `lost write`, `race condition`, `racey`, `inconsistent state`, `non[- ]?atomic` |
| Security | `injection`, `XSS`, `CSRF`, `SQL inject`, `auth bypass`, `unsafe deserialization`, `secret`, `credential`, `RCE`, `path traversal`, `SSRF` |
| Regressions | `regression`, `breaks?`, `broken`, `previously worked`, `removed without replacement` |
| Hygiene that hides bugs | `silently? swallow`, `silent fail`, `unreachable`, `dead code that should run`, `unhandled exception`, `missing error check` |
| Branch structure | `mixed concerns`, `commit does too much`, `should be split`, `multiple unrelated changes` |

### Minor (do not loop on these)

| Category | Trigger keywords |
|---|---|
| Formatting | `formatting`, `whitespace`, `indentation`, `line length`, `semicolon` |
| Naming | `rename`, `naming`, `consider naming`, `convention prefers`, `more descriptive name` |
| Style | `prefer`, `idiomatic`, `style`, `nit`, `nitpick`, `cosmetic` |
| Docs polish | `typo in comment`, `comment phrasing`, `docs polish`, `wording` |
| Speculative perf | `might be faster`, `consider caching`, `speculative`, `micro[- ]?optimization` |
| Scope creep | `while you're at it`, `also consider`, `bonus`, `would be nice` |

### Default-when-ambiguous: MAJOR

Items matching neither list (or matching both) are classified as `unclassified_treated_as_major`. Conservative: better the evaluator looks at it than to silently filter it out.

The classifier emits these in a separate bucket so reviewers can see what the policy is being noisy about. The evaluator reads ALL three buckets (major, minor, unclassified) but spends most of its evaluation budget on `major + unclassified_treated_as_major`. Minor items skip evaluation entirely (they're not loop-triggers).

## Severity-aware shortcut

If Codex's `severity_raw` field is one of the standard values, short-circuit:

| `severity_raw` | Classification |
|---|---|
| `critical`, `high`, `error`, `blocker`, `must-fix` | **major** (skip keyword scan) |
| `low`, `info`, `style`, `nit`, `polish`, `optional` | **minor** (skip keyword scan) |
| `medium`, `warning`, `suggestion`, `unknown`, anything else | run the keyword scan |

The keyword scan is the fallback when severity is missing or ambiguous.

## The classifier's role vs the evaluator's role

| Step | Done by | What it does | What it decides |
|---|---|---|---|
| Classify | `classify-review-feedback.py` (script, regex/keyword) | Partitions items into major/minor/unclassified buckets | Which items the loop should LOOK AT |
| Evaluate | Worker sub-agent (Phase 3) using `/do-review` skill | Reads cited code; reasons about each major item against actual codebase | Which items to ACCEPT / REJECT / mark AMBIGUOUS |
| Apply | Worker sub-agent (Phase 3); Main agent direct (Phase 8) | Applies the accepted subset via diff-walk | Whether the fix lands cleanly |

The classifier is **not** the final word. It's the gate that says "this item is worth the evaluator's time". The evaluator's `/do-review` is what decides if Codex was right.

## Worked examples (classifier's view)

| Codex item body | Classifier output | Note |
|---|---|---|
| "Off-by-one in `slice(0, n-1)` — drops the last element." | major | "off-by-one" + "drops the last" — clear correctness issue. Evaluator likely accepts. |
| "This will deadlock when both locks are taken in opposite order." | major | "deadlock". Evaluator must read the lock acquisition order to confirm. |
| "Consider renaming `tmp` to `pendingResult` for clarity." | minor | "consider renaming" — naming. Evaluator never sees this; loop ignores. |
| "Trailing whitespace on line 42." | minor | "whitespace". Evaluator never sees this. |
| "Auth bypass: `if (admin || user.id == req.user_id)` lets any user read any record." | major | "auth bypass" + the specific code is a security issue. Evaluator likely accepts (high signal). |
| "While you're at it, the surrounding test file has a typo." | minor | "while you're at it" — scope creep. Evaluator skips. |
| "This commit mixes the new endpoint with unrelated logging changes." | major | "mixed concerns" — branch structure. Evaluator might accept (split commits) or reject (it's coherent enough). |
| "Consider extracting `parseConfig` into its own module." | unclassified→major | speculative refactor; ambiguous; default major. Evaluator probably rejects (scope creep dressed as defect). |
| "I'm not sure but this might be racey under heavy load." | major | "race" appears (via "racey"); conservative. Evaluator reads the code to verify. |

The classifier's job is breadth (don't miss anything real). The evaluator's job is depth (don't apply anything fake).

## Worked examples (evaluator's view)

The evaluator receives the classifier's `major[]` and decides:

| Item (from classifier as major) | Evaluator decision | Reason |
|---|---|---|
| "Off-by-one in `slice(0, n-1)`" | accepted | Confirmed: code reads `slice(0, n-1)` where n is count. Fix correct. |
| "Race condition under heavy load" | rejected | Read code: this is inside a transaction wrapper; no race possible. Codex didn't see the wrapper. |
| "Mixed concerns in commit" | rejected | Read commit: 3 files, all serving the same concern (renaming + callers + test). Coherent. |
| "Extract parseConfig" | rejected | Scope creep dressed as defect. PR shouldn't expand. |
| "Auth bypass" | accepted | Confirmed: code does `||` not `&&` on the auth check. Fix correct. |
| "Greptile says extract; copilot says inline" | ambiguous (both) | Cross-source contradiction. Surface for human. |

The evaluator's rationales are evidence-cited: every decision references specific code or logic.

## Repo-local overrides

If the target repo's `CONTRIBUTING.md` or `AGENTS.md` says e.g. "all naming nits must be addressed before merge", **honor it**. The override goes into the repo policy, not into per-branch judgement.

To apply a repo-local override, edit `policy.json` next to the script (or pass `--policy <path>`):

```json
{
  "promote_to_major": ["naming", "rename"],
  "demote_to_minor": [],
  "additional_major_triggers": ["custom-trigger-1"],
  "additional_minor_triggers": []
}
```

If `policy.json` is absent, defaults apply.

## Why default-major

Two failure modes are asymmetric:
- **Over-loop on a minor item** (classifier sends it to evaluator; evaluator rejects): cost = evaluator time, but real items still ship correctly. Recovery = adjust the policy.
- **Skip a major item** (classifier filters it out; evaluator never sees it; loop terminates): cost = a real bug ships. Recovery = a bug fix PR after merge.

The over-loop cost is bounded (20-round cap × evaluator time). The skip cost is unbounded (production incident). Default to the bounded failure.

## When the policy is wrong

If the same minor-y item keeps showing up as `unclassified_treated_as_major` AND the evaluator keeps rejecting it:

1. Don't bypass the classifier per branch — that pollutes the loop with judgement calls.
2. Add the item's keyword to the minor list in this file (and the classifier's regex).
3. Re-run the classifier on prior rounds' JSON to confirm the new partition.
4. Document the change in the commit message.

## When the classifier is wrong (false negative)

If a real major item is being misclassified as minor (and never reaches the evaluator):

1. Read the item's body — is the keyword genuinely there?
2. If yes, add a stronger keyword to the major list.
3. If no (the keyword is ambiguous or missing), Codex's output is the issue — file it as a Codex feedback-format mismatch.

## Tie-breaking when both lists match

When the same item matches both major and minor regexes:

1. Count the number of distinct major triggers vs minor triggers in the body.
2. Whichever is higher wins.
3. If tied, **default major**.

The evaluator sorts it out either way.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Treat classifier's `major[]` as "apply this list" | Direct-apply violates invariant 11. Classifier is just the first gate. |
| Skip the evaluator for "high-confidence" major items | "High-confidence" by what metric? The evaluator is the metric. |
| Override the classifier per round (toggle keywords) | Per-round overrides drift; no consistent policy. Edit the policy file once. |
| Add every keyword Codex emits to the major list | Inflates `major[]`; evaluator wastes time rejecting noise. Keep major sharp. |
| Treat `unclassified_treated_as_major` as "skip these" | They go to the evaluator like the others. Default conservative. |

## Bottom line

The classifier is the breadth gate (is this item even worth looking at?). The evaluator is the depth gate (is this item a real problem?). Both gates run on every Codex review. Direct-apply skips both — forbidden. Apply only what the evaluator accepts.
