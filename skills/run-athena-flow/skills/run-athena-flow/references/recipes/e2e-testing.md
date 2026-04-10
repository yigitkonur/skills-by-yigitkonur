# E2E Test Workflow Recipe

Use the `e2e-test-builder` workflow to generate Playwright E2E tests for your project.

## Install

```bash
athena workflow install e2e-test-builder@lespaceman/athena-workflow-marketplace --name e2e-test-builder
```

## Run

```bash
cd /your/project
athena-flow --workflow=e2e-test-builder
```

The workflow loads two plugins (`e2e-test-builder`, `site-knowledge`), sets isolation to `minimal`, and starts a loop.

## What Happens

1. The agent analyzes your existing test conventions (`/analyze-test-codebase`)
2. Plans test coverage for untested surfaces (`/plan-test-coverage`)
3. Generates Playwright test files (`/write-e2e-tests`)
4. Runs the tests with `npx playwright test`
5. Iterates — fixing failures, adding missing coverage

The loop continues until the agent outputs `ATHENA_COMPLETE`, `ATHENA_BLOCKED`, or 10 iterations are reached.

## The Tracker File

The workflow writes state to `.athena-tracker.json` in your project root:

```json
{
  "testsGenerated": ["homepage.spec.ts", "login.spec.ts"],
  "testsRemaining": ["checkout.spec.ts"],
  "failures": []
}
```

Each subsequent iteration receives the continue prompt with the tracker path interpolated.

## Skills Available

| Skill | Description |
|-------|-------------|
| `/add-e2e-tests <url> <feature>` | Full pipeline orchestrator |
| `/analyze-test-codebase [path]` | Detect Playwright config and conventions |
| `/plan-test-coverage <url> <feature>` | Build a prioritized coverage plan |
| `/explore-website <url> <goal>` | Extract selectors via browser interaction |
| `/generate-test-cases <url> <journey>` | Generate structured TC-ID specs |
| `/write-e2e-tests <description>` | Implement executable Playwright tests |

## CI Mode

```bash
athena-flow exec "add e2e tests for the checkout flow" \
  --workflow=e2e-test-builder \
  --on-permission=allow \
  --on-question=empty \
  --timeout-ms=600000
```

## Customizing

Copy the workflow locally and modify it:

```bash
cp ~/.config/athena/workflows/e2e-test-builder/workflow.json ./my-workflow.json
```

Edit `promptTemplate`, `maxIterations`, `model`, or `isolation` to suit your project.

## Browser Automation

The `e2e-test-builder` plugin includes the `agent-web-interface` MCP server for browser automation. This provides semantic page snapshots instead of raw DOM access, producing more stable selectors and faster test generation.
