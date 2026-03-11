# Naming Conventions

Standards for naming skills, directories, files, and frontmatter fields.

## Skill directory naming

The directory name is the skill's primary identifier. It becomes the `/slash-command` in Claude Code and the lookup key in discovery tools.

### Rules

| Rule | Example | Why |
|---|---|---|
| Kebab-case only | `build-copilot-sdk-app` | Consistent, URL-safe, command-line friendly |
| Lowercase letters and numbers | `review-pr` | Case sensitivity varies across platforms |
| Hyphens as separators | `create-component` | Underscores and spaces are non-standard |
| No leading/trailing hyphens | `my-skill` not `-my-skill-` | Breaks parsing in some systems |
| No consecutive hyphens | `my-skill` not `my--skill` | Ambiguous in URLs and CLIs |
| Max 64 characters | Most names fit in 20-40 | Keeps tree output and menus readable |
| Descriptive verb-noun pattern | `build-mcp-server` | Tells the agent what action + what target |

### Naming patterns by skill type

| Skill type | Pattern | Examples |
|---|---|---|
| Builder/creator | `build-{thing}` or `create-{thing}` | `build-mcp-server`, `create-component` |
| Reviewer/analyzer | `review-{thing}` | `review-pr`, `review-security` |
| Runner/executor | `run-{thing}` | `run-playwright`, `run-tests` |
| Initializer | `init-{thing}` | `init-project`, `init-config` |
| Converter | `convert-{source}-{target}` | `convert-snapshot-nextjs` |
| Research/exploration | `research-{topic}` | `research-powerpack` |
| Debugging | `debug-{tool}` | `debug-tauri-devtools` |

### Common naming mistakes

| Mistake | Problem | Better |
|---|---|---|
| `skill` or `my-skill` | Not descriptive | `build-react-app` |
| `typescript` | Too broad — what does it do? | `develop-typescript` |
| `v2-new-auth-handler` | Version in name | `handle-auth` |
| `SKILL` (uppercase dir) | Case-sensitive platforms fail | `skill` (lowercase) |
| `build_mcp_server` | Underscores non-standard | `build-mcp-server` |
| `buildMcpServer` | CamelCase breaks conventions | `build-mcp-server` |
| `claude-helper` | "claude" prefix is reserved by Anthropic | `ai-helper` |
| `anthropic-tools` | "anthropic" prefix is reserved by Anthropic | `agent-tools` |

## Reserved names

Anthropic reserves skill names containing "claude" or "anthropic" as a prefix. Skills with these names will be rejected during upload.

```yaml
# Forbidden
name: claude-code-helper
name: anthropic-review

# Acceptable
name: code-review-helper
name: agent-review-tool
```

## Frontmatter `name` field

The `name` in frontmatter usually matches the directory name. When it differs, the frontmatter `name` takes precedence for the slash command.

```yaml
---
name: build-skills          # This becomes /build-skills
description: Use skill if...
---
```

### When name ≠ directory name

Acceptable when:
- The directory name is scoped (e.g., `skills/build-skills/` → name: `build-skills`)
- The repo organizes skills under a prefix the skill shouldn't inherit

Never:
- Use spaces or special characters in the `name` field
- Change the name after publication without a deprecation notice

## Frontmatter `description` field

### Formula

```
Use skill if you are [doing what action] and need [what outcome] [optional: before/after/including what].
```

### Checklist

- [ ] Starts with "Use skill if you are"
- [ ] States the action (building, reviewing, deploying, etc.)
- [ ] States the outcome or context
- [ ] Includes technology keywords users would naturally say
- [ ] Under 1024 characters
- [ ] No angle brackets (`<`, `>`)
- [ ] Specific enough to avoid false triggers
- [ ] Broad enough to catch relevant queries

### Examples ranked by quality

**Excellent** — specific action, clear trigger, technology keywords:
```yaml
description: Use skill if you are building TypeScript applications with the GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools, streaming, hooks, custom agents, or BYOK.
```

**Good** — clear action and outcome:
```yaml
description: Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based workflow that clusters files, correlates existing comments, validates goals, and produces actionable findings.
```

**Adequate** — functional but could be more specific:
```yaml
description: Use skill if you are setting up automated npm publishing via GitHub Actions.
```

**Poor** — too vague, no trigger phrases:
```yaml
description: Helps with TypeScript projects.
```

**Bad** — angle brackets inject instructions:
```yaml
description: Use skill to <generate> components with <proper typing>.
```

## Reference file naming

### File naming rules

| Rule | Example | Why |
|---|---|---|
| Kebab-case | `streaming-patterns.md` | Consistent with directory naming |
| Descriptive of content | `define-tool-zod.md` | Self-documenting in tree output |
| Max 50 characters | Keep it concise | Readable in `tree` and `ls` output |
| `.md` extension | Always markdown | Agents know how to parse markdown |
| No version suffix | `auth.md` not `auth-v2.md` | One current version per topic |
| No redundant prefix | `oauth.md` not `auth-oauth.md` | Parent directory provides context |

### Naming by content type

| Content type | Pattern | Examples |
|---|---|---|
| How-to guide | `{verb}-{noun}.md` | `setup-oauth.md`, `create-session.md` |
| Concept explanation | `{noun}.md` or `{noun}-{qualifier}.md` | `architecture.md`, `token-lifecycle.md` |
| Reference/lookup | `{noun}-types.md` or `{noun}-reference.md` | `event-types.md`, `rpc-methods.md` |
| Pattern collection | `{noun}-patterns.md` | `streaming-patterns.md`, `error-patterns.md` |
| Troubleshooting | `{noun}-errors.md` or `troubleshooting.md` | `build-errors.md`, `auth-errors.md` |

## Reference subdirectory naming

Match subdirectory names to decision tree top-level branches.

```
Decision tree branch:        Subdirectory:
├── Sessions                 references/sessions/
├── Custom tools             references/tools/
├── Events                   references/events/
├── Auth & BYOK              references/auth/
└── Type reference           references/types/
```

### Subdirectory naming rules

| Rule | Example | Why |
|---|---|---|
| Plural nouns | `events/` not `event/` | Matches natural language |
| Short (1-2 words) | `auth/` not `authentication-and-authorization/` | Keeps paths readable |
| Domain concepts | `hooks/`, `patterns/` | Maps to how users think |

## Cross-skill references

When one skill mentions another (in description or body):

```markdown
For MCP server setup, see the `build-mcp-sdk-server` skill.
```

Always use the target skill's `name` field, not its directory path. The agent resolves the name to the correct location.

## Canonical naming audit

Before shipping, verify naming consistency across all artifacts:

| Artifact | Should match |
|---|---|
| Directory name | Kebab-case, verb-noun |
| Frontmatter `name` | Directory name (usually identical) |
| SKILL.md `# Title` | Human-readable version of the name |
| README label (if in a pack) | Same as frontmatter `name` |
| Cross-skill references | Frontmatter `name` of the target |

### Audit command

```bash
# Check for naming inconsistencies
skill_dir="my-skill"
echo "Directory: $skill_dir"
grep '^name:' "$skill_dir/SKILL.md" | head -1
grep '^# ' "$skill_dir/SKILL.md" | head -1
```
