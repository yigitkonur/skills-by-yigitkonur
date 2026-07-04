---
name: run-agent-browser
description: Use skill if you are driving the agent-browser CLI for ad hoc browser automation — @ref snapshots, sessions, forms, extraction, screenshots, headed/stealth, or provider runs.
allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)
---

# run-agent-browser

This skill exists because the agent is being asked to operate a terminal REPL, not author a script. The pattern is type-one-command, read-its-output, decide, type-the-next. Scripts and templates are not the protocol here. Run `agent-browser` inline, one command at a time, and update the session/tab/ref scratchpad after every state-changing call. The transcripts below are the muscle memory — read them before reading any rules table.

## STOP — if you find yourself writing a `*.sh` file or composing a multi-line heredoc before any inline command has been run

Warning signs you are derailing:

1. Drafting a `.sh` file with `set -euo pipefail` for a task the user asked you to perform once.
2. Planning the whole flow in advance — "first I'll open, then fill, then click, then verify" — without having opened anything yet.
3. Writing a `for` loop to iterate over URLs / accounts / selectors before you have observed a single page.
4. Writing `if` branches on output you have not yet seen.

Replace those instincts with this pattern. Each command is its own message in the same `Bash` tool; the daemon keeps the browser alive between calls. The agent's job between calls is to **read the output** and **update the scratchpad**.

The command names in this skill are literal. Do not invent aliases from other browser tools:

- Use `agent-browser open URL`, not `agent-browser nav URL`.
- Use `agent-browser --session NAME open URL` when you want a named session, not `agent-browser session start`.
- Use `agent-browser snapshot -i` for interactive refs, not bare `snapshot` when you need `@e` targets.
- Use refs exactly as returned (`@e14`, `@e3`). Do not write pseudo-flags such as `@ref=...`.

```
1. $ agent-browser open https://example.com
2. $ agent-browser wait --load networkidle
3. $ agent-browser snapshot -i
   (observe refs; pick one)
4. $ agent-browser fill @e3 "query"
5. $ agent-browser click @e4
6. $ agent-browser wait --load networkidle
7. $ agent-browser get url
8. $ agent-browser snapshot -i
   (verify new state; refs are fresh)
```

Six to ten inline calls solve almost any 80% task. Reach for a script only when the user explicitly asked for a reusable harness, or when the task is genuinely loop-shaped over a pre-known list. Even then, prefer running the inline flow once and only generalizing after the happy path works.

## Session/tab/ref scratchpad — maintain this mentally

```yaml
session: default          # or --session NAME (add --restore to persist state across cold starts)
profile: null             # or --profile PATH (persistent Chrome user data dir)
active_tab: 0             # always know which tab the next command targets
tabs:                     # list every tab you opened
  - {index: 0, url: ..., title: ...}
last_snapshot_at: step_N  # refs are valid ONLY until the next nav/click that changes DOM
refs: [e1, e2, ...]       # mark stale after nav, tab switch, modal open, SPA route change
sensitive_state: false    # true if you loaded auth, used --profile, or saved state to disk
```

Update after every `open`, `click`-that-navigates, `tab new`, `tab tN`, `back`, modal open/close, or any state change. If you cannot answer "which tab is active, and when was the last snapshot?" from memory, run `agent-browser tab` and `agent-browser snapshot -i` before the next action.

## Verify the CLI is reachable, then go

```
$ agent-browser --version
0.31.1
```

If the command is not found, install once: `npm install -g agent-browser` (pin in production — see `references/safety.md`). If the first browser command fails because Chromium is missing, run `agent-browser install` once and retry. Treat that as part of the happy path, not troubleshooting.

---

### Scenario A — Login form, verify by URL and title

Goal: log into a SaaS app and confirm landing on `/dashboard`.

─── state ───
tab: 0 | session: default | refs: none yet | sensitive_state: false

1. ```
   $ agent-browser open https://app.example.com/login
   → ok | url=https://app.example.com/login | title=Sign in
   ```
   (what I now know: I am on the login page; no refs yet — must snapshot.)

2. ```
   $ agent-browser wait --load networkidle
   → ok
   ```
   (state: page settled; safe to snapshot.)

3. ```
   $ agent-browser snapshot -i
   → 4 refs:
     @e1 [input type="email"] placeholder="Email"
     @e2 [input type="password"] placeholder="Password"
     @e3 [button] "Sign in"
     @e4 [a] "Forgot password?"
   ```
   (what I now know: e1=email, e2=password, e3=submit. last_snapshot_at = step 3.)

4. ```
   $ agent-browser fill @e1 "user@example.com"
   → ok
   ```
   (state: refs still valid; no nav.)

