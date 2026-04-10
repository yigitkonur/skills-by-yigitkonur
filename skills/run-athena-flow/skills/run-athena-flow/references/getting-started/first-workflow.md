# Your First Workflow

Install a workflow from the marketplace, run it, and see what happens.

## Install the Workflow

```bash
athena workflow install e2e-test-builder@lespaceman/athena-workflow-marketplace --name e2e-test-builder
```

Athena clones the marketplace repo (first time only), reads the workflow catalog, and copies the definition to `~/.config/athena/workflows/e2e-test-builder/workflow.json`.

## Activate and Run

```bash
cd /your/project
athena-flow --workflow=e2e-test-builder
```

The workflow auto-loads its declared plugins (`e2e-test-builder`, `site-knowledge`), applies its isolation preset, and injects its prompt template into the session.

## What You'll See

The header shows the session state:

```
ATHENA v0.2.3 | ⠙ working              claude-sonnet-4-5 | tools:12 | ████░░░░░ | ●
```

The event feed streams every tool call as it happens:

```
09:41:02  tool.pre     claude  Read          src/tests/setup.ts
09:41:03  tool.post    claude  Read          2.1kb
09:41:05  tool.pre     claude  Bash          npx playwright test --list
09:41:09  tool.post    claude  Bash          exit 0
09:41:10  perm.req     athena  Write         src/tests/homepage.spec.ts
```

Each row is a discrete event from the agent runtime — tool calls, results, permission prompts, and agent messages.

## The Loop in Action

The `e2e-test-builder` workflow has `loop.enabled: true`. Athena re-prompts the agent after each iteration until:

- The agent outputs the `completionMarker` (`ATHENA_COMPLETE`)
- The agent outputs the `blockedMarker` (`ATHENA_BLOCKED`)
- `maxIterations` (10) is reached

A tracker file (`.athena-tracker.json`) persists state across iterations so the agent picks up where it left off.

## Next Steps

- Learn about workflows and the schema in detail
- Explore available plugins
- Build a custom workflow from scratch
