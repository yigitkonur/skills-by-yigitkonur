# Managed headed-CDP pool

This wrapper runs one persistent, visible Google Chrome process per registered lane, supervised by launchd. Lanes are not fixed: `pool create`/`pool remove` (below) add and drop them at runtime, and nothing about a lane's name, port, or count is hardcoded in the wrapper — the table below is only this particular machine's current lanes. The `agent-browser` executable on `PATH` is a local wrapper: ordinary browser commands acquire one lane, connect through CDP, serialize commands for that lane, and release the lease on an exact top-level `agent-browser close`.

This is the default for local web automation. It avoids one Chrome process per agent, profile-lock collisions, daemon socket collisions, and stale `Singleton*` cleanup while retaining real Chrome profiles and windows.

## Prerequisites (one-time per machine)

Two things must exist before `pool create` (or any lane) works: this wrapper on `PATH` as `agent-browser`, and a per-lane supervisor script that launchd runs to keep one headed Chrome window alive per lane. Neither ships with the official `agent-browser` CLI — a fresh machine has neither.

Save the following as `~/.local/libexec/agent-browser-chrome-lane` and `chmod +x` it. It takes `<lane-name> <port> <profile-dir>`, launches headed Chrome on that CDP port with that profile, and preserves tab state across restarts. Nothing in it is hardcoded to a name, port, or username — the same file backs every lane on any machine:

```sh
#!/bin/sh
# launchd supervisor for one headed Chrome CDP lane.
set -u

lane="$1"
port="$2"
profile="$3"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
pool_root="$HOME/.agent-browser/cdp-pool"
tab_root="$pool_root/tabs"
tmp_root="$pool_root/tmp"
manifest="$tab_root/$lane.json"

mkdir -p "$profile" "$tab_root" "$tmp_root"
chmod 700 "$pool_root" "$tab_root" "$tmp_root" "$profile" 2>/dev/null || true

snapshot_tabs() {
  snapshot_tmp="$manifest.$$"
  if curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/list" \
    | jq '[.[] | select(.type == "page" and .url != "about:blank") | {title, url}]' > "$snapshot_tmp" 2>/dev/null; then
    chmod 600 "$snapshot_tmp"
    mv "$snapshot_tmp" "$manifest"
  else
    rm -f "$snapshot_tmp"
  fi
}

restore_tabs() {
  [ -s "$manifest" ] || return 0
  current="$tmp_root/$lane.current.$$"
  desired="$tmp_root/$lane.desired.$$"
  curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/list" \
    | jq -r '.[] | select(.type == "page" and .url != "about:blank") | .url' | sort > "$current"
  jq -r '.[].url' "$manifest" | sort > "$desired"
  if ! cmp -s "$current" "$desired"; then
    curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/list" \
      | jq -r '.[] | select(.type == "page") | .id' \
      | while IFS= read -r target; do
          curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/close/${target}" >/dev/null 2>&1 || true
        done
    jq -r '.[].url | @uri' "$manifest" \
      | while IFS= read -r encoded_url; do
          curl -fsS --max-time 2 -X PUT "http://127.0.0.1:${port}/json/new?${encoded_url}" >/dev/null 2>&1 || true
        done
  fi
  curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/list" \
    | jq -r '.[] | select(.type == "page" and .url == "about:blank") | .id' \
    | while IFS= read -r target; do
        curl -fsS --max-time 2 "http://127.0.0.1:${port}/json/close/${target}" >/dev/null 2>&1 || true
      done
  rm -f "$current" "$desired"
}

"$chrome" \
  "--remote-debugging-port=$port" \
  --remote-debugging-address=127.0.0.1 \
  "--user-data-dir=$profile" \
  --no-first-run \
  --no-default-browser-check \
  --restore-last-session &
chrome_pid=$!

stop_lane() {
  snapshot_tabs
  kill -TERM "$chrome_pid" 2>/dev/null || true
  wait "$chrome_pid" 2>/dev/null || true
  exit 0
}
trap stop_lane HUP INT TERM

attempt=0
while [ "$attempt" -lt 40 ]; do
  if curl -fsS --max-time 1 "http://127.0.0.1:${port}/json/version" >/dev/null 2>&1; then
    restore_tabs
    break
  fi
  kill -0 "$chrome_pid" 2>/dev/null || break
  sleep 0.5
  attempt=$((attempt + 1))
done

while kill -0 "$chrome_pid" 2>/dev/null; do
  snapshot_tabs
  sleep 10
done

wait "$chrome_pid"
exit $?
```

Once that file is in place, `agent-browser pool create <name>` (see "Creating and removing lanes" below) does everything else: generates the launchd plist, bootstraps it, and waits for CDP to answer.

## Architecture and invariants

Example only — this is what one machine currently has registered. Yours will differ unless you create the same lanes:

