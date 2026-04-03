---
name: build-openclaw-plugin
description: Use skill if you are building OpenClaw plugins — registering tools, channels, model providers, writing plugin manifests, and configuring tool profiles.
---

# Build OpenClaw Plugin

Build plugins that extend the OpenClaw agent runtime with new tools, channels, model providers, speech engines, image generators, and bundled skills.

## Trigger boundary

Use this skill when the task involves:

- Creating a new OpenClaw plugin from scratch
- Registering tools, channels, model providers, speech providers, or image generators
- Writing or editing an `openclaw.plugin.json` manifest
- Bundling skills inside a plugin
- Configuring tool profiles, allow/deny lists, or provider-specific restrictions
- Publishing a plugin to npm as an external package
- Migrating to or from the Plugin SDK

Do NOT use this skill for:

- Building standalone OpenClaw skills without plugin packaging (use build-skills)
- Optimizing an existing MCP server (use optimize-mcp-server)
- General Node.js/TypeScript development unrelated to OpenClaw
- Configuring OpenClaw itself (agent config, environment setup)

## Core concepts

OpenClaw plugins are npm packages that register one or more extension points:

| Extension point | What it does | Example |
|---|---|---|
| **Tools** | Typed function definitions sent to the model API | File search, web scrape, database query |
| **Channels** | Communication interfaces (Slack, Discord, REST, etc.) | Telegram bot channel, webhook receiver |
| **Model providers** | LLM backends (OpenAI, Anthropic, local models) | Custom fine-tuned model endpoint |
| **Speech providers** | Text-to-speech / speech-to-text engines | ElevenLabs, Whisper |
| **Image generators** | Image creation backends | DALL-E, Stable Diffusion |
| **Skills** | Bundled skill directories loaded when plugin is enabled | Domain-specific prompt workflows |

Plugins are classified as:

- **Core** — shipped with OpenClaw, maintained in the main repo
- **External** — npm-published, installed separately, community-maintained

## Decision tree

```
User request
|
+-- "Create a new plugin from scratch"
|   -> Read references/guides/plugin-manifest.md
|   -> Read references/guides/plugin-lifecycle.md
|   -> Follow: New Plugin Workflow (below)
|
+-- "Register a tool in my plugin"
|   +-- Single tool ----------> Read references/guides/tool-registration.md
|   +-- Multiple tools -------> Read references/guides/tool-registration.md
|   +-- Tool needs groups -----> Read references/patterns/tool-profiles-and-restrictions.md
|   +-- Tool needs allow/deny -> Read references/patterns/tool-profiles-and-restrictions.md
|
+-- "Register a channel or provider"
|   +-- Channel (messaging) ---> Read references/guides/channel-provider-setup.md
|   +-- Model provider --------> Read references/guides/channel-provider-setup.md
|   +-- Speech provider -------> Read references/guides/channel-provider-setup.md
|   +-- Image generator -------> Read references/guides/channel-provider-setup.md
|
+-- "Bundle skills in my plugin"
|   -> Read references/guides/plugin-lifecycle.md (skills section)
|   -> Read references/patterns/plugin-skills-bundling.md
|
+-- "Configure tool profiles or restrictions"
|   +-- Set up profiles (full/coding/messaging/minimal)
|   |   -> Read references/patterns/tool-profiles-and-restrictions.md
|   +-- Allow/deny lists
|   |   -> Read references/patterns/tool-profiles-and-restrictions.md
|   +-- Provider-specific restrictions
|       -> Read references/patterns/tool-profiles-and-restrictions.md
|
+-- "Publish my plugin"
|   -> Read references/guides/plugin-lifecycle.md (publishing section)
|
+-- "Debug a plugin issue"
    +-- Plugin not loading -----> Read references/guides/plugin-manifest.md (validation)
    +-- Tool not appearing -----> Read references/patterns/tool-profiles-and-restrictions.md
    +-- Config gating issue ----> Read references/guides/plugin-manifest.md (requires section)
    +-- Skills not loading -----> Read references/patterns/plugin-skills-bundling.md
```

## New Plugin Workflow

