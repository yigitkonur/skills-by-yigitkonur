# Testing the herdr-raycast skill

Back to [SKILL.md](../SKILL.md). The skill is a set of claims about a CLI and
about agents that change under it. This folder keeps the claims honest: it
finds where the skill disagrees with the installed herdr, where it disagrees
with itself, and what to run again when something changes.

## What is tested

| kind of claim | example | checked by |
| --- | --- | --- |
| CLI contract | `agent read --source detection` exists | layer H, automatic |
| behaviour seen in runs | a turn in an unfocused workspace ends `done` | layer L, by hand |
| self-consistency | SKILL.md and SYSTEM_PROMPT.md state one wait rule | layer S, automatic |
| policy | merges go to the user | review, not tests |

A claim without evidence of its own is marked *(untested)* or credited to its
source (the user's practice, the dossier) where it stands.

## Layers

- **S, static** (`python3 tests/lint.py`): the regression rules below hold in
  every skill file; every case has a Trace line, and every Trace phrase still
  stands in the skill file it names; no code span wraps onto a second line;
  relative links resolve; SKILL.md stays under 500 lines and its frontmatter
  still names its folder and keeps `description` and `compatibility`.
- **H, help contract** (same run): every herdr command, flag and listed value
  shown in a code span exists in the installed CLI (`herdr completion zsh` for
  the tree, `<path> --help` for flags and values); every `agent` subcommand and
  every `--source` value is named; stated counts match the tree. Only `--help`
  and `completion zsh` run, and neither executes a command; paths the binary
  routes itself (update, server, attach …) are never probed. This file's
  runbook gets the drift check too, but not the rules: it quotes old wordings
  on purpose.
- **L, live** (the runbook below, by hand): each case runs in a workspace you
  created, one herdr command per call, its reply read before the next. Not a
  script, on purpose: the skill's own rule is one command, one reply, one
  decision, and a case is only as good as its reading.

`lint.py` exits 1 on any FAIL. A WARN names flags of a command the skill shows
but never mentions; after an update, new flags surface there.
`python3 tests/lint.py --tree agent pane` lists leaves with their flags and
values.

## Regression rules

Each rule fails on something that once went wrong in this skill.

| rule | fails on | because |
| --- | --- | --- |
| R1 | `status` called refused over `--machine` without "bare" or `status server` | bare `status` exits 2; `status server --json` works (T1) |
| R2 | "returns at once" with "settled" but without "match" | a wait returns at once only when the current state is in its `--until` set (T2) |
| R3 | `MARK_$?` or `MARK_[0-9]` without "nonce" | a reused marker matches the previous run at once (T6) |
| R4 | "N sources" unlike the `--source` values in help | there are four (T4) |
| R5 | "N commands" or "N groups" unlike the completion tree (±3 with `~`) | 104 leaf commands, 18 groups on 0.9.3 |
| R6 | delivery after `timeout` stated as certain, without "may or may not" or "whether" | `--timeout 0` typed nothing; `--timeout 1000` timed out and was answered (T3) |
| R7 | "grill" and `blocked` in one paragraph without "prose" | grilling asked its six questions in prose and settled `done`, never `blocked` (T19) |
| R8 | "leaves its transcript" and claude in one sentence without "fullscreen" | with `"tui": "fullscreen"` claude keeps no scrollback, and `recent` read only the 20 visible rows (T19) |
| R9 | "turn ended" with `completion_seq` or "Compare it" in one sentence without "Herdr" | an agy team run settled `done` with a new `completion_seq` three times while its team still worked (T20) |
| SPAN | a code span wrapped onto the next line | lint pairs backticks per line, so it never saw the `agent read` and `--until done --until blocked` that were wrapped |
| TRACE | a case without a Trace line, or a Trace phrase gone from its file | a finding fixed in one file and missed or undone in another |
| FRONT | SKILL.md's `name` is not its folder's, or `description` or `compatibility` is missing | Raycast rewrote SKILL.md through its plugin link (see "Raycast rewrites SKILL.md") |

## Cases

Predictions for T1–T10 went into the ledger at 2026-10-03 00:48 (+03), before
any live run, each with its source in brackets; T11 and T12 were added during
the run. All ran on monster with herdr 0.9.3 on both ends (protocol 22) and
codex-cli 0.160.0; the scratch repo, workspaces and codex trust entry were
removed afterwards.

T13–T20 were predicted at 02:23 the same night and T21 at 02:38 (T15b and
T15c just before their runs), all on monster again with claude 2.1.284,
codex-cli 0.160.0 and agy behind its wrapper; T14, T16 and T18 also ran on
this Mac. The workspaces, the scratch folder and agy's trust entry were
removed afterwards; claude's trust entry in `~/.claude.json`, its project
folder and agy's conversation folders stayed and are recorded in the ledger.

| case | claim under test | prediction | result |
| --- | --- | --- | --- |
| T1 | `status` is refused over `--machine` | bare `status` exits 2; `status server --json` exits 0 with version and protocol [own run 2026-10-02] | PASS: exit 2, "not an API-backed machine command"; `status server --json` exit 0: version 0.9.3, protocol 22, compatible |
| T2 | a wait on a settled agent returns at once | only when the current state is in the `--until` set: on a `done` agent, no `--until` and `--until done` return at once, `--until blocked` and `--until idle` time out [dossier C07] | PASS: no `--until` 0.83 s and `--until done --until blocked` 0.85 s, exit 0; `--until blocked` 5.9 s and `--until idle` 6.1 s, exit 1 `timeout` (an unfocused `done` is not `idle`) |
| T3 | after `timeout` the prompt was still delivered | `agent wait --timeout 0` on a `done` agent returns the match at once [by analogy with `wait-output`, dossier C13]; `agent prompt --wait --timeout 0` exits 1 `timeout` and delivers nothing [dossier C08] | PASS: wait 0.60 s exit 0, and with `--until blocked` exit 1 in 0.77 s, so 0 checks once; prompt exit 1 in 0.70 s, nothing typed. Opposite condition: `--timeout 1000` exit 1 in 1.72 s, yet answered (`completion_seq` 278 → 281). The claim held for 1000 ms, not for 0 |
| T4 | three read sources (cli.md) against "all four" (SKILL.md) | `detection` exists for `agent read` and `pane read`, not for `wait-output`, and returns a plain-text snapshot, the classifier's input [help, dossier C13] | PASS: on codex byte-identical to `visible`, at the trust dialog (14 lines) and after a turn (43 lines); on a shell pane the wrapped screen (25 lines); plain text, no envelope |
| T5 | renaming shows only `rename <target> <name>` | `--clear` drops the name; the old name gives `agent_not_found`; the pane ID still targets the same terminal [help, dossier C12] | PASS: exit 0, no `name` key, same pane, terminal and `completion_seq`; old name `agent_not_found`; pane ID works; renamed back |
| T6 | `echo MARK_$?` with `--regex 'MARK_[0-9]+'` | a reused marker matches the previous run at once; a per-run nonce waits for the new command; `--match` on a word the command types matches its own echo at once [dossier C13, own run] | PASS: stale `MARK_0` in 0.66 s during `sleep 6`; nonce `MARK_q7x_1` after 8.06 s of `sleep 12`; `--match LIT_q8y` hit the typed line in 0.66 s. The typed `MARK_$?` line itself never matched |
| T7 | `worktree open` re-attaches an orphaned checkout | on a checkout already open it returns that workspace with `already_open: true`, and `--label` renames it [dossier C21] | PASS: same workspace, pane and terminal, `already_open: true`, label renamed |
| T8 | the usage offers `--workspace` or `--cwd` | both together exit 2 [usage] | PASS: exit 2, the usage as plain text, no JSON |
| T9 | `idle` and `done` do not prove success | codex given a model that does not exist shows an error and settles like a success [dossier: claude 401] | PASS: start exit 0 in 5.4 s; prompt exit 0 in 5.0 s, `done`; on screen a 400 error, "not supported when using Codex with a ChatGPT account" |
| T10 | the snapshot holds workspaces, tabs, panes, agents, version | it also holds `protocol`, `layouts` and focus fields; agents carry `agent_session` [own run 2026-10-02] | PASS: plus `focused_workspace_id`, `focused_tab_id`, `focused_pane_id`; `agent_session` on 17 of 25 agents |
| T11 | a pane that `cd`s into a worktree joins it | only the pane's `cwd` changes [added during the run] | PASS: `cwd` and `foreground_cwd` moved; `workspace_id` and the workspace's `checkout_path` stayed |
| T12 | `agent start` returning `idle` means ready | none: seen while setting up T4 | SEEN: `idle` and `interactive_ready: true` in 5.1 s with the trust dialog up; the next `agent get` read `blocked` (`trust_directory`, priority 950, top 20 non-empty lines); no `completion_seq` before the first turn |
| T13 | a wait on a `blocked` agent *(untested in v4.7)* | at codex's trust dialog a default `agent wait` and `--until blocked --timeout 0` return `blocked` at once, `--until idle --timeout 4000` exits 1, and `agent prompt --wait` exits 1 `agent_blocked` and types nothing [T2 rule, help] | PASS: `start` replied `idle` and `interactive_ready`, the next `get` `blocked`; default wait exit 0 in 1.03 s, `--until blocked --timeout 0` exit 0, `--until idle` exit 1 after 5.1 s; prompt exit 1 `agent_blocked` in 0.82 s, the screen byte-identical |
| T14 | read formats *(help only in v4.7)* | `pane read --format ansi` keeps the shell's `ESC[31m`, `--ansi` gives the same bytes, `--format text` has no ESC; `pane wait-output --raw` matches an ESC pattern a plain wait misses [help] | PARTIAL: `--format ansi`, `--ansi` and `--raw` byte-identical, but Herdr re-renders colours (`ESC[31m` became `ESC[0m` then `ESC[38;5;1m`) and ends lines with CRLF; `agent read --format ansi` pads rows to the pane width. MISS: `pane wait-output --raw` matched no ESC pattern, on monster or on this Mac; plain `RED48` matched with and without it |
| T15 | agy's trust dialog has no rule (herdr feedback) | `start` exit 0 `idle`; `get` stays `idle`; `agent explain` names no trust rule; `--until blocked` times out; a default wait returns at once [feedback list, SKILL] | PASS: no rule matched (`default_known_agent_idle_fallback`; monster's local `agy.toml` 2026.09.28.1 shadows the remote rules, and neither has one); `--until blocked` exit 1 after 5.8 s; default wait exit 0 in 0.97 s. T15b: a prompt into the dialog exited 1 `agent_prompt_stalled` after 12.7 s, answered the dialog and lost its text; T15c: the same prompt then exit 0 in 4.98 s |
| T16 | explain flags *(help only)* | `--format json` equals `--json`; `--verbose` says more; `--file <saved text> --agent codex` classifies a saved screen offline: `blocked`, `trust_directory` [help] | PASS: same keys; plain 5 lines, `--verbose` 37; `--file` on this Mac in 0.08 s gave `blocked`, `trust_directory`; over `--machine` it exits 2, "not an API-backed machine command" |
| T17 | split flags *(help only)* | `pane split --ratio 0.3 --right-click pane` exits 0 and the snapshot's `layouts` holds 0.3 or 0.7 [help] | PASS: the original pane kept 0.3 (12 of 40 rows), the new one the rest; the ratio shows only in `layouts` (`splits`), not in the reply; `--right-click` changed nothing visible |
| T18 | read-only flags *(help only)* | `integration status --outdated-only` exits 0 and lists nothing [help] | PASS, but over `--machine` it exits 2; over ssh on monster exit 0, nothing outdated (claude v10, codex v8, droid v3, kimi v7, cursor v1, antigravity-cli v3, grok v2); `plugin list --json` is forwarded (4 plugins, keyed `plugin_id`) |
| T19 | claude's grilling asks through question dialogs *(untested under Herdr)* | `start` stops at the trust dialog with `agent_not_ready`; then "grill me on this before you plan: …" loads `grilling`, whose questions come as dialogs, `blocked` [harnesses.md] | MISS: the trust part held (`agent_not_ready` in 5.0 s, rule `live_blocked_form` from monster's local rules, `down enter` passed it); `grilling` loaded by itself, then asked six questions in prose and settled `done` after 20 s. Also seen: monster's claude settings set `"tui": "fullscreen"` (no scrollback: `recent` gave the 20 visible rows, the turn was in the transcript jsonl) and bypass mode |
| T20 | agy's `/teamwork-preview` forms a team with a check pass *(user report)* | a team and a check pass on screen; `working`, then `done`; the file exists [harnesses.md] | PASS as worded, not as meant: first `blocked` at "Question 1/1" after 27.6 s (`enter` took the small team); then an implementer, three reviewers and a victory auditor, about 22 min for a 7-byte file. Meanwhile a default wait settled `idle` (seq 332, no `completion_seq`) and `--until done --until blocked` settled `done` three times (`completion_seq` 338, 342, 344), each gone a moment later; it ended `idle` (356) with no `completion_seq` |
| T21 | `done` stays until seen (v4.7: reading, explaining and waiting leave it) | a `done` survives `agent get`, 15 s, `agent read` (`visible`, `recent`, `recent-unwrapped`), `pane read` and `pane get` [SKILL] | PASS: `done` 331 through all seven. Both claude `done`s later read `idle`, keeping `completion_seq`: 325 two seconds after a client focused the workspace (server log), 331 with nothing logged; agy's `done`s in that focused workspace stayed until the next wait |

