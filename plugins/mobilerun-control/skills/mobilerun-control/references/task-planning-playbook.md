# Task-planning playbook

How to turn *any* phone request into a deterministic CLI plan you execute yourself. No cloud
agent decides anything — you do, one verified step at a time.

> Set `MR_DEVICE` and `SKILL` once before any of the flows below (see SKILL.md "Set two
> variables"); the `"$SKILL/scripts/..."` calls then run from any cwd.

## The method

1. **State the goal + done-condition.** "Read 10 posts in r/X then draft a comment on one" →
   done = a comment is composed in the field (and, only after user confirms, posted).
2. **Preflight.** `bash "$SKILL/scripts/mr-preflight.sh"` until it prints `ready`.
3. **Decompose into loop iterations.** Each iteration is CAPTURE → DECIDE → ACT → VERIFY. Write the
   iterations as concrete commands *before* touching the device, then adapt as the real tree comes back.
4. **Anchor on text, not coordinates.** Plan steps as "tap the element whose text is *Search*",
   then resolve the live bounds at execution time from a fresh `mr-snap`. Hardcoded pixels rot
   across screens, scrolls, and devices.
5. **Verify each step changed the screen the way you predicted.** If not, the mismatch is
   information about your *perception* first (stale snap? wrong screen?) — re-snap and re-plan from
   the new truth rather than re-firing the same tap.
6. **Gate the irreversible step.** Posting/sending/buying → compose, show the user, get a yes.

## Reusable sub-patterns

- **Open an app:** `mobilerun device start <pkg>` (find pkg via `mobilerun device apps`), then
  `mr-wait.sh read` for first paint, then `mr-snap`.
- **Tap a labelled control:** `mr-snap` → grep the tree for the label → `mr-tap.sh --bounds "<its bounds>"`.
- **Search inside an app:** tap the search affordance → snap → find the `EditText`/`AutoCompleteTextView`
  → tap it to focus → `mr-wait.sh think` → `mr-type.sh "<query>"` → `mobilerun device press enter`.
- **Scroll to find an off-screen item:** snap → if not present, `swipe 540 1700 540 700 --duration 0.4`
  → `mr-wait.sh` → snap → repeat, max ~8 swipes; stop if the tree stops changing (end of list).
  See `navigation-and-gestures.md`.
- **Dismiss a popup / permission dialog:** snap → look for `Allow`/`Not now`/`Close`/`✕` → tap it.
- **Wait for load:** prefer verifying via snap over fixed sleeps; add `mr-wait.sh` only for animations.

## Worked example A — Reddit: read 10 posts, then comment on one

This is the canonical "explore then author" flow, and it shows the outward-step rule in practice:
you go all the way to a composed comment and then stop for the user's go-ahead before submitting.

```bash
export MR_DEVICE=<serial>
export SKILL=<absolute path to this skill dir>   # so "$SKILL/scripts/..." resolves from any cwd
bash "$SKILL/scripts/mr-preflight.sh"

# 1. Open Reddit and land on a feed
mobilerun device start com.reddit.frontpage
bash "$SKILL/scripts/mr-wait.sh" read
bash "$SKILL/scripts/mr-snap.sh"            # confirm App: Reddit, find the feed

# 2. Read 10 posts. One "read" = bring a post into view, capture it, dwell, scroll.
seen=0
while [ "$seen" -lt 10 ]; do
  bash "$SKILL/scripts/mr-snap.sh" > /tmp/mr/feed.txt          # capture current posts
  # YOU read /tmp/mr/feed.txt: extract post titles / bodies now on screen.
  # (Optionally Read the SHOT= png for image posts.)
  bash "$SKILL/scripts/mr-wait.sh" read                         # human dwell, ~2.5-6s
  mobilerun device swipe 540 1750 540 650 --duration 0.45   # scroll one screen
  seen=$((seen+1))
  bash "$SKILL/scripts/mr-wait.sh"                              # 0.6-1.8s between scrolls
done
# You now have 10 posts' worth of content read off the successive snaps.

# 3. Pick ONE post worth commenting on, open it
bash "$SKILL/scripts/mr-snap.sh"                                # find the chosen post's title bounds
bash "$SKILL/scripts/mr-tap.sh" --bounds "<post title bounds>"  # open the post (comments view)
bash "$SKILL/scripts/mr-wait.sh" read
bash "$SKILL/scripts/mr-snap.sh"

# 4. Open the comment composer
#    Look in the tree for "Add a comment", "Comment", or a compose field at the bottom.
bash "$SKILL/scripts/mr-tap.sh" --bounds "<add-a-comment bounds>"
bash "$SKILL/scripts/mr-wait.sh" think
bash "$SKILL/scripts/mr-snap.sh"                                # find the comment EditText; confirm Keyboard: Visible

# 5. Compose a HUMAN comment (read references/writing-like-a-human.md first), focus + type human
bash "$SKILL/scripts/mr-tap.sh" --bounds "<comment field bounds>"
bash "$SKILL/scripts/mr-wait.sh" think
bash "$SKILL/scripts/mr-type.sh" "honestly had the same issue last week — turning off the cache fixed it for me" --human
bash "$SKILL/scripts/mr-snap.sh"                                # verify the text is in the field

# 6. STOP. Show the composed comment to the user. Only on explicit "yes":
#    tap the Post/Reply button (find its bounds from the snap), then verify it posted.
```

What you'll see on-device: opening Reddit lands on a feed (`App: Reddit (com.reddit.frontpage)`);
the toolbar search button and post titles appear in the tree with real bounds; scrolling
re-indexes the tree (so re-snap each loop); the comment field reports `Keyboard: Visible` +
`Focused Element` once focused. The post step is the only outward action, so it's the one you gate.

## Worked example B — Settings: turn ON Dark theme

```bash
bash "$SKILL/scripts/mr-preflight.sh"
mobilerun device start com.android.settings ; bash "$SKILL/scripts/mr-wait.sh"
bash "$SKILL/scripts/mr-snap.sh"                                  # READ the header activityName first!
# `start` RESUMES Settings wherever it was last (often a leftover search/sub-page), NOT the home
# list — so if you're not on the home screen, press back/home to a known state and re-snap. Then:
bash "$SKILL/scripts/mr-snap.sh" ; # grep the tree for "Display"; resolve ITS bounds from THIS snap
bash "$SKILL/scripts/mr-tap.sh" --bounds "<Display row bounds from this snap>"   # -> opens Display
bash "$SKILL/scripts/mr-wait.sh" ; bash "$SKILL/scripts/mr-snap.sh"        # find "Dark theme" Switch + isChecked
# read isChecked first; tap the Switch to flip it; verify it changed
bash "$SKILL/scripts/mr-tap.sh" --bounds "<Dark theme Switch bounds from this snap>"
bash "$SKILL/scripts/mr-snap.sh"                                  # confirm: Dark theme ; isChecked flipped
```
The `isChecked=True/False` on `Switch` elements is your verification signal for any toggle: read it
before and after the tap and watch it flip, rather than assuming the tap took. **Resolve each
element's bounds from the live snap** — the pixel boxes above are placeholders, not constants
(they differ by device/ROM/screen, and `start` may not even land you on the screen you expect).

## Worked example C — search-and-open in any app

```bash
# In an app with a search icon at a known toolbar position:
bash "$SKILL/scripts/mr-tap.sh" --xy 733 168            # search icon (or find its bounds via snap)
bash "$SKILL/scripts/mr-wait.sh" think ; bash "$SKILL/scripts/mr-snap.sh"
bash "$SKILL/scripts/mr-tap.sh" --bounds "<search EditText bounds>"   # focus
bash "$SKILL/scripts/mr-wait.sh" think
bash "$SKILL/scripts/mr-type.sh" "best mechanical keyboards"          # atomic paste for a query is fine
mobilerun device press enter
bash "$SKILL/scripts/mr-wait.sh" read ; bash "$SKILL/scripts/mr-snap.sh"       # read results, tap a result by its bounds
```

## When a step won't resolve

- Element not in the tree → it may be off-screen (scroll), or inside web/Compose content that only
  *partially* exposes a11y (Chrome web pages and Reddit posts DO surface links/summaries as
  elements, but some bodies don't) → snap first, then `screenshot + Read + tap by pixel` for the
  parts the tree omits. See `capture-state.md`.
- Tap did nothing twice → the element may be a non-clickable label; tap its clickable *parent row*
  (wider bounds) instead, or use `mr-tap.sh` on the row container.
- Screen unexpectedly different → a popup/interstitial appeared; snap, handle it, resume
  (`navigation-and-gestures.md` → Dialogs).
- The whole screen is a sign-in wall ("Sign in to continue", e.g. signed-out Play Store) → the
  feature needs an account, which is the user's to provide, so the task can't proceed here. Report
  it blocked ("needs sign-in") and move on, rather than tapping *Sign in* or looking for a way
  around. See `navigation-and-gestures.md` → Dialogs.
- A control with **no clickable label and no `isChecked`** (a `SeekBar` slider) → set it via its
  `Decrease`/`Increase` buttons or a track-position tap, and verify by the thumb bounds shifting.
  See `navigation-and-gestures.md` → Sliders.
