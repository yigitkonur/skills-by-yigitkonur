# Recipe — Git and PR Loop

The full start → code → PR → done cycle for an agent picking up a Linear issue. Covers Git, Jujutsu, draft PRs, branch naming, and stopping work without assuming a transactional rollback.

## The five-line happy path

```bash
linear-cli i start LIN-123 --checkout       # 1. assign me + In Progress + create + checkout branch
# ... edit code, run tests ...
git add . && git commit -m "fix: handle null session in /login"
linear-cli g pr LIN-123 --draft             # 2. open a draft PR; auto-fills title + body
linear-cli done                             # 3. read current branch, mark issue Done
```

## What `i start --checkout` does

Sequentially (the Linear mutation happens before the Git operation):

1. Assigns the issue to you (`me`).
2. Sets state to the team's first started-type workflow state.
3. Uses Linear's `branchName`, or a generated identifier/title branch name.
4. Checks it out.

If checkout fails, the issue may already be assigned and started; inspect both systems before retrying. If the branch already exists, `i start --checkout` re-uses it. To override the branch name:

```bash
linear-cli g checkout LIN-123 -b custom-branch-name
```

To create the branch without checking out:

```bash
linear-cli g create LIN-123
```

To just print the canonical branch name:

```bash
linear-cli g branch LIN-123
```

## Reverse direction: branch → issue

```bash
linear-cli context                          # human-readable
linear-cli context --output json            # parse with jq
```

`context` reads the current branch, extracts the Linear identifier (e.g. `feat/SCW-123-foo` → `SCW-123`), and fetches the issue. See `json-shapes.md` for the payload.

Gate any branch-driven workflow on `context`:

```bash
ISSUE=$(linear-cli context --output json | jq -r '.issue_id // empty')
[ -n "$ISSUE" ] || { echo "no Linear issue on this branch"; exit 1; }
```

## Creating the PR

```bash
linear-cli g pr LIN-123                     # PR with auto-filled title/body from issue
linear-cli g pr LIN-123 --draft             # draft PR
linear-cli g pr LIN-123 --base main         # specify base
linear-cli g pr LIN-123 --web               # pass through gh's browser-based creation flow
```

Requires the GitHub `gh` CLI authenticated to the same repo. In 0.3.28 the title is `[IDENTIFIER] Issue title`; the body is only `Linear: ISSUE_URL`, not the issue description. Review and expand the PR body before publication when more context is needed.

## Closing the loop

```bash
linear-cli done                             # marks current branch's issue as Done
linear-cli done --status "In Review"        # set a different state
linear-cli done -s "In Progress"            # short flag
```

`done` reads the current branch, extracts the issue identifier, and updates state. Equivalent to:

```bash
ISSUE=$(linear-cli context --output json | jq -r .issue_id)
linear-cli i update "$ISSUE" -s Done
```

## Leaving a finding in passing

When you discover something during the work, comment on the issue without leaving the branch:

```bash
linear-cli cm create "$(linear-cli context --output json | jq -r .issue_id)" \
  -b "Root cause: missing null check in handler.go:412 — fix in commit abc123."
```

Useful for handoff notes, partial fixes, or "I split this off into LIN-201".

## Splitting work mid-flow

If the issue grows new scope, split it:

```bash
PARENT=$(linear-cli context --output json | jq -r .issue_id)
CHILD=$(linear-cli i create "Follow-up: extract retry helper" -t ENG --id-only --quiet)
linear-cli rel parent "$CHILD" "$PARENT"
linear-cli cm create "$PARENT" -b "Split out retry-helper extraction → $CHILD."
```

## Abort and revert

If you start work but realize it's the wrong issue or the work isn't viable:

```bash
linear-cli i stop LIN-123 --unassign                # backlog/unstarted + unassign
git checkout "$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
git branch -d "$BRANCH_NAME"                        # delete only after checking the branch and preserving work
```

`i stop` chooses a backlog-type state, falling back to unstarted; it does not restore the issue's previous state. Unassignment requires `--unassign`. Verify the previous state/assignee before any manual restoration. Use `git symbolic-ref` to detect the workspace's default branch.

## Jujutsu (jj) support

For jj users, use the existing `git` commands and force `--vcs jj` when auto-detection is not enough:

```bash
linear-cli g checkout LIN-123 --vcs jj       # bookmark + check out
linear-cli g branch LIN-123 --vcs jj         # show bookmark name
linear-cli g create LIN-123 --vcs jj         # bookmark without check out
linear-cli g pr LIN-123                      # PR via GitHub CLI
linear-cli g commits --vcs jj                # show commits with Linear trailers
```

## Draft → ready

When a draft PR is ready for review, mark it with `gh` (no Linear-specific command needed) and add a comment to the issue:

```bash
gh pr ready                                                    # convert draft → ready
linear-cli cm create "$(linear-cli context --output json | jq -r .issue_id)" \
  -b "PR is ready for review."
linear-cli i update "$(linear-cli context --output json | jq -r .issue_id)" -s "In Review"
```
