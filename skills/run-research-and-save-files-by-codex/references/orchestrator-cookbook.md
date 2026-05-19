# Orchestrator Cookbook

Claude's playbook for the codex-delegated variant. When to read which
files, when to dispatch the next wave, when to escalate effort, when
to fall back to a Claude subagent, when to stop and report.

This is the "what Claude does between codex jobs" guide. The codex
mechanics live in `codex-exec-contract.md`; the dispatch loop lives in
`wave-dispatch.md`; the effort policy lives in `effort-routing.md`.
This file is the meta-loop.

## Claude's role per phase

| Phase | What Claude does (no codex) | What Claude triggers (codex dispatch) |
|---|---|---|
| 0 — Charter | Read user request; ask up to 3 clarifying questions; write `_meta/01-charter.md`; pick framing; draft the effort plan | Nothing |
| 1 — Discovery + Scope | Render 2 prompts (discovery + axes) to `<workdir>/prompts/wave-1/`; verify input/output paths; pick `high` effort | Dispatch 2 codex jobs in parallel |
| Between 1 and 2 | Read `_meta/02-entities.md` + `_meta/03-axes.md`; reconcile tiers; surface to user; iterate if user adjusts | Nothing |
| 2 — Template authoring | Write `_meta/_PRODUCT_TEMPLATE.md` and per-axis `_COMPARISON_TEMPLATE_<axis>.md` personally; show to user | Nothing |
| 3 — Architecture | Plan tree shape, MAX-N caps, file-count expectation; write `_meta/06-file-budget.md`; build the Wave 2 dispatch plan (slug → entity → output paths → effort) | Optionally dispatch the `init-corpus.sh` script (or run it personally) to scaffold the corpus root |
| Wave 2 — Per-entity packs | Render N prompts; verify each prompt's input paths are correct and disjoint; pick effort per job (default medium; overrides per dispatch plan) | Dispatch N codex jobs (bounded concurrency 8 default) |
| Between Wave 2 and Wave 3 | Read every produced entity pack; reconcile contradictions; update `_meta/02-entities.md` if new tiers emerge; revise effort plan for Wave 3 if needed | Nothing |
| Wave 3 — Per-axis cross | Render M prompts (one per axis); each prompt lists the N entity files as input paths; pick `high` effort | Dispatch M codex jobs |
| Between Wave 3 and Wave 4 | Read every cross file; surface decision-flippers; identify entities worth promoting for additional research | Nothing |
| Wave 4 (optional) | Render profile-page prompts OR promoted-research prompts | Dispatch codex jobs |
| 7 — Verification + Master summary | Read every file in the corpus personally; run verification commands; write `_meta/00-master-summary.md`; produce completion statement | Nothing — the master summary is non-delegable |

## When to read which file

The reading loop after every wave is the load-bearing orchestrator
behavior. The minimum reads:

- **After Wave 1:** `_meta/02-entities.md` AND `_meta/03-axes.md` in full. These are the inputs to every downstream wave; sloppy reading here cascades.
- **After Wave 2:** every `<entity-slug>/` folder produced — overview + every populated section + sources. Yes, every one. Skipping a pack means the next wave's cross-axis comparison reads a corpus the orchestrator hasn't validated.
- **After Wave 3:** every `_cross/<axis>/00-overall-comparison.md` AND the granular comparison files. The orchestrator must be able to state which entity wins which scenario before Wave 4 dispatches.
- **After Wave 4:** every profile page (if produced) OR every promoted-research pack.
- **Phase 7:** every file in the corpus, including `_meta/`. The master summary is the orchestrator's synthesis of all of it.

If the corpus is too large for Claude to read in one pass, split the
reading across multiple tool turns but never skip files. The reading
budget is real; the temptation to "spot-check 3 random files" is the
single largest source of corpus integration failure.

## When to escalate effort to `high`

After a wave's audit, the orchestrator may bump the next wave's effort
from `medium` to `high`. Triggers:

- **A `core` entity's pack reveals decision-flipping uncertainty** — vendor claims contradicted by Reddit; pricing scenarios where the user's use case is unclear. Wave 3 for the affected axes should be `high` even if the effort plan said `medium`.
- **A cross-axis comparison reveals two entities are functionally interchangeable** but the user needs to pick one. Dispatch a `high`-effort Wave 4 promoted-research pair for those two entities.
- **The user's question has shifted mid-session** (rare but happens). Re-derive the effort plan from the new scope; do not paper over the old plan.

Record every escalation in `_meta/effort-plan.md` with the trigger
that motivated it.

## When to fall back to a Claude subagent (instead of codex)

This skill is "codex by default" but the orchestrator may swap in a
Claude subagent for one job when:

- **The job is decision-flipping and codex has produced contradictory outputs twice.** A Claude subagent's interactive multi-round behavior sometimes produces a clearer synthesis than codex's one-shot.
- **The job needs to interleave research with multiple tool turns.** Codex returns one final file; Claude subagents can do "search, read, ask the user, search again, finalize" — when that loop is needed, a Claude subagent is the right shape.
- **The job is genuinely small** (5-10 minutes of research). Codex overhead doesn't pay back; just run a Claude subagent.