| Lane | CDP | Profile | Intended use |
|---|---:|---|---|
| `general` | 9222 | `~/.agent-browser/real-chrome-cdp-profile` | Generic browsing |
| `profound` | 9411 | `~/.agent-browser/profound-cdp-profile` | Profound authenticated state |
| `peec` | 9444 | `~/.agent-browser/peec-solo2-profile` | Peec authenticated state |
| `slot_01`-`slot_10` | 9501-9510 | `~/.agent-browser/slot_NN-cdp-profile` | Plain scratch lanes, no persistent auth |

On this machine, `slot_01`-`slot_10` exist to absorb overflow so agents don't queue on the 3 named lanes under multi-agent load. They carry no persistent authenticated state — pick any lane that shows `free` in `pool status` by number, e.g. `pool use slot_07`. There is nothing special about the name `slot_NN`; it is just this machine's naming convention. Use `agent-browser pool create <any-name>` to add lanes with whatever names and count fit your own workflow.

The endpoints bind to loopback. launchd keeps Chrome and the lane supervisor alive. The supervisor periodically records nonblank tab URL/title state and restores the exact URL multiset after a Chrome restart.

The wrapper:

- derives a per-agent owner from the process tree;
- grants one lane lease to that owner, waiting up to 60 seconds when all lanes are busy;
- expires abandoned leases after one hour;
- serializes commands within each lane;
- turns the first fresh `open URL` into `tab new URL`, preventing takeover of a pre-existing tab;
- leaves pre-existing profile tabs alone;
- releases the lane only when the first command word is top-level `close`.

The pool is shared infrastructure. Never kill its Chrome processes, delete profile locks or `Singleton*` files, delete wrapper sockets/PIDs/leases, bind the ports publicly, or run `close --all`.

## Start sequence

Run these one at a time and read each result:

```bash
agent-browser pool status
agent-browser open https://example.com
agent-browser pool current
agent-browser tab
agent-browser snapshot -i
```

Record the lane, port, owner, active tab, and the tab created for the task. A successful command does not prove the expected page state; verify URL/title or visible content separately.

### Select an authenticated lane

Selection must happen before any browser command:

```bash
agent-browser pool use peec
agent-browser pool current
agent-browser open https://app.peec.ai
```

If the owner already holds another lane, `pool use` returns that existing lane rather than migrating the lease. Check `pool current`. If it is wrong, close owned tabs, run the exact top-level `agent-browser close`, then select the desired lane before reopening.

Do not select `peec` or `profound` merely because they are free. Persistent authenticated profiles contain user state; use the least-privileged suitable lane — for anonymous/scratch work, prefer any free `slot_01`-`slot_10` over `general`, and `general` over `peec`/`profound`.

## Command routing

| Need | Command shape | Why |
|---|---|---|
| Normal headed browsing | `agent-browser COMMAND ...` | Lease and reuse a pool lane |
| Public URL text fetch only | `agent-browser pool real read URL` | Avoid an unnecessary Chrome lease |
| Pool control/status | `agent-browser pool status|current|use|recover|doctor|create|remove` | Wrapper-owned operation |
| Current CLI docs/install/doctor | `agent-browser skills ...`, `agent-browser --help`, etc. | Wrapper passes non-browser control commands through |
| Explicit remote/local CDP | `agent-browser pool real --cdp ... COMMAND` | Intentional bypass |
| Provider, engine, profile, auto-connect | `agent-browser pool real ...` | Intentional unmanaged runtime |
| Extension, init script, proxy, UA, raw launch args | `agent-browser pool real ...` | Pool Chrome is already launched; launch mutation cannot reliably apply |

Use `pool real` only when the task requires a property the pool cannot provide. State the bypass and its cleanup in the handoff. Do not combine pool ownership assumptions with an unmanaged process.

## Creating and removing lanes

Lanes are not hardcoded in the wrapper — they are a plain-text registry at `~/.agent-browser/cdp-pool/lanes.conf` (`name port`, one per line), read fresh on every invocation. `pool status` always reflects exactly what is in that file plus real launchd/CDP state; the "Architecture" table above is one machine's snapshot, not a fixed set baked into the tool.

```bash
agent-browser pool create NAME [PORT]   # PORT optional; auto-picks the next free port from 9500 up
agent-browser pool remove NAME          # must not be currently leased; profile is left on disk
```

`pool create`:

- validates `NAME` (letters/digits/underscore, must start with a letter) and rejects a duplicate;
- auto-assigns a port starting at 9500 when none is given, skipping both registered ports and ports already bound by something else;
- writes `~/Library/LaunchAgents/com.<user>.agent-browser-cdp.<name>.plist` — `<user>` comes from `id -un`, never hardcoded, so the identical command works on any machine and any account;
- creates the Chrome profile at `~/.agent-browser/<name>-cdp-profile`;
- `launchctl bootstrap`s the lane and polls CDP before reporting success;
- rolls back the plist and registry line if `launchctl bootstrap` fails, so a failed create never leaves half-registered state.

`pool remove` refuses a currently-leased lane, unloads the launchd service (`launchctl bootout`), deletes the plist, and drops the registry line. It does **not** delete the Chrome profile directory — that holds real cookies/session state, and is left for you to remove explicitly once you are sure you don't need it.

