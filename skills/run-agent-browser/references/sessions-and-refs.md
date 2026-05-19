# Sessions, refs, authentication, and persistence

Everything about the live state of a browser context — which session you are in, which tab is active, whether the refs from your last snapshot are still valid, and how to log in once and stay logged in.

**Related:** `commands.md` for flags and subcommands, `safety.md` for sensitive-command policy, `SKILL.md` for the operating transcripts.

---

## Part 1 — Snapshot and refs

### How refs work

Traditional approach: pass full DOM/HTML to the model, model emits CSS selector, run action (~3k–5k tokens per step).

agent-browser approach: `snapshot -i` returns a compact accessibility tree with `@e1`, `@e2`, ... refs (~200–400 tokens). Subsequent commands take the ref directly.

```bash
agent-browser snapshot -i
```

### Output format (text mode)

```
Page: Example Site — Home
URL: https://example.com

@e1 [header]
  @e2 [nav]
    @e3 [a] "Home"
    @e4 [a] "Products"
  @e5 [button] "Sign In"

@e6 [main]
  @e7 [h1] "Welcome"
  @e8 [form]
    @e9  [input type="email"]    placeholder="Email"
    @e10 [input type="password"] placeholder="Password"
    @e11 [button type="submit"]  "Log In"
```

### Ref notation

```
@e1 [tag type="value"] "text content" placeholder="hint"
│    │   │             │               │
│    │   │             │               └─ Other attributes shown
│    │   │             └─ Visible text
│    │   └─ Key attributes
│    └─ HTML tag (or accessibility role)
└─ Unique ref ID within THIS snapshot
```

### Ref lifecycle — when refs go stale

Refs are invalid after any of these:

- Page navigation (`open`, click that follows a link, form submission with redirect).
- SPA route change (URL changed without a hard navigation).
- Tab switch (`tab N`) — refs are scoped to one tab.
- Modal opens or closes.
- Dynamic content loads (AJAX, infinite scroll, dropdown expansion).
- Any time you have not snapshotted in many steps and the page might have changed.

Symptom of using a stale ref: `Error: ref @eN not found` or wrong element clicked. Cure: `agent-browser snapshot -i`, then retry with the fresh ref.

### Scoped snapshots — for crowded pages

When `snapshot -i` returns 50+ elements, narrow it:

```bash
agent-browser snapshot -i -s "main"
agent-browser snapshot -i -s "#checkout-form"
agent-browser snapshot -i -s "[role='dialog']"
```

The `-s / --selector` flag takes a CSS selector, not a `@ref`.

### Other snapshot flags

```bash
agent-browser snapshot              # full accessibility tree
agent-browser snapshot -i           # interactive elements only (default for most work)
agent-browser snapshot -i -c        # compact (drops empty structural wrappers)
agent-browser snapshot -i -d 3      # limit depth to 3
agent-browser snapshot -i --json    # JSON output for machine parsing
```

### `snapshot -i` shows ONLY interactive elements

| Element | In `-i`? | Examples |
|---|---|---|
| Links (`<a>`) | yes | Navigation, clickable text |
| Buttons | yes | Submit, toggle, action |
| Inputs | yes | Text, checkbox, radio |
| Textareas | yes | Multi-line |
| Selects | yes | Dropdowns |
| Headings, paragraphs, spans, divs | no | Body text, labels, status |
| Table cells (no link) | no | Data cells |
| Images | no | Unless they have alt text |

For non-interactive text use `get text SELECTOR` (single match) or `eval --stdin` (multiple). See `SKILL.md` Scenario C.

### JSON schema for `snapshot -i --json`

```json
{
  "success": true,
  "data": {
    "origin": "https://example.com",
    "refs": {
      "e1": { "name": "Submit", "role": "button" },
      "e2": { "name": "Email",  "role": "textbox" }
    },
    "snapshot": "- button Submit [ref=e1]..."
  },
  "error": null
}
```

The refs live at `.data.refs`. There is no `.elements[]` array.

```bash
# Get all refs
agent-browser snapshot -i --json | jq '.data.refs'

# Filter by role
agent-browser snapshot -i --json | jq '.data.refs | to_entries[] | select(.value.role == "button")'

# Compact list with names
agent-browser snapshot -i --json | jq '[.data.refs | to_entries[] | {ref: .key, name: .value.name, role: .value.role}]'
```

### Hidden UI components

Dropdowns, popovers, accordions, modals, autocompletes, tab panels — their children only enter the DOM after a user action. They will NOT appear in `snapshot -i` until triggered.

Signs: a button with a chevron, an accordion header, an autocomplete input where you typed nothing yet.

Discovery loop:

```bash
agent-browser snapshot -i           # shows the trigger but no children
agent-browser click @eN             # the trigger
agent-browser wait 500              # let it render
agent-browser snapshot -i           # now the children appear
```

