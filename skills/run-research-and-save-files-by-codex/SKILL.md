---
name: run-research-and-save-files-by-codex
description: Use skill if you are orchestrating a multi-file research corpus where Claude designs the waves and folder tree but every web-research task is delegated to codex exec.
---

# Run Research And Save Files (Codex-Delegated Variant)

This skill builds the same kind of **multi-file evidence corpus on disk** as
`run-research-and-save-files` — per-entity packs, cross-axis comparisons,
source ledgers, optional profile pages, master summary — but with one
substitution: every web-research task inside a wave is performed by a
parallel `codex exec` subprocess instead of a Claude subagent.

Claude stays in the orchestrator seat. Claude decomposes the question,
designs the folder tree, names every output file, chooses the wave shape,
sets concurrency, picks the reasoning effort per wave, reads every codex
output between waves, and writes the master summary personally. Codex does
the actual web research and writes its answer to a file the orchestrator
specified.

## When to use this skill instead of `run-research-and-save-files`

This is a variant. Both skills produce the same corpus shape, run the
same wave model, and apply the same filesystem-as-context-channel
discipline. Pick this skill over the Claude-subagent version when **any
one** of these matches:

- The user explicitly asked for codex (*"use codex for the research"*, *"run this through codex"*, *"codex exec the per-entity work"*).
- Fan-out is large enough that parallel `codex exec` is cheaper or faster than serial Claude turns — e.g., 15+ `core` entities to research in a single wave, or 30+ cross-axis files where each is short and mechanical.
- The orchestrator wants the research subprocesses to run **detached** while it keeps Claude's context window clean for synthesis.
- The orchestrator wants effort routing as a first-class lever — running mechanical extraction at `low`, normal entity research at `medium`, and cross-axis synthesis at `high`, with the budget split made explicit.

Stay on `run-research-and-save-files` when:

| Situation | Why |
|---|---|
| Fan-out is small (≤4 entities, single sub-wave) | Codex overhead doesn't pay back; Claude subagents are simpler. |
| The user has not explicitly asked for codex AND fan-out is moderate (5-10 entities, one wave) | Default to the Claude path unless there's a reason to delegate. |
| Codex is unavailable or unauthenticated | Cannot dispatch without a working `codex --version` + auth. |
| The orchestrator wants to *interleave* synthesis and research mid-wave | Claude subagents return tool-by-tool; codex returns one final file per job. |
| The deliverable is a single chat reply / one Markdown file | Use `run-research` (not this skill, not the Claude variant). |

Anything else routes the same as `run-research-and-save-files` — read its
"When to use this skill" section. The triggers are identical; only the
**executor of the search** differs.

## The orchestrator's two-layer mental model

Claude is the **orchestrator**. Codex is the **research executor**.

| Decision | Owner | Output |
|---|---|---|
| What are the entities? What are the axes? | **Claude** | `_meta/01-charter.md`, `_meta/02-entities.md`, `_meta/03-axes.md` |
| What is the folder tree? What is the file-naming scheme? | **Claude** | `_meta/06-file-budget.md`, the directory skeleton |
| What does each wave research? Who owns which file? | **Claude** | Per-wave dispatch plan |
| What reasoning effort does each wave need? | **Claude** | Per-wave effort label (`low` / `medium` / `high`) |
| What prompt does codex receive for each task? | **Claude** writes; codex executes | `prompts/<slug>.md` per task |
| Web search, page extraction, evidence synthesis per task | **Codex** | `answers/<slug>.md` per task |
| Between-wave reading and reconciliation | **Claude** | Wave summaries, contradictions log |
| Master summary, profile pages | **Claude** | `_meta/00-master-summary.md`, `<entity>.md` profiles |

The contract is identical to Phase A's filesystem-as-context-channel
principle: codex jobs receive **only the files the orchestrator names in
the prompt**, and they write **only to the path the orchestrator
assigned**. Codex jobs in the same wave never see each other's outputs;
the orchestrator reads the wave's outputs, decides what the next wave's
prompts will reference, then dispatches the next wave.

## Filesystem-as-context-channel — same as Phase A

