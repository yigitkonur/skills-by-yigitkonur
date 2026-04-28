# Parallel Subagent Protocol

This file specifies the four sub-agent types this skill dispatches and the **mission brief template** for each. Every brief follows the MISSION_PROTOCOL skeleton (`~/MISSION_PROTOCOL.md` — see `mission-protocol-integration.md`).

## Invocation matrix per brief

The codex plugin marks `/codex:review` as `disable-model-invocation: true`. Sub-agents physically cannot call it via `Skill(...)` — they must invoke the underlying companion script via Bash. `/codex:resc` requires the `Agent` tool which forked sub-agents do not have. Use the matrix below in every brief:

| Surface | Worker / PR-Creator / Evaluator | How to invoke from the brief |
|---|---|---|
| Codex review | Worker (Phase 3) | `python3 <this-skill>/scripts/run-codex-review.py --branch … --base … --worktree … --output …` (wrapper internally calls `codex-companion.mjs review --json`). |
| Codex rescue | NOT for sub-agents | Phase 6 trigger is main-agent-only; sub-agents do not call it. |
| `/ask-review` | PR-Creator (Phase 5) | `Skill(skill="ask-review", args="…")` — model-invocable. |
| `/do-review` | Evaluator (Phase 7) | `Skill(skill="do-review", args="…")` — model-invocable. |
| `/do-review` | Worker (Phase 3) | **Never.** Workers are appliers; decisions are pre-made before dispatch. See "Mission Brief: Worker" below. |

**Forbidden in every brief:**

- Direct shell invocation of `codex`, `codex review`, `codex review --background`, or any other `codex …` form (no such CLI flags exist).
- Inventing a "shim" or wrapper because the codex CLI doesn't accept some flag.
- Inventing a coordinator/worker pattern that diverges from the templates below.
- Calling `Skill(codex:review)` or `Skill(codex:resc)` from a sub-agent context — both will fail; the plugin disables them.

If `<this-skill>/scripts/run-codex-review.py` cannot find a working `codex-companion.mjs`, the codex plugin is missing. Sub-agent hands back FAILED with `terminal_reason: "codex plugin unavailable"`. Main agent surfaces to the user and stops.

## Sub-agent inventory

| Phase | Sub-agent | Dispatched by | Lifecycle |
|---|---|---|---|
| 3 | **Applier** | Main agent | Fresh per round per branch; applies pre-decided fixes, validates, pushes, exits. |
| 5 | **PR-Creator** | Main agent | One per DONE branch; opens the PR, then exits. |
| 7 | **Evaluator** | Main agent | One per PR; reads gathered reviews, returns decisions JSON. |

**Main agent is the coordinator across all branches** — it owns the round cadence, runs codex review wrappers in parallel, evaluates major items via `Skill(do-review)` in its own context, and dispatches per-round Appliers. Phase 8 is also main-agent direct.

> **Why main-agent-as-coordinator (load-bearing):** older versions of this skill used a per-branch Coordinator sub-agent that held the convergence loop. In practice these long-lived sub-agents (5+ hours, dozens of rounds) drift, lose context, or hit harness session limits. Main agent is the only stable owner of the multi-hour cadence. Sub-agents are short-lived single-purpose appliers / PR-creators / evaluators.

## Ownership boundary (hard rule)

```
1 worktree  =  1 branch  =  N rounds driven by main agent (cap 20)
1 round-per-branch  =  1 fresh Applier sub-agent
1 DONE PR  =  1 PR-Creator → 1 codex rescue (main-agent direct) → 1 Evaluator
```

- An Applier mutates ONLY files inside its branch's worktree path.
- An Applier NEVER touches another branch, another worktree, or the manifest entries of other branches.
- An Applier NEVER opens PRs, merges, or retires branches — those are PR-Creator (5), main-agent (8), or cleanup-worktrees (9) jobs.
- An Applier does NOT run codex review or classify — main agent does that before the dispatch.
- Main agent NEVER edits inside a worktree while an Applier is running.
- Different branches can have concurrent Appliers (parallel rounds across branches), physically isolated by separate worktrees.

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

## Brief templating (mandatory for parallel dispatches)

When dispatching N parallel sub-agents (N appliers in Phase 3, N PR-Creators in Phase 5, N evaluators in Phase 7), **never hand-write N separate briefs via N `Write` tool calls**. That pattern burns thousands of tokens, drifts copy-paste errors across briefs, and adds 5+ minutes of wall-time per phase.

**Mandatory pattern:**

1. Write **one** template file with `{{PLACEHOLDER}}` slots, e.g. `/tmp/applier-brief-template.md`.
2. Render N concrete briefs from the template + a per-branch decisions JSON in **one Python invocation**:

