---
name: mobilerun-control
description: "Use if controlling or testing a connected Android phone via the mobilerun CLI — tap, type, swipe."
allowed-tools: Bash(mobilerun:*) Bash(adb:*) Read
---

# Mobilerun device control — you are the agent

`mobilerun` is your **hands and eyes** on a real phone. **You** are the brain. You read the
screen with `mobilerun device ui` / `device screenshot`, decide the next move with your own
reasoning, and act with deterministic `mobilerun device` commands. No cloud, no Gemini, no
`mobilerun run`, no API key — those are explicitly out of scope here.

Scripts live in `scripts/` next to this file; reference docs in `references/`. **Set two
variables once per session, before the loop** — the skill is invoked with the *project* cwd,
not this folder, so a bare `scripts/mr-preflight.sh` will `No such file or directory`. And because
each Bash call is a fresh shell (one command per call), no `cd` persists between calls to rescue a
relative path — so address scripts absolutely:

```bash
export MR_DEVICE=<serial>                       # find it with: mobilerun devices
export SKILL=<absolute path to this skill dir>  # the folder holding this SKILL.md
```

Then call every script as `bash "$SKILL/scripts/<name>"` — that's how the runnable blocks below
are written, so they work from any cwd. (Prose and tables name a script by its bare filename,
e.g. `mr-tap.sh`, purely for brevity.)

## The mental model

Six ideas make every other instruction in this skill obvious. Hold them and the right move usually
follows on its own.

1. **You are the agent.** The cloud path (`mobilerun run` / Gemini) needs an API key this setup
   doesn't have, so the intelligence is *you*: you read the screen, choose the next move, and issue
   one deterministic `mobilerun device` command at a time. There's nothing else deciding — every tap
   is yours.
2. **Act on the snapshot you just took.** The element list is rebuilt by a pre-order walk and
   renumbered on every UI change, so index 9 in an old capture is a different element now. The tap
   you're about to make has to come from the capture you're looking at: snap → act on *that* snap →
   snap again to see what happened.
3. **One command per call, and read its printed line.** Each Bash call runs a single `mobilerun`
   command so you can read its result — `Tapped (x,y)`, `Typed:`, the tree. Piping (`cmd | tail`)
   hands you `tail`'s exit code instead of mobilerun's, so a real error reads as success; trust the
   printed words, or `${PIPESTATUS[0]}` if you must pipe.
4. **Move like a person.** Pause between actions and aim a few pixels off dead-center. This reads
   human, and it's also more *correct*: the dwell lets animations and lazy lists settle before your
   next snap, and the offset avoids landing on an overlapping child element. `mr-wait.sh` and
   `mr-tap.sh`'s jitter do this for you.
5. **Compose outward steps, show them, then commit.** Anything other people or the account will
   see — posting, sending, commenting, buying, installing/uninstalling, signing out, a factory
   reset — you build up to and then *stop*, show the user, and submit only on their yes. A
   reversible setting you're just testing is different: change it, verify, and restore it yourself.
6. **Begin ready.** `mr-preflight.sh` resolves the device, rides out the USB settle, and re-asserts
   accessibility in the form the version check expects — the things that otherwise make the first
   command of a session fail. Run it once up front and the loop starts on solid ground.

**The through-line: perception before action.** Hold the six ideas above and one truth explains
them all — *almost every failure on this device is a perception failure, not an action failure.*
You rarely fail because you tapped the wrong pixel; you fail because you acted on a belief about the
screen that a fresh snap would have corrected. That belief takes four shapes, and naming the one
you're in hands you the fix:

- **Stale snapshot** — you act on a capture the screen already moved past; any scroll renumbers the
  tree. *Snap → act on that snap → snap again.*
- **Assumed location** — you act on where you *think* you are, not what the header says: `start`
  resumes a leftover screen, and a stray `back` can drop you into another app entirely. *Read the
  phone-state `activityName` before you act.*
- **Unconfirmed blank** — you read "no output" as an empty tree without checking the *snap itself*
  was empty; a swallowed pipe looks identical to a wedged a11y service. *Confirm the missing
  `Clickable UI elements` line before you believe it.*
- **Trusted doc** — you act on a documented shape, flag, or schema you never ran; docs drift, the
  device does not. *Run it once and read the real bytes.*

So when something doesn't work, your first move is not a different tap — it's a fresh snap, because a
surprising result is data about your perception before it is data about the device. The lone
exception is a *tool-contract gap*: when the command itself cannot express what you need (clearing a
field to empty), you fix the tool, not your looking — see `references/text-input.md`.

## The loop

```
0. SETUP (once):      export MR_DEVICE=<serial> ; export SKILL=<abs path to this skill dir>
   PREFLIGHT (once):  bash "$SKILL/scripts/mr-preflight.sh"     # ready + heals a11y/version/USB
   ── then repeat ──
1. CAPTURE:           bash "$SKILL/scripts/mr-snap.sh" [--boxes]   # indexed UI tree (+ screenshot, +numbered boxes)
2. DECIDE (you):      read the tree/screenshot; pick the target element by its TEXT/resourceId;
                      copy its bounds (x1,y1,x2,y2). When unsure of layout, Read the SHOT= PNG.
3. ACT:               bash "$SKILL/scripts/mr-tap.sh" --bounds "x1,y1,x2,y2"   # jittered box-center tap
                      bash "$SKILL/scripts/mr-type.sh" "text" [--clear|--human]   (focus the field first)
                      mobilerun device swipe … / press back|home|enter / start <pkg>
                      bash "$SKILL/scripts/mr-wait.sh" [read|think|MIN MAX]   # human pause between steps
4. VERIFY:            bash "$SKILL/scripts/mr-snap.sh" ; confirm the expected change appeared.
                      If nothing changed, retry the tap once; if it's still unchanged, re-plan from
                      the new snap rather than repeating the same tap.
```

