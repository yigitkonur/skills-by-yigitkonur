# herdr CLI facts (0.9.3)

Back to [SKILL.md](../SKILL.md). Seen in runs unless marked [help] (read from
`--help` or usage only). Case numbers (T1 …) point to
[tests/README.md](../tests/README.md).

## Help

- `herdr <group> <sub> --help` prints that command's usage (exit 0) and runs
  nothing: swept over every command locally on 2026-10-02, two spot checks on
  monster; `workspace create --help` created no workspace. Option descriptions
  are mostly empty; the flag names and value sets are what it gives. The bare
  group prints its command list (exit 2).
- `herdr completion zsh` holds the whole tree (18 groups, 104 leaf commands,
  every flag) without running anything; `python3 tests/lint.py --tree` lists
  it with flags and values. `herdr --skill` prints the bundled skill.
- Not probed with `--help`, because the top-level usage routes some of them
  itself: `update`, `server` (bare, `stop`, `reload-*`), `config reset-keys`,
  `channel set`, every `attach`/`observe`/`control`, `machine reconnect`,
  `plugin install`, `session stop`/`delete`.

## Subcommands used or listed

- workspace: list, create (`--cwd`, `--label`, `--env`, `--focus`/`--no-focus`),
  get, focus, rename, report-metadata, close (`--group`, accepted although its
  `--help` omits it)
- tab: list (`--workspace`), create (`--workspace`, `--cwd`, `--label`,
  `--no-focus`)
- pane: list (`--workspace`), get, split, move, close, read (`--source visible`,
  `recent`, `recent-unwrapped`, `detection`; default `recent`), run,
  wait-output, send-text, send-keys, process-info (takes `--pane <id>`; a
  positional ID is an unknown option)
- agent: list, get, read (the same four sources), explain, prompt, wait,
  send-keys, start, rename (`--clear` drops the name, T5), focus (moves the
  user's view; never run here); attach is interactive (never from Raycast)
- worktree: list, create, open, remove
  (lifecycle in [orchestration.md](orchestration.md))
- api snapshot; machine list, status, reconnect (reconnect needs the user)
- read-only, seen: `status client --json` (this Mac's client: version,
  channel, protocol, capabilities, binary, session), `status server --json`
  (also over `--machine`; on monster version 0.9.3, protocol 22, compatible,
  session default), `integration status` (exit 2 over `--machine`, so run it
  on the machine itself: monster lists claude v10, codex v8, droid v3, kimi v7,
  cursor v1, antigravity-cli v3, grok v2; `--outdated-only` printed nothing
  on either machine, T18), `session list --json`, `config check`,
  `channel show`, `plugin list --json` (forwarded; four plugins on monster,
  each keyed `plugin_id`; `--plugin <id>` returns that one)
- listed only [help]: `notification show <title> --body --sound done|request`,
  `server agent-manifests`, `pane layout|edges|neighbor|zoom|swap|resize`,
  `pane report-*`/`release-agent` (for agent hooks, not for us), `terminal`,
  `plugin`; named sessions (`--session <name>`) give an isolated server for
  risky experiments
- flags tried on monster, 2026-10-03:
  - `pane read --format ansi`, `--ansi` and `--raw` gave byte-identical
    output: colours re-rendered by Herdr (the shell's `ESC[31m` came back as
    `ESC[0m` then `ESC[38;5;1m`) and CRLF line ends; `--format text` is the
    default. `agent read --format ansi` pads each row to the pane's width;
    stripped of colours and padding it equals the text read (T14).
  - `pane wait-output --raw` changed nothing seen: no pattern holding an ESC
    matched (three tried, on monster and locally), plain `RED48` matched with
    or without it, and its reply's `read` stayed text (T14).
  - `agent explain`: `--format json` is `--json`; without either it prints
    five lines of text, and `--verbose` adds every rule's matchers and region
    (37 lines); `--file <saved text>` with `--agent <kind>` classifies
    offline with this Mac's rules in 0.08 s and exits 2 over `--machine`
    (T16).
  - `pane split --ratio 0.3`: the pane being split kept 0.3 (12 of 40 rows),
    the new pane got the rest; the ratio shows in the snapshot's `layouts`
    (`splits`), not in the split's reply. `--right-click pane` (values
    `herdr`, `pane`) changed nothing visible in any reply (T17).