## Trace

Where each finding is stated. `lint.py` fails when a case has no line here, or
when a phrase is no longer in the skill file it names; rewording a finding
means updating its line in the same change.

| case | file | phrase |
| --- | --- | --- |
| T1 | SKILL.md | a bare `status` is refused |
| T1 | references/cli.md | a bare `status` is refused |
| T2 | SKILL.md | only when the current state matches its `--until` set |
| T2 | SKILL.md | A wait matches a state, the current one included |
| T2 | SYSTEM_PROMPT.md | current state matches its `--until` set |
| T2 | references/cli.md | only when the current state matches |
| T3 | SKILL.md | the prompt may or may not have been delivered |
| T3 | SKILL.md | `--timeout 0` checks once |
| T3 | SYSTEM_PROMPT.md | leaves open whether the text arrived |
| T3 | references/cli.md | with `--timeout 0` was never typed |
| T4 | SKILL.md | `agent read <target> --source detection` |
| T4 | references/cli.md | Its `--source` has no `detection` |
| T5 | SKILL.md | `agent rename <target> --clear` |
| T5 | references/cli.md | `--clear` drops the name |
| T6 | SKILL.md | with a nonce new for each run |
| T6 | references/cli.md | a reused marker matches the previous run's line at once |
| T7 | references/orchestration.md | with `already_open: true` |
| T7 | references/cli.md | adds `already_open: true` |
| T8 | references/orchestration.md | `--workspace` and `--cwd` exclude each other |
| T8 | references/cli.md | `worktree list` given both `--workspace` and `--cwd` |
| T9 | SKILL.md | printed a 400 error and settled `done`, exit 0 |
| T9 | references/harnesses.md | the turn settled `done` with exit 0 |
| T10 | SKILL.md | where the user's view is (`focused_workspace_id`) |
| T10 | references/cli.md | `focused_workspace_id`, `focused_tab_id`, `focused_pane_id` |
| T11 | references/orchestration.md | A shell's `cd` does not move a pane |
| T11 | references/cli.md | changed both cwds and not `workspace_id` |
| T12 | SKILL.md | so the reply came before the dialog was classified |
| T12 | references/harnesses.md | just not before `start` returns |
| T12 | references/cli.md | the next `agent get` read `blocked` |
| T13 | SKILL.md | returns that `blocked` at once |
| T13 | references/cli.md | got `agent_blocked` in 0.8 s |
| T14 | references/cli.md | gave byte-identical output |
| T14 | references/cli.md | `pane wait-output --raw` changed nothing seen |
| T15 | SKILL.md | agy's trust dialog has no rule at all and reads `idle` |
| T15 | SKILL.md | `local_override_shadowing_remote: true` |
| T15 | references/harnesses.md | Herdr has no rule for that dialog |
| T15 | references/cli.md | dialog stayed `idle` for good |
| T16 | references/cli.md | classifies offline with this Mac's rules |
| T17 | references/cli.md | the ratio shows in the snapshot's `layouts` |
| T18 | references/cli.md | `--outdated-only` printed nothing |
| T19 | SKILL.md | unless its TUI is fullscreen |
| T19 | SYSTEM_PROMPT.md | Grilling asks in prose and ends its turn |
| T19 | references/harnesses.md | asked six questions in prose |
| T19 | references/harnesses.md | rule `live_blocked_form` |
| T20 | SKILL.md | A settle can be a single frame |
| T20 | SYSTEM_PROMPT.md | says Herdr saw a turn end meanwhile |
| T20 | references/harnesses.md | no `● Agent(` row is left on screen |
| T20 | references/cli.md | An `idle` reached straight from `working` had none |
| T21 | SKILL.md | Reading, explaining and waiting leave it in place |
| T21 | references/cli.md | A `done` that turned `idle` kept it |