Give the loop a budget: if the goal state isn't reached in ~15–25 capture→act cycles, stop and
report what you saw — a stalled plan is information, so re-plan instead of looping on.

## The box-select click system (the core mental model)

`mobilerun device ui` prints every on-screen element as:

```
Current Clickable UI elements:
'index. className: resourceId; checkedState, text - bounds(x1,y1,x2,y2)':
9. TextView: "android:id/title", "Network & internet" - (221,462,566,519)
34. Switch: "…/switchWidget", "Dark theme" ; isChecked=False - (859,1912,996,2038)
```

- The **bounds `(x1,y1,x2,y2)`** are absolute device pixels: `left,top,right,bottom`.
- The Portal can **draw these as numbered boxes** on screen (`mr-snap.sh --boxes`, or
  `adb shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:true`).
  The number in each box's **top-right corner matches the `device ui` index** — this is your
  set-of-marks. Use it when you (or the user) want to *see* what's clickable.
- To **click element N**: `center = ((x1+x2)//2, (y1+y2)//2)`, then tap (with jitter). `mr-tap.sh
  --bounds "…"` does the math + jitter — the same center mobilerun computes internally.
- Identify a target by its **text / resourceId**, not by a remembered number: the index is only
  meaningful in the snap it came from, so re-snap and re-find the element each time before you tap.

Full mechanics, overlap handling, raw JSON: `references/box-select-and-clicking.md`.

## Capture: which signal to use

| Need | Use | Why |
|---|---|---|
| Find tappable targets + exact bounds | `mobilerun device ui` (default) | cheap, text, precise pixels — your primary sense |
| Understand layout / images / a screen with no a11y tree | `mobilerun device screenshot` → **Read** the PNG | you are multimodal; Read renders the PNG visually |
| See *which* elements are clickable, visually | `mr-snap.sh --boxes` → Read the BOXES png | numbered overlay = set-of-marks |
| Programmatic raw tree | `adb … content query --uri …/state_full` | JSON with index/bounds/flags |

How to choose between them, and how to handle the temp-path screenshot: `references/capture-state.md`.

## Acting: primitives

| Action | Command | Notes |
|---|---|---|
| Tap element | `mr-tap.sh --bounds "x1,y1,x2,y2"` | jittered center; re-snap first |
| Tap raw point | `mr-tap.sh --xy X Y` | when you have pixels (e.g. from a screenshot) |
| Long-press | `mobilerun device long-press X Y` | context menus; not on iOS |
| Type / paste | `mr-type.sh "text" [--clear] [--human]` | **focus the field first** (tap, ~0.5s settle) |
| Scroll | `mobilerun device swipe 540 1700 540 700 --duration 0.4` | up-swipe scrolls down; re-snap after |
| Set a slider | tap its `Decrease`/`Increase` buttons, or a point along the track | `SeekBar` has no `isChecked`; verify by thumb-bounds shift |
| System buttons | `mobilerun device press back\|home\|enter` | back is 2-stage if keyboard is up; only these three |
| Launch app | `mobilerun device start <package>` | get packages from `device apps` |

Gestures, scrolling a list to find an item, paging: `references/navigation-and-gestures.md`.
Text entry, how the keyboard works on this device, atomic paste vs human typing: `references/text-input.md`.

## Stealth & looking human

Default to human cadence: `mr-wait.sh` between actions, `mr-wait.sh read` while "reading" a post,
jittered taps, natural scroll distances, and `--human` typing for anything a person authored
(comments, messages). See `references/stealth-and-human-pacing.md`. When you compose text a human
will be seen to have written, also read `references/writing-like-a-human.md` so it doesn't read
like an LLM.

## Planning any task

Decompose the goal into the loop above, expressed as concrete CLI steps before you touch the
device. Worked end-to-end plans (Reddit "read N posts then comment", Settings toggles, search-and-
open, multi-app flows) are in `references/task-planning-playbook.md`. Start there for any non-trivial request.

## Reference routing

| File | Read when |
|---|---|
| `references/task-planning-playbook.md` | Planning ANY multi-step task into CLI steps; worked examples. **Start here.** |
| `references/box-select-and-clicking.md` | Tapping elements: indices, bounds, center math, overlap, numbered boxes, raw JSON. |
| `references/capture-state.md` | Choosing/using `ui` vs `screenshot` vs raw state; reading the PNG; temp-path handling. |
| `references/text-input.md` | Typing/pasting; how the keyboard behaves on this device; clearing fields; special characters. |
| `references/navigation-and-gestures.md` | Scrolling, paging a list to find an off-screen item, back/home, switching apps. |
| `references/stealth-and-human-pacing.md` | Pacing, jitter, natural scrolling/typing, anti-bot-pattern hygiene. |
| `references/writing-like-a-human.md` | Composing comments/messages/posts that read human, not LLM. |
| `references/command-reference.md` | Exact CLI flags, Portal content-provider endpoints (query vs insert), bash discipline. |
| `references/device-health-and-recovery.md` | What preflight does and why; re-asserting accessibility, the version pin, USB-blip and empty-tree recovery, GrapheneOS specifics. Read when something degrades mid-session. |
