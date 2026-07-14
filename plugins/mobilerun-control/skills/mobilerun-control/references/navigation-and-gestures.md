# Navigation & gestures

## Launch / switch apps

```bash
mobilerun device apps -d "$MR_DEVICE"            # user apps: "pkg (Label)"
mobilerun device apps --system -d "$MR_DEVICE"   # + system apps
mobilerun device start com.reddit.frontpage -d "$MR_DEVICE"   # launch by package
```
Find a package by grepping `device apps` for the label (Reddit is `com.reddit.frontpage`, Settings
is `com.android.settings`). After `start`, give it a `mr-wait.sh read` for first paint, then snap.

**`start` resumes a running app where it left off — it doesn't reset it to a home screen.** If the
app was already open mid-flow, you land on the screen it was last showing; re-`start`ing Settings,
for example, reopens whatever sub-page it was on rather than the Settings home. So the first thing
after a `start` is a snap: read the phone-state `activityName` to learn where you actually are, and
if you need a known starting point, press `back`/`home` to walk to it instead of assuming the app
reset. (This is an *assumed-location* failure — see the perception through-line in SKILL.md.)

Rich inventory with versions/system-flag (JSON):
```bash
adb -s "$MR_DEVICE" shell content query --uri content://com.mobilerun.portal/packages
```

## System buttons

```bash
mobilerun device press back     # also closes keyboards/dialogs
mobilerun device press home     # to launcher
mobilerun device press enter    # submit a focused field / confirm
```
Only these three are supported; `back` steps up one screen (and from a top-level screen, out to the
home list), `home` goes to the launcher.

**When the keyboard is up, `back` retracts it first.** A Back press is consumed by the most
transient thing on screen, and an open IME is more transient than the screen under it — so if the
header shows `Keyboard: Visible`, the first `back` just hides the keyboard and leaves you on the
same screen with your text intact. Re-snap to see this: once `keyboardVisible` is false but you're
still on the same screen, a second `back` is what actually leaves it. Reading that first
unchanged-but-keyboardless snap as "back failed" and re-tapping is the trap to avoid — it was
working, it just had the keyboard to clear first. (In WhatsApp's text editor: back #1 hid the
keyboard, back #2 left the editor.)

## Scrolling

A swipe **from lower y to higher y scrolls the content DOWN** (reveals what's below):

```bash
mobilerun device swipe 540 1750 540 650 --duration 0.45 -d "$MR_DEVICE"   # one screen down
mobilerun device swipe 540 650 540 1750 --duration 0.45 -d "$MR_DEVICE"   # one screen up
```
- Center-column x (≈540 on a 1080-wide device) avoids side drawers.
- `--duration` ≈ 0.3–0.6s reads natural; very fast swipes can fling unpredictably.
- **Re-snap after every scroll** — a swipe shifts the element list, so the indices renumber.

### Scroll to find an off-screen item

```bash
target="Privacy"
for i in $(seq 1 8); do
  ui="$(mobilerun device ui -d "$MR_DEVICE")"
  printf '%s\n' "$ui" | grep -qiF "$target" && { echo "found"; break; }
  prev_count="$(printf '%s\n' "$ui" | grep -c '^[0-9]')"
  mobilerun device swipe 540 1750 540 650 --duration 0.45 -d "$MR_DEVICE"
  bash "$SKILL/scripts/mr-wait.sh"
  new_count="$(mobilerun device ui -d "$MR_DEVICE" | grep -c '^[0-9]')"
  # end-of-list guard: if the tree stopped changing, stop scrolling
  [ "$new_count" = "$prev_count" ] && { echo "reached end without finding $target"; break; }
done
```
Cap the scroll count (here 8) so a missing item ends the search instead of scrolling forever, and
stop early when the element count stops changing — equal counts across a swipe mean the list didn't
move, i.e. the bottom (or a screen that doesn't scroll). If scrolling *seems* to do nothing, first
confirm from the header you're still in the target app: a stray earlier `back` can leave you in the
launcher's app drawer, scrolling the wrong screen and wrongly concluding the loop is broken (an
assumed-location trap).

## Horizontal swipes / carousels

```bash
mobilerun device swipe 900 1200 200 1200 --duration 0.4 -d "$MR_DEVICE"   # swipe left (next)
mobilerun device swipe 200 1200 900 1200 --duration 0.4 -d "$MR_DEVICE"   # swipe right (prev)
```

## Sliders, steppers & SeekBars

A `SeekBar` (volume, brightness, font/display size) is set by *position*, not by tapping a label, so
it's handled differently from a row or a switch. Two ways, in order of reliability:

1. **Reach for the discrete +/- buttons when they exist.** Many sliders are bracketed by
   `Decrease …`/`Increase …` icon buttons whose bounds sit just left and right of the track; tapping
   one moves the slider exactly one step, which is the most precise way to set it. On Settings →
   *Display size & text* → *Font size*, those are `Decrease font size` (84,1553,210,1679) and
   `Increase font size` (870,1525,996,1651) — one tap on Increase steps the size up, one on Decrease
   brings it back.
2. **Otherwise tap a point along the track.** For a track with bounds `(x1,y,x2,y)`, tap
   `x = x1 + (x2-x1) * fraction` at the track's mid-`y` (e.g. 70% → `x1 + 0.7*(x2-x1)`). This is
   coarse, so re-snap and nudge toward the value you want.

**Confirm the change by the thumb, since a slider has no `isChecked`.** The inner `SeekBar` (the
thumb) has its own bounds, and they shift along the track as the value changes — that shift is your
confirmation. Some sliders also state the level in their description, like Display size's
`SeekBar: "Value, 1"`. Stepping Font size up once, for instance, moves the thumb from
`(295,1525,421,1651)` to `(386,1553,512,1679)`, and a Decrease tap returns it to `(295,…)` — read
those bounds before and after rather than assuming the tap landed.

## Long-press (context menus, selection, drag-start)

```bash
mobilerun device long-press 540 1200 -d "$MR_DEVICE"    # ~1s hold; not supported on iOS
```
Snap afterward to read the context menu that appears, then tap an option by its bounds.

## Dialogs, permissions, interstitials

Apps interrupt flows with permission prompts, rating nags, and "What's new" sheets. After any action
that might trigger one, snap and clear it before resuming the plan — the dismiss control is usually
labelled `Allow`/`While using the app`/`Not now`/`Cancel`/`Close`/`Skip`/`✕` (Chrome's "Set as
default browser?" dialog, for instance, clears via `Cancel`).

- **When there's no dismiss button in the tree**, you're looking at a coachmark, tooltip, or a
  one-time "added to Quick Settings" popup that exposes only its text. A `back` clears these too, or
  tap a point clearly *outside* the popup's bounds — a font-size Quick-Settings coachmark with no
  button clears with a single `back`.
- **A sign-in wall is a stopping point, not a dialog to clear.** When the whole screen is a
  login / account-required wall — Play Store's `UnauthenticatedMainActivity` showing only a *Sign in*
  button is the clearest case — the feature simply isn't available without an account, and entering
  one is the user's call (it's an outward, user-only action). So the right move is to report it as
  blocked ("<app> needs sign-in") and move on, rather than tapping *Sign in* or hunting for another
  way through.