## Runbook (layer L)

`m` is the machine label, `D` an absolute scratch path there
(`/tmp/herdr-raycast-<chat id>-tests`), `<target>` the ssh target from
`herdr machine list --json`. Prefix everything you create (`hr47`, then `hr48` here) so it
is plainly yours. Write the predictions into the ledger first, with the time.
Then one herdr command per bash call, the bash timeout 30000 above herdr's
`--timeout`, `rc=$?` taken right after the command, and each reply recorded
in the ledger before the next.

Setup:

    ssh <target> 'git init -q D/repo && git -C D/repo -c user.name=t -c user.email=t@t commit -q --allow-empty -m init'
    ssh <target> 'cp ~/.codex/config.toml D/codex-config.bak'
    herdr --machine m api snapshot                                                    # note focused_workspace_id
    herdr --machine m workspace create --cwd D/repo --label hr47-tests --no-focus     # W, shell pane p0
    herdr --machine m pane split p0 --direction right --cwd D/repo --no-focus          # p1

T1 and T10:

    herdr --machine m status server --json
    herdr --machine m status
    herdr --machine m api snapshot

T6, in the shell pane p0:

    herdr --machine m pane run p0 'true; echo MARK_$?'
    herdr --machine m pane wait-output p0 --regex 'MARK_[0-9]+' --timeout 10000
    herdr --machine m pane run p0 'sleep 12; false; echo MARK_$?'
    herdr --machine m pane wait-output p0 --regex 'MARK_[0-9]+' --timeout 20000
    herdr --machine m pane wait-output p0 --regex '^MARK_1$' --timeout 20000
    herdr --machine m pane run p0 'sleep 12; false; echo MARK_q7x_$?'
    herdr --machine m pane wait-output p0 --regex 'MARK_q7x_[0-9]+' --timeout 20000
    herdr --machine m pane run p0 'sleep 12; echo LIT_q8y'
    herdr --machine m pane wait-output p0 --match LIT_q8y --timeout 20000

