# Supervising a Worker Agent in a Sibling Pane

How the manager pane finds, drives, waits on, and recovers a worker agent in the same tab.
Project-agnostic. Pair with `herdr-reference.md` for the wider CLI surface.

---

## Quick reference

| Task | Command |
|---|---|
| Confirm you're inside Herdr | `test "${HERDR_ENV:-}" = 1` |
| Own identity | `printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"` |
| Find siblings in this tab | `herdr agent list`, filter by `tab_id == $HERDR_TAB_ID` |
| Snapshot one agent | `herdr agent get <target>` |
| Send a mission safely | heredoc to file, then `herdr agent prompt <target> "$(cat file)"` |
| Wait for settle | `herdr agent wait <target> --until idle --timeout <ms>` |
| Read output | `herdr agent read <target> --source recent-unwrapped --lines 120` |
| Diagnose `unknown` | `herdr agent explain <target> --json` |
| Nudge without a prompt | `herdr agent send-keys <target> <key>` |

---

## 0. Pick the topology before you spawn anything

The reflex to reach for an in-process subagent is usually wrong when Herdr is available. A
subagent lives inside *your* context window, dies when your turn ends, and leaves no
terminal the user can look at. A Herdr pane is a real, persistent terminal the user can
click, read, and take over.

Decide by two questions: **does it need repo isolation?** and **is it the same scope as
work already running?**

```
Needs its own branch / checkout?
├── YES → herdr worktree create      (branch + checkout + workspace + tab + pane, one call)
└── NO  → Same scope as this tab's work?
          ├── YES → herdr pane split          (sibling pane, same tab, shared context)
          └── NO  → herdr tab create          (separate view, same workspace)

Read-only research, no terminal needed, result consumed immediately?
└── in-process subagent is fine — that's what it's good at
```

| Situation | Use | Why |
|---|---|---|
| Parallel feature work that would collide on files | `worktree create` | Real branch isolation; agents can't stomp each other |
| A second agent on the *same* work you're supervising | `pane split` | Same tab, user sees both side by side |
| Logs / server / test-watcher alongside agents | `tab create` | Keeps the agent tab uncluttered |
| A long-running mission you'll come back to across turns | any Herdr pane | Survives your turn ending |
| One-shot read-only fan-out for ground truth | in-process subagent | No terminal needed; cheap and parallel |

The decisive question: **would the user ever want to look at this, or take it over?** If
yes, it belongs in a pane. Persistence and visibility are the whole point.

### Same scope → split a pane in this tab

```bash
split=$(herdr pane split --current --direction right --no-focus)
worker=$(printf '%s\n' "$split" | jq -r '.result.pane.pane_id')
herdr agent start reviewer --kind claude --pane "$worker"
```

`pane split` accepts `--direction right|down`, `--ratio FLOAT`, `--cwd PATH`, `--env
KEY=VALUE`, and `--focus`/`--no-focus`. Choose direction from the actual rectangle: split a
wide pane `right`, a tall one `down`. Check `herdr pane edges` first if unsure.

`agent start` **requires an existing shell pane at its prompt** — it never creates layout.
Supported kinds include `claude`, `codex`, `gemini`, `cursor`, `copilot`, `kimi`, `grok`,
`droid`, `amp`, `opencode`, and others. Arguments after `--` pass through unchanged. Startup
waits 30s by default; `--timeout` must be >3000 and ≤300000 ms.

### Isolated work → create a worktree

```bash
created=$(herdr worktree create --branch fix/thing --base main --no-focus)
path=$(printf '%s\n'  "$created" | jq -r '.result.worktree.path')
pane=$(printf '%s\n'  "$created" | jq -r '.result.root_pane.pane_id')
```

One call does branch + checkout + workspace + tab + root pane. Params (verified against
`herdr api schema --json`, `worktree.create`): `branch`, `base`, `path`, `cwd`, `label`,
`workspace_id`, `focus`. **Read the path back from the response — never hardcode one.**

