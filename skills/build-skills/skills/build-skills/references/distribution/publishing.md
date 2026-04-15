# Publishing and Distribution

How to publish skills to the ecosystem, manage versions, and follow community standards.

## Distribution channels

### Channel 1: GitHub repository (primary)

Skills live in GitHub repos. The repo structure determines how they're discovered and installed.

#### Single-skill repository

```
my-skill/
├── SKILL.md
├── references/
│   ├── guide.md
│   └── api-reference.md
├── LICENSE
└── README.md
```

#### Multi-skill repository (skill pack)

```
skills-collection/
├── README.md
├── LICENSE
├── skills/
│   ├── skill-a/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── skill-b/
│   │   ├── SKILL.md
│   │   └── references/
│   └── skill-c/
│       ├── SKILL.md
│       └── references/
```

#### Repo-embedded skills

Skills can live inside application repos:

```
my-app/
├── .claude/
│   └── skills/
│       └── deploy-staging/
│           └── SKILL.md
├── src/
│   └── ...
└── package.json
```

### Channel 2: skills.sh / Playbooks marketplace

The primary discovery platform for Claude skills.

#### How indexing works

1. Skills are submitted via GitHub repo URL
2. The platform searches standard paths for SKILL.md files:
   - `skills/{name}/`, `{name}/`, `.skills/{name}/`
   - `.claude/skills/{name}/`, `.agent/skills/{name}/`
   - `.cursor/skills/{name}/`, `.agents/skills/{name}/`
   - `src/skills/{name}/`
3. Frontmatter is parsed for metadata (name, description)
4. The skill appears in search results

#### Discovery signals

| Signal | Impact | How to optimize |
|---|---|---|
| Description quality | High | Include specific trigger phrases and technology keywords |
| Install count | High | Grow organically through quality |
| Search relevance | Medium | Name and description match common search queries |
| Repo stars | Medium | Good README, solve real problems |
| Author reputation | Low | Multiple published skills signal experience |

### Channel 3: Direct installation

Users can install skills directly from GitHub:

```bash
# Install skill-dl first
sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash
skill-dl --version

# Using skill-dl CLI
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ~/.claude/skills/

# Discover candidate skills before downloading
skill-dl search skill creation research comparison --top 20

# Using git clone
git clone https://github.com/owner/repo.git
cp -r repo/skills/my-skill ~/.claude/skills/

# Using npx (if skill provides an installer)
npx skills install skill-name
```

### Channel 4: Skills API

For programmatic use cases — applications, agents, and automated workflows.

**Key capabilities**:
- `/v1/skills` endpoint for listing and managing skills
- Add skills to Messages API requests via the `container.skills` parameter
- Version control and management through the Claude Console
- Works with the Claude Agent SDK for building custom agents

**When to use API vs. interactive surfaces**:

| Use case | Best surface |
|---|---|
| End users interacting with skills | Claude.ai / Claude Code |
| Manual testing and iteration | Claude.ai / Claude Code |
| Individual, ad-hoc workflows | Claude.ai / Claude Code |
| Applications using skills programmatically | API |
| Production deployments at scale | API |
| Automated pipelines and agent systems | API |

Note: Skills in the API require the Code Execution Tool beta.

