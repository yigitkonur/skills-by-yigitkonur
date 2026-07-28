# ci-cd-optimize

Diagnose or optimize slow CI/CD pipelines by measured bottleneck, not folklore — GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepos, Docker builds, runner queues, deployment paths, and Swift/Xcode CI — while preserving required checks, cache correctness, and exact-artifact verification.

It also covers **waiting on a pipeline without stalling the session**: a SHA-pinned watcher contract that emits one line per state change and always terminates with an explicit verdict, so an agent never blocks on a hung or never-registered run. See `references/ci-watching.md`.

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