`worktree remove` takes `workspace_id` (required) and `force`. It removes the checkout and
**never deletes the branch**. Use `worktree open` when the checkout already exists; the
response carries `already_open` so you don't duplicate a workspace.

Note: `herdr worktree <sub> --help` prints the top-level usage rather than subcommand help.
Use `herdr api schema --json` for exact params — it's authoritative.

Two checks immediately after creating a worktree, both learned the hard way:

1. `git log --oneline -1` in the new checkout — stale-base branching is a recurring worker
   mistake
2. Confirm `.claude/hooks/` exists if the repo configures hooks. Without it **every prompt
   into that pane is rejected** and the pane bounces straight back to idle (see §6.2)

### Creation responses — capture IDs, never predict them

| Command | ID lives at |
|---|---|
| `workspace create` | `.result.workspace`, `.result.tab`, `.result.root_pane` |
| `tab create` | `.result.tab`, `.result.root_pane` |
| `pane split` | `.result.pane` |
| `worktree create` | `.result.workspace`, `.result.tab`, `.result.root_pane`, `.result.worktree` |

Creating a workspace also creates its first tab and root pane; creating a tab creates its
root pane. Don't split immediately after creating — you already have a pane.

After `pane move` across workspaces the pane ID changes: continue with
`.result.move_result.pane.pane_id`. A wait already in progress ends with
`agent_not_running`.

Clean up only what you created. Never `herdr server stop` or `session stop` to reset a stuck
agent — those kill every pane on the box.

---

## 1. Discovery

Herdr injects identity into the manager's own environment:

```bash
test "${HERDR_ENV:-}" = 1 || { echo "not inside a Herdr pane"; exit 1; }
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

Then find the sibling — the agent whose `tab_id` matches yours and whose `pane_id` doesn't. This is the default target set for the skill; do not widen to other tabs/workspaces unless the current tab truly has no suitable worker or the mission explicitly needs another scope:

```bash
herdr agent list | python3 -c '
import json,os,sys
tab, me = os.environ["HERDR_TAB_ID"], os.environ["HERDR_PANE_ID"]
for a in json.load(sys.stdin)["result"]["agents"]:
    if a["tab_id"] == tab and a["pane_id"] != me:
        print(a["pane_id"], a["agent_status"], a.get("foreground_cwd"), sep=" | ")
'
```

Each entry carries `pane_id`, `tab_id`, `agent_status`, `cwd`, `foreground_cwd`,
`terminal_title_stripped`.

**Diff `foreground_cwd` against `cwd` on every read.** If the worker moved into a worktree,
`foreground_cwd` shows it while `cwd` still shows the original repo — this is the earliest
signal of the missing-hooks failure (§6.2).

`herdr pane layout --current` confirms tab membership spatially but carries no
`agent_status` — use `agent list` / `agent get` for lifecycle.

Note: `herdr pane list --tab <id>` is **not** a valid flag. Use `herdr pane list` and filter,
or `herdr pane layout`.

Always target an explicit pane ID. Omitting the target can act on another client's focused
pane.

### Proving the channel before you rely on it

The first time you drive an unfamiliar pane, prove the channel is real rather than an echo
of your own text. Send a nonce and read the ack back:

```bash
NONCE="ACK-$(od -An -N3 -tx1 /dev/urandom | tr -d ' \n')"
herdr agent prompt <target> "CHANNEL HANDSHAKE TEST (no code changes, reply only).
Reply with exactly one line and do nothing else — no file reads, no writes, no commands:
ACK $NONCE FROM <target> CWD=<your cwd>" --wait --timeout 180000
sleep 15
herdr agent read <target> --source recent-unwrapped --lines 40
```

If the nonce comes back verbatim, the channel is confirmed. Report that to the user with the
evidence, not just "it works".

---

## 2. Sending a mission prompt safely

**The failure that cost a full round:** a multi-paragraph prompt passed inline containing
backticks was interpreted by the *manager's own shell* as command substitution. The text
was consumed before `herdr agent prompt` ever ran; the worker got nothing, and nothing in
the return value said so.

Safe pattern — heredoc with a **quoted** delimiter, then pass the file contents:

```bash
cat > /tmp/mission-001.txt <<'MISSION_EOF'
Fix the loader so it validates on first run instead of silently defaulting.

