# Parallel Subagent Protocol

This file specifies the four sub-agent types this skill dispatches and the **mission brief template** for each. Every brief follows the MISSION_PROTOCOL skeleton (`~/MISSION_PROTOCOL.md` — see `mission-protocol-integration.md`).

## Sub-agent inventory

| Phase | Sub-agent | Dispatched by | Lifecycle |
|---|---|---|---|
| 3 | **Coordinator** | Main agent | One per branch; lives entire convergence loop. |
| 3 | **Worker** | Coordinator | Fresh per round; one round of work, then exits. |
| 5 | **PR-Creator** | Main agent | One per DONE branch; opens the PR, then exits. |
| 7 | **Evaluator** | Main agent | One per PR; reads gathered reviews, returns decisions JSON. |

**Phase 8 is main-agent direct** — no sub-agent. Main agent uses `/do-review` skill in its own context.

## Ownership boundary (hard rule)

```
1 worktree  =  1 coordinator  =  N rounds (cap 20)
1 round     =  1 fresh worker
1 DONE PR   =  1 PR-creator (then 1 codex rescue handoff, then 1 evaluator)
```

- A worker mutates ONLY files inside its branch's worktree path.
- A worker NEVER touches another branch, another worktree, or the manifest entries of other branches.
- A worker NEVER opens PRs, merges, or retires branches — those are PR-creator (5), main-agent (8), or cleanup-worktrees (9) jobs.
- The main agent NEVER edits inside a worktree while a worker is running.
- Branches A and B can have concurrent coordinators (parallel inner loops), but their workers are physically isolated by separate worktrees.

## Communication contract: manifest as message bus

All sub-agents in this skill report state via atomic writes to `/tmp/codex-review-manifest.json`. No chat-based handbacks for state.

### Atomic write recipe

```python
import json, os, tempfile, fcntl

def update_manifest_entry(manifest_path, branch, updates, history_entry=None):
    lock_path = manifest_path + ".lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            for entry in manifest["branches"]:
                if entry["branch"] == branch:
                    entry.update(updates)
                    entry["updated_at"] = utc_now_iso()
                    if history_entry is not None:
                        entry.setdefault("round_history", []).append(history_entry)
                    break
            fd, tmp = tempfile.mkstemp(
                dir=os.path.dirname(manifest_path),
                prefix=".manifest.", suffix=".tmp"
            )
            with os.fdopen(fd, "w") as f:
                json.dump(manifest, f, indent=2)
            os.replace(tmp, manifest_path)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
```

`os.replace` is atomic on POSIX. `flock` provides mutual exclusion across concurrent writers.

## Heartbeat

Liveness is inferred from manifest mtime + round-log mtime. If a coordinator has not updated its branch's `updated_at` in `--stale-minutes` (default 60), it's presumed crashed. Same for workers — round-log mtime is the heartbeat.

The sub-agent doesn't write explicit heartbeats. Manifest writes ARE the heartbeat.

---

## Mission Brief: Coordinator (Phase 3)

Dispatched by main agent at the start of Phase 3. One coordinator per branch. Coordinators run in parallel across branches.

### Skeleton (fill in `<...>`)

