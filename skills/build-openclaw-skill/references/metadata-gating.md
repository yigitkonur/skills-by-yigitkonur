# Metadata Gating Guide

How to use the `metadata` field to gate skill availability based on environment requirements — required binaries, environment variables, config keys, and installer specs.

## Why metadata gating matters

Without gating, a skill that requires `docker` will load for users who don't have Docker installed. The agent will follow the skill's instructions, fail on the first `docker` command, and waste the user's time. Metadata gating prevents this by checking requirements before the skill is offered.

## The metadata field format

The `metadata` field must be **single-line JSON** in the frontmatter. OpenClaw does not support multi-line YAML for this field.

```yaml
metadata: {"openclaw": {"requires": {"bins": ["node", "npm"], "env": ["GITHUB_TOKEN"], "config": ["tsconfig.json"]}, "primaryEnv": "GITHUB_TOKEN"}}
```

### Structure breakdown

```json
{
  "openclaw": {
    "always": false,
    "emoji": "🔧",
    "os": ["darwin", "linux"],
    "requires": {
      "bins": ["binary1", "binary2"],
      "anyBins": ["alt-tool-a", "alt-tool-b"],
      "env": ["ENV_VAR_1", "ENV_VAR_2"],
      "config": ["config-file.json"]
    },
    "primaryEnv": "ENV_VAR_1",
    "install": []
  }
}
```

| Key | Type | Purpose |
|---|---|---|
| `openclaw` | object | Top-level namespace for OpenClaw-specific metadata |
| `openclaw.always` | boolean | If `true`, skill is included in every session regardless of other gates. Use sparingly for foundational skills. |
| `openclaw.emoji` | string | UI decoration displayed in the macOS Skills UI (e.g., `"🚀"`). Cosmetic only. |
| `openclaw.os` | string[] | Platform filter. Array of `"darwin"`, `"linux"`, `"win32"`. Skill is only eligible on listed platforms. Omit to allow all. |
| `requires` | object | Environment requirements that must be met |
| `requires.bins` | string[] | Binary executables that must ALL exist in PATH |
| `requires.anyBins` | string[] | At least ONE of the listed binaries must exist in PATH (logical OR, unlike `bins` which is logical AND) |
| `requires.env` | string[] | Environment variables that must be set |
| `requires.config` | string[] | Config files that must exist in the project |
| `primaryEnv` | string | The most important env var (shown in setup instructions) |

## Requirement types

### Binary requirements (`bins` — all required)

Check that ALL listed executables exist in the system PATH.

```yaml
metadata: {"openclaw": {"requires": {"bins": ["docker", "docker-compose"]}}}
```

Use cases:
- CLI tools the skill's workflow depends on (`node`, `python`, `go`, `cargo`)
- Runtime dependencies (`docker`, `kubectl`, `terraform`)
- Build tools (`make`, `cmake`, `gcc`)

The agent checks `which <binary>` or equivalent before offering the skill.

### Binary requirements (`anyBins` — at least one required)

Check that AT LEAST ONE of the listed executables exists in the system PATH. Use this when a skill can work with alternative tools.

```yaml
metadata: {"openclaw": {"requires": {"anyBins": ["pnpm", "npm", "yarn", "bun"]}}}
```

Use cases:
- Multiple package managers that serve the same purpose
- Alternative CLI tools (`vim` or `nvim`, `podman` or `docker`)

### Environment variable requirements (`env`)

Check that environment variables are defined (non-empty).

```yaml
metadata: {"openclaw": {"requires": {"env": ["OPENAI_API_KEY", "DATABASE_URL"]}}}
```

Use cases:
- API keys for external services
- Database connection strings
- Feature flags or configuration values

### Config file requirements (`config`)

Check that configuration files exist in the project directory.

```yaml
metadata: {"openclaw": {"requires": {"config": ["package.json", ".env"]}}}
```

Use cases:
- Project type detection (`package.json` for Node, `Cargo.toml` for Rust)
- Required config files (`.env`, `docker-compose.yml`)

