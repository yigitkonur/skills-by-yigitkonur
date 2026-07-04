# Box-select & clicking

The deterministic targeting system: read indexed elements with bounding boxes, click one by the
center of its box. The formulas here are the same ones mobilerun uses internally, so a tap you
compute lands exactly where the CLI would put it.

## The element line

`mobilerun device ui` emits, under `Current Clickable UI elements:`:

```
'index. className: resourceId; checkedState, text - bounds(x1,y1,x2,y2)':
9.  TextView: "android:id/title", "Network & internet" - (221,462,566,519)
13. Switch: "com.android.settings:id/switchWidget", "Adaptive brightness" ; isChecked=True - (859,651,996,777)
```

- **index** — 1-based, assigned by **pre-order DFS** (parent before children) and recomputed on
  every capture, so a number only means something inside the snapshot it came from. Because the
  numbering is rebuilt each time, an index you remember from an earlier snap now points at a
  different element — re-finding the element by its text on a fresh snap before each tap is what
  keeps you from tapping the wrong thing (the single most common cause of a stray tap).
- **bounds `(x1,y1,x2,y2)`** = `left,top,right,bottom` in **absolute device pixels**
  (this device is 1080×2400). Indentation in the output = tree depth.
- **text** falls back through `text → contentDescription → resourceId → className`.
- **checkedState** appears only on checkable elements: `isChecked=True|False` — your toggle
  verification signal.

## Click formula

```
center_x = (x1 + x2) // 2
center_y = (y1 + y2) // 2
mobilerun device tap center_x center_y
```

`scripts/mr-tap.sh --bounds "x1,y1,x2,y2"` does this and adds human jitter (±6px, clamped inside
the box). To see it concretely: a Settings row at `(0,1639,1080,1831)` has center `(540,1735)`, and
tapping there opens the Display screen; a switch at `(859,1912,996,2038)` has center `(927,1975)`,
and tapping there flips it (watch `isChecked` go False→True to confirm).

Inline (no script):
```bash
b="859,1912,996,2038"; IFS=', ' read x1 y1 x2 y2 <<<"$b"
mobilerun device tap $(((x1+x2)/2)) $(((y1+y2)/2))
```

## Tap the right thing

- **Prefer the clickable row over its label.** A `TextView` title may not itself be clickable;
  its parent `LinearLayout` row (wider bounds, e.g. `(0,1639,1080,1831)`) is the tap target.
  When a center tap on a label does nothing, tap the enclosing row.
- **Overlap:** if a higher-index element overlaps your target, a dead-center tap can hit the
  wrong one. Aim at an un-covered quadrant of the box instead of the exact center (mobilerun's
  internal `get_clear_point` does the same). `mr-tap.sh` jitter usually sidesteps this; widen
  `--jitter` or pick a corner if needed.
- **Tiny/zero-size elements** (`<5px`) are filtered out and have no usable center — pick a
  meaningful parent.

## The numbered boxes (set-of-marks)

The Portal can **draw each element's box on screen with its index in the top-right corner**, in a
cycling 8-color scheme — a visual map of what's clickable. The overlay is a non-touchable
accessibility window, so it never blocks your taps.

```bash
# turn boxes ON / OFF — this is an insert endpoint, so use `insert` (a `query` here returns "Unknown endpoint")
adb -s "$MR_DEVICE" shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:true
adb -s "$MR_DEVICE" shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:false
# shift the boxes vertically if they sit high/low:
adb -s "$MR_DEVICE" shell content insert --uri content://com.mobilerun.portal/overlay_offset --bind offset:i:100
```

`mobilerun device screenshot` **hides** the overlay by default, so to capture an *annotated* image
you must use raw `screencap` while the overlay is on — exactly what `mr-snap.sh --boxes` does:

```bash
adb -s "$MR_DEVICE" exec-out screencap -p > /tmp/boxes.png   # captures the drawn boxes
```

Read that PNG to *see* the numbered targets; the numbers equal the `device ui` indices (both are
1-based pre-order). Use boxes when a screen is visually dense or you want to show the user what's
actionable. For actually tapping, work from the text tree — it's exact and needs no vision tokens.

## Raw JSON tree (when you want to parse, not eyeball)

```bash
adb -s "$MR_DEVICE" shell content query --uri content://com.mobilerun.portal/state_full
# -> Row: 0 result={"status":"success","result":{
#      "a11y_tree":{"resourceId":"","className":"android.widget.FrameLayout","text":"…",
#                   "boundsInScreen":{"left":0,"top":0,"right":1080,"bottom":2400},
#                   "isClickable":…,"children":[ …nested nodes… ]},
#      "phone_state":{…}}}
```
Confirm this shape by running the query once rather than trusting a remembered structure — a
documented schema is a claim; the payload on the wire is the truth. Note especially that bounds are
the `boundsInScreen` **object** below, not a flat `"l, t, r, b"` string — assuming the latter is a
*trusted-doc* slip.

Three things the formatted `device ui` view hides here:
- **`Row: 0 result=` prefix** — it's a ContentProvider row; strip it: `json="${raw#Row: 0 result=}"`.
- **`{"status":…,"result":{…}}` wrapper** — the tree and state live under `.result`.
- **`a11y_tree` is a single nested node** (root → `children[]`), not a flat indexed array, and
  bounds are an **object** `boundsInScreen:{left,top,right,bottom}` — not a `"l, t, r, b"` string.
  (Same numbers as the formatted `(l,t,r,b)`.) Nodes carry `isClickable/isCheckable/isEditable/…`
  flags; `phone_state` carries currentApp, packageName, keyboardVisible, focusedElement.
Over the TCP/HTTP channel (`/state_full`) you get the same `{status,result:{…}}` body **without**
the `Row:` prefix — see `command-reference.md`.