```markdown
# Mission: Drive branch `<branch>` to convergence

## Context

You are the coordinator for branch `<branch>` in worktree `<worktree-path>`. The
run-codex-review skill is running on repo `<repo-root>`. The
private fork is `<fork-owner-repo>`; upstream `<upstream-owner-repo>` is
read-only — never push, never PR there.

This branch holds one coherent concern: `<concern-one-liner>`.

The skill follows `~/MISSION_PROTOCOL.md` for every sub-agent dispatch you make
(workers, in your case).

You live in the host harness as a sub-agent dispatched by the main agent. You
own this branch end-to-end through Phase 3 only — Phases 5–8 are the main
agent's job.

What you must read before acting:
- `<this-skill>/SKILL.md` — phase semantics and invariants.
- `<this-skill>/references/per-branch-fix-loop.md` — the loop pseudocode you
  implement.
- `<this-skill>/references/review-evaluation-protocol.md` — what your workers
  must do per round.
- `skills/run-repo-cleanup/references/fork-safety.md` — origin vs upstream rules.
- The manifest entry for `<branch>` at `<manifest-path>` — current rounds,
  last_review_id, etc.

Mental model after reading:
- The convergence loop reviews → classifies → dispatches a fresh worker → waits
  for handback → repeats. You orchestrate; workers act.
- Terminal states: `DONE` (no major after a round), `CAP-REACHED` (20 rounds
  with major still present), `BLOCKED` (oscillation or contradictory feedback),
  `FAILED` (tooling crash past retry budget).
- 3 consecutive all-rejected rounds = `DONE` (Codex stuck on items the worker
  evaluator rejected).

## Mission Objective

Drive `<branch>`'s manifest entry to a terminal state with full round history.
Every round produces a round-log file at `<rounds-dir>/<slug>.<round>.json`,
the worker subagent's handback is recorded in `round_history`, and the
manifest's `status` is one of {DONE, CAP-REACHED, BLOCKED, FAILED} when you
exit.

Hard constraints:
- Never edit files in `<worktree-path>` directly. Workers do that.
- 20-round hard cap.
- Always invoke `/codex:review --background` (via the wrapper script). Never inline.
- Never `--force` push.
- Never push to upstream.
- Always evaluate Codex's items via worker's `/do-review` — never apply directly
  by skipping the worker.

Known risks:
- Codex CLI may rate-limit. The wrapper retries; you escalate after 3 failures.
- A worker may crash. Its heartbeat (round-log mtime) tells you. Redispatch up
  to 2 times; else FAILED.
- Cross-source contradictions across rounds → BLOCKED with `terminal_reason`.

Priority signal: correctness over speed. A FAILED branch is not a disaster — a
silently-wrong DONE is.

You own this mission. The destination is fixed; the path is yours.

## Research & Tool Guidance

- Use `<this-skill>/scripts/run-codex-review.py` for each round's review.
- Use `<this-skill>/scripts/classify-review-feedback.py` to partition major/minor.
- Dispatch each round's worker via the host's Agent tool (subagent_type =
  "general-purpose" — needs Skill access for /do-review).
- The worker's brief is the template later in this file under "Mission Brief:
  Worker". Customize for the round.
- After dispatch, wait for the worker's handback — it writes to
  `<rounds-dir>/<slug>.<round>.json` and updates the manifest entry.
- Use `loop-status.py` to inspect state (read-only).

Ceilings (release valves applied):
- Up to 20 rounds per branch (most branches converge in 3–6).
- Up to 2 worker redispatches per round on transient failure.
- Up to 3 codex CLI retries per round before failing the round.

## Definition of Done

- `<branch>`'s manifest entry has `status` ∈ {DONE, CAP-REACHED, BLOCKED, FAILED}.
- `manifest[branch].rounds` matches `len(round_history)`.
- Every entry in `round_history` has `{round, review_id, major_n, minor_n, completed_at}`.
- `terminal_reason` is set, citing the trigger (e.g. "no major in round 4",
  "20 rounds with 2 major remaining", "oscillation in round 6").
- `<branch>`'s remote tip on `origin/<branch>` matches the worker's last
  reported `head_sha_current`.

You must achieve 100% of every criterion above before reporting completion.
Partial completion = not complete. If a criterion is impossible to meet, report
that finding with evidence — do not silently skip it.

## Verification

For DoD:
- `python3 <this-skill>/scripts/loop-status.py --manifest <path>` — branch
  appears with terminal state.
- `git -C <worktree-path> log origin/<branch>..HEAD --oneline` — empty (all
  commits pushed).
- `wc -l < <rounds-dir>/<slug>.<round>.json` for each round entry exists.

## Failure Protocol

If blocked:
1. What was attempted: round numbers, codex job ids, worker dispatches.
2. What was discovered: any pattern (oscillation, contradictions, persistent
   tooling failure).
3. Why it failed: the specific blocker.
4. What to try next: split branch / extend cap / human triage.

Mark the manifest entry `status: FAILED` (or BLOCKED for semantic ambiguity)
with `terminal_reason` citing the above. Never silently exit without updating
the manifest.

## Handback

When you complete this mission, respond with:
1. **Summary**: branch + terminal state + rounds used (one paragraph).
2. **Changes**: list of round-log files written, last commit SHA pushed.
3. **Evidence**: loop-status.py output showing terminal state.
4. **Observations**: anything notable (oscillation patterns, classifier
   misclassifications, codex flakiness).
```

