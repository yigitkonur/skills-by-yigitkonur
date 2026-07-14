---
name: run-deep-research
description: "Use if running deep multi-file research over 5+ entities or a market — wave-dispatched corpus."
---

# Run Deep Research

This skill produces a **multi-file evidence corpus on disk**, never a single chat reply.
Per-entity evidence packs, cross-axis comparison rollups, source ledgers, optional
profile pages, and a master summary — all written into a navigable folder tree the
user can read, edit, link from, and re-enter later. The filesystem is the deliverable.

The orchestrator does not search the web personally. The orchestrator decomposes,
architects the folder tree, dispatches research in waves, gates between waves, and
synthesizes the final master summary. The actual web research runs on a **chosen
executor — Claude subagents or `codex exec`** — selected up front at intake (see
**Executor — Claude subagents or codex**). The orchestrator role is identical either
way: each research task invokes the `run-research` discipline (3-tool research
surface, `## Not found` harvesting, citation rules, parallel scope dispatch). The
filesystem is the only context channel between waves — research tasks do not see each
other's outputs except through files the orchestrator names in the next brief.

## When to use this skill

Trigger on any of these phrasings:

- *"research / compare / evaluate 5+ tools / vendors / projects / frameworks"*
- *"market analysis of [category] / competitive landscape / category map / competitor research"*
- *"build a research corpus / evidence pack / decision corpus on [category]"*
- *"deep research on [SaaS / OSS / dev-infra / data-API / regulated category]"* with per-vendor pages
- *"give me pricing + capability + integration + security + audience matrices across [vendors]"*
- *"navigable folder of product pages, comparison rollups, source ledgers, and profile pages"*
- *"every numeric / versioned / priced claim must cite a verbatim source quote"*
- *"the deliverable is a folder tree the team can navigate"*, not a chat reply
- *"audit / shortlist [population]"* against a fixed axis catalog (cost, performance, fit, risk, longevity)
- The user names 5+ vendors / projects upfront and asks for a structured side-by-side
- *"use codex for the research"*, *"run this through codex exec"* — same corpus, codex executor (an intake choice, not a different skill)

Do NOT use when:

| Situation | Use instead |
|---|---|
| One technical question, single answer | `run-research` |
| 1-4 entities, one polished single-page summary, no folder structure | `run-research` |
| Finding or shortlisting GitHub repos as the deliverable | `run-github-scout` |
| Many small factual web questions, one parseable answer file each | `search-it-bulk-by-codex` |
| Codebase analysis, code review, or implementation work | not this skill |
| Polished single deliverable (HTML battlecard, slide deck) | downstream skills polish |

The fence: `run-research` answers **one question** and returns **one synthesis**;
this skill answers **N questions across N entities** and returns a **multi-file
corpus**. If the deliverable is a folder, you are in this skill. If it's a chat
reply or a single Markdown file, you are in `run-research`.

## Intake — always ask first (AskUserQuestion)

Before any decomposition, template authoring, or dispatch, run **one batched
`AskUserQuestion` call** to lock the run's shape. This is mandatory — never start a
heavy pass on assumptions, and never burn fan-out budget before the user has
confirmed the executor. Batch the discrete decisions into a single call so the user
answers once; make the recommended default the first option of each:

1. **Executor** — Claude subagents (default) · `codex exec` (cheaper/faster large fan-out) · decide by fan-out size.
2. **Scale** — compact (5-10) · standard (10-40) · deep (40-100) · tiered (100+).
3. **Framing** — domain-agnostic corpus · industry / vendor category.
4. **Scope** — discover entities vs. use the user's named list; confirm the `<topic-slug>/` output folder and whether profile pages are wanted.

Capture the **decider** and **use case** from the conversation (or the question's
free-text notes) — these anchor `_meta/01-charter.md`; without them "good" and "bad"
are undefined. If `AskUserQuestion` is unavailable (non-interactive run), fall back to
the stated defaults and record the assumption in the charter. Full question wording,
option sets, recommended defaults, and the headless fallback: `references/intake.md`.

The intake answers seed Phase 0: executor + scale + framing go straight into the
charter; the codex executor additionally requires a per-wave effort plan (§Executor).

## The orchestrator's mental model

Every deep-research question reduces to one shape: **a population of entities,
evaluated across a set of axes, producing per-entity evidence packs + per-axis
cross-entity comparisons + a master decision artifact.** Strip away the domain
and that shape remains.