- still [help] only: `notification show --position` (it would show on the
  user's screen)

## Limits and defaults

- `agent start --kind`: claude, codex, agy and 21 others [help].
- `agent start --timeout`: default 30000 ms; the API accepts more than 3000 and
  at most 300000.
- `agent prompt` [help]: an agent already `blocked` gets `agent_blocked` before
  any input is sent; with `--wait`, a submission from a non-working state that
  reaches neither `working` nor `blocked` within 5000 ms gets
  `agent_prompt_stalled`; a caller `--timeout` that runs out first gives
  `timeout`; turns are not tracked. Seen: `/stop` sent to a codex whose turn
  had just ended came back `agent_prompt_stalled` and ran anyway; a prompt
  with `--timeout 0` was never typed, one with `--timeout 1000` timed out in
  1.7 s and was answered (T3). At codex's trust dialog (`blocked`) the prompt
  got `agent_blocked` in 0.8 s and the screen stayed byte-identical (T13); at
  agy's, which reads `idle`, its Enter answered the dialog, the text was lost,
  and `agent_prompt_stalled` came after 12.7 s (T15).
- `agent wait --until idle|working|blocked|done|unknown`, repeatable
  (`--until done --until blocked`); without `--until` it matches `idle`,
  `done` or `blocked`, and `unknown` only when named [help]. It returns at
  once (exit 0) only when the current state matches: on a `done` codex, no
  `--until` and `--until done --until blocked` returned in under a second,
  `--until blocked` and `--until idle` timed out with exit 1 `timeout` (T2).
  `--timeout 0` checks once: `done` matched in 0.6 s, `--until blocked` timed
  out in 0.8 s (T3). On a `blocked` codex the default set returned in 1.0 s
  and `--until blocked --timeout 0` at once, while `--until idle` timed out
  (T13). Without `--timeout` it waits forever.
- `agent start` help promises "detected … and ready for input"; codex and agy
  returned `idle` with a trust dialog on screen, claude `agent_not_ready`.
  agy's reply even said `interactive_ready: true` over its trust dialog. On
  monster a codex start replied `idle` and `interactive_ready: true`, and the
  next `agent get` read `blocked` (rule `trust_directory`, T12). agy's trust
  dialog stayed `idle` for good: no rule for it in the remote or the local
  rules, `fallback_reason` `default_known_agent_idle_fallback` (T15). Agent
  args go after `--`; claude with `-- --model opusplan --effort high` gave
  `agent_not_ready` in 5.0 s, its dialog `blocked` by `live_blocked_form`
  (T19).
- `agent read --lines N` counts back from the bottom. While codex works, more
  lines than its screen holds (45 on monster) fail with `agent_not_idle`;
  `--source visible` still reads.

## Replies

- `workspace create` → `.result.workspace.workspace_id`, its tab and
  `.result.root_pane.pane_id`
- `workspace get` → the workspace with its `worktree` (`checkout_path`,
  `is_linked_worktree`, `repo_key`, `repo_name`, `repo_root`)
- `tab create` → `.result.tab.tab_id`, `.result.root_pane.pane_id`
- `pane split` → `.result.pane.pane_id`
- `pane get` → the pane with `workspace_id`, `cwd` and `foreground_cwd`; a
  `cd` run in the pane changed both cwds and not `workspace_id` (T11).
- `agent start` → `type: agent_started`, `.result.argv` (what was typed) and
  `.result.agent` with `interactive_ready`.
- `agent prompt` → `type: agent_prompted`; with `--wait` it also carries
  `.result.agent.agent_status`, plus `completion_seq` when it settled `done`
  (not `blocked`). A 2 s turn still came back `done`, not
  `agent_prompt_stalled`.
- `agent wait` and `agent get` → `type: agent_info`, `.result.agent`.
- `pane send-text` → no stdout, exit 0; Turkish and `₺` arrived intact.
- `pane run` → no stdout, exit 0, and nothing about the command's own exit
  status. End the command with a marker that carries it and a nonce new for
  each run, `; echo MARK_<nonce>_$?`: a reused marker matches the previous
  run's line at once (T6).
- `pane wait-output <pane> --regex <re> --timeout <ms>` (or `--match <text>`)
  → `type: output_matched`, `matched_line` and a `read` of the pane
  (`recent_unwrapped`). It searches what is already there before polling
  [help]: a stale `MARK_0` matched in 0.66 s while the next command slept, and
  `--match` on a word in the command matched the typed command line (T6). The
  typed line itself never matched a digits pattern, since it shows `$?`. Its
  `--source` has no `detection`.
- `pane process-info --pane <id>` → `type: pane_process_info`, `shell_pid`,
  `foreground_processes[{argv, cwd, name, pid}]`; a harness's background
  children do not appear.
- `worktree create`/`open` → `worktree_created`/`worktree_opened` with
  `workspace`, `tab`, `root_pane`, `worktree{branch, path, open_workspace_id, …}`;
  `open` on a checkout already open adds `already_open: true` and returns its
  workspace (T7). `worktree remove` → `worktree_removed` (`forced`, `path`,
  `workspace_id`); `worktree list` → `worktree_list` with `source` and
  `worktrees[]`.
- `workspace close` → `{"result":{"type":"ok"}}`; `send-keys` → ok only
- `api snapshot` → `.result.snapshot` with `workspaces`, `tabs`, `panes`,
  `agents`, `layouts`, `version`, `protocol` and the user's focus
  (`focused_workspace_id`, `focused_tab_id`, `focused_pane_id`). Workspaces
  carry `worktree`, panes `terminal_id`, `revision` and `terminal_title`,
  agents `state_change_seq`; 17 of 25 agents on monster also had
  `agent_session` (`agent`, `kind`, `source`, `value`) (T10).
- `agent explain --json` → bare object, no envelope: `state`, `matched_rule`
  (`id`, `priority`, `region`, `state`), `evaluated_rules[]` (each with
  `matched` and `evidence`: its matchers and a `region_preview`),
  `visible_idle`, `visible_blocker`, `visible_working`, `fallback_reason`,
  `warnings`, and the rule set's `manifest_source`, `manifest_version`,
  `cached_remote_version`, `local_override_shadowing_remote` and
  `remote_update_status` (monster codex: 2026.10.01.1, current; agy and
  claude: local overrides in `~/.config/herdr/agent-detection/`, T15, T16).
- Unset fields are omitted, not null (`name`, `completion_seq`, `label`).
- `completion_seq` is absent while an agent works and before its first turn
  ends. It equalled the agent's `state_change_seq` when the turn ended (both
  278), so it grows by more than one per turn (278 → 281 across one prompt):
  compare it with greater-than. Pane `revision` and `terminal_title` stayed the
  same across that turn; only `completion_seq` tracked it (T3). A `done` that
  turned `idle` kept it, and the change did not bump `state_change_seq`
  (claude 325 after a client focused its workspace, 331 with nothing logged;
  T19, T21). An `idle` reached straight from `working` had none (agy 332, and
  356 at the end of a finished team run; T20), so its absence does not say
  the work is unfinished.

