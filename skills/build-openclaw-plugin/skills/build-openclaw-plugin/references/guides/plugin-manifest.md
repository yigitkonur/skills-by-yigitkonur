# Plugin Manifest Reference

The `openclaw.plugin.json` file is the required manifest for every OpenClaw plugin. It declares what the plugin provides and what it requires to run.

## File location

Place `openclaw.plugin.json` at the root of the npm package (next to `package.json`). It must be included in the published package via the `files` field in `package.json`.

## Name boundary: package vs runtime identifier

Do not treat the npm package name and the manifest `name` as the same field.

- npm package name: usually `openclaw-plugin-yourname`
- manifest `name`: the runtime plugin identifier inside `openclaw.plugin.json`

Example:

- `package.json` `name`: `openclaw-plugin-example`
- `openclaw.plugin.json` `name`: `example`

The runtime identifier is what `openclaw plugins enable <name>` and runtime status output will use.

## Full manifest schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Human-readable description of what this plugin does",
  "main": "dist/index.js",
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["MY_API_KEY", "MY_SECRET"]
      }
    }
  },
  "tools": [
    {
      "name": "my_tool",
      "description": "What this tool does and when to use it",
      "group": "group:web",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The search query"
          }
        },
        "required": ["query"]
      }
    }
  ],
  "channels": ["telegram", "slack"],
  "modelProviders": ["my-custom-model"],
  "speechProviders": ["my-tts-engine"],
  "imageGenerators": ["my-image-gen"],
  "skills": ["skills"]
}
```

## Field reference

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Runtime plugin identifier, kebab-case, distinct from the npm package name |
| `version` | string | Yes | Semver version |
| `description` | string | Yes | What the plugin does (shown in UI) |
| `main` | string | Yes | Path to compiled entry point |
| `metadata` | object | No | Plugin metadata including config requirements |
| `tools` | array | No | Tool definitions (see Tool Registration guide) |
| `channels` | array | No | Channel type identifiers |
| `modelProviders` | array | No | Model provider identifiers |
| `speechProviders` | array | No | Speech provider identifiers |
| `imageGenerators` | array | No | Image generator identifiers |
| `skills` | array | No | Relative paths to skill directories |

### metadata.openclaw.requires.config

An array of configuration key names. The plugin is **disabled** unless every listed key has a non-empty value in the OpenClaw configuration.

```json
{
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["OPENAI_API_KEY"]
      }
    }
  }
}
```

This is the gating mechanism — it prevents the plugin from loading when its dependencies (API keys, service URLs, etc.) are not configured. Users see a clear message about which config keys are missing.

**Rules for config gating:**

- List only keys that are truly required for the plugin to function
- Use SCREAMING_SNAKE_CASE for config key names
- Each key must match exactly what the user sets in their OpenClaw config
- If the plugin has optional features that need additional config, handle those in the plugin code (not in the manifest requires)

## Validation checklist

When your manifest is ready, verify:

- [ ] `name` is unique, kebab-case, does not contain "openclaw" prefix (that is implied)
- [ ] `name` matches the runtime/plugin identifier you will enable locally
- [ ] `version` follows semver
- [ ] `main` points to the compiled output (not TypeScript source)
- [ ] Every tool in `tools` has `name`, `description`, and `parameters`
- [ ] Every required config key in `metadata.openclaw.requires.config` is documented in README
- [ ] `openclaw.plugin.json` is listed in `package.json` `files` array
- [ ] The file parses as valid JSON (no trailing commas, no comments)

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `main` points to `.ts` file | Plugin fails to load at runtime | Point to `dist/index.js` (compiled output) |
| Manifest `name` copied from npm package name | Runtime enable/status commands refer to the wrong identifier | Keep npm package name and manifest `name` distinct and document both |
| Config key name mismatch | Plugin disabled even when config exists | Match key names exactly (case-sensitive) |
| Missing from `files` in package.json | Plugin installs but manifest not found | Add `"openclaw.plugin.json"` to `files` array |
| Trailing comma in JSON | Parse error on load | Use a JSON linter before publishing |
| Empty `tools` array when tools exist | Tools not registered | Populate the array with tool definitions or register dynamically in code |
| `skills` path is absolute | Skills not found on other machines | Use relative paths from the plugin root |
