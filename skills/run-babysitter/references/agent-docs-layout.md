# The .agent-docs Memory Layout

The babysitter's entire memory lives in `.agent-docs/` at the repo root. It is
committed (so the steward's reasoning becomes part of project history and travels
with the repo) **except** `.agent-docs/scratchpad/`, which is git-ignored working
memory. This file is the schema and the init scaffold.

## Design discipline: append-only truth, projected snapshots

Borrowed from durable-execution engines (Temporal Event History, Zeebe's journal,
event sourcing): **the append-only log is the source of truth; everything else is a
projection (a cache) derived from it.**

- `RUNLOG.md` is **append-only**. Never edit a past entry. It is the truth.
- `STATE.md` and `POINT-OF-VIEW.md` are **projections** — rewritten each cycle as
  the current best summary. If they are ever lost or look stale, rebuild them by
  reading `RUNLOG.md`.
- `failures.md` is **append-only** (an episodic buffer; you only ever add).
- `scratchpad/` is **disposable** per-cycle thinking; never trusted across runs.

This means a crash mid-cycle never corrupts truth: at worst you re-derive `STATE.md`
from `RUNLOG.md` and continue.

## Directory structure

```
.agent-docs/
├── README.md                  what this dir is, who writes it, how to read it
├── memory/
│   ├── STATE.md               projection: where things stand right now
│   ├── POINT-OF-VIEW.md       the steward's standing thesis about the project
│   ├── RUNLOG.md              append-only: one entry per cycle (source of truth)
│   └── failures.md            append-only: approaches that failed, so they aren't repeated
├── roadmap.md                 the gradual-expansion ladder of hardening frontiers
├── issues/
│   ├── filed/<slug>.md        idempotency ledger: one file per opened issue
│   └── drafts/<slug>.md       drafted-but-not-filed issues (e.g. gh unavailable)
├── plans/<topic>.md           comprehensive multi-cycle plans
└── scratchpad/                GIT-IGNORED per-cycle step-by-step thinking
    └── <ISO8601>-cycle.md
```

## File schemas

### memory/STATE.md (projection — overwritten each cycle)

```markdown
# Babysitter State

- **Mode:** enhance
- **Cycle:** 7
- **Last run (UTC):** 2026-05-23T18:40:00Z
- **Last-seen commit:** d433ed4
- **Repo:** owner/name  (issues: enabled | disabled)
- **Current focus:** resilience — network retry/backoff frontier
- **Open issues authored by me:** 4  (see issues/filed/)
- **Roadmap rung:** 3 of 9  ("Romania")
- **Lifecycle state:** IDLE        # see references/loop-and-recovery.md
- **Stall counter:** 0
- **Dashboard issue:** #42
```

### memory/POINT-OF-VIEW.md (projection — refined by reflection)

The steward's *thesis*. This is where the skill earns "has a point of view." A few
sharp paragraphs, not a log:

```markdown
# Point of View

## What this project is
<one paragraph: purpose, stack, maturity, who depends on it>

## How it tends to fail
<the recurring fragility themes you have observed — e.g. "network calls assume the
happy path; timeouts are rarely set; errors are swallowed rather than logged">

## Where hardening pays off most
<ranked: the 2-3 areas where small investments most reduce future pain>

## Standing beliefs (updated by reflection)
- <belief> — formed cycle N, evidence: <…>
```

### memory/RUNLOG.md (append-only — the source of truth)

One entry per cycle, newest appended at the bottom. Never edit prior entries.

```markdown
## Cycle 7 — 2026-05-23T18:40:00Z
- **Read:** 3 commits since d433ed4; 4 open issues; CI green.
- **Triage:** no critical bug; existing issues stable; invented hardening (tier ⓒ).
- **Decision:** add structured logging around the install path (roadmap rung 3).
- **Action:** filed issue #45 "observability: structured logs for install flow".
- **Outcome:** ok. Ledger: issues/filed/observability-structured-logs-install.md
- **Next:** rung 4 — timeout on the remote-MCP fetch.
```

### memory/failures.md (append-only — episodic buffer)

Before acting, read the last few entries so you do not repeat a failed approach.

```markdown
## 2026-05-23T18:10Z — gh issue create rate-limited
Tried filing during a burst; got 403 secondary-rate-limit. Lesson: one issue per
cycle, and back off 60s on 403 before retrying once. (transient)
```

### roadmap.md (the gradual ladder)

The expansion plan, ordered. Each cycle advances at most one rung. New ideas are
appended as future rungs, never jumped to.

```markdown
# Hardening Roadmap  (advance one rung per cycle)

> Gradual by design: Bulgaria → Romania → Vienna, never straight to Portugal.

- [x] 1. Stability — guard the nil-config path in startup        (issue #41, done)
- [x] 2. Resilience — timeout on the primary network call        (issue #43)
- [ ] 3. Observability — structured logs for the install flow    (issue #45) ◄ current
- [ ] 4. Resilience — retry+backoff on remote-MCP fetch
- [ ] 5. Graceful failure — partial-write rollback on save
- [ ] … (frontier; refine as the point of view sharpens)
```