If clicking does nothing, try `hover @eN` then re-snapshot.

### Selector priority (when refs are not available)

1. `@refs` from `snapshot -i` — most stable, lowest tokens.
2. Semantic locators — `find role button click --name "Submit"`, `find label "Email" fill "..."`. Framework-agnostic.
3. CSS selectors — used inside `get text`, `is visible`, etc. Strict-mode: exactly one match.
4. XPath — last resort, brittle.

---

## Part 2 — Sessions

A session is a browser context with its own cookies, storage, IndexedDB, cache, history, and open tabs. agent-browser supports three persistence strategies that are NOT interchangeable:

| Strategy | What persists | Across runs? | Combine with others? | Best for |
|---|---|---|---|---|
| (none) default ephemeral | nothing | no | — | one-off tasks, default for everything |
| `--session NAME` | cookies + storage within one run | no (without `state save`) | yes, with explicit `state save/load` | parallel isolated work in one run (multi-account testing) |
| `--session-name NAME` | cookies + localStorage | yes, auto | not with `--profile` or `--state` | named app/account state across runs |
| `--profile PATH` | cookies + localStorage + IndexedDB + service workers + cache (full Chrome profile) | yes, native | not with `--state` or `--session-name` | single-user "always logged in" |
| `state save FILE` / `state load FILE` | snapshot of cookies + storage to JSON file | yes, manual | with `--session` for explicit imports | portable state files for CI |

Pick exactly one. Mixing them confuses persistence.

### Session command

```bash
agent-browser session               # which session am I in?
agent-browser session list          # list all active sessions
```

### `--session` (one-run isolation)

```bash
agent-browser --session auth   open https://app.example.com/login
agent-browser --session public open https://example.com
agent-browser --session auth   fill @e1 "user@example.com"
agent-browser --session public get text body
```

Each session has independent cookies/storage/history/tabs. Use named sessions when you genuinely need parallel isolated work in the same run (e.g., admin + viewer at the same time). Otherwise stay in the default session.

### `--session-name` (auto-save across runs)

```bash
agent-browser --session-name myapp open  https://app.example.com
agent-browser --session-name myapp fill  @e1 "user@example.com"
agent-browser --session-name myapp close   # state auto-saved

# A day later:
agent-browser --session-name myapp open  https://app.example.com
# → cookies/storage restored; usually still logged in
```

The state file lives under `~/.agent-browser/states/` and is keyed by the session name. Set `AGENT_BROWSER_ENCRYPTION_KEY` (64-char hex) before save/login to encrypt at rest. `AGENT_BROWSER_STATE_EXPIRE_DAYS` auto-expires stale states (default 30 days).

### `--profile` (full Chrome persistence)

```bash
export AGENT_BROWSER_PROFILE="$HOME/.agent-browser/profile"
agent-browser open https://app.example.com    # authenticated automatically
```

Or per-command:

```bash
agent-browser --profile ~/.myapp open https://app.example.com
```

`--profile` cannot be combined with `--state` or `--session-name`. The profile manages its own state natively.

Use different paths for different test users:

```bash
agent-browser --profile ~/.profiles/admin  open https://app.example.com
agent-browser --profile ~/.profiles/viewer open https://app.example.com
```

### State files (`state save` / `state load`)

```bash
agent-browser state save  ./auth-state.json
agent-browser state load  ./auth-state.json
```

The file contains:

```json
{ "cookies": [...], "localStorage": {...}, "sessionStorage": {...}, "origins": [...] }
```

Treat state files as secrets — they contain session tokens. Add `*.auth-state.json` to `.gitignore`. Delete after use, or set `AGENT_BROWSER_ENCRYPTION_KEY` for encryption.

### Cleanup

```bash
agent-browser close                      # close current session
agent-browser --session auth close       # close a named session
agent-browser close --all                # close every session (use with care)
```

Close only sessions you created. If you joined a pre-existing context, leave it.

---

## Part 3 — Tabs and windows

`tab` lists, switches, opens, and closes tabs within the current session/window. `window new` opens a separate browser window.

```bash
agent-browser tab                       # list (also `tab list`)
agent-browser tab new                   # open blank new tab; focus does NOT auto-switch
agent-browser tab new https://docs/...  # open URL in new tab; focus does NOT auto-switch
agent-browser tab 2                     # switch focus to tab index 2
agent-browser tab close                 # close current tab
agent-browser tab close 1               # close tab index 1
agent-browser click @eN --new-tab       # click a link, force it open in new tab
agent-browser window new                # open a new browser window
```

After any `tab new`, `tab N`, `click ... --new-tab`, popup, or window switch:

```bash
agent-browser tab                       # confirm which tab is active
agent-browser get url                   # confirm focus
agent-browser get title
agent-browser snapshot -i               # refs from the previous tab are gone
```

