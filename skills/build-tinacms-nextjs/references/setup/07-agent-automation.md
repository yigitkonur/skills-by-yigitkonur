# Agent Automation Guardrails

Optional agent-runtime guardrails for teams that repeatedly work on TinaCMS projects. This is not part of the main setup path. Use it only when the project already supports local agent settings, hooks, command allowlists, or MCP-style tool servers.

## What to automate

| Guardrail | Why |
|---|---|
| Block manual edits under `tina/__generated__/` and `.tina/__generated__/` | Generated clients and types must come from `tinacms build` |
| Warn before manual edits to `tina/tina-lock.json` | The lockfile is committed but generated from schema compilation |
| Prefer `tinacms build` after schema edits | Keeps generated client/types current |
| Prefer `tinacms audit` after content migration | Catches path, field-name, and `_template` drift |
| Allow read-only project check scripts | Fast lane detection without mutating a project |
| Keep formatting hooks scoped to edited source files | Avoid slow whole-repo formatting churn |

## Read-only command allowlist

If your agent runtime supports command allowlists, these are usually safe to pre-approve:

```text
pnpm tinacms build
pnpm tinacms audit
pnpm tinacms dev
pnpm dlx @tinacms/cli@latest audit
npm view tinacms version
npm view @tinacms/cli version
npm view next version
npm view react version
bash scripts/check-tina-versions.sh
bash scripts/check-tina-env.sh
```

Adjust command prefixes for npm, yarn, or bun projects. Do not allow broad destructive shell patterns just to make TinaCMS work.

## Generated-file protection

Configure your agent runtime to reject edits when the target path matches:

```text
tina/__generated__/**
.tina/__generated__/**
```

For `tina/tina-lock.json`, prefer a warning instead of a hard block. The file is generated, but schema changes legitimately update it and the updated lockfile should be committed.

## Documentation/tool access

For current docs, prefer official TinaCMS, Next.js, React, and npm registry sources. If your runtime supports doc-fetching or browser MCP servers, route them to official docs first:

- TinaCMS setup, CLI, TinaCloud, and self-hosting docs
- Next.js App Router, Draft Mode, Proxy, caching, and metadata docs
- npm registry metadata for patch-level package versions

Use browser-driven testing for visual editing only when a local or deployed site is available. Otherwise report that visual editing was not observed at runtime.

## Project-level helper prompts

If the project supports local reusable prompts or project skills, keep them project-specific:

| Prompt | Job |
|---|---|
| `new-block` | Add one TinaCMS block template, component, and renderer mapping |
| `new-collection` | Add one content collection with schema, sample content, and route |
| `tina-audit` | Run audit/build and inspect generated client plus common visual-editing markers |
| `tina-deploy-check` | Verify env vars, build order, lane decision, cache/revalidation, and runtime |

Do not publish project-specific prompts as global skills unless they generalize across projects.

## When to skip this

Skip automation setup for one-off TinaCMS work, small projects, or repos without an agent-runtime convention. Manual checks plus the scripts in this skill are enough.

## Verification

```bash
# Generated clients should not be tracked.
git ls-files tina/__generated__ .tina/__generated__

# Tina lockfile should be tracked when present.
git ls-files tina/tina-lock.json

# Read-only check scripts should run without mutating files.
git status --short
bash scripts/check-tina-versions.sh .
bash scripts/check-tina-env.sh .
git status --short
```
