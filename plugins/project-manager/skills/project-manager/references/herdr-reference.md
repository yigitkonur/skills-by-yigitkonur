# Herdr Reference — worktrees, socket API, config, panes

Verified against `herdr 0.8.0-preview.2026-08-04-d78e3d3b5126` via `herdr --skill`,
`herdr api schema --json`, `herdr --default-config`, group help output, and live read-only
probes. Project-agnostic.

`herdr --skill` prints the official agent instruction file — when this document and the
installed binary disagree, the binary wins. Re-run it after any `herdr update`.

## Command reference

| Area | Command | Purpose |
|---|---|---|
| Worktree | `herdr worktree list [--workspace ID \| --cwd PATH]` | List worktrees for the repo owning that workspace/cwd |
| Worktree | `herdr worktree create [--branch NAME] [--base REF] [--path PATH] [--label TEXT] [--no-focus]` | Branch + checkout + workspace + tab + pane, one call |
| Worktree | `herdr worktree open (--path PATH \| --branch NAME) [--no-focus]` | Re-open an existing checkout as a workspace |
| Worktree | `herdr worktree remove --workspace ID [--force]` | Remove the checkout; the branch survives |
| API | `herdr api schema [--json]` | Full request/response/event JSON Schema |
| API | `herdr api snapshot` | One-shot full live state |
| Config | `herdr --default-config` | Annotated default config.toml |
| Config | `herdr config check` | Validate config.toml |
| Config | `herdr server reload-config` | Hot-apply config edits |
| Integration | `herdr integration install <kind>` | Wire native lifecycle/session hooks for an agent kind |
| Integration | `herdr integration status [--outdated-only]` | Installed integration versions / drift |
| Pane | `herdr pane neighbor --direction left\|right\|up\|down` | Adjacent pane ID, no focus change |
| Pane | `herdr pane process-info [--current]` | Real PID / argv / cwd of the foreground process |
| Pane | `herdr pane wait-output <id> (--match\|--regex) [--timeout MS]` | Block until output matches |
| Pane | `herdr pane run <id> <command>` | Send command text + Enter atomically |
| Pane | `herdr pane zoom [id] [--toggle]` | Maximize / restore a pane |
| Notification | `herdr notification show <title> [--body] [--sound]` | Toast the human |
| Session | `herdr session list \| attach \| stop \| delete` | `stop`/`delete` are destructive |

---

## A. Worktrees — the native way

Choosing *which* primitive to create — pane, tab, worktree, or workspace — is a supervision
decision, not a Herdr detail; it lives in `supervising-agents.md` §0. What follows is the
mechanical reference for the worktree path.

Project-manager default bias:
- if the work belongs to the same branch/same acceptance goal the user is already watching, do **not** open a worktree — split a sibling pane
- if the worker needs true checkout isolation or a separately mergeable lane, open a worktree
- if you are tempted to use a worktree only because "it feels cleaner", stop; that is usually over-engineering, not safety

The docs frame Herdr as three primitives: **layout** (workspace/tab/pane) creates terminal
locations, **pane** controls a raw terminal, **agent** controls a recognised coding agent. A
pane exists with or without an agent, and `agent start` needs an *available* shell pane —
one whose interactive shell owns the foreground, with no command, editor, or agent running.
It never creates layout.

Creating a workspace also creates its first tab and root pane; creating a tab creates its
root pane. Layout creation and pane splitting **leave focus unchanged by default**;
`--no-focus` states that explicitly, which is worth writing so the intent is legible.

### Creating the checkout

One call does branch + checkout + workspace + tab + root pane and returns every ID you need.

```bash
herdr worktree create --branch fix/thing --base main --no-focus
```

Flags: `--workspace ID` / `--cwd PATH` (which repo to fork from), `--branch NAME`,
`--base REF`, `--path PATH` (explicit checkout path, otherwise derived from config),
`--label TEXT`, `--focus` / `--no-focus` (defaults to non-focus).

End to end, `create`:

1. runs the `git worktree add` equivalent at the resolved path
2. creates a **workspace** (sidebar entry) wrapping that checkout
3. creates a **tab** in that workspace
4. creates a **root pane** cwd'd into the checkout

The response type is `worktree_created`, carrying `workspace`, `tab`, `root_pane`, and
`worktree` objects. **Read the path back from the response — never hardcode one.** The
documented default layout is `<worktrees.directory>/<repo>/<branch-slug>`, but `--path`
or config can change it.

```bash
# Parse what you actually got back
herdr worktree create --branch fix/thing --base main --no-focus \
  | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; print(r["worktree"]["path"], r["root_pane"]["pane_id"])'
```

### `open` vs `create`

Use `open` when the checkout already exists on disk — from a previous session, or from a
raw `git worktree add` outside Herdr:

```bash
herdr worktree open --path /abs/path/to/checkout --no-focus
herdr worktree open --branch fix/thing --no-focus
```

The `worktree_opened` response includes `already_open` — if a live workspace already
represents that worktree, Herdr returns it instead of duplicating. Using `create` on an
existing branch/path is redundant and error-prone; check `list` first.

```bash
herdr worktree list --cwd "$PWD"
```

Returns each worktree with `path`, `branch`, `is_linked_worktree`, `is_prunable`, and
`open_workspace_id` — the last tells you which are already live in Herdr.

### `remove`

```bash
herdr worktree remove --workspace <id> [--force]
```

Removes the git checkout and closes the Herdr workspace. **The branch itself is never
deleted.** `--force` is only for when git refuses (uncommitted changes) — don't pass it
reflexively, since that's exactly the case where a human should look first.

### Why native over raw `git worktree add`

- One structured response with all IDs, versus a bare directory you then have to wire up
- Herdr tracks the repo relationship (`repo_key`, `open_workspace_id`) so `list`/`open`
  can prevent duplicate representations
- `remove` coordinates git removal with workspace close — no orphaned sidebar entries

### The worktree gotcha that cost a round

A worktree created outside the normal path may lack repo-local `.claude/` runtime files.
If the checkout has no `.claude/hooks/` but the repo configures hooks, **every
UserPromptSubmit in that pane fails and the prompt never reaches the model** — the pane
just bounces back to idle almost instantly.

Detect: `foreground_cwd` points into a worktree, and prompts return to `idle` far too fast
with a hook error in the raw scrollback.

Repair: copy the hooks directory in from the main checkout, then resend and confirm
`working` follows.

```bash
cp -a <main-checkout>/.claude/hooks/. <worktree>/.claude/hooks/
```

Projects can avoid this permanently by listing such untracked-but-required files in
`.worktreeinclude` where the tooling supports it.

---

## B. Socket API and the event stream

Newline-delimited JSON over a Unix socket: `~/.config/herdr/herdr.sock` (default session)
or `~/.config/herdr/sessions/<name>/herdr.sock`. `HERDR_SOCKET_PATH` overrides it. Every
`herdr <group> <sub>` command is a thin wrapper: open socket, one request, print, exit.

```json
{"id": "req_1", "method": "ping", "params": {}}
{"id": "req_1", "result": {"type": "pong", "version": "0.8.0-preview...", "protocol": 19}}
{"id": "req_1", "error": {"code": "not_found", "message": "pane not found"}}
```

`herdr api schema --json` is the authoritative method list — `request.oneOf` enumerates
every `{method, params}` pair (~70 methods at protocol 19). Grep for `"const":` under
`properties.method` rather than trusting any written list, since methods ship between
versions.

### Push events instead of polling

For long supervision, subscribing beats looping `agent get`. **`pane_id` is required on
every subscription** — there is no wildcard. Omitting it returns `invalid_request: missing
field 'pane_id'` *and closes the connection*. Watch N panes by passing N entries:

```json
{"id": "sub_1", "method": "events.subscribe", "params": {"subscriptions": [
  {"type": "pane.agent_status_changed", "pane_id": "w1:p2"},
  {"type": "pane.output_matched", "pane_id": "w1:p2", "source": "recent_unwrapped",
   "match": {"type": "substring", "value": "DONE"}}
]}}
```