T12, T4, T2, T5 and T3, on a codex in p1:

    herdr --machine m agent start hr47c --kind codex --pane p1 --timeout 30000
    herdr --machine m agent get hr47c                                                  # T12: blocked yet?
    herdr --machine m agent read hr47c --source visible --lines 40
    herdr --machine m agent read hr47c --source detection                              # compare with the read above
    herdr --machine m agent explain hr47c --json
    herdr --machine m agent send-keys hr47c enter                                      # the key the dialog names
    herdr --machine m agent prompt hr47c "Reply with exactly the word PONG47" --wait --timeout 120000
    herdr --machine m agent read hr47c --source detection
    herdr --machine m agent read hr47c --source visible
    herdr --machine m pane read p0 --source detection
    herdr --machine m agent wait hr47c --timeout 5000
    herdr --machine m agent wait hr47c --until blocked --timeout 5000
    herdr --machine m agent wait hr47c --until idle --timeout 5000
    herdr --machine m agent wait hr47c --until done --until blocked --timeout 5000
    herdr --machine m agent rename hr47c --clear
    herdr --machine m agent get p1
    herdr --machine m agent get hr47c
    herdr --machine m agent rename p1 hr47c
    herdr --machine m agent wait hr47c --timeout 0
    herdr --machine m agent wait hr47c --until blocked --timeout 0
    herdr --machine m agent prompt hr47c "Reply with exactly the word ZERO47" --wait --timeout 0
    herdr --machine m agent get hr47c
    herdr --machine m agent read hr47c --source visible --lines 30
    herdr --machine m agent prompt hr47c "Reply with exactly the word ONE47" --wait --timeout 1000
    herdr --machine m agent get hr47c                                                  # completion_seq above the last?
    herdr --machine m agent read hr47c --source visible --lines 30

