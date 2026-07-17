---
name: test-martool-cli
description: Use skill if you are exhaustively testing or release-gating martool CLI commands in a source checkout or deployed Coolify container over SSH, without local Docker or provider spend.
---

# Test martool CLI

Run martool's two authoritative black-box matrices through one evidence-producing entrypoint. Use source mode for a checkout and Coolify mode for an already-deployed container. A full pass proves every manifest-derived case completed with exact coverage and no provider calls; a filtered pass is diagnostic only.

## Essential rules

1. Read the nearest repository instructions before running or changing anything.
2. Use martool's bundled audit harnesses as the source of truth. Do not reimplement their flag cases in ad hoc shell loops.
3. Run against the user's requested target. If they name Coolify, Hetzner, SSH, a deployed image, or say not to use local Docker, use Coolify mode and never start local Docker.
4. Predeclare the scope: full release proof or one-command diagnostic. Never describe a filtered or single-matrix run as exhaustive.
5. Require zero platform provider calls and zero paid provider calls. Do not add credentials to make an audit pass.
6. Pin deployed evidence to one healthy container ID and image ID before the run; fail if either changes.
7. Save and inspect the raw reports plus `combined.json` before claiming a result.

## When to use

Use this skill when the user asks to:

- run all martool CLI commands or flags;
- combine the generated and platform CLI audits;
- verify a martool release candidate or deployed image;
- reproduce one martool command's flag matrix;
- prove CLI coverage without DataForSEO spend; or
- test the live Coolify image over SSH instead of local Docker.

Do not use it for a generic CLI, MCP protocol testing, live provider-quality testing, deployment, or application feature development. Use `test-by-mcpc-cli` for MCP transport/tool smoke and `deploy-coolify-cloud` for deployment changes.

## Reference router

| Situation | Read |
|---|---|
| First use, installation, runtime prerequisites, or locating the skill script | [references/installation.md](references/installation.md) |
| Deciding whether evidence is exhaustive and interpreting JSON or exit codes | [references/audit-contract.md](references/audit-contract.md) |
| Hetzner/Coolify, SSH, container discovery, image pinning, or remote safety | [references/coolify-remote.md](references/coolify-remote.md) |
| A command fails, coverage is partial, discovery is ambiguous, or reports are missing | [references/troubleshooting.md](references/troubleshooting.md) |

Common reading sets:

- First source run: installation + audit contract.
- First deployed run: installation + Coolify remote + audit contract.
- Failed run: audit contract + troubleshooting; add Coolify remote for SSH/container failures.

## Workflow

### 1. Frame the proof

Record:

- target: source checkout or existing Coolify deployment;
- scope: both matrices or a diagnostic subset;
- expected source revision or deployed image;
- report directory; and
- completion condition.

The default completion condition is: both matrices pass, coverage is exact, platform `provider_calls` and `paid_provider_calls` are zero, the target stays pinned, and the combined verdict is `verified`.

### 2. Resolve the installed skill

Resolve `MARTOOL_CLI_SKILL_DIR` to the directory containing this `SKILL.md`. Do not assume the skill lives in the target repository.

```bash
export MARTOOL_CLI_SKILL_DIR=/path/to/installed/test-martool-cli
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" --help
```

Read [installation](references/installation.md) if the skill path, Node, pnpm, SSH, or remote Docker access is uncertain.

### 3. Preflight the requested target

For a source checkout, confirm `package.json` identifies martool and use its supported Node/pnpm versions. The runner builds `dist/cli/main.js` by default; use `--no-build` only when intentionally auditing an already-built artifact.

For Coolify, require an explicit SSH host or alias. The runner discovers exactly one running, healthy container from `coolify.projectName` and `com.docker.compose.service`, unless `--container` explicitly pins one. It verifies the image contains the CLI and both audit scripts before spending time on the matrices.

Do not deploy, restart, recreate, or install packages in the remote container. A missing or stale image is deployment evidence, not permission to mutate production.

### 4. Run the combined audit

Source checkout:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target source \
  --repo /path/to/martool \
  --report-dir /tmp/martool-cli-source-proof
```

Existing Coolify deployment:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify \
  --ssh-host hetzner \
  --report-dir /tmp/martool-cli-coolify-proof
```

The runner writes progress to stderr and exactly one compact JSON summary to stdout. Redirect stdout if another system needs to consume it; the evidence directory still receives `combined.json` and the raw matrix reports.

### 5. Use diagnostics without overstating them

Select one matrix only when isolating a failure:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target source --repo /path/to/martool \
  --matrix generated
```

Filter to one exact manifest command when reproducing its cases:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify --ssh-host hetzner \
  --command "keywords research"
```

A run using `--matrix` other than `all` or any `--command` filter must return `diagnostic-pass`, not `verified`. Read [the audit contract](references/audit-contract.md) before reporting the result.

### 6. Inspect evidence and classify the outcome

Inspect `combined.json` first, then the raw report named by any failed check.

Possible outcomes:

| Verdict | Meaning | Next action |
|---|---|---|
| `verified` | Both full matrices passed with exact coverage on one pinned target | Report the target IDs, totals, coverage, and zero-provider proof |
| `diagnostic-pass` | Every selected case passed, but the scope was intentionally partial | Report the exact matrix/command scope; do not call it exhaustive |
| `failed` | Preflight, execution, coverage, safety, or target-pinning contract failed | Classify from the raw report and [troubleshooting](references/troubleshooting.md) |

Do not convert an unavailable provider, stale deployment, missing harness, ambiguous container, or incomplete matrix into a pass by weakening validation.

### 7. Report at the evidence rung reached

Include:

- source commit or deployed container/image IDs;
- selection (`all`, one matrix, or one command);
- manifest-derived command counts;
- attempted/pass/fail totals for each executed matrix;
- coverage completeness;
- platform provider-call counters;
- raw report hashes and combined report path; and
- final verdict.

Historical command/case counts are examples only. The current `martool usage --json` manifest and raw audit reports determine the expected totals for every run.

## Guardrails

- Never use local Docker for Coolify verification.
- Never print remote environment variables, Docker inspect environment data, credentials, or SSH configuration.
- Never run paid provider commands to prove the CLI harness.
- Never hard-code current command or case counts as acceptance thresholds.
- Never report `verified` from a single matrix, filtered command, old report, or changed container.
- Never edit martool's generated `skills/martool/SKILL.md` by hand; it is product-generated usage guidance, not this testing workflow.
