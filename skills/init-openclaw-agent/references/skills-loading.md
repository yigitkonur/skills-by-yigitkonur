# Skills Loading Configuration

OpenClaw agents load skills from multiple sources with a fixed precedence order. Understanding this order and the loading configuration is essential for predictable agent behavior.

## Skill precedence

Skills are resolved in this order. The first match wins:

```
1. workspace skills     (highest priority)
2. managed/local skills
3. bundled skills
4. extra dirs skills    (lowest priority)
```

This means:
- A workspace skill with the same name as a bundled skill will shadow the bundled one
- You cannot override a workspace skill from extra dirs
- If you need to override a bundled skill, place your version in the workspace

### Precedence implications

| Scenario | What happens |
|----------|-------------|
| Same skill name in workspace and bundled | Workspace version loads; bundled is ignored |
| Same skill name in managed/local and extra dirs | Managed/local version loads; extra dirs is ignored |
| Skill only in extra dirs | Loads normally (no shadowing) |
| Skill removed from workspace but exists in bundled | Bundled version loads (workspace no longer shadows) |

## Configuration options

### skills.load.extraDirs

Add external directories that contain skills. Each directory is scanned for valid skill folders (directories containing a SKILL.md file).

```yaml
skills:
  load:
    extraDirs:
      - /home/user/my-custom-skills
      - /opt/team-skills
      - ./relative/path/to/skills    # Relative to workspace root
```

**Rules:**
- Paths can be absolute or relative to the workspace root
- Each directory is scanned non-recursively for immediate child directories containing SKILL.md
- Invalid paths are silently skipped (no error, skill just will not load)
- Duplicate skill names across extra dirs are resolved by directory order (first listed wins)

### skills.entries

Per-skill configuration for environment variables, API keys, and other settings.

```yaml
skills:
  entries:
    my-skill:
      env:
        DATABASE_URL: "postgres://localhost:5432/mydb"
        LOG_LEVEL: "debug"
      apiKey: "sk-..."
    another-skill:
      env:
        REGION: "us-east-1"
```

**The key in `skills.entries` must match the skill's directory name** (which must match the `name` field in its SKILL.md frontmatter).

#### env

Key-value pairs injected as environment variables when the skill is loaded. Use for:
- Database connection strings
- Service endpoints
- Feature flags
- Log levels

#### apiKey

A dedicated field for API keys. Functionally equivalent to putting the key in `env`, but signals intent clearly and may be handled differently by secret management systems.

**Security note:** Prefer environment variables or secret management over hardcoding values in config files. If the config file is version-controlled, API keys in plaintext are a security risk.

### watchDebounceMs

Controls how quickly the skill watcher reacts to file changes.

```yaml
skills:
  watchDebounceMs: 1000    # Wait 1 second after last change before reloading
```

**Default:** Varies by runtime. Typically 300-500ms.

**When to adjust:**
- **Increase (1000-2000ms):** During active skill development when rapid file saves cause reload storms
- **Decrease (100-200ms):** When you need skills to reload nearly instantly (e.g., automated testing pipelines)
- **Leave default:** For production deployments where skills change infrequently

## Skill directory structure

A valid skill directory must contain at minimum a SKILL.md file:

```
my-skill/
+-- SKILL.md              # Required: skill definition with frontmatter
+-- references/            # Optional: reference files routed from SKILL.md
|   +-- guide.md
|   +-- patterns.md
+-- scripts/               # Optional: automation scripts
|   +-- validate.sh
+-- evals/                 # Optional: evaluation definitions
    +-- evals.json
```

The skill name is determined by:
1. The `name` field in SKILL.md frontmatter (authoritative)
2. The directory name (must match the `name` field)

## Skill loading workflow

When the OpenClaw runtime starts or the watcher detects changes:

1. Scan workspace skill directories
2. Scan managed/local skill directories
3. Scan bundled skill directories
4. Scan each path in `skills.load.extraDirs` (in order)
5. For each skill found, check if a higher-precedence skill with the same name already loaded
6. If no conflict, load the skill and apply any `skills.entries` configuration
7. Inject env vars and apiKey from the matching `skills.entries` entry

## Common patterns

### Team-shared skills

Place shared skills in a central directory and reference from each agent's config:

```yaml
skills:
  load:
    extraDirs:
      - /opt/team-skills    # Shared across all agents
```

This lets you update team skills in one place without modifying individual agent workspaces.

### Development vs production

Use different extra dirs for different environments:

```yaml
# Development config
skills:
  load:
    extraDirs:
      - ./skills-dev       # Local development skills
      - /opt/team-skills   # Team shared skills
  watchDebounceMs: 500     # Fast reload during development

# Production config
skills:
  load:
    extraDirs:
      - /opt/team-skills   # Team shared skills only
  watchDebounceMs: 5000    # Infrequent reloads in production
```

### Skill environment isolation

Different skills may need different configurations of the same service:

```yaml
skills:
  entries:
    data-fetcher:
      env:
        API_ENDPOINT: "https://api.production.example.com"
        TIMEOUT_MS: "5000"
    data-fetcher-staging:
      env:
        API_ENDPOINT: "https://api.staging.example.com"
        TIMEOUT_MS: "30000"
```

## Troubleshooting skill loading

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Skill not found by agent | Not in any scanned directory, or directory missing SKILL.md | Verify path in extraDirs and presence of SKILL.md |
| Wrong version of skill loads | Higher-precedence copy exists | Check workspace and managed/local for shadowing copies |
| Skill loads but env vars missing | `skills.entries` key does not match skill name | Verify the key matches the `name` in SKILL.md frontmatter exactly |
| Skill reloads too frequently | watchDebounceMs too low during active development | Increase to 1000-2000ms |
| Skill does not reload after changes | watchDebounceMs too high, or watcher not running | Decrease debounce or restart the runtime |
| Extra dir skills not loading | Path is invalid or has no valid skill subdirectories | Check that the path exists and contains directories with SKILL.md |

## Validation checklist

- [ ] All extraDirs paths are valid and accessible
- [ ] No unintended shadowing between precedence levels
- [ ] Every skill that needs env vars has a matching `skills.entries` key
- [ ] API keys are not hardcoded in version-controlled config files
- [ ] watchDebounceMs is appropriate for the deployment context
- [ ] Skill names match between directory names and SKILL.md frontmatter
