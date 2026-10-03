---
name: herdr-raycast
description: "Use if driving Herdr from Raycast AI Chat via bash, locally or over SSH; inside a pane, use herdr."
compatibility: "Raycast AI Chat on macOS (bash tool with background tasks); herdr CLI 0.9.3 locally and on each saved machine."
---

# Herdr from Raycast

Adapted from the skill bundled with herdr 0.9.3 (`herdr --skill`) for one situation:
a Raycast AI chat supervising Herdr agents from outside Herdr. The installed binary
is still the authority for syntax: every `<group> <sub> --help` prints that
command's usage and runs nothing, and `herdr completion zsh` maps all 104
commands with their flags. `herdr --skill` prints the original; its mechanics
hold here, its stance (run inside Herdr, ask before answering) does not.

Reading or editing this skill does not by itself authorize launching agents or
touching existing sessions; a task from the user does, within its scope.

References, relative to this file (`~/.claude/skills/herdr-raycast/`); read one
when the work reaches it:
[orchestration](references/orchestration.md) (ledger, briefs, worktrees, review) ·
[harnesses](references/harnesses.md) (claude, codex, agy) ·
[raycast](references/raycast.md) (waiting, background tasks, automations) ·
[cli](references/cli.md) (syntax, replies, errors, keys) ·
[research](references/research.md) (`research-mcp`) ·
[tests](tests/README.md) (lint, live cases, what to run again).

## Working with the user

The user hands you outcomes, not steps. The work runs in throwaway folders and
git repositories and nothing is in production (unless the project's card says
otherwise), so a wrong move costs a revert, not a loss. The user's attention is
the scarce resource; spend yours instead.

- **Decide what git can undo.** Choosing between sound approaches, answering an
  agent from the brief, retrying, reshaping the plan, trusting a folder you
  created: do it, and note it in the ledger.
- **Facts are yours to find; decisions are the user's.** Before asking, look:
  the ledger, the repo, the machine, `research-mcp`. Split a goal made of
  independent pieces before refining any of them. Ask only what the evidence
  leaves open and what would change the brief (scope, architecture, rework,
  what "done" means), in dependency order; then start, with your assumptions
  written in the ledger and named in your reply.
- **Bring the user only what git cannot undo or evidence cannot settle**: merge
  or push to a default branch, deploy, spending, credentials, bypass-permission
  modes, `--force` removals, deleting what you did not create, a matter of taste
  or direction only they can own. Ask with Raycast's question tool
  (`elicitation`), one question per call: two to four concrete options, your
  recommendation first, each saying what it leads to, no "other" (the user can
  always type). A question left in prose ends the run; the tool keeps it alive.
  Only input the user must write themselves (an idea, a text) is asked plainly.
- **Finished is a fork, not a stop.** Report what was verified, then offer the
  next round as options: what usually follows work of this kind.

## Conducting work through agents

You are the conductor. Agents write, run and check; you decide what is asked of
whom and in what order, and you keep the score. Detail pulled into this chat
crowds out the plan, so stay at the level of briefs, states and receipts.

- **The ledger is your memory.** Attention fades over a long chat and compaction
  drops detail, so the plan lives in `/tmp/herdr-raycast-<chat id>/ledger.md`,
  the id from `chat__get-current-chat`: no other chat writes there, and a resumed
  chat finds its own notes. Read it before acting in a turn; update it whenever
  a state changes. Each waiting agent gets a line: server, name, pane, waiter
  task id, marker, last `completion_seq`.
- **Small briefs, one turn each.** A brief should be finishable in one turn and
  checkable afterwards. Before anything large, ask only for a plan written to a
  file; read it, then hand it out one step at a time. A large task handed over
  whole is lost whole, even by agents that run teams of their own (user's
  experience); the ledger is what lets you cut it small.
- **`herdr wait` is the heartbeat.** Every prompt is followed by a wait and a
  read before the next step is chosen. An unwatched agent drifts, and so does an
  orchestrator that guesses what happened.
- **One command, one reply, one decision.** Run herdr commands one at a time and
  let each reply choose the next. No scripts: a chain that runs unattended also
  fails unattended.
- **Parallel work lives in worktrees; a pull request is its receipt.** One
  worktree per parallel agent, each ending with a pushed branch and an open PR.
  A worktree is a workspace: removing it ends its agent and deletes the
  checkout, so confirm the PR on the machine first, and close the main
  workspace last. Merging stays with the user.