The load-bearing principle is unchanged. Every codex `exec` is a narrow
read-write contract against the shared corpus directory:

- The prompt names **input paths** the codex job may read (paths to files
  the orchestrator wrote earlier — charter, entity list, axis catalog,
  templates, neighboring evidence packs only if explicitly shared).
- The prompt names **the single output path** the codex job must write
  (one answer file per job: `<entity-slug>/<NN>-<axis>.md` for a
  per-entity-per-axis job; `_cross/<axis-slug>/<NN>-<topic>.md` for a
  cross-axis job).
- Write scopes between sibling codex jobs in the same wave are
  **disjoint** — no two jobs write to the same path.
- Between waves, the orchestrator personally reads every produced file
  before the next wave's prompts reference any of them.
- Skip-existing is the default retry strategy. A wave re-run never
  overwrites a `done` answer file; only `failed` and `never-started`
  re-dispatch.

The filesystem is the deliverable, the audit trail, and the context
channel — same as Phase A. Codex changes the executor of each task, not
the topology.

## Effort routing — first-class wave-level lever

Every codex spawn passes one of three reasoning-effort levels via
`-c model_reasoning_effort=<low|medium|high>`. Pick the level per wave,
not per job. Record the choice in the dispatch plan.

| Effort | When to use | Wave shapes that fit |
|---|---|---|
| **`high`** | Codex is *synthesizing* across many sub-findings, *designing* the next wave's corpus structure, or *comparing across entities* | Wave 1 entity-slate generation when the candidate pool is large or ambiguous; Wave 1 axis catalog derivation; Wave 3 per-axis cross-entity comparison; Wave 4 promoted-entity decisive research; the final master-summary precursor draft |
| **`medium`** | Normal per-entity research — full evidence pack, multiple template sections, real synthesis required | Wave 2 per-entity pack research (the canonical case); any standalone deep-research task that maps to one entity × one axis pair |
| **`low`** | Mechanical extraction with a constrained answer shape — one fact per source, structured-data extraction, source-ledger normalization | Per-source distillation (one row per URL); Reddit thread quote extraction with fixed schema; pricing-table normalization across sources; source-map maintenance |

Three concrete examples, mapped explicitly:

1. **Wave 3 per-axis cross synthesis over 12 entities for the `pricing` axis** → **`high`**. Codex reads all 12 entities' `01-pricing.md` files plus the comparison template, produces `_cross/pricing/00-overall-comparison.md` with rankings, scenario-cost models, and decision-flippers. This is comparison and synthesis across many sources; medium under-thinks it.

2. **Wave 2 per-entity pack for one vendor across ~8 axes, full evidence required** → **`medium`**. Codex reads the charter + entity-list row + product template, does its own multi-round web research, writes `<entity-slug>/00-overview.md` through `09-sources.md`. This is the canonical per-entity case.

3. **Per-source extraction wave: 40 source URLs already in `_meta/02-discovered-sources.md`, one row per source needed** → **`low`**. Codex reads one URL, returns one structured row (title, claim, evidence quality). Forty parallel low-effort jobs is dramatically cheaper than 40 medium-effort jobs and the answer shape is fixed.

4. **Wave 1 entity-slate design — 80 candidate names emerged from discovery; need a tiered list of `core` / `secondary` / `discovered-only`** → **`high`**. Codex must reason about category boundaries, identify duplicates, tier by evidence quality, surface adjacencies. Tiering across 80 candidates is structurally a synthesis task, not an extraction one.

For deeper rules and edge cases on effort selection: `references/effort-routing.md`.

## Codex exec contract

Every codex invocation passes the same flag spine; only the prompt,
output path, working directory, and reasoning effort differ per job.

```
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -m gpt-5.5 \
  -c model_reasoning_effort=<low|medium|high> \
  --json \
  -o <workdir>/answers/<slug>.md \
  -C <corpus-root> \
  < <workdir>/prompts/<slug>.md
```

The flag-by-flag rationale, model overrides, JSON event handling, and
the MCP-active `-o`-as-truth fallback are in
`references/codex-exec-contract.md`. The prompt skeleton each codex job
receives is in `references/codex-prompt-skeleton.md`. The wave-dispatch
mechanics (bounded concurrency, slug derivation, status tracking,
skip-existing, audit) are in `references/wave-dispatch.md`.