The four invariants in every session:

- **A finite set of entities.** The unit researched one folder per (products,
  candidates, projects, providers, papers, plans). The orchestrator's first job
  is to enumerate and tier them.
- **A finite set of evaluation axes.** Dimensions the decider weighs (cost,
  performance, fit, risk, longevity, compliance). Each has a native primitive
  (currency-per-period, milliseconds, score). Without native primitives,
  comparison is incoherent.
- **A decider with a use case.** Without this, "good" and "bad" are undefined.
- **A decision artifact.** Without this, the research has no closing condition.

The orchestrator's four jobs in order:

1. **Decompose** — what are the entities, what are the axes? See `references/thinking.md`. Without rigorous decomposition, no amount of evidence saves the corpus.
2. **Structure** — design the folder tree, file-naming scheme, MAX-N ceilings before any research dispatches. See `references/filesystem.md`.
3. **Dispatch** — write briefs that bind each research task to its specific scope, the run-research discipline, and the exact file paths it owns. See `references/subagent-briefs.md` (Claude) or `references/codex/codex-prompt-skeleton.md` (codex).
4. **Synthesize** — read every output file personally; resolve contradictions; write the master summary. See `references/synthesis.md`.

## Filesystem as context channel

This is the load-bearing principle of every wave-based orchestrated session.

- Each research task receives **only the files the orchestrator names in its brief**.
- Each research task writes **only to the folder the orchestrator assigned**.
- The orchestrator reads outputs **after each wave** and decides what the next wave reads.
- No research task sees another's working notes, search history, or mid-stream outputs — only the persisted files the orchestrator chooses to share.

This is what makes the wave model scale. With more than two or three research tasks
in flight, in-memory context collapses. With files, the wave model composes cleanly
to dozens of entities and multiple sub-waves. Treat `<corpus-root>/` as the shared
blackboard; treat each research task's prompt as a narrow read-write contract against
that blackboard. (The contract is identical whether the task is a Claude subagent or
a `codex exec` job — only the executor differs.)

Operational consequences:

- Briefs name **input paths** (what the task reads) and **output paths**
  (what the task writes), explicitly and exhaustively.
- Write scopes between sibling tasks in the same wave are **disjoint** — no
  two tasks own the same folder.
- Between waves, the orchestrator **reads every file produced**. This is not
  delegable.
- If a task needs evidence from another task's output, that evidence is
  passed through a file the orchestrator surfaces in the next wave's brief —
  never through "ask the other agent."

## Two framings, same skeleton

The methodology is domain-agnostic. The output structure has two named
defaults — pick once at Phase 0 and stay consistent. Both produce the same kind
of multi-file evidence corpus; the difference is vocabulary and which reference
files are loaded.

