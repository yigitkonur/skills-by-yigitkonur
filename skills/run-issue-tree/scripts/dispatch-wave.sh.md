# dispatch-wave.sh

Purpose: prepare ready leaf issues for runtime-native subagent dispatch.

Mutates: no by default. With `--mark-in-progress`, selected issues are relabeled `status:in-progress` and `status:ready` is removed.

Arguments:

```bash
bash dispatch-wave.sh OWNER/REPO ROOT_ISSUE [--limit N] [--output-dir DIR] [--mark-in-progress]
bash dispatch-wave.sh --repo OWNER/REPO --root ROOT_ISSUE [--concurrency N]
```

Outputs:

- `status.md` from `issue-tree-status.sh`
- `manifest.json` with one entry per selected ready issue
- `prompts/issue-N.md` prompt files generated from issue bodies

Manifest fields:

- `issue_number`
- `title`
- `wave`
- `labels`
- `prompt_file`
- `blockers`
- `parent`
- `expected_completion_report_fields`

Examples:

```bash
bash "$SKILL_DIR/scripts/dispatch-wave.sh" yigitkonur/example 42 --limit 3
bash "$SKILL_DIR/scripts/dispatch-wave.sh" yigitkonur/example 42 --concurrency 2 --mark-in-progress
```

Failure modes:

- Missing `gh` or `jq`.
- No readable issue tree.
- Invalid concurrency cap.
- GitHub label mutation failure when `--mark-in-progress` is used.

This script does not call any subagent API. Use the current runtime's native task/subagent tool with the emitted prompt files.
