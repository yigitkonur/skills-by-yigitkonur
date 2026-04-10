# Marketplace

Workflows and plugins are distributed through marketplace repositories — GitHub repos with catalog files that Athena uses for resolution.

## Primary Marketplace

The default marketplace is `lespaceman/athena-workflow-marketplace` on GitHub.

## Installing a Workflow

```bash
athena workflow install e2e-test-builder@lespaceman/athena-workflow-marketplace --name e2e-test-builder
```

This:

1. Clones the marketplace repo to `~/.config/athena/marketplaces/lespaceman/athena-workflow-marketplace/` (cached after first use)
2. Reads `.athena-workflow/marketplace.json` to find the workflow
3. Copies the definition to `~/.config/athena/workflows/e2e-test-builder/workflow.json`

Then activate it:

```bash
athena-flow --workflow=e2e-test-builder
```

## Plugin Resolution

Plugins are resolved at runtime (not pre-installed). A marketplace ref like `e2e-test-builder@lespaceman/athena-workflow-marketplace` causes Athena to:

1. Clone/update the marketplace repo
2. Read `.claude-plugin/marketplace.json`
3. Resolve the plugin from the `source` path (relative to `pluginRoot`)
4. Load the plugin directory

## Versioned Plugin Resolution

Plugins can also be fetched from npm with version pinning:

```json
{
  "plugins": [
    { "ref": "my-plugin@org/repo", "version": "1.2.0" }
  ]
}
```

Versioned plugins are cached at `~/.config/athena/plugin-packages/`. Falls back to marketplace git repo if npm fails.

## Marketplace Repository Structure

```
athena-workflow-marketplace/
  .claude-plugin/
    marketplace.json          # Plugin catalog
  .athena-workflow/
    marketplace.json          # Workflow catalog
  .workflows/
    e2e-test-builder/
      workflow.json
      system-prompt.md
  plugins/
    e2e-test-builder/
      .claude-plugin/plugin.json
      skills/
        add-e2e-tests/SKILL.md
    site-knowledge/
      .claude-plugin/plugin.json
      skills/...
```

## The Two Catalogs

### Plugin Catalog: `.claude-plugin/marketplace.json`

```json
{
  "name": "athena-workflow-marketplace",
  "owner": { "name": "lespaceman" },
  "metadata": { "pluginRoot": "./plugins" },
  "plugins": [
    { "name": "e2e-test-builder", "source": "e2e-test-builder", "description": "..." }
  ]
}
```

With `pluginRoot: "./plugins"`, the `source` is a subdirectory name. Without it, use a relative path.

### Workflow Catalog: `.athena-workflow/marketplace.json`

```json
{
  "workflows": [
    { "name": "e2e-test-builder", "source": "./.workflows/e2e-test-builder/workflow.json", "description": "..." }
  ]
}
```

## Manifest Resolution Priority

Athena checks for marketplace manifests in this order:
1. `.athena-workflow/marketplace.json` (preferred)
2. `.claude-plugin/marketplace.json` (legacy/fallback)

## Caching

Marketplace repos are cloned to `~/.config/athena/marketplaces/<owner>/<repo>/`. Athena pulls latest on each use. If offline, the cached version is used.

## Hosting a Private Marketplace

Any GitHub repo with the correct structure acts as a marketplace:

```
your-marketplace/
  .claude-plugin/marketplace.json
  .athena-workflow/marketplace.json  # optional
  plugins/my-plugin/...
  .workflows/my-workflow/...         # optional
```

Reference as `plugin-name@your-org/your-marketplace`.

## Workflow CLI Commands

```bash
athena workflow install <ref> --name <local-name>  # Install from marketplace
athena workflow list                                # List installed workflows
athena workflow search <query>                      # Search marketplace
athena workflow remove <name>                       # Remove installed workflow
athena workflow upgrade <name>                      # Upgrade to latest
athena workflow use <name>                          # Set as active workflow
```

## Marketplace CLI Commands

```bash
athena marketplace add <owner/repo>    # Add a marketplace source
athena marketplace remove <owner/repo> # Remove a marketplace source
athena marketplace list                # List configured marketplaces
```
