# Sessions, tabs, and reference lifecycle

## Refs are observation-scoped handles

`snapshot` emits accessibility-tree references such as `@e1`. A ref belongs to the page/frame/tab state that produced it.

```bash
agent-browser snapshot -i
agent-browser click @e3
agent-browser snapshot -i
```

Invalidate refs after:

- navigation or reload;
- a click/submission that changes the page;
- modal, menu, dialog, or dynamic list changes;
- tab or frame switch;
- reconnect, pool recovery, or browser restart.

Do not manufacture refs, reuse refs from another tab, or write `@ref=e3`.

## Snapshot modes

```bash
agent-browser snapshot
agent-browser snapshot -i
agent-browser snapshot -i -u
agent-browser snapshot -i -c -d 4
agent-browser snapshot -s '#main'
```

`-i` is interactive-first; current output can retain useful headings/structure, so “interactive only” is too absolute. It still may omit visible noninteractive detail. Use full `snapshot` or `read` for content extraction.

`--json` makes snapshot output parseable. Do not parse decorative CLI text when JSON is available.

Annotated screenshots provide a visual ref map:

```bash
agent-browser screenshot --annotate ./annotated.png
```

The labels are not durable. Re-snapshot after the state changes.

## Locator escalation

Use this order:

1. Fresh ref.
2. Semantic locator by role/label/text/test ID.
3. Narrow CSS selector.
4. Small inspected `eval --stdin` computation.

When a ref stops resolving, re-snapshot before changing strategy. A stale ref is not proof that the element disappeared.

## Tabs

```bash
agent-browser tab
agent-browser tab new --label app https://example.com
agent-browser tab app
agent-browser tab close app
```

Current tab IDs are stable strings such as `t1`. Positional integers are rejected. `tab new` opens and switches to the new tab. Labels are task-local aliases; create them before using or closing them.

Maintain:

```yaml
active_tab: t3
owned_tabs: [t3, t5]
last_snapshot_tab: t3
refs_fresh: true
```

On the managed pool, the first fresh `open URL` becomes a new tab. Record its ID immediately. Never inspect, switch to, or close pre-existing authenticated tabs unless the requested task specifically targets them.

## Frames

One level of iframe content may appear inline in snapshots. When explicit targeting is needed:

```bash
agent-browser frame '#checkout-frame'
agent-browser snapshot -i
agent-browser frame main
agent-browser snapshot -i
```

Frame switches invalidate the working refs. Cross-origin restrictions and application behavior still apply.

## Managed pool versus upstream sessions

| Runtime | Isolation/persistence | Cleanup |
|---|---|---|
| Managed pool | Owner-scoped lane lease over persistent headed Chrome profile | Close owned tabs, then exact `agent-browser close` |
| Upstream named session | Separate agent-browser daemon/session | `agent-browser --session NAME close` |
| Restore key | Periodically saved auth/session state (default autosave interval currently 30s) | Close session; retain/delete key per task |
| Explicit profile | Persistent Chrome user-data directory | Close runtime; avoid concurrent reuse |

Do not add `--session` to managed-pool commands: it can defeat the wrapper's exact release path. Use named sessions only under intentional unmanaged `pool real` execution or where the pool command is unavailable.

## Stable unmanaged session IDs

For scripts that truly need an upstream session, derive a stable non-secret name:

```bash
SESSION="$(agent-browser session id --scope worktree --prefix qa)"
agent-browser --session "$SESSION" open https://example.com
agent-browser --session "$SESSION" snapshot -i
agent-browser --session "$SESSION" close
```

Scopes include `worktree`, `cwd`, and `git-root`; verify current help. A stable session enables reconnect, but it is not a lock-free substitute for concurrent agents sharing the same name.

## Restore state

For unmanaged hosts where authenticated continuity matters:

```bash
agent-browser --session "$SESSION" --restore service-login open https://example.com
```

Restore state auto-saves periodically while open and on close according to configured policy. Use a stable session so another command reconnects to the same runtime. Configure check URL/text/function when a stale or wrong account state would be dangerous.

Restore keys and state files may contain authentication material. Never commit them or print their contents.

## Authentication vault

Prefer credential providers or stdin over command-line secrets:

```bash
agent-browser auth login service \
  --credential-provider vault \
  --item 'Service account'
```

If a provider is unavailable, use `--password-stdin` and keep the secret out of logs. For an existing managed authenticated lane, use the profile rather than exporting credentials.

## Cookie import

For an approved unmanaged transfer, prefer a protected file:

```bash
agent-browser cookies set --curl ./cookie-export.txt
```

Treat the file as a credential. Do not paste cookie values into chat, shell arguments, or committed templates.

## Session recovery

Managed:

```bash
agent-browser pool status
agent-browser pool recover
agent-browser pool doctor
```

Unmanaged:

```bash
agent-browser session list
agent-browser doctor --offline --quick
agent-browser doctor
```

`doctor` can automatically clean stale daemon sidecars. `doctor --fix` is destructive repair and requires intentional authorization. Never start by deleting sockets, PIDs, or Chrome locks manually.