`agent_status` is an optional extra filter on `pane.agent_status_changed`; omit it to get
every transition. First line back is `{"id":"sub_1","result":{"type":"subscription_started"}}`;
pushed events arrive as bare lines carrying **no `id`**:

```json
{"event":"pane.agent_status_changed",
 "data":{"pane_id":"wRB:p6","workspace_id":"wRB","agent_status":"done","agent":"claude"}}
```

**Naming gotcha — the spelling depends on the method, not on request-vs-event:**

| Where | Spelling |
|---|---|
| `events.subscribe` filter `type` | dot — `pane.agent_status_changed` |
| Pushed subscription event `event` | dot — `pane.agent_status_changed` |
| `events.wait` `match_event.event` | underscore — `pane_agent_status_changed` |
| `events.wait` result envelope | underscore — `pane_agent_status_changed` |

Using a dot in `events.wait` is a hard error: `unknown variant`, returned with an **empty
`id`**, and the server drops the connection. Re-read the schema rather than guessing.

Only three subscribable types exist: `pane.agent_status_changed`, `pane.output_matched`,
`pane.scroll_changed`. `AgentStatus` values: `idle`, `working`, `blocked`, `done`,
`unknown` — but `pane report-agent --state` accepts only `idle`, `working`, `blocked`,
`unknown`, because `done` is *derived* (idle + not yet seen), never reported.

Three caveats that break naive monitors:

- **`events.wait` is level-triggered, not edge-triggered.** It returns immediately if the
  pane is *already* in the requested state. A match does not prove a fresh transition
- **No keepalive or heartbeat.** A live subscription can sit silent for a long stretch —
  silence is not failure, so never time out on quiet alone
- **No resume cursor.** Events during a disconnect are lost; after a reconnect re-bootstrap
  with `herdr api snapshot` or `herdr agent list` before trusting incremental state

There is no shell command that tails a continuous stream. `herdr api` has exactly two
subcommands, `snapshot` and `schema` — no `call`, `subscribe`, or `watch`. For a single
expected transition prefer the CLI (`herdr agent wait <target> --until blocked --timeout
120000`), which is server-owned and event-driven rather than a poll. Open a raw socket only
when you genuinely need a long-lived multi-pane monitor.

Bootstrap pattern: `herdr api snapshot` once for full state, then `events.subscribe` to
stay in sync incrementally.

---

## C. Configuration

- Path: `~/.config/herdr/config.toml`; override with `HERDR_CONFIG_PATH`
- Validate: `herdr config check`
- Hot reload: `herdr server reload-config` (some startup-only keys still need a restart)
- Reset keybindings: `herdr config reset-keys` (backs up first)

Sections a supervisor cares about:

| Section | Keys | Why it matters |
|---|---|---|
| `[worktrees]` | `directory` (default `~/.herdr/worktrees`) | Where `worktree create` puts checkouts when `--path` is omitted |
| `[terminal]` | `new_cwd`, `default_shell`, `shell_mode` | cwd for panes/tabs created without explicit `--cwd` |
| `[session]` | `resume_agents_on_restore` | Whether agent panes reconnect to native sessions after a server restart — needs integrations reporting session refs |
| `[ui.toast]` | `delivery` (`off`/`herdr`/`terminal`/`system`), `delay_seconds` | Whether background state changes ever reach the human |
| `[ui.sound]` | `enabled`, per-agent overrides | Audio cue on state change |
| `[keys]` | `prefix`, `new_worktree`, `open_worktree`, `remove_worktree` | Worktree keybindings (some unset by default) |
| `[experimental]` | `allow_nested` | Must be true to launch herdr inside a herdr pane; off by default |
| `[advanced]` | `scrollback_limit_bytes` (default 10,000,000) | How far back `pane read` can reach |

`herdr --default-config` is the ground truth for every key and default — it's regenerated
per version, so read it rather than trusting a summary.