### issues/filed/&lt;slug&gt;.md (idempotency ledger)

Written **the moment** an issue is filed. Its existence is the proof the issue was
opened — the dedup gate checks here first. `<slug>` is the normalized title.

```markdown
# Filed: observability — structured logs for install flow
- **Issue:** #45  https://github.com/owner/name/issues/45
- **Filed (UTC):** 2026-05-23T18:40:00Z
- **Cycle:** 7
- **Title:** observability: structured logs for the install flow
- **Status:** open
```

### plans/&lt;topic&gt;.md (comprehensive plans)

When a step deserves more than the issue body holds, write the full plan here and
link it from the issue. Sections: Problem · Context/evidence · Approach (with
alternatives considered) · Acceptance criteria · Dependencies · Complexity ·
Risks · Rollout/verification.

### scratchpad/&lt;ISO8601&gt;-cycle.md (git-ignored thinking)

One file per cycle. Force yourself to think here in writing **before** deciding:
list what you read, the candidate steps you considered and rejected (and why), and
the one you chose. This keeps deep reasoning out of the committed record and out of
the main context window until it has crystallized into a decision.

## INIT scaffold (first run only)

When `.agent-docs/memory/STATE.md` does not exist:

1. **Create the tree:** all directories above (`memory/`, `issues/filed/`,
   `issues/drafts/`, `plans/`, `scratchpad/`).
2. **Handle `.gitignore` (low-freedom — do exactly this).** Goal: track everything
   under `.agent-docs/` **except** `scratchpad/`. A global gitignore very often
   hides dot-directories (a `.*/` rule is common — it is the reason repos un-ignore
   `.planning/`, `.github/`, etc.), so the **robust, always-safe** block un-ignores
   `.agent-docs/` first and then re-ignores the scratchpad. Order matters (last
   match wins). Append, only if absent:

   ```gitignore
   # Babysitter memory: committed, except the scratchpad. The un-ignore lines
   # defeat any global rule (e.g. `.*/`) that would otherwise hide this dot-dir.
   !.agent-docs/
   !.agent-docs/**
   .agent-docs/scratchpad/
   ```

   This block is correct whether or not a global ignore exists — where none does,
   the un-ignore lines are harmless no-ops. **Always verify** it took effect, because
   a silent global ignore is the difference between committed memory and lost memory:

   ```bash
   git check-ignore .agent-docs/memory/STATE.md \
     && echo "STILL IGNORED — fix .gitignore before committing" \
     || echo "trackable — good"
   git check-ignore .agent-docs/scratchpad/x >/dev/null \
     && echo "scratchpad ignored — good" || echo "scratchpad NOT ignored — fix it"
   ```

3. **Baseline the project** (this is the steward's first read): read `README`,
   `CLAUDE.md`/`AGENTS.md`/`CONTRIBUTING.md`, the build system, CI config, test
   setup, and package manifests. Skim recent history (`git log --oneline -30`) and
   any open issues. Think in the scratchpad.
4. **Seed `POINT-OF-VIEW.md`** from that baseline — an honest first thesis.
5. **Seed `roadmap.md`** with an ordered ladder of hardening frontiers, smallest
   and most valuable first.
6. **Write `README.md`** explaining the directory to humans (it is the babysitter's
   memory; humans may read it, and may reply inside `AWAITING_HUMAN.md`).
7. **File the inaugural issue** — the first rung — through the full ACT path
   (`references/issue-authoring.md`), and create the dashboard issue.
8. **Write `STATE.md` (mode now "enhance"), append the cycle-0 `RUNLOG.md` entry,
   commit** `.agent-docs/` with `chore(babysitter): init — baseline + roadmap`.

After init, every subsequent run is ENHANCE mode.

## Atomic writes (low-freedom)

Never write a memory file in place if a crash mid-write could corrupt it. Write to
a temp file and rename (rename is atomic on POSIX):

```bash
tmp="$(mktemp)"; printf '%s\n' "$content" > "$tmp" && mv "$tmp" .agent-docs/memory/STATE.md
```

Append-only files (`RUNLOG.md`, `failures.md`) may use `>>` directly.

## Reflection trigger (forming the point of view)

Modeled on Generative Agents' reflection: do not reflect every cycle, but on a
cadence (every ~5 cycles, or when several related observations have accumulated),
run a reflection pass: read the recent `RUNLOG.md` entries, synthesize them into
1-3 higher-level beliefs, and update `POINT-OF-VIEW.md`. Reflection is how the
steward graduates from logging events to *having an opinion* about the project.