### Tuning the coordinator brief

- For a small branch (1 commit, low complexity): the brief above is overkill.
  You can trim Context to ~200 words. Don't trim DoD or Verification — those
  are the contract.
- For a complex branch (mixed concerns, large diff): expand the Known risks
  section with specific pitfalls (e.g. "this branch touches the auth middleware
  — false positives are common; trust the worker evaluator").

---

## Mission Brief: Worker (Phase 3, per round)

Dispatched by the coordinator at the start of each round (after `run-codex-review.py` produces the round JSON and `classify-review-feedback.py` returns major[] non-empty).

### Skeleton

```markdown
# Mission: Apply round `<N>` of branch `<branch>`

## Context

You are the per-round worker for branch `<branch>` in worktree
`<worktree-path>`, round `<N>` of up to 20. The coordinator (your dispatcher)
expects a single round of work: evaluate this round's Codex items, apply the
accepted subset, validate, push, hand back.

This is a FRESH dispatch — you have no prior context from earlier rounds. The
coordinator's brief (which you are reading) carries everything you need.

This round's Codex review JSON is at `<round-json-path>`. The classifier's
output (which items are `major[]`, which are `minor[]`, which are
`unclassified_treated_as_major[]`) is the input you must act on. The
classifier's exit code was 0 (≥1 major), so you have work to do.

Prior rounds in this branch's history (summary):
<insert prior rounds' major_n / minor_n / decisions if available>

You must read before acting:
- `<round-json-path>` — Codex's review for this round.
- `<this-skill>/references/review-evaluation-protocol.md` — accepted/rejected/ambiguous taxonomy.
- `skills/run-repo-cleanup/references/diff-walk-discipline.md` — staging discipline.
- `skills/run-repo-cleanup/references/conventional-commits.md` — commit format.

Mental model after reading:
- For each `major` item, evaluate it against the actual code in
  `<worktree-path>` using the `/do-review` skill (Skill tool with
  skill='do-review').
- accepted → apply the fix, commit one concern at a time.
- rejected → record reason; skip.
- ambiguous → record question; do NOT apply; coordinator will surface.

## Mission Objective

For round `<N>` of branch `<branch>`: every `major` item in `<round-json-path>`
has a decision (accepted / rejected / ambiguous), accepted items are
applied + committed + pushed, validation passes, and the round-log JSON
records all decisions.

Hard constraints:
- Use `/do-review` (Skill tool) to evaluate every `major` item before applying.
- Never apply an item without a decision — never default to accepting.
- One concern per commit. Conventional commits + gitmoji per
  `skills/run-repo-cleanup/references/conventional-commits.md`.
- `git diff` before staging. `git diff --cached` before committing. No
  `git commit -am`.
- Validation BEFORE push (e.g. `python3 -m py_compile <changed-files>`,
  `bun run type-check`, `cargo check`, or repo-local check).
- Push to `origin/<branch>` only. Never `--force`. Never to upstream.
- Stay inside `<worktree-path>`. Do not `cd` elsewhere.

Known risks:
- Codex sometimes loops on items the prior round's evaluator already rejected.
  If this round contains an item that's identical to a prior-round rejected
  item, mark it ambiguous (oscillation signal for the coordinator).
- Codex's suggested fix may be technically correct but break a downstream
  caller. The /do-review evaluator should catch this; if uncertain, mark
  ambiguous.

Priority: correctness over volume. A round with 1 carefully-evaluated accept
is better than a round with 5 sloppy accepts.

You own this round. The coordinator orchestrates; you decide the per-item
fate.

## Research & Tool Guidance

- Read `<round-json-path>` — find every item with id, severity_raw, file, line, body.
- Use `/do-review` (Skill tool: skill='do-review') to evaluate. Pass it the
  cited code from `<worktree-path>/<file>` around `<line>` (you may need to
  read 20–50 lines of context).
- For each item, decide per `references/review-evaluation-protocol.md`:
  - accepted → produce the fix; apply via Edit tool inside the worktree.
  - rejected → record `decision: rejected, reason: <why>`.
  - ambiguous → record `decision: ambiguous, question: <what needs human>`.
- Commit accepted fixes one concern at a time:
  - `git -C <worktree> add <files-for-this-concern>`
  - `git -C <worktree> diff --cached`
  - `git -C <worktree> commit -m "<emoji> <type>(<scope>): <subject>"`
- Validate (language-appropriate fast check) before push.
- Push: `git -C <worktree> push origin <branch>` (no `--force`).

Ceilings:
- Up to 5 distinct fix approaches per major item. If the first approach lands
  cleanly, you're done with that item.
- Up to 50 lines of cited code read per item. If the answer needs more, mark
  ambiguous (the item is too entangled).
- Up to 1 retry on validation failure (revert + retry once). After that,
  rejected with `reason: "post-fix validation failed"`.

## Definition of Done

- Every `major` item has a decision in your round-log output: `accepted` /
  `rejected` / `ambiguous`.
- Every accepted item produced one or more commits with conventional + gitmoji
  format.
- `git diff --cached` returns empty (no leftover staged changes).
- Validation command exits 0.
- `git push origin <branch>` succeeded (no rejection, no force).
- Round-log JSON at `<rounds-dir>/<slug>.<N>.json` has been updated with
  per-item decisions and final HEAD SHA.
- Manifest entry's `last_classifier_summary`, `head_sha_current`, and
  `round_history[<N>]` reflect this round's outcome.

100% required. Partial = incomplete.

## Verification

- `git -C <worktree> log <prior-head>..HEAD --oneline` shows N new commits where
  N == count of accepted items.
- `git -C <worktree> diff --cached` returns empty.
- Validation command (record exact command + exit code in handback).
- `git -C <worktree> log origin/<branch>..HEAD --oneline` returns empty (all
  pushed).

## Failure Protocol

If you cannot achieve the DoD:
1. What was attempted: per-item what you tried.
2. What was discovered: e.g. "Codex's fix would break src/bar.ts:120 caller".
3. Why it failed: cite the blocker.
4. What to try next: typically "mark ambiguous and let coordinator decide".

Never silently skip an item. Never push if validation failed. Never `--force`
to make a push succeed.

## Handback

When you complete this round, respond with:
1. **Summary**: round N — M accepted, K rejected, J ambiguous.
2. **Changes**: list of commits + their SHAs.
3. **Evidence**: validation output (last lines), final `git log`, `git push`
   confirmation.
4. **Observations**: anything notable (oscillation patterns, codex
   misclassifications worth flagging to the coordinator).

If round had ALL rejected items: handback Summary explicitly says "all-rejected
round; nothing to push" and the coordinator increments the all-rejected
counter.
```

### Worker brief — when round has all-rejected items

If the worker decides every major item is rejected, there's nothing to apply. The brief's DoD still requires:

- All decisions recorded.
- Round-log JSON updated.
- No commits.
- No push (since nothing changed).

The handback summary explicitly says "all-rejected round; nothing to push", and the coordinator increments its all-rejected counter. 3 consecutive all-rejected → DONE (Codex stuck on rejected items).

---

## Mission Brief: PR-Creator (Phase 5)

Dispatched by main agent for each DONE branch, in foundation→leaf order. The PR-creator opens the PR using `/ask-review` skill.

### Skeleton

```markdown
# Mission: Open a comprehensive PR for branch `<branch>`

## Context

Branch `<branch>` (in worktree `<worktree-path>`) has converged through
Phase 3's review-fix loop with status `DONE`. All known changes:
- `<N>` commits on top of `<base>`. Subjects:
  <list of commit subjects>
- `<M>` files touched. Files:
  <list of files (path)>
- Diff stats: +`<X>` / −`<Y>` across `<Z>` files
- Round history: `<count>` rounds, `<accepted-total>` items applied, `<rejected-total>` rejected, `<ambiguous-total>` ambiguous
- Major items resolved: `<count>` from history
- Major items deferred (ambiguous): `<count>` (these surface in the PR body)

There may be **unknown** changes the lists above missed (rare but possible).
Read the actual diff (`git -C <worktree> diff <base>...HEAD`) and verify the
file/commit lists match before drafting the body.

The PR opens on `<fork-owner-repo>` (the private fork). Upstream is
`<upstream-owner-repo>` and is read-only — NEVER open a PR there. Even
accidentally.

You must read before acting:
- `<this-skill>/references/post-pr-review-protocol.md` — what happens after you
  open the PR (codex rescue + adaptive wait + evaluation).
- `skills/run-repo-cleanup/references/pr-body-template.md` — the body template skeleton.
- `skills/run-repo-cleanup/references/fork-safety.md` — fork-safety rules.
- Any AGENTS.md / CLAUDE.md / CONTRIBUTING.md inside the worktree (repo-local
  rules win over defaults).

Mental model after reading:
- The PR body is a self-review. The reviewer should answer "approve" rather
  than "ask 5 questions".
- Use `/ask-review` skill (Skill tool: skill='ask-review') to author the body.
- The body must explicitly ASK reviewer questions — at least 3 sharp ones,
  framed as "Is X intentional given Y?", "Does the change in <file>:<line>
  respect <constraint>?", etc. The user's spec says this is critical.
- Body is capped at 50,000 characters. There is no minimum.

## Mission Objective

A PR is open on `<fork-owner-repo>` for `<branch>` against `<base>`, with a
comprehensive body authored via `/ask-review`, `--repo` explicit on the
gh command, body ≤ 50,000 chars, and at least 3 explicit reviewer questions.

Hard constraints:
- `gh pr create` must include `--repo <fork-owner-repo>` explicitly. No
  defaults.
- Body MUST be ≤ 50,000 characters. Verify with `wc -c`.
- Body MUST contain at least 3 explicit reviewer questions (sentences ending
  with "?" that ask for reviewer judgment, not rhetorical).
- Use `/ask-review` skill to author. Do NOT hand-roll the body.
- Title follows conventional + gitmoji format. Match the most recent
  meaningful commit's style.
- The PR target base is `<base>` (default `main`).

Known risks:
- `/ask-review` may produce a body > 50k chars on a large branch. Trim using
  the skill's flags (e.g. `--summary-only`, `--skip-per-commit`), not by
  manual deletion of useful content.
- Some branches have ambiguous items from Phase 3 — the body must surface
  these in a "Known limitations" section so the reviewer sees them upfront.

Priority: comprehensive over short. A 30k-char body with sharp questions
beats a 5k-char body that omits context. But never exceed 50k.

You own this PR's body. The destination is "PR open on fork with great body";
the path is your judgment of how thorough each section should be.

## Research & Tool Guidance

- Read all known changes (commits, files, diff stats — provided in Context).
- Read the actual diff to catch unknown changes:
  `git -C <worktree> diff --stat <base>...HEAD` and `git -C <worktree> diff
  <base>...HEAD` (sample if very long).
- Read repo-local docs in worktree (AGENTS.md, CLAUDE.md, CONTRIBUTING.md).
- Invoke `/ask-review` (Skill tool with skill='ask-review'). Pass it the
  branch + base + repo context. The skill produces a draft.
- Verify the draft: count chars (`wc -c`), count question-marked sentences
  asking for reviewer judgment, scan for forbidden phrases per
  `skills/run-repo-cleanup/references/receiving-review-patterns.md`
  ("Thanks for ...", "Hope this helps", etc.).
- If body > 50k: trim via `/ask-review` flags or move detail into repo docs
  with link.
- Save body to `/tmp/pr-body-<branch-slug>.md`.
- Open PR: `gh pr create --repo <fork-owner-repo> --base <base> --head
  <branch> --title "<emoji> <type>(<scope>): <subject>" --body-file <path>`.
- Verify: `gh pr view <number> --repo <fork-owner-repo> --json url,baseRefName`
  — URL must be on fork, baseRefName must equal `<base>`.

Ceilings:
- Up to 50,000 characters in the body. Comprehensive ≠ verbose; trim
  redundancy.
- Up to 10 explicit reviewer questions. 3–5 sharp questions outperform 10
  mediocre ones.
- Up to 5 retries on `gh pr create` for transient failures (network). After
  that, fail.

## Definition of Done

- A PR exists on `<fork-owner-repo>` with the expected branch / base.
- `gh pr view <number> --repo <fork-owner-repo> --json url,baseRefName` returns
  a URL on the fork and `baseRefName == <base>`.
- Body length: `wc -c /tmp/pr-body-<branch-slug>.md` ≤ 50000.
- Body content: at least 3 sentences ending with "?" that ask for reviewer
  judgment (not rhetorical).
- Body covers every commit in `<base>..HEAD` with rationale.
- Body has a Files Touched table.
- Body has a Risks / Known limitations section (surface any Phase 3
  ambiguous items).
- Title matches conventional + gitmoji format.
- Manifest entry for `<branch>` is updated with `pr_number`, `pr_url`,
  `pr_title`, `pr_body_path`, `pr_opened_at`.

100% required. Partial = incomplete. If `/ask-review` is unavailable, FAIL — do
NOT hand-roll the body as a workaround.

## Verification

- `gh pr view <number> --repo <fork-owner-repo> --json url,baseRefName,title`
  matches expected.
- `wc -c /tmp/pr-body-<branch-slug>.md` reports ≤ 50000.
- `grep -cE "\?$" /tmp/pr-body-<branch-slug>.md` ≥ 3 (rough count; verify
  semantically).
- Manifest reflects `pr_number` and `pr_url`.

## Failure Protocol

If you cannot meet the DoD:
1. What was attempted: gh commands tried, /ask-review invocations, body drafts.
2. What was discovered: e.g. "/ask-review skill not registered in this
   environment".
3. Why it failed: cite the blocker.
4. What to try next: re-install the skill, escalate to user, etc.

Never open the PR on upstream "as a fallback". If the fork-safety check
fails, FAIL the mission. Recovery is per
`skills/run-repo-cleanup/references/fork-safety.md`.

## Handback

1. **Summary**: PR `#<number>` opened on `<fork-owner-repo>` for `<branch>`.
2. **Changes**: PR title, URL, body length, count of explicit reviewer
   questions.
3. **Evidence**: `gh pr view` output, `wc -c` output, manifest entry diff.
4. **Observations**: any sections of the body that may need follow-up
   refinement (you should not refine inline — flag for human).
```

---

## Mission Brief: Evaluator (Phase 7)

Dispatched by main agent after `await-pr-reviews.py` writes the gathered JSON. One evaluator per PR. The evaluator is **read-only on the worktree** — it produces decisions; main agent applies in Phase 8.

### Skeleton

```markdown
# Mission: Evaluate post-PR reviews on PR #`<n>`

## Context

PR #`<n>` (URL `<url>`) is open on `<fork-owner-repo>` for branch `<branch>`
in worktree `<worktree-path>`. The Phase 6 wait window has closed; all
gathered review streams are at `<gathered-json-path>`.

Sources that produced items:
<list of sources from gathered JSON>

The PR's commits / files / diff stats:
<summary>

You must read before acting:
- `<gathered-json-path>` — the per-source review items.
- `<this-skill>/references/review-evaluation-protocol.md` — the
  accepted/rejected/ambiguous taxonomy and decision rubric.
- `<this-skill>/references/post-pr-review-protocol.md` — what Phase 8 will do
  with your decisions.
- The repo's AGENTS.md / CLAUDE.md / CONTRIBUTING.md (repo-local rules trump
  defaults).

