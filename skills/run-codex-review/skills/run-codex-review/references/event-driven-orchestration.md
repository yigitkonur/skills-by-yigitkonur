# Event-Driven Orchestration (Phases 3, 5, 6, 7)

This skill is multi-hour and parallel. Main agent does NOT poll. It dispatches in parallel, sets up event sources (Monitor / Bash run_in_background / Agent run_in_background / ScheduleWakeup), goes idle, and reacts to notifications as they fire.

This file is the **single pinned spec** for which event source to use in which phase. Failure mode: dispatching N parallel things and then sitting in a Bash poll loop checking each. That defeats the parallelism and burns tokens.

## The four event sources

| Source | What it pushes | Use for |
|---|---|---|
| `Bash` with `run_in_background: true` | One notification when the command exits | One-shot "tell me when X completes" — codex review wrapper finishes; rescue job exits; build completes |
| `Agent` with `run_in_background: true` | One notification when the sub-agent hands back | Applier handback; PR-Creator handback; Evaluator handback |
| `Monitor` | One notification per stdout line; ends when command exits, timeout fires, or `TaskStop` | Streams of events — new PR comments arriving over 30 min; new file changes; log error stream |
| `ScheduleWakeup` (in `/loop` dynamic mode only) | Re-fires the `/loop` prompt after a delay | Idle-tick fallback when no signal exists to watch; pacing a self-driven loop |

**Picking the right one is mechanical, not aesthetic:**

- One notification ↔ Bash/Agent run_in_background.
- Stream of notifications ↔ Monitor.
- Sub-agent did the work ↔ Agent run_in_background (the dispatch IS the event source).
- Long-running shell command did the work ↔ Bash run_in_background (the exit IS the event).
- Want to wake yourself up later ↔ ScheduleWakeup (only valid in `/loop` dynamic mode; runtime clamps to [60, 3600]).

Never sit in a `while true; do …; sleep N; done` loop **inside the main agent's turn**. That blocks the runtime and burns tokens. Either dispatch via Bash run_in_background (which IS the loop, just owned by the harness) or use Monitor (which streams).

## Phase-by-phase canonical patterns

### Phase 3 — codex review + applier loop

**Per branch, per round, main agent runs:**

```
1. Bash(run_in_background=True): python3 scripts/run-codex-review.py --branch <b> ... --output <rounds-dir>/<slug>.<round>.json
   → notification: "Background command 'codex review: <branch>' completed"

2. (after notification) Read the round-log JSON, classify, evaluate per item via Skill(do-review) in own context.

3. If accepted decisions exist:
     Agent(run_in_background=True, prompt=<applier-brief-with-pre-decided-fixes>)
     → notification: "Agent 'Applier: <branch>' completed"

4. Repeat for round N+1 until terminal state.
```

**Anti-pattern**: launching 8 codex reviews via `Bash run_in_background`, then immediately launching 8 SEPARATE `Bash run_in_background` polling watchers (`until grep -qE "Reviewer (finished|failed)" ... ; do sleep 5; done`) to watch when each finishes. The codex review wrapper script itself exits when the review completes — the Bash run_in_background's own completion notification IS the signal you want. Don't double up.

**Anti-anti-pattern**: if the wrapper script is missing or doesn't reliably exit on terminal state, fix the wrapper. Don't paper it over with a polling watcher.

**Wall-clock cap**: codex reviews can hang on certain tools (e.g., remote codebase-search APIs returning slowly). The wrapper enforces `--timeout 1500s` by default; on hang it exits non-zero with `terminal_reason: "review-hang past wall-clock cap"`. Main agent treats as FAILED for that round; retries once; then surfaces.

### Phase 5 — PR creation (rate-limit-aware)

**N PRs to open. Pattern:**

```
1. Render N PR-Creator briefs from one template + per-branch JSON (see "Brief templating" in parallel-subagent-protocol.md). NEVER hand-write N separate briefs.

2. Throttle to ≤4 simultaneous PR-Creator dispatches.
   - GitHub's GraphQL budget is shared with `gh pr create` body uploads; opening 9 in parallel exhausts it.
   - The PR-Creator brief MUST instruct the sub-agent to use REST endpoints (`gh api repos/<owner>/<repo>/pulls -f title=... -f body=@<file> -f base=... -f head=...`) — not `gh pr create` (which uses GraphQL by default).

3. Dispatch first batch of 4 in parallel via Agent(run_in_background=True).
   → 4 handback notifications fire as PRs open.

4. As each handback lands, dispatch next from the queue.

5. When a handback says "rate-limited", main agent waits for the reset (gh api rate_limit returns Unix timestamp) via ScheduleWakeup(delaySeconds=<reset_in - now + 60>) if in /loop, or by deferring that PR's redispatch to the next round of completions.
```

**Anti-pattern**: dispatching all N in parallel and hoping for the best. Verified failure mode in production: 1+ of N rate-limits, agent has to retry-with-different-strategy.

