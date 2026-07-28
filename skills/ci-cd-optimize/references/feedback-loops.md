# Feedback loops: watching CI without blocking, flooding, or false greens

How an agent (or engineer) receives the result of a CI run safely. The core
failure modes this file prevents: blocking a session on a foreground watch,
accepting a green run for the wrong commit, treating an empty or partial
answer as success, and missing late-registering workflows.

## Contents

- [Choosing a waiting primitive](#choosing-a-waiting-primitive)
- [The exact-SHA contract](#the-exact-sha-contract)
- [Using scripts/ci-watch.py](#using-scriptsci-watchpy)
- [Verdicts, exit codes, and precedence](#verdicts-exit-codes-and-precedence)
- [Custom provider probes](#custom-provider-probes)
- [Registration races and late workflows](#registration-races-and-late-workflows)
- [Reacting to results](#reacting-to-results)
- [Shrinking the loop](#shrinking-the-loop)
- [Harness wiring](#harness-wiring)

## Choosing a waiting primitive

| Need | Primitive | Why |
|---|---|---|
| One notification when CI finishes | Background command that exits at terminal state (`ci-watch.py`) | Single completion signal; no polling in the session |
| React to each state change / first red | Streaming monitor over `ci-watch.py` output lines | `CI-RED` arrives before the run finishes; act early |
| Gate a follow-up action on green | `ci-watch.py <sha> ... && <next-step>` | Exit-code classes make chaining safe (superseded exits 3, not 0) |

Do not use foreground TTY watch commands (`gh run watch`, `avr run watch`
without automation flags) inside an agent session: they block the loop and
their redraw output is unusable as an event stream. Do not poll with bare
sleeps: either you flood the provider or you idle past the result.

## The exact-SHA contract

A verdict is only meaningful for one exact commit:

- Pin the full 40-character SHA. Branch-latest, PR-check summaries, and
  auto-selected "most recent run" views can silently report a different
  commit's result.
- After any watch, the reported runs' `head_sha` must equal the pinned SHA.
  A green run for another commit proves nothing about yours.
- A newer push to the branch retires the watcher: its verdict becomes
  `superseded`, and the new commit needs its own watcher. Never reinterpret
  a stale watch as evidence for the new tip.
- A rerun creates a new attempt for the same run. The latest attempt is
  authoritative: an old failed attempt must not false-red a green rerun, and
  a green first attempt must not mask a red rerun.

## Using scripts/ci-watch.py

Run it; do not read its source into context. It is stdlib-only Python.

```bash
python3 scripts/ci-watch.py <full-40-hex-sha> \
  --repo OWNER/REPO --branch <branch> \
  --deadline 1800 --registration-deadline 180 --settle-deadline 60
```

Defaults suit a typical push-triggered pipeline; tune deadlines to the
pipeline's real p95, not hope. GitHub is the built-in provider (uses `gh`,
already authenticated). Key flags:

- `--expect-none` — for path-filtered commits where zero runs is the correct
  outcome. Success requires a successful probe *proving* the empty result;
  a dead probe can never satisfy it.
- `--allow-neutral` — run-level `skipped`/`neutral` conclusions count as
  green. Only use when the effectiveness contract explicitly permits those
  workflows to skip (see `effectiveness-contract.md`).
- `--probe-command CMD ARG...` — custom provider probe (must be last flag).

Output is append-only lines, one JSON payload each: `CI-EVENT`
(registration, state changes, retired attempts, branch-tip changes),
`CI-RED` (first sight of a red unit, with a ready-to-run log argv),
`CI-ERR` (deduplicated probe problems), `CI-HB` (liveness while quiet), and
exactly one `CI-DONE` with the verdict.

`CI-RED` carries a `scope` field: `run` for run-level conclusions, `job`
when the built-in GitHub probe surfaces an already-failed job inside a
still-running run. Job reds arrive minutes before the run completes — react
to them — but they never decide the verdict: the run's own conclusion stays
authoritative, so a `continue-on-error` job cannot false-red a green run.

The registration window is clamped to the overall deadline. If a complete
enumeration has proven zero runs when the overall deadline arrives, the
verdict is `no-run` (or `success` under `--expect-none`), never a
misleading `timeout`.

## Verdicts, exit codes, and precedence

| Verdict | Exit | Meaning |
|---|---|---|
| `success` | 0 | Every run-level unit explicitly green after the settle window |
| `failure` | 1 | Genuine red for the pinned SHA (always wins over supersession) |
| `cancelled` | 1 | Cancelled/skipped/neutral units without proven supersession |
| `timeout` | 2 | Hard deadline reached with active units and no red |
| `no-run` | 2 | Nothing registered within the registration deadline |
| `probe-dead` | 2 | Probe/config failures exhausted the error budget |
| `superseded` | 3 | Branch tip provably moved; no genuine red evidence |

Precedence rules worth internalizing:

- **Red beats everything.** A genuine failure for the pinned SHA is real
  evidence; a newer push does not erase it.
- **Cancelled is not failure and not superseded.** It becomes `superseded`
  only when the branch tip is *proven* to have moved. A failed tip lookup
  proves nothing.
- **Nothing unknown is green.** Unknown states, malformed probe output,
  partial output from a nonzero probe exit, incomplete enumeration, and
  post-registration empty responses are all probe errors — they can only
  lead to `probe-dead`, never to `success`.
- **Exit 2 means "no verdict", not "failed CI".** Distinguish it in
  automation: rerunning a red pipeline and rerunning a dead probe are
  different responses.

## Custom provider probes

For providers without built-in support (GitLab, CircleCI, Buildkite, Avrea,
in-house), supply `--probe-command`. The probe receives `CI_WATCH_SHA`,
`CI_WATCH_REPO`, `CI_WATCH_BRANCH` in its environment and must print one
JSON envelope per invocation:

```json
{
  "schema_version": 1,
  "provider": "gitlab",
  "repository": "group/project",
  "sha": "<the exact 40-hex sha it queried>",
  "complete": true,
  "branch_tip": null,
  "units": [
    {"run_id": "12345", "attempt": 1, "name": "test: unit",
     "state": "active", "url": "https://...",
     "log_hint": ["glab", "ci", "trace", "12345"]}
  ]
}
```

Contract:

- `state` uses only the canonical vocabulary: `active`, `green`, `red`,
  `cancelled`, `neutral`. The probe owns the translation from provider
  states; the watcher rejects anything else. Never map an unfamiliar
  provider state to `green` "because it sounds done".
- `complete: true` asserts the enumeration covered every unit for the SHA
  (all pages). If the probe cannot prove completeness, it must exit nonzero
  instead — a nonzero exit invalidates all of its output by design.
- `branch_tip` is either a full 40-hex SHA (proven) or `null` (unknown).
  Never guess.
- `log_hint` is an argv array, never a shell string.

### PR gating is a different surface

Required PR checks can include third-party check runs that never appear in
the Actions runs enumeration, so the built-in probe can report green while
the PR is still not mergeable. When PR merge is the actual gate, watch that
surface: build a custom probe over `gh pr checks <pr> --json name,bucket`
(terminal when nothing is pending) — noting it can also list
expected-but-unreported checks. Watch whichever surface actually gates you.

## Registration races and late workflows

Between `git push` and the first visible run there is a window where the
provider reports nothing. The watcher handles these; know why they exist:

- **Registration deadline** — an empty answer during the window is normal;
  an empty answer forever means `no-run` (path filters? workflow disabled?
  wrong branch trigger?). Never treat early emptiness as green.
- **Settle window** — after every known run finishes, the watcher keeps
  probing briefly. Staggered sibling workflows and `workflow_run`-chained
  pipelines register late; the first fast workflow finishing green is not
  the pipeline being green. Any new unit re-opens the window.
- **Reusable-workflow startup failures** — a caller can fail with
  `startup_failure` and zero jobs (bad ref, path, inputs, permissions).
  There are no step logs to fetch; diagnose by reducing the caller to a
  minimal `uses:` job. The watcher reports these as run-level red.

## Reacting to results

- On `CI-RED`, act immediately: run the attached `log_hint` command, read
  the failing step, and start the fix while remaining jobs run. Do not wait
  for the full pipeline when the first red already tells you the outcome.
- On `failure`, fetch logs for the exact failing run/job ID — not "latest
  run". Fix attributable defects, commit, push, and arm a **new** watcher
  for the new SHA.
- On `timeout`, go look: queued (capacity — see
  `capacity-and-contention.md`), hung job, or a deadline set below the
  pipeline's real duration. Never extend the deadline as a reflex.
- On `probe-dead`, fix the probe/auth/API problem first; you have no
  verdict yet. Re-running the pipeline does not repair a dead probe.
- On a CI-only failure (passes locally), reproduce the *condition*, not the
  whole pipeline: job-wide env vars, a clean checkout, a different working
  directory, absent secrets. Narrow reproduction beats re-running the full
  run to debug.
- On identical-SHA rerun requests, remember: a pass-after-retry is a flake
  signal, not a green pipeline (see `testing-and-flakiness.md`).

## Shrinking the loop

When CI is the only verification surface, the full pipeline is often too
slow a question. Two ways to ask narrower ones:

- **Dispatchable lanes** — a `workflow_dispatch` workflow with a mode input
  (typecheck-only, build-only, affected-only) answers one question in
  seconds. Two correctness guards: dispatch only after confirming the remote
  ref's SHA equals your local HEAD, and correlate the resulting run by head
  SHA plus dispatch-time window — display-title matching silently attaches
  to the wrong run.
- **A separate non-gating workflow** for visible-but-not-blocking checks
  beats a broad `continue-on-error`, which reports green while hiding a
  real failure inside a "passing" job.

Keep local checks to instant ones (formatting, lint on changed files, one
targeted test) and push everything heavy to CI; a cheap local guard for
whatever CI checks *first* prevents the most common self-inflicted red.

## Harness wiring

- Background single-completion (preferred when only the terminal verdict
  matters): run `ci-watch.py` as a background command; the harness notifies
  on exit; then read the `CI-DONE` line and branch on the exit code.
- Streaming (when first-red reaction matters): attach a monitor to the
  watcher's stdout. The output is already line-oriented, diff-gated, and
  rate-bounded — do not add extra filtering that could swallow `CI-DONE`.
- Never trust the exit code of a pipeline that post-processes the watcher:
  `ci-watch.py ... | head` reports `head`'s exit 0 even on a hard failure,
  because a pipeline's status is its last stage's. Capture output first
  (`out=$(...)`; `code=$?`) or check `${PIPESTATUS[0]}` in bash.
- Keep `--heartbeat` under the consuming model's prompt-cache TTL (the 120s
  default sits well below a typical ~5-minute TTL) so long waits stay cheap
  for an agent session.
- Always give the outer harness a timeout comfortably larger than
  `--deadline` (deadline + 120s is a good floor) so the watcher, not the
  harness, decides the verdict. An operator Ctrl-C still emits a final
  `CI-DONE` (`probe-dead`, reason `interrupted`, exit 2 — no verdict). A
  harness kill produces no `CI-DONE` and must be treated as "no verdict",
  never as failure or success.