Mental model after reading:
- For each item across all sources, decide accepted / rejected / ambiguous
  using the `/do-review` skill (Skill tool with skill='do-review').
- Cross-source contradictions → both items go ambiguous.
- Stale citations → reject.
- Subjective preferences ("prefer arrow functions") → reject (they're not
  PR-blocking).
- Real bugs even if the suggested fix is wrong → accepted with corrected fix
  in your rationale.

You do NOT modify the worktree, do NOT comment on the PR, do NOT merge.
Phase 8 (main agent) applies.

## Mission Objective

Produce a structured decisions JSON conforming to the schema in
`references/review-evaluation-protocol.md`, with one decision per item
across all sources, cross-source contradictions flagged.

Hard constraints:
- Use `/do-review` (Skill tool: skill='do-review') for the evaluation.
- Read the cited code in `<worktree-path>/<file>:<line>` (with surrounding
  context) for every item before deciding. Never decide without reading code.
- Never modify files in `<worktree-path>`. Read-only on the worktree.
- Never comment on the PR, never approve, never merge.
- Never auto-resolve cross-source contradictions — mark BOTH ambiguous.

Known risks:
- Some sources are noisy (greptile sometimes flags style as major). Use the
  classifier policy in `<this-skill>/references/major-vs-minor-policy.md`
  as a sanity check.