The wrapper seeds `lanes.conf` the first time it runs after being installed or upgraded, by scanning `~/Library/LaunchAgents/com.<user>.agent-browser-cdp.*.plist` for lanes that already exist, so upgrading it never drops a lane you already created by hand. On a genuinely fresh machine with no prior setup, `lanes.conf` starts empty and every browser command fails with `No CDP lanes are registered yet. Create one: agent-browser pool create general` until you run `pool create` — that message is the expected first-run state, not a bug.

## Tabs and cleanup

The task owns only tabs it created. Current tab IDs are stable strings (`t1`, `t2`), not positional indexes.

```bash
agent-browser tab
agent-browser tab close t7
agent-browser close
agent-browser pool status
```

Important distinctions:

- `tab close t7` closes one tab but does not release the lane.
- `agent-browser --session name close` does not trigger the wrapper's pool release because `--session` is the first argument.
- `agent-browser close` must be exact and top-level for managed cleanup.
- `close --all` can affect other agents and is prohibited.

Chrome refuses to close its final tab. If the task-owned tab is the final tab, switch explicitly to that owned ID, navigate it to `about:blank`, then release the lease. Do not solve this by closing another tab.

## Recovery

Use the narrowest rung and inspect the result before continuing:

```bash
agent-browser pool status
agent-browser pool current
agent-browser pool recover
agent-browser pool doctor
```

- `status` shows lane health and leases.
- `current` identifies the caller's assignment.
- `recover` repairs wrapper/supervisor state without manual file deletion.
- `doctor` performs the deeper pool diagnostic.

After recovery, reopen the intended URL and verify it. Do not infer that restored tabs mean the previous DOM, refs, form state, downloads, or JS execution survived. Snapshot refs are always invalid after a restart or reconnect.

### Why commands "hang" and how to tell it from a real failure

The wrapper waits up to 60 seconds for a lane before giving up, and that wait produces no output — it just looks stuck. With only 3 named lanes this happens constantly under real multi-agent load; it is the most common source of "the agent is stuck" reports. Work through this order instead of killing and blindly retrying:

1. `agent-browser pool status` first, always. If `general`/`profound`/`peec` show `leased`, that is the entire explanation. Switch to a free `slot_NN` lane (`pool use slot_04`) rather than waiting on a named lane you don't specifically need auth state from. If `pool status` prints only the header with no rows, no lanes are registered yet — `agent-browser pool create general` and retry.
2. If a command still stalls on a `slot_NN` lane, don't block the foreground indefinitely — background it and check back. Genuine contention can legitimately take 60-150s end to end (lane wait + Chrome launch/navigation + CDP round trip), which is normal, not broken.
3. An explicit error ending in `daemon may be busy or unresponsive` or `Resource temporarily unavailable (os error 35)` confirms real contention, not a syntax or targeting mistake — retry the same command, don't start guessing at flags.
4. Still stuck after that: `agent-browser pool recover`, then re-verify with `pool status` before retrying the original command.

Provisioning-time caveat: bootstrapping several lanes at once can transiently crash an already-running lane's GPU/network subprocess. Chrome exits cleanly (`exit 0`) when that happens, and because every lane's plist uses `KeepAlive/SuccessfulExit=false`, launchd does **not** auto-restart a clean exit — it needs a manual `launchctl kickstart -k gui/$(id -u)/com.$(id -un).agent-browser-cdp.<lane>`. After any bulk lane-provisioning change, re-check `pool status` for every previously-healthy lane, not just the new ones.

## Multi-agent edge cases

- A lane is a serialization boundary, not a privacy boundary. Other profile tabs may exist.
- One agent should retain one lane for a task; do not hop lanes mid-flow.
- The wrapper waits for a lane rather than spawning more Chrome. A timeout is evidence of contention, not permission to bypass silently.
- A stale lease may expire, but the task should still clean up normally. Do not wait for TTL as routine cleanup.
- Opening additional URLs creates and switches to new owned tabs. Record every returned/observed tab ID.
- Labels improve task-local clarity but do not authorize closing a label you did not create.
- Persistent cookies/storage remain after lease release. Log out or mutate shared account state only when the user requested that outcome.

### Delegation contract

For each delegated browser mission, specify the desired lane (or `auto`), URL/domain boundary, account/workspace, authorized persistent effects, deterministic proof, and cleanup. The worker must discover its own tab ID and refs; IDs from the coordinator's lane are meaningless and can be dangerous.

Parallelize only independent read flows or mutations against distinct state. If two workers would update the same account, form, record, or tab-dependent workflow, serialize them even when two lanes are available. The coordinator should verify the worker's final URL/DOM/error evidence rather than accepting “done.”

## Verification checklist

Before claiming a pool task complete:

1. Verify expected URL/title or DOM state.
2. Run `agent-browser errors` for UI/runtime work.
3. List tabs and close only task-owned IDs/labels.
4. Run exact `agent-browser close`.
5. Run `agent-browser pool status` and confirm the owner no longer holds the lane.
6. Report any persistent account/profile mutation and sensitive artifacts.
