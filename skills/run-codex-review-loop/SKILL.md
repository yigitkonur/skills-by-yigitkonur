---
name: run-codex-review-loop
description: Use skill if you are running native codex review across multiple branches, comparing findings, or rescuing a saved branch-review loop.
---

# run-codex-review-loop

Run repeatable Codex review passes across a bounded set of branches without relying on the retired `run-codex-2` dispatcher. This skill owns the thin loop around native `codex exec review`; `run-review` in the main pack owns one-off review routing, PR handoff, and feedback triage.

## Use This When

- The user names two or more branches and asks for Codex review, convergence, or close-out.
- A prior branch-review loop has saved review outputs and the user asks to resume or rescue it.
- The user wants a side-by-side comparison of Codex findings across branches.

Do not use this for:

- A single PR, branch, commit, or uncommitted diff. Use `run-review` Mode D.
- Opening a PR or writing a self-review body. Use `run-review` Mode B.
- Triaging human or bot comments already posted on a PR. Use `run-review` Mode C.
- Generic multi-agent implementation fan-out. This skill is review-only.

## Preconditions

Run these before starting the loop:

```bash
codex --version
git rev-parse --is-inside-work-tree
git status --short
```

Require `codex-cli 0.130.0` or newer. If the working tree is dirty, stop and either ask for an explicit `--uncommitted` one-off review via `run-review` Mode D or have the user provide clean branch refs. Do not mix local dirty changes into a multi-branch comparison.

For every branch named by the user:

```bash
git rev-parse --verify <branch>
```

If a branch does not resolve locally, fetch it explicitly or report that it is missing. Do not silently drop it.

## Review Loop

1. Create a timestamped output directory:
   ```bash
   mkdir -p "/tmp/codex-review-loop/$(date +%Y%m%dT%H%M%SZ)"
   ```
2. Record the input manifest as plain text:
   ```text
   base: <base-ref>
   branches:
   - <branch-a>
   - <branch-b>
   ```
3. For each branch, switch to the branch, verify it is clean, and run:
   ```bash
   codex exec review \
     --base <base-ref> \
     --json \
     -o "/tmp/codex-review-loop/<run-id>/<branch-slug>-last.md" \
     "Review only major correctness, security, data-loss, API-contract, and stability risks. Ignore style."
   ```
4. If the user requested a different focus, preserve their wording in the prompt. Do not broaden it.
5. After every run, verify the `-o` file exists and is non-empty before moving to the next branch.

## Resume / Rescue

When resuming, locate the latest run directory under `/tmp/codex-review-loop/` or use the user-provided directory. Read its manifest and list which branch output files already exist. Continue only missing branches unless the user explicitly asks to rerun all.

Never reuse a stale manifest if the branch list in the user's current request differs. Write a new run directory instead.

## Synthesis

Read every `<branch-slug>-last.md` and produce:

| Branch | Verdict | Major findings | Evidence | Next action |
|---|---|---|---|---|

Rules:

- Deduplicate the same finding across branches by file path and behavior.
- Mark findings as `branch-specific` or `shared`.
- If Codex produced no actionable findings for a branch, say `clean` for that branch.
- If a Codex run failed, mark that branch `blocked` with the exact failed command and stderr summary.

## Boundaries

- Do not edit code. This is a review loop, not a fix loop.
- Do not create PRs, push, or post comments unless the user explicitly asks for that separate action.
- Do not invent a replacement dispatcher script. Native `codex exec review` is the execution surface.
- Do not reference retired skills or deleted paths.

## Final Output

Return the run directory, branch matrix, deduplicated findings, failed branches if any, and the exact verification rung reached:

- Rung 1: branch refs verified
- Rung 2: `codex exec review` completed for every branch
- Rung 3: output files checked non-empty
- Rung 4: findings synthesized and deduplicated
