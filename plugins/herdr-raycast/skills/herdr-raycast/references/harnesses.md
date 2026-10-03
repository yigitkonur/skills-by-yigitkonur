# Harnesses: claude, codex, agy

Back to [SKILL.md](../SKILL.md). Flags are from each CLI's `--help` on
2026-10-02 (local claude 2.1.285, codex 0.160.0, agy 1.2.15; monster claude
2.1.284, codex 0.160.0); behaviour is from runs under Herdr unless marked.

## Who does what (user's practice, 2026-10-02)

| role | harness | after `agent start <name> --kind <k> --pane <p> --` |
| --- | --- | --- |
| plan, architecture, stubborn bugs | claude | `--model opus --effort high` (`xhigh` or `max` for the hardest) |
| execute one plan step | agy | `--model gemini-3.8-flash-high` (ids from `agy models`) |
| review someone else's work | any harness but the author's | as above |
| one-off small jobs | whichever is idle | |

`--model opus --effort high` showed "Opus 5.5 with high effort" on screen. Quota
is not a constraint by the user's account, but each status bar shows it (codex
"weekly 8% left", agy "5H"/"7D", claude "5H Limit"); glance before handing out
long work. A project folder's instructions may override this table.

- `grilling` interviews whoever gave the goal until no decision is left open.
  Both machines have it; `grill-me` only hands over to it and on monster is
  slash-only (`disable-model-invocation: true`; the local copies carry
  suffixed names). On monster, "grill me on this before you plan: <goal>"
  made claude load `grilling` by itself (its transcript shows the call), and
  it asked six questions in prose, each with its recommendation, then ended
  the turn: `prompt --wait` came back `done` after 20 s, not `blocked` (T19).
  So a fuzzy planning brief opens with that line; read the questions (from the
  transcript when claude is fullscreen) and answer them in one ordinary
  prompt, from the ledger and the card, relaying only true decisions to the
  user, claude's recommendation first. The question dialogs below came from
  asking for the question tool, not from grilling.
- agy's `/teamwork-preview <task>` forms a team inside agy (monster, T20). It
  first wrote a prompt draft and asked "Question 1/1" how to proceed
  (`blocked`; `enter` took the recommended small team), then ran an
  implementer, three reviewers and a victory auditor: about 22 minutes for a
  one-line file. While the team ran, Herdr settled `idle` once and `done`
  three times, each gone a moment later: its working rule wants the
  `● Agent(…)` rows' animated dots, and the narrow pane cut rows short. So the
  run is over when no `● Agent(` row is left on screen and the result checks
  out on the machine. Meanwhile wait `--until blocked` with a `--timeout` (a
  dialog is the one event that needs you) and read the screen each time it
  times out. Still hand it one plan step, not the plan.
- Asking first works as its own brief: "questions only, no files, end with
  MARKER", then answers, then the build. All three asked through their question
  tools and built what was agreed.

## Flags that matter

| harness | model | effort | autonomy |
| --- | --- | --- | --- |
| claude | `--model` alias (`opus`, `sonnet`, `fable`) or full name | `--effort low, medium, high, xhigh, max` | `--permission-mode acceptEdits, auto, bypassPermissions, manual, dontAsk, plan` |
| codex | `-m <model>`, `-p <profile>`, `-c key=value` | `-c model_reasoning_effort=<level>` (config key) | `-s <sandbox>`, `-a on-request` or `never` (`untrusted` is rejected) |
| agy | `--model` (`agy models` lists them) | `--effort low … max` | `--mode accept-edits` or `plan`, `--sandbox`, `--dangerously-skip-permissions` |

Also: claude `--permission-prompts host|none` (with `--print`); agy `--add-dir`,
`--new-project`, `--project`, `-c`, `-p`. Codex in supervised mode, asking
before it acts: `-- --sandbox read-only --ask-for-approval on-request`. Bypass
and "dangerously" flags are the user's choice, never a default. A rejected flag
is typed into the shell like any other (see "Starting an agent is typing").
With the local configs, all three read and ran commands outside their own
folder without asking; the brief was the only fence.

## First run in a new folder (seen 2026-10-02, local)

| harness | what `agent start` returned | on screen | keys that passed it |
| --- | --- | --- | --- |
| claude | `agent_not_ready`, exit 1, after 3 s | trust dialog, default "No, exit" | `down`, `enter` |
| codex | `idle`, exit 0, after 3 s | "Cannot use the background server" (1 run without daemon / 2 cancel), then "Trust this folder?" | `1`, then `enter` (a second `1` did nothing) |
| agy | `idle`, exit 0, after 4 s | "Yes, I trust this folder" as default | `enter` |

On monster, codex in a fresh worktree showed the trust dialog alone (`enter`);
the background-server dialog depends on the machine, so read the screen rather
than expect it. There (2026-10-03) `agent start` replied `idle` with
`interactive_ready: true` and the next `agent get` read `blocked`, rule
`trust_directory`: Herdr does classify codex's trust dialog, just not before
`start` returns. Past the dialog, codex's header read "permissions: YOLO mode"
and its model "GPT-6.1-Sol medium".

Claude on monster, started with `-- --model opusplan --effort high`, stopped
at its trust dialog: `agent_not_ready` after 5.0 s, the dialog `blocked` by
rule `live_blocked_form` from monster's local rules, and `down enter` passed
it. Its status line then said "bypass permissions on" with no such flag
typed, because monster's `~/.claude/settings.json` sets
`permissions.defaultMode` to `bypassPermissions` (and `"tui": "fullscreen"`);
`opusplan` showed "Sonnet 5.5" outside plan mode (T19).