```python
import json, pathlib
template = pathlib.Path("/tmp/applier-brief-template.md").read_text()
decisions = json.loads(pathlib.Path("<rounds-dir>/decisions.json").read_text())
for branch_slug, payload in decisions.items():
    body = template
    for k, v in payload.items():
        body = body.replace(f"{{{{{k}}}}}", v if isinstance(v, str) else json.dumps(v, indent=2))
    pathlib.Path(f"/tmp/applier-brief-{branch_slug}.md").write_text(body)
print(f"rendered {len(decisions)} briefs")
```

Then dispatch:

```
for branch_slug in decisions:
    Agent(
        prompt=f"Read /tmp/applier-brief-{branch_slug}.md and execute.",
        subagent_type="general-purpose",
        run_in_background=True,
    )
```

**Why mandatory**: production trace showed an agent writing 7+5+9 = 21 briefs across Phases 3 and 5 via 21 separate Write calls. Each brief was 50-140 lines of mostly-identical text with per-branch decisions varying. Template + render in one shot is ~3 tool calls vs. 21; cuts orchestration cost by ~85%.

**Brief content rules** (apply per template type):

- Applier briefs: one template per round (`/tmp/applier-brief-template-r<N>.md`); placeholders for branch, worktree, base, prior-round commits, this-round decisions.
- PR-Creator briefs: one template; placeholders for branch, worktree, base, status, round_history summary, concern.
- Evaluator briefs: one template; placeholders for PR number, gathered-reviews JSON path, taxonomy reference.

The template ITSELF must be revised when its corresponding "Mission Brief" template skeleton in this file changes. The two are versioned together.

## Heartbeat

Liveness is inferred from manifest mtime + round-log mtime. If an Applier has not updated its branch's `updated_at` in `--stale-minutes` (default 60), it's presumed crashed. The sub-agent doesn't write explicit heartbeats — manifest writes ARE the heartbeat.

---

## Coordinator role (main-agent self-direction)

There is **no Coordinator sub-agent** in this skill. Older drafts dispatched a per-branch Coordinator subagent that held the convergence loop; in production those long-lived sub-agents drift, lose context, or hit harness session limits. **Main agent is the coordinator across all branches** — it owns the round cadence directly.

Main agent's coordinator self-direction (no brief — main reads this section as its own playbook):

- **Per round across all active branches:**
  1. In parallel, launch `python3 <this-skill>/scripts/run-codex-review.py --branch <b> --base <base> --worktree <wt> --output <rounds-dir>/<slug>.<round>.json` for every active branch via Bash background tasks.
  2. As each review completes (Monitor or Bash run_in_background callbacks), run `python3 <this-skill>/scripts/classify-review-feedback.py --review-json <path>`.
     - Exit 1 (no major) → mark branch DONE with `terminal_reason: "no major in round <N>"`.
     - Exit 0 (≥1 major) → continue.
  3. For each major item, read cited code (Read tool, ±25 lines around `file:line`), then call `Skill(skill="do-review", args="--item <body> --code <cited_code>")` in main's own context. Record decision per `references/review-evaluation-protocol.md`.
  4. For each branch with at least one accepted decision: dispatch ONE Applier sub-agent with the brief in "Mission Brief: Applier" below. Pre-decided fixes baked in.
  5. As Appliers hand back, update manifest's `round_history[<N>]` per branch.
  6. Increment per-branch round counter; loop until all branches terminal.

- **Terminal states** (`manifest.status`):
  - `DONE` — no major after a round (classifier exit 1).
  - `CONVERGED-AT-CAP` — `<this-skill>'s` configured `max_rounds_per_branch` exhausted with at least one round of fixes pushed; remaining items captured in PR body. (See SKILL.md "Convergence taxonomy".)
  - `CAP-REACHED` — 20 rounds (or configured cap) with no convergence. Surface for human.
  - `BLOCKED` — oscillation (3 consecutive all-rejected rounds → reclassify as DONE; persistent ambiguous items → BLOCKED) or cross-source contradictions.
  - `FAILED` — tooling crash past retry budget; codex plugin unavailable; Applier failed to push.

- **Non-negotiables:**
  - Never edit inside a worktree while its Applier is running.
  - Never `--force`. Never push to upstream.
  - Decisions stay with main agent; appliers stay mechanical.
  - Read the manifest, not the worktree, for state — Appliers update the manifest atomically.

- **Cost / wall-time expectations** (do not be surprised; do not invent shortcuts):
  - Each codex review wrapper call: ~3–15 minutes wall.
  - Each Applier dispatch: ~3–10 minutes wall.
  - Round per branch: ~10–25 minutes serial. With N parallel branches: same wall, N× quota.
  - Typical convergence: 3–6 rounds per branch (per `references/major-vs-minor-policy.md`).
  - Round-2+ commonly find new items (refinements of round-1 fixes). 6/8 branches in production runs needed round-2 fixes. **This is normal — do not invent `DONE-PRAGMATIC` to shortcut.**

