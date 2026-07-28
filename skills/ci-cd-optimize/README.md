# ci-cd-optimize

Diagnose or optimize slow CI/CD pipelines by measured bottleneck, not folklore — GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepos, Docker builds, runner queues, deployment paths, and Swift/Xcode CI — while preserving required checks, cache correctness, and exact-artifact verification.

**Category:** ops

Includes `scripts/ci-watch.sh` — a non-blocking GitHub Actions watcher for agents that must
wait on a pipeline (commit-pinned, diff-gated, always terminates with a verdict). See
`references/agent-feedback-loop.md`.

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