For the broader codex orchestration surface this skill draws from —
auth gating, the `--dangerously-bypass-approvals-and-sandbox` rationale,
proxy / managed-companion setups, JSON-event taxonomy, sandbox/effort
overrides via env — refer the user to the canonical codex skill,
`run-codex-2`. This skill is the research-specific lens; `run-codex-2`
is the general codex orchestration framework.

## Two framings, same skeleton

Same as Phase A. Pick once at Phase 0 and stay consistent.

| Framing | Trigger | Cross-axis folder default | Reference skills |
|---|---|---|---|
| **Domain-agnostic corpus** | *"compare / research / evaluate N entities"* in any domain | `_cross/<axis>/` | See `run-research-and-save-files` references |
| **Industry / vendor category** | *"market analysis / competitive landscape / category map / competitor research"* | `_cross-<scope>/` with archetype taxonomies | See `run-research-and-save-files` industry references |

This skill's references focus on the codex mechanics. For corpus
architecture, template authoring, profile-page patterns, vertical
taxonomies, and the worked-example walkthroughs, install
`run-research-and-save-files` alongside this skill — its references are
the same; only the executor differs. Or read its SKILL.md directly for
the corpus design phases.

## Phase model

Same eight phases as Phase A; the executor of research-doing waves
flips from Claude subagents to codex exec.

| Phase | Goal | Executor | Effort |
|---|---|---|---|
| **0 — Charter** | Decider / scale / framing | Claude personal | n/a |
| **Wave 1 — Discovery + Scope** | Enumerate entities AND derive axis catalog. Includes the deep category pre-pass for industry framing. | Codex exec, 2 parallel jobs (discovery + axes); if the candidate pool is small or already named, can be Claude personal | **`high`** for discovery; **`high`** for axes (synthesis tasks) |
| **2 — Template authoring** | Maximalist `_PRODUCT_TEMPLATE.md` + per-axis `_COMPARISON_TEMPLATE_<axis>.md` | Claude personal — templates are the comprehensiveness contract; the orchestrator must own them | n/a |
| **3 — Architecture** | Tree shape, MAX-N caps, file-count expectation, entity tiers | Claude personal | n/a |
| **Wave 2 — Per-entity packs** | Fill `<entity-slug>/` for every `core` entity (parallel codex jobs, bounded concurrency cap default 8) | Codex exec, N parallel jobs (one per entity) | **`medium`** standard; **`high`** for promoted decisive entities |
| **Wave 3 — Per-axis cross synthesis** | Compare entities along each axis (parallel codex jobs, one per axis) | Codex exec, M parallel jobs (one per axis) | **`high`** (cross-entity comparison is synthesis) |
| **Wave 4 (optional) — Profile pages OR promoted research** | Standalone `<entity-slug>.md` decision pages OR additional research packs for promoted entities | Codex exec (profile pages can also be Claude personal for stylistic control) | **`medium`** profile pages; **`high`** promoted research |
| **7 — Verification + Master summary** | Resolve contradictions; write `_meta/00-master-summary.md`; run verification gate | Claude personal — the master summary cannot be delegated | n/a |

Per-wave dispatch templates, prompt skeletons, slug rules, and the
between-wave gate procedure: `references/wave-dispatch.md`.

## Workdir layout

Every run produces this exact tree. The corpus root holds the actual
evidence (same shape as Phase A). The workdir sidecar tracks the codex
fanout state.