5. ```
   $ agent-browser fill @e2 "$APP_PASSWORD"
   → ok
   ```
   (state: refs still valid.)

6. ```
   $ agent-browser click @e3
   → ok
   ```
   (state: click probably triggers navigation; refs MUST be treated stale after the wait below.)

7. ```
   $ agent-browser wait --url "**/dashboard"
   → ok
   ```
   (what I now know: URL pattern matched — login succeeded.)

8. ```
   $ agent-browser get url
   → https://app.example.com/dashboard
   ```
   (verification rung: URL confirms. Now title too.)

9. ```
   $ agent-browser get title
   → Dashboard — Example
   ```
   (verified. last_snapshot_at = stale; if I act again I re-snapshot first.)

If step 7 times out, the click did not navigate — re-snapshot, look for an inline error toast (`agent-browser get text ".error"`), and either fix the credentials or escalate to `--headed` (Scenario E pattern). Do not retry the same click in a loop.

---

### Scenario B — Multi-tab side trip, return to original task

Goal: while on a product page, open the docs in a new tab, copy one value, come back, and continue editing the form.

─── state ───
tab: 0 | session: default | refs: valid as of step 1 | sensitive_state: false

1. ```
   $ agent-browser snapshot -i
   → @e1 [input] "Name"  @e2 [a href="/docs/api"] "API docs"  @e3 [button] "Save"
   ```
   (active_tab=0; refs fresh.)

2. ```
   $ agent-browser click @e2 --new-tab
   → ok | opened in new tab
   ```
   (state: tab 1 was opened, but **focus does not auto-switch**. active_tab still = 0.)

3. ```
   $ agent-browser tab
   → [0] https://app.example.com/edit/42  *active
     [1] https://docs.example.com/api
   ```
   (confirms two tabs; I still need to switch.)

4. ```
   $ agent-browser tab t1
   → ok | switched to tab 1
   ```
   (state update: active_tab = 1. ALL refs from step 1 are now stale.)

5. ```
   $ agent-browser wait --load networkidle
   → ok
   ```

6. ```
   $ agent-browser get text "code.api-key-example"
   → sk_live_xxxxxxxxxxxxxxxx
   ```
   (extracted one value; no need to snapshot — selector matched exactly one.)

7. ```
   $ agent-browser tab close t1
   → ok | tab 1 closed, focus returned to tab 0
   ```
   (state update: active_tab = 0. refs from step 1 are STILL stale — modal/nav can change them, but more importantly I have been gone for several steps. Re-snapshot.)

8. ```
   $ agent-browser snapshot -i
   → @e1 [input] "Name"  @e2 [a] "API docs"  @e3 [button] "Save"
   ```
   (refs may have the same IDs by coincidence — they are still a NEW snapshot. last_snapshot_at = step 8.)

9. ```
   $ agent-browser fill @e1 "Service using sk_live_xxxxxxxxxxxxxxxx"
   → ok
   ```

10. ```
    $ agent-browser click @e3
    → ok
    ```

The headline lesson: `--new-tab` opens a tab but does not focus it. `tab t1` switches focus (tab targets take a `t` prefix — bare `tab 1` is rejected; use `t1`, `t2`, or a label). Every tab switch is a navigation event for ref lifecycle purposes — re-snapshot.

---

### Scenario C — Structured multi-element extraction with `eval --stdin`

Goal: extract the top 10 article titles and URLs from a listing page.

─── state ───
tab: 0 | session: default | refs: none | sensitive_state: false

1. ```
   $ agent-browser open https://news.example.com/
   → ok | url=https://news.example.com/ | title=News
   ```

2. ```
   $ agent-browser wait --load networkidle
   → ok
   ```

3. ```
   $ agent-browser get text ".story-title"
   → Error: strict mode violation — 47 elements matched ".story-title"
   ```
   (what I now know: `get text` is strict-mode — fails when more than one element matches. This is the canonical signal to switch to `eval --stdin`.)

4. ```
   $ agent-browser get count ".story-title"
   → 47
   ```
   (good — confirms the selector is right; just too many matches for `get text`.)

5. ```
   $ agent-browser eval --stdin <<'EVALEOF'
   const items = document.querySelectorAll('article .story-title a');
   JSON.stringify(
     Array.from(items).slice(0, 10).map(el => ({
       title: el.textContent.trim(),
       url: el.href
     })),
     null, 2
   );
   EVALEOF
   → [
       {"title":"...","url":"https://..."},
       ...10 entries...
     ]
   ```
   (extracted. Use heredoc with `<<'EVALEOF'` — single-quoted delimiter — so the shell does not expand `$` or backticks inside the JS.)

