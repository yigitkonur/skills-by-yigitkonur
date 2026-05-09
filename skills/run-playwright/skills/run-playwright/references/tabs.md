# Tabs, Sessions, Popups, And Cleanup

Use this reference for tab maps, named sessions, profile cleanup, popups, dialogs, and shared browser etiquette in `playwright-cli`.

## Tab Commands

```bash
playwright-cli tab-list
playwright-cli tab-new
playwright-cli tab-new https://example.com/docs
playwright-cli tab-select 0
playwright-cli tab-close
playwright-cli tab-close 2
```

Keep a tab map while working:

```text
0 -> app dashboard -> expected logged-in state
1 -> docs lookup -> disposable
2 -> OAuth popup -> waiting for callback
```

After `tab-select`, run:

```bash
playwright-cli eval "() => window.location.href"
playwright-cli snapshot
```

Refs from the previous tab are invalid.

## tab-new URL Behavior

Current `@playwright/cli@0.1.13` help documents `tab-new [url]`, and a smoke test with a `data:` URL opened the requested URL in the new tab.

Use either:

```bash
playwright-cli tab-new https://example.com/side-route
```

or the two-step fallback when working with a pinned older package or if the new tab lands on `about:blank`:

```bash
playwright-cli tab-new
playwright-cli goto https://example.com/side-route
```

Record the fallback as version drift if it happens.

## Session Commands

```bash
playwright-cli list
playwright-cli list --all
playwright-cli close
playwright-cli -s=research close
playwright-cli close-all
playwright-cli kill-all
playwright-cli delete-data
playwright-cli -s=research delete-data
```

`close` stops the current/default browser. `-s=name close` stops a specific named browser. `delete-data` removes stored profile data for the selected session.

Use `close-all` only when you intentionally own every session. Use `kill-all` only for stale or zombie process recovery.

## Named Sessions

```bash
playwright-cli -s=auth open https://app.example.com/login
playwright-cli -s=auth snapshot
playwright-cli -s=public open https://example.com
playwright-cli -s=public snapshot
```

Each named session has separate cookies, localStorage, sessionStorage, IndexedDB, cache, history, and tabs.

Set a default session in the environment:

```bash
export PLAYWRIGHT_CLI_SESSION=auth
playwright-cli snapshot
```

Prefer short, semantic names. Very long session names can make local socket paths brittle on some systems.

## Profile Modes

Default is in-memory:

```bash
playwright-cli open https://example.com
```

Persistent generated profile:

```bash
playwright-cli -s=auth open https://example.com --persistent
```

Custom profile directory:

```bash
playwright-cli -s=auth open https://example.com --profile=./profiles/auth
```

Delete only owned scratch profile data:

```bash
playwright-cli -s=auth delete-data
```

## Cleanup

At start, note:

- initial session
- initial tab index and URL
- tabs/sessions you create

At end:

```bash
playwright-cli tab-list
playwright-cli tab-close 2        # only tabs you created
playwright-cli -s=scratch close   # only sessions you created
```

Do not delete shared auth state or pre-existing sessions unless the user requested teardown.

## Popups And New Windows

For OAuth or `target=_blank` flows, `run-code` is safer because it captures the popup and triggering action together:

```bash
playwright-cli run-code "async page => {
  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    page.locator('a[target=_blank]').first().click()
  ]);
  await popup.waitForLoadState();
  return { title: await popup.title(), url: popup.url() };
}"
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

If the popup changes the main page state, re-verify the main tab before continuing.

## Dialogs

Dialog commands must run while the dialog is active:

```bash
playwright-cli dialog-accept
playwright-cli dialog-dismiss
playwright-cli dialog-accept "prompt text"
```

If a dialog auto-dismissed or never appeared, these commands can fail. Reproduce with a trace if timing matters.

## Shared Session Etiquette

When sharing a browser session, operate as a tab tenant:

1. Create or select only the tab you need.
2. Re-run `tab-list` before closing because indexes shift.
3. Use explicit `tab-close <index>`.
4. Do not run `close`, `close-all`, `kill-all`, or `delete-data` in shared sessions unless you own the whole context.
5. Return to the starting tab when useful.

## Orchestrator Brief

```text
PLAYWRIGHT CLI RULES

Use the current or assigned session.
Keep a tab map.
After tab switches, run URL check and snapshot.
Use fresh refs only.
Close only tabs/sessions you created.
Do not use close-all, kill-all, or delete-data unless you own all affected state.
Return artifact paths and cleanup state.
```