agy asked although both `/tmp` and `/private/tmp` are in its
`trustedWorkspaces`: it stores the resolved path (`/private/tmp/<dir>`) and a
listed parent does not cover its subfolders. Trust stores: codex
`~/.codex/config.toml` `[projects."<path>"]`, claude
`~/.claude.json` `projects[*].hasTrustDialogAccepted`, agy
`~/.gemini/antigravity-cli/settings.json` `trustedWorkspaces`. Answer the dialog
yourself in folders you created (SKILL.md, "Working with the user"). The answer
outlives the run: codex's `enter` wrote a `[projects."<path>"]` table marking
the folder trusted, and the next codex there started without asking. After a
scratch run, remove that table and nothing else; agy's answer is one entry in
`trustedWorkspaces`. Every running claude rewrites `~/.claude.json`, so leave
claude's entry and record it.

agy's `agent start` once returned `idle` with `interactive_ready: true` while
its pane still showed only the shell line; the trust dialog appeared about 3 s
later. Herdr has no rule for that dialog, in the remote rules or monster's
local ones: it reads `idle`, `--until blocked` timed out, a default wait
returned at once, and a prompt sent into it was taken as the dialog's
`enter`, which trusted the folder and lost the text (`agent_prompt_stalled`
after 12.7 s, T15). Read the screen again a few seconds after an agy start
before prompting.

## Question dialogs (asked for "your question tool, widest mode")

| harness | how it asks | Herdr status | keys |
| --- | --- | --- | --- |
| claude | AskUserQuestion: up to four questions as tabs plus a Submit tab, ASCII previews beside options; more questions come as a second dialog | `blocked` for each dialog | `enter` picks; in multi-select `enter` toggles and a "Next" row moves on; `n` opens notes, typed with `pane send-text`; the Submit tab needs `enter` |
| codex | questions printed in prose plus "Queued follow-up inputs ? 5 questions shift+← to answer"; title "[ . ] Action Required" | `blocked`, then `done` when the turn ended unanswered about 66 s later | answer the prose with an ordinary prompt; `shift+left` is accepted but its effect was not seen |
| agy | `ask_question`: one question per page, "Question n/5", ASCII previews in fences | `blocked` only when the page is short; tall pages read `idle`/`done` | single: arrows and `enter`; multi: `space` toggles, `enter` submits; `→`/`←` move; "Write-in..." opens "Your answer:", typed with `pane send-text`, then `enter` "Submit All" |

- In claude, `enter` while the notes field has focus submits the note alone
  ("notes only") and drops the highlighted option. Leave the field first if
  both should count.
- The agy rule wants a line starting with "question" and a `─` border within the
  bottom 16 non-empty lines; a page whose previews are taller hides both.

## How their screens behave

- **codex** starts in about 5 s on monster; trivial prompts take 4–7 s. Answers
  are `• text` lines and your prompt comes back rewrapped. It redraws one screen
  (45 lines on monster) whose bottom six to eight lines are the input box and
  the status bar (context left, quota). Its window title is the thread name from
  the first prompt and goes stale. A prompt sent mid-turn is folded into that
  turn. Herdr reads its state from the window title, and its trust dialog
  from the top 20 non-empty lines (rule `trust_directory`). Given a model it
  cannot use (`-m hr47-no-such-model`), codex started normally; the first
  prompt printed a 400 error ("not supported when using Codex with a ChatGPT
  account") and the turn settled `done` with exit 0.
- **claude** leaves its transcript in scrollback unless its TUI is fullscreen,
  so `recent` reaches back; fullscreen on monster, `recent` gave only the 20
  visible rows, and the whole turn was in
  `~/.claude/projects/<cwd with / as ->/<session>.jsonl` there (T19).
  Herdr reads its state from the prompt box. A trivial turn took 2 s and still
  came back `done` from `prompt --wait`.
- **agy** also keeps its transcript from the banner on: `▸ Thought for …` lines,
  `● Bash(…)` tool lines, then plain answer lines, above a `>` input box and a
  status line (context, 5H and 7D quota). Herdr reads `working` from its
  command lines and falls back to `idle` when no rule matches.

## Interrupting a turn (monster, an agent running `sleep N` for you)

| harness | key | what happened | what actually stopped the command |
| --- | --- | --- | --- |
| codex | `esc` | turn ended `done` within 1 s ("Conversation interrupted"); the command lived on: "1 background terminal running · /ps · /stop" | `agent prompt <t> "/stop"` without `--wait` |
| codex | `ctrl+c` | menu "Task is still running": 1 Cancel task / 2 Run in background / 3 Exit; status stayed `working` (rule `osc_title_working`), so a wait timed out | `enter` (Cancel) ended the turn `done`, command still alive; then `/stop` |
| agy | `esc`, `ctrl+c` | nothing; status `working` throughout (rule `background_command_working`, bottom 20 lines) | `agent prompt <t> "/tasks"` without `--wait` opens its task list; `k` kills the highlighted task (`cancelled`), the turn ends `done`; `esc` closes the list |
| claude | | not tried | |

Codex options 2 and 3 exit codex itself. Slash commands that start no turn
(`/stop`, `/tasks`) go without `--wait`; with it, `/stop` came back
`agent_prompt_stalled` and still ran. Check the process on the machine
(`pgrep -f`), not the status: `done` arrived while the command still ran.