```
<corpus-root>/                                    (the deliverable — same as Phase A)
├── README.md
├── _meta/
│   ├── 00-master-summary.md
│   ├── 01-charter.md
│   ├── 02-entities.md
│   ├── 03-axes.md
│   ├── _PRODUCT_TEMPLATE.md          (or 04-product-template.md / 05-axis-templates.md)
│   ├── _COMPARISON_TEMPLATE_<axis>.md
│   └── 06-file-budget.md
├── <entity-slug>/
│   ├── 00-overview.md ... 09-sources.md
├── <entity-slug>.md                              (optional profile page)
└── _cross/<axis-slug>/                           (or _cross-<scope>/)
    ├── 00-overall-comparison.md
    └── 01-<scenario>.md ...

<workdir>/                                        (codex-fanout sidecar, per run)
├── run.json                                      (run_id, effort_by_wave, concurrency, started_at)
├── prompts/
│   ├── wave-2/<entity-slug>.md                   (rendered prompts per job)
│   ├── wave-3/<axis-slug>.md
│   └── ...
├── logs/
│   ├── wave-2/<entity-slug>.log                  (stderr + JSONL stream per job)
│   └── ...
├── status/
│   ├── wave-2/<entity-slug>.status               (queued | running | done | failed | skipped)
│   └── ...
└── audit/
    ├── wave-2.txt
    └── ...
```

`answers/` does not live in `<workdir>/` — codex writes directly to
the final corpus paths via `-o <corpus-root>/<entity-slug>/<NN>-<file>.md`.
That removes one copy step and makes the corpus directory the canonical
output even mid-run. Logs and status files stay in `<workdir>/` so the
corpus directory contains only the deliverable.

Slug rules, status semantics, audit gate, and the exact dispatch loop
are in `references/wave-dispatch.md`.

## Pinned defaults

| Key | Default |
|---|---|
| Trigger threshold | 5+ entities, multi-axis evaluation, folder-tree output, codex explicitly chosen OR fan-out ≥15 jobs in some wave |
| Default scale | `compact` / `standard` / `deep` / `tiered` — same labels as Phase A |
| Concurrency cap (codex jobs in parallel) | 8 per wave default; raise via env var with explicit `--i-have-measured` justification, hard ceiling 32 |
| Default model | `gpt-5.5` (override via `USE_CODEX_CODEX_MODEL`) |
| Default effort by wave | Wave 1 `high`, Wave 2 `medium`, Wave 3 `high`, Wave 4 `medium`/`high` per type; mechanical-extraction waves `low` |
| Skip-existing | On — `<answer-path>` non-empty means the job is `skipped`, never re-dispatched without explicit force |
| Per-job timeout | 25 minutes (`timeout 1500`) — hung codex processes land in `failed`, not stall the pool |
| Retry policy | 2 retries on `failed`, with a narrower prompt the second time; never auto-retry below-floor `done` answers |

## Hard rules (load-bearing)

These break the run when ignored.

1. **Claude is the orchestrator. Codex is the executor.** Claude never delegates folder design, file naming, charter authoring, template authoring, between-wave reading, or master-summary writing. Codex never decides the next wave's shape on its own.
2. **One answer file per codex job.** Path is derived deterministically from `(wave, slug)`. Two jobs writing to the same path is a hard failure.
3. **Skip-existing is the default retry strategy.** Re-running a wave never overwrites a non-empty answer file. Resume after partial failure costs zero, by construction.
4. **Concurrency is bounded.** Default cap 8 per wave; max 32. Never naked `&` fanout; never `xargs -P 0`.
5. **Every codex job receives a rendered prompt file on disk** at `<workdir>/prompts/<wave>/<slug>.md` — never inlined via shell substitution.
6. **Per-job stderr + JSONL log** → `<workdir>/logs/<wave>/<slug>.log`. Never piped into the answer file.
7. **An empty (0-byte) or whitespace-only answer file is `failed`, not `done`.** Atomic rename `.tmp` → final after codex exit. Without atomic rename, a crashed codex leaves a partial file that future runs incorrectly skip.
8. **Between-wave reading is non-delegable.** Before dispatching the next wave, Claude reads every produced file personally.
9. **Effort is chosen per wave, not per job.** Mixing effort levels inside a single wave is allowed only when the wave is genuinely heterogeneous (rare) and the dispatch plan records the per-job override explicitly.
10. **Templates first, codex jobs second.** Phase 2 (template authoring) is orchestrator-personal. Wave 2 codex jobs receive the template in their input paths; without it, codex produces non-comparable packs.
11. **No single-report output.** This skill produces a multi-file corpus. If the user wants a single chat reply, redirect to `run-research`.
12. **Two-level orchestration only.** Codex jobs never spawn their own codex jobs through this skill.

