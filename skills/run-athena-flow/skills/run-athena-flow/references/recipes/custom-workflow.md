# Custom Workflow from Scratch

Build a workflow definition, test it locally, and optionally publish it.

## 1. Create the Workflow File

```json
{
  "name": "dependency-audit",
  "version": "1.0.0",
  "description": "Audit project dependencies for issues.",
  "promptTemplate": "Audit all dependencies in this project. Check for outdated packages, known vulnerabilities, and unused dependencies. Output a structured report.",
  "plugins": [],
  "isolation": "strict",
  "model": "sonnet"
}
```

## 2. Add a Loop (Optional)

For iterative tasks, add loop configuration:

```json
{
  "name": "dependency-audit",
  "version": "1.0.0",
  "description": "Audit project dependencies for issues.",
  "promptTemplate": "Audit all dependencies in this project.",
  "loop": {
    "enabled": true,
    "completionMarker": "ATHENA_COMPLETE",
    "maxIterations": 5,
    "blockedMarker": "ATHENA_BLOCKED",
    "trackerPath": ".audit-tracker.json",
    "continuePrompt": "Continue the audit. Tracker: {trackerPath}"
  },
  "isolation": "strict"
}
```

## 3. Bundle Plugins

Reference marketplace or local plugins:

```json
{
  "plugins": [
    "my-plugin@my-org/my-marketplace",
    "./local-helpers"
  ]
}
```

These auto-load when the workflow activates. MCP configs from all plugins are merged.

## 4. Add a System Prompt (Optional)

```json
{
  "systemPromptFile": "./system-prompt.md"
}
```

Create the markdown file relative to the workflow directory.

## 5. Add Environment Variables (Optional)

```json
{
  "env": {
    "NODE_ENV": "test",
    "AUDIT_STRICT": "true"
  }
}
```

## 6. Install Locally

Copy to the local registry:

```bash
mkdir -p ~/.config/athena/workflows/dependency-audit
cp workflow.json ~/.config/athena/workflows/dependency-audit/
```

## 7. Test

Interactive:

```bash
athena-flow --workflow=dependency-audit
```

Headless:

```bash
athena-flow exec "audit dependencies" --workflow=dependency-audit
```

## 8. Publish to a Marketplace

Add the workflow to a marketplace repo:

```
your-marketplace/
  .athena-workflow/
    marketplace.json
  .workflows/
    dependency-audit/
      workflow.json
      system-prompt.md
```

Register in `.athena-workflow/marketplace.json`:

```json
{
  "workflows": [
    {
      "name": "dependency-audit",
      "source": "./.workflows/dependency-audit/workflow.json",
      "description": "Audit project dependencies for issues"
    }
  ]
}
```

Others install with:

```bash
athena workflow install dependency-audit@your-org/your-marketplace --name dependency-audit
```

## Workflow Design Tips

- Keep `promptTemplate` focused on outcomes, not implementation steps
- Use `trackerPath` for tasks that span multiple iterations
- Set `maxIterations` based on expected task complexity (5-10 for most workflows)
- Use `isolation: "strict"` unless your workflow needs web access or MCP tools
- Test in interactive mode before deploying to CI
- Use `systemPromptFile` for complex behavioral guidance that would clutter `promptTemplate`
