# scenario-detect.sh

Read-only heuristic signal collector for `init-makefiles` scenario classification.

## Use

Run from the downstream project root, or pass the root explicitly:

```bash
bash scripts/scenario-detect.sh
bash scripts/scenario-detect.sh /path/to/project
```

The script prints:

- observed on-disk signals
- candidate scenario labels with rough confidence
- a reminder to produce the final `Classification result` block manually

It does not choose the final scenario. The agent still applies the seven-scenario decision rules in `references/scenario-detection.md`.

## Read-only contract

The script never writes, stages, commits, deletes, chmods, moves, or edits files. It only runs filesystem reads, optional `jq`, `grep`, and `find`.

## Heuristic limits

- It cannot know provider intent from dashboard state.
- It cannot prove whether a custom backend deploys to Railway unless repo files show that.
- It treats a Mac app without `Host macbook` as a medium-confidence Scenario G candidate that still needs a remote target decision.
- It treats frontend + Supabase + custom backend as the supported C+D combined shape, but the final classification must confirm whether the backend deploys separately.

Use this script before asking an ambiguity question so the question is grounded in observed signals.