T9, a second codex in a new split (the folder is trusted by now):

    herdr --machine m pane split p1 --direction down --cwd D/repo --no-focus           # p2
    herdr --machine m agent start hr47e --kind codex --pane p2 --timeout 30000 -- -m hr47-no-such-model
    herdr --machine m agent prompt hr47e "Reply with exactly the word ERR47" --wait --timeout 120000
    herdr --machine m agent read hr47e --source visible --lines 30

T7, T8 and T11:

    herdr --machine m worktree create --workspace W --branch hr47-a --path D/wt-a --label hr47-wt --no-focus   # V
    herdr --machine m worktree open --workspace W --branch hr47-a --label hr47-relabel --no-focus
    herdr --machine m workspace get V
    herdr --machine m worktree list --workspace W --cwd D/repo
    herdr --machine m workspace get W
    herdr --machine m pane run p0 'cd D/wt-a'
    herdr --machine m pane get p0
    herdr --machine m workspace get W

Cleanup, in this order (a linked workspace blocks closing W):

    herdr --machine m worktree remove --workspace V
    herdr --machine m workspace close W
    herdr --machine m api snapshot                                                     # focus as noted; nothing hr47 left

Last, on the target: answering codex's trust dialog added a
`[projects."D/repo"]` table to `~/.codex/config.toml`. Remove that table and
nothing else, confirm with `diff D/codex-config.bak ~/.codex/config.toml` (no
output), then `rm -rf D`.