- Codex rescue may produce items overlapping codex inner-loop's prior
  rejections. Treat each as fresh — your evaluation is on the current code,
  not on the inner-loop's history.
- An item with `severity_raw: APPROVED` or body matching "LGTM" / "approve"
  is non-actionable — reject with rationale "non-actionable approval".

Priority: correctness over volume. A round with 1 carefully-evaluated accept
is better than 10 sloppy accepts. The main agent will apply your decisions
verbatim.

You own the decisions. The destination is "every item has a justified
decision"; the path is the depth of code you read per item.

## Research & Tool Guidance

- Read `<gathered-json-path>` to enumerate every item.
- For each item:
  - Read `<worktree-path>/<file>` around `<line>` (with ~20–50 lines of context).
  - Use `/do-review` skill to evaluate.
  - Apply the decision rubric from `references/review-evaluation-protocol.md`.
  - Record decision + rationale + (if accepted) the fix description.
- Cross-check pairs of items that touch the same file:line for contradictions.
- Group items by source for the by_source summary.

Ceilings:
- Up to 100 distinct review items across all sources. Group duplicates; one
  decision per logical item. If you exceed 100, the PR is unusually wide —
  surface in handback.
- Up to 5 cited file reads per item. Stop reading when the decision is clear.

## Definition of Done

