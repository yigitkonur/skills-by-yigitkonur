---
name: run-codex-review-loop
description: "Use skill if you are running repeatable Codex reviews across lenses or branches, optionally verifying and fixing confirmed findings in isolated worktrees."
---

# run-codex-review-loop

Run repeatable Codex review passes without relying on a retired dispatcher. This skill owns multi-round native Codex review execution; `run-review` owns one-off review routing, PR handoff, and feedback triage.

Three modes:

- **Mode A — Multi-lens checkout audit (default):** review the **current active checkout branch** (whatever `git branch --show-current` reports — often `main`) through many independent review lenses, in rounds, until findings converge.
- **Mode B — Multi-branch comparison:** the original branch loop — run review across two or more named branches and compare findings.
- **Mode C — Verified fix loop:** run the multi-lens audit, independently verify every candidate finding, fix confirmed issues in isolated worktrees, merge only exact-SHA-green changes, and repeat with fresh reviewers until convergence.

Route by requested outcome:

- Two or more named branches, comparison, or branch close-out -> Mode B.
- Explicit permission to fix, merge, or keep going until clean -> Mode C.
- Everything else — "review the whole project", "full audit", "multiple lenses", "review main", "review the current branch" — -> Mode A.

## Use This When

- The user asks for a complete, multi-lens, whole-project Codex review of the current checkout branch.
- The user asks to keep reviewing until issues converge or the branch is clean enough.
- The user names two or more branches and asks for Codex review, convergence, close-out, or comparison.
- The user asks to verify and fix review findings through isolated worktrees and exact-SHA CI.
- A prior review loop has saved outputs and the user asks to resume or rescue it.

Do not use this for:

- A single small PR, commit, or uncommitted diff. Use `run-review` Mode D.
- Opening a PR or writing a self-review body. Use `run-review` Mode B.
- Triaging human or bot comments already posted on a PR. Use `run-review` Mode C.
- Generic multi-agent implementation fan-out. Mode C fixes only independently verified review findings.

## Preconditions

Run these before any mode:

```bash
codex --version
git rev-parse --is-inside-work-tree
git branch --show-current
git rev-parse --verify HEAD
git status --short
```

Require `codex-cli 0.130.0` or newer.

- **Mode A:** a dirty tree is allowed because the target is the current checkout as-is. Record `tree: clean|dirty` in the manifest.
- **Mode B:** a dirty tree blocks. Stop and either ask for clean branch refs or use a one-off review flow instead.
- **Mode C:** require a known clean integration branch, an identified build/test gate, and explicit authority for the intended fixes, branches, pushes, PRs, and merges. Do not infer external-write authority from a request to review.

For every branch named in Mode B:

```bash
git rev-parse --verify <branch>
```

If a branch does not resolve locally, fetch it explicitly or report that it is missing. Do not silently drop it.

## Mode A — Multi-lens checkout audit

### Phase 0: Explore first

Do not start with Codex prompts. First understand the project enough to choose the right review lenses.

Spawn 1–3 **Sonnet-class explore agents** — Claude Sonnet or an equivalent mid-tier model. The point is fast, broad project mapping, not top-tier deep reasoning. Use equivalent local/default agents if Sonnet is unavailable. Give each agent a bounded mission such as:

- Map the repo: product purpose, areas, entry points, runtime boundaries, and highest-risk modules.
- Identify external systems, credential paths, write/mutation paths, data stores, and irreversible operations.
- Read AGENTS.md/CLAUDE.md plus architecture/safety docs and extract the invariants the code must uphold.
- Find where docs make concrete guarantees that could drift from implementation.

The explore outputs are steering inputs. They decide what Codex reviews to run. Do **not** use a generic checklist when the project tells you what matters. A fragile ERP integration needs concurrency/token/governor lenses; a public web API needs authz/rate-limit lenses; a data pipeline needs idempotency/freshness/data-loss lenses.

Highest priority targets are the project's own explicit invariants — especially AGENTS.md, CLAUDE.md, operational-safety docs, architecture docs, and schemas. A contradiction between a stated invariant and runtime code is usually a real finding.

### Phase 1: Plan each round

From exploration, write a lens list for round 1.

Rules:

- Run **minimum 3 and maximum 20 Codex reviews per round**.
- Scale with repo size and risk. 5–8 lenses is typical for a mid-size repo; 12–20 is for large or safety-critical systems.
- Each lens must be genuinely distinct: different subsystem, different failure class, or different design question.
- Do not split one lens into many near-duplicates just to hit a count.
- If the user supplied focus text, preserve it and route it into the lens plan; do not broaden away from it.

