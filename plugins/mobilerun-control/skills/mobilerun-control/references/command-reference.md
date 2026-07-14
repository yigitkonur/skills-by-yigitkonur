# Command reference

Exact surface for deterministic control. (The natural-language `mobilerun run` agent and OAuth/
`configure`/cloud are intentionally omitted — you drive the device yourself, as the mental model in
SKILL.md describes.)

## `mobilerun device <sub>` (shared flags: `-d/--device`, `-c/--config`, `--tcp`, `--ios`)

| Sub | Args / flags | stdout on success | Notes |
|---|---|---|---|
| `screenshot` | — | the saved PNG **temp** path | the path is an OS temp file; copy it off `/var/folders` if you need it later |
| `ui` | — | phone-state header + indexed elements | your primary sense |
| `tap` | `X Y` | `Tapped (X, Y)` | ints, device pixels |
| `long-press` | `X Y` | `Long pressed (X, Y)` | ~1s; not on iOS |
| `swipe` | `X1 Y1 X2 Y2 [--duration S]` | `Swiped (..) -> (..)` | duration seconds, default 1.0 |
| `type` | `TEXT [--clear]` | `Typed: TEXT` | field must be focused first; `--clear` alone (no TEXT) blanks the field |
| `press` | `back\|home\|enter` | `Pressed <b>` | only these three |
| `apps` | `[--system]` | `pkg (Label)` per line | inventory |
| `start` | `PACKAGE` | `App started: …` | launch by package |

## Device / health commands

| Command | Use |
|---|---|
| `mobilerun devices` | list serials (`Found N connected device(s):`) |
| `mobilerun ping -d <s>` | readiness (`Portal is installed and accessible. You're good to go!`) |
| `mobilerun doctor -d <s>` | 14 checks + auto-fix (installs/enables); reverts Portal to the **compatible** version |
| `mobilerun setup -d <s> [--path APK] [--portal-version X] [--latest]` | install+enable Portal (**destructive — confirm first**) |
| `mobilerun connect <ip:5555>` / `disconnect <ip:5555>` | wireless adb over TCP/IP |

## Portal ContentProvider endpoints (`content://com.mobilerun.portal/<path>`)

**The verb is part of the endpoint.** Each path answers to one of `query` or `insert`, never both;
ask an insert-only path with `query` and it replies `Unknown endpoint`. Match the verb in the table.

| Path | Verb | Returns / effect |
|---|---|---|
| `state` | query | compact a11y_tree + phone_state JSON |
| `state_full` | query | full tree (all flags) + phone_state + device_context |
| `version` | query | Portal version string |
| `packages` | query | installed apps JSON (pkg, label, versionName, isSystemApp) |
| `auth_token` | query | bearer token for the TCP/HTTP API |
| `keyboard/input` | **insert** | type text: `--bind base64_text:s:<b64> --bind clear:b:<bool>` (paste primitive) |
| `overlay_visible` | **insert** | draw/hide numbered boxes: `--bind visible:b:<bool>` |
| `overlay_offset` | **insert** | shift boxes: `--bind offset:i:<px>` |

Example:
```bash
adb -s "$MR_DEVICE" shell content query  --uri content://com.mobilerun.portal/state_full
adb -s "$MR_DEVICE" shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:true
```

## TCP/HTTP transport (faster than ContentProvider)

`mobilerun doctor` shows the forward (e.g. `localhost:18080 -> device:8080`). With the `auth_token`:
```bash
adb -s "$MR_DEVICE" forward tcp:18080 tcp:8080
TOK=$(adb -s "$MR_DEVICE" shell content query --uri content://com.mobilerun.portal/auth_token | grep -oE '[0-9a-f-]{36}')
curl -s -H "Authorization: Bearer $TOK" http://localhost:18080/state_full
```
Pass `--tcp` to `mobilerun device …` to use this channel instead of ContentProvider.

## Bash discipline (so each command's result is trustworthy)

- **One `mobilerun` command per Bash call**, and read success from the printed line (`Tapped`,
  `Typed:`, the tree) rather than the pipeline's exit code — a pipe hands back the *last* stage's
  exit, so `mobilerun … | tail` reports `tail`'s success even when mobilerun errored. Pipe only when
  you must, and then read `${PIPESTATUS[0]}` instead of `$?`.
- One command per call also keeps each invocation matchable by the `Bash(mobilerun:*)` /
  `Bash(adb:*)` permission rules — in a compound `a && b` or `a | b`, *each* part must be allowed.
- **Quote globs**: `grep -rn 'pat' --include='*.py'` — an unquoted `*.py` throws "no matches" in zsh.
- **Reach for a heredoc on anything with quotes or escapes**: `python3 - <<'PY'` stays readable and
  correct where an inline `sed -n ",+45p"`/`awk` one-liner quietly breaks.
- `timeout 25 mobilerun device screenshot …` is still covered by `Bash(mobilerun:*)` (the
  `timeout`/`time`/`nice` wrappers are stripped before matching) — use it to bound hangs.