If any rule is violated, the run is no longer idempotent and the rest of
this skill stops applying.

## Operator preflight

Before the first wave dispatches, verify:

1. `codex --version` succeeds. Confirm the CLI is on PATH and a recent
   build (this skill assumes `codex-cli 0.130.0` or later).
2. **Auth gate** — `codex login status` (or proxy / managed-companion
   equivalent). If `codex login status` says "Not logged in" but the
   machine uses a proxy or managed setup, set
   `USE_CODEX_SKIP_CODEX_AUTH=1` and run a tiny smoke test before
   dispatching the real fleet. The smoke recipe lives in
   `run-codex-2`'s preflight; replicate it here before any wave.
3. The corpus root path is chosen and writable.
4. The workdir sidecar path is chosen (default `./corpus-runs/<run_id>/`).
5. The effort plan is recorded — wave-by-wave, `low`/`medium`/`high`.

Auth-gate failure surfaces only after the runner spawns codex; that
error doesn't appear in the dispatcher envelope. Skipping the smoke
test is the canonical way to waste a full wave's budget on entries
that all fail at the runner-spawn auth handshake.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Claude searches the web personally | Defeats the codex-delegation point; pollutes Claude's context | Dispatch a codex job. Claude orchestrates, codex executes. |
| Effort routing not chosen — every wave gets `medium` | Wastes budget on extraction waves; under-thinks synthesis waves | Pick per-wave effort up front; record in `run.json` |
| Concurrency raised without measurement | Rate-limit cascade, tier-shared starvation | Default 8 per wave; raise only with `--i-have-measured "<reason>"` |
| Codex jobs in same wave write to overlapping paths | Last writer wins; evidence silently overwritten | Disjoint write scopes; one job per path |
| Naked `&` fanout / `xargs -P 0` | Unbounded fan-out exhausts API quotas and OS file handles | Bounded worker pool; cap default 8, max 32 |
| Inlining the input via shell substitution | Quoting bugs, shell injection across jobs | Render prompt in-process, write to `prompts/<wave>/<slug>.md`, redirect stdin |
| Reading `logs/*.log` as source of truth | The answer file is canonical; logs are forensics | Audit `answers/`; consult `logs/` only on failure |
| Overwriting `done` answer in place | Defeats skip-existing; double-spends codex budget | Archive to `answers/.prev/<slug>.md.<ts>`, then re-dispatch |
| No `timeout` wrapper | One hung codex process stalls the pool indefinitely | `timeout 1500` on every spawn; hung jobs flip to `failed` |
| Mixing `--full-auto` or `-s read-only`/`-s workspace-write` | Sandbox modes interact badly with web research and writes | Use `--dangerously-bypass-approvals-and-sandbox` per the maintainer's contract |
| Skipping the template-coverage audit | "Looks done" masks missing sections | Run the verification gate; template-coverage audit is non-negotiable |
| Codex reasoning effort `high` everywhere | Burns budget on tasks that don't need it | Effort routing per wave; `high` only for synthesis-shaped waves |
| Single-output thinking ("write me a report") | Loses the multi-file corpus contract | Multi-file corpus is the deliverable; route to `run-research` if user wants a single report |

## Self-correction triggers

If you notice yourself doing any of the following — **stop**:

- **Claude searching the web itself** instead of dispatching codex → STOP. Dispatch.
- **Codex dispatched without a rendered prompt file on disk** → STOP. Render to `prompts/<wave>/<slug>.md` first; idempotency depends on the stable artifact.
- **More than 8 codex jobs running concurrently without an `--i-have-measured` justification** → STOP. Cap.
- **Two codex jobs in the same wave writing to the same `-o` path** → STOP. Disjoint scopes only.
- **An empty answer file marked `done`** → STOP. Empty = `failed`. Re-dispatch (after fix), do not paper over.
- **Templates skipped, Wave 2 dispatched directly** → STOP. Templates are the comprehensiveness contract; without them codex packs aren't comparable.
- **Effort routing not chosen** — every wave at `medium` by accident → STOP. Pick per-wave effort up front; `high` for synthesis-shaped waves, `low` for mechanical extraction.
- **Reading codex `--json` events to infer "done"** — they're a stream, not a state machine — STOP. Trust the answer file's non-empty status and the explicit `status/<slug>.status` write.
- **Skipping the between-wave read** ("the answer files look fine, dispatch next wave") → STOP. The orchestrator reads every produced file personally before dispatching the next wave.
- **Skipping the completion gate** → STOP. Run the verification commands; template-coverage audit, link check, source-ledger presence are non-negotiable.