T13–T21 (v4.8) ran in a fresh W. On the target first `git init -q D/agy`,
`mkdir D/claude` and the codex backup as above; then, one call each:

    herdr --machine m pane split p0 --direction right --cwd D/repo --no-focus                                  # p1, codex
    herdr --machine m pane split p1 --direction down --ratio 0.3 --right-click pane --cwd D/agy --no-focus     # p2, agy; T17
    herdr --machine m pane split p0 --direction down --cwd D/claude --no-focus                                 # p3, claude
    herdr --machine m agent start hr48c --kind codex --pane p1 --timeout 30000         # T13; leave its trust dialog up
    herdr --machine m agent get hr48c                                                   # blocked
    herdr --machine m agent wait hr48c --timeout 5000
    herdr --machine m agent wait hr48c --until blocked --timeout 0
    herdr --machine m agent wait hr48c --until idle --timeout 4000
    herdr --machine m agent prompt hr48c "Reply with exactly the word BLK48" --wait --timeout 10000
    herdr --machine m agent read hr48c --source detection                               # T16; save the reply as S here
    herdr --machine m agent explain hr48c --json
    herdr --machine m agent explain hr48c --format json
    herdr --machine m agent explain hr48c --verbose
    herdr agent explain --file S --agent codex                                          # on this Mac; exit 2 over --machine
    herdr --machine m pane run p0 'printf "\033[31mRED%s\033[0m\n" 48'                  # T14; the typed line never holds RED48
    herdr --machine m pane read p0 --source visible --lines 12 --format ansi
    herdr --machine m pane read p0 --source visible --lines 12 --ansi
    herdr --machine m pane read p0 --source visible --lines 12 --raw
    herdr --machine m pane wait-output p0 --regex '\x1b\[[0-9;]*mRED48' --raw --timeout 3000
    herdr --machine m pane wait-output p0 --regex RED48 --raw --timeout 3000
    herdr --machine m api snapshot                                                      # T17: layouts, splits
    ssh <target> 'herdr integration status --outdated-only'                             # T18; exit 2 over --machine
    herdr --machine m plugin list --json
    herdr --machine m agent start hr48a --kind agy --pane p2 --timeout 30000            # T15; read again ~3 s later
    herdr --machine m agent explain hr48a --json
    herdr --machine m agent wait hr48a --until blocked --timeout 5000
    herdr --machine m agent prompt hr48a "Reply with exactly AGY48" --wait --timeout 20000     # T15b, into the dialog
    herdr --machine m agent prompt hr48a "Reply with exactly AGY48" --wait --timeout 120000    # T15c, the control
    herdr --machine m agent start hr48p --kind claude --pane p3 --timeout 30000 -- --model opusplan --effort high   # T19
    herdr --machine m agent send-keys hr48p down enter
    herdr --machine m agent prompt hr48p "grill me on this before you plan: add a tiny greeting script to this repo" --wait --timeout 240000
    herdr --machine m agent prompt hr48p "Reply with exactly the word DONE48 and nothing else" --wait --timeout 120000   # T21; agent get after each read
    herdr --machine m agent prompt hr48a "/teamwork-preview create a file named team48.txt in this folder containing exactly the line TEAM48, then stop" --wait --timeout 540000   # T20
    herdr --machine m agent send-keys hr48a enter                                       # "Question 1/1": the recommended team
    herdr --machine m agent wait hr48a --until blocked --timeout 240000                 # then read; again until no ● Agent( row is left

