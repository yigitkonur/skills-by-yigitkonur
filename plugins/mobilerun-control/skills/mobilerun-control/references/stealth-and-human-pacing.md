# Stealth & human pacing

Goal: actions that read as a person using their phone, not a script hammering coordinates. This
matters for reliability (apps animate, debounce, lazy-load) *and* for staying under the bot
heuristics consumer apps run. It's hygiene rather than evasion — it won't defeat real anti-fraud
systems, and it's not for mass-spamming, faking engagement, or evading a ban; keep within each app's
terms.

## The four habits

1. **Let time pass between actions.** Give each step a randomized gap with `scripts/mr-wait.sh`, and
   vary which dwell you use — a fixed interval is itself a machine signature, whereas the spread
   below looks like a person:
   - `mr-wait.sh` → 0.6–1.8s (between ordinary steps)
   - `mr-wait.sh think` → 0.4–1.2s (deciding / before typing)
   - `mr-wait.sh read` → 2.5–6.0s (dwelling on a post/article)

2. **Aim a little off-center.** Let your taps scatter the way a real finger does — `mr-tap.sh`
   offsets ±6px (clamped inside the box) for you. Besides reading human, the offset steps around an
   overlapping child element that a dead-center tap would catch (see `box-select-and-clicking.md`).

3. **Scroll the way a reader does.** Vary swipe distance and duration, mix a few short swipes with a
   longer one, and pause to "read" (`mr-wait.sh read`) between them. A column of identical swipes at
   a fixed cadence is the giveaway you're avoiding.

4. **Type authored text gradually.** A comment, DM, or post a person is meant to have written should
   arrive the way they'd write it — `mr-type.sh "…" --human` sends it in word chunks with randomized
   0.25–0.7s pauses, instead of the instantaneous full-string burst that reads as a paste. Atomic
   paste (`mr-type.sh "…"`) is the natural choice for search boxes and URLs, where pasting is what a
   person does anyway.

## Session shape

- Mix the texture of real use: interleave reading, small scrolls, and the occasional back-track
  rather than running a long row of identical actions.
- On a long session, drop in an occasional longer idle (`mr-wait.sh 8 20`), as if the user glanced
  away.
- Keep the rhythm irregular — calling `mr-wait.sh` between steps already does this, so the cadence
  never settles into a perfect period.

## Reliability bonus

These habits also fix real flakiness: the `mr-wait.sh` dwell after an action gives animations and
lazy-loaded lists time to settle, so your next snap reflects the true screen — which means fewer
"tap landed on the old layout" errors. Pacing is both camouflage and correctness.
