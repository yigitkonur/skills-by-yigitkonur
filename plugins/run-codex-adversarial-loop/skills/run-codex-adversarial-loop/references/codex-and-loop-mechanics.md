# Codex + loop mechanics

Operational detail for `run-codex-adversarial-loop`. Load when actually firing
reviews, managing worktrees, or deciding when to stop.

## Resolving and invoking the Codex companion

The Codex plugin ships a companion that wraps `adversarial-review` and writes a
structured report. It is version-pinned under the plugin cache; resolve the
newest rather than hardcoding a version:

```bash
COMPANION=$(ls -t ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | head -1)
[ -n "$COMPANION" ] || { echo "Codex companion not found — is the codex plugin installed?"; exit 1; }
```

Invoke one review (run each in the background so many run in parallel):

```bash
node "$COMPANION" adversarial-review "<PROMPT>"
```

The review flags live **inside the prompt string**, not as separate CLI args:
`--model gpt-5.5 --effort xhigh <the rest of the prompt>`.

### Model constraint (important)

On a ChatGPT-account Codex login, use **`gpt-5.5`**. Do NOT use
`gpt-5.5-codex` — it errors with "model is not supported when using Codex with
a ChatGPT account" (that id is API-key only). Use `--effort xhigh` for depth on
hard reviews; drop to `high` for cheaper cursory passes. Confirm the account's
default model with `grep model ~/.codex/config.toml`.

### Prompt-string hygiene (zsh/bash safety)

The prompt is one big double-quoted argument. Avoid characters the shell
expands inside double quotes: **no backticks** (command substitution), **no
un-escaped `$`**, and avoid `!` (history expansion in interactive zsh). Write
`apps/web/src/lib/ui` not a backticked path. Unicode (arrows, en-dashes) is
fine inside quotes.

## Backgrounding and output files

Launch each review with the background option so all reviewers run
concurrently; each writes its full report to its own task output file. Keep a
map of `lens-name → output-file` at launch. Do not read the giant JSONL
transcript of a subagent; for Codex reviews, read the companion's final report
text (the `# Codex Adversarial Review` block at the end of its output file).

Concurrency: firing 15–26 reviews at once is fine. Each is independent.

## Collecting and deduping

Once all reviews are terminal, extract verdicts + finding headlines with
`scripts/scan-verdicts.sh` (pass it the output-file paths). Build one ledger
keyed by `(file, defect-class)`:

- Collapse exact duplicates (two lenses citing the same `file:line`).
- Bucket into: **candidate-real**, **likely-known/by-design**, **out-of-scope**
  (e.g. a finding in a frozen subsystem), **needs-verify-vs-recent-fix** (a
  claim that may already be handled by a prior loop's merge).
- Every candidate-real and every needs-verify item goes to Phase 5 verification.

## Verification routing

Batch verification: one verifier subagent can take a small cluster of related
findings, or one per finding for the trickiest. Verifiers are **read-only** and
**blind to the source** (never told the finding came from Codex — frame as "a
prior analysis flagged…"). They return CONFIRMED / REFUTED / PARTIAL with cited
evidence, plus any additional issues they noticed. Treat their output as a
claim too, but a much stronger one than the raw review.

## Worktree discipline (fixers)

Every fixer runs in an **isolated worktree created before the fixer is
assigned** — never the main checkout, so parallel fixers cannot corrupt each
other. Two ways, depending on the harness:

- If launching fixers via a subagent tool that supports worktree isolation,
  request that isolation per fixer.
- Otherwise create one explicitly per group: branch off the current integration
  branch, e.g. `git worktree add ../wt-fix-<group> -b fix/<group> <base>`, and
  point the fixer at that path.

Enforce **disjoint file ownership**: give each fixer its file set AND the list
of files sibling fixers own, with "do not touch those". Same-file findings must
land in the same fixer. This is what lets many fixers run at once without merge
conflicts.

## Merge discipline

- A fixer's "CI is green" is a claim. Read the run yourself: confirm
  `conclusion == success` **on the exact head SHA the fixer pushed**, and that
  the required gate check passed. A green on a stale SHA is a false green.
- Merge greened PRs into the integration branch one at a time; if the tree
  moved, rebase the remaining fixer branches before merging.
- After a merge, pull the integration branch so the next decisions see truth.

## Build-check routing (Phase 9)

After a batch merges, run the project's build/test gate on the integration
branch. Route by size:

- **Minor** (lint nit, trivial type, stray import, formatting): the
  orchestrator fixes it inline and re-pushes.
- **Non-trivial** (a real regression, a cross-cutting break): spawn one focused
  subagent with the failing output; drive it to green like any fixer.

Return the branch to green before looping.

## Loop and convergence

Each iteration re-explores and re-derives lenses; **reviewers are stateless** —
give them no hint that earlier iterations happened (so they audit fresh and
sample different corners). Carry forward only the cumulative already-fixed
ledger (so they do not re-report merged fixes).

Stop when any holds:

- A whole wave **converges to noise**: findings are only low-value hardening on
  not-yet-built surfaces, or verifiers refute the majority.
- A user-set bound is hit (max loops, time, or token budget).
- The remaining findings are all out-of-scope (belong to a frozen/owned
  subsystem) → hand them to the backlog.

Report each wave's yield (real fixes merged vs refuted vs out-of-scope) so the
convergence decision is evidence-based, not a guess.

## Cost note

Many parallel xhigh reviews plus verifiers plus fixers is a large spend. Confirm
the user wants that scale before a big wave, and prefer fewer, well-grouped
lenses over many redundant ones — the minimal covering set is cheaper AND finds
more per run than a broad crowd that re-discovers the same issues.
