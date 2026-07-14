# Prompt templates

Copy-adaptable scaffolds for each subagent role in `run-codex-adversarial-loop`.
Adapt the bracketed slots to the project discovered in Phase 1. These are
starting points — tune wording to the codebase, but keep the load-bearing
clauses (marked ★).

## 1. Explorer subagent (Phase 1, read-only)

> You are mapping a codebase so a review loop can target it. READ-ONLY — do not
> edit. Scope: `[repo or subsystem]`. Investigate `[your area: e.g. structure &
> build / runtime & data flow / tests / domain constraints / git history]` and
> return a COMPACT digest (conclusions, not file dumps):
> - the modules/dirs in your area and what each is responsible for;
> - the stack + notable versions and any framework idioms in use;
> - hard constraints and laws (e.g. "backend is frozen", tenancy/RLS, "no
>   destructive git", explicit-path staging, design/honesty rules);
> - test posture (what is covered, what harness);
> - the last ~15 commits touching your area (what recently changed/was fixed).
> Cite paths. Your final message IS the digest.

Synthesize all digests into one **project map** + an **already-known / laws**
ledger reused in every later prompt.

## 2. Reviewer (Phase 3, Codex adversarial-review)

Shared frame (★ keep all four) + a lens slot. Everything after `--effort xhigh`
is the review instruction.

> `--model gpt-5.5 --effort xhigh` REVIEW LENS `[N of M]` — `[lens name]`. One
> of `[M]` parallel reviewers, each owning ONE surface.
> ★ TARGET the FULL committed source tree at `[scope path]`, not a diff — an
> empty diff is NOT a clean bill; read broad, then deep in your lens only.
> ★ ALREADY-KNOWN / OUT-OF-SCOPE (do NOT re-report unless the item itself is
> flawed): `[cumulative fixed-ledger + laws, e.g. "backend frozen — report
> backend issues as notes not fixes; prior fixes: …"]`.
> ★ STAY IN YOUR LENS; other reviewers own the rest: `[forbidden overlap]`.
> ★ RULE: ground every finding in a cited file:line or a concrete failure
> scenario; if you cannot, return a clean verdict plainly — a fabricated
> finding is worse than a miss.
> LENS: `[the surface + failure-family, derived from the project map — e.g.
> "the query-cache and stores: keys whose scope mismatches the data, persisted
> state surviving identity change, hydration races"]`.

Do NOT name the specific bug. Give a surface + failure-family and let it hunt.

## 3. Verifier (Phase 5, read-only, BLIND TO SOURCE) ★ the trust guard

Never reveal the finding came from Codex. Frame neutrally and ask for
expansion.

> You are independently checking a claim about this codebase. READ-ONLY.
> A prior analysis flagged: "`[finding summary]`" at `[file:line]`, with this
> reasoning: `[one-line scenario]`.
> ★ Independently verify against the actual code whether this is TRUE. Do not
> assume the prior analysis is correct — it is sometimes wrong or misreads
> intentional code.
> ★ While you are in that area, report anything MORE you find that is related.
> Return: a VERDICT — CONFIRMED / REFUTED / PARTIAL — with cited file:line
> evidence and the concrete failure scenario (or why it is a non-issue), plus a
> list of any ADDITIONAL issues you noticed nearby. Your final message IS the
> verdict.

Batch a small related cluster into one verifier when efficient. Treat verifier
output as a strong claim; the orchestrator still makes the final call.

## 4. Fixer (Phase 7, in a worktree, grouped)

> You are fixing a verified group of findings in `[project]`. You work in an
> isolated git worktree `[path]` on branch `[fix/<group>]` off `[base]`.
> ★ VERIFY each finding against the code before fixing; if a claim is wrong,
> refute it with evidence instead of "fixing" it.
> ★ YOUR FILES ONLY: `[explicit file list]`. Sibling fixers own `[other files]`
> — do NOT touch those. Respect project laws: `[e.g. frozen backend, tokens
> only, no destructive git, explicit-path staging]`.
> FINDINGS (verify then fix): `[per finding: severity, one-line, file:line,
> scenario, and any "verify vs recent fix" caveat]`.
> Add/adjust tests per fix. `[Build/test locally only if the project allows;
> otherwise CI is the proof rung.]`
> SHIP: conventional commits (scope required), stage explicit paths only, push
> ONCE, open a PR against `[base]`, and drive CI to a TERMINAL conclusion on the
> exact head SHA. REPORT: per-finding verdict (confirmed/refuted + mechanism),
> tests added, PR/URL + head SHA + CI conclusion.

Group so that same-file or same-subsystem findings go to ONE fixer; keep every
fixer's file set disjoint from the others.

## Notes on adaptation

- The **already-known ledger grows each loop** — append merged fixes so later
  reviewers do not re-report them.
- If the project forbids local heavy builds, tell fixers "CI is the proof rung"
  and drive runs to terminal; otherwise let them build/test locally.
- Keep reviewer prompts roughly the length of a short paragraph per lens — long
  enough to be clear, short enough not to over-direct.