### Phase 0: Verify the runtime boundary first

Before scaffolding anything, verify these three boundary conditions:

1. **SDK source is real.** Confirm the actual Plugin SDK import path from the target OpenClaw runtime, monorepo, or an existing working plugin. Do not assume a public npm package exists just because examples show one.
2. **Package name and runtime name are distinct.** Decide both identifiers up front:
   - npm package name: usually `openclaw-plugin-{your-name}`
   - manifest `name`: the runtime plugin identifier inside `openclaw.plugin.json`
3. **Local verification path exists.** Know how you will install and enable the plugin in a real OpenClaw runtime before you start coding.

Success signal for this phase: the SDK import path is known and a local build can resolve it. If you cannot verify the SDK source or local runtime path, stop at manifest/design output and ask for the missing runtime evidence instead of inventing installation steps.

### Phase 1: Define scope

1. Identify which extension points the plugin provides (tools, channels, providers, skills)
2. Decide core vs. external classification
3. Choose both names now:
   - npm package name: `openclaw-plugin-{your-name}`
   - manifest/runtime name: short kebab-case plugin identifier used by OpenClaw
4. List configuration keys the plugin needs from the OpenClaw config

### Phase 2: Scaffold

Generate the project structure:

```
openclaw-plugin-example/
+-- openclaw.plugin.json       # Plugin manifest (required)
+-- package.json               # npm package metadata
+-- src/
|   +-- index.ts               # Plugin entry point
|   +-- tools/                 # Tool definitions
|   |   +-- my-tool.ts
|   +-- channels/              # Channel implementations (if any)
|   +-- providers/             # Model/speech/image providers (if any)
+-- skills/                    # Bundled skills (if any)
|   +-- my-skill/
|       +-- SKILL.md
|       +-- references/
+-- tsconfig.json
+-- README.md
```

### Phase 3: Write the manifest

Read `references/guides/plugin-manifest.md` for the full manifest specification. Minimal example:

```json
{
  "name": "example",
  "version": "1.0.0",
  "description": "An example OpenClaw plugin",
  "main": "dist/index.js",
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["EXAMPLE_API_KEY"]
      }
    }
  },
  "tools": [],
  "channels": [],
  "modelProviders": [],
  "speechProviders": [],
  "imageGenerators": [],
  "skills": ["skills"]
}
```

In this example, the npm package could be named `openclaw-plugin-example` while the manifest `name` remains `example`. Keep those two names aligned in documentation, but do not collapse them into one concept.

### Phase 4: Implement extension points

For each extension point, follow the relevant reference:

- **Tools**: Read `references/guides/tool-registration.md` — define typed functions with name, description, parameters schema, and handler; the handler still performs runtime validation before any side effect
- **Channels/Providers**: Read `references/guides/channel-provider-setup.md` — implement the required interface for the extension type
- **Skills**: Read `references/patterns/plugin-skills-bundling.md` — place skill directories under the declared `skills` path

### Phase 5: Configure restrictions

If the plugin's tools need controlled access:

- Set up tool groups for logical organization
- Configure allow/deny lists if certain tools should be restricted
- Assign tool profiles for different usage contexts
- Read `references/patterns/tool-profiles-and-restrictions.md`

### Phase 6: Test and publish

Use the CLI loop below only if the target runtime actually exposes `openclaw plugins ...` commands. If it does not, stop after step 1 and ask for the exact config-based local plugin load path instead of guessing the config file, key, or install location.

1. Verify the SDK/build path first. Success signal: `tsc --noEmit`, the repo's build command, or equivalent local build resolves the actual OpenClaw SDK imports without path hacks.
2. Install the plugin locally with an absolute path:
   - `openclaw plugins install -l /abs/path/to/openclaw-plugin-example`
3. Enable it by the manifest/runtime name, not the npm package name:
   - `openclaw plugins enable example`
4. Run `openclaw doctor`, then `openclaw status` to confirm the runtime is healthy and the plugin is visible.
5. Verify each extension point actually appears and behaves correctly:
   - tools are listed and callable
   - skills load from the declared relative path
   - config gating disables the plugin when required keys are missing
   - invalid tool input is rejected by the handler, not just by the manifest schema
