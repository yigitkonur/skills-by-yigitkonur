# validate-issue-body.sh

Purpose: validate a GitHub Issue body before creation or dispatch.

Mutates: no.

Arguments:

```bash
bash validate-issue-body.sh BODY_FILE [--repo OWNER/REPO]
```

Checks:

- body is at or below 60,000 characters
- required sections exist
- required ownership and completion protocol lines exist exactly
- vague Definition of Done patterns are absent
- tool-specific command patterns are absent
- referenced issue numbers exist when `--repo` is provided

Examples:

```bash
bash "$SKILL_DIR/scripts/validate-issue-body.sh" /tmp/issue-body.md
bash "$SKILL_DIR/scripts/validate-issue-body.sh" /tmp/issue-body.md --repo yigitkonur/example
```

Failure modes:

- Missing body file.
- Missing `gh` when `--repo` is used.
- Any validation error listed above.
- GitHub auth, permission, or rate-limit errors during reference checks.