Cleanup: close W (`herdr --machine m workspace close W`), check on the target
that `diff D/codex-config.bak ~/.codex/config.toml` prints nothing (codex's
dialog was never answered), remove agy's one `trustedWorkspaces` entry for
D/agy from `~/.gemini/antigravity-cli/settings.json`, then `rm -rf D`. Leave
claude's entry in `~/.claude.json` and record it.

## When something new is learned

1. **Write it down as seen**: command, reply, exit code, time, server, herdr
   and harness versions, into the ledger. A claim from elsewhere (a dossier,
   another chat, this skill) is a prediction, not a result.
2. **Reproduce the smallest variant** in a workspace you created. A CLI
   contract (exit code, field, flag) needs one run; a state, timing or focus
   effect needs a second run, or the opposite condition beside it. T3 shows
   why: `--timeout 0` and `--timeout 1000` gave opposite answers to one
   question. Predict what you will read, not only the state: T20's
   "`working`, then `done`" held while the team still worked. A flag that
   misbehaves over `--machine` runs once more on this Mac before it is blamed
   (T14), and a cause read from one run gets a control run (T21 found a
   `done` turn `idle` with no focus logged).
3. **Classify it.** It changes a CLI fact (add or fix an H check), a behaviour
   (add or update a case here) or contradicts the skill (add a regression rule
   that fails on the old wording, and see it fail before the fix).
4. **Find every restatement** before editing: the case's Trace lines, then a
   grep of its key terms across SKILL.md, references/ and SYSTEM_PROMPT.md.
   Fix all of them in one change; a fact fixed in one file and left in
   another is the contradiction these tests exist to catch.
5. **Re-run**: lint to 0 FAIL, then the L cases whose Trace lines changed.
6. **Record**: the case row (result, date, versions), its Trace lines, a commit
   that names the cases. When a new result contradicts a recorded one, run the
   old case again before overwriting it; if both hold, the difference is a
   condition (version, harness, focus, machine) and the row names it.

## Raycast rewrites SKILL.md

Seen eight times on 2026-10-03 with Raycast 2.6.2.0, at 01:49:40, 02:00:55,
02:10:39, 03:00:03, 03:35:09, 03:44:48, 03:54:31 and 04:04:07, each the
second a projection folder was made. For a Claude process that loads this
skill, Raycast links it into
`$TMPDIR/raycast-local-subscription-skills/<id>/skills/herdr-raycast-<hash>`
(a symlink to this folder) and writes SKILL.md through the link: `name` gets
the hash (quoted), `compatibility` is dropped, and the body is a cached copy,
v4.6 (9152a7c) each time it was compared, although the folder held a newer
version at the last seven. The writer was another Raycast AI session: its
processes carried
`Skill(raycast:herdr-raycast-0c36108d)` and `--effort xhigh` in `ps` (the
03:35:09 and 03:54:31 ones with `--plugin-dir-no-mcp` set to that folder),
while this chat's (`--effort max`) carried none. At 02:00:55 it replaced v4.7, already
committed as faab301, and the 20 SKILL.md edits made before 01:49 were most
likely lost the same way. TRACE failed on 11 phrases, FRONT on `name` and
`compatibility`. An earlier draft of this section blamed this chat's own
approved edits; `ps` disproved it.

- Any session that has the skill loaded can undo an edit at any moment. Keep
  the edited SKILL.md outside this folder, then copy it in, lint and commit
  in one bash call.
- Before a commit, and after another session used the skill, run
  `git -C ~/.agents status -- skills/herdr-raycast`. A modified SKILL.md
  that fails FRONT is a session's copy: restore it with
  `git -C ~/.agents checkout -- skills/herdr-raycast/SKILL.md` and never
  commit it.
- It does not put the file back: after the third rewrite no process carried
  the skill, and SKILL.md stayed as written. Its 03:35:09 process was gone by
  03:46:48 and a new one had started at 03:44:48, rewriting SKILL.md right
  after a lint had passed on it: a new process, and a rewrite, likely comes
  with each of its turns *(inferred)*.