- **The author does not verify its own work.** Cheap, decisive checks (exit
  codes, git state, the PR exists) you run on the machine; reviews and test runs
  go to a second agent.
- **Decide with evidence, brief with conclusions.** Before a library,
  architecture or stubborn-bug decision, ask `research-mcp`: it returns quoted,
  sourced passages instead of whole pages. Give the agent the decision and two
  or three source URLs, not the search.
- **Plan with depth, execute in small steps.** Claude Opus at high effort or
  above writes the plan to a file, as detailed as it can; agy (Gemini 3.8 Flash
  High) executes it one step at a time; a different harness reviews. Quota is
  not a constraint. Flags: [harnesses](references/harnesses.md); the planning
  brief: [orchestration](references/orchestration.md).

## Principles (learned by running it)

- **Trust the reply you already have.** Mutating commands return what they made:
  `workspace create` gives the workspace, its tab and `root_pane`;
  `agent prompt --wait` gives the agent with its settled `agent_status`. Branch on
  that. Query again only when the command itself failed.
- **One snapshot is the map.** `api snapshot` returns every workspace, tab, pane
  and agent, with labels, the server `version` and `protocol`, and where the
  user's view is (`focused_workspace_id`), in one call. On monster eleven
  `tab list` calls took 7 s; the snapshot took under a second. Agents carry no tab
  label, so "the semrush agent" is a join on `workspace_id`/`tab_id` (section 4).
- **Status belongs to panes; an agent is a presence.** Every pane, tab and
  workspace has a status, and an empty shell reports `unknown`. Whether an agent
  is there is answered by the `agent` field, not by the status.
- **`done` is unread news that does not keep.** `done` is a finished turn not
  yet seen in Herdr. Reading, explaining and waiting leave it in place: a
  `done` outlived `agent get`, `pane get`, `visible`, `recent` and
  `recent-unwrapped` reads and 15 s idle. One turned `idle` when the server
  log showed a client focusing its workspace; another turned `idle` with
  nothing logged, while later `done`s in that focused workspace stayed. So an
  `idle` hides whether a turn ended since you last looked; Herdr's record of
  that is `completion_seq`. It is dropped while the agent works and kept in
  the `idle` that follows a `done`, but a finished agy team run ended `idle`
  without one. A `completion_seq` above the ledger's says Herdr saw a turn
  end; whether the work ended is the screen's to say ("The status is Herdr's
  guess").
- **A wait is a process, not a promise.** Killing a wait (`kill_task`, or the
  bash tool timing out) ends only the waiting; the agent works on. The reverse
  does not hold: closing an agent's workspace left its `agent wait` hanging, so
  whoever closes an agent also stops its waiters. Several waiters, from this
  chat and others, can watch the same agent at once.
- **Herdr tracks states, not turns.** A wait matches a state, the current one
  included, not your message; `agent prompt --wait` first waits for the turn
  to start (`working` or `blocked`). Codex folds a prompt sent mid-turn into
  that turn ("Messages to be submitted after next tool call"), so one
  completion answered both; only your marker word tells whose answer it is.
- **The status is Herdr's guess; the screen is the fact.** `blocked` means
  Herdr recognized a dialog, not that every dialog gets recognized. agy's
  question dialog read `done` while tall ASCII previews pushed its header out of
  Herdr's view and `blocked` when it was short, flipping from one question to
  the next; agy's trust dialog has no rule at all and reads `idle`. A settle
  can be a single frame: during an agy team run (`/teamwork-preview`) Herdr
  settled `idle`, then `done` again and again, each `done` with a new
  `completion_seq`, while the team's `● Agent(…)` rows still ran under the
  input box. Codex's question tool showed `blocked`, then ended the turn by itself
  about a minute later with its questions left in prose. So every settle is
  followed by a read: a footer naming keys ("Enter to select", "enter Submit")
  is a dialog whatever the status says; a question in prose is a finished turn,
  answered with an ordinary prompt. Codex's last six to eight lines are its input
  box and status bar (context, quota), so read above them.
- **A read is a screen, not a document.** You get the terminal after the agent's
  UI has rendered it, so code blocks or JSON you asked for may not survive. A
  marker word you chose will, and so will your prompt: codex rewrapped it and
  the marker landed alone on a prompt line. Match the answer's line (`• MARKER`
  in codex), not "any line without my wording".
