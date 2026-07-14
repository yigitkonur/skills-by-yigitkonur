# run-agent-browser

An agent skill for reliable `agent-browser` automation with fresh `@ref` snapshots, deterministic verification, trust-boundary handling, and Yigit's multi-agent headed-Chrome CDP pool.

The official upstream skill is dynamic: the installed CLI supplies version-matched guidance through `agent-browser skills get core [--full]`. This skill layers local runtime policy and multi-agent ownership on top instead of freezing an upstream command catalog.

Last reconciled against `agent-browser 0.31.1` and upstream commit [`afae698`](https://github.com/vercel-labs/agent-browser/commit/afae698a51242166170b6fe4809dd57fe9f75798). Always refresh from the [official discovery skill](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) and installed core skill when the CLI changes.

## What it adds

- headed persistent Chrome lanes (`general`, `profound`, `peec`);
- automatic per-agent leasing and per-lane serialization;
- task-owned tab tracking and exact lease cleanup;
- recovery without deleting Chrome locks or daemon files;
- explicit routing for public `read`, unmanaged launch flags, providers, Electron, and remote CDP;
- prompt-injection, secret, artifact, and outward-action policy;
- current references, pool-aware templates, and smoke helpers.

## Install

As a Codex/Claude plugin:

```text
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-agent-browser@yigitkonur
```

With the Skills CLI:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-browser
```

## First check

```bash
bash scripts/check-agent-browser-version.sh
agent-browser pool status
agent-browser skills get core
```

Read `SKILL.md` first. The six files under `references/` are routed detail, not optional duplicated documentation.
