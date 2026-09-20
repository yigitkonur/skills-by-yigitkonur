# Standalone Mission Briefs

Read this before delegating work to an agent in an isolated Herdr pane. The mission brief must carry sufficient context for the worker to decide what to do, what not to modify, what proves completion, and how to report back to the orchestrator.

---

## 1. Scope & Isolation First

1. **One Agent, One Worktree**: Never delegate implementation without a dedicated checkout (`git worktree add -b feature/<name> .worktrees/<name> origin/main`).
2. **Single-Model Fleet**: Ensure the worker agent executes on the exact same model as the orchestrator (`herdr agent start worker-<name> --kind <kind> --pane <id> -- --model <model>`).
3. **Independent Outcome**: Assign an independently verifiable task. Split research from implementation when an architectural seam is unresolved.
4. **Contract Seams**: If a worker needs changes to a shared composition root (`AppDelegate`, global routes, database schemas), the worker must mock the dependency locally and request contract integration rather than editing the root directly.

---

## 2. Standard Mission Brief Template

Every mission brief submitted via `herdr agent prompt` should follow this structured markdown schema:

```markdown
# Mission Brief: <Task Title>

## 1. Context & Objective
- **Problem**: Why this work is necessary.
- **Accepted Outcome**: The exact user-visible or behavioral change required.
- **Relevant Files**: Starting paths and documentation pointers.
- **Exclusions**: Files, APIs, or architectural patterns strictly out of scope.

## 2. Implementation & Quality Mindset
- **TDD Requirement**: Write a focused, failing test first (Red). Implement the minimal production code to pass the test (Green). Refactor while preserving green checks.
- **No Headless Hacks**: Stay interactive and visible in your terminal pane.

## 3. Delivery & PR Protocol
- **Branch**: feature/<task-name>
- **Worktree**: .worktrees/<task-name>
- When your tests pass:
  1. Commit your changes with a conventional commit message.
  2. Push your branch: `git push origin feature/<task-name>`
  3. Open a **Draft Pull Request**:
     `gh pr create --draft --title "feat: <task-name>" --body "$(cat .agent-runs/report.md)"`
  4. Save your structured report to `.agent-runs/report.md`.

## 4. MANDATORY COMPLETION & CALLBACK MANDATE
- Orchestrator Pane: <CALLER_PANE_ID>
- Orchestrator Tab: <CALLER_TAB_ID>
- Your Pane: <WORKER_PANE_ID>

When your task is complete (or if blocked by an unresolvable issue):
1. NOTIFY THE ORCHESTRATOR IMMEDIATELY by executing:
   herdr agent prompt "<CALLER_PANE_ID>" "I'm the herdr agent in pane <WORKER_PANE_ID> (tab <WORKER_TAB_ID>). I've finished my work on feature/<task-name>. PR: #$(gh pr view --json number -q .number) (Draft). Tests are passing. You can read my full report with: herdr agent read <WORKER_PANE_ID> --source recent-unwrapped --lines 100"
2. Show desktop alert:
   herdr notification show "Task Complete: <task-name>" --body "Worker in pane <WORKER_PANE_ID> opened Draft PR" --sound done
```

---

## 3. Making the Finish Line Honest

- **Implementation**: An open Draft PR is an intermediate milestone. It signals that code is synthesized and ready for an independent, clean-context review.
- **Research**: A research brief completes with bounded evidence, confidence scores, and open questions; it does not close an implementation issue.
- **Review**: A review brief points to an existing Draft PR diff (`gh pr diff <PR_NUMBER>`). The reviewer leaves review comments and reports sign-off back to the orchestrator pane.

---

## 4. Safe Submission Pattern

Always submit briefs from a static file using quoted parameter expansion to prevent shell syntax interpolation or log leakage:

```bash
herdr agent prompt "$WORKER_PANE_ID" "$(cat /tmp/mission-brief-$TASK_NAME.txt)"
```
