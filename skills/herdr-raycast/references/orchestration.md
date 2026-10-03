# Orchestration

How the conductor's stance in [SKILL.md](../SKILL.md) turns into practice. Parts
marked *(untested)* come from CLI usage or the user's guidance and have not yet
been run by this skill.

## The ledger

`/tmp/herdr-raycast-<chat id>/ledger.md` on this Mac. The chat id comes from
`chat__get-current-chat`; it survives compaction, so the folder is both
collision-safe and findable again. `/tmp` is cleared on reboot; move anything
that must last into the chat folder's instructions or a note.

Keep it short and current, for example:

    # Goal: fix the login timeout in app (monster)
    ## Targets
    monster w6A:p3  name api-fix  codex  /srv/app  branch fix/login
    ## Steps
    - [x] plan -> /srv/app/PLAN-login.md (read; 6 steps)
    - [ ] step 1 sent, marker LGN1
    ## Waiters (server, name, pane, task, marker, last completion_seq)
    monster api-fix p3 shell-... LGN1 seq 4
    ## Decided without asking
    - vitest over jest: already in the repo
    ## Waiting on the user
    - codex asks to run migrations (blocked; options y / n)

Write the intent before a command and the observed state after it. At the start
of a turn read the ledger before `api snapshot`: the ledger says what you
expect, the snapshot what is there, and a difference is news.

## Briefs

A brief carries everything the agent may not assume:

- the goal and where to work (absolute path, branch);
- limits: what not to touch, no merge, no deploy, no secrets, no new
  dependencies without asking;
- how to finish: what to deliver, then a last line with a marker word you chose
  (codex prints answers as `• text`, so the line reads `• MARKER`);
- for an answer longer than one screen (codex keeps only one, 45 lines on
  monster): a file on that machine to write, and a reply that is only its
  path. Shorter answers are read from the screen, by their marker.

Before large work, the first brief asks for nothing but a plan in a file (see
the next section). Read it, correct it, then send the steps one at a time:
prompt → wait → read → check → ledger.

Step by step is only as good as its reading. In one early run the guesses crept
in there, where a reply was predicted instead of read. So run one command per
call, branch on what it returned, and let the next step wait for that reply.

## From goal to steps *(user's practice; untested here)*

1. **Plan.** Brief Claude Opus (high or above; [harnesses](harnesses.md)) for a
   plan only, written to a file (in the repo when it should travel with the
   PR, else under `/tmp` on that machine). Give it a generous ceiling, "at most
   2500 lines": a smaller model will execute it, and the detail is what lets
   you cut it into steps that each fit one turn, each with its own check. When
   the goal is still fuzzy, open the brief with "grill me on this before you
   plan" ([harnesses](harnesses.md)); answer its questions from the ledger.
2. **Waves.** In the same Claude session, after the plan exists: "If you
   orchestrated this plan with as many sub-agents as you like, in at most five
   waves (fewer, even one, if that is better; your call), how would you split
   it?" The answer is the wave plan; copy it into the ledger.
3. **Steps.** Hand each wave's steps to executors (agy), one step per brief,
   parallel steps in separate worktrees. The ledger holds the whole; no agent
   ever does.

## Parallel work in worktrees (run on monster, 2026-10-02)

Usage printed by `herdr worktree` (0.9.3):

    worktree list   [--workspace ID | --cwd PATH] [--trust-repository]
    worktree create [--workspace ID | --cwd PATH] [--branch NAME] [--base REF] [--path PATH]
                    [--label TEXT] [--focus|--no-focus] [--trust-repository]
    worktree open   [--workspace ID | --cwd PATH] (--path PATH | --branch NAME) [--label TEXT]
                    [--focus|--no-focus] [--trust-repository]
    worktree remove --workspace ID [--force] [--trust-repository]

`--workspace` and `--cwd` exclude each other: given both, `worktree list`
exited 2 with that usage as plain text, not JSON (2026-10-03).

A worktree is a workspace. `create` checks the branch out under
`~/.herdr/worktrees/<repo>/<branch>` (not beside the repo) and returns
`type: worktree_created` with `.result.workspace.workspace_id`,
`.result.root_pane.pane_id` (already in the checkout) and `.result.worktree.path`.
Given `--cwd` instead of `--workspace`, `create` and `open` also open a workspace
for the repo's main checkout, labelled with the repo name; it is yours to close.
A repo you created needed no `--trust-repository`; the harness started inside
still asked its own trust question (codex said it trusts the repo root).

Lifetimes, as run:

- `worktree remove --workspace <ws>` (`worktree_removed`) closed the workspace,
  ended the agent working in it without asking, deleted the checkout and kept
  the branch. Run it only after the PR is confirmed.
- Untracked or modified files refuse it: `dirty_worktree_requires_force`,
  exit 1. That refusal is the safety; `--force` is the user's.
- Closing the main workspace while worktree workspaces exist returns
  `workspace_group_close_required`. `--group` (accepted, though `--help` omits
  it) closed them all and their agents, but left the checkouts on disk.
  Remove worktrees first; close the main workspace last.
- An orphaned checkout comes back with
  `worktree open --cwd <repo> --branch <branch>` (`worktree_opened`) and can
  then be removed properly. On a checkout that is already open, `open` returned
  that same workspace, pane and terminal with `already_open: true`, and its
  `--label` renamed the workspace (2026-10-03).
- A shell's `cd` does not move a pane: after `cd` into a linked checkout, a
  pane of the main workspace kept its `workspace_id`, and that workspace still
  named the main checkout; only the pane's `cwd` changed (2026-10-03). Start a
  worktree's agent in that worktree's own root pane.
- `worktree list` (`worktree_list`) shows the main checkout and each linked one
  with its `open_workspace_id`.

Before briefing a PR, check that the machine can push (`gh auth status` there).
Two traps on monster: an invalid `GH_TOKEN` in the environment shadowed a valid
`gh` login (use `env -u GH_TOKEN`), and a global
`credential.https://github.com.username` naming another account broke
`git push` even with a valid login; a repo-local
`git config credential.https://github.com.username <login>` fixed it.

Per parallel task: create the worktree on its own branch with `--no-focus` →
start the agent in its root pane, read the screen, answer the trust question →
brief that ends "commit, push the branch, open a PR, reply with the PR URL and
the marker" → a background wait per agent → confirm on the machine (`gh pr list`,
no dirty files, nothing unpushed) → `worktree remove`. Run this way, agy and
codex each delivered a PR in parallel from two worktrees of one repo.

## Review by a second agent *(untested)*

The author's report is a claim. Review is a separate brief to another agent,
another harness where possible, in a tab or split of the same workspace:
"review <branch or PR> against <plan or acceptance criteria>; run <tests>;
reply PASS or FAIL with reasons, then the marker". You run only the cheap,
decisive checks: exit codes, `git status` and `git log` on the machine, the PR's
existence.

## Being told when work ends

A background `agent wait` per agent costs nothing until it returns, so it is the
default; the automation fallback for a chat no one returns to is in
[raycast.md](raycast.md).
