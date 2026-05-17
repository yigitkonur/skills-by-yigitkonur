# issue-tree-status.sh

Purpose: read a GitHub Issue tree and report the operational execution state.

Mutates: no.

Arguments:

```bash
bash issue-tree-status.sh OWNER/REPO ROOT_ISSUE
bash issue-tree-status.sh --repo OWNER/REPO --root ROOT_ISSUE
```

Reports:

- root issue
- dynamically discovered `wave:*` labels
- current wave
- per-wave totals for closed, open, ready, blocked, in-progress, failed, and needs-review
- ready leaf issues
- parent issues ready for closure verification
- blocked issues with blockers
- failed issues awaiting recovery
- stale status-label warnings

Examples:

```bash
bash "$SKILL_DIR/scripts/issue-tree-status.sh" yigitkonur/example 42
```

Failure modes:

- Missing `gh` or `jq`.
- Any issue, sub-issue list, or parent lookup cannot be fetched.
- GitHub auth, permission, or rate-limit errors.