Detection notes: labels are canonical IDs only (`claude`, `codex`, `pi` — not
`claude-code`). Custom signal is pushed via `herdr pane report-metadata <id> --source <hook>
--token name=value`. `HERDR_PROCESS_DETECTION` selects `native` (default) or
`child-groups` (Linux opt-in).

---

## D. Integrations

```bash
herdr integration install <kind>
herdr integration status --outdated-only
```

Supported kinds: `pi`, `omp`, `claude`, `codex`, `copilot`, `devin`, `droid`, `kimi`,
`opencode`, `kilo`, `hermes`, `qodercli`, `cursor`, `mastracode`, `antigravity-cli`,
`grok`.

An installed integration lets the agent (or its hook) actively **report** lifecycle state
via `pane.report_agent` instead of Herdr inferring it from screen content. That means:

- far fewer `unknown` classifications — if a pane is chronically `unknown`, installing the
  matching integration is the direct fix
- `agent_session` tracking, which is what makes `[session] resume_agents_on_restore` able
  to reconnect a pane after a restart

`integration install` is mutating — don't run it mid-mission on a pane doing real work.

---

## E. Pane primitives worth knowing

| Primitive | When a supervisor reaches for it |
|---|---|
| `pane neighbor --direction ...` | Find "the pane to my right" by ID without changing focus — safer than guessing IDs |
| `pane edges` | Check which sides are tab boundaries before choosing a split direction |
| `pane process-info` | Ground truth on what's actually running when `agent_status` is `unknown` — is the process alive or exited? |
| `pane wait-output <id> --match ...` | Block for a specific string (a build's success line) instead of polling `pane read` |
| `pane run <id> <cmd>` | Fire an ordinary shell command in a sibling pane (text + Enter atomically). For shell commands, never for agent prompts |
| `pane move` / `pane swap` | Relocate or reorder panes across tab/workspace boundaries |
| `pane zoom [--toggle]` | Temporarily maximize a pane to read dense output |
| `pane send-text` vs `send-keys` | `send-text` types literal characters (no Enter); `send-keys` sends key events (`esc`, `ctrl+c`, `enter`). Use `agent prompt` for agent turns, not raw pane input |
| `pane report-agent` / `report-metadata` | Push custom lifecycle/label signal — the mechanism integrations use internally. Only needed when building a hook for an unsupported agent kind |

Read sources: `visible` (viewport only), `recent`, `recent-unwrapped` (soft-wraps joined —
best for transcripts), `detection` (the plain-text snapshot used for classification).

---

## F. Notifications

```bash
herdr notification show "Mission complete" \
  --body "Worker finished the refactor; 0 test failures." \
  --sound done --position bottom-right
```

The response reports `shown: bool` plus a `reason` (`shown`, `disabled`, `rate_limited`,
`no_foreground_client`, `busy`) — check it rather than assuming delivery, since it depends
on the human's `[ui.toast] delivery` config and whether a client is attached.

Use `--sound done` when a long mission finishes, `--sound request` when something needs a
human decision the supervisor can't make (e.g. the worker hit `blocked`).

---

## G. Session and server management — the destructive corner

```bash
herdr session list [--json]
herdr session attach <name>
herdr session stop <name>      # DESTRUCTIVE
herdr session delete <name>    # DESTRUCTIVE
herdr server stop              # DESTRUCTIVE — kills the server and every pane process
```

None of these is ever a routine supervisor action. Never use them to "reset" a stuck
agent — that's what scoped, reversible tools are for (`agent send-keys <target> esc`,
or closing a single pane you created). Run them only when the human explicitly asks to
tear the server or a named session down.

`herdr server reload-config` is the one safe command in this group.

---

## Verification notes

Verified live: `--skill`, `api schema --json`, `--default-config`, all group help,
`worktree list --json`, `api snapshot`. Confirmed against herdr.dev configuration and
socket-API docs, which agree with the schema.

Not verified (would have required mutating a live session): the exact output format of
`config check`, and the precise filesystem side effects of `integration install` per
target.