**Anti-anti-pattern**: serializing all N. Phase 5 then becomes 9× ~5min = 45 min serial, when it could be ~3 batches × ~5min = 15 min throttled-parallel.

### Phase 6 — codex rescue + adaptive review window

**Per PR (after Phase 5 succeeded), main agent runs:**

```
1. Trigger codex rescue. In a programmatic loop, main agent invokes:
     Bash(run_in_background=True):
       node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task \
         --write --fresh --effort xhigh \
         "<comprehensive review prompt for PR #<n>>"

   This IS the same code path the /codex:resc slash command runs internally —
   /codex:resc dispatches a Codex sub-agent via the codex-companion.mjs task
   subcommand. In a programmatic loop, calling it directly is sanctioned.

   → notification: "Background command 'codex:rescue PR #<n>' completed"
       when the rescue review finishes posting to the PR.

2. Arm a Monitor (one per PR) that polls the PR's comments+reviews:

     Monitor(
       command='''
         pr=<n>
         repo="<owner>/<repo>"
         start=$(date -u +%s)
         seen_ids=""
         last_event=$start
         BASE_WAIT=900     # 15 min before first quiet-check
         QUIET_WINDOW=180  # terminate on 3 min of no new comments after base wait
         CAP=1800          # 30 min hard cap

         emit_new_items() {
           # Issue comments
           while IFS=$'\\t' read id user body; do
             [ -z "$id" ] && continue
             echo "$seen_ids" | grep -q "i$id" && continue
             seen_ids="$seen_ids i$id"
             last_event=$(date -u +%s)
             echo "PR #$pr [$user]: $(echo "$body" | head -c 200 | tr '\\n' ' ')"
           done < <(gh api "repos/$repo/issues/$pr/comments" --jq '.[] | "\\(.id)\\t\\(.user.login)\\t\\(.body)"' 2>/dev/null || true)
           # Review comments
           while IFS=$'\\t' read id user state body; do
             [ -z "$id" ] && continue
             echo "$seen_ids" | grep -q "r$id" && continue
             seen_ids="$seen_ids r$id"
             last_event=$(date -u +%s)
             echo "PR #$pr REVIEW [$user $state]: $(echo "$body" | head -c 200 | tr '\\n' ' ')"
           done < <(gh api "repos/$repo/pulls/$pr/reviews" --jq '.[] | "\\(.id)\\t\\(.user.login)\\t\\(.state)\\t\\(.body // "")"' 2>/dev/null || true)
         }

         # Initial seed pass (don't emit pre-existing comments)
         emit_new_items >/dev/null
         seen_initialised=1

         while true; do
           emit_new_items
           now=$(date -u +%s)
           since_last=$((now - last_event))
           total=$((now - start))
           # Termination: past base wait + 3min quiet, OR hard cap
           if [ $total -ge $BASE_WAIT ] && [ $since_last -ge $QUIET_WINDOW ]; then
             echo "PR-$pr-DONE quiet (no new comments in ${since_last}s, total ${total}s)"
             exit 0
           fi
           if [ $total -ge $CAP ]; then
             echo "PR-$pr-DONE cap (${total}s elapsed)"
             exit 0
           fi
           sleep 30
         done
       ''',
       description="PR #<n> review comments (codex/copilot/copilot-pr-reviewer/greptile/devin/cubic/human)",
       persistent=False,
       timeout_ms=2700000,   # 45 min hard ceiling
     )

   Each new comment fires one notification. The terminal "PR-<n>-DONE …" line
   fires the final notification, the script exits, the Monitor releases.

3. When the Monitor terminates with PR-<n>-DONE, main agent has all gathered
   review items. It dispatches a Phase 7 Evaluator sub-agent for that PR.
```

**Why this Monitor shape:**
- One Monitor per PR keeps termination independent — PR-A finishing doesn't cancel PR-B's wait.
- The seed pass populates `seen_ids` from existing comments without emitting them; only NEW arrivals fire notifications.
- The 30-second poll interval respects GitHub rate limits (≤120 req/hour per PR for issues+reviews; well within budget).
- Both `issues/<pr>/comments` (line-level) AND `pulls/<pr>/reviews` (review summaries) are polled — different bots use different surfaces (Copilot uses reviews, Devin uses comments, etc.).
- `|| true` after the `gh api` calls absorbs transient API failures without killing the monitor.
- The terminal `PR-<n>-DONE …` line is filterable downstream — main agent's reaction logic matches `^PR-\d+-DONE` to know "this PR is ready for Phase 7".

**Anti-pattern: per-event Monitor.** Don't arm a Monitor that emits ONLY the success line — silence equals "still running" equals "running forever". The pattern above emits one notification per actual comment AND a terminal line.

**Anti-pattern: skipping the base wait.** Bots often arrive at minute 13 (Greptile is famously slow). Quiet-detection starting at second 0 would terminate immediately on initial silence. The 900s base floor is non-negotiable.

### Phase 7 — Evaluator dispatch (one per PR, parallel)

After all Phase 6 Monitors terminate (or as each one terminates):