### Primary environment variable (`primaryEnv`)

Highlights the single most important environment variable. Used in setup instructions and error messages.

```yaml
metadata: {"openclaw": {"requires": {"env": ["API_KEY", "API_SECRET"]}, "primaryEnv": "API_KEY"}}
```

## Installer specs

When a required binary is missing, OpenClaw can suggest or run installation commands. Installer specs define how to install each dependency.

### Installer entry fields

Each installer entry is an object with the following fields:

| Field | Type | Required | Purpose |
|---|---|---|---|
| `id` | string | Yes | Unique identifier for this installer entry |
| `kind` | string | Yes | One of `"brew"`, `"node"`, `"go"`, `"download"` |
| `formula` | string | If kind=brew | Homebrew formula name (e.g., `"node"`) |
| `bins` | string[] | No | Binary names this installer provides (for verification after install) |
| `label` | string | No | Human-readable label shown in the UI (e.g., `"Node.js via Homebrew"`) |
| `os` | string[] | No | Platform filter per installer entry. Array of `"darwin"`, `"linux"`, `"win32"`. |
| `url` | string | If kind=download | Download URL. Required when kind is `"download"`. |
| `archive` | string | No | Archive format: `"tar.gz"`, `"tar.bz2"`, or `"zip"` |
| `extract` | boolean | No | Force extraction of the downloaded archive |
| `stripComponents` | integer | No | Number of leading path components to strip during extraction (like `tar --strip-components`) |
| `targetDir` | string | No | Installation directory. Default: `~/.openclaw/tools/<skillKey>` |

### Installer kinds

| Kind | Command | Use for |
|---|---|---|
| `brew` | `brew install <formula>` | macOS packages (requires `formula` field) |
| `node` | `npm install -g <package>` | Node.js CLI tools (respects `skills.install.nodeManager` config) |
| `go` | `go install <package>@latest` | Go binaries |
| `download` | Custom URL-based download | Platform-specific binaries (requires `url` field) |

### Installer example

```json
{
  "openclaw": {
    "requires": { "bins": ["mytool"] },
    "install": [
      {
        "id": "mytool-brew",
        "kind": "brew",
        "formula": "mytool",
        "bins": ["mytool"],
        "label": "mytool via Homebrew",
        "os": ["darwin"]
      },
      {
        "id": "mytool-download",
        "kind": "download",
        "url": "https://example.com/mytool-linux-amd64.tar.gz",
        "archive": "tar.gz",
        "stripComponents": 1,
        "bins": ["mytool"],
        "label": "mytool binary (Linux)",
        "os": ["linux"]
      }
    ]
  }
}
```

### OS filtering

Installer specs and the top-level `openclaw.os` field use the same platform values:

| OS | Value |
|---|---|
| macOS | `darwin` |
| Linux | `linux` |
| Windows | `win32` |

The top-level `openclaw.os` gates the entire skill by platform. Per-installer `os` filters which installer entry is offered on each platform.

## Sandbox considerations

When running in a sandboxed environment (Docker container), required binaries must exist inside the container. OpenClaw provides the `agents.defaults.sandbox.docker.setupCommand` configuration to install dependencies at container startup.

### How it works

1. The skill declares `bins` requirements in metadata
2. If running in sandbox mode, OpenClaw checks the container for those binaries
3. Missing binaries trigger the `setupCommand` if configured
4. The skill only loads after all requirements are met

### Configuring sandbox setup

