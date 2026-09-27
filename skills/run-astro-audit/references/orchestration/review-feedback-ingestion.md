# Code-Review Feedback Ingestion & Follow-Up Remediation

This guide establishes the protocol for harvesting code-review comments (from automated bots such as Codex, GitHub Actions, or human maintainers) on open audit PRs, triaging findings, and dispatching follow-up remediation rounds.

---

## 1. Review Feedback Harvesting

### 1.1 Querying Pull Request Comments via GitHub CLI

```bash
# View general issue/PR conversation comments
gh pr view <PR_NUMBER> --comments

# View inline diff review comments
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments \
  --jq '.[] | {id: .id, path: .path, line: .line, body: .body, user: .user.login}'
```

---

## 2. Review Comment Triage Taxonomy

Every harvested comment must be classified into one of 3 categories before touching code:

| Category                              | Definition                                                                                                                         | Action Required                                                                          |
| :------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------- |
| **P1: Blocking Defect**               | Logic bug, broken type contract, missed edge case, regression in existing tests, or security loophole.                             | **Mandatory Fix**: Dispatch follow-up subagent round immediately.                        |
| **P2: Stylistic / Nit**               | Variable naming suggestion, minor comment clarification, or optional code formatting.                                              | **Surgical Polish**: Apply if clean and zero-risk; otherwise note in PR response.        |
| **P3: False Positive / Out-of-Scope** | Review bot hallucinated non-existent API, failed to understand Astro compilation, or requested changes outside the audit boundary. | **Defend & Dismiss**: Reply with technical evidence and link to architectural invariant. |

---

## 3. Dispatching Follow-Up Remediation Rounds

When P1 or P2 feedback requires code modifications:

1. **Re-activate the Assigned Worktree**:
   ```bash
   cd .worktrees/wt-<ID>
   git status
   ```
2. **Formulate the Surgical Follow-Up Brief**:
   - Provide the reviewer's exact feedback, target file, and line number.
   - Specify the exact invariant to preserve.
   - Command the subagent to fix the issue, re-run scoped Vitest tests, commit, and push.
3. **Commit & Push Update**:
   ```bash
   git add <modified-files>
   git commit -m "fix(review): address review feedback on <subsystem> (#<PARENT_ID>)"
   git push origin fix/audit-<ID>
   ```
4. **Close the Loop**:
   - Post a comment on the PR detailing the fix and test evidence:
     ```bash
     gh pr comment <PR_NUMBER> --body "✅ Addressed reviewer feedback in commit \`$(git rev-parse --short HEAD)\`. All scoped integration tests pass."
     ```
