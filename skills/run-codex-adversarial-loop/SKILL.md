---
name: run-codex-adversarial-loop
description: Use skill if you are fanning out many parallel Codex adversarial reviews across derived lenses, independently verifying every finding, fixing confirmed issues in grouped worktrees, and looping until clean.
---

# Run Codex Adversarial Review Loop

Orchestrate a bounded, self-verifying quality loop over a codebase using Codex
as a fan-out adversarial reviewer. The loop is: **explore the project → derive
review lenses from what was found → fan out parallel Codex reviews → collect →
independently verify every finding → re-evaluate → fix verified issues in
grouped worktree subagents → merge → build-check → loop with fresh reviewers
until a wave returns only noise.**

Two ideas make this reliable and are non-negotiable:

1. **Reviewers are derived, not dictated.** Explorer subagents learn the actual
   project first; the review lenses come from that map. Do not hardcode "check
   X" — let the exploration decide what surfaces exist and matter.
2. **Every Codex finding is independently verified before any fix.** Codex
   under a "find something" framing sometimes misreads intentional code or
   invents issues. A separate verifier confirms/refutes each claim against the
   code — and is asked to report anything *more* it sees — before a fixer
   touches anything.

Run the whole thing as the orchestrator. Spawn subagents for exploration,
verification, and fixing. Keep control of triage and merges.

## Prerequisites (Phase 0)

- **Codex CLI present.** Confirm `codex --version` works and the companion
  script resolves (see `references/codex-and-loop-mechanics.md` for the exact
  path glob and the `gpt-5.5` vs `gpt-5.5-codex` account constraint).
- **Git repo with a clean-enough tree** and a known integration branch
  (usually `main`). Confirm the build/test gate command (CI or local).
- **Agree the scope** with the user if ambiguous (whole repo, or one subsystem
  such as a single app/package). State the chosen scope.

## The loop at a glance

| Phase | Actor | Output |
|---|---|---|
| 1 Explore | parallel read-only subagents | project map (structure, stack, laws, prior fixes, test posture) |
| 2 Design lenses | orchestrator | ~50 candidate lenses → minimal covering set (~15–26), each grounded |
| 3 Review | parallel Codex reviews (background) | one report file per lens |
| 4 Collect | orchestrator | deduped finding ledger (by file + defect-class) |
| 5 Verify | parallel verifier subagents (blind to source) | CONFIRMED / REFUTED / PARTIAL + extra findings |
| 6 Re-evaluate | orchestrator | verified fix-list, grouped into disjoint-file batches |
| 7 Fix | grouped subagents in **worktrees** | one PR per group, CI green |
| 8 Merge | orchestrator | fixes on the integration branch |
| 9 Build-check | orchestrator (minor) or subagent (major) | branch stays green |
| 10 Loop | orchestrator | re-run from Phase 1 with fresh reviewers, or stop |

## Phase 1 — Explore (learn before judging)

Spawn several read-only explorer subagents in parallel, one per broad area
(e.g. structure/build, runtime/data flow, tests, domain constraints, prior
git history). Instruct each to return a compact digest, not file dumps. The
orchestrator synthesizes a **project map**: module layout, stack/versions,
data/control flow, hard constraints ("frozen backend", design laws, tenancy),
existing test coverage, and the last N fixes from `git log`. This map is the
raw material for lens design and for the shared "already-known / out-of-scope"
ledger every later prompt carries.

## Phase 2 — Design the review lenses (derive, then minimize)

From the project map, brainstorm ~50 candidate review lenses spanning
correctness, state/data, security/trust, contract-fidelity (frontend vs real
backend shapes, or module vs its contract), accessibility, performance,
cross-cutting semantics (dates, number formatting, money), UX/honesty, build/
deps, and test rigor — **tailored to what actually exists in this project.**

Then **reduce to a minimal covering set** by contextually grouping near-neighbors
into one reviewer each, dropping near-zero-yield lenses with a stated reason.
Aim for the count where each lens is one reviewer-sized coherent substrate +
one failure family — typically 15–26. Score and select per
`references/lens-design.md`. Assign each lens a **primary region + forbidden
overlap** so reviewers do not converge on the same rich surface.

Do not tell reviewers the specific bug to find. Give each a surface and a
failure-family and let it hunt.

## Phase 3 — Fan out Codex reviews

Fire one Codex adversarial review per lens, in the background, each writing to
its own output file. Every reviewer prompt carries the shared frame:

- **Target the full committed tree, not a diff** ("an empty diff is not a clean
  bill").
- **The already-fixed / out-of-scope ledger** from the project map + prior
  loops ("do not re-report unless the fix itself is flawed").
- **The anti-fabrication rule**: "ground every finding in a cited file:line or
  a concrete failure scenario; if you cannot, return a clean verdict — a
  fabricated finding is worse than a miss."
- **The lens** (surface + failure-family), and its forbidden-overlap.

Exact invocation, backgrounding, model/effort, and output handling are in
`references/codex-and-loop-mechanics.md`. Prompt scaffold is in
`references/prompt-templates.md`.

## Phase 4 — Collect and dedupe

Wait for all reviews to reach a terminal state. Extract each report's verdict +
finding headlines with `scripts/scan-verdicts.sh`. Build one ledger, deduped by
`(file, defect-class)`. Split into: candidate real findings, likely-known/
by-design, and out-of-scope (e.g. backend when backend is frozen).

## Phase 5 — Verify (the critical guard — do this BEFORE any fix)

For each candidate finding (or tight cluster), spawn a **verifier subagent**.
Frame it **neutrally and blind to the source** — never say "Codex said". Use:

> "A prior analysis flagged: `<finding>` at `<file:line>`. Independently check
> the code and decide whether this is actually true. While you are in that
> area, report anything MORE you find. Return a verdict — CONFIRMED / REFUTED /
> PARTIAL — with cited evidence, plus any additional issues."

Verifiers run read-only in parallel. This step is why the loop is trustworthy:
it catches Codex misreads (intentional code read as a bug) and invented issues,
and it opportunistically expands real findings. Scaffold in
`references/prompt-templates.md`.

## Phase 6 — Re-evaluate (orchestrator judgment)

Using the verifier statements, the orchestrator re-triages by itself: keep
CONFIRMED, drop REFUTED (record them as verified false-positives), fold in the
"anything more" additions, and route out-of-scope items to a wishes/backlog
note instead of a fix. Then group the surviving verified issues into
**disjoint-file fix batches** — same-file or same-subsystem issues go to one
fixer so no two fixers touch the same file.

## Phase 7 — Fix in worktrees (grouped)

**Create a worktree per fix-group before assigning it** (all fixer subagents
run in isolated worktrees, never the main checkout). Give each fixer: its
grouped findings, an explicit file-ownership boundary (and the list of files
sibling fixers own), a **verify-then-fix mandate** ("confirm each against the
code; refute with evidence if wrong"), tests-per-fix, and drive-CI-to-green.
Scaffold in `references/prompt-templates.md`; worktree discipline in
`references/codex-and-loop-mechanics.md`.

## Phase 8 — Merge

As each fixer's PR goes green **on the exact pushed SHA**, review the diff and
merge to the integration branch. Rebase later fixers if the tree moved. Do not
trust a fixer's self-reported "green" — read the run.

## Phase 9 — Build-check

After the batch merges, run the build/test gate on the integration branch. If
it surfaces a **minor** issue (a lint nit, a trivial type fix, a stray import),
the orchestrator fixes it directly. If **non-trivial**, spawn a focused
subagent. Return the branch to green before looping.

## Phase 10 — Loop or stop

Re-run from Phase 1 (or at least re-explore and re-derive lenses) with **fresh
reviewers that are given no memory that this is a later iteration** — they
always audit from scratch, so each pass samples different corners. Carry only
the growing already-fixed ledger.

**Stop when a whole wave converges to noise**: findings are only low-value/
hardening on not-yet-built surfaces, or verifiers refute most of them. Report
the convergence and hand the residual to the normal backlog. Also stop at any
user-set bound (max loops / time / budget). Never loop forever.

## Guardrails

- **Verify before fix, always.** No fixer runs on an unverified Codex finding.
- **Reviewers derive lenses; the skill never dictates specific checks.**
- **All fixer subagents work in worktrees created before assignment; fixers
  own disjoint files.**
- **Merges require CI green on the exact SHA, read by the orchestrator.**
- **Loop reviewers are stateless across iterations** (no "round N" leakage) so
  they explore fresh each time.
- **Respect project laws discovered in Phase 1** (frozen backend, no
  destructive git, staging explicit paths, etc.). Out-of-scope findings become
  backlog notes, not edits.

## Resources

- **`references/codex-and-loop-mechanics.md`** — companion path resolution,
  model/effort constraints, backgrounding + output files, dedup, worktree
  discipline, merge/build-check routing, convergence criteria.
- **`references/prompt-templates.md`** — copy-adaptable scaffolds for explorer,
  reviewer (shared frame + lens slot), verifier (neutral/blind framing), and
  fixer (verify-then-fix + worktree) prompts.
- **`references/lens-design.md`** — the 50-candidate → minimal-covering-set
  method, the scoring model, and how to group without losing coverage.
- **`scripts/scan-verdicts.sh`** — extract verdicts + high/medium finding
  headlines from a set of Codex report files for fast triage.
