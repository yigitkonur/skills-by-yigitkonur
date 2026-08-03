# run-testsprite-frontend

Creating, running, debugging, or release-gating TestSprite frontend browser tests, including public-target CLI or localhost MCP routing; not backend, load, security, or local-unit testing.

**Category:** testing

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-testsprite-frontend@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-testsprite-frontend
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Plan auditor

Resolve the installed/loaded skill directory to an absolute path; never pass `{baseDir}` literally. Use `--json` for machine-readable errors and warnings:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json "<PLAN_FILE>"
```

`--authorized-outward-step INDEX` is repeatable and zero-based. It changes only that detected step from an error to a warning; it does not grant authorization. `--self-test` is for maintainers/CI only and does not validate a plan.