Record the fallback in the dispatch plan: `slug → executor (codex|claude-subagent) → reason`. The fallback is not a defeat — it's a recognition that codex and Claude subagents are complementary.

If the fallback rate exceeds 20% of jobs in a wave, the wave is
misshaped — reconsider whether this skill is the right choice vs.
`run-research-and-save-files` (which is Claude-subagent-by-default).

## When to stop and ask the user

Claude stops mid-session and surfaces a question when:

- **The discovered entity list contradicts the charter.** E.g., charter said "compare 8 cloud-browser vendors", Wave 1 surfaced 23 viable candidates plus 5 adjacent categories. Stop; surface; ask the user to refine scope.
- **Template authoring (Phase 2) reveals that the category has no shared axes.** I.e., the entities don't actually compete head-to-head. Stop; surface; recommend split-into-two-corpora or pivot to `run-research`.
- **Wave 2's audit shows ≥40% of jobs failed.** A high failure rate signals a systemic issue (auth, rate-limit, prompt malformed). Stop; surface; do not auto-retry the whole wave at once.
- **The master summary cannot be written without making a claim the corpus doesn't support.** Stop; surface; identify the missing evidence; recommend a Wave 4 promoted-research dispatch or accept the gap and write the summary with the gap named.

The orchestrator does not pause for mid-wave approval. Once a wave is
running, let it finish; only stop on the wave boundary.

## When to declare the corpus done

Phase 7's completion gate has three artifacts:

1. **Template-coverage audit clean.** Every required template section
   is addressed in every `core` pack (content OR insufficient-evidence
   entry).
2. **Link-integrity check clean.** Every local Markdown link in the
   corpus resolves.
3. **Source-ledger presence.** Every `core` entity has a populated
   `09-sources.md` (or `09-sources/`); every cross-axis folder has a
   `09-sources/` if it cites web sources.

After all three pass, write `_meta/00-master-summary.md`:

- Corpus path
- Total files, total `core` entities
- Top entry points (the 3-5 files a buyer should read first)
- Critical findings (decision-flippers, contradictions, surprises)
- Unresolved gaps (named explicitly; never "everything looks fine")
- Verification results

Then the completion statement to the user.

## Failure modes specific to the orchestrator

| Failure | Symptom | Fix |
|---|---|---|
| Orchestrator dispatches Wave 2 before reading Wave 1 outputs | Wave 2 input paths reference files the orchestrator hasn't validated; corpus is unintegrated | Hard rule: read Wave 1 outputs in full before rendering Wave 2 prompts |
| Orchestrator picks `medium` for every wave silently | Synthesis waves under-think; cost-effective extraction waves over-spend | Phase 0 must produce an explicit effort plan; show it to the user |
| Orchestrator delegates the master summary to a codex job | Master summary becomes a stitched concatenation of per-wave summaries | Master summary is Claude-personal; no exceptions |
| Orchestrator runs codex with overlapping `-o` paths within a wave | Last writer wins; evidence silently overwritten | Validate output-path disjointness before dispatching the wave |
| Orchestrator skips the audit gate ("looks done") | Below-floor entries and template-coverage gaps mask as success | Run the audit; surface below-floor entries; never auto-declare done |
| Orchestrator over-retries failed jobs | Same failure repeats; budget burns | 2 retries max; on 3rd failure, log the gap in `_meta/open-gaps.md` |

## Cross-skill coordination

This skill plays well with:

- `run-research-and-save-files` — the same corpus shape executed by Claude subagents. Switch when fan-out shrinks or the user pivots away from codex.
- `run-codex-2` — the broader codex orchestration framework. Refer the user to it when they need batch/exec/review/single/rescue modes outside the corpus-research context.
- `run-research` — the single-question companion. Pop down to it when the user pivots from "build a corpus" to "answer one specific question I had about an entity."
- `review-self` and `review-pr` — for the rare case where the corpus produces follow-up code work. Out of scope for this skill.

The triggers for switching between this skill and Claude-variant
`run-research-and-save-files` are listed in this skill's `SKILL.md`
under "When to use this skill instead". Re-read those triggers if the
session shifts mid-run.

## The orchestrator's own preflight

Before dispatching the first wave, Claude personally verifies:

1. `codex --version` succeeds. Surface the version to the user.
2. The auth-gate smoke (see `codex-exec-contract.md`) returns "auth OK" if running through a proxy / managed setup.
3. The corpus root path is writable and either empty or contains only the optional `init-corpus.sh` scaffold.
4. The workdir sidecar path is chosen and the `prompts/`, `logs/`, `status/`, `audit/` subdirectories exist (or are auto-created on first dispatch).
5. The effort plan is recorded.
6. The user has approved the effort plan and the per-wave job count.

Skipping any of these turns the first wave into a debugging session.
Five minutes of preflight saves a wave's worth of API budget.