**Documentation**:
- [Skills API Quickstart](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/quickstart)
- [Create Custom Skills](https://docs.claude.com/en/api/skills/create-skill)
- [Skills in the Agent SDK](https://docs.claude.com/en/docs/agent-sdk/skills)

### Channel 5: Organization deployment

Admins can deploy skills workspace-wide:
- Automatic updates across the organization
- Centralized management via admin console
- No individual user installation required

### Open standard: AgentSkills.io

Anthropic has published [Agent Skills](https://agentskills.io/home) as an open standard. Skills are designed to be portable across tools and platforms — the same skill should work whether using Claude or other AI platforms. Authors can note platform-specific requirements in the `compatibility` field.

## Publishing checklist

Before publishing a skill:

### Content quality

- [ ] SKILL.md has valid frontmatter with `name` and `description`
- [ ] Description follows the "Use skill if you are..." formula
- [ ] Decision tree routes to all reference files
- [ ] No orphaned reference files
- [ ] All examples are tested and working
- [ ] Pitfalls table covers common mistakes
- [ ] Guardrails prevent agent misuse

### Structural quality

- [ ] Directory name matches frontmatter `name`
- [ ] All files use kebab-case naming
- [ ] Reference files are 100-400 lines each
- [ ] SKILL.md is under 500 lines
- [ ] No binary files or large assets
- [ ] No secrets, credentials, or personal data

### Repository quality

- [ ] LICENSE file exists (Apache-2.0 or MIT recommended)
- [ ] README.md describes the skill(s)
- [ ] .gitignore excludes OS/editor artifacts
- [ ] No node_modules, build artifacts, or temp files
- [ ] Clean git history (no accidental commits)

### Discovery optimization

- [ ] Description contains keywords users would search for
- [ ] Skill name is descriptive and follows naming conventions
- [ ] README includes usage examples
- [ ] Repository topics include relevant tags

## Versioning strategy

### Semantic versioning (SemVer)

```
MAJOR.MINOR.PATCH

1.0.0 → Initial stable release
1.1.0 → New reference files added
1.2.0 → New decision tree branches
2.0.0 → Breaking change: restructured references, renamed files
```

### What counts as a breaking change

| Change | Breaking? | Why |
|---|---|---|
| Adding new reference files | No | Existing workflows unaffected |
| Reorganizing into subdirectories | Yes | File paths change |
| Renaming the skill directory | Yes | Slash command changes |
| Changing frontmatter `name` | Yes | Lookup key changes |
| Updating content in existing files | No | Paths stable |
| Removing reference files | Yes | Skills referencing them break |
| Changing the description | No | But may affect auto-invocation |

### Version tracking options

| Method | Pros | Cons |
|---|---|---|
| Frontmatter `version` field | Visible in SKILL.md | Manual update required |
| Git tags (`v1.0.0`) | Standard, automatable | Requires git workflow |
| Changelog file | Detailed history | Extra maintenance |
| Git commit messages | Zero overhead | Hard to scan for versions |

Recommended: Use frontmatter `version` + git tags for published skills.

## Community standards

### Quality expectations

The skill community values:

1. **Specificity over breadth** — A skill that does one thing well beats one that covers everything poorly
2. **Evidence over opinion** — Claims should be traceable to verified sources
3. **Progressive disclosure** — Load minimal context, expand on demand
4. **Original synthesis** — Distill patterns, don't clone existing skills
5. **Maintenance commitment** — Published skills should stay current

### Content guidelines

| Do | Don't |
|---|---|
| Include working code examples | Include untested examples |
| Cite sources for best practices | Present opinions as facts |
| Version your frontmatter | Ship without version tracking |
| Keep reference files focused | Create monolithic reference dumps |
| Test with the target agent | Assume it works without testing |

### Contribution to skill packs

When contributing to a curated skill pack (multi-skill repository):

1. **Follow the pack's conventions** — naming, structure, style
2. **Read existing skills first** — understand the quality bar
3. **Match the complexity level** — don't over-engineer or under-deliver
4. **Remove all clutter** — no leftover research files, no packaging artifacts
5. **Cross-reference correctly** — use frontmatter `name` for other skills in the pack

## Maintenance practices

### Active maintenance

| Frequency | Action |
|---|---|
| Monthly | Check for outdated API references or deprecated patterns |
| Quarterly | Review install/feedback metrics, update based on user issues |
| On dependency release | Verify examples still work with new versions |
| On user report | Fix confirmed issues within a week |

### Deprecation

When retiring a skill:

1. Add a deprecation notice to SKILL.md
2. Update description to mention the replacement (if any)
3. Keep the skill available for 6 months
4. Archive the repository after the grace period

```yaml
---
name: old-skill
description: "[DEPRECATED] Use new-skill instead. This skill is no longer maintained."
---

# Old Skill (Deprecated)

This skill has been replaced by `new-skill`. Please migrate.
```

### Handling forks and derivatives

When someone else's skill is the basis for yours:

1. Acknowledge the original in your README
2. Don't use the same `name` — it creates conflicts
3. Don't copy wholesale — synthesize and improve
4. Consider contributing improvements back as PRs

## Optimizing for discovery

### Description keywords

Include keywords that match how users think about the problem:

```yaml
# Good — includes natural search terms
description: Use skill if you are building TypeScript applications with the GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools, streaming, hooks, custom agents, or BYOK.

# The keywords here match searches for:
# - "copilot sdk"
# - "typescript copilot"
# - "streaming"
# - "custom agents"
# - "BYOK"
```

### README optimization

Your README is the landing page for human users:

```markdown
# Skill Name

One-line description matching the SKILL.md description.

## What this skill does

2-3 sentences expanding on the description.

## Quick install

\```bash
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ~/.claude/skills/
\```

## What's included

- SKILL.md — main instructions with decision tree
- references/ — X files covering [topics]

## Usage

Invoke with `/skill-name` or let Claude auto-detect from your prompt.

## Contributing

[Link to contribution guidelines]
```