- Its copy is the version that was current when Raycast was launched:
  Raycast has run since 01:31:11, and the newest commit of SKILL.md then was
  v4.6 (23:33:27 the night before; v4.7 came at 01:59:27). So the copy is
  most likely read at launch and never refreshed *(inferred)*; a Raycast
  restart would test that *(untested)*. Git history is not touched: every
  commit of SKILL.md, v1 to v4.8, has `name: herdr-raycast` and a growing
  line count, so only uncommitted SKILL.md edits can be lost.
- It is not this skill's quirk. `ego-browser` (untracked in git) was
  rewritten the same way at 03:06:47, the second its projection was made:
  `name: "ego-browser-5a9f8b60"`. A process that reused that projection at
  03:54:36 left the file alone, while herdr-raycast, restored at 03:49,
  got a new projection at 03:54:31 and was rewritten. The processes run
  with `--no-session-persistence`, and no other SKILL.md with this skill's
  text exists under `~/.config`, `~/.claude`, `~/.codex` or Raycast's
  Application Support, so the cached copy is held inside Raycast
  *(inferred)*. Raycast skips a skill whose `name` is not its folder's
  (Raycast Manual, Skills), so a rewritten skill likely stops loading in
  other chats until restored *(untested)*.

## Retest triggers

| change | how it shows | run again |
| --- | --- | --- |
| herdr client, server or protocol | `herdr --version`; `herdr --machine m status server --json` | lint, every case |
| Herdr's detection rules | `agent explain <target> --json` → `manifest_version`, `manifest_source` (codex 2026.10.01.1 on monster; monster also keeps local rules in `~/.config/herdr/agent-detection/` for agy 2026.09.28.1, claude 2026.10.01.1 and kimi, dated 2026-10-01, which shadow the remote ones) | T2, T4, T9, T12, T13, T15, T19, T20 and the harness tables; the rules carry their own version and `remote_update_status`, so states may change while `herdr --version` does not *(inferred)* |
| a harness version | `<harness> --version` on the machine; the header of [harnesses](../references/harnesses.md) | T2–T5, T9, T12, the harness tables |
| the agy wrapper (`~/.local/bin/agy`, a bash script on both machines) | its size and sha256: monster 2725 B, `39cf7634ad5866cc…`; this Mac 3117 B, `69096ab4853d8f28…` (2026-10-03) | agy start and dialog behaviour; T15, T20 |
| monster's claude settings (`~/.claude/settings.json`: `tui`, `permissions.defaultMode`) | the file | T19, R8 and claude's rows in [harnesses](../references/harnesses.md) |
| Herdr's harness integrations | `herdr integration status` over ssh on each machine (exit 2 over `--machine`) | T15, T20 and the harness tables |
| server restart or reconnect | snapshot IDs differ from the ledger | re-resolve targets; T10 |
| a new machine | `herdr machine list --json` | T1, T6 and one agent start there |
| an edit to the skill | `git diff` | lint; the cases whose Trace lines it touched |
| another Raycast session loads this skill or any other (2.6.2.0 here; ego-browser too) | `Skill(raycast:herdr-raycast-…)` in `ps`; SKILL.md modified in `git status`; lint FRONT | restore it from git (section above), then lint |

## History

| date | skill | lint | live |
| --- | --- | --- | --- |
| 2026-10-03 | v4.6 | 13 FAIL, 9 WARN; 28 FAIL once Trace, SPAN and R6 were added | T1–T10 as predicted; T11 and T12 added |
| 2026-10-03 | v4.7 | 0 FAIL, 0 WARN; twice 20 or more FAIL when another session's Raycast copy overwrote SKILL.md (TRACE, then FRONT too), cleared by restoring it from git | no new run: the fixes restate T1–T12 and are traced |
| 2026-10-03 | v4.8 | R7–R9 added and seen failing on the v4.7 wording (6 FAIL), then 0 FAIL, 0 WARN; Raycast rewrote SKILL.md four times more (03:35:09; 03:44:48 right after a passing lint; 03:54:31 and 04:04:07 after the commit), each undone (edited copy, then `git checkout`), and ego-browser's SKILL.md once (03:06:47) | T13–T21: T13, T15–T18 and T21 as predicted; T14 missed on `wait-output --raw`, T19 on grilling's dialogs; T20 held as worded while its `done`s were false; a second `done` → `idle` with no logged cause |
