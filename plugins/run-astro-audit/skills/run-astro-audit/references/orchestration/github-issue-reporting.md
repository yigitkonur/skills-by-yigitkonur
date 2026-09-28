# GitHub Issue Reporting & Ledger Synchronization

This reference specifies how repository audit findings are published to GitHub Issues, mapped into structured tracking artifacts, and recorded in the repository remediation ledger.

---

## 1. Issue Architecture: Parent & Child Hierarchy

Audit topics follow a two-tier hierarchy to keep discussions focused and avoid monolithic 2,000-line issue threads:

```
  Parent Issue: [Audit - <Workload Title>]: Full-Repo Astro 7 Audit (#1252)
      │
      ├── Sub-Issue: [Sub-Issue #1252] 61-NEXTJS-GHOST-IMPORTS-001 (#1253)
      ├── Sub-Issue: [Sub-Issue #1252] 61-NEXTJS-GHOST-IMPORTS-002 (#1254)
      └── Sub-Issue: [Sub-Issue #1252] 61-NEXTJS-GHOST-IMPORTS-003 (#1255)
```

---

## 2. GitHub CLI Publishing Recipes

### 2.1 Publishing the Parent Audit Issue

```bash
gh issue create \
  --title "[Audit - $WORKLOAD_TITLE]: Full-Repo Astro 7 Audit" \
  --body-file "docs/audits/results/$CATEGORY/$WORKLOAD_SLUG/issue-body.md" \
  --label "audit,astro-7,needs-remediation"
```

### 2.2 Publishing Child Sub-Issues

```bash
gh issue create \
  --title "[Sub-Issue #$PARENT_ID] $DEFECT_ID: $DEFECT_SUMMARY" \
  --body "### Defect Details
- **Parent**: #$PARENT_ID
- **Severity**: $SEVERITY
- **Target File**: \`$FILE_PATH:$LINE\`
- **Root Cause**: $ROOT_CAUSE
- **Remediation**: $REMEDIATION_PLAN" \
  --label "sub-issue,audit"
```

---

## 3. Structured Artifact Schemas

### `findings.json` Schema

Every audited topic maintains a machine-readable `findings.json`:

```json
{
  "workloadId": "64",
  "slug": "64-zod-date-coercion-frontmatter-schema",
  "category": "07-migration-and-core-contracts",
  "parentIssue": 1291,
  "findings": [
    {
      "id": "64-ZOD-DATE-COERCION-FRONTMATTER-SCHEMA-001",
      "subIssue": 1292,
      "severity": "Critical",
      "targetFile": "src/features/events/data/event-partition.ts",
      "targetLine": 146,
      "title": "Strict calendar date regex causes 100% of event entries to be dropped",
      "rootCause": "YAML unquoted dates coerce to full ISO timestamps; regex matches only YYYY-MM-DD",
      "invariant": "All 1,524 authored event records must be preserved and partitioned",
      "status": "Resolved"
    }
  ]
}
```

---

## 4. Live Remediation Ledger Synchronization

All active and completed workloads are recorded in `docs/audits/remediation-ledger.md`.

### Ledger Table Schema

```markdown
| ID  | Topic & Workload                          | Parent Issue |    Sub-Issues     |   Status    | Branch & Worktree                   |    PR URL    | Disposition & Findings |
| --- | ----------------------------------------- | :----------: | :---------------: | :---------: | ----------------------------------- | :----------: | ---------------------- |
| 64  | `64-zod-date-coercion-frontmatter-schema` | [#1291](...) | 3 subs (#1292...) | **PR OPEN** | `fix/audit-64` (`.worktrees/wt-64`) | [#1356](...) | 6/6 findings resolved  |
```

### Ledger Update Procedure

1. Upon PR creation, append or update the row with the PR URL, branch name, and resolved sub-issue count.
2. Update the document header with the current completion tally (e.g. `(70/70 — 100% Remediated via Open PRs)`).
3. Validate formatting:
   ```bash
   pnpm check:doc-integrity
   pnpm diff:check
   pnpm premerge:runner:prepush
   ```
4. Commit and push directly to `origin/main`.
