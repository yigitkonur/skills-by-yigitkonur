# run-codex-review

Run parallel per-branch `/codex:review` fix-rereview loops with `/do-review` evaluators, then open PRs via `/ask-review`, fire codex rescue, and run adaptive multi-bot review evaluation before merging foundation→leaf on the private fork only.

**Category:** orchestration

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-review
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
