---
name: run-agent-device
description: "Use if testing or debugging an iOS app via agent-device CLI — simulator flows, evidence, bug triage."
allowed-tools: Bash(agent-device:*)
---

# run-agent-device — iOS product testing

Drive the installed `agent-device` CLI as a serial REPL against an iOS simulator or device: run one command, read its full output, decide the next command from what it actually said. You are testing a *product*, not just a screen — most "UI bugs" you will find live in another layer (dev server, app code, backend, environment), and this skill's job is to keep you from fixing the wrong one.

**Not this skill:** Android-first device control (use `mobilerun-control`), web/browser automation (use `run-agent-browser`), authoring XCTest/unit tests, or App Store release operations. agent-device *can* drive Android and web, but this skill's guidance is iOS-product-testing shaped.

## Authority order — the CLI's help wins

agent-device ships version-matched instructions. When syntax or behavior is uncertain, ask the tool, not your memory:

```bash
agent-device --help                # command list + agent quickstart
agent-device help workflow         # full operating reference (the big one)
agent-device <command> --help      # exact flags for one command
agent-device --version
```

Route by task before starting:

| Task smells like | Read first |
|---|---|
| Follow a written test script / acceptance checklist | `agent-device help manual-qa` |
| Explore the app and report issues with evidence | `agent-device help dogfood` |
| Prove a code change / perf fix / regression on-device | `agent-device help validate` |
| Logs, network, alerts, traces, crashes, flaky failures | `agent-device help debugging` |
| App is React Native / Expo / dev client | `agent-device help react-native` + [references/dev-loop-react-native.md](references/dev-loop-react-native.md) |
| Component props/state/renders/rerenders | `agent-device help react-devtools` |
| JS heap growth / leak proof | `agent-device help cdp` |
| Physical iPhone/iPad, signing setup | `agent-device help physical-device` |

If this file ever conflicts with the installed CLI's current help, the CLI wins; fix this skill afterward.

Full annotated command surface (all 65 subcommands, grouped, with when-to-use): [references/command-map.md](references/command-map.md). Read it once per session instead of running `--help` per command.

## Session start

```bash
agent-device devices --platform ios          # pick target; --device "iPhone 17 Pro" only if several
agent-device open <AppName-or-bundle-id> --platform ios
agent-device snapshot -i                     # interactive refs for the first action
```

- `open` without `--relaunch` foregrounds an already-running app without restarting it. Use `--relaunch` when the test needs fresh process state ("start from the home screen").
- Unknown app id → `agent-device apps`, then open the discovered id. Never invent bundle ids or open artifact paths.
- Run `doctor` only when something fails or the user asks for setup diagnostics — it is not routine prep.
- Sessions: stateful commands run **serially** in one session. Parallelize only read-only commands or separate sessions/devices. If a prompt names a session, put `--session <name>` on every command in that flow.
- `close` when done. The iOS XCTest runner stays warm ~5 min after close, so consecutive opens are cheap.

## Core interaction loop

1. `snapshot -i` → refs like `@e12`, plus `[off-screen below]` scroll hints.
2. Act with `press` / `fill` / `click` / `longpress` `<@ref|selector|x y>` **`--settle`** on every mutating action that supports it.
3. The settled diff **is** your next observation. Do not add `wait stable` or another snapshot when the diff already shows the next target. If it prints `not settled`, follow its hint before the next ref-based action.
4. Verify named expectations with `wait text "…"` / `wait <selector>` / `is` / `get` / `find` — a bare screenshot or snapshot is **not** verification of a named expectation.
5. Refs go stale after any mutation, and `open`/`--relaunch` invalidates all of them. After a mutation, prefer a known selector (`press 'label="Send"'`) or refresh with `snapshot -i` (scope with `-s "Container"` when possible).

Targets: `@e12` refs from the *latest* snapshot/settle output, or selectors — `id="submit"`, `label="Search"`, `text="…"`, `role=button label="Follow"`. Never CSS selectors, never placeholder refs like `@eN` in a plan. Ambiguous selectors auto-resolve (deepest node, then smallest area) — add `id=` or longer text to force a different match. Labels containing apostrophes are shell-quoting hazards; prefer the @ref.

Text entry: `fill <target> <text> --settle` **replaces**; `type <text>` **appends** to the focused field (autoFocused fields are already focused — `fill` there replaces the whole value, which is usually what you want). `fill <target> ""` is not a supported clear — use a visible clear control or report the gap. Keyboard on screen usually does not block taps: press the next target directly; only `keyboard dismiss` when hiding it is the actual goal.

