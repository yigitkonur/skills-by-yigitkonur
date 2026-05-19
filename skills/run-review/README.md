# run-review

Single entry point for every code-review intent. The skill routes the request to one of four modes:

- **A — Do a review.** Review a PR, branch diff, or working tree for merge readiness.
- **B — Ask for review.** Clean up the user's branch, draft a self-review body, open the PR.
- **C — Evaluate received feedback.** Triage human / bot / markdown review feedback into accept / pushback / clarify / defer / dismiss.
- **D — Delegate to codex.** Run `codex review` (or `codex exec review`) and surface the findings.

Replaces the old `review-pr`, `review-self`, and `review-feedback` skills, plus folds in the `codex review` CLI as a first-class delegation target. The mode is always either inferred from the user's literal phrasing or asked outright — never silently picked.

**Category:** productivity

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-review
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
