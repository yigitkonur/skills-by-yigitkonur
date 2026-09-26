# Review-and-Fix Contract & Quality Gates

This reference codifies review mechanics, exact-SHA binding, failure budget rules, and GitHub PR interactions across all Herdr operating modes.

---

## 1. Exact-SHA Review Invariant

1. **Strict 40-Character Commit SHA Binding**:
   Technical review and verification bind strictly to an exact, full 40-character commit SHA:
   ```bash
   CANDIDATE_SHA="$(git rev-parse HEAD)"
   ```
   Inspectors must verify that the SHA exists in the repository object database and that `git status --porcelain` is clean before auditing.
2. **Automatic Invalidation on Commit Advance**:
   Any subsequent commit, fix, rebase, or format edit pushes the branch HEAD to a new commit SHA ($SHA_2 \neq SHA_1$). This **automatically invalidates** any prior review or approval.
3. **Delta Decisions for New HEADs**:
   When an author pushes a correction commit producing a new SHA, the same independent reviewer may evaluate the new HEAD via a focused delta and impact check on the newly changed diff, issuing an explicit decision for the new SHA without requiring a full reset to an unfamiliar reviewer.

---

## 2. Reviewer Role & Read-Only Hardening Partner

1. **Read-Only Verification**:
   - The reviewer acts as an adversarial hardening partner. The reviewer audits specification conformance, code standards, edge cases, regression risk, and test suite execution at the exact candidate SHA in clean context.
   - Reviewers do NOT self-approve their own work. If a reviewer authors production fixes directly, it transfers to the author role, requiring a different independent reviewer to perform the final approval.
2. **Direct Verification Commands**:
   Run linters, type checks, and automated tests directly:
   ```bash
   npm run typecheck --if-present
   npm test --if-present
   ```
3. **GitHub PR Review Mechanics**:
   - If independent GitHub accounts are available:
     ```bash
     gh pr review "$PR_URL" --approve -b "LGTM: verified candidate commit $(git rev-parse HEAD). All checks pass."
     ```
   - **Self-Authored PRs**: If the reviewer runs under the same GitHub token or account as the PR author, `gh pr review --approve` returns `Can not approve your own pull request`. In that case, submit a structured review comment:
     ```bash
     gh pr review "$PR_URL" --comment -b "LGTM: verified candidate commit $(git rev-parse HEAD). All automated tests pass."
     ```
   - **Branch Protection Notice**: A same-account review comment is operational evidence for the supervisor, but does NOT bypass branch-protection approval requirements.

---

## 3. Finite Review Bounds & Failure Budgets

To prevent endless automated review-and-fix ping-pong:

1. **Two-Round Failure Budget**:
   - If two consecutive correction rounds fail to achieve candidate approval or resolve check failures, **stop automated retries immediately**.
   - Escalate the concrete technical blocker, conflicting requirements, and trade-offs to the supervisor or user.
2. **No Artificial Budget Resets**:
   - Running read-only inspection tools, changing error IDs, rephrasing prompts, or switching model tiers do NOT reset the failure budget.
3. **No Material Waivers**:
   - A material defect (e.g. failing integration test, unhandled promise rejection, security vulnerability) cannot be reclassified as "advisory" or waived merely to reach an approval.
4. **Cosmetic Invariant**:
   - Purely stylistic or non-functional nitpicks must not block candidate approval once functional criteria and test gates pass.