## Output contract

Surface these artifacts at the phase that produces them:

1. **Phase 0** — scope + scale + framing + the **effort plan** (per-wave `low`/`medium`/`high`).
2. **Wave 1** — entity list + axis catalog + category-understanding note.
3. **Phase 2** — resolved category list + maximalist product template + per-axis comparison templates.
4. **Phase 3** — tree shape + file-count expectation + the dispatch map for Wave 2 (which slug → which entity → which effort).
5. **Wave 2** — per-entity codex dispatch envelope (run_id, wave, slug list, concurrency cap, effort), then progress notes as jobs complete. Audit summary at wave end.
6. **Wave 3** — cross-axis codex dispatch envelope + ranking summary after the wave's audit gate passes.
7. **Wave 4 (optional)** — profile-page index OR promoted-entity packs.
8. **Phase 7** — completion statement (corpus path, files, entry points, gaps, verification, template coverage, total codex jobs and their terminal states).

## Reference routing

Load only the reference whose phase is active.

| Reference | Read when |
|---|---|
| `references/codex-exec-contract.md` | Any phase that dispatches codex — flag spine, JSON event handling, MCP-active fallback, model and effort overrides |
| `references/effort-routing.md` | Phase 0 (designing the effort plan); any wave-transition (validating the chosen effort) |
| `references/codex-prompt-skeleton.md` | Wave 1, 2, 3, 4 — the 7-section prompt skeleton every codex job receives, with input-paths / output-path / run-research integration block |
| `references/wave-dispatch.md` | Wave 1, 2, 3, 4 — bounded-concurrency dispatch loop, slug rules, skip-existing, status tracking, audit gate, retry policy |
| `references/orchestrator-cookbook.md` | Between waves — when to read outputs, when to escalate effort, when to fall back to a Claude subagent, when to stop |

For the corpus design phases (charter, template authoring, architecture,
verification, profile pages, vertical taxonomies, worked examples), use
the references inside `run-research-and-save-files`. This skill is the
research-execution lens; the corpus design lens lives in the Claude
variant.

## Quick start

The first ten minutes of any session:

1. **Preflight** — `codex --version`, auth gate, smoke test if proxy/managed (see `references/codex-exec-contract.md`).
2. **Phase 0** — write `_meta/01-charter.md` and the **effort plan** (per-wave `low`/`medium`/`high`). Show the user the effort plan before any wave dispatches.
3. **Wave 1** — render 2 prompts (`prompts/wave-1/discovery.md`, `prompts/wave-1/axes.md`), dispatch 2 codex jobs at `high` effort in parallel. Wait. Read both outputs personally.
4. **Phase 2** — Claude writes the maximalist templates personally. Show them to the user before Wave 2.
5. **Phase 3** — finalize architecture; record the Wave 2 dispatch map (slug → entity → effort).

After that: Wave 2 (per-entity, possibly multiple sub-waves) → Wave 3
(per-axis cross synthesis) → optional Wave 4 → Phase 7 verification +
master summary (Claude-personal). At every wave boundary, Claude reads
every produced file before dispatching the next wave.

If anything is unclear, the question is almost always upstream: read
`references/orchestrator-cookbook.md` and recheck the decomposition,
folder tree, or effort plan before dispatching more codex jobs.

## Bottom line

Same wave-dispatched, filesystem-as-context-channel corpus as
`run-research-and-save-files`. The difference is that every web-research
job is a parallel `codex exec` subprocess; Claude orchestrates without
ever calling a web tool itself. The deliverable is the corpus directory;
the workdir sidecar is the audit trail; the effort plan is the budget
contract; the orchestrator's reads between waves are the gates.