- **History lives in the agent's UI, not in Herdr.** `recent` holds only what the
  agent left in scrollback. Claude leaves its transcript there unless its TUI is
  fullscreen (`"tui": "fullscreen"` in `~/.claude/settings.json`, as on
  monster). Codex redraws one screen (all four sources gave the same 45 lines,
  even at `--lines 200`), and so does fullscreen claude (`recent` gave its 20
  visible rows). For anything older, ask the agent, or read claude's transcript
  on the machine: `~/.claude/projects/<cwd with / as ->/<session>.jsonl`.
- **The agent's report is a claim; the machine is the witness.** Check results on
  the machine itself (non-interactive `ssh` to the `target` from
  `herdr machine list --json`), not by asking the agent again.
- **The brief is the only fence you bring.** An agent may act without any
  approval dialog (on monster, codex runs in YOLO mode and claude with "bypass
  permissions on"), so scope and limits must travel inside the prompt.
- **Starting an agent is typing; ready is what the screen shows.** `agent start`
  types `<kind> <agent-args>` at the shell prompt and nothing checks the args: a
  rejected flag left its error in the shell while `agent start` waited out its
  timeout (read that with `pane read`). A start that returns is not a ready
  agent either. In new folders claude stopped at its trust dialog with
  `agent_not_ready`, while codex and agy returned `idle`, even
  `interactive_ready: true`, with a trust or daemon dialog on screen. On
  monster the next `agent get` read codex `blocked`, so the reply came before
  the dialog was classified. agy's trust dialog never was: it stayed `idle`, a
  default wait returned at once, and a prompt sent into it was taken as the
  dialog's Enter and came back `agent_prompt_stalled`, the text lost. Read the
  screen after every start (agy's dialog came about 3 s late) and answer what
  it shows.
- **A dialog speaks its own keys.** Each harness prints its keys in the footer
  (codex `y`/`p`/`esc`, claude "Enter to select · Tab", agy "space Toggle ·
  enter Submit"). Send what the screen offers, then read it again. One dialog
  may hold several questions and is still one `blocked`; the next dialog is the
  next `blocked`, so start a fresh wait after each answer.
- **Lifetimes nest.** Closing a workspace ends its panes and their agents;
  `agent_not_found` afterwards confirms the cleanup. Waiters sit outside that
  nest (see "A wait is a process").
- **Stopping a turn is not stopping its work.** `esc` ended codex's turn
  (`done`) while the command it had started ran on in the background; agy
  ignored `esc` and `ctrl+c` until its own task list killed the job. Stop work
  through the harness's task control (codex `/stop`, agy `/tasks` then `k`),
  then confirm on the machine that the process is gone; the status will not
  tell you ([harnesses](references/harnesses.md)).
- **A surprise is a test case.** When a reply contradicts this skill, record it
  in the ledger (command, reply, exit code, versions), reproduce it in a
  workspace you created, and fix every file that states it in one change;
  [tests](tests/README.md) holds the cases, the lint and what to run again.

## 1. Where you are

- You run in Raycast, outside Herdr. `HERDR_ENV` is unset by design. Do not check
  it and do not stop because of it. If `HERDR_ENV=1` *is* set, you are inside a
  Herdr pane: stop using this skill and use the `herdr` skill instead.
- You have no caller pane. Never use `--current`, `$HERDR_PANE_ID`,
  `$HERDR_TAB_ID`, `$HERDR_WORKSPACE_ID` or `herdr pane current`. Give every
  command an explicit pane/tab/workspace ID or a unique live agent name. A command
  with an omitted target can fall back to the UI-focused pane, which belongs to
  the user.
- The user's Herdr TUI is live and you are a second client. Do not focus or switch
  anything unless asked: `agent focus <target>` and `workspace focus <id>` move
  the user's view *(not run here)*. Pass `--no-focus` when creating
  workspaces, tabs, panes or worktrees; with it, three workspaces worked through
  a 15-minute round and the user's focus never moved. Closing a workspace that
  holds the focus moves the user's view to another one.

## 2. Servers: local and saved machines

- Local Mac: `herdr <command>` (socket `~/.config/herdr/herdr.sock`).
- Saved SSH machine: `herdr --machine <label> <command>` on **every** command,
  including discovery. Known label: `monster`. List profiles with
  `herdr machine list --json`.
- `--machine` forwards API commands only: a bare `status` is refused (exit 2,
  "not an API-backed machine command"), while `status server --json` gives the
  server's version and protocol, as does `.result.snapshot.version` from
  `api snapshot`.
- IDs and agent names are scoped to one server. The same ID can exist on both
  (on 2026-10-02 `w4D` was `errands` locally and `aura-monorepo` on monster).
  Always name the server when you report or act: `monster wT:p1Z`, `local w2H:pAG`.
- Do not combine `--machine` with `--session` or `--remote`. Forwarding never
  installs, starts or restarts a server and never falls back to local.
- A connection failure does not prove a mutation was not applied. Inspect remote
  state before retrying.
- Diagnose with `herdr machine status <label> --json`. `herdr machine reconnect`
  needs the user to finish SSH authentication: tell them to run it.

## 3. Raycast tools

Details and evidence: [raycast](references/raycast.md).

- The bash tool times out after 30 s by default, at most 600000 ms; macOS has no
  `timeout` command. Bound every foreground wait with Herdr's `--timeout MS` and
  give the bash call at least that plus 30000. When the tool times out first,
  the command is killed (`timedOut: true`, partial output kept); the agent is not.
- A background task (`run_in_background: true`) is the persistent waiter: it
  outlives the turn (a background `agent wait` returned normally after 663 s),
  may omit `--timeout`. Give each waited agent its own task holding one
  command. Read it with `get_task_output` (`wait_seconds` at most 110) or `cat`
  its `logPath`. Kill it by ID when done, and before closing what it watches.
  Block on the waiter; never poll Herdr (`agent get`, `agent read`) in a loop.
  A lost waiter is replaced: a new `agent wait` returns at once when the
  agent's current state matches its `--until` set, and a `completion_seq`
  above the ledger's says Herdr saw a turn end meanwhile. A finished wait is
  noticed only when this chat next runs a turn; for a chat no one returns to,
  a 5-minute Raycast automation is the costlier fallback
  *(untested; [raycast](references/raycast.md))*.
- Control commands return a JSON envelope (`.result` or `.error`), except
  `agent explain --json`, which prints its object bare (`state`, `matched_rule`,
  `visible_blocker`). `agent read` and `pane read` return plain terminal text.
  Parse JSON with `python3`, read unset fields with `.get` (they are omitted, not
  null), and take IDs from replies instead of predicting them.
- Errors print `{"error":{"code":...}}` with exit 1; syntax errors exit 2. The
  codes seen so far are in [cli](references/cli.md).
- The bash tool runs zsh, where `$PIPESTATUS` is empty. A trailing `| head` hides
  the exit code; use `setopt pipefail` or drop the pipe when the status matters.
  Any command in between, `echo` included, resets `$?`: take `rc=$?` right
  after the command.
- Never run commands that open an interactive client; they hang the bash tool:
  bare `herdr`, `herdr --remote …`, `herdr session attach`, `herdr agent attach`.

## 4. Discover (read-only, safe at any time)

```bash
herdr [--machine m] api snapshot             # whole tree + server version
herdr [--machine m] agent get <target>
herdr [--machine m] agent read <target> --source recent-unwrapped --lines 120
herdr [--machine m] agent explain <target>   # rule and evidence behind a status
herdr [--machine m] status server --json     # server version and protocol
```

`workspace list`, `tab list --workspace`, `pane list --workspace` and
`agent list` are narrower views of the same tree.

Agents carry no tab label, so "the semrush agent" is a join: an agent's
`workspace_id` and `tab_id` lead to the workspace and tab whose `label`s name
it. On a busy machine, cut the snapshot down with a short `python3 -c` filter
over that one reply; shaping a reply is reading, not chaining commands. When
several agents match ("mcp-" matched five on monster), narrow by `cwd` and
last output before asking. A codex title is the thread name from its first
prompt and does not follow later work, so trust labels and names over titles.

When the user asks what is running, check both local and every relevant machine.

## 5. Agent states

- `idle`: ready. `done`: ready, with a finished turn the user has not viewed.
  Neither proves the task succeeded: a codex given a model that does not exist
  printed a 400 error and settled `done`, exit 0.
- `working`: busy.
- `blocked`: Herdr recognized an approval or question dialog. A dialog it
  misses shows as `idle` or `done`; only the screen tells them apart.
- `unknown`: no classification. An empty shell pane reports it too; check the
  `agent` field before concluding an agent is there. Never completion.
- `agent explain <target>` names the detection rule and screen evidence behind a
  status (codex: window title; claude: prompt box). Use it when a state looks
  wrong; `--json` adds every rule evaluated and the rules' `manifest_version`.
  The rules can be the machine's own: on monster, `manifest_source` named a
  local override in `~/.config/herdr/agent-detection/` for agy and claude
  (`local_override_shadowing_remote: true`), so one harness can read
  differently per machine. `agent read <target> --source detection` returns
  the text the rules read (on codex, the visible screen).

Agent commands accept a unique live agent name or the pane ID currently hosting
the agent, not terminal IDs or kind labels. Names match `[a-z][a-z0-9_-]{0,31}`,
follow the current occupant and are cleared when that agent exits or is replaced,
or by `agent rename <target> --clear`; the old name then gives `agent_not_found`
while the pane ID still works.
Pane IDs change when a pane moves to another workspace. Re-resolve targets with
`api snapshot` or `agent list` at the start of each turn instead of trusting IDs
from chat history or the ledger.

## 6. Send work and read results

```bash
herdr [--machine m] agent prompt <target> "$(cat <<'EOF'
...brief...
EOF
)" --wait --timeout 300000          # bash tool timeout >= 330000
```

- Pass the brief through a quoted heredoc as above, so nothing is expanded
  locally.
- `--wait` waits for the first settled `idle`, `done` or `blocked` and returns
  the agent; branch on `.result.agent.agent_status`. Do not add `--until` for
  that default.
- `agent_blocked`: nothing was sent (the screen stayed byte-identical); the
  agent is at a dialog Herdr recognized (see section 7).
- `agent_prompt_stalled`, `timeout` or a connection error: the prompt may or may
  not have been delivered. With `--timeout 0` nothing was typed; with
  `--timeout 1000` it timed out and the agent answered anyway; after
  `agent_prompt_stalled` a codex `/stop` still ran. Run `agent get` and
  `agent read` before doing anything; `agent wait` collects the result. Never
  resubmit blindly.
- Slash commands that start no turn (`/stop`, `/tasks`) go without `--wait`.
- If the agent is already `working`, the wait is satisfied by the current turn
  ending, and codex steers your text into that turn. Send to a working agent
  only when steering is what the user wants; otherwise wait first.
- Without `--wait`, `agent prompt` returns at once (`type: agent_prompted`).
  `--wait --until working` confirms delivery in about a second; collect the
  result later with `agent wait`.
- Which to use: a turn of a few minutes fits a foreground `--wait --timeout`;
  long or parallel work takes `--wait --until working` and then one background
  `agent wait` per agent (section 3). Two worktree agents ran this way.
- Standalone wait: `agent wait <target> [--until blocked] --timeout <ms>`. It
  returns at once (exit 0) only when the current state matches its `--until`
  set (by default `idle`, `done` or `blocked`); otherwise it waits for the
  next match, forever without `--timeout`. `--timeout 0` checks once. `--until`
  repeats (`--until done --until blocked`), which skips an `idle` you do not
  care about, but not a `done` you have already read: that one matches again
  at once, so wait `--until working` first.
- Read results with `--source recent-unwrapped --lines N`; `--lines` counts back
  from the bottom. While codex works, more lines than its screen holds (45 on
  monster) fail with `agent_not_idle`; `--source visible` still reads it. Ask
  the agent to end its answer with a marker word and extract by the last one,
  after the wait returns: agy once printed it mid-turn, before its edits. If the
  answer is longer than a screen or still does not appear, ask the agent to
  write it as Markdown under
  `/tmp` and reply only with the path, then read the file on that same machine
  (for a remote one, over SSH to the target shown by `herdr machine list --json`).
- An agent's claim of success is not verification. Before you report work as
  done, check the files, git state or URLs on the machine, and let a second
  agent review or run the tests when they matter.

## 7. Blocked agents and questions

1. Read the dialog: `agent read <target> --source visible --lines 60` shows the
   question, the command, the agent's reason and numbered options with their
   keys. `agent explain` names the rule that saw it.
2. Answer it yourself when the answer is reversible and inside the brief:
   trusting a folder you created, edits and commands in the agent's own repo,
   a question the brief or plan already settles. Note the answer in the ledger.
3. Otherwise ask the user through `elicitation`: server, pane, the question and
   options as written, what each causes, your recommendation first. Anything on
   the user's list in "Working with the user" always goes to them.
4. Send the key the dialog names:
   `agent send-keys <target> <key> [key ...]`. Accepted: single characters
   (`y`, `1`), `enter`, `esc`, `tab`, `shift+tab`, `space`, `backspace`, arrows
   (`up` …), `ctrl+x`, `alt+x`, `f1`–`f12`, in any case. `home`, `end`,
   `pageup`, `pagedown`, `delete`, `insert` and `ctrl-a` are rejected. One bad
   name rejects the whole list (`invalid_key`) before any byte is written. A
   free-text field (claude's notes, agy's write-in) takes
   `pane send-text <pane_id> '<text>'`,
   which types without Enter and prints nothing. How each harness asks and
   which keys answer it: [harnesses](references/harnesses.md).
5. `send-keys` returns only `ok`. Read the screen and confirm the choice was
   taken before the next wait: a wait matches the current state, so one started
   while the dialog is still up returns that `blocked` at once (1.0 s at codex's
   trust dialog, where `--until idle` timed out instead). After an answer that
   took, `agent wait` returned the turn's end. Declining in codex cancels the
   whole turn, which still ends as `done`.

## 8. Create layout and start agents

There is no caller pane to split from. Choose the workspace or pane explicitly:

```bash
herdr [--machine m] workspace create --cwd <path> --label <label> --no-focus
#   -> .result.workspace.workspace_id, .result.root_pane.pane_id
herdr [--machine m] tab create --workspace <ws> --cwd <path> --label <label> --no-focus
#   -> .result.tab.tab_id, .result.root_pane.pane_id
herdr [--machine m] pane split <pane_id> --direction right|down --cwd <path> --no-focus
#   -> .result.pane.pane_id
herdr [--machine m] agent start <name> --kind <kind> --pane <pane_id> [--timeout MS] [-- <agent-args>]
herdr [--machine m] agent rename <target> <name>
```

- Remote paths must be absolute, `~` or start with `~/`.
- `agent start` needs a shell pane at its prompt with nothing in the foreground.
  A launch that dies surfaces only as `timeout`, so keep `--timeout` near
  30000 (all three harnesses returned in 3–5 s). Every harness met a new folder
  with a trust dialog, `/tmp` subfolders included; the keys per harness are in
  [harnesses](references/harnesses.md). In folders you created, answer it
  yourself.
- Run an ordinary command: `pane run <pane_id> '<cmd>; echo MARK_<nonce>_$?'`
  with a nonce new for each run (single quotes, so `$?` reaches the pane), then
  `pane wait-output <pane_id> --regex 'MARK_<nonce>_[0-9]+' --timeout <ms>`.
  `pane run` itself reports nothing about the command, so the marker carries
  its exit code. `pane wait-output` searches what is already there first: a
  marker reused without a nonce matched the previous run at once, and
  `--match` on a word in the command matched the typed command line.
  `pane send-text` and `pane send-keys` drive panes that have no agent.
- Parallel work goes into `herdr worktree` ([orchestration](references/orchestration.md)).
  Create what the task needs, labelled so it is plainly yours, and close it
  when the task ends; never reshape the user's own workspaces.

## 9. Raycast chat ↔ agent mapping

- Raycast chats cannot be messaged by Herdr agents, so there are no callbacks
  into Raycast. Raycast learns state only by reading Herdr in a turn.
- A Raycast chat or folder that supervises an agent should record its target as
  `<server> <agent-name>` with the last known pane ID as a fallback, in its
  ledger. Prefer agent names over pane IDs; suggest `agent rename` to the user
  when agents are unnamed.

## 10. Safety

- Do not close workspaces, tabs, panes or sessions you did not create unless the
  user explicitly asked. Never add `--group` just to bypass
  `workspace_group_close_required`.
- Stop only your own background tasks, by task ID. Other chats run
  `herdr … agent wait` on the same agents, so never `pkill` or `killall` herdr.
- Never run `herdr server stop`, kill the Herdr process, `herdr update`,
  `herdr config reset-keys` or `herdr server reload-config` unless asked.
- Do not add, remove, enable, disable or reconnect machines unless asked.
- Use `--trust-repository` only for repositories you created or the user
  vouched for.
- A brief may ask an agent to push its own branch and open a PR; everything on
  the user's list in "Working with the user" stays with the user.
- Do not probe a mutating subcommand by omitting its arguments; commands such as
  `workspace create` run with defaults.
- Client and server versions can differ; check `herdr status client --json`
  here and `status server --json` on each server (over `--machine` too) before
  relying on newer features. A missing method is not permission to upgrade a
  server.

## 11. Reporting

- Every state you report must come from command output in the current turn.
- Name the server and pane or agent for each item.
- Report separately what was submitted, consumed, completed and verified.
- If something failed, give the command and its error code, and say which step
  remains unverified.