Constraints:
- Root-cause first; instrument the boundary before patching.
- Report the exact command you used to verify, and its raw output.

This backtick example `echo test` must reach the agent literally.
MISSION_EOF

herdr agent prompt <target> "$(cat /tmp/mission-001.txt)"
```

The quoted delimiter is load-bearing. Unquoted, the shell expands backticks, `$(...)`,
`$VAR` and `\` *while writing the file* — so any command you quote for the worker turns
into its own output. Quoted, the body is literal.

Never build a prompt as a bare inline string with backticks. Never pipe it through `echo`
with interpolation.

---

## 3. Confirming the mission actually landed

`agent prompt` returning "sent" only means text was typed and submitted. Confirm pickup:

```bash
herdr agent prompt <target> "$(cat /tmp/mission-001.txt)"
sleep 15
herdr agent get <target>                                        # expect: working
herdr agent read <target> --source recent-unwrapped --lines 30  # expect: mission topic visible
```

If the tail still shows the *previous* turn's recap and status sits at `idle`/`done`
rather than `working`, delivery stalled — resend rather than assuming.

`--wait` requires an observed state change within ~5s of submission or it returns
`agent_prompt_stalled`. Useful, but the explicit check above is more reliable when the
terminal is slow to redraw.

---

## 4. The wait loop

```bash
herdr agent wait <target> --until idle --timeout 590000
```

On timeout it exits 1 with:

```json
{"error":{"code":"timeout","message":"timed out waiting for agent status"},"id":"cli:agent:wait"}
```

**A timeout is not a failure — it means the worker is still working.** This is the single
most important thing to internalise about long supervision. Treat it as "keep watching".

Sustainable loop — wait in bounded slices, peek briefly on each timeout:

```bash
TARGET=<pane-id>
while true; do
  if herdr agent wait "$TARGET" --until idle --timeout 590000 >/dev/null 2>&1; then
    break                                    # settled
  fi
  herdr agent read "$TARGET" --source recent-unwrapped --lines 25   # still working: glance
done
herdr agent get "$TARGET"
herdr agent read "$TARGET" --source recent-unwrapped --lines 200
```

Bounded slices (3–10 min) beat one giant wait: they let you spot a stall, a hook error, or
a compaction banner early without needing push events. For genuinely long unattended runs,
prefer the `events.subscribe` socket watcher in `herdr-reference.md` §B.

What to look for in each peek:

- the same line repeating across several peeks → possible stall
- an error or hook-failure box → §6.2
- a task-list footer whose items aren't advancing → worker may be stuck on one item
- a compaction banner → §6.4

---

## 5. Lifecycle states

| State | Meaning | What the supervisor does |
|---|---|---|
| `working` | Active turn | Keep waiting. Do not prompt again — a second prompt queues and confuses the turn |
| `idle` | Turn finished, prompt empty | Read output, verify claims, then next mission or close out |
| `done` | Settled before the tab was last observed | Treat like `idle` |
| `blocked` | Approval/question UI detected | Read the pane immediately, surface the exact question. Never blind-`send-keys` past it |
| `unknown` | Classifier uncertain | `agent explain <target> --json`. Does not prove completion either way |

Reading the pane footer helps too: a spinner glyph (`⠐`, `⠂`, `⠴`) in the title means
working; an empty `❯` prompt with a recap block above it means settled.

Chronic `unknown` on a supported agent kind usually means the matching integration isn't
installed — see `herdr-reference.md` §D.

### Why you almost always see `done`, never `idle`

`idle` and `done` are **the same underlying state**. The only difference is whether that tab
has been *seen*:

```
agent finishes its turn
   └─ tab focused in the Herdr UI, or `pane focus` / `agent focus` targeted it → idle
   └─ nobody looked at it yet                                                  → done