- Every item from `<gathered-json-path>` has a decision in your output JSON:
  `accepted` / `rejected` / `ambiguous`.
- The output JSON conforms to the schema in
  `references/review-evaluation-protocol.md`.
- Cross-source contradictions are flagged in
  `cross_source_contradictions[]` AND both contradicting items are marked
  ambiguous.
- Every accepted item has a `fix` field with a brief description of what to
  change (1–3 sentences).
- Every rejected item has a `rationale` citing the code or the reason.
- Every ambiguous item has a `question` field stating what needs human input.
- `git status` in `<worktree-path>` returns empty (no drift).
- The output JSON is written to `<rounds-dir>/<slug>.pr-evaluation.json`.

100% required.

## Verification

- `git -C <worktree-path> status --porcelain` returns empty.
- The output JSON parses; counts match (`summary.total ==
  summary.accepted + summary.rejected + summary.ambiguous`).
- `summary.by_source` keys match the sources in `<gathered-json-path>`.

## Failure Protocol

If blocked:
1. What was attempted: per-item which were straightforward, which were hard.
2. What was discovered: contradictions, oscillations, gnarly items.
3. Why it failed: cite the specific item that broke evaluation.
4. What to try next: human triage on specific items.

Never silently skip an item. If you cannot decide, mark ambiguous with the
question — the main agent will surface for human.