Good lens shapes:

- Safety-critical subsystem plus all callers.
- Security and credential handling, including git history when relevant.
- API contract, schemas, samples, and data integrity.
- Error paths, partial failure, retries, idempotency, and data loss.
- Concurrency, locking, queues, cancellation, and shutdown behavior.
- Adversarial architecture challenge: assumptions, tradeoffs, scaling limits, single points of failure.
- Docs-vs-code drift for operational claims.
- Test coverage versus stated invariants.

Every lens prompt must demand:

- Read complete relevant files, not only search snippets.
- Trace at least one concrete path from entry point to risky behavior.
- Report only correctness, security, data-loss, API-contract, stability, or design-risk findings.
- Ignore style, formatting, naming, and vague best-practice advice.
- Give file:line evidence, concrete trigger scenario, severity, and why it matters.
- If clean after genuinely tracing, say `clean` explicitly.

### Phase 2: Run the round

Create one run directory and one subdirectory per round:

```bash
mkdir -p "/tmp/codex-review-loop/$(date +%Y%m%dT%H%M%SZ)/round-1"
```

Record a manifest at the run root:

```text
mode: multi-lens
branch: <current-branch>
head: <sha>
tree: clean|dirty
rounds-max: 10
round: 1
lenses:
- <lens-slug>: <one-line focus>
```

Launch all lenses for the round in parallel, preferably in background tasks, one Codex run per lens. Use whichever execution surface is available:

1. Codex companion runtime if installed:
   ```bash
   node "<codex-plugin>/scripts/codex-companion.mjs" task "<lens prompt>"
   ```
2. Native Codex:
   ```bash
   codex exec review --json -o "/tmp/codex-review-loop/<run-id>/round-N/<lens-slug>.md" "<lens prompt>"
   ```

After each run completes:

- Verify the output exists and is non-empty.
- Save or copy the result to `<run-dir>/round-N/<lens-slug>.md` so the run is resumable.
- If a run fails, mark that lens `blocked` with the exact command and stderr summary. Do not silently drop it.

### Phase 3: Synthesize the round

Read every lens output and produce a deduplicated table:

| # | Severity | Finding | Evidence | Lenses | Status |
|---|---|---|---|---|---|

Rules:

- Deduplicate by file path plus behavior, not by wording.
- Mark findings seen by multiple independent lenses as corroborated.
- Carry status across rounds: `new`, `still-open`, `fixed-verified`, or `regressed`.
- If a lens found nothing, record `clean` for that lens.
- Do not treat a Codex report as verified truth. Independently check every substantive finding against the current code and classify it `confirmed`, `refuted`, or `partial` with file:line evidence. A clean verdict remains clean; never require a reviewer to invent a finding.

### Phase 4: Loop until convergence

Run up to **10 rounds**. In Mode A, fixes may be applied outside this skill by the main agent or user; Mode A itself remains review-only. Mode C owns its explicitly authorized fix loop.

For each next round:

- Re-read the current branch/HEAD and update the manifest.
- Keep lenses that found confirmed high-value issues, rewritten to verify whether those issues still exist.
- Drop lenses that came back clean twice unless new code makes them relevant again.
- Add new lenses if fixes, exploration, or prior findings reveal a new risk area.
- Do not exceed 20 lenses in any round.

Stop early when the loop converges. Convergence means one of:

- A round returns only small-detail/trivial findings: no critical/high issues and nothing that changes behavior, data integrity, security, API contract, or operational safety.
- Two consecutive rounds add no new substantive findings.
- All previously confirmed substantive findings are verified fixed or intentionally accepted by the user.

When stopping, state exactly which condition fired. Do not keep grinding after convergence; extra rounds at that point manufacture noise.

## Mode B — Multi-branch comparison

1. Create a timestamped run directory and manifest:
   ```text
   mode: branch-comparison
   base: <base-ref>
   branches:
   - <branch-a>
   - <branch-b>
   ```
2. For each branch, switch to it, verify clean, and run:
   ```bash
   codex exec review \
     --base <base-ref> \
     --json \
     -o "/tmp/codex-review-loop/<run-id>/<branch-slug>-last.md" \
     "Review only major correctness, security, data-loss, API-contract, and stability risks. Ignore style."
   ```
3. Preserve any user-provided focus text. Do not broaden it.
4. Verify each output file exists and is non-empty before moving to the next branch.
5. Synthesize:

| Branch | Verdict | Major findings | Evidence | Next action |
|---|---|---|---|---|

Deduplicate shared findings across branches. Mark findings as `branch-specific` or `shared`. Mark clean branches as `clean`. Mark failures as `blocked` with exact command and stderr summary.

## Mode C — Verified fix loop

Mode C reuses Mode A Phases 0–3, then continues through verification, repair, and a fresh review round. Read these before execution:

- `references/lens-design.md` for deriving the smallest covering lens set;
- `references/prompt-templates.md` for explorer, reviewer, verifier, and fixer briefs; and
- `references/codex-and-loop-mechanics.md` for Codex invocation, resumable artifacts, worktrees, exact-SHA CI, merge order, and convergence.

### Phase 4: Verify every candidate

For each candidate finding or tight related cluster, dispatch an independent read-only verifier that is blind to the source. Ask whether the claim is `CONFIRMED`, `REFUTED`, or `PARTIAL`, require cited evidence and a concrete failure scenario, and invite nearby related findings.

The orchestrator makes the final decision. Keep confirmed findings, narrow partial findings to their proved core, and record refuted findings so later rounds do not repeat them. No fixer may receive an unverified finding.

### Phase 5: Build disjoint fix groups

Group surviving findings by shared files and subsystem. Same-file findings belong to one group. Every group receives an explicit owned-file set and the sibling-owned files it must not touch.

Before dispatching, create one isolated worktree and branch per group from the verified integration SHA. Never let parallel fixers edit the main checkout or overlapping files.

### Phase 6: Fix and verify

Each fixer must reconfirm its findings, implement only confirmed fixes, add or adjust focused tests, and run the permitted local gate. A refuted claim is reported with evidence rather than "fixed."

When remote publication is authorized, push each branch once, open its PR, and drive required CI to a terminal conclusion. Treat a green run as proof only when its `head_sha` equals the exact pushed SHA and all required gates passed.

### Phase 7: Merge and build-check

Review and merge exact-SHA-green groups one at a time. Rebase remaining groups when the integration tree moves, then re-establish their proof. After the batch lands, run the integration branch's build/test gate. Repair only trivial fallout inline; route non-trivial regressions through a focused worktree.

### Phase 8: Repeat with fresh reviewers

Start a fresh Mode A exploration and lens derivation against the new integration SHA. Do not tell reviewers which round this is. Carry only the project laws plus the confirmed fixed/refuted ledger.

Stop when one condition is proved:

- a complete wave yields no new confirmed substantive findings;
- two consecutive waves add no new confirmed substantive findings;
- all remaining items are explicitly accepted or out of scope; or
- the user's declared round, time, or budget bound is reached.

Report per wave: raw candidates, confirmed, partial, refuted, fixed, merged, and residual.

## Resume / Rescue

Locate the latest run directory under `/tmp/codex-review-loop/` or use the user-provided path. Read the manifest and list completed outputs.

- Mode A: continue missing lenses in the current round, then synthesize. Do not rerun completed lenses unless the user asks or HEAD changed.
- Mode B: continue missing branches only.
- Mode C: continue from the manifest and ledger at the first incomplete phase; never rerun completed reviews or fixes unless the target SHA changed.
- If current scope differs from the manifest — branch, base, lens intent, or round target — create a new run directory. Never reuse a stale manifest.

## Boundaries

- Modes A and B do not edit code. Only Mode C may edit, and only within the explicitly authorized fix scope.
- Do not create PRs, push, merge, post comments, deploy, or trigger external actions without explicit authority for that action.
- Do not invent a replacement dispatcher script. Codex companion or native `codex exec` is the execution surface.
- Do not reference retired skills or deleted paths.
- Never require reviewers to find an issue. Fabrication is worse than a clean result.

## Final Output

Return:

- Run directory.
- Mode and target branch/HEAD.
- Rounds executed and stop condition, for Mode A.
- Branch matrix, for Mode B.
- Wave ledger, verifier verdicts, fix groups, exact SHAs, CI conclusions, and merge results for Mode C.
- Deduplicated findings with severity, evidence, lenses, and status.
- Blocked lenses/branches, if any.
- Exact verification rung reached:

Verification rungs:

- **Rung 1:** target branch/refs verified; exploration complete for Mode A.
- **Rung 2:** every Codex run completed or is explicitly blocked.
- **Rung 3:** output files checked non-empty and saved into the run directory.
- **Rung 4:** findings synthesized, deduplicated, and status-tracked across rounds or branches.