```

**Reading through the CLI does not mark it seen.** So a supervisor who only ever reads and
never focuses will observe `done` essentially forever — which is correct behaviour, not a
bug. Two consequences worth internalising:

- `--until idle` is the wrong default for an unattended supervisor. It can hang while the
  worker sits finished-but-unseen. Use the default settled set (`idle`, `done`, `blocked`),
  or name states explicitly: `--until idle --until done`. This exact mistake produced a
  spurious timeout early in one campaign — the prompt had landed, the agent had answered, and
  the wait was watching for a state that would never arrive.
- Don't "fix" it by calling `agent focus` to force `idle`. That steals the user's focus to
  satisfy your own wait condition.

`unknown` deserves its own caution: it means an agent is present but Herdr cannot classify it
confidently. It is **not** evidence of successful completion. `blocked` detection is
deliberately strict for screen-manifest agents — if no manifest rule matches, Herdr falls
back to `idle` and labels it `default_known_agent_idle_fallback` in `agent explain`. So a
novel approval prompt can surface as `idle` rather than `blocked`. When a worker looks
finished but the work plainly isn't, read the pane before believing the state.

Claude Code's state authority is the **screen manifest**, not lifecycle hooks — its
integration provides session identity for restore, not full lifecycle coverage. That is why
its state can lag a real transition, and why the pane text is the tiebreaker.

### Prompt and wait in one call, when it matters

`agent prompt --wait` submits immediately, then requires an observed lifecycle change within
five seconds or returns `agent_prompt_stalled`. A caller `--timeout` of five seconds or less
returns the ordinary timeout error instead. After activity is observed it waits for the first
requested settled status.

It does **not** track individual turns. If the agent was already working, completion of
*that* turn can satisfy your wait — so a `--wait` on a busy agent may return before your
prompt is even processed. When that ambiguity matters, wait for the settled state first, then
prompt.

At the socket level `agent.prompt` accepts a `wait` object (`until`, `timeout_ms`) so submit
and wait happen in one request, closing the race between two separate calls. `agent.wait`
pins the resolved pane occupant, so a replacement agent cannot satisfy a wait meant for the
one you were watching.

### Reading a full-screen agent's history

Claude Code renders its transcript in the terminal's **alternate screen**, not Herdr's
scrollback. For an idle, recognised agent sitting at the bottom of its transcript, a `recent`
or `recent-unwrapped` read with `--lines` larger than the visible screen makes Herdr drive
the agent's own scroll interface, collect overlapping pages, and return the viewport to the
bottom.

That only works when the agent is idle. `agent read --lines N` needing alternate-screen
history returns `agent_not_idle` while the agent is working, blocked, or unknown — wait for a
settled state and retry, or fall back to `--source visible`. Herdr will not move the viewport
for `visible`, `detection`, ANSI reads, output waits, subscriptions, a manually scrolled
agent, or a direct attachment.

If a long response still won't come back cleanly, ask the worker to write it as Markdown to a
temp path and reply with only that path, then read the file. That is the documented escape
hatch and it beats fighting the viewport.

---

## 4b. Real monitoring vs. the illusion of it

Calling `agent get` between your replies to the user is **not monitoring**. It feels like it
— you check, you see `working`, you say "nöbetteyim". But you are blind in every gap, and the
gap is where the worker dies. A real case: the worker hit `API Error: Server error
mid-response`, stopped, and sat idle for a long stretch while the supervisor reported active
watching. The user noticed first. That is the worst possible way to be caught.

Project-manager rule: before adding any watcher, answer this silently:
- what signal am I missing right now?
- does `agent wait` already cover it?
- does a socket subscription already cover it?
- am I adding this cron because I need survival across turns, or because I am guessing?

If you cannot answer, do not add another monitor yet.

Two layers, because on a harness that kills background processes at turn boundaries neither
one alone survives.

### Layer 1 — push subscription, during an active turn

Subscribe to lifecycle transitions **and** the exact error line, so a stop is signalled
rather than discovered:

```json
{"id":"watch","method":"events.subscribe","params":{"subscriptions":[
  {"type":"pane.agent_status_changed","pane_id":"<pane>"},
  {"type":"pane.output_matched","pane_id":"<pane>","source":"visible",
   "strip_ansi":true,"match":{"type":"regex","value":"^\\s*● API Error:"}}
]}}
```

Three failure modes worth not rediscovering:

- **Never send a second request down the subscription socket.** Adding a `pane.read` baseline
  call to fetch a revision number reset the connection outright
  (`ConnectionResetError: [Errno 104]`). That socket carries events; take state snapshots
  through the CLI on a separate connection.
- **Match on `visible`, not `recent_unwrapped`.** Scrollback matching re-fires on an error
  that happened an hour ago, and you cannot distinguish it from a fresh one.
- **Anchor the pattern.** A bare `API Error:` substring matches that phrase inside your own
  mission prompt — the watcher fired on text it had just sent. `^\s*● API Error:` binds to
  the terminal's own marker glyph.

Three protocol facts that shape how you read this stream:

- **`pane_id` is required on every subscription.** There is no wildcard; omitting it fails
  with `invalid_request` *and drops the connection*. Watch several panes by listing several
  entries in the same array.
- **Silence is not failure.** There is no keepalive or heartbeat — a healthy subscription
  can sit quiet for a long stretch. Never treat a quiet socket as a dead worker.
- **A disconnect loses events; there is no resume cursor.** After any reconnect, re-bootstrap
  with `herdr agent list` or `herdr api snapshot` before trusting incremental state.

After subscribing, take one CLI snapshot: the worker may already have settled before your
subscription opened, and the event for that transition is gone. (The socket-level
`events.wait` has the mirror-image property — it is level-triggered and returns immediately
when the pane is *already* in the requested state, so a match there never proves a fresh
transition.)

### Layer 2 — scheduler safety net, between turns

Harness-tracked background processes are killed when the assistant turn closes, so the push
watcher dies the moment you reply to the user. That gap is not theoretical — it is where a
stopped worker sits unnoticed. A `CronCreate` job covers it.

**Arm this whenever a worker will run past the end of your reply.** Not only in autonomous
mode: the moment you send a mission and then answer the user, Layer 1 is gone.

```
CronCreate(
  cron:      "*/30 * * * *"     # or "7,37 * * * *" — off-minute, see below
  recurring: true
  durable:   false              # session-only; dies with the session, which is correct
  prompt:    <the supervision instruction, written for a cold read>
)
```

Two rules for the cron expression. Pick an **off-minute** (`7,37` rather than `0,30`) so you
aren't landing on the same instant as every other scheduled job on the planet. And match the
period to how fast the thing you're watching actually changes: 30 minutes for a long build-out
mission, tighter only when a real signal justifies it.

The prompt is read by a future you with **no memory of this conversation**, so it has to
carry everything: the exact pane ID, the project, what "still working" looks like, what to do
for each terminal state, and an explicit instruction to stay silent while the worker is
`working`. A vague "check on the agent" produces a check that reports nothing useful and
wakes the user for no reason.

Before arming a second job, run `CronList` — duplicate watchers on one pane produce
duplicate `continue` sends, and two `continue`s into one agent queue up and confuse the turn.
Cancel with `CronDelete` when the mission closes; say in your report that you did.

The honest framing: this is a fallback for a process-lifecycle limit, not continuous
monitoring. Push events are the real mechanism. Say it that way rather than dressing the
poll up as something it isn't.

### The recovery policy

The distinction that matters is that `continue` is right for exactly one class of stop:

```
working                                 → silent, no user message
● API Error: Server error mid-response  → save evidence, send "continue", confirm working
idle / done                             → independently verify before relaying anything
blocked / unknown                       → read the pane, diagnose, escalate only if the
                                          decision is genuinely the user's
