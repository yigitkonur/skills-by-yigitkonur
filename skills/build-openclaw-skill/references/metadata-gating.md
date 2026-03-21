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
    "requires": {
      "bins": ["binary1", "binary2"],
      "env": ["ENV_VAR_1", "ENV_VAR_2"],
      "config": ["config-file.json"]
    },
    "primaryEnv": "ENV_VAR_1"
  }
}
```

| Key | Type | Purpose |
|---|---|---|
| `openclaw` | object | Top-level namespace for OpenClaw-specific metadata |
| `requires` | object | Environment requirements that must be met |
| `requires.bins` | string[] | Binary executables that must exist in PATH |
| `requires.env` | string[] | Environment variables that must be set |
| `requires.config` | string[] | Config files that must exist in the project |
| `primaryEnv` | string | The most important env var (shown in setup instructions) |

## Requirement types

### Binary requirements (`bins`)

Check that executables exist in the system PATH.

```yaml
metadata: {"openclaw": {"requires": {"bins": ["docker", "docker-compose"]}}}
```

Use cases:
- CLI tools the skill's workflow depends on (`node`, `python`, `go`, `cargo`)
- Runtime dependencies (`docker`, `kubectl`, `terraform`)
- Build tools (`make`, `cmake`, `gcc`)

The agent checks `which <binary>` or equivalent before offering the skill.

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

### Installer types

| Type | Command | Use for |
|---|---|---|
| `brew` | `brew install <package>` | macOS packages |
| `node` | `npm install -g <package>` | Node.js CLI tools |
| `go` | `go install <package>@latest` | Go binaries |
| `download` | Custom URL-based download | Platform-specific binaries |

### Installer spec format

Installer specs are defined alongside the metadata, typically in the skill's documentation or setup instructions:

```
Required: node (>= 18.0.0)
  Install: brew install node
  Install (alternative): download from https://nodejs.org

Required: openclaw-cli
  Install: npm install -g @openclaw/cli
```

### OS filtering

Installer specs can be filtered by operating system:

| OS | Value |
|---|---|
| macOS | `darwin` |
| Linux | `linux` |
| Windows | `win32` |

Example: a dependency only needed on macOS would include `os: darwin` in its installer spec.

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

## Debugging gating issues

When a skill doesn't appear despite being installed:

1. **Check frontmatter syntax** — any YAML error silently hides the skill
2. **Check `bins` requirements** — run `which <binary>` for each required binary
3. **Check `env` requirements** — run `echo $VAR_NAME` for each required env var
4. **Check `config` requirements** — verify files exist in the project root
5. **Check JSON format** — ensure metadata is single-line, valid JSON
6. **Check the skills watcher** — save SKILL.md to trigger a reload
