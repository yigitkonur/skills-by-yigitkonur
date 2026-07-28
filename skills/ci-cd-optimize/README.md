# ci-cd-optimize

Diagnose and optimize slow CI/CD pipelines by **measured bottleneck, not folklore** — GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepos, Docker builds, runner queues, deployment paths, Swift/Xcode CI, and the adjacent problem of **waiting on CI without stalling the session**.

The skill is workflow-first:

1. read prior runs and separate queue / setup / execution / transfer,
2. find the true critical path,
3. choose the smallest reversible experiment,
4. preserve required checks and trust boundaries,
5. close the feedback loop with a bounded, SHA-pinned watcher when CI is the only verification surface.

It ships a provider-neutral watcher contract plus a stdlib-only `ci-watch.py`, and routes to detailed references for capacity/contention, change-based CI, caching, testing/flakiness, runners, deployment, containers, monorepos, and vendor-specific behavior.

**Category:** ops

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install ci-cd-optimize@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/ci-cd-optimize
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
