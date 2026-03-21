# Plugin Lifecycle

This guide covers how OpenClaw discovers, loads, and manages plugins — from installation through runtime to publishing.

## Discovery and loading order

When OpenClaw starts, it discovers plugins through these mechanisms in order:

1. **Core plugins** — bundled in the OpenClaw installation, always available
2. **Installed plugins** — npm packages in the project's `node_modules` that contain `openclaw.plugin.json`
3. **Local plugins** — directories referenced in the OpenClaw configuration file

For each discovered plugin, OpenClaw:

1. Reads `openclaw.plugin.json`
2. Checks config gating — are all `metadata.openclaw.requires.config` keys present?
3. If gating passes: loads the `main` entry point and calls `initialize()`
4. Registers all declared extension points (tools, channels, providers, skills)
5. If gating fails: skips the plugin and logs which config keys are missing

## Config gating in detail

Config gating is the primary mechanism for conditional plugin activation.

```json
{
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
      }
    }
  }
}
```

**How it works:**

- OpenClaw checks each key against its configuration store
- ALL listed keys must have non-empty values
- If any key is missing or empty, the entire plugin is disabled
- The user sees a message indicating which keys need to be set

**When to use config gating:**

- API keys required for the plugin to function
- Service URLs or endpoints
- Feature flags that control plugin availability

**When NOT to use config gating:**

- Optional features within the plugin (handle these in code with graceful fallbacks)
- User preferences (these should be runtime settings, not plugin gates)

## Initialization

The plugin's `initialize()` method runs after config gating passes:

```typescript
export default class MyPlugin extends Plugin {
  async initialize(config: Record<string, string>): Promise<void> {
    // config contains the resolved OpenClaw configuration
    // This is where you:
    // - Validate credentials
    // - Set up connections
    // - Initialize caches
    // - Register dynamic tools (if not declared in manifest)
  }
}
```

**Rules:**

- `initialize()` should fail fast if critical setup fails
- Do not start long-running background processes here — use lazy initialization
- Store config references for later use by tools and providers
- Throw a descriptive error if initialization fails (do not silently degrade)

## Shutdown

When OpenClaw shuts down, it calls `shutdown()` on each loaded plugin:

```typescript
async shutdown(): Promise<void> {
  // Close database connections
  // Stop webhook listeners
  // Flush pending writes
  // Cancel timers
}
```

**Rules:**

- `shutdown()` must complete within a reasonable timeout (5 seconds)
- Never throw from `shutdown()` — log errors instead
- Clean up all resources to prevent memory leaks during testing

## Skills loading

When a plugin declares `"skills": ["skills"]`, OpenClaw loads skill directories from that path relative to the plugin root.

```
my-plugin/
+-- openclaw.plugin.json    # "skills": ["skills"]
+-- skills/
    +-- my-workflow/
    |   +-- SKILL.md
    |   +-- references/
    +-- my-other-skill/
        +-- SKILL.md
```

Skills are loaded **only when the plugin is enabled** (config gating passed). They follow the same SKILL.md format as standalone skills.

See `references/patterns/plugin-skills-bundling.md` for detailed bundling patterns.

## Core vs. external plugins

| Aspect | Core | External |
|---|---|---|
| Location | Shipped in OpenClaw repo | Published to npm |
| Maintenance | OpenClaw team | Community / third party |
| Discovery | Always available | Must be `npm install`ed |
| Config gating | Same mechanism | Same mechanism |
| Quality bar | Must pass OpenClaw CI | Author's responsibility |
| Versioning | Follows OpenClaw version | Independent semver |

### Building a core plugin

Core plugins live in the OpenClaw monorepo. If you are contributing:

1. Follow the monorepo's contribution guidelines
2. Place the plugin in the designated plugins directory
3. Add tests that run in OpenClaw's CI
4. Update the plugin registry documentation

### Building an external plugin

External plugins are standalone npm packages:

1. Create a standard npm package
2. Include `openclaw.plugin.json` at the root
3. Ensure `package.json` `files` includes the manifest and compiled output
4. Publish to npm: `npm publish`
5. Users install with: `npm install openclaw-plugin-yourname`

## Publishing checklist

Before publishing an external plugin:

- [ ] `openclaw.plugin.json` is valid and complete
- [ ] `package.json` `files` includes `openclaw.plugin.json` and `dist/`
- [ ] `main` in manifest points to compiled JS (not TypeScript)
- [ ] All config keys are documented in README
- [ ] Plugin loads correctly in a fresh OpenClaw installation
- [ ] Config gating works: plugin disabled when keys are missing
- [ ] Config gating works: plugin enables when keys are provided
- [ ] All tools respond correctly to valid and invalid input
- [ ] `shutdown()` cleans up without errors
- [ ] Package name follows convention: `openclaw-plugin-{name}`
- [ ] Version follows semver
- [ ] No secrets, API keys, or hardcoded credentials in source

## Plugin SDK migration

If migrating from an older plugin format to the current Plugin SDK:

1. Replace custom registration code with `extends Plugin`
2. Move tool definitions to the `tools` property or manifest
3. Implement `initialize()` and `shutdown()` lifecycle methods
4. Update `openclaw.plugin.json` to match the current schema
5. Test that all extension points register correctly after migration
