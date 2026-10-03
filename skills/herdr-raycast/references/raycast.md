# Raycast tools for waiting and watching

Back to [SKILL.md](../SKILL.md).

## bash

- Default timeout 30 s, maximum 600000 ms. On timeout the call returns
  `timedOut: true`, `exitCode: null` and the partial output, and kills its child
  (for example a herdr wait); the agent is untouched.
- macOS has no `timeout`. Bound waits with herdr's `--timeout MS` and set the
  bash timeout to that plus 30000. Linux machines such as monster do have
  `timeout`.
- Checks on a machine:
  `ssh -o BatchMode=yes -o ConnectTimeout=10 <target> '<cmd>'`, with the target
  from `herdr machine list --json`.
- zsh 5.9: `$PIPESTATUS` is empty (use `setopt pipefail` and `${pipestatus[1]}`);
  `${=VAR}` splits words; an unmatched glob is an error; a trailing `| head`
  hides the exit code. Any command in between, even an `echo`, resets `$?` and
  `${pipestatus[1]}`: a check once printed `exit=0` for a command that had
  exited 2. Take `rc=$?` right after the command.

## Background tasks: the persistent waiter

- `bash` with `run_in_background: true` returns a task id and a `logPath` at
  once. The task outlives the turn and is bounded by the chat, so a background
  wait may omit `--timeout`; a foreground one never may. A background
  `agent wait --timeout 900000` returned normally after 663 s and was read in a
  later turn.
- One task per waited agent, holding a single `agent wait`: each can be read and
  killed by its own id without disturbing the others, and nothing inside it can
  hang half-way. Several waiters, from this chat or others, can watch one agent;
  all of them return.
- `get_task_output` returns when new output arrives or after `wait_seconds`.
  Keep `wait_seconds` at 110 or less: a call still open at 120 s fails although
  the tool advertises 300. `0` returns at once.
- Raycast warns about identical consecutive tool calls ("same tool call with
  identical arguments several times in a row"). When you must look again,
  change the call: `cat` the `logPath`, a different `wait_seconds`, or a bounded
  `agent wait`.
- `kill_task` ends the shell and its herdr children; the agent works on.
  Closing a workspace does not end waits on its agents, so kill your task first.

## When no one is in the chat

Herdr cannot call into a Raycast chat. A finished background wait is noticed when
the chat next runs a turn. If that must happen without the user, an automation
(Raycast's create-automation tool, recurring every 5 minutes, targeting this
chat) can send a short status prompt. Untried here; each run spends a turn, so a
background `herdr wait` stays the default.

## Chat tools worth knowing

- `chat__get-current-chat` gives the chat id that names the ledger folder.
- `create-chat` opens an independent chat with no shared context, for example
  for a blind test of this skill.
- `ai-projects__get-folder-instructions` reads this folder's always-on
  instructions; in a chat outside any folder it fails with "The current chat is
  not in a folder."
- `ai-projects__update-folder-instructions` replaces them whole, so pass the
  full new text *(untested)*.
