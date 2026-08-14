# Autonomous Mode — running unattended

When the user declares themselves away ("10 saat yokum", "sen devam et", "soru sorma"),
supervision changes shape. This file covers that mode.

The contract: **no questions, keep the worker moving, verify everything, don't stop until
the goal is genuinely met.** During an away window a question is worse than a
wrong-but-reversible decision, because a question stalls everything until they return.

---

## 1. What changes

| Attended | Autonomous |
|---|---|
| Ask via AskUserQuestion when the call is theirs | Decide, note the decision, report it later |
| Report after each round | Accumulate; report at the end or at checkpoints |
| Stop at an irreversible action for authorization | Use standing authorization if already granted; otherwise route around |
| Wait for direction when blocked | Resolve the blocker yourself from repo evidence |

What does **not** change: verification rigor, evidence discipline, and never running a
destructive command that wasn't authorized before the window started.

---

## 2. Set up the loop before anything else

Do this first, so the loop survives even if your current turn ends unexpectedly.

**Primary supervision loop** — every 30 minutes:

Use this only because your assistant turn ends and kills in-turn monitors. If Herdr wait or
a live socket watcher already covers the current attended slice, do not add this just because
it feels responsible.

```javascript
CronCreate({
  cron: "*/30 * * * *",
  recurring: true,
  durable: false,
  prompt: "Monitor the worker agent in pane <ID> completing <mission>. Use herdr agent get/read/wait/prompt. If idle with incomplete work, send a precise English continuation prompt. If blocked, resolve it autonomously from repo evidence — do not ask the user. Verify every completion claim independently (git, CI exact SHA, live probes, fresh browser evidence). Never print secrets. Continue until <explicit acceptance criteria>. The user is away: ask no questions."
})
```

**Backup watchdog** — on off-minutes, because `agent wait` can miss transitions:

```javascript
CronCreate({
  cron: "17 * * * *",
  recurring: true,
  durable: false,
  prompt: "BACKUP MONITOR for pane <ID> and the primary loop. Independently inspect agent state and recent output. Detect stalled/idle/blocked/contradictory progress the main loop may have missed. If incomplete and idle, send a continuation prompt; if blocked, resolve autonomously. Do not duplicate work while the agent is actively progressing. Ask no questions."
})
```

**Window-end audit** — a one-shot at the cutoff:

```javascript
CronCreate({
  cron: "<min> <hour> <dom> <month> *",
  recurring: false,
  durable: false,
  prompt: "The authorized autonomous window has ended. Audit whether the mission is genuinely complete against every original goal. If complete, verify independently, cancel the recurring monitors, and prepare a concise Turkish report. If incomplete, keep the monitors and continue autonomously without asking questions."
})
```

Compute the cutoff explicitly rather than eyeballing it:

```bash
date '+%Y-%m-%d %H:%M %Z'
date -d '+10 hours' '+%Y-%m-%d %H:%M %Z  dom=%d month=%m'
```

Tell the user, in the acknowledgement turn, which jobs you armed and their IDs.

---

## 3. The wait/peek rhythm

Between cron fires, the main loop is:

```
agent wait --until idle --timeout <ms>
   ├── settled  → read output, verify, next mission or close out
   └── timeout  → read a short tail, look for stall signals, wait again
```

A timeout is not a failure. See `supervising-agents.md` §4.

What to look for in each peek:

- the same line repeating across peeks → possible stall
- a hook-failure box → worktree hooks missing
- a task-list whose items never advance → stuck on one item
- a compaction banner → re-anchor the worker
- a "blocked" state → read the pane, resolve, unblock

---

## 4. Deciding without the user

Rank by reversibility:

**Decide freely** — which file to read, how to word a brief, whether to spawn research
subagents, how long to wait, which of two equivalent technical approaches to demand,
whether to reject a report.

**Decide, but record it prominently for the final report** — changing the order of
planned work, accepting a documented known-limit as not-a-defect, choosing a different
implementation approach after the first died, spending significant compute on
verification.

**Do not do it** unless authorization was already explicit before the window: deleting or
destroying resources, force-pushing, deploying to production, rotating credentials,
sending anything outward-facing, closing another pane or session.

If you hit a genuinely user-only decision with no standing authorization, do the reversible
part, leave the irreversible part undone, and surface it clearly at the end. Don't stall
the whole mission on it.

---

## 5. Answering the worker's questions

A `blocked` worker asking a question is not a reason to wake the user. Resolve it from:

1. the repo's own guides and runbooks
2. the code itself
3. git history — how was this decided before?
4. the mission's stated goal and acceptance criteria
5. the reversibility rule above

Then answer in the mission-brief voice: English, factual, with the evidence that justifies
your answer, so the worker doesn't re-litigate it.

---

## 6. Handling host and infrastructure blockers

Autonomous mode is where you'll meet these. Verify before acting — an error string is a
claim too:

```bash
df -h /    # disk bytes
df -i /    # inodes
```

Observed real case: a wait call surfaced `no space left on device`, but `df` showed 18%
usage and 20% inodes — transient. Deleting files based on that error would have destroyed
another session's work for nothing.

Rule: on a shared host, never clean up shared caches or temp trees to unblock yourself.
Verify, retry, and if it's genuinely real, report it rather than improvising.

---

## 7. Don't let the loop drift

Two failure modes specific to long autonomous runs:

**Goal drift.** After many rounds and possibly a compaction of your own, re-anchor: restate
the original goal and acceptance criteria, and check the work against them — not against
the most recent sub-task.

**Accepting late-stage claims more easily.** Verification standards tend to sag near the
end, exactly when the worker most wants to be finished. The last claim deserves the same
scrutiny as the first — in practice the most expensive false green of a campaign often
arrives in the final round, when everyone is tired and it's tempting to just accept it.

---

## 8. Closing the window

When the goal is genuinely met:

1. Run the pre-acceptance checklist in `verification.md` §14
2. Cancel every recurring monitor you armed (`CronDelete`)
3. Stop any background watchers or temp servers you started
4. Leave the worker's panes and worktrees alone unless you created them
5. Write the final report in the standard format, including:
   - what was completed, with evidence
   - every decision you made on the user's behalf
   - what is genuinely still open, and why
   - anything that needed authorization you didn't have

Optionally signal completion so they see it without watching the pane:

```bash
herdr notification show "Mission complete" --body "<one-line summary>" --sound done
```

---

## 9. Reporting after a long window

The user has been away for hours and will read one thing. Structure it as:

- the standard `Genel Durum` block — where things landed
- what was done, in rounds, briefly
- **the false greens you caught** — usually the most valuable part, and the thing that
  tells them how much to trust the worker next time
- decisions you made autonomously
- what remains open, separated into "needs you" vs "just not done yet"

Keep the voice. A ten-hour report written as a dry incident log will not get read.
