# Review-and-Fix Contract & Quality Gates

This reference codifies the review mechanics, exact-SHA binding, failure budget rules, and GitHub PR interactions for Herdr-Lite.

---

## 1. Exact-SHA Review Invariant

1. **Strict Commit SHA Binding**:
   Technical review and verification bind strictly to an exact commit SHA:
   ```bash
   CANDIDATE_SHA="$(git -C "$WORKTREE_PATH" rev-parse HEAD)"
   ```
2. **Automatic Invalidation on Commit Advance**:
   Any subsequent commit, fix, rebase, or format edit produces a new commit SHA ($SHA_2 \neq SHA_1$), which **automatically invalidates** prior reviews.
3. **Delta Decisions**:
   When an implementer or reviewer adds a commit, the reviewer performs a delta review evaluating only the newly changed diff and directly affected tests, issuing an explicit decision for the new HEAD SHA.

---

## 2. Review-and-Fix Protocol

Unlike passive code review where an auditor only comments and blocks, the Herdr-Lite Sibling Reviewer acts as a hardening partner:

1. **Verify Baseline & Diffs**:
   Inspect the full change against base:
   ```bash
   git -C "$WORKTREE_PATH" diff "origin/main...HEAD"
   ```
2. **Execute Validation Suites**:
   Run linters, type checks, and automated tests:
   ```bash
   npm run typecheck
   npm run test
   ```
3. **Direct Patching**:
   If edge cases, missing test assertions, or minor type errors are detected:
   - The reviewer writes the missing test cases or bug fixes directly in the shared worktree.
   - Stages and commits the patch:
     ```bash
     git add <patched_files>
     git commit -m "fix(review): harden edge case and add regression test"
     git push
     ```
4. **Formal GitHub PR Approval**:
   Once all automated checks pass on the final candidate SHA:
   ```bash
   gh pr review "$PR_URL" --approve -b "LGTM: verified candidate commit $(git -C "$WORKTREE_PATH" rev-parse HEAD). All test suites and edge cases pass."
   ```

   > [!NOTE]
   > **Self-Authored PRs**: If the reviewer runs under the same GitHub token or account as the author who created the PR, `gh pr review --approve` will return `Review Can not approve your own pull request`. In that case, submit a formal review comment instead:
   > ```bash
   > gh pr review "$PR_URL" --comment -b "LGTM: verified candidate commit $(git -C "$WORKTREE_PATH" rev-parse HEAD). All test suites and edge cases pass."
   > ```
   > The orchestrator recognizes this comment verification and proceeds with the serial merge.

---

## 3. Finite Review Bounds & Failure Budget

To prevent endless automated review-and-fix ping-pong:

- **Strict Two-Round Limit**: If two consecutive correction rounds fail to resolve a test failure or achieve candidate approval, **stop automated retries immediately**.
- **No Artificial Failure Budget Resets**: Switching model tiers, changing error IDs, rephrasing prompts, or running read-only inspection tools **do NOT reset** the failure budget.
- **Escalation Mandate**: Hitting the 2-round limit requires a concrete escalation report detailing the conflicting requirements, unresolvable test errors, and specific trade-offs for human decision.
- **No Material Waivers**: A material defect (e.g. failing integration test, unhandled promise rejection, security vulnerability) cannot be reclassified as "advisory" or waived merely to reach an approval.
- **Cosmetic Comments Non-Blocking**: Purely stylistic or non-functional nitpicks must not block PR approval or trigger another correction round once functional criteria pass.