Coordinates are last resort: after refs/selectors fail or accessibility omits the target, get rects with `snapshot -i --json`, press the center, verify with `diff snapshot -i`, and say why you used coordinates. Avoid screen edges, tab bars, and the home-indicator zone — they trigger system navigation.

Waits: `wait text "…" [timeoutMs]` polls every 300 ms (default timeout 10 s) and **fails loudly on timeout** — that failure is signal, not noise. Network-backed results can land after the settle window; follow the settled action with an explicit `wait text`/`wait <selector>` for server-loaded content.

## The product-test loop

When the task is "test the app / features end to end, fix what breaks":

1. **Tour** one feature at a time against a coverage list you maintain (screens, flows, edge states). Capture baseline `snapshot -i` + `screenshot <path>` on entry.
2. **Bug found → stop touring.** Capture evidence *now* (screenshot, `network dump`, `logs path`, exact repro commands), then root-cause before writing any fix — see the triage table below and [references/bug-triage.md](references/bug-triage.md).
3. **Fix at the root layer**, not the symptom layer.
4. **Refresh the right runtime** — the fix does nothing until the running code actually contains it (next section).
5. **Retest from adequately fresh state** (state matrix below), reproducing the *original* symptom path — not just re-reading the diff.
6. **Resume the tour where you left off**; re-run any flow your fix could have invalidated.

Rules that keep this loop honest:

- **Every failure is new.** After fixing cause #1, the next run may fail for a *different* root cause behind the same symptom. Re-read the actual error text every retry; never assume "same bug."
- **Three failed fixes on one symptom → stop patching.** Re-derive the root cause from fresh evidence (logs, network, backend state); the approach is dead, not the goal.
- **Claim only the rung you reached.** "Fix deployed" ≠ "bug gone." The bug is gone when the original repro path passes live, on-device, from fresh state.

## Layer triage — where the bug actually lives

Empty screens, wrong data, and dead buttons are usually not screen bugs. Probe cheapest-first:

| Symptom | First probe | Likely layer |
|---|---|---|
| Empty list/feed/dashboard, spinner forever | `network dump --include headers` — did the request fire? status? body? | Backend or auth, not UI |
| Tap "succeeds" but nothing changes | settled diff / `diff snapshot -i`; check response for `targetHittable: false`; `snapshot -i` for overlays sitting on top | Overlay interception or wrong target |
| Fix applied but behavior identical | Prove the running app contains the new code (below) | Stale runtime |
| Data appears but is wrong/stale | `network dump --include body`, then query the backend directly (curl/DB) with the *current* user's identity | Backend logic or wrong-user assumption |
| Works once, fails on repeat | Server-side state from the earlier run (idempotency keys, created records) | Test-state pollution |
| Crash / hang / RN red screen | `logs clear --restart` → repro → `logs path`; `react-native dismiss-overlay` for LogBox; `debug symbols` for crash artifacts | App code |
| Permission sheet blocks flow | `alert get` → `alert accept|dismiss`; if "no alert" but sheet visible, it's app-owned UI: `snapshot -i` + press by label | Platform dialog vs app sheet |
| Snapshot sparse / AX unavailable | `screenshot` as visual truth, coordinate-nav off the bad screen, retry `snapshot -i` | Screen-specific AX gap |

Full playbook with backend-probe patterns, current-user identification, and async-job polling: [references/bug-triage.md](references/bug-triage.md).

## Runtime freshness — the #1 false-negative source

"My fix didn't work" is, more often than not, "the running app never executed my fix." Before debugging logic, prove freshness:

- **JS change (React Native/Expo):** `agent-device metro reload` — but first confirm *which* Metro serves this app: which project root, which worktree, which port. A dev client happily loads JS from a different checkout than the one you edited. `agent-device doctor` reports dev-server reachability; `lsof -iTCP:8081 -sTCP:LISTEN` + the process cwd tells you whose Metro it is. Editing repo A while Metro serves repo B burns hours.
- **Native change:** Metro reload cannot deliver it. Rebuild/reinstall the binary, then `open --relaunch`.
- **Backend change:** the app talking to a deployed backend needs that backend *redeployed* (and env vars synced, if the platform snapshots them at deploy time) before on-device retesting means anything.
- **Still unsure?** Add a temporary visible marker (a log line or on-screen string) to the changed code and confirm it appears at runtime. One minute spent here saves a false "fix didn't hold."

RN/Expo specifics (Metro truth, Expo Go vs dev client opens, reload-vs-relaunch-vs-rebuild): [references/dev-loop-react-native.md](references/dev-loop-react-native.md).

