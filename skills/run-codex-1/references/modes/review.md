# Review mode — per-branch convergence loop

Drive `codex exec review` per branch per round. Classify findings as major or minor. Zero major findings converge; major or ambiguous findings block the branch with artifact paths for the main agent to evaluate.

This skill never opens PRs and never merges. Use `review-self` for PR creation and the user's normal merge flow. Review mode produces clean branches and converged findings; the human ships them.

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

One branch IS in scope for review mode — Q2 routes a single named branch to the same per-branch converge-or-cap loop. Use the dispatcher path (`node run-codex-1.mjs review --branches feat/foo`) so you get manifest seeding, monitor wiring, and the markdown→JSON sidecar that feeds `classify-review-feedback.py`. Drop to bare `codex exec review --base main` only when you explicitly do **not** want any of that wiring (e.g. a one-off ad-hoc check whose findings you'll read by eye and discard).

When to skip:
- Branches with mixed concerns → split first via repo-cleanup tools.
- Multi-bot review evaluation → out of scope; this skill drives codex review only.

## Inputs

```
node run-codex-1.mjs review --branches feat/auth feat/billing docs/quickstart
```

`--branches` also accepts a file path: if its value resolves to an existing file, the dispatcher reads one branch per line from it (`expandBranches` in `run-codex-1.mjs:632-649`). So `--branches branches.txt` is equivalent to listing every branch on the command line. There is no separate `--branches-file` flag.

### Stacked branches and `--base`

The dispatcher accepts a single `--base <ref>` that applies to every branch in the invocation. For stacked branches (e.g. `feat/notifications` based on `feat/inbox`, which is itself based on `main`), reviewing all of them in one invocation against `--base main` is wrong — the diff for `feat/notifications` would also include `feat/inbox`'s changes. Run review separately per stack level with the appropriate `--base` for each. Per-branch base override is not yet wired (related to the `round_focus` note below).

Per-branch settings flow through `tasks.json`-like structure inside the manifest:

```json
{
  "branch": "feat/auth",
  "base_branch": "main",
  "max_rounds": 10,
  "round_focus": "the auth subsystem refactor: session handling, token rotation, audit logging"
}
```

`round_focus` is **informational only — not consumed by the runner today; planned.** Neither `handleReview` (`run-codex-1.mjs:1700-1797`) nor `run-review.sh` reads this field. The review prompt template (`references/templates/review.tmpl.md`) leaves `<one-sentence summary of the branch's intent>` as a manual placeholder for the operator to fill before invoking review on a single branch with custom intent.

### Custom-prompt injection: not supported in dispatcher today

The dispatcher does NOT inject prompts into `codex exec review`. `handleReview` (`run-codex-1.mjs:1709-1710`) accepts only these value options: `branches | base | concurrency | cwd | monitor-root | run-id | i-have-measured`. There is no `--prompt`, `--prompt-file`, or `--focus` flag. `run-review.sh:284` invokes `codex exec review` with hardcoded flags plus `--base` and no positional prompt; `mode_state.task.prompt` is not read by the runner. So today there is no first-class path to:

- Inject a custom spec doc as the review focus (e.g. "review against `specs/api-design-v2.md`").
- Express a hostile / aggressive / perf-focused review intent.

The only "intensity" dial wired today is the classifier's **default-when-ambiguous: major** rule (`classify-review-feedback.py:9, 157, 214, 332`), which over-promotes ambiguous findings to major. That is a conservative bias, not a hostility dial; it does not let you redirect codex's attention or change what codex flags.

For perf-focused or hostile review, use workaround (a) below — the single-mode bridge with a hand-crafted brief is the highest-fidelity path. Cross-link `references/universal/prompt-discipline.md` for how to author a hostile-review brief (binary success criteria, explicit attack surface, forbidden hand-wavy verdicts).

**Three documented workarounds** (use the existing fix pattern: do not preserve the dispatcher's hardcoded prompt — bypass it):

1. **Single-mode bridge.** Run `node run-codex-1.mjs single --prompt-file <brief.md>` once per branch with a hand-written brief that names the spec doc or the perf focus and instructs codex to produce review-shaped findings. Loses manifest seeding for the review fleet, monitor wiring, and the markdown→JSON sidecar that feeds `classify-review-feedback.py`. Gains full prompt control. Best for the 1–3 branch case.
2. **Repo-conventions discovery.** Place the spec or focus into `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` at the repo root. The default review template's discovery step (`references/templates/review.tmpl.md:22`) reads those files transparently, so codex picks up the focus without any flag plumbing. Best when the focus is a durable repo concern (the spec is the spec, not a one-off).
3. **Bare `codex exec review`.** Drop the dispatcher entirely for ad-hoc / one-shot needs: `cd <worktree> && codex exec review --base main --json -o <out.md> < <brief.md>`. Loses every piece of skill machinery (manifest, monitor, classifier, audit) but gains full prompt control with no bridge.

Surfacing `--prompt-file` on `handleReview` is a known-but-not-yet-implemented enhancement. Do not promise it; use a workaround above.

## Pre-flight

1. `git rev-parse --is-inside-work-tree` succeeds (`handleReview` refuses if `.git` is absent under the resolved workspace root).
2. Each branch in `--branches` exists locally OR can be fetched from `origin`.
3. Each branch has a remote ref on `origin` (if not, push first).
4. `codex login status` — gated by `bootstrap.sh:74` (called by the dispatcher at `run-codex-1.mjs:1794` *before* every mode handler). `handleReview` itself does not duplicate the check; the universal pre-flight covers it. Escape hatch for proxy / managed-auth setups: `ORCHESTRATE_SKIP_CODEX_AUTH=1` (per `SKILL.md` pre-flight). Skip entirely with `ORCHESTRATE_SKIP_CODEX_PREFLIGHT=1` when the workflow has already verified auth.
5. `<skill-root>/scripts/codex-cc/lib/args.mjs`, `state.mjs`, and `workspace.mjs` are present; the dispatcher imports them.
6. `codex exec review --help` shows `--json`, `-o`, `--base`, `-m`, and `--dangerously-bypass-approvals-and-sandbox`.

## Per-branch flow

**The runner is single-round per invocation.** `run-review.sh <manifest.json> <round-number>` runs exactly one round across every non-terminal branch in the manifest, in parallel (default `JOBS=4`). The dispatcher fires it with round `1`; the operator (or a follow-up wrapper) re-invokes for round 2, 3, … until convergence.

The runner stays single-round-per-invocation by design (it's a worker, not a coordinator). At v2.0-beta the orchestrator (operator or main agent) drives the round loop manually by re-invoking the runner with an incremented round number until convergence. The v3.0 trajectory moves the loop into `handleReview` in the dispatcher; see `../../../../../unification-strategy/tasks/04-phase-three-runners-and-dispatcher.md` Decision 11.

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
        status=done finished_at=now exit_code=0 \
        last_findings_path="$findings_path" \
        last_findings_json="$findings_json"
else
    manifest-update.sh entry "$MANIFEST" "$id" \
        status=failed finished_at=now exit_code="$rc" \
        last_error="codex review exit $rc"
fi
```

That's the entire runner. There is no internal round counter, no apply queue, no all-rejected-streak detection, no terminal-state logic. The runner writes `status=done` when a round produces non-empty findings (the canonical manifest enum has no `reviewed` value — see `references/universal/manifest-contract.md:140`); the **orchestrator** (Claude main agent) is responsible for:

1. Reading `last_findings_json` after the round terminates — that's the path to feed into `classify-review-feedback.py`. The runner synthesizes this JSON sidecar from the per-round JSONL events (see "Findings format" below); `last_findings_path` points at the markdown report and is for human eyes / forensic review only. **Feeding the markdown into the classifier crashes with exit 2.**
2. (Optional) Reading `last_findings_path` for the human-readable narrative.
3. Running `classify-review-feedback.py --input "$last_findings_json"` on the JSON sidecar.
4. Calling `Skill(review-pr)` to evaluate each major item.
5. Applying accepted items via `Edit` directly in the worktree.
6. Pushing the worktree's branch (`git -C <wt> push`).
7. Deciding whether to call the runner again for round 2 — and writing the terminal-state field (`converged`, `cap_reached_*`, `three_all_rejected`, `blocked`) into the manifest by hand via `manifest-update.sh`.

### Findings format

`codex exec review` emits **Markdown** to the path passed to `-o`, even with `--json` set — codex review's `-o` output is its own narrative report, not the JSONL event stream. The runner records this markdown path as `mode_state.last_findings_path`. `classify-review-feedback.py` requires JSON input, so it cannot read that markdown directly.

The runner bridges this gap by synthesizing a sidecar JSON file from the captured JSONL events (`run-review.sh:340-393`) and recording it as `mode_state.last_findings_json`. **That sidecar is what the classifier reads** — always feed `last_findings_json`, never `last_findings_path`. Shape:

```json
{
  "review_id": "<slug>.r<N>",
  "findings": [],
  "raw_text": "<concatenated agent_message text>",
  "slug": "<slug>",
  "base": "<base ref>",
  "round": <N>,
  "findings_md": "<absolute path to the markdown report>",
  "thread_id": "<first thread.started event's id, if any>",
  "agent_messages": ["..."],
  "raw_event_count": <int>
}
```

The `findings` array is empty in today's sidecar — `classify-review-feedback.py` falls back to `raw_text` (concatenated `agent_message` text) for parsing. If the JSONL is missing or malformed the runner writes a stub with an `error` key (`jsonl_missing` / `jsonl_parse_failed`) so the classifier still has something to surface.

Operator-side richer transforms (e.g. handcrafting per-finding `{file, line, severity, category, summary, rationale}` items into `findings`) are still possible and may improve classifier accuracy:

- **Agent bridge.** Spawn a small `single` mode mission with a prompt that reads the markdown at `last_findings_path` and emits enriched `findings[]` items into a JSON file you then pass to `--input`.

Structured-finding extraction inside `run-review.sh` itself is **Planned**.

### Multi-round loop (Planned)

The behavior in earlier drafts — "loop until converged or `max_rounds=10`, detect three-all-rejected streaks, set `terminal_state` automatically" — is **Planned**. Manual workaround for today:

```bash
# Round 1 — fired by the dispatcher automatically.
node run-codex-1.mjs review --branches feat/auth,feat/billing

# Wait for run-review.sh to flip every entry to `done` or `failed`.
# Then for each branch with status=done:
#   - Read mode_state.last_findings_json (sidecar synthesized by the runner).
#   - Classify via classify-review-feedback.py, evaluate via /review-pr,
#     apply via Edit, push.
#   - If round produced fixes → flip status back to queued and fire round 2:

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
- Per-item evaluation is **main agent's** work using `review-pr` or a documented local equivalent. It produces accepted / rejected / ambiguous decisions with rationale.
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
| `done` | One round produced non-empty findings cleanly; the orchestrator must now read `last_findings_json` and decide whether more rounds are needed. **For review mode, `done` is a "round complete, awaiting orchestrator decision" signal — not the final per-branch terminal.** The orchestrator converts to a terminal value (`converged`, `cap_reached_*`, `blocked`, etc.) under `mode_state.terminal_state` once it decides the branch's outcome. The manifest enum has no `reviewed` value (see `references/universal/manifest-contract.md:140`). |
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

Do not invent additional states. If a situation doesn't fit, pick `blocked` with a `terminal_reason` describing the mismatch, surface it, and file the issue. Mapping rule for the runner's per-round `done`: it is **not** the per-branch terminal state. Treat it as "round complete" and write the per-branch terminal under `mode_state.terminal_state` as soon as you've decided the branch's outcome; leaving entries at bare `done` without a `terminal_state` indefinitely is ambiguous between "round 1 awaiting next-round decision" and "branch finished cleanly."

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
3. The user opens PRs via `review-self` (separate skill) and merges via their normal flow.
4. Manifest deleted only after every branch is converged AND every worktree is removed.

The skill **never opens PRs**. Use `review-self` for that.

## Out of scope (kept out, intentionally)

- PR opening — `review-self` owns this.
- Multi-bot review wait — no third-party reviewers; codex is the only review source.
- Foundation-to-leaf merge orchestration — use `run-repo-cleanup` or manual merging.
- Auto-merge — operator-driven only.
- An Applier sub-agent that evaluates and applies — main agent owns evaluation; main agent applies directly via `Edit`.

## Anti-patterns

- Asking codex review to FIX things. Review is read-only by design. The findings are inputs; fixes happen in main agent's own context.
- Letting the classifier output drive apply directly. Always go through main-agent `review-pr` or a documented local equivalent first.
- Extending `max_rounds` past 10 silently. The cap exists to prevent oscillation; bump only after the user confirms the branch needs more rounds AND the trend is convergent.
- Reviewing branches with mixed concerns. Codex flags every concern in every round; the loop never converges. Split first.
- Auto-merging converged branches. The user merges; the skill stops at converged.
