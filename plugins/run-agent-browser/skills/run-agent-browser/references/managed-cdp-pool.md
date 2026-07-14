# Managed headed-CDP pool

This Mac runs three persistent, visible Google Chrome processes supervised by launchd. The `agent-browser` executable on `PATH` is a local wrapper: ordinary browser commands acquire one lane, connect through CDP, serialize commands for that lane, and release the lease on an exact top-level `agent-browser close`.

This is the default for local web automation. It avoids one Chrome process per agent, profile-lock collisions, daemon socket collisions, and stale `Singleton*` cleanup while retaining real Chrome profiles and windows.

## Architecture and invariants

| Lane | CDP | Profile | Intended use |
|---|---:|---|---|
| `general` | 9222 | `~/.agent-browser/real-chrome-cdp-profile` | Generic browsing |
| `profound` | 9411 | `~/.agent-browser/profound-cdp-profile` | Profound authenticated state |
| `peec` | 9444 | `~/.agent-browser/peec-solo2-profile` | Peec authenticated state |

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

Do not select `peec` or `profound` merely because they are free. Persistent authenticated profiles contain user state; use the least-privileged suitable lane.

## Command routing

| Need | Command shape | Why |
|---|---|---|
| Normal headed browsing | `agent-browser COMMAND ...` | Lease and reuse a pool lane |
| Public URL text fetch only | `agent-browser pool real read URL` | Avoid an unnecessary Chrome lease |
| Pool control/status | `agent-browser pool status|current|use|recover|doctor` | Wrapper-owned operation |
| Current CLI docs/install/doctor | `agent-browser skills ...`, `agent-browser --help`, etc. | Wrapper passes non-browser control commands through |
| Explicit remote/local CDP | `agent-browser pool real --cdp ... COMMAND` | Intentional bypass |
| Provider, engine, profile, auto-connect | `agent-browser pool real ...` | Intentional unmanaged runtime |
| Extension, init script, proxy, UA, raw launch args | `agent-browser pool real ...` | Pool Chrome is already launched; launch mutation cannot reliably apply |

Use `pool real` only when the task requires a property the pool cannot provide. State the bypass and its cleanup in the handoff. Do not combine pool ownership assumptions with an unmanaged process.

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
