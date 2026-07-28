# ci-cd-optimize

Diagnose or optimize slow CI/CD pipelines by measured bottleneck, not folklore — GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepos, Docker builds, runner queues, deployment paths, and Swift/Xcode CI — while preserving required checks, cache correctness, exact-artifact verification, and the agent feedback loop that consumes the result.

Includes a provider-neutral CI watcher (`scripts/ci-watch.py`) plus deep references for caching, checkout/artifacts, measurement, runner contention, deployment verification, and non-blocking CI feedback loops.

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