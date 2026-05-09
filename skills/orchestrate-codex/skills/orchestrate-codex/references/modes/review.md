# Review mode — per-branch convergence loop

Drive `codex exec review` per branch per round. Classify findings as major or minor. Zero major findings converge; major or ambiguous findings block the branch with artifact paths for the main agent to evaluate.

This skill never opens PRs and never merges. Use `ask-review` for PR creation and the user's normal merge flow. Review mode produces clean branches and converged findings; the human ships them.

## Contents

- When to pick review mode
- Inputs
- Pre-flight
- Runtime loop
- Terminal states
- Role boundaries
- Recovery

## When to pick review mode

- A list of branches that need rigorous review before shipping.
- Each branch has a coherent concern (one PR's worth of changes).
- The user wants codex review as the source of findings — not Greptile / Devin / Copilot, not human reviewers (yet).

When to skip:
- One branch → run `codex exec review --base main` directly.
- Branches with mixed concerns → split first via repo-cleanup tools.
- Multi-bot review evaluation → out of scope; this skill drives codex review only.

## Inputs

```
node orchestrate-codex.mjs review --branches feat/auth feat/billing docs/quickstart
```

Or `--branches-file branches.txt` (one branch per line).

Per-branch settings flow through `tasks.json`-like structure inside the manifest:

```json
{
  "branch": "feat/auth",
  "base_branch": "main",
  "max_rounds": 10,
  "round_focus": "the auth subsystem refactor: session handling, token rotation, audit logging"
}
```

`round_focus` is the per-branch context the prompt template uses. See `references/templates/review.tmpl.md`.

## Pre-flight

1. `git rev-parse --is-inside-work-tree` succeeds (`handleReview` refuses if `.git` is absent under the resolved workspace root).
2. Each branch in `--branches` exists locally OR can be fetched from `origin`.
3. Each branch has a remote ref on `origin` (if not, push first).
4. `codex login status` — warn unless `~/.codex/config.toml` declares no `model_provider`. Note that `handleReview` itself does **not** call `codex login status` (earlier drafts of SKILL.md claimed it did); the operator should check it manually before invoking review mode if their setup is unusual.
5. `<skill-root>/scripts/codex-cc/lib/args.mjs`, `state.mjs`, and `workspace.mjs` are present; the dispatcher imports them.
6. `codex exec review --help` shows `--json`, `-o`, `--base`, `-m`, and `--dangerously-bypass-approvals-and-sandbox`.

## Per-branch flow

**The runner is single-round per invocation.** `run-review.sh <manifest.json> <round-number>` runs exactly one round across every non-terminal branch in the manifest, in parallel (default `JOBS=4`). The dispatcher fires it with round `1`; the operator (or a follow-up wrapper) re-invokes for round 2, 3, … until convergence.

The multi-round looping shown in earlier drafts of this doc is **Planned — not yet wired** in `run-review.sh`. Until it ships, the operator drives rounds manually.

### What one round actually does

```bash
# In run-review.sh, for each non-terminal entry, in parallel:

# 1. Setup worktree (or reuse if worktree_path is recorded in the manifest).
ALLOW_REUSE=1 bash setup-worktree.sh "$slug" "$branch" "$base"
WORKTREE="../$repo-wt-review-$slug"  # via worktree-contract

# 2. Mark entry running with round counter.
manifest-update.sh entry "$MANIFEST" "$id" status=running attempts=+1 \
    round="$ROUND_NUM" started_at=now

# 3. Run codex exec review. Note: emits MARKDOWN, not JSON, despite --json.
findings_path="$ROUNDS_DIR/$slug.r$ROUND_NUM.md"
jsonl_path="$ROUNDS_DIR/$slug.r$ROUND_NUM.jsonl"
errlog="$ROUNDS_DIR/$slug.r$ROUND_NUM.err.log"

(cd "$WORKTREE" && \
    codex exec review "${CODEX_FLAGS[@]}" --base "$base" --json -o "$findings_path" \
    2>"$errlog") \
    | tee "$jsonl_path" \
    | CODEX_FILTER_LEVEL="$FILTER_LEVEL" bash codex-json-filter.sh \
    | sed "s/^/[review:$slug] /"

# 4. Mark terminal.
if [ ${PIPESTATUS[0]} -eq 0 ] && [ -s "$findings_path" ]; then
    manifest-update.sh entry "$MANIFEST" "$id" \
        status=reviewed finished_at=now exit_code=0 \
        last_findings_path="$findings_path"
else
    manifest-update.sh entry "$MANIFEST" "$id" \
        status=failed finished_at=now exit_code="$rc" \
        last_error="codex review exit $rc"
fi
```

That's the entire runner. There is no internal round counter, no apply queue, no all-rejected-streak detection, no terminal-state logic. The runner emits a `reviewed` status when a round produces non-empty findings; the **orchestrator** (Claude main agent) is responsible for:

1. Reading `last_findings_path` after the round terminates.
2. Bridging the markdown findings into JSON (see "Findings format" below).
3. Running `classify-review-feedback.py` on the JSON.
4. Calling `Skill(do-review)` to evaluate each major item.
5. Applying accepted items via `Edit` directly in the worktree.
6. Pushing the worktree's branch (`git -C <wt> push`).
7. Deciding whether to call the runner again for round 2 — and writing the terminal-state field (`converged`, `cap_reached_*`, `three_all_rejected`, `blocked`) into the manifest by hand via `manifest-update.sh`.

### Findings format

`codex exec review` emits **Markdown** to the path passed to `-o`, even with `--json` set (see `run-review.sh` line ~218 — the file extension is `.md`, and codex review's `-o` output is its own narrative report, not the JSONL stream). `classify-review-feedback.py` requires JSON input.

There is **no built-in bridge** in the current skill. Until one ships, the orchestrator must transform the markdown findings into JSON shaped like:

```json
{
  "branch": "feat/auth",
  "round": 1,
  "items": [
    {"id": "f1", "severity": "major|minor", "file": "src/foo.ts", "line": 42,
     "category": "correctness|stability|data-integrity|security|regression|hygiene|branch-structure|formatting|naming|docs|perf|scope",
     "summary": "...", "rationale": "..."}
  ]
}
```

Workarounds:

- **Manual bridge.** Read the markdown by hand, hand-craft the JSON above, run `classify-review-feedback.py --input <hand-crafted.json>`.
- **Agent bridge.** Spawn a small `single` mode mission with a prompt that converts the markdown findings to the JSON schema; pipe its `-o` file into the classifier.

Either path is currently the operator's responsibility. Markdown-to-JSON inside `run-review.sh` is **Planned**.

### Multi-round loop (Planned)

The behavior in earlier drafts — "loop until converged or `max_rounds=10`, detect three-all-rejected streaks, set `terminal_state` automatically" — is **Planned**. Manual workaround for today:

```bash
# Round 1 — fired by the dispatcher automatically.
node orchestrate-codex.mjs review --branches feat/auth,feat/billing

# Wait for run-review.sh to flip every entry to `reviewed` or `failed`.
# Then for each branch with status=reviewed:
#   - Read mode_state.last_findings_path
#   - Bridge to JSON, classify, evaluate via /do-review, apply via Edit, push.
#   - If round produced fixes → bump round counter, fire round 2:

bash scripts/run-review.sh /abs/path/to/manifest.json 2

# Repeat until convergence or until you've decided one of the terminal states
# below applies. Write the chosen terminal state by hand:

bash scripts/manifest-update.sh entry /abs/path/to/manifest.json <id> \
    status=converged \
    mode_state.terminal_state=converged
```

## Why the role split (read this once)

The script classifies. It does not apply code edits. That boundary keeps review findings observable and keeps contextual decisions in the main agent.

In this skill:
- The classifier (`classify-review-feedback.py`) is mechanical and runs as a script.
- Per-item evaluation is **main agent's** work using `do-review` or a documented local equivalent. It produces accepted / rejected / ambiguous decisions with rationale.
- The apply queue (`apply-review-decisions.py`) is a read-only ordered listing of `file:line:intended-shape:rationale`. The script does not modify the worktree.
- The main agent applies accepted fixes directly in its own context, then reruns review when appropriate.

Direct-apply without contextual evaluation is forbidden. Main agent evaluates; main agent applies.

## Major vs minor policy

Loop on (major):
- correctness bugs in the changed code.
- runtime stability regressions (race conditions, null derefs, silent error swallowing).
- data integrity hazards (lost writes, ordering bugs, partial state on failure).
- security regressions.
- regressions of existing behavior.
- hygiene that hides bugs.
- branch-structure issues that block reviewability.

Do not loop on (minor):
- formatting, naming preferences, style nits.
- doc-only polish.
- speculative perf.
- scope creep.

Default-when-ambiguous (classifier): **major**, conservative. The user's repo `CONTRIBUTING.md` may tighten further; the skill respects it.

## Terminal states

The runner writes one of two `status` values to each entry:

| Status (written by runner) | Meaning |
|---|---|
| `reviewed` | One round produced non-empty findings cleanly; the orchestrator must now read `last_findings_path` and decide whether more rounds are needed. **This is a `running`-flavored status, not a final terminal.** Treat `reviewed` as "round complete, awaiting orchestrator decision." |
| `failed` | The codex-review spawn errored, exited non-zero, produced empty findings, or worktree setup failed. |

The orchestrator-driven terminal taxonomy (the values you write into `mode_state.terminal_state` by hand once you've decided a branch is finished):

| Terminal state | Meaning | Acceptable? |
|---|---|---|
| `converged` | Latest round produced 0 major items after evaluation. | yes — branch is done |
| `cap_reached_with_progress` | Round 10 hit; at least one round pushed fixes; remaining items go to PR body as known-deferred. | yes — branch is done with carry-over |
| `cap_reached_no_progress` | Round 10 hit; no round produced apply-able fixes. | surface — branch likely needs splitting |
| `cap_reached` | Generic round-cap-hit umbrella state when granular sub-state is undecided. | surface; pick `_with_progress` or `_no_progress` once you've inspected the rounds |
| `three_all_rejected` | 3 consecutive rounds where main agent rejected every item. Codex is producing items that don't survive evaluation. | mark done-with-reason; further rounds won't help |
| `blocked` | Major or ambiguous findings require contextual evaluation/apply, persistent ambiguous items, oscillation, or contradictions that need a human decision. | surface for human decision |
| `failed` | Tooling crash past retry budget; codex review crashed; classifier crashed. | surface for human |

Do not invent additional states. If a situation doesn't fit, pick `blocked` with a `terminal_reason` describing the mismatch, surface it, and file the issue. Mapping rule for the runner's `reviewed`: it is **not** a terminal state. Convert to one of the orchestrator-driven values above as soon as you've decided the branch's outcome; leaving entries at `reviewed` indefinitely confuses rescue (which treats `reviewed` as in-flight-ish).

## Recovery

| Symptom | Mitigation |
|---|---|
| `codex exec review` exits non-zero | Re-run once (transient network). On second failure, mark round `failed`, status `failed`, rescue eligible. |
| Classifier cannot parse normalized JSON | Capture the raw output; mark `failed`; the classifier or normalizer needs a fix. |
| Round 10 hit | Set terminal state per the table above. Do not extend the cap silently. |
| Major findings persist after evaluation/apply | Rerun review after fixes; if it oscillates, mark `blocked` and surface the contradiction. |
| Branch CI is red before review starts | Surface immediately. Reviewing red code pollutes the findings. The user fixes CI first. |

Full taxonomy: `references/universal/failure-modes.md`.

## Cleanup

After every branch reaches a terminal state:
1. The skill produces a deliverable: per-branch summary (rounds, classifier outcomes, accepted/rejected/ambiguous counts, terminal state).
2. `python3 cleanup-worktrees.py --execute` removes worktrees for branches that are converged AND merged. Refuses converged-but-unmerged.
3. The user opens PRs via `ask-review` (separate skill) and merges via their normal flow.
4. Manifest deleted only after every branch is converged AND every worktree is removed.

The skill **never opens PRs**. Use `ask-review` for that.

## Out of scope (kept out, intentionally)

- PR opening — `ask-review` owns this.
- Multi-bot review wait — no third-party reviewers; codex is the only review source.
- Foundation-to-leaf merge orchestration — use `run-repo-cleanup` or manual merging.
- Auto-merge — operator-driven only.
- An Applier sub-agent that evaluates and applies — main agent owns evaluation; main agent applies directly via `Edit`.

## Anti-patterns

- Asking codex review to FIX things. Review is read-only by design. The findings are inputs; fixes happen in main agent's own context.
- Letting the classifier output drive apply directly. Always go through main-agent `do-review` or a documented local equivalent first.
- Extending `max_rounds` past 10 silently. The cap exists to prevent oscillation; bump only after the user confirms the branch needs more rounds AND the trend is convergent.
- Reviewing branches with mixed concerns. Codex flags every concern in every round; the loop never converges. Split first.
- Auto-merging converged branches. The user merges; the skill stops at converged.
