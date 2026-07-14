# Device health & recovery

What `scripts/mr-preflight.sh` does, why each part exists, and how to recover mid-session. Run
preflight once at the start of every session; return here when something degrades.

## Readiness, in order

1. **Resolve device** — arg → `$MR_DEVICE` → the single connected `device`.
2. **`adb wait-for-device` + a short re-detect loop** — the USB link blips for a moment during app
   launches and installs, so a command fired right after one can hit `device not found`. The loop
   waits for the link to come back so your first real command lands.
3. **ROM detect** — greps packages for `grapheneos`. This phone is GrapheneOS, a hardened ROM that
   gates accessibility more strictly, which is why the service has to be re-asserted explicitly
   (below) rather than left to auto-enable.
4. **Portal present + version** — confirms `com.mobilerun.portal` is installed and notes its
   version. The version you have is the compatible one on purpose (see the pinning section); there's
   nothing to upgrade.
5. **Re-assert accessibility** — the step that actually makes the session work (below).
6. **`mobilerun ping`** — the gate. Only `good to go` means ready.

## Accessibility: why the name format matters, and why it resets

Two mechanisms are worth understanding, because together they explain almost every "Portal not
enabled" surprise:

- **The name format.** The device can store the service under its **short** name
  `com.mobilerun.portal/.service.MobilerunAccessibilityService`, but mobilerun's readiness check
  substring-matches the **fully-qualified** name. When only the short form is stored the service is
  genuinely *running* (the tree works) yet `ping`/`doctor` say "not enabled" — they're matching the
  string, not the live service. Writing the fully-qualified form satisfies the check, so that's what
  preflight writes:
  ```bash
  FQ=com.mobilerun.portal/com.mobilerun.portal.service.MobilerunAccessibilityService
  adb -s "$MR_DEVICE" shell settings put secure enabled_accessibility_services "$FQ"
  adb -s "$MR_DEVICE" shell settings put secure accessibility_enabled 1
  ```
- **Why it resets.** `mobilerun setup`/`doctor` uninstall and reinstall the Portal APK when they
  update it, and that clears `enabled_accessibility_services` — so accessibility comes back off
  after any update. Re-asserting the name after a setup/doctor/update puts it back; preflight does
  this every run, which is why running preflight at the start of a session is enough to keep it healthy.
- **GrapheneOS extra:** auto-enable can be blocked entirely; if the FQ write doesn't take, open
  **Settings → Accessibility → Mobilerun Portal** by hand (you may first need to allow the app's
  "Restricted setting" via the ⋮ menu on its App info page). After that, preflight keeps it healthy.

Verify the service is truly working regardless of the label: `content query …/state_full` returning
an `a11y_tree` means it's up even if `ping` is grumpy about the name.

## Version pinning: the compatible Portal is the right one

`mobilerun 0.6.2` maps to a **compatible** Portal (currently **0.7.14**) through its version map,
and it keeps the device on that version on purpose. If a newer Portal is installed by hand (e.g.
0.7.15), `device ui`/`doctor` auto-download and **revert** it back to the pinned version, and a
`device screenshot` run during that swap may report `Portal auto-setup failed (outdated)`. So the
pinned version isn't a limitation to work around — it's the matched pair for this CLI:

- Install/keep the compatible version; a hand-installed `--latest` won't stick, because the CLI
  restores the pin.
- An "outdated/auto-setup" error on a single screenshot/ui call usually means a revert is in
  progress — run `mr-preflight.sh` and retry the call once, and it settles.

## Mid-session recovery

| Symptom | Recovery |
|---|---|
| `device '…' not found` / `Failed to list packages` | USB blip → `adb -s "$MR_DEVICE" wait-for-device`; re-run `mr-preflight.sh`; retry the action once |
| `ui` returns empty / identical tree repeatedly | first confirm it's the snap line that's missing, not swallowed stdout from a pipe; a genuinely empty tree means a11y wedged or app blocks a11y → preflight; if still empty, switch to screenshot+Read and tap by pixel |
| `ping` says not accessible but trees worked | the short-vs-fully-qualified name mismatch → re-write the FQ name (above) |
| screenshot errors "outdated/auto-setup" | a version revert is in progress → preflight, retry once |
| taps land but nothing happens | stale indices (re-snap) or you tapped a non-clickable label (tap the parent row) |
| keyboard won't accept text | see `text-input.md` IME section (enable Portal IME, type, restore) |

The Portal also self-recovers under load: the host retries state fetch with backoff and restarts
the accessibility service + TCP server after repeated failures. So a transient empty tree often
fixes itself on the next snap — retry once before escalating.

## Restart the Portal cleanly

```bash
adb -s "$MR_DEVICE" shell am force-stop com.mobilerun.portal
mobilerun device start com.mobilerun.portal -d "$MR_DEVICE"
bash "$SKILL/scripts/mr-preflight.sh"
```