test or CI failure                      → never a blind "continue"
```

A blanket auto-continue buries a red test as if it were an upstream hiccup, which is worse
than not watching at all: it manufactures the appearance of progress. Save the visible pane
to a file on every event — when you are woken by a notification, that snapshot is the only
record of what the screen looked like at the moment things went wrong.

And when a watcher of yours breaks, say so in the report. A monitoring layer that silently
fails is indistinguishable from one that never existed.


---

## 6. Failure modes and recovery

### 6.0 Stray text in the input line corrupts the next mission

Before every prompt, clear the pane's input line:

```bash
herdr agent send-keys <target> ctrl+u
```

Anything left in the composer — a character the user typed and abandoned, a queued message,
a half-written sentence — gets **prepended to your mission** and silently changes it. This
has landed as a stray `f`, a stray `w`, and once an entire unsent instruction fused to the
front of a brief. The agent then does something subtly wrong and neither of you can see
why, because the pane shows the merged text as if you wrote it.

Two habits go with it:

- **Name the target once, at the start of the session**, so no later command depends on
  remembering a pane id: `herdr agent rename <pane-id> komsu`. The name follows the pane's
  occupant, survives your own context resets, and reads clearly in every transcript.
- **Watch the shell, not just the agent.** A mission containing something that looks like a
  CLI flag at the start of a line can be eaten by your own shell before it reaches Herdr.
  If a brief contains flags, send it from a file (§3) and read the pane back to confirm
  what actually arrived.

### 6.0b Choosing the read source by lifecycle state

Reading the wrong source wastes a round on an error instead of an answer:

| State | Source | Why |
|---|---|---|
| `working` | `--source visible` | Alternate-screen history can't be scrolled mid-turn; a large `recent-unwrapped` read is refused outright |
| `idle` / `done` | `--source recent-unwrapped` | Full transcript with soft wraps joined |

Reads never mark a tab seen, so you can watch continuously without moving the user's view.

### 6.1 Prompt queued but not picked up

Covered in §3. Symptom: status stays `idle`/`done`, tail shows no trace of the mission.
Fix: resend from file; verify `working` follows.

### 6.2 Worker in a worktree missing `.claude/hooks/`

The worker `cd`s into a worktree created without the repo's `.claude/` runtime. Every
subsequent `UserPromptSubmit` fails a hook lookup and **the prompt never reaches the
model**.

Detection:

- `foreground_cwd` points into a worktree path
- raw scrollback (`--source recent`, not `recent-unwrapped`) shows a hook-failure box right
  after a submitted prompt
- the pane snaps back to `idle` far too fast for a real turn, repeatably

Repair:

```bash
cp -a <main-checkout>/.claude/hooks/. <worktree>/.claude/hooks/
```

Then resend and confirm `working` follows instead of another instant bounce.

### 6.3 Host errors surfacing inside a wait call

A wait or prompt can surface a host-level error (`no space left on device`, inode
exhaustion) rather than a lifecycle timeout. **Verify before acting** — the error can be
transient, and deleting files on a shared host based on one error string is how you break
someone else's work:

```bash
df -h /    # bytes
df -i /    # inodes — ENOSPC-shaped errors are often inode exhaustion
```

If there's genuine headroom, it was transient: retry the wait. If it's real, surface it
rather than improvising cleanup on a shared machine.

### 6.4 Context compaction mid-mission

Detection: the footer's `ctx N%` drops sharply, a compaction banner appears, or the worker
starts re-deriving things it already knew — re-reading files, re-stating the goal, asking
about constraints already given.

Recovery: do not assume the brief survived. Send a short re-anchor (same file pattern as
§2) restating the goal, the definition of done, and the two or three hard constraints —
not the whole original mission. Then watch the next actions for constraint drift before
trusting any further "done".

### 6.5 The worker reverts its own work and declares it impossible

Observed: after three failed attempts at one approach, the worker reverted everything and
reported a blocker. Sometimes that's honest; often the *approach* was dead, not the goal.

Response: don't accept "impossible" without a failed probe attached. Supply a genuinely
different angle — a different interface, a different layer, an API instead of a UI — and
re-issue. Persist on the goal; retire the approach.

### 6.6 Wedged, not busy

A worker that is genuinely working changes *something*. A wedged one — usually stuck in an
API retry loop — looks identical to itself round after round, and the pane keeps rendering
a spinner the whole time.

The tell is a combination, never one signal alone:

```bash
date '+%H:%M:%S'
stat -f '%Sm %N' -t '%H:%M:%S' <files it should be touching>
herdr agent read <target> --source visible --lines 40
```

Wedged when **all three** hold: the pane's cost and elapsed counters read exactly what they
read at the previous checkpoint, no file it should be touching has changed for a long
stretch, and the tail shows the same frame. One `ctrl+c` recovers it, and a prompt you
queued while it was stuck runs on the next turn.

This is the one sanctioned exception to "never `ctrl+c` a running turn" in §7 — you are
not interrupting work, you are ending a loop that is not doing any.

### 6.7 Context exhaustion — reset rather than argue

Past roughly 70% context a worker starts losing track of what it already did. Observed: one
insisted a wave was uncommitted that had been committed hours earlier, and refused to
advance until it was "finished". Arguing with it burns rounds; its context is the problem,
not its reasoning.

```bash
herdr agent send-keys <target> ctrl+u
herdr agent prompt <target> "/clear"
```

Then re-brief with an authoritative state summary in four parts:

1. the workspace layout,
2. **what is already done and must not be redone** — with the commit ids and test counts
   *you* verified, not the ones it reported,
3. the current task,
4. the standing rules.

After a reset the same worker typically runs an order of magnitude cheaper and stops
second-guessing settled ground. Note that this is different from §6.4: there the worker
compacted on its own and you re-anchor what survived; here you decide to wipe it because
what survived is wrong.

### 6.8 The reviewer-fanout spiral

The most expensive failure mode observed, because it looks like diligence. The worker
spawns several background reviewers, each pins the file hashes it is reviewing, and then
the worker keeps editing. Every reviewer returns `TARGET_CHANGED` and cancels itself.
Nothing gets reviewed, hours burn, and the pane looks productive throughout.

Break it:

1. `ctrl+c` the current turn.
2. Confirm the tree is stable and the suite is green.
3. Freeze the file set and record the exact hashes **yourself**.
4. Launch exactly **one** review pinned to those hashes, instructed to return
   `TARGET_CHANGED` and stop if any hash moves.
5. Tell the worker to make no edits until that review returns.

The line to put in every brief: **one background reviewer at a time, and never pin a
reviewer to hashes while you are still editing.**

---

## 7. Supervisor etiquette

- **Never steal focus.** All discovery/read commands are focus-neutral. Don't call
  `agent focus` or `pane focus` unless the user asked for the view to move.
- **Never kill the worker.** No `pane close` on their pane, no `esc`/`ctrl+c` spam to
  interrupt a running turn, never `herdr server stop`.
- **Don't spawn duplicates.** Reuse the sibling that's already there. New panes/worktrees
  only when the task genuinely needs one — and with `--no-focus`.
- **Clean up only what you created.** Never remove the worker's pane, worktree, or session.
- **Every claim is unverified until you check it yourself.** A lifecycle event proves state
  changed, not that the work succeeded. See `verification.md`.
