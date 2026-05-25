# Triage and the Gradual-Expansion Curriculum

This file governs phases ③ TRIAGE and ④ DECIDE: how to rank what matters, how to
scan for hardening, and how to choose the *next rung* without ever leaping.

## The three tiers (strict precedence)

Rank every candidate into a tier. **Never act on a lower tier while a higher tier
has open, unaddressed work** — this is the capping rule that keeps the steward
honest (modeled on "never open a low issue while a critical one is untouched").

### ⓐ Critical bugs — always win

Signals: a crash, data loss, a broken build, a failing CI gate, or a regression
traceable to a recent commit. If `orient.sh` shows red CI or a commit that
plausibly broke something, investigate that first. A critical bug outranks every
hardening idea, every time.

### ⓑ Existing open issues — advance before you invent

Before inventing new work, look at what is already in the tracker. The highest
value move is often to **deepen, clarify, or unblock** an existing issue: add
missing acceptance criteria, attach fresh evidence from recent commits, or note
that a dependency is now resolved. Inventing new work while good issues sit
half-specified is how trackers rot.

### ⓒ Self-invented hardening — only when ⓐ and ⓑ are clear

This is where the steward earns its keep. Scan through the hardening lens (below)
and propose the single most valuable, appropriately-sized next step.

## Priority bands

Tag each issue with a band; map to the repo's existing priority labels if it has
them, else use `P0`–`P3`.

| Band | Meaning | Capping rule |
|---|---|---|
| **P0** | Critical bug / active breakage | Nothing else proceeds until addressed (filed + plan). |
| **P1** | High-value hardening; real failure risk | Do not file P2/P3 while a P1 is unfiled. |
| **P2** | Solid resilience/observability improvement | Normal cadence. |
| **P3** | Nice-to-have polish | Only when nothing better exists; rarely worth a cycle. |

## The hardening lens

When inventing work (tier ⓒ), scan the code and recent changes against these four
dimensions. Concrete questions to ask — each is a candidate issue if the answer is
"no" and you can cite evidence:

### Stability
- Are there unhandled states, nil/undefined paths, or unchecked array/dict access?
- Could a recent commit have introduced a race or an ordering assumption?
- Are there `TODO`/`FIXME`/`HACK` markers near load-bearing code?
- Do startup/shutdown paths assume the happy case?

### Resilience
- Do network/IO calls have **timeouts**? Any unbounded wait?
- Is there **retry with backoff** on transient failures — and a cap so it can't spin?
- Does the system **degrade** when a dependency is down, or hard-fail?
- Are there single points of failure with no fallback?

### Observability
- When something fails, is there a **log line that says what and why** — actionable,
  not just `catch {}`?
- Are key operations traceable (correlation/IDs, structured fields)?
- Are there metrics/counters for the things that matter (failures, retries, latency)?
- Could an on-call engineer diagnose a failure from the logs alone?

### Graceful failure handling
- On partial failure, does state roll back cleanly, or is it left half-written?
- Do user-facing errors explain the problem and the next step?
- Are exit codes / error returns honest (no `exit 0` on failure)?
- Is there a clean path when the *expected* failure happens (file missing, perms,
  offline)?

**Out of scope:** security, auth, secrets, CVEs. If you see one, record it in
`POINT-OF-VIEW.md` and surface it to the human — do not file it as hardening.

## The gradual-expansion curriculum

The expansion philosophy — *Bulgaria → Romania → Vienna, never straight to
Portugal* — is operationalized as an **automatic curriculum** (the technique
Voyager uses: propose the next task that is appropriately difficult *for the
current state*, bottom-up).

### How to pick the next rung

1. Read `roadmap.md`. The current frontier is the first unchecked rung.
2. Ask: *given the project's current stability and what's already filed, what is the
   smallest step that meaningfully advances the frontier?*
3. The right step is **adjacent** to what's already solid — one country over. If the
   project just got timeouts (Bulgaria), the next rung is retry/backoff (Romania),
   not a full resilience-framework rewrite (Portugal).
4. If the most valuable idea is large, **decompose it** onto the roadmap as several
   rungs and take only the first this cycle.
5. The chosen step should feel *inevitable* — the obvious next thing a careful
   engineer would do, not a clever leap.

### Sizing (effort)

| Size | Heuristic | Use |
|---|---|---|
| **S** | < ~half a day; one file/function | Preferred. Most rungs should be S. |
| **M** | ~1-3 days; a few files, a test | Fine when clearly bounded. |
| **L** | a week+; cross-cutting | **Never invent directly.** Decompose into S/M rungs first. |

Never invent an L step, and never invent any tier-ⓒ step while a tier-ⓐ bug or a
half-specified tier-ⓑ issue exists.

## "Always productive" without becoming noisy

The steward should produce value every cycle, but **value is not always a new
issue**. Reconcile "file issues" with "never spam" like this:

1. If a worthy, deduplicated, evidence-backed step exists → file it (the default).
2. Else, if an existing issue can be meaningfully deepened → deepen it (comment /
   updated plan), and log that as the cycle's output.
3. Else, if the roadmap needs refinement → sharpen the ladder and the point of view.
4. Never manufacture a low-signal issue just to "have filed something." A cycle
   that thoughtfully advances the roadmap and memory is a successful cycle.
