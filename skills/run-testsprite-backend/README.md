# run-testsprite-backend

Create, debug, and release-gate TestSprite backend API tests against real deployed services.

This skill treats TestSprite as an independent HTTP client and evidence collector. It helps an agent turn repository contracts into executable Python, use managed credentials, inspect immutable run artifacts, separate product defects from test/deployment/provider failures, and loop through a fresh deployed-revision check.

It does **not** make a stale deployment current, provision missing accounts or proxies, solve CAPTCHA/human gates, or make an LLM diagnosis authoritative. Those conditions remain explicit release or operations gates instead of being weakened into passing assertions.

High-value uses include semantic response checks, real source URL validation, streaming order, routing metadata, typed errors, dependency chains, cleanup, and external-provider behavior. For local unit tests, load/fuzz testing, frontend browser journeys, or an API with no public target, use the repository's native or specialist workflow instead.

**Category:** testing

The entrypoint is [`SKILL.md`](SKILL.md). Detailed phase references live under [`references/`](references/); the bundled auditor statically rejects common vacuous, secret-bearing, private-target, and unbounded backend scripts before upload.

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-testsprite-backend@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-testsprite-backend
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