Do not try inline `eval "Array.from(document.querySelectorAll('.story-title a')).map(a => a.href)"`. Shell escaping with nested single/double quotes corrupts the JS. The heredoc pattern is the safe form.

---

### Scenario D — Recovery from stale refs after a SPA route change

Goal: from a list view, click into one item; after the SPA route changes, the next snapshot's refs are different — narrate the recovery.

─── state ───
tab: 0 | session: default | refs: valid as of step 1

1. ```
   $ agent-browser snapshot -i
   → @e1 [a] "Item A"  @e2 [a] "Item B"  @e3 [a] "Item C"
   ```
   (three list items; I want Item B.)

2. ```
   $ agent-browser click @e2
   → ok
   ```
   (state: SPA route may change URL without a hard navigation. Refs are now SUSPECT.)

3. ```
   $ agent-browser wait --url "**/item/**"
   → ok
   ```
   (URL pattern confirms route change happened.)

4. ```
   $ agent-browser get url
   → https://app.example.com/item/B
   ```

5. ```
   $ agent-browser click @e3
   → Error: ref @e3 not found
   ```
   (predicted. The old refs are from the list view. Re-snapshot.)

6. ```
   $ agent-browser snapshot -i
   → @e1 [button] "Edit"  @e2 [button] "Delete"  @e3 [a] "Back to list"  @e4 [input] "Title"
   ```
   (new refs for the detail view. `@e3` here is "Back to list" — completely different element from the old `@e3`.)

7. ```
   $ agent-browser click @e1
   → ok
   ```
   (now safe.)

Refs are scoped to the snapshot that produced them. Any navigation, SPA route change, tab switch, modal open, dynamic load, or form submission may invalidate them. Symptom: `ref not found` or wrong element clicked. Fix: re-snapshot, then act.

---

### Scenario E — Headed escalation when headless gets walled

Goal: headless mode hits a Cloudflare challenge; re-run the same step with `--headed` and continue.

─── state ───
tab: 0 | session: default | refs: none | sensitive_state: false

1. ```
   $ agent-browser open https://shop.example.com/
   → ok
   $ agent-browser get title
   → Just a moment...
   ```
   (Cloudflare interstitial — headless was detected.)

2. ```
   $ agent-browser close
   → ok
   $ agent-browser --headed --session shop open https://shop.example.com/
   → ok | (visible browser window)
   ```
   (re-opening with `--headed` and a named session so state auto-persists. sensitive_state: true — there is now persistent state on disk for "shop".)

3. ```
   $ agent-browser --session shop wait --load networkidle
   → ok
   $ agent-browser --session shop get title
   → Shop — Example
   ```
   (challenge passed.)

4. Continue the task under `--session shop`. After the work is done, decide explicitly whether to keep the persisted state. If you keep it, note it in the output contract.

Headed mode is also the right answer for 2FA, manual auth, or any flow where a human needs to look at the screen. For non-interactive provider escalation (Browserbase, Kernel) see `references/advanced.md`.

---

## Operating rules (commentary on the transcripts above)

1. **Snapshot before acting.** Every transcript above starts with a snapshot before the first interaction. After any nav, click that nav'd, tab switch, modal open, or SPA route change, treat all refs as stale.
2. **Re-snapshot after every state change.** Scenario D's recovery exists because refs are scoped to the snapshot that produced them.
3. **`get text` is strict-mode.** Multi-element matches throw. Switch to `eval --stdin` with a single-quoted heredoc (Scenario C).
4. **`--new-tab` opens a tab but does not focus it.** `tab t1` switches focus (tab targets need the `t` prefix — bare `tab 1` errors). Both are navigation events for ref lifecycle (Scenario B).
5. **Verify with at least one deterministic check after every meaningful interaction.** `get url`, `get title`, `get text`, `get value`, `is visible`, `is checked`, `diff snapshot`. URL + title is the cheapest pair.
6. **Reuse the current session by default.** Spawn a named `--session NAME` only for parallel isolated work. Add `--restore` to a named session only when state should auto-save/restore (cookies + localStorage) across separate runs. Spawn `--profile PATH` only when full-Chrome persistence (IndexedDB, service workers, cache) is needed.
7. **Prefer `tab new` over `window new`.** Use `window new` only when the site truly requires a separate window.
8. **`agent-browser back` not `go back`.** `back` preserves history and form state; re-opening the URL drops both.
9. **`snapshot -i` hides non-interactive text.** Headings, paragraphs, spans, labels. For data extraction use `get text SELECTOR` (single match) or `eval --stdin` (multiple). See `references/sessions-and-refs.md` for the JSON schema and scoped snapshots.
10. **`diff snapshot` requires the subcommand.** Bare `diff` fails. Flags: `--baseline <file>`, `--selector <sel>`, `--compact`.
11. **`check` and `uncheck` return the new checked state (`true`/`false`)**, not `ok`. Expected.
12. **`find` is the ref-free alternative to `snapshot -i`.** `find role button click --name "Save"`, `find text "Sign in" click`, also `label`/`placeholder`/`testid` — targets a single element by accessible role/text without capturing refs first. Use it for one known control; use `snapshot -i` when exploring.
13. **Close only what you opened.** Tabs, sessions, state files, profiles. Leave pre-existing context alone.