---

## Mission Brief: Applier (Phase 3, per round)

Dispatched by **main agent** (not by a coordinator subagent — that role was dropped) at the start of each round, after main agent has:
1. Run the codex review wrapper for this branch.
2. Run the classifier to partition major/minor.
3. Evaluated each major item itself using `Skill(do-review)` in main's own context.
4. Composed the per-item fix specs (file, line, intended code shape, rationale).

The applier's job is **mechanical**: apply the pre-decided fixes, validate, push. It is not an evaluator. The brief MUST NOT mention `/do-review` — that framing pulls the agent into evaluator-mode and produces decision-only failure.

### Skeleton

```markdown
# Mission: Round <N> of `<branch>` — apply N pre-decided fixes, validate, push

You are an APPLIER for branch `<branch>` in worktree `<worktree-path>`. The
decisions below were made before this dispatch. Your only job is BINARY
EXECUTION: apply, validate, push. **Anything short of pushed commits is FAILED.**

This is NOT an evaluation task. Do NOT invoke `/do-review`. Do NOT propose
alternative fixes. Do NOT produce decision JSON. Do NOT stop at "Verdict:
apply" — apply IS the deliverable.

## Context

- **Worktree**: `<worktree-path>`
- **Branch**: `<branch>` (on `origin/<branch>`)
- **Base**: `<base-ref>`
- **Round**: <N> of up to 20. Prior rounds (if any): <commit SHAs>.
- **You own this worktree's setup.** If validation needs `node_modules` /
  `.venv` / build artifacts that don't exist yet, install them yourself
  (`pnpm install`, `npm install`, `bun install`, `pip install -r ...`).
  Main agent does NOT preflight dependencies.

## Pre-decided fixes (apply each exactly)

### Fix 1: <one-line summary>
- **File**: `<worktree-path>/<file>`
- **Around line**: <line>
- **Current shape** (verbatim from current code):
  ```
  <existing code excerpt>
  ```
- **Intended shape** (apply this; preserve indentation):
  ```
  <new code excerpt>
  ```
- **Rationale**: <why — main agent's evaluator decision summary>
- **Commit message**: `<emoji> <type>(<scope>): <subject>` per
  `skills/run-repo-cleanup/references/conventional-commits.md`.

### Fix 2: …
(repeat per item)

## Hard constraints

- One concern per commit. N fixes = N commits.
- `git diff` before staging. `git diff --cached` before committing. No `git commit -am`.
- Validate BEFORE push (e.g. `pnpm run build && pnpm test`, `bun run type-check`,
  `cargo check`, or whatever the repo's `CONTRIBUTING.md` / `AGENTS.md` says).
- Push to `origin/<branch>` only. Never `--force`. Never to upstream.
- Stay inside `<worktree-path>`. Do not `cd` elsewhere.

## Definition of Done (binary)

- N new commits exist on local HEAD with conventional + gitmoji messages.
- `git -C <worktree-path> diff --cached` returns empty.
- Validation command exits 0.
- `git -C <worktree-path> push origin <branch>` succeeded.
- `git -C <worktree-path> rev-parse origin/<branch>` matches local HEAD.
- Manifest entry updated: `head_sha_current`, `round_history[<N>]`.

Anything short of all of the above = FAILED. Hand back FAILED with
`terminal_reason` naming the specific gate that did not pass.

## Failure protocol

- If a fix's intended shape doesn't apply cleanly (file moved, line shifted,
  current shape mismatch): STOP, do NOT improvise. Hand back FAILED with
  `terminal_reason: "fix N intended-shape mismatch — main agent re-evaluate"`.
  Main agent will re-decide and re-dispatch.
- If validation fails after a fix: revert the offending commit, hand back
  FAILED with the validation output.
- If push is rejected (non-fast-forward, hook failure): hand back FAILED with
  the rejection output. NEVER `--force`.

## Handback shape

```json
{
  "applied": <N>,
  "pushed": true | false,
  "head_sha": "<sha>",
  "validation_exit": 0 | <nonzero>,
  "commit_shas": ["<sha1>", ...],
  "terminal_reason": null | "<one-sentence>"
}
```
```

### Why no `/do-review` in this brief

Empirically verified across multiple production runs: when the worker brief mentions `/do-review`, ~100% of dispatched workers stop after producing decision JSON without applying or pushing. The /do-review framing pulls the agent into evaluator-mode; "Verdict: apply" feels like the deliverable to the agent. Splitting evaluation (main agent) from application (worker, with explicit pre-decided fix specs and binary push DoD) is the empirical fix. Do not re-introduce eval framing into the worker brief.

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