## Fresh-state matrix

"Fresh" has independent levels — pick deliberately per retest; onboarding/auth flows usually need all of them:

| Level | Command | Resets |
|---|---|---|
| Foreground | `open <app>` | Nothing (idempotent foreground) |
| Process | `open <app> --relaunch` | In-memory state only |
| Local storage | `settings clear-app-state [app-id]` | Keychain-adjacent app data, caches, onboarding-done flags |
| Server account | In-app sign-out, or a new (anonymous) account | Server-side user state |
| Permissions | `settings permission reset <service>` | Prior grant/deny decisions |

Watch-out: repeated fresh-account runs create *many* server-side users. When probing the backend, identify the current run's user from evidence (newest `created_at`, device id, a value you just typed) — never assume the record you're looking at belongs to the run you're testing.

## Evidence and reporting

- Screenshots to named paths per finding: `screenshot ./out/issue-001.png`; add `--overlay-refs` when showing the tappable target matters.
- Log windows small: `logs clear --restart` → `logs mark "before X"` → repro → `logs path`. Never cat a full stale log into context.
- Network: `network dump --include headers` (or `body`/`all`) — this is the request/response evidence, better than log spelunking.
- Video for interactive repros: `record start ./out/issue.mp4` … `record stop`; `--hide-touches` for gesture-heavy captures.
- Perf: `perf metrics --json` first pass; `perf frames --json` for jank; artifacts (heap, traces, profiles) stay on disk — report path + size, never paste raw dumps.
- While exploring, do **not** pipe agent-device output through `grep`/`jq`/`head` or add `2>/dev/null` — raw output carries refs, warnings, and hints your next step needs.
- Report per finding: severity, affected flow, exact repro commands (real refs/selectors, no placeholders), expected vs actual, evidence paths, and the *layer* of the root cause. If nothing was found, report coverage and residual risk — not "bug-free."

## Hard-won rules (each of these cost real time once)

| Do this | Not that |
|---|---|
| Prove the running app contains your fix before retesting the symptom | Assume edit + reload reached the device (wrong Metro/worktree/port is silent) |
| Drag blocking floating overlays away: `gesture pan <x> <y> <dx> <dy> <ms>` (dev-menu bubbles, FABs) | Keep tapping "through" an overlay that is eating your presses |
| `network dump` before touching UI code for any empty/wrong-data screen | "Fix" the screen that faithfully renders bad data |
| Re-read the actual error on every retry — second failures often have new causes | Retry harder on the assumption it's the same bug |
| Retest auth/onboarding from a truly new account + cleared storage | Trust a retest that silently reused server-side state |
| Identify the current test user in backend probes by fresh evidence | Query "the user" and reason from someone else's rows |
| Verify async product results with `wait text "…" <generous-ms>`; poll backend jobs on the backend side | Spam snapshots at the UI waiting for a server job |
| Use `--settle` and read the settled diff as the next observation | Sandwich every action between full snapshots |
| Escalate stuck iOS waits to `screenshot` visual truth (AX can be screen-specifically broken) | Retry `snapshot` forever on an AX-unavailable screen |
| In shell probe loops around the CLI: avoid naming a variable `status` (readonly in zsh) and remember zsh does not word-split unquoted vars | Lose a polling loop to a shell quirk and misread it as a device problem |
| Background long polls (job status, CI, deploys) and keep testing | Block the session foreground-sleeping on a slow backend |

## Guardrails

- Serial mutations per session — never parallel `press`/`fill`/`open`/`close` against one session.
- No placeholders in final command plans: if the ref is unknown, the plan starts with `snapshot -i`.
- Coordinates only after refs/selectors fail, with rects from `snapshot -i --json` and a stated reason.
- Never delete evidence artifacts mid-session.
- Do not "fix" a flow by weakening its verification (skipping the assert, widening the wait, accepting the wrong text).
- App auth needing a real OTP/2FA: ask the user for the code; do not fabricate entry.
- If info is not visible/exposed in the UI, report the gap — do not wander unrelated screens to force it.

## Reference routing

| File | Load when |
|---|---|
| [references/command-map.md](references/command-map.md) | Once per session for the full command surface, or when unsure which command owns a job |
| [references/bug-triage.md](references/bug-triage.md) | A bug is found and needs root-causing across layers, or a fix didn't hold |
| [references/dev-loop-react-native.md](references/dev-loop-react-native.md) | The app is React Native / Expo / a dev client |
