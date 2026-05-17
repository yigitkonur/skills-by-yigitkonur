# Body Size Validation

Pre-creation validation rules for issue bodies. Run before every `gh issue create` call and before dispatching any issue body as a worker prompt.

## Canonical Validator

Use the bundled script instead of recreating shell snippets:

```bash
bash "$SKILL_DIR/scripts/validate-issue-body.sh" /path/to/issue-body.md --repo "$REPO"
```

Read `scripts/validate-issue-body.sh.md` for arguments, examples, and failure modes.

The script checks:

- body is at or below 60,000 characters
- required sections exist
- exact ownership and completion protocol lines exist
- vague DoD patterns are absent
- tool-specific command patterns are absent
- referenced issue numbers exist when `--repo` is provided

## Split Decision Tree

```
Body > 60,000 chars?
├── YES -> Split into parent-stub + child-detail
│         Split at semantic boundaries
│         Parent stub: under 2,000 chars
│         Children: standard issue-body template with parent reference
│
└── NO -> Proceed with creation
         Body > 40,000 chars? -> consider splitting for readability
         Body < minimum by type? -> add execution context
```

## Split Protocol

When a body exceeds 60,000 characters:

1. Keep the parent stub under 2,000 characters with scope summary, parent-level DoD, wave/dependency fields, and placeholder child references.
2. Split child issues at semantic boundaries such as vertical slices, modules, user-story groups, or migration phases.
3. Move detailed file paths, edge cases, and verification criteria into child issues. Each child still uses the full issue body template.
4. Create child issues first, capture real issue numbers, then edit the parent stub to replace placeholders with child links.
5. Preserve wave, priority, and dependency semantics across the split. Move detail downward; do not change execution order just to satisfy the size limit.

## Minimum Body Size

Issue bodies that are too short usually lack enough context for autonomous execution.

| Type | Min chars | Signal if below |
|---|---:|---|
| `type:epic` | 500 | May need more child context |
| `type:feature` | 1,000 | Missing context or DoD |
| `type:task` | 1,500 | Worker will likely lack context |
| `type:subtask` | 800 | May be fine if parent provides context |

## Batch Validation

Validate all bodies before creating any issue in a batch:

```bash
for body_file in issue-bodies/*.md; do
  bash "$SKILL_DIR/scripts/validate-issue-body.sh" "$body_file" --repo "$REPO"
done
```

If any body fails, fix or split the batch before creating issues. Do not partially create an issue set when the remaining bodies are known-invalid.
