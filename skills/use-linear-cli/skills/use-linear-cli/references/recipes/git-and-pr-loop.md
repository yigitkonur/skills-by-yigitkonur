# Recipe — Git and PR Loop

The full start → code → PR → done cycle for an agent picking up a Linear issue. Covers Git, Jujutsu, draft PRs, branch naming, and the auto-revert path when work is abandoned mid-flow.

## The five-line happy path

```bash
linear-cli i start LIN-123 --checkout       # 1. assign me + In Progress + create + checkout branch
# ... edit code, run tests ...
git add . && git commit -m "fix: handle null session in /login"
linear-cli g pr LIN-123 --draft             # 2. open a draft PR; auto-fills title + body
linear-cli done                             # 3. read current branch, mark issue Done
```

## What `i start --checkout` does

Atomically:

1. Assigns the issue to you (`me`).
2. Sets state to the team's "In Progress" workflow state.
3. Creates the branch `<user>/lin-123-<title-slug>` (or matches the team's branch convention).
4. Checks it out.

If the branch already exists, `i start --checkout` re-uses it. To override the branch name:

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
linear-cli g pr LIN-123 --web               # open in browser after creation
```

Requires the GitHub `gh` CLI authenticated to the same repo. The PR title and body are auto-generated from the Linear issue (title, description, identifier in the body).

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
linear-cli i stop LIN-123              # unassign + reset to previous state
git checkout main                      # leave the branch
git branch -D <user>/lin-123-...       # optional cleanup
```

`i stop` is the inverse of `i start` (without the `--checkout`).

## Jujutsu (jj) support

For jj users, every Git command has a parallel:

```bash
linear-cli j checkout LIN-123          # bookmark + check out
linear-cli j bookmark LIN-123          # show bookmark name
linear-cli j create LIN-123            # bookmark without check out
linear-cli j pr LIN-123                # PR via jj git push
linear-cli g commits                   # show commits with Linear trailers
```

## Draft → ready

When a draft PR is ready for review, mark it with `gh` (no Linear-specific command needed) and add a comment to the issue:

```bash
gh pr ready                                                    # convert draft → ready
linear-cli cm create "$(linear-cli context --output json | jq -r .issue_id)" \
  -b "PR is ready for review."
linear-cli i update "$(linear-cli context --output json | jq -r .issue_id)" -s "In Review"
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `i start LIN-123 --checkout` | Atomic: assign + In Progress + branch + checkout. |
| `g checkout LIN-123` | Just the branch part. Doesn't change assignment or state. |
| `i update LIN-123 -s Done` | Generic. Safe for any issue. |
| `linear-cli done` | Convenience for "the branch I'm on right now". |
| `g pr LIN-123` | Creates a GitHub PR. Needs `gh` authenticated. |
| `g branch LIN-123` | Prints the branch name; does not create or check out. |

## See also

- `issues/lifecycle.md` for the full `i start`/`i stop`/`i update` flag matrix.
- `recipes/triage-and-comments.md` for handling inbound comments and screenshots.
- `recipes/creating-many-issues.md` for spawning sub-issues.
- `output-and-scripting.md` for the chaining patterns used above.
