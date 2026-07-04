# Capturing screen state

Your senses. Pick the cheapest one that answers the question.

## 1. UI tree — `mobilerun device ui` (primary)

Text, exact pixel bounds, fast, no vision tokens. This is your default every iteration.

```bash
mobilerun device ui -d "$MR_DEVICE"
```

Output = a **phone-state header** then the **indexed element list**:

```
**Current Phone State:**
• **App:** Settings (com.android.settings)
• **Keyboard:** Hidden
• **Focused Element:** ''

Current Clickable UI elements:
'index. className: resourceId; checkedState, text - bounds(x1,y1,x2,y2)':
9. TextView: "android:id/title", "Network & internet" - (221,462,566,519)
```

Read the header first: it tells you **which app/screen you're on** (verify navigation), whether
the **keyboard is up** (did focus work?), and the **focused element** (did typing land?). Element
schema and clicking: `box-select-and-clicking.md`.

`scripts/mr-snap.sh` wraps `ui` + a saved screenshot and refuses to return a broken/empty tree, so
the tree you plan from is always a real one.

## 2. Screenshot + Read — vision

When you need layout, colors, images, a CAPTCHA-ish screen, or the parts of a screen the a11y tree
omits. You are multimodal — the `Read` tool renders the PNG visually.

**Web and Compose screens are usually *partially* exposed, not blank — so try `device ui` first.**
Chrome web pages surface their links, headings and form fields as elements with real bounds: on a
Google results page each result's title and URL come through as tappable `View`s you can tap
directly. Jetpack Compose apps often pack a whole unit into one node's description — a Reddit feed
post arrives as `"From r/x … 957 upvotes, 25 comments"` on a single `post_unit`. What the tree tends
to drop is loose body text (Reddit comment bodies, for instance, show up as an unnamed
`comment_body_tag` with no text). So the pattern is: snap, act on what the tree gives you, and reach
for screenshot+Read only to read the text it left out. A truly empty tree (games, custom canvases)
is the genuinely screenshot-only case.

```bash
shot=$(mobilerun device screenshot -d "$MR_DEVICE" | tail -1)   # prints a temp path
```
Then `Read` that path — the rendered PNG shows the real screen (Settings rows, Reddit posts, button
labels) clearly enough to reason about and tap by pixel.

**Screenshots land in a temp path the OS may reclaim.** That path is an ephemeral
`/var/folders/.../mobilerun_*.png`, so if you need it later — to compare before/after or refer back —
copy it somewhere stable first: `cp "$shot" /tmp/mr/keep_$(date +%s).png`. `mr-snap.sh` already does
this for you, copying into `/tmp/mr/<serial>/`.

Capture the path as the **last stdout line** — earlier lines may include an auto-setup notice.

## 3. Annotated boxes — `mr-snap.sh --boxes`

Screenshot with the numbered element boxes drawn on it (set-of-marks). Use to *show* the user
what's clickable or when a screen is visually dense. See `box-select-and-clicking.md`.

## 4. Raw JSON — `content query …/state_full`

Programmatic tree with full flags + phone_state. Use when you want to filter elements in code
rather than read them. See `box-select-and-clicking.md`.

## Decide quickly

| Question | Cheapest answer |
|---|---|
| "What can I tap and where?" | `device ui` |
| "Did my tap change the screen?" | `device ui` (compare header + key elements) |
| "What does this actually look like / no a11y tree?" | `screenshot` → Read |
| "Show me the clickable map" | `mr-snap.sh --boxes` → Read |
| "Is the keyboard up / what's focused?" | `device ui` header |

## Pitfalls

- **Empty or unchanged tree** → first confirm it's the *tree* that's empty, not your command: a
  real empty snap has no `Clickable UI elements` line, whereas a `cmd | grep` that printed nothing
  while the tree was fine only *looks* blank. A genuinely empty tree means a11y wedged or the app
  blocks it → re-run `mr-preflight.sh`, retry once; if still empty, switch to screenshot+Read and
  tap by pixel. A single transient empty usually fixes itself on the next snap — re-perceive before
  you escalate. The easy mistake is the *believed*-empty: a pipe swallowed the output while the tree
  was actually fine — far more common than a genuinely wedged a11y service. (`device-health-and-recovery.md`)
- **Stale snapshot** → anything that scrolls or navigates re-indexes the elements, so a snap from
  before the change describes a screen that's gone. Re-snap, then act on the new one.
- **Reading the screenshot path** → take it from the **last** stdout line (earlier lines can carry
  an auto-setup notice) and confirm it's a real file before relying on it, rather than trusting the
  exit code of a pipe.