| Framing | Trigger | Default output flavor | Load first |
|---|---|---|---|
| **Domain-agnostic corpus** | *"compare / research / evaluate N entities"* in any domain (OSS projects, models, hardware, papers, candidates, locations, regulations, frameworks) | `_cross/<axis>/` rollups; `_meta/04-product-template.md` + `_meta/05-axis-templates.md` | `references/thinking.md`, `references/filesystem.md`, `references/orchestration.md`, `references/templates.md` |
| **Industry / vendor category** | *"market analysis / competitive landscape / category map / competitor research / vendor evaluation"* | `_cross-<scope>/` rollups; `_meta/_PRODUCT_TEMPLATE.md` + `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per criterion; profile pages by default | `references/industry/category-taxonomies.md`, `references/industry/template-authoring.md` (keystone), `references/industry/industry-architecture.md`, `references/industry/discovery.md`, `references/industry/evidence-and-synthesis.md`, `references/industry/mission-briefs.md`, `references/industry/profile-pages.md`, `references/industry/research-powerpack-and-explore.md`, `references/industry/worked-example-cloud-browsers.md` |

Framing is resolved at intake. If the user's framing is genuinely ambiguous (e.g.,
"research 8 LLM providers" — both fit), the intake's framing question settles it;
do not switch mid-session. Switching framings mid-run forces a corpus rewrite.

## Executor — Claude subagents or codex

Research-doing waves run on one of two executors, chosen once at intake and recorded
in the charter. Corpus shape, wave model, templates, and the filesystem-as-context
discipline are identical — only *who performs each web search* differs.

| | Claude subagents (default) | codex exec |
|---|---|---|
| Each research task is | a Claude subagent invoking `run-research` | a parallel `codex exec` subprocess writing one answer file |
| Best when | fan-out ≤ ~10, interleaved multi-turn research, stylistic control | large fan-out (≥15 jobs/wave), detached burning, cheap parallel credits, explicit effort routing |
| Orchestrator dispatches | subagent briefs (`references/subagent-briefs.md`) | one rendered prompt file per job + a bounded-concurrency loop |
| Effort lever | n/a | per-wave `low`/`medium`/`high` via `-c model_reasoning_effort=` |

What never changes between executors: the orchestrator owns decomposition, folder
tree, file naming, template authoring, between-wave reads, and the master summary.
Phases 0/2/3/7 and the synthesis waves (Wave 3, profile-page Wave 4) are
**orchestrator-personal** regardless of executor.

When codex is chosen, its load-bearing mechanics — exec flag spine, idempotent
skip-existing, one answer file per job, bounded concurrency (8/wave, 32 ceiling),
rendered prompt files on disk, per-wave effort routing, and the preflight auth gate —
live in `references/codex/`:

| Codex reference | Read when |
|---|---|
| `references/codex/codex-exec-contract.md` | Any codex dispatch — flag spine, JSON events, model/effort overrides, MCP-active fallback |
| `references/codex/effort-routing.md` | Phase 0 — designing the per-wave `low`/`medium`/`high` effort plan |
| `references/codex/codex-prompt-skeleton.md` | Waves 1-4 — the 7-section prompt each codex job receives, with input-paths / output-path / run-research block |
| `references/codex/wave-dispatch.md` | Waves 1-4 — bounded-concurrency loop, slug rules, skip-existing, status tracking, audit gate, retry |
| `references/codex/orchestrator-cookbook.md` | Between waves — when to read, escalate effort, fall back to a Claude subagent, declare done |

## Pinned defaults

| Key | Default |
|---|---|
| Trigger threshold | 5+ entities, multi-axis evaluation, folder-tree output |
| Executor | Claude subagents (default); `codex exec` when chosen at intake, or when fan-out ≥15 jobs in some wave |
| Default scale | `compact` 5-10 entities, ~80-200 files; `standard` 10-40 entities, ~150-500 files; `deep` 40-100 entities, ~500-2000 files; `tiered` 100+ entities, full packs for top tier only |
| Hard wave cap | 8 research tasks per wave for domain-agnostic framing; 20 per wave for industry framing |
| Codex concurrency | 8 jobs/wave default; hard ceiling 32, raise only with measured justification |
| Codex model / effort | `gpt-5.5`; per-wave `low`/`medium`/`high` — Wave 1 `high`, Wave 2 `medium`, Wave 3 `high`. See `references/codex/effort-routing.md` |
| Recommended wave size | 6-8 tasks when integration quality or context pressure matters |
| Research-task retry policy | 2 retries max per failed task, with a narrower prompt each time (codex: skip-existing, never overwrite a `done` answer) |
| Profile pages | Default yes for `core` tier at `standard` scale or larger (industry framing); optional for domain-agnostic |
| File count policy | Bounded by template-section-count × entity-count + cross-axis files. No fixed numeric cap; templates are the boundary. |
| Source ledger policy | Per-entity ledgers in `<entity-slug>/09-sources/` (or `09-sources.md` for compact corpora); cross-corpus ledgers in `_cross-<scope>/09-sources/` |

## Phase model

Eight phases, each with an artifact gate. Skip a phase only when its artifact
is not needed for the user's stated outcome — and state the reason.

| Phase | Goal | Artifact gate |
|---|---|---|
| **0 — Charter** | Apply intake answers; clarify decider, scale, archetype; pick framing + executor | `_meta/01-charter.md` scope statement + corpus scale + framing label + executor (+ effort plan if codex) |
| **Wave 1 — Discovery + Scope** | Enumerate entities AND derive axis catalog (parallel, 2 tasks). Includes the **deep category pre-pass** (industry) — buyer axes, native pricing units, practitioner channels, regulatory regimes. | `_meta/02-entities.md` (or `discovered-entities.md`) + `_meta/03-axes.md` + category-understanding note |
| **2 — Template authoring** | Write maximalist `_meta/04-product-template.md` + `_meta/05-axis-templates.md` (domain-agnostic) OR `_meta/_PRODUCT_TEMPLATE.md` + per-criterion `_meta/_COMPARISON_TEMPLATE_<criterion>.md` (industry). Templates set the comprehensiveness boundary. | Templates locked AND shown to the user |
| **3 — Architecture** | Plan tree shape, MAX-N caps, entity tiers, file-count expectation derived from templates. Optionally scaffold via `scripts/init-corpus.sh`. | `_meta/06-file-budget.md` / `_meta/file-budget.md` |
| **Wave 2 — Per-entity packs** | Fill `<entity-slug>/` for every `core` entity (parallel, ≤8 per sub-wave domain-agnostic; ≤20 per sub-wave industry). Each task owns one folder; write scopes disjoint. Each invokes run-research. | Populated `<entity-slug>/` folders; every template section addressed (content OR explicit "insufficient evidence" entry naming the data gap) |
| **Wave 3 — Per-axis cross synthesis** | Compare entities along each axis. LOCAL-ONLY (no web tools). Each task owns one cross folder. | Populated `_cross/<axis-slug>/` or `_cross-<scope>/` folders with ranking + matrix + decision-flippers |
| **Wave 4 (optional) — Profile pages OR promoted research** | Standalone `<entity-slug>.md` decision pages at corpus root (LOCAL-ONLY) OR additional research packs for promoted entities (web-capable, invokes run-research) | Profile pages OR new entity packs |
| **7 — Verification + Master summary** | Orchestrator personally reads every file. Resolves contradictions. Writes `_meta/00-master-summary.md`. Runs verification gate. | `_meta/00-master-summary.md` + verification log; template-coverage audit passes |

Research-doing waves (1, 2, optional 4-promoted) run on the chosen executor — Claude
subagents invoking run-research, or codex exec jobs. Wave 3 and profile-page Wave 4
are **LOCAL-ONLY** synthesis — read files, no web tools. Phases 0, 2, 3, 7 are
**orchestrator-personal** — no delegation, regardless of executor.

Full wave choreography, brief structure, between-wave gates: `references/orchestration.md`
(Claude) and `references/codex/wave-dispatch.md` (codex).

## Tool steering at a glance

The orchestrator chooses the tool category for each use case in the brief; the
research task executes it (a Claude run-research session, or a codex exec job).

| Use case | Wave | Tool dispatch |
|---|---|---|
| Find entities | 1A / Discovery | Parallel `web-search` keyword probes (open web + explicit `site:reddit.com/r/.../comments` probes) → optional `scrape-link` on category indexes |
| Map axes / deep category pre-pass | 1B / Discovery | `web-search` to surface candidate analyses → `scrape-link` with extract = "decision axes / native pricing units / practitioner channels" on 2-3 authoritative analyses |
| Per-entity overview | 2 | `get-research-consultancy` per entity → parallel `web-search` (open web + reddit-scoped keyword probes) → `scrape-link` on docs and Reddit threads with a facet-rich `extract` |
| Per-entity sentiment | 2 | `scrape-link` on Reddit thread permalinks with a quote-preserving `extract` (Reddit API fetches the full threaded post + comments; scrape-link extracts sentiment/quotes from it) |
| Cross-entity synthesis | 3 | LOCAL-ONLY: read files, no web tools |
| Profile pages | 4 / orch | LOCAL-ONLY: read pack, write profile |
| Master summary | 7 | LOCAL-ONLY: orchestrator reads everything, writes |

For tool API, fallback chains, and operational thresholds (URL counts, facet
counts, parallel calls), the brief points to the run-research tool reference. For
industry-framing graceful degradation (Powerpack → WebSearch → curl chain), see
`references/industry/research-powerpack-and-explore.md`.

## Output architecture contract

Domain-agnostic framing default tree:

```
<corpus-root>/
├── README.md                                       (entry point)
├── _meta/                                           (MAX 8 files)
│   ├── 00-master-summary.md                        (Phase 7)
│   ├── 01-charter.md                               (Phase 0; Wave 1 resolves)
│   ├── 02-entities.md                              (Wave 1A output)
│   ├── 03-axes.md                                  (Wave 1B output)
│   ├── 04-product-template.md                      (Phase 2)
│   ├── 05-axis-templates.md                        (Phase 2)
│   ├── 06-file-budget.md                           (Phase 3)
│   └── 07-dispatch-log.md                           (running log)
├── <entity-slug>/                                   (one per core; MAX 15 files)
│   ├── 00-overview.md
│   ├── 01-<axis-1>.md ... 0N-<axis-N>.md
│   └── 09-sources.md
├── <entity-slug>.md                                 (optional profile at root)
└── _cross/
    └── <axis-slug>/                                (MAX 12 files)
        ├── 00-overall-comparison.md
        └── 01-<scenario>.md ...
