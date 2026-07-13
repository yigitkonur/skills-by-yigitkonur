---
name: run-railway
description: "Use if running railway CLI — deploys, logs, env vars, link, ssh, db shells, scaling."
---

# run-railway

Drive the installed `railway` CLI from evidence, not memory. This skill is the routing layer: it picks the right reference, the right command, and the right scope (local binary vs upstream docs) for every Railway question an agent runs into during ongoing platform operations.

## Use this skill when

- *the user types or pastes a literal `railway <subcommand>` and wants the right flags, aliases, or nested forms*
- *the job is choosing between near-twin commands — `up` vs `deploy`, `redeploy` vs `restart`, `delete` vs `unlink`, `connect` vs `ssh`, `run` vs `shell` vs `dev`*
- *the user is reading logs, checking deploy status, scaling a service, editing variables, attaching a domain, or opening a DB shell against a Railway service*
- *the user pastes a Railway dashboard URL or asks "which project/service/environment am I linked to?"*
- *the docs show a Railway command the local binary does not have, or the user says "latest", "current", "today" — version-drift reconciliation*
- *the question is about Railway functions, volumes, or shell completion output for the installed CLI*
- *the user wants first-party Railway database analysis (Postgres, MySQL, Redis, Mongo) rooted in CLI access*

## Do NOT use this skill when

- the job is **authoring a `make prod` / `make deploy` target or a Makefile control plane** that wraps Railway commands — use `init-makefiles` to generate the scenario-appropriate scaffold; this skill answers what the wrapped commands do, but does not write the Makefile
- the work is **purely Railway dashboard, GraphQL API, or REST API** with no CLI decision to make
- a generic shell, Git, or container-build skill answers the question with no Railway-specific context
- the task is **infrastructure architecture planning** with no installed `railway` binary in play

## Non-negotiable rules

1. **Local snapshot is truth** for the installed binary. The extracted help under `references/cli/` describes what is actually invokable on this machine.
2. **Upstream docs are context, not proof.** Newer Railway pages may show commands or families the installed CLI cannot run. Mark scope explicitly.
3. **Never guess flags, aliases, possible values, or nested subcommands** from memory. Route to `references/cli/railway-cli-command-reference.md`.
4. **Read-safe by default.** This skill is reference-first. Do not run mutating commands (`up`, `redeploy`, `restart`, `down`, `delete`, `unlink`, `variable set`, `domain add`, `scale`) unless the user explicitly asked for the operational action.
5. **Do not conflate near-twins.** `deploy` ≠ `up`, `redeploy` ≠ `restart`, `delete` ≠ `unlink`, `connect` ≠ `ssh`, `run` ≠ `shell` ≠ `dev`. Always disambiguate when the user's wording is ambiguous.
6. **Trust explicit identifiers over the linked directory.** A pasted dashboard URL or explicit `--project / --environment / --service` always wins over `cwd` link state.
7. **Version-drift gate.** If the user says "latest" / "current" / "today", or the question references a family the local snapshot doesn't have (e.g. `skills`, `agent`, `bucket`, `starship`), read `references/research/version-drift.md` first.

## Workflow

1. **Establish scope.** Local installed CLI, upstream Railway sources, or both? State it on the first line of every answer.
2. **Run `railway --version`** when version drift could plausibly matter and the user has a shell.
3. **Pick the smallest reference set** using the splits below. Avoid loading the full command reference unless flags or aliases are needed.
4. **Answer in the output contract** (scope → command → flags → near-neighbor distinction → version-drift note if material).

## Decision splits — load-bearing routing