Treat every tab change as a navigation event for ref lifecycle. See `SKILL.md` Scenario B.

---

## Part 4 — Authentication

### Strategy decision

| Situation | Strategy |
|---|---|
| One-off scrape, no auth needed | default ephemeral |
| Single test user, "always logged in" | `--profile PATH` (set `AGENT_BROWSER_PROFILE` globally) |
| Named app, want auto-resume across runs | `--session-name NAME` |
| Already logged in to Chrome on the host | `--auto-connect`, save state once |
| Multiple credentials managed centrally | `auth save` / `auth login` (auth vault) |
| Portable state file for CI | `state save FILE` once, `--state FILE` in CI |
| Manual auth / 2FA required | `--headed` with `--session-name`, complete in the window |

### Auth vault (recommended for credential reuse)

Stores credentials encrypted on disk and replays the login flow on demand. The model never sees the password.

```bash
# Save (password via stdin — never as a CLI arg)
echo "$PASSWORD" | agent-browser auth save github \
  --url https://github.com/login \
  --username user@example.com \
  --password-stdin

# Use
agent-browser auth login github       # navigates, fills, submits

# Inspect / clean up
agent-browser auth list
agent-browser auth delete github
```

Set `AGENT_BROWSER_ENCRYPTION_KEY` before save/login to encrypt the vault entries.

### Import auth from your running Chrome

Fastest way to bootstrap. Requires Chrome already logged in to the target site.

```bash
# Step 1 (one-time): start Chrome with remote debugging
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222

# Step 2: log in normally in that Chrome window

# Step 3: grab the state
agent-browser --auto-connect state save ./my-auth.json

# Step 4: use it
agent-browser --state ./my-auth.json open https://app.example.com/dashboard
```

`--remote-debugging-port` exposes full browser control on localhost — use only on trusted machines.

To make the imported auth auto-persist:

```bash
agent-browser --session-name myapp state load ./my-auth.json
# From now on, state is auto-saved/restored under the name "myapp".
```

### Basic login flow (manual, when you need to log in once and save)

```bash
agent-browser open https://app.example.com/login
agent-browser wait --load networkidle
agent-browser snapshot -i
# (refs: @e1=email, @e2=password, @e3=submit)
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "$APP_PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save ./auth-state.json
```

Subsequent runs:

```bash
agent-browser state load ./auth-state.json
agent-browser open https://app.example.com/dashboard
agent-browser get url    # confirm not bounced to /login
```

### OAuth / SSO

```bash
agent-browser open https://app.example.com/auth/google
agent-browser wait --url "**/accounts.google.com**"
agent-browser snapshot -i
agent-browser fill @e1 "user@gmail.com"
agent-browser click @e2
agent-browser wait 2000
agent-browser snapshot -i
agent-browser fill @e3 "$GOOGLE_PASSWORD"
agent-browser click @e4
agent-browser wait --url "**/app.example.com**"
agent-browser state save ./oauth-state.json
```

### 2FA

```bash
# Show the browser so the human can complete the second factor
agent-browser --headed --session-name myapp open https://app.example.com/login
agent-browser --session-name myapp snapshot -i
agent-browser --session-name myapp fill @e1 "user@example.com"
agent-browser --session-name myapp fill @e2 "$APP_PASSWORD"
agent-browser --session-name myapp click @e3

# Wait for the human; long timeout
AGENT_BROWSER_DEFAULT_TIMEOUT=120000 agent-browser --session-name myapp wait --url "**/dashboard"
# State is auto-saved under "myapp" on close.
```

### HTTP Basic auth

```bash
agent-browser set credentials user pass
agent-browser open https://protected.example.com/api
```

### Cookie-based auth

```bash
agent-browser cookies set session_token "abc123xyz" --domain .example.com --path /
agent-browser open https://app.example.com/dashboard
```

### Token refresh handling — what to check, not what to script

When loading saved state, always verify it is still valid before assuming you are logged in:

```bash
agent-browser state load ./auth-state.json
agent-browser open https://app.example.com/dashboard
agent-browser get url
# If it shows /login or /signin — the session expired; re-run the login flow.
```

If you discover the session is expired mid-task, do the inline login flow once more and `state save` again. Do not paper over expirations with retry loops.

### Security

- Never commit state files. Add `*.auth-state.json` to `.gitignore`.
- Set `AGENT_BROWSER_ENCRYPTION_KEY` (64-char hex) for at-rest encryption.
- Pass passwords through env vars, stdin, or the auth vault — never as CLI args.
- Set `AGENT_BROWSER_STATE_EXPIRE_DAYS` to auto-expire saved state.
- After a job that used `--profile`, `--session-name`, or saved state, name explicitly in the output contract what state remains on disk.