```

Industry framing default tree:

```
<topic-slug>/
├── README.md
├── _meta/
│   ├── research-plan.md
│   ├── _PRODUCT_TEMPLATE.md                        (Phase 2 maximalist template)
│   ├── _COMPARISON_TEMPLATE_<criterion>.md         (Phase 2 per-criterion)
│   ├── methodology-and-source-policy.md
│   ├── discovered-entities.md
│   └── file-budget.md
├── _cross-<scope>/
│   ├── 00-overview/
│   ├── <criterion-a>/
│   ├── <criterion-b>/
│   └── 09-sources/
├── <entity-slug>/
│   ├── 00-overview/
│   ├── <vertical-context-1>/
│   ├── <vertical-context-2>/
│   └── 09-sources/
└── <entity-slug>.md                                 (profile page; Phase 6)
```

When the executor is codex, a per-run **workdir sidecar** (`prompts/`, `logs/`,
`status/`, `audit/`, `run.json`) tracks the fanout state alongside the corpus —
codex writes answers directly to the final corpus paths via `-o`. See
`references/codex/wave-dispatch.md` for the sidecar layout.

Concrete folder + file naming rules, MAX-N ceilings, numbered-prefix scheme,
and the agent-chosen-filename rule: `references/filesystem.md`. Vertical-specific
category names (SaaS, OSS, dev-infra, data/API, regulated, consumer):
`references/industry/category-taxonomies.md`.

Numeric prefixes are scan order, not semantic naming. Filenames within each
numbered subfolder are agent-chosen based on the evidence found for that
specific entity. Two research tasks may legitimately land different
filenames in the same numbered subfolder — that is correct.

## Hard rules (load-bearing)

These break the corpus when ignored. Keep them at the top of mind.

1. **Run the intake AskUserQuestion batch before any wave.** Executor, scale, and
   framing are locked at intake and recorded in the charter — never start a heavy
   pass on assumptions.
2. **The orchestrator does not search.** Searching is the research task's job, via
   the `run-research` discipline embedded in its brief (Claude subagent or codex job).
3. **The orchestrator does not delegate synthesis.** Read every entity pack and
   every cross file personally before the master summary.
4. **Templates first, files second.** Phase 2 (template authoring) MUST
   complete before any entity-pack or cross-comparison file is written.
   Skipping templates is a hard failure — depth varies per task and
   comparability is lost.
5. **Maximalist templates, not generic skeletons.** A thin `_PRODUCT_TEMPLATE.md`
   (≤15 sections) means Phase 1's deep category pre-pass was skipped. Re-do it.
   Target ~30+ vertical-specific sections.
6. **MAX 8 tasks per wave (domain-agnostic) / MAX 20 per wave (industry).** Beyond
   the cap, run sequential sub-waves. For the codex executor, concurrency is bounded
   at 8/wave, 32 ceiling. Coordination overhead exceeds parallelism savings above the cap.
7. **Disjoint write scopes.** Each research task owns exactly one folder. No two
   tasks in the same wave write to the same path.
8. **Every research-doing brief invokes run-research.** Embed the run-research
   integration block verbatim — see `references/subagent-briefs.md` (Claude) or
   `references/codex/codex-prompt-skeleton.md` (codex).
9. **Every numeric / versioned / priced claim cites a verbatim quote.** Snippet
   citations are forbidden.
10. **No placeholder / stub files.** A template section with no evidence becomes
    a one-paragraph "insufficient evidence" entry inside an existing file in the
    same subfolder, naming the specific data gap. **Never** a stub file.
11. **Folder names are vertical-specific, filenames are agent-chosen.** The
    orchestrator chooses subfolder names per category (Phase 2). Research tasks
    pick the `01-meaningful-title.md` filenames inside those folders based on
    the evidence they surface.
12. **Separate confirmed facts, vendor/project claims, practitioner evidence,
    and inference.** Never treat snippets as evidence. Never present Reddit as
    "consensus" without per-comment attribution.
13. **Two-level orchestration only.** Research tasks do not create their own
    sub-tasks (no subagent spawns a subagent; no codex job spawns a codex job).
14. **No single-report output.** This skill produces a multi-file corpus. If
    the user wants a single report, redirect to `run-research`.
15. **MAX-N caps are ceilings, not targets.** 15 per entity / 12 per
    cross-axis / 8 per meta. Below ceiling is normal; sparse evidence is
    acceptable. See `references/filesystem.md`.
16. **Codex executor: idempotency is load-bearing.** Skip-existing is the default
    retry strategy; one answer file per job; every job gets a rendered prompt file on
    disk; an empty answer is `failed`, not `done`; between-wave reads are still
    non-delegable. Full contract: `references/codex/wave-dispatch.md` and
    `references/codex/codex-exec-contract.md`.

If any rule is violated, the rest of this skill stops applying — stop, recover,
and resume only after the violation is corrected.

## Self-correction triggers

If you notice yourself doing any of the following — **stop**:

- **Dispatching any wave before the intake AskUserQuestion batch is answered** → STOP. Run intake first; lock executor, scale, framing.
- **Skipping Phase 2 templates** and dispatching Wave 2 directly → STOP. Templates are the comprehensiveness contract.
- **Writing a thin or generic product template** (≤15 sections) → STOP. Re-do Phase 1's deep category pre-pass; re-author with ~30+ distinct sections. See `references/industry/template-authoring.md`.
- **Hardcoding filenames in the template** → STOP. Templates list sections + questions; tasks pick filenames per their evidence.
- **Letting a research task silently skip a template section** → STOP. Every section gets content OR an explicit one-paragraph "insufficient evidence" entry naming the gap.
- **Dispatching more than the cap** (8 domain-agnostic / 20 industry; codex 8/wave) **in one wave** → STOP. Coordination overhead exceeds parallelism savings. Split into sub-waves. See `references/orchestration.md`.
- **Summarizing Reddit as "consensus"** without per-comment attribution → STOP. Apply the audience-evidence fields from `references/synthesis.md` / `references/industry/evidence-and-synthesis.md`.
- **Treating a vendor's marketing page as confirmed fact** → STOP. Re-classify per source hierarchy; vendor claims belong in the vendor-claim ledger row.
- **Searching the web yourself as the orchestrator** → STOP. Dispatch a research task. Searching is the task's job, via run-research.
- **Delegating synthesis** → STOP. Read every core pack and every cross folder personally before writing the master summary.
- **Producing a single-report output** ("here's the markdown report") → STOP. This skill produces a multi-file corpus. If the user wants a single report, redirect to `run-research`.
- **Codex: choosing `medium` for every wave by accident, or marking an empty answer `done`** → STOP. Pick per-wave effort up front; empty = `failed`. See `references/codex/effort-routing.md` and `references/codex/wave-dispatch.md`.
- **Skipping the completion gate** ("looks done") → STOP. Run the verification commands in `references/verification.md`. Template-coverage audit, link check, source-ledger presence are non-negotiable.
- **Research task stalled, timed out, or returned shallow output** → STOP improvising. Apply the recovery procedures in `references/failure-modes.md` (Claude) or `references/codex/orchestrator-cookbook.md` (codex).

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Dispatching before the intake batch | Wrong executor/scale/framing locked in; rework | Always run the AskUserQuestion intake first |
| Templates skipped or written after entity research | No comprehensiveness boundary; depth varies by task | Phase 2 first, Wave 2 second. Always. |
| Template is thin or generic (≤15 sections) | Misses decider-weighted axes; produces shallow corpus | Re-do the deep category pre-pass; re-author maximalist template (~30+ sections) |
| Template prescribes exact filenames | Removes evidence-driven naming; tasks pad to fit | Templates list sections + questions; tasks pick filenames |
| Stub files for sections with no evidence | Pollution; no actual content | "Insufficient evidence" entry inside an existing file naming the data gap |
| Identical empty subfolders for every entity | Copy-paste research, no value | Create only evidence-justified files; address every template section |
| Cross-axis file is concatenation of per-entity summaries | Doesn't compare; just appends | Comparison template prescribes axes, ranking, scenarios; tasks follow |
| Pricing copied from page without unit economics | Vendors hide overages, gating, scenario costs | Preserve native units, model scenarios, name missing variables explicitly |
| Reddit evidence presented as "consensus" | Bias and small samples are erased | Preserve thread, username, date, quote, bias label |
| Source verification skipped because "it's clearly true" | Stale facts, contradicted vendor claims | Source ledger non-optional for `core` entities |
| Profile page duplicates evidence-pack content | Duplication; no synthesis added | Profile = readable narrative + links into pack; pack = atomic evidence files |
| Single-output thinking ("write me a report") | Loses navigability and source-traceability | Multi-file corpus is the contract; route to run-research if user wants single report |
| Orchestrator searches the web | Defeats wave model; pollutes orchestrator context | Orchestrator architects, dispatches, gates, synthesizes. Research tasks search via run-research |
| Orchestrator delegates synthesis | Master summary becomes stitched per-task paragraphs | Orchestrator personally reads every core pack and every cross folder before master summary |
| Codex: effort `medium` everywhere, or naked `&` fanout | Wastes budget; rate-limit cascade | Per-wave effort routing; bounded worker pool (8/wave, 32 ceiling). See `references/codex/` |

## Output contract

Show these artifacts at the phase that produces them. Never batch all artifacts
to the end.

1. **Phase 0** — scope statement + corpus scale + framing (domain-agnostic / industry) + executor (Claude / codex) + (if codex) the per-wave effort plan.
2. **Wave 1** — discovered entities table (tier + source URL + 1-line rationale) AND axis catalog AND category-understanding note (industry framing).
3. **Phase 2** — resolved category list AND the maximalist product template AND each cross-axis / cross-criterion template. Show inline (or summarized with link) — they are the comprehensiveness contract for the rest of the work.
4. **Phase 3** — file-count expectation derived from templates + tree shape + the Wave 2 dispatch map (which task owns which entity; for codex, slug → entity → effort).
5. **Wave 2** — dispatch map, then evidence-pack progress notes as tasks complete (codex: dispatch envelope + audit summary at wave end).
6. **Wave 3** — cross-axis / cross-criterion ranking summary.
7. **Wave 4** (optional) — profile-page index.
8. **Phase 7** — completion statement (path, files, entry points, gaps, verification, template coverage; for codex, total jobs and terminal states).

## Reference routing

Load only the reference whose phase is active. Loading all references at once
exhausts context.

| Reference | Read when |
|---|---|
| `references/intake.md` | Before Phase 0 — the mandatory AskUserQuestion batch: questions, option sets, recommended defaults, headless fallback |
| `references/thinking.md` | Phase 0, every session — the decomposition protocol; what counts as an entity vs axis vs primitive |
| `references/templates.md` | Phase 0, 2, 3 — concrete formats for charter, product template, axis templates, file budget; tier-promotion mechanics (domain-agnostic framing) |
| `references/orchestration.md` | Wave 1, 2, 3 — wave choreography, parallel-dispatch rules, tool steering, between-wave gate procedure (Claude executor) |
| `references/filesystem.md` | Phase 3 — directory contract, MAX-N caps, file naming, context-sharing through files |
| `references/subagent-briefs.md` | Wave 1, 2, 3, 4 — copy-paste-ready Claude brief templates with the run-research integration block |
| `references/synthesis.md` | Phase 7 — claims ledger discipline, profile-page template, master-summary structure, personal-read gate procedure |
| `references/verification.md` | Phase 7 — completion-gate commands and template-coverage audit |
| `references/failure-modes.md` | Any wave — recovery procedures for task timeouts, shallow output, MAX-N overflow, contradictions |
| `references/codex/codex-exec-contract.md` | Codex executor, any dispatch — flag spine, JSON events, MCP-active fallback, model/effort overrides |
| `references/codex/effort-routing.md` | Codex executor, Phase 0 — designing the per-wave effort plan; any wave transition |
| `references/codex/codex-prompt-skeleton.md` | Codex executor, Waves 1-4 — the 7-section prompt skeleton with input-paths / output-path / run-research block |
| `references/codex/wave-dispatch.md` | Codex executor, Waves 1-4 — bounded-concurrency dispatch loop, slug rules, skip-existing, status, audit, retry |
| `references/codex/orchestrator-cookbook.md` | Codex executor, between waves — when to read outputs, escalate effort, fall back to a Claude subagent, declare done |
| `references/industry/industry-architecture.md` | Phase 3 (industry framing) — 4-layer industry tree, file-count derivation from templates, entity tiering, validation gates |
| `references/industry/category-taxonomies.md` | Phase 2 (industry framing) — archetype skeletons (SaaS, OSS, dev-infra, data/API, regulated, consumer) before adapting to the vertical |
| `references/industry/template-authoring.md` | **Keystone reference** (industry framing). Phase 2 — writing the maximalist `_PRODUCT_TEMPLATE.md` and per-criterion `_COMPARISON_TEMPLATE_<criterion>.md` files |
| `references/industry/profile-pages.md` | Wave 4 / Phase 6 (industry framing) — writing standalone `<entity>.md` decision pages |
| `references/industry/discovery.md` | Wave 1 (industry framing) — sub-question decomposition, tiering, deep category pre-pass |
| `references/industry/evidence-and-synthesis.md` | Wave 2-3 (industry framing) — source hierarchy, source-map and claims-ledger schemas, Reddit/practitioner rules, pricing/unit-economics standards, cross-category structure |
| `references/industry/worked-example-cloud-browsers.md` | Any phase (industry framing) — annotated walkthrough of the cloud-browsers corpus including actual template artifacts. Mirror its *discipline*; do not copy slugs. |
| `references/industry/mission-briefs.md` | Wave 1, 2, 3, 4 (industry framing) — prompts for discovery, entity-pack, cross-comparison, audience, source-verification, profile-writer tasks |
| `references/industry/research-powerpack-and-explore.md` | Wave 1, 2, 3 (industry framing) — portable Research Power Pack API shapes (`get-research-consultancy`, `web-search`, `scrape-link`) plus web-capable research and local-corpus Explore patterns (≤20 per wave) |
| `scripts/init-corpus.sh` + `scripts/init-corpus.md` | Phase 0 or 3 — deterministic corpus scaffolding; root/meta starter files only, never entity evidence placeholders |

## Quick start

The first five minutes of any session:

1. **Intake** — run the single batched `AskUserQuestion` call (executor / scale / framing / scope). See `references/intake.md`. Never dispatch a wave before this is answered.
2. **Phase 0** — write `_meta/01-charter.md` from the intake answers + decider/use-case. Read `references/thinking.md` and `references/templates.md` (or `references/industry/discovery.md` + `references/industry/template-authoring.md` for industry framing) for the charter format. State framing + executor explicitly; if codex, write the effort plan (`references/codex/effort-routing.md`).
3. **Wave 1** — dispatch parallel discovery + scope tasks in one tool message. Both invoke run-research. Use `references/subagent-briefs.md` (Claude) / `references/industry/mission-briefs.md` (industry), or `references/codex/codex-prompt-skeleton.md` + `references/codex/wave-dispatch.md` (codex). Wait for both. Read every output personally.
4. **Phase 2/3** — read Wave 1 outputs; write templates per `references/templates.md` or `references/industry/template-authoring.md` (industry, keystone); plan architecture per `references/filesystem.md` or `references/industry/industry-architecture.md`. Optionally scaffold with `scripts/init-corpus.sh <topic-slug>` (see `scripts/init-corpus.md`). Show the architecture to the user before Wave 2.

After that, the loop is: Wave 2 (per-entity, possibly multiple sub-waves) →
Wave 3 (per-axis cross) → optional Wave 4 → Phase 7 verification + master
summary. Wave choreography lives in `references/orchestration.md` (Claude) and
`references/codex/wave-dispatch.md` (codex); the Phase 7 gate procedure lives in
`references/verification.md` and `references/synthesis.md`.

If anything is unclear, the question is almost always upstream: read
`references/thinking.md` and clarify the decomposition before dispatching more
tasks.

## Guardrails

- Do not make landing-page-style reports. Build the actual research corpus.
- Do not collapse product facts, pricing, practitioner sentiment, and source verification into one undifferentiated file.
- Do not create raw dump folders unless the user explicitly asks. Summarize and source-map instead.
- Do not use the same category names for every vertical when better names are available.
- Do not outsource final synthesis. The orchestrator reads the files and resolves contradictions personally.
- Do not exceed the per-wave cap. Run multiple waves instead.
- Do not let research tasks create sub-tasks. Two-level orchestration only.
- Do not start Wave 2 entity research before Phase 2 templates are written and shown to the user.
- Do not declare completion without running the Phase 7 verification, including the template-coverage audit.

## Bottom line

Ask the intake batch → decompose into entities × axes → architect the folder tree →
dispatch research in waves (Claude subagents or codex exec) through filesystem-bound
briefs → between waves, read everything personally → write the master summary → run
the verification gate. The filesystem is the deliverable, the context channel, and
the audit trail in one. If the deliverable is anything other than a folder of
source-backed evidence files, this is the wrong skill.