In the OpenClaw agent configuration:

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "setupCommand": "apt-get update && apt-get install -y curl jq"
        }
      }
    }
  }
}
```

### Best practices for sandbox

- Keep `setupCommand` minimal — only install what's actually needed
- Use the skill's `bins` requirement to document what the setup command must provide
- Test the skill in both sandboxed and non-sandboxed environments
- If your skill needs many binaries, consider providing a custom Docker image instead

## Complete examples

### Skill requiring Node.js and an API key

```yaml
---
name: deploy-vercel
description: Use skill if you are deploying a project to Vercel, managing deployments, or configuring Vercel project settings. Trigger phrases include "vercel deploy", "deploy to vercel", "vercel project".
metadata: {"openclaw": {"requires": {"bins": ["node", "npx"], "env": ["VERCEL_TOKEN"]}, "primaryEnv": "VERCEL_TOKEN"}}
---
```

### Skill requiring Docker and a config file

```yaml
---
name: run-local-stack
description: Use skill if you are starting, stopping, or managing the local development stack with Docker Compose. Trigger phrases include "local stack", "docker compose", "dev environment".
metadata: {"openclaw": {"requires": {"bins": ["docker", "docker-compose"], "config": ["docker-compose.yml"]}}}
---
```

### Skill with no external requirements

```yaml
---
name: write-tests
description: Use skill if you are writing unit tests, integration tests, or test utilities for an existing codebase. Trigger phrases include "write tests", "add tests", "test coverage".
---
```

No `metadata` field needed — the skill works with built-in agent capabilities only.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Multi-line YAML for metadata | Gating silently fails, skill loads without checks | Use single-line JSON |
| Misspelled binary name in `bins` | Skill never loads even when tool is installed | Test with `which <binary>` |
| Overly strict requirements | Skill excluded from too many users | Only require what's truly needed |
| Missing `primaryEnv` | Setup instructions lack focus | Set it to the most important env var |
| Requiring config files that are generated | Skill won't load until build runs | Require source files, not build artifacts |
| Not testing in sandbox | Works locally, fails in container | Test with `agents.defaults.sandbox.docker` enabled |

## Configuration fields

These settings control skill behavior at the OpenClaw configuration level (not inside frontmatter).

| Config key | Type | Default | Purpose |
|---|---|---|---|
| `skills.install.nodeManager` | string | `"npm"` | Package manager used for `kind: "node"` installers. One of `"npm"`, `"pnpm"`, `"yarn"`, `"bun"`. |
| `skills.entries.<key>.config` | object | — | Arbitrary per-skill configuration. This is an opaque object passed to the skill at runtime; OpenClaw core does not inspect it. |
| `allowBundled` | string[] | — | When present, only the listed bundled skill names are eligible. All other bundled skills are excluded. Omit to allow all bundled skills. |

### Example: overriding per-skill config

```json
{
  "skills": {
    "entries": {
      "deploy-staging": {
        "config": {
          "region": "us-east-1",
          "dryRun": true
        }
      }
    }
  }
}
```

The skill can read these values at runtime. Core passes them through without validation.

### Example: restricting bundled skills

```json
{
  "allowBundled": ["commit", "review-pr", "create-pr"]
}
```

Only the three listed bundled skills are eligible. All others are excluded.

## Error conditions

These conditions cause a skill or installer to be excluded:

| Condition | Result |
|---|---|
| Missing required binary (from `requires.bins`) | Skill excluded at load time |
| In sandbox mode, required binary missing inside container | Skill excluded (binary must also exist inside the container) |
| Missing required env var and no `skills.entries` override | Skill excluded |
| Missing required config path | Skill excluded |
| Invalid installer spec (e.g., `kind: "download"` without `url`) | That installer entry is ignored |
| Skill folder realpath escapes configured root | Skill silently ignored for security |

## Security: realpath escaping

If a skill folder's resolved realpath escapes the configured skills root directory (e.g., through symlinks pointing outside), the skill is silently ignored. This prevents directory traversal attacks.

## Debugging gating issues

When a skill doesn't appear despite being installed:

1. **Check frontmatter syntax** — any YAML error silently hides the skill
2. **Check `bins` requirements** — run `which <binary>` for each required binary
3. **Check `env` requirements** — run `echo $VAR_NAME` for each required env var
4. **Check `config` requirements** — verify files exist in the project root
5. **Check JSON format** — ensure metadata is single-line, valid JSON
6. **Check the skills watcher** — save SKILL.md to trigger a reload