## Errors

Exit 1 with `{"error":{"code":…}}` on stderr (stdout is empty, so read with
`2>&1`). Seen: `timeout`; `agent_not_found` (also for a pane without an agent,
and for the name of a closed agent or one cleared with `--clear`);
`agent_blocked`; `invalid_key`; `agent_not_idle`; `agent_not_ready` (claude at
its trust dialog); `agent_prompt_stalled`; `workspace_group_close_required`
(closing a main workspace with worktree workspaces open);
`dirty_worktree_requires_force` (`worktree remove` on untracked or modified
files). Syntax errors exit 2 and print plain usage, not JSON: `worktree list`
given both `--workspace` and `--cwd` (T8). Over `--machine`, a bare `status`,
`agent explain --file` and `integration status` exit 2 as well ("not an
API-backed machine command", T1, T16, T18).

## Keys (`agent send-keys`)

Accepted, in any case: single characters, `enter`, `esc`, `tab`, `shift+tab`,
`space`, `backspace`, `up`, `down`, `left`, `right`, `ctrl+<x>`, `alt+<x>`,
`f1`–`f12`. Rejected: `home`, `end`, `pageup`, `pagedown`, `delete`, `insert`,
and the dash form `ctrl-a`. One bad name rejects the whole list before any byte
is written.

## Machines

- `--machine <label>` forwards API commands only: a bare `status` is refused
  (exit 2, "not an API-backed machine command"), while `status server --json`
  gives the server's version and protocol (T1); so does `api snapshot` →
  `.result.snapshot.version`. `agent explain --file` and
  `integration status` exit 2 the same way: run them on the machine itself
  (T16, T18).
- `machine list --json` gives each label's ssh `target`;
  `machine status <label> --json` diagnoses. Forwarding never installs, starts
  or restarts a server and never falls back to local.