| Need | Read |
|---|---|
| `up` vs `deploy`, `redeploy` vs `restart`, rollback, `down` | `references/cli/deployments-and-releases.md` |
| `link` vs `init`, `delete` vs `unlink`, `add`, `open`, auth/context, `docs`, `completion`, `upgrade` | `references/cli/context-projects-and-linking.md` |
| `run` vs `shell` vs `dev`, `dev configure`, `dev clean`, local var injection | `references/cli/local-development-and-shells.md` |
| `status`, `logs`, `connect` vs `ssh`, service-level routing | `references/cli/observability-and-access.md` |
| `environment`, `variable`, `domain`, `scale`, `service scale` | `references/cli/configuration-networking-and-scaling.md` |
| Functions or volumes (attach/detach/delete distinctions) | `references/cli/functions-and-volumes.md` |
| "What Railway command should I use for this job?" (intent-first) | `references/cli/common-workflows.md` |
| Audit: every local top-level command family is covered | `references/cli/command-family-coverage.md` |
| Exact flags, aliases, nested subcommands, possible values | `references/cli/railway-cli-command-reference.md` |
| Raw help wording, examples, or formatting proof | `references/cli/railway-cli-live-help-snapshot.md` |
| Dashboard URL parsing, resource model, safe preflight | `references/upstream/resource-model-and-preflight.md` |
| First-party setup runbook (workspace, project, service, template) | `references/upstream/operations/setup.md` |
| First-party deploy runbook (`up`, redeploy/restart, build config, Railpack, Dockerfile, monorepo) | `references/upstream/operations/deploy.md` |
| First-party configure runbook (env, variables, domains, networking, config patches) | `references/upstream/operations/configure.md` |
| First-party operate runbook (status, logs, metrics, health, recovery) | `references/upstream/operations/operate.md` |
| Official docs endpoints, community search, GraphQL gaps, template discovery | `references/upstream/docs-and-api/request.md` |
| Railway DB analysis — pick the engine | `references/database/analyze-db.md` |
| Railway PostgreSQL analysis | `references/database/analyze-db-postgres.md` |
| Railway MySQL analysis | `references/database/analyze-db-mysql.md` |
| Railway Redis analysis | `references/database/analyze-db-redis.md` |
| Railway MongoDB analysis | `references/database/analyze-db-mongo.md` |
| "Latest"/"current"/"today" or docs show a command the local CLI lacks | `references/research/version-drift.md` |

## Quick triage cues

- "What flags does `railway X` support?" → `references/cli/railway-cli-command-reference.md`
- "Show me the exact help text for `railway X`" → `references/cli/railway-cli-live-help-snapshot.md`
- "Which Railway command fits this job?" → `references/cli/common-workflows.md`
- "I pasted a dashboard URL" → `references/upstream/resource-model-and-preflight.md`
- "The docs show a command I do not have" → `references/research/version-drift.md`
- "I want Railway's own runbook, not just CLI syntax" → matching file under `references/upstream/operations/`

## Refresh the local snapshot

Run from this skill's content directory after a `railway` upgrade:

```bash
node scripts/extract-railway-cli-help.mjs
railway --version
```

This regenerates `references/cli/railway-cli-command-reference.md`, `references/cli/railway-cli-live-help-snapshot.md`, and `references/cli/railway-cli-command-tree.json` so this skill keeps tracking the installed binary.

## Output contract

Return Railway answers in this order unless the user asks for a different shape:

1. **Scope line** — `local installed CLI`, `upstream Railway sources`, or `both`.
2. **Best command or routed next step** — copy-pasteable when the answer is a command.
3. **Important flags, aliases, nested subcommands, possible values** — only what's relevant.
4. **Near-neighbor distinction** — when the next confusion is one keystroke away.
5. **Version-drift note** — only if it materially changes the answer.

## Guardrails

- Do not treat `railway deploy` and `railway up` as synonyms. `up` ships local code; `deploy` provisions a template.
- Do not treat `railway delete` and `railway unlink` as synonyms. `delete` destroys the resource; `unlink` only detaches the local link.
- Do not treat `railway redeploy` and `railway restart` as synonyms. `redeploy` rebuilds; `restart` bounces the running container.
- Do not treat `railway connect` and `railway ssh` as synonyms. `connect` opens a DB shell; `ssh` opens a service shell.
- Do not present upstream-only commands as locally available without saying so explicitly.
- Do not default to dashboard instructions when the user asked about the CLI.
- Do not let upstream runbooks override the local extracted CLI when the question is about the installed binary's exact surface.
- Do not trust the linked directory over an explicit dashboard URL or explicit `--project / --environment / --service` flags.
- Do not mutate Railway resources unless the user explicitly asked for an operational action.
- Do not author Makefile deploy targets here — that is `init-makefiles`. This skill explains the commands; `init-makefiles` wraps them.