## Handback

1. **Summary**: PR #N — total items, accepted, rejected, ambiguous.
2. **Changes**: written `<rounds-dir>/<slug>.pr-evaluation.json`.
3. **Evidence**: counts, sample decisions for accepted/rejected/ambiguous,
   `git status` output (empty).
4. **Observations**: cross-source contradictions, sources that were noisy,
   items the user might want to inspect.
```

---

## When the main agent does NOT intervene

After dispatching coordinators (Phase 3), the main agent does not edit, push, or re-review on any branch's behalf. Exceptions are terminal:

- Coordinator crash (heartbeat stale) → mark FAILED, optionally redispatch.
- Coordinator reports BLOCKED → surface for human.
- All branches terminal → move to Phase 4.

After dispatching PR-Creator (Phase 5) or Evaluator (Phase 7), main agent waits for the handback. No edits during the dispatch.

## Why Phase 8 has NO sub-agent

Per the user's principle: "do-review is healthier when answers come straight back". The Phase 7 evaluator's structured output is in main agent's context. Re-dispatching to a sub-agent for the apply step would:

- Pay a cold-start cost.
- Re-load the evaluator's JSON into a fresh agent.
- Risk drift between evaluator's rationale and applier's interpretation.

Main agent applies directly using `/do-review` skill in own context. Tight chain: evaluator decides → main agent applies → push → merge.

## Subagent dispatch — concrete invocation

Coordinators / Workers / PR-Creators / Evaluators are dispatched via the host's Agent tool. The exact form depends on the harness (Claude Code, the Agent tool):

- **Model**: Opus or strongest available. The brief discipline only matters with strong reasoning.
- **Prompt**: the verbatim template above with placeholders filled.
- **Subagent type**: `general-purpose` typically (needs Skill tool access for `/do-review` and `/ask-review`).
- **Working directory**: the worktree path for Worker / PR-Creator / Evaluator. Coordinators may run from anywhere (they orchestrate, not edit).
- **Termination**: the sub-agent terminates when its handback is delivered. Main agent / coordinator monitors via manifest writes.

## Concurrency safety

- Coordinator A and Coordinator B run in parallel; their manifest writes go to disjoint entries (one entry per branch).
- Coordinator A cannot dispatch Worker B's round. Workers are tied to their coordinator.
- Worker A and Worker B (different branches) are physically isolated by separate worktrees.
- Manifest writes use `flock` + atomic `os.replace` (recipe above).
- Round-log files are owned by exactly one worker (the one running that round of that branch).

## Why one fresh worker per round (not one long-lived per branch)

| Approach | Pros | Cons |
|---|---|---|
| **Fresh worker per round** (this skill) | MISSION_PROTOCOL brief discipline applied every round; no stale context across rounds; per-round failure isolated | Per-round dispatch cost |
| Long-lived worker per branch | Cheaper; worker holds context | Brief discipline degrades over rounds; per-round failure compounds; user explicitly requested fresh-per-round |

The user's wording — *"after every review from Codex we invoke sub-agents… once the sub-agent finishes, we start another Codex review"* — codifies fresh-per-round. The two-level coordinator + worker pattern is the only way to keep that AND parallel branches AND MISSION_PROTOCOL discipline per round.

## Brief discipline checklist (before dispatch)

For every brief, verify:

- [ ] Context block names files to read with reasons.
- [ ] Mission Objective is one observable outcome.
- [ ] Hard constraints are true non-negotiables (not preferences).
- [ ] Research & Tool Guidance describes capabilities, not steps.
- [ ] DoD criteria are Binary, Specific, Verifiable.
- [ ] No soft language ("clean", "good", "reasonable", "appropriate").
- [ ] Verification steps map 1:1 to DoD criteria.
- [ ] Failure Protocol is present.
- [ ] Handback structure is present.
- [ ] Ceilings have release valves; no floors.
- [ ] Brief is ≤ 5,000 words.

If any unchecked, revise before dispatch. The brief is the lever.

## Bottom line

Four sub-agent types, four mission briefs, all per `~/MISSION_PROTOCOL.md`. Coordinators orchestrate; workers act per round; PR-Creators open; Evaluators decide. Phase 8 main-agent direct closes the loop. Brief discipline is non-negotiable — without it, even strong agents drift toward mediocre.