## Do this, not that

| Do this | Not that | Tied to |
|---|---|---|
| Reuse the default session for one continuous task | Spawn a new session per page | Scenario A |
| `click @e2 --new-tab` then `tab t1` then re-snapshot | Click and assume focus moved | Scenario B |
| `eval --stdin <<'EVALEOF' ... EVALEOF` for multi-element extraction | Inline `eval "Array.from(...)..."` with nested quotes | Scenario C |
| Re-snapshot after every SPA route / nav / tab switch | Reuse a ref across a navigation | Scenario D |
| Escalate to `--headed` when headless is walled; keep the same `--session` | Retry the same headless command in a loop | Scenario E |
| Verify with `get url` + `get title` before declaring success | Trust that "click @e3 → ok" means the form submitted | Scenarios A, D |

## Recovery cookbook

- **`ref not found`** — page changed since the last snapshot. Run `agent-browser snapshot -i` and retry with the new ref.
- **`strict mode violation — N elements matched`** — `get text`/`get value` requires exactly one match. Switch to `eval --stdin <<'EVALEOF'` (Scenario C) or narrow the selector.
- **Unexpected redirect** — `agent-browser get url` and `agent-browser get title` first; if on a login screen, load saved state or follow the auth flow. See `references/sessions-and-refs.md`.
- **Slow or flaky page** — `agent-browser wait --load networkidle`, then `agent-browser wait 2000` as a fallback, then re-snapshot. Increase `AGENT_BROWSER_DEFAULT_TIMEOUT` only when a specific page genuinely needs longer.
- **Stale daemon / `EADDRINUSE`** — `agent-browser close`. If that fails, see `references/safety.md` § stale daemon for socket cleanup.
- **Sensitive operation about to run** — before `eval` that mutates, `download`, `state save/load`, `cookies set`, `storage local set`, `network route`, `--allow-file-access`, `--executable-path`, `--cdp`, `--args`: stop and read `references/safety.md` for scope and approval rules.
- **Hidden UI (dropdown / popover / accordion)** — initial snapshot will not show children. Click the trigger, `wait 500`, re-snapshot. See `references/sessions-and-refs.md` § hidden UI.

## When NOT to use this skill

- Writing TypeScript browser-automation code with `@onkernel/sdk` → use `build-kernel-ts-sdk`.
- Reconstructing a Next.js project from a captured site → ownership stays with `convert-url-to-nextjs`; this skill is only invoked for live capture.
- Documenting a SaaS visual system → this skill is only invoked for browser evidence, not for producing the design document itself.
- Static research, no live browser context needed.

## Reference routing

| Need | Read |
|---|---|
| Full command + flag reference (every subcommand, every option, env vars) | `references/commands.md` |
| Session / tab / profile / snapshot-ref lifecycle / JSON schema / authentication / hidden UI | `references/sessions-and-refs.md` |
| Safety policy, sensitive commands, stale daemon recovery, troubleshooting, SSL, serverless | `references/safety.md` |
| Provider/stealth/proxy/profiling/video/iOS/extensions/network interception/install | `references/advanced.md` |

Helper scripts in `scripts/` (`check-agent-browser-version.sh`, `inspect-page.sh`) exist for one-off bootstrap or first-pass capture by other skills. Do not wrap normal browser work in them; run agent-browser inline.

## Output contract — when work ends, report

- Final active URL and title.
- Mode used (default / `--headed` / `--profile PATH` / `--session NAME` / `-p PROVIDER` / `--engine ENGINE`) when non-default.
- Deterministic verifications run, e.g. `get url`, `get title`, `get text`, `get value`, `is visible`, `is checked`, `diff snapshot`.
- Evidence paths created — screenshots, videos, traces, profiles, saved state files.
- Extracted data shape when data was extracted — JSON array, CSV rows, table, key-value map — plus selectors/refs used and a count check (`get count SELECTOR`).
- Cleanup performed — tabs closed, sessions closed, state files kept or deleted, profile left in place or removed. If `sensitive_state` was ever true, name explicitly what persisted.
