# React Native / Expo dev-loop with agent-device (iOS)

Load this only when the app under test is React Native, Expo, or a development client. Authority: `agent-device help react-native`; this file adds the traps that live *around* the CLI.

## Which runtime refresh does my change need?

| Change | Refresh | Command |
|---|---|---|
| JS/TS code, styles, assets via bundler | Metro reload | `agent-device metro reload` |
| Env var read at bundle time (`EXPO_PUBLIC_*` etc.) | Restart the dev server, then reload | restart Metro process → `metro reload` |
| Native module, pod, entitlement, app config affecting the binary | Rebuild + reinstall | rebuild → `install`/`reinstall` → `open --relaunch` |
| Backend code the app calls | Deploy the backend | platform deploy, then retest |

There is **no** `agent-device reload` — the command is `metro reload`. Native startup reset is `open <app> --relaunch`.

## The wrong-Metro trap (highest-cost RN mistake)

A dev client binds to *a* Metro, not necessarily *your* Metro. With several checkouts/worktrees of the same app on one machine, it is easy to edit repo A while the simulator loads JS from repo B — every "fix" is then a no-op and every retest a false negative.

Prove which Metro serves the app before trusting any retest:

```bash
lsof -iTCP:8081 -sTCP:LISTEN          # who listens
lsof -p <pid> | grep cwd              # which checkout owns it
agent-device doctor                    # dev-server reachability as agent-device sees it
```

If it's the wrong checkout: either apply the fix to the serving checkout too, or point the app at the right server (`open … --metro-host 127.0.0.1 --metro-port <port> --relaunch`). Multiple worktrees can share one installed native build by giving each its own port:

```bash
agent-device open "MyApp" --platform ios --device "iPhone 17" --session a --metro-port 8081 --relaunch
agent-device open "MyApp" --platform ios --device "iPhone 17 Pro" --session b --metro-port 8082 --relaunch
```

One simulator cannot run two copies of the same bundle id.

Sandbox note: if a restricted shell can't `curl localhost:8081/status` but an unrestricted host shell can, the dev server is fine — the sandbox probe is not authoritative.

## Opening Expo Go / dev clients

These are host *shells*; the project loads via URL:

```bash
agent-device open "Expo Go" exp://127.0.0.1:8081 --platform ios   # host + URL preferred
agent-device snapshot -i                                           # confirm project UI, not the splash
```

- Direct URL open (`open exp://…`) can report success while the shell splash stays focused — always verify with `snapshot -i`.
- Use a provided project URL; never invent one or a bundle id. Dev clients: open the installed dev-client app id, then the dev-client URL if provided.
- Setting up a server for Expo: `agent-device metro prepare --kind expo`.

## Overlays: LogBox / RedBox / dev menus

- Warning/error overlay in the snapshot → `agent-device react-native dismiss-overlay`, then `snapshot -i`. Never press overlay text bodies manually; record the overlay as a finding.
- **Floating dev-menu bubbles and FABs intercept taps** while looking harmless. If presses on a control "succeed" without effect, check whether a floating element covers it; move it with `gesture pan <x> <y> <dx> <dy> <durationMs>` (drag it to a corner) or target a coordinate away from it.
- Overlay still visible after dismiss-overlay → `screenshot --overlay-refs` for evidence and report; don't keep pressing.

## RN-specific state pitfalls worth suspecting early

These generate "impossible" on-device behavior with clean-looking code:

- **Stale closures:** a `useCallback`/`useMemo`/effect capturing an old value because the dependency array is incomplete. But note: adding the missing dep is a *hypothesis* until the live retest passes — the real cause may be the value being legitimately empty at call time.
- **Context resets on identity change:** providers that reset state in an effect watching `user?.id` (or similar) will silently wipe values between screens whenever the auth session re-resolves. If a value set on screen N is empty on screen N+2, check for a reset path before blaming the setter.
- **Single-write gates:** flows where a flag/id is written exactly once at flow end are fragile — if that write is skipped (guard falsy, closure stale, user changed), nothing repairs it later. When you find one, also add/verify a read-side fallback.
- **Debounced/search inputs:** characters can be dropped at native speed; `fill <target> <text> --delay-ms 80` paces entry.

## Component-level evidence

When the question is *why* React rendered this way (props/state/hooks, slow renders, rerenders):

```bash
agent-device react-devtools status
agent-device react-devtools wait --connected     # app attached, not just helper running
agent-device react-devtools profile start
# drive the interaction
agent-device react-devtools profile stop
agent-device react-devtools profile slow --limit 5
agent-device react-devtools profile report @c5
```

`status` before `wait`; `start` only if status says the helper isn't running. `@c` refs reset after reload. Keep profile windows narrow. If DevTools can't connect, continue with logs/network/perf instead of blocking.

JS heap leaks: `agent-device help cdp` (usage samples → snapshot diffs → leak-triplet → retainers). Native/process memory is `perf memory sample`, not cdp.
