# Current command guide

This is a curated routing guide, not an exhaustive frozen command catalog. Refresh syntax from the installed version before guessing:

```bash
agent-browser skills get core
agent-browser skills get core --full
agent-browser COMMAND --help
agent-browser --version
```

The upstream repository's `skills/agent-browser/SKILL.md` is intentionally a discovery stub. The installed `core` skill and command help are version-matched and authoritative.

## Managed-pool note

On Yigit's Mac, plain browser commands use the headed CDP pool. `agent-browser pool real ...` calls the underlying CLI without pool leasing. Read `managed-cdp-pool.md` before explicit CDP/profile/provider/launch mutation.

## Navigation and inspection

```bash
agent-browser open https://example.com     # navigate; first managed open creates a task tab
agent-browser open                         # unmanaged: launch about:blank for pre-navigation setup
agent-browser back
agent-browser forward
agent-browser reload
agent-browser snapshot                     # accessibility tree
agent-browser snapshot -i                  # interactive-first refs
agent-browser snapshot -i -u               # include link URLs
agent-browser snapshot -s '#main'           # scope selector
agent-browser snapshot -c -d 4             # compact, depth-limited
agent-browser read                          # active rendered DOM as readable text
agent-browser read https://example.com      # public URL content negotiation/fallback fetch
```

For a public URL that needs no browser session, prefer:

```bash
agent-browser pool real read https://example.com
```

`read URL` can negotiate Markdown, try `.md`, discover nearby `llms.txt`, and fall back to HTML conversion. Check `read --help` for `--raw`, `--require-md`, `--llms`, `--outline`, `--filter`, and timeout options.

## Interaction

```bash
agent-browser click @e1
agent-browser dblclick @e1
agent-browser fill @e2 'text'               # replace value
agent-browser type @e2 'text'               # type through keyboard events
agent-browser press Enter
agent-browser hover @e3
agent-browser focus @e3
agent-browser check @e4
agent-browser uncheck @e4
agent-browser select @e5 value
agent-browser drag @e1 @e2
agent-browser upload @e6 ./file.pdf
agent-browser scroll down 500
agent-browser scrollintoview @e7
```

Prefer refs or semantic `find` locators. Use quoted arguments and `--stdin` for complex JavaScript rather than shell-fragile interpolation.

## Semantic finders

```bash
agent-browser find role button click --name 'Save'
agent-browser find label 'Email' fill 'person@example.com'
agent-browser find text 'Continue' click
agent-browser find testid submit click
agent-browser find placeholder 'Search' fill 'query'
```

Use `--exact` when partial matches are ambiguous. Run `find --help` for the current supported locator/action matrix.

## Get and assertions

```bash
agent-browser get url
agent-browser get title
agent-browser get text @e1
agent-browser get value @e2
agent-browser get attr @e1 href
agent-browser get count '.row'
agent-browser is visible @e1
agent-browser is enabled @e1
agent-browser is checked @e1
```

These are observation commands, not a complete assertion framework. Compare the output to the expected state and report the actual observation.

## Waits

```bash
agent-browser wait @e1
agent-browser wait '#spinner' --state hidden
agent-browser wait --text 'Saved'
agent-browser wait --url '**/dashboard'
agent-browser wait --load networkidle
agent-browser wait --fn 'document.readyState === "complete"'
agent-browser wait --download ./downloads
agent-browser wait 500
```

Prefer selector/text/URL/load/function waits. A fixed millisecond wait is a last-resort diagnostic.

## Tabs and frames

```bash
agent-browser tab
agent-browser tab new --label docs https://docs.example.com
agent-browser tab docs
agent-browser tab close docs
agent-browser frame '#payment-frame'
agent-browser frame main
```

Tab IDs are strings like `t1`; positional indexes are rejected. `tab new` opens and switches to the new tab. Snapshot again after every tab or frame switch.

## Screenshots, PDF, errors, and diffs

```bash
agent-browser screenshot ./page.png
agent-browser screenshot --full ./full.png
agent-browser screenshot --annotate ./annotated.png
agent-browser screenshot @e1 ./element.png
agent-browser pdf ./page.pdf
agent-browser errors
agent-browser console
agent-browser diff snapshot
agent-browser diff screenshot --baseline ./before.png
```

`--full` is screenshot-specific; `--annotate` is also accepted as a global default. Annotated labels correspond to refs from that capture; state changes invalidate them like any other refs.

## Network, storage, cookies, and headers

```bash
agent-browser network requests
agent-browser network requests --clear
agent-browser network route '**/api/**' --abort
agent-browser cookies get
agent-browser cookies set --curl ./protected-cookie-export.txt
agent-browser storage local get key
agent-browser storage session get key
agent-browser set headers '{"X-Test":"value"}'
agent-browser set offline on
```

These surfaces can expose secrets or change traffic. Read `trust-boundaries.md`; use `COMMAND --help` for exact payload shapes.

## Sessions, restore, and auth

```bash
agent-browser --session task open https://example.com
agent-browser --session task --restore login-key open https://example.com
agent-browser session list
agent-browser session id --scope worktree --prefix qa
agent-browser auth login service --credential-provider vault --item 'Service account'
agent-browser state save ./state.json
```

State files are credentials. The managed pool normally replaces explicit browser sessions with owner-scoped lane leases; do not prepend `--session` to managed commands.

## Debug and performance

```bash
agent-browser trace start
agent-browser trace stop ./debug-trace.json
agent-browser profiler start
agent-browser profiler stop ./profile.json
agent-browser record start ./flow.webm https://example.com
agent-browser record stop
agent-browser pool real --headed --enable react-devtools open https://example.com
agent-browser react tree
agent-browser react inspect COMPONENT_ID
agent-browser vitals
```

`trace` and `profiler` produce Chrome DevTools trace JSON for DevTools or Perfetto, not Playwright trace archives. `record` produces WebM and starts a fresh browser context while preserving cookies/localStorage.

## Batch and JSON

```bash
agent-browser --json snapshot -i
agent-browser batch --bail \
  '["open","https://example.com"]' \
  '["snapshot","-i"]'
```

Use JSON for machine parsing and `batch` only when no intermediate decision is needed.

## MCP and specialized skills

```bash
agent-browser mcp
agent-browser mcp --help
agent-browser skills list
agent-browser skills get electron
agent-browser skills get slack
agent-browser skills get dogfood
agent-browser skills get vercel-sandbox
agent-browser skills get agentcore
```

Use the specialized skill for its runtime, then verify syntax against current CLI help. Do not transplant browser-web assumptions into Electron, Slack, or cloud sandboxes.

## Global flags change

Global options evolve. Current notable categories include session/restore, namespace, profile/state, providers, explicit CDP/auto-connect, headed mode, headers/proxy/user-agent/args, JSON/debug, content boundaries/action policy, engine, screenshots, and idle timeout. Verify exact names and types with `agent-browser --help`; do not resurrect removed `--native` or `AGENT_BROWSER_NATIVE` guidance.
