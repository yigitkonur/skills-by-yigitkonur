# Review-and-Fix Contract & Quality Gates

This reference codifies review mechanics, exact commit object ID binding, failure budget rules, evidence quality standards, and GitHub PR interactions across all Herdr operating modes.

---

## 1. Full Verified Commit Object ID Invariant

1. **Commit Object ID & Clean Tree Binding**:
   Technical review and verification bind strictly to a full verified Git commit object ID (supporting both SHA-1 40-character and SHA-256 64-character repositories) AND a clean working tree:
   ```bash
   CANDIDATE_SHA="$(git rev-parse HEAD)"
   git cat-file -e "${CANDIDATE_SHA}^{commit}"
   test -z "$(git status --porcelain)"
   ```
   **Exact SHA alone cannot certify a dirty shared tree**: An uncommitted file or staged mutation in the checkout invalidates the candidate claim. The working tree must be proven clean.
2. **Review Environment Isolation**:
   - If review occurs in a shared checkout with the author, the author session must be **frozen** during review.
   - If review checks or test suites mutate files, or if the author must continue working, allocate an isolated native checkout (Git worktree) for the review.
3. **Automatic Invalidation on Commit Advance**:
   Any subsequent commit, fix, rebase, or format edit pushes the branch HEAD to a new commit object ID ($SHA_2 \neq SHA_1$). This **automatically invalidates** any prior review or approval.
4. **Delta Decisions for New HEADs**:
   When an author pushes a correction commit producing a new SHA, the same independent reviewer evaluates the new HEAD via a focused delta and impact check on the newly changed diff, issuing an explicit decision for the new candidate without requiring a full reset to an unfamiliar reviewer.

---

## 2. Reviewer Role & Read-Only Hardening Partner

1. **Read-Only Verification**:
   - The reviewer acts as an adversarial hardening partner. The reviewer audits specification conformance, code standards, edge cases, regression risk, and test suite execution at the exact candidate SHA in clean context.
   - Reviewers do NOT self-approve their own work. If a reviewer authors production fixes directly, it transfers to the author role, requiring a different independent reviewer to perform the final approval.
2. **Evidence Quality Standards**:
   - Do NOT certify visual or interactive UI behavior from code formatters, linters, or unit tests alone. Visual or browser behavior requires actual rendering evidence or browser test verification.
   - Report requested runtime/model separately from observed runtime/model. Process tree or `argv` inspection proves launch intent or binary defaults, but does NOT prove runtime-selected model or effort; true model verification requires inspecting native TUI headers, status bars, menus, or native session queries. If native verification is unavailable, explicitly state that the observed model is unverified.
3. **Direct Verification Commands**:
   Execute repository-authorized syntax, typecheck, and test commands (e.g. `npm test`, `pytest`, `cargo test`, `make test`, `python3 scripts/validate-skills.py`):
   ```bash
   # Run repository-authorized check commands
   <AUTHORIZED_REPO_CHECK_COMMAND>
   ```
4. **GitHub PR Review Mechanics**:
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
