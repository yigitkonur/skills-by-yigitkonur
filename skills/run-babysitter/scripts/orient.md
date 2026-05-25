# orient.sh

Read-only world snapshot for phase ① ORIENT. Gathers, in one markdown block, the
facts the babysitter needs to start a cycle.

## Usage

```bash
bash {baseDir}/scripts/orient.sh [last_seen_sha]
```

- `last_seen_sha` (optional) — the `Last-seen commit` from `.agent-docs/memory/STATE.md`.
  If given and valid, the script lists commits in `last_seen..HEAD`. If omitted or
  not found, it shows recent history instead.

## Output

A markdown block with: git HEAD/branch/dirty count; commits since the last cycle;
and a GitHub section (repo, whether issues are enabled, open-issue count,
babysitter-authored open issues, recent CI runs).

## Degradation (by design — the skill's own graceful-failure scope)

- No `gh` installed, or not authenticated → prints a "degrade to draft-only" note.
- Issues disabled on the repo → prints a "DISABLED → draft-only" note.
- No GitHub Actions → the CI line is simply omitted.

The script never exits non-zero except when not run inside a git repo. It never
writes to the repository.