```
For each PR with completed Monitor:
  Read the PR's gathered comments+reviews (gh api dump → JSON file).
  Agent(run_in_background=True, prompt=<evaluator-brief-for-this-PR>)
  → notification: "Agent 'Evaluator: PR #<n>' completed"

Up to 9 Evaluators in parallel — they don't share rate limits with PR creation.
```

### Phase 8 — main agent direct apply

**No event sources.** Main agent is the actor; it reads each PR's evaluator JSON, applies accepted items via Edit, validates, pushes, merges. Sequential per PR (foundation→leaf), since merges affect downstream branches' bases.

The only event source in Phase 8 is **CI status** between push and merge:

```
After git push origin <branch>:
  Bash(run_in_background=True):
    until [ "$(gh pr checks <n> --json bucket --jq 'all(.[]; .bucket != "pending")')" = "true" ]; do
      sleep 30
    done
    gh pr checks <n>
  → notification when all checks land terminal state.
```

## ScheduleWakeup as fallback ticker

In `/loop` dynamic mode, `ScheduleWakeup` re-fires the `/loop` prompt after a delay. Use it as a **safety ticker**, not as the primary signal:

```
After dispatching all Phase 5 PR-Creators with run_in_background:
  ScheduleWakeup(
    delaySeconds=1200,   # 20 min — past 5-min cache TTL but amortized
    prompt="<the same /loop prompt this skill was invoked under>",
    reason="fallback wake in case any PR-Creator handback gets lost",
  )
```

The actual handbacks SHOULD fire well before 1200s; ScheduleWakeup catches the case where the harness drops a notification (rare but happens). When it fires, main agent re-checks state via the manifest and proceeds.

**Cache-window math** (load-bearing):
- Anthropic prompt cache TTL = 5 min (300 s). Wake-ups past 300s read full conversation context uncached.
- 60–270s = stays cached, cheap. Use for active polling near the action.
- 300s = WORST OF BOTH — pay cache miss without amortization. Never pick this.
- 1200–1800s = one cache miss buys a long wait. Use for idle ticks.

Don't think in round-number minutes. Think in cache windows.

## Combining sources — the canonical Phase 6 idle pattern

After dispatching N parallel codex:rescue jobs and arming N Monitors:

```
1. Bash run_in_background × N → each emits "rescue job <n> finished"
2. Monitor × N → each emits "PR #<n> [<user>]: <body>" per comment, then "PR-<n>-DONE …"
3. ScheduleWakeup (1200s in /loop, OR no-op if not in /loop) → safety ticker
4. Main agent ends turn.
5. Notifications fire over the next 15-30 min:
   - Rescue jobs complete (informational; the comment-poller catches their posted reviews)
   - Comments arrive (informational; appended to gathered-reviews JSON)
   - Monitor terminates with PR-<n>-DONE (signal to dispatch Phase 7 Evaluator for that PR)
6. Main agent dispatches Evaluator on each "PR-<n>-DONE" event.
7. Evaluator handbacks (Agent run_in_background) trigger Phase 8 apply for that PR.
```

Sub-100 lines of orchestration logic; main agent burns ~zero tokens during the wait windows.

## Common mistakes from production traces

| Mistake | Fix |
|---|---|
| 8 separate `Bash run_in_background` polling watchers (one per branch) duplicating the codex review wrapper's own completion signal | The wrapper's own exit IS the event. One Bash run_in_background per branch is enough. |
| Monitor that only emits the success line | Filter must cover failure too. Emit on every terminal state (comment, error, timeout). Silence ≠ success. |
| `Monitor(command='tail -f log | grep -m 1 "ready"')` for a single-event "tell me when ready" | Use Bash run_in_background with `until grep -q "ready" log; do sleep 0.5; done` instead. `tail -f` never exits on match; the monitor sits armed until timeout. |
| Hand-rolling N comment-poller commands inline in N Monitor calls | Render a parameterized poller from a template; pass `--pr <n>` args. (See `scripts/await-pr-reviews.py`.) |
| ScheduleWakeup(delaySeconds=300) | Worst of both worlds. Drop to 270 (cache-warm) or jump to 1200 (cache-miss-amortized). |
| Sitting in a `while …; sleep …` loop in the main agent's own turn | Blocks the runtime. Use Bash run_in_background or Monitor. |
| Per-PR Monitor + per-branch comment-poller-ALSO-as-Bash-run_in_background, doubling up | Pick one source per signal. Comments → Monitor. Rescue completion → Bash run_in_background. Don't duplicate. |
| Verbose status tables every turn ("Live state", "Phase X complete") | One sentence per phase boundary. The Final Deliverable in Phase 9 is the place for tables. |

## Bottom line

`run_in_background` for one-shot completions. `Monitor` for streams. `Agent run_in_background` for sub-agent handbacks. `ScheduleWakeup` (in /loop only) for fallback ticks with cache-aware delays. Combine all four; sit idle; react. Phases 5-8 are 4-7 hours of wall-clock that should consume ~15 minutes of main agent's actual work.