6. If the plugin CLI is unavailable in the target environment, stop after manifest/build verification and report that local runtime verification is blocked until the user provides a working OpenClaw install path or the exact config-based local plugin entry used by that runtime. Do not invent the config key or file name.
7. For external plugins: publish to npm with proper `openclaw.plugin.json` in the package

## Tool groups reference

Tools are organized into groups for bulk allow/deny operations:

| Group | Purpose |
|---|---|
| `group:fs` | File system operations |
| `group:runtime` | Code execution, shell commands |
| `group:web` | HTTP requests, web scraping |
| `group:ui` | UI rendering, display |
| `group:memory` | Persistent memory, knowledge base |
| `group:sessions` | Session management |
| `group:messaging` | Message sending, channels |
| `group:nodes` | Workflow node operations |
| `group:automation` | Automated task execution |
| `group:agents` | Sub-agent spawning and management |
| `group:media` | Audio, video, image processing |

## Tool profiles quick reference

| Profile | Includes | Use case |
|---|---|---|
| `full` | All tools | Unrestricted agent access |
| `coding` | `group:fs` + `group:runtime` + `group:sessions` + `group:memory` + `group:media` | Software development workflows |
| `messaging` | `group:messaging` + session list/history/send/status | Chat-focused agents |
| `minimal` | `session_status` only | Monitoring, health checks |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Missing `openclaw.plugin.json` in published package | Add it to `package.json` `files` array |
| Plugin loads but tools not visible | Check tool group membership and active profile |
| Config gating not working | Verify `metadata.openclaw.requires.config` key names match exactly |
| Skills directory not found | Use relative path from plugin root in manifest `skills` array |
| Deny list not blocking a tool | `tools.deny` overrides `tools.allow` — verify the tool name or group |
| Provider-specific restrictions ignored | Check `tools.byProvider` matches the model provider ID exactly |
| Tool parameters not validated | Define a schema for model guidance, then validate again in the handler before side effects |
| Plugin works locally but fails when installed from npm | Ensure `dist/` is built and `main` field points to compiled output |

## Reference routing

### Guides

| File | Read when |
|---|---|
| `references/guides/plugin-manifest.md` | Creating or editing `openclaw.plugin.json`, understanding manifest fields, config gating, validation |
| `references/guides/tool-registration.md` | Defining tools — typed function signatures, parameter schemas, handlers, tool naming |
| `references/guides/channel-provider-setup.md` | Implementing channels, model providers, speech providers, or image generators |
| `references/guides/plugin-lifecycle.md` | Understanding plugin loading order, initialization, publishing, and the core vs external distinction |

### Patterns

| File | Read when |
|---|---|
| `references/patterns/tool-profiles-and-restrictions.md` | Configuring tool profiles (full/coding/messaging/minimal), allow/deny lists, provider-specific restrictions, tool groups |
| `references/patterns/plugin-skills-bundling.md` | Bundling skills inside a plugin, skill directory structure, skill loading behavior when plugin is enabled |

## Guardrails

- NEVER publish a plugin without `openclaw.plugin.json` in the package.
- NEVER hardcode API keys or secrets in plugin source — use config gating via `metadata.openclaw.requires.config`.
- NEVER register tools without descriptions — the model cannot select undescribed tools.
- NEVER assume the SDK package name or import path; verify it against the target OpenClaw runtime first.
- NEVER assume all tools are available — respect the active profile and allow/deny lists.
- ALWAYS validate tool input parameters in the handler; model-generated parameters and manifest schemas are not a security boundary.
- ALWAYS declare required config keys in the manifest so the plugin is disabled when config is missing.
- ALWAYS test with `minimal` profile to verify graceful degradation when tools are restricted.
- ALWAYS use kebab-case for plugin names and tool names.
- PREFER tool groups for bulk access control over individual tool allow/deny entries.
- PREFER `tools.deny` for blocking specific dangerous tools rather than allowlisting everything else.
- When deny and allow conflict, deny always wins.
