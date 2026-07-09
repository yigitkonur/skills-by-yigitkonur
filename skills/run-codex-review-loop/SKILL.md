---
name: run-codex-review-loop
description: Use skill if you are running Codex review loops across current branches, multiple lenses, comparisons, convergence rounds, or saved review runs.
---

# run-codex-review-loop

Run repeatable Codex review passes without relying on the retired `run-codex-2` dispatcher. This skill owns the loop around native Codex review execution; `run-review` in the main pack owns one-off review routing, PR handoff, and feedback triage.

Two modes:

- **Mode A — Multi-lens checkout audit (default):** review the **current active checkout branch** (whatever `git branch --show-current` reports — often `main`) through many independent review lenses, in rounds, until findings converge.
- **Mode B — Multi-branch comparison:** the original branch loop — run review across two or more named branches and compare findings.

Pick Mode B only when the user names two or more branches. Everything else — "review the whole project", "full audit", "multiple lenses", "review main", "review the current branch" — is Mode A.

## Use This When

- The user asks for a complete, multi-lens, whole-project Codex review of the current checkout branch.
- The user asks to keep reviewing until issues converge or the branch is clean enough.
- The user names two or more branches and asks for Codex review, convergence, close-out, or comparison.
- A prior review loop has saved outputs and the user asks to resume or rescue it.

Do not use this for:

- A single small PR, commit, or uncommitted diff. Use `run-review` Mode D.
- Opening a PR or writing a self-review body. Use `run-review` Mode B.
- Triaging human or bot comments already posted on a PR. Use `run-review` Mode C.
- Generic multi-agent implementation fan-out. This skill is review-only.

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
- Do not treat a Codex report as verified truth. Before final synthesis, spot-check enough file:line evidence to reject obvious hallucinations or stale paths.

### Phase 4: Loop until convergence

Run up to **10 rounds**. Between rounds, fixes may be applied outside this skill by the main agent or user; this skill itself remains review-only.

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

## Resume / Rescue

Locate the latest run directory under `/tmp/codex-review-loop/` or use the user-provided path. Read the manifest and list completed outputs.

- Mode A: continue missing lenses in the current round, then synthesize. Do not rerun completed lenses unless the user asks or HEAD changed.
- Mode B: continue missing branches only.
- If current scope differs from the manifest — branch, base, lens intent, or round target — create a new run directory. Never reuse a stale manifest.

## Boundaries

- Do not edit code. This is a review loop, not a fix loop.
- Do not create PRs, push, post comments, deploy, or trigger external actions unless the user explicitly asks for that separate action.
- Do not invent a replacement dispatcher script. Codex companion or native `codex exec` is the execution surface.
- Do not reference retired skills or deleted paths.

## Final Output

Return:

- Run directory.
- Mode and target branch/HEAD.
- Rounds executed and stop condition, for Mode A.
- Branch matrix, for Mode B.
- Deduplicated findings with severity, evidence, lenses, and status.
- Blocked lenses/branches, if any.
- Exact verification rung reached:

Verification rungs:

- **Rung 1:** target branch/refs verified; exploration complete for Mode A.
- **Rung 2:** every Codex run completed or is explicitly blocked.
- **Rung 3:** output files checked non-empty and saved into the run directory.
- **Rung 4:** findings synthesized, deduplicated, and status-tracked across rounds or branches.
