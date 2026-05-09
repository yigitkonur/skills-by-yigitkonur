# cluster-files.sh

## Purpose

Read-only file classifier for `do-review`. It turns a changed-file list into a markdown cluster map grouped by data, security, API, core, frontend, infrastructure, configuration, documentation, tests, types, and mixed files.

## Inputs

Read newline-delimited paths from stdin:

```bash
git diff --name-only main...HEAD | scripts/cluster-files.sh
```

Or ask the script to read a local git diff:

```bash
scripts/cluster-files.sh --base main --head HEAD
```

## Outputs

Markdown on stdout:

- total file count
- comparison source
- files grouped by review concern
- test/type pairing rules

No files are written.

## Examples

```bash
printf '%s\n' src/api/users.ts tests/api/users.test.ts README.md | scripts/cluster-files.sh
```

```bash
scripts/cluster-files.sh --base origin/main --head feature-branch
```

## Read / Write Surface

- Stdin mode reads only the provided path list.
- `--base/--head` mode runs `git diff --name-only BASE...HEAD`.
- Does not stage files, checkout refs, edit files, call GitHub, or mutate the working tree.

## Failure Modes

- Unknown flag: exits 2.
- Only one of `--base` or `--head` supplied: exits 2.
- `git` missing in `--base/--head` mode: exits 127.
- Invalid refs: exits with the underlying `git diff` error.
- Ambiguous paths fall into `Other / Mixed`; use `references/analysis/file-clustering.md` for manual refinement.

## SKILL.md Routing

Phase 3 routes here for an initial cluster map before deep review. The output is a starting point; pair tests and type/schema files with the consuming source clusters during manual review.
