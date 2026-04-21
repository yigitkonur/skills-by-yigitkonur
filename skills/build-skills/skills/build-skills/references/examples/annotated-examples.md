# Annotated Examples

Real-world examples of well-structured skills with explanations of why they work.

## Example 1: Comprehensive SDK skill

This example shows a Tier 3 skill covering a full SDK. It demonstrates extensive decision tree routing, organized reference subdirectories, and multiple reading sets.

### Structure

```
build-copilot-sdk-app/
├── SKILL.md                              # 343 lines
└── references/
    ├── agents/
    │   ├── cli-extensions.md
    │   ├── custom-agents.md
    │   ├── mcp-servers.md
    │   └── skills-system.md
    ├── auth/
    │   ├── byok-providers.md
    │   ├── environment-variables.md
    │   └── github-oauth.md
    ├── client/
    │   ├── lifecycle-and-health.md
    │   ├── setup-and-options.md
    │   └── transport-modes.md
    ├── events/
    │   ├── agent-events.md
    │   ├── assistant-events.md
    │   ├── hook-events.md
    │   ├── permission-events.md
    │   ├── session-lifecycle-events.md
    │   ├── streaming-patterns.md
    │   ├── system-events.md
    │   ├── tool-events.md
    │   └── user-input-events.md
    ├── hooks/
    │   ├── error-handling-hook.md
    │   ├── post-tool-use.md
    │   ├── pre-tool-use.md
    │   ├── session-lifecycle-hooks.md
    │   └── user-prompt-submitted.md
    ├── patterns/
    │   ├── backend-service.md
    │   ├── fleet-mode.md
    │   ├── multi-client.md
    │   ├── plan-autopilot-mode.md
    │   ├── ralph-loop.md
    │   ├── scaling.md
    │   ├── steering-and-queueing.md
    │   └── workspace-files.md
    ├── permissions/
    │   ├── permission-handler.md
    │   ├── permission-kinds.md
    │   └── user-input-handler.md
    ├── sessions/
    │   ├── create-and-configure.md
    │   ├── infinite-sessions.md
    │   ├── persistence-and-resume.md
    │   └── system-messages.md
    ├── tools/
    │   ├── define-tool-zod.md
    │   ├── json-schema-tools.md
    │   ├── override-builtin-tools.md
    │   └── tool-results-and-errors.md
    └── types/
        ├── client-types.md
        ├── event-types.md
        ├── hook-types.md
        ├── rpc-methods.md
        ├── session-types.md
        └── tool-types.md
```

### Why it works

| Pattern | Implementation | Effect |
|---|---|---|
| **Decision tree** | 80+ leaf nodes organized by 10 top-level categories | Agent finds the right reference in one scan |
| **Quick start** | 3 progressive examples (basic, streaming, custom tool) | Covers 80% of initial use cases |
| **Key patterns** | 7 essential patterns with TypeScript examples | Demonstrates canonical usage |
| **Pitfalls table** | 10 entries with specific fixes | Prevents the most common mistakes |
| **Reading sets** | 7 named scenarios with 3-6 files each | Bundles related references for common tasks |
| **Reference organization** | 10 subdirectories matching tree categories | Predictable file locations |
| **Final reminder** | Explicit instruction to load minimally | Prevents context budget blowout |

### Key annotations

**Frontmatter** — note how the description includes technology keywords AND use cases:
```yaml
description: Use skill if you are building TypeScript applications with the GitHub
  Copilot SDK (@github/copilot-sdk), including sessions, tools, streaming, hooks,
  custom agents, or BYOK.
```

**Decision tree depth** — exactly 3 levels (category → task → file). Never deeper:
```
├── Custom tools
│   ├── defineTool with Zod ───────────► references/tools/define-tool-zod.md
│   ├── JSON Schema tools ────────────► references/tools/json-schema-tools.md
│   ├── Tool results & errors ────────► references/tools/tool-results-and-errors.md
│   └── Override built-in tools ──────► references/tools/override-builtin-tools.md
```

**Reading sets** — named with user intent, not technical categories:
```markdown
### "I need a basic app with custom tools"
- references/client/setup-and-options.md
- references/tools/define-tool-zod.md
- references/permissions/permission-handler.md
- references/events/streaming-patterns.md
```

## Example 2: Process-oriented skill

This example shows a skill that guides a multi-step workflow rather than documenting an API.

### Structure

```
build-skills/
├── SKILL.md                              # ~300 lines
└── references/
    ├── authoring/
    │   ├── skillmd-format.md
    │   ├── decision-tree-patterns.md
    │   └── reference-file-structure.md
    ├── patterns/
    │   ├── skill-organization.md
    │   └── naming-conventions.md
    ├── research/
    │   ├── fact-checking.md
    │   └── source-verification.md
    ├── distribution/
    │   └── publishing.md
    ├── examples/
    │   ├── annotated-examples.md
    │   └── anti-patterns.md
    ├── research-workflow.md
    ├── remote-sources.md
    ├── comparison-workflow.md
    ├── source-patterns.md
    └── skill-research.sh
```

### Why it works

| Pattern | Implementation | Effect |
|---|---|---|
| **Phase-based routing** | Research → Compare → Synthesize → Ship | Matches natural workflow |
| **Existing + new references** | Keeps proven workflow files, adds structured subdirs | Backward compatible |
| **Examples as references** | Annotated real skills, not hypothetical ones | Concrete, verifiable |
| **Anti-patterns file** | Dedicated file for what NOT to do | Prevents common mistakes explicitly |

## Example 3: Minimal effective skill

Not every skill needs 30 reference files. Here's a well-structured micro-skill.

### Structure

```
init-agent-config/
├── SKILL.md                              # 120 lines
└── references/
    ├── claudemd-format.md
    └── agentsmd-format.md
```

### SKILL.md outline

```yaml
---
name: init-agent-config
description: Use skill if you are creating or reviewing CLAUDE.md and AGENTS.md
  files that configure AI coding agents for your project.
---

# Init Agent Config

## Decision tree

  What do you need?
  ├── Create CLAUDE.md ───────► references/claudemd-format.md
  ├── Create AGENTS.md ──────► references/agentsmd-format.md
  └── Audit existing config ─► Both files + checklist below

## Quick start

[15 lines — minimal CLAUDE.md template]

## Audit checklist

[20 lines — validation steps]

## Guardrails

[5 lines — constraints]
```

### Why it works

| Pattern | Implementation | Effect |
|---|---|---|
| **Two reference files** | One per config format | Right-sized for the topic |
| **Simple 3-branch tree** | Create A, Create B, Audit both | No over-engineering |
| **Inline quick start** | Template directly in SKILL.md | No file loading for the common case |
| **Focused description** | Exactly what it does + when | Clean auto-invocation |

## Example 4: Effective description patterns

Descriptions are the most impactful single element. Here are real descriptions that work well:

### Technology + use cases pattern

```yaml
description: Use skill if you are building TypeScript applications with the
  GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools,
  streaming, hooks, custom agents, or BYOK.
```
Why: Lists the technology AND specific use cases (sessions, tools, streaming...).

### Workflow + outcome pattern

```yaml
description: Use skill if you are reviewing a GitHub pull request with a
  systematic, evidence-based workflow that clusters files, correlates existing
  comments, validates goals, and produces actionable findings.
```
Why: Describes the workflow AND the expected outcome.

### Action + prerequisite pattern

```yaml
description: Use skill if you are creating or redesigning a Claude skill and
  need workspace-first evidence, remote skill research, and comparison
  before drafting.
```
Why: States the action AND what preparation is needed.

## Structural patterns to replicate

### Pattern: Pitfalls table

Always use a table, not prose. Include the fix, not just the problem.

```markdown
## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Missing `onPermissionRequest` | Required on every session. Use `approveAll` for unattended. |
| `sendAndWait` timeout | Default 60s. Pass explicit: `sendAndWait(opts, 300_000)`. |
| Streaming events not arriving | Set `streaming: true` in SessionConfig. |
```

### Pattern: Minimal reading sets

Name sets with user intent in quotes. Include 3-6 files per set.

```markdown
## Minimal reading sets

### "I need a basic app with custom tools"
- `references/client/setup-and-options.md`
- `references/tools/define-tool-zod.md`
- `references/permissions/permission-handler.md`
```

### Pattern: Final reminder

End SKILL.md with an explicit loading instruction:

```markdown
## Final reminder

This skill is split into many small, atomic reference files organized by
domain. Do not load everything at once. Start with the smallest relevant
reading set above, then expand into neighboring references only when the
task actually requires them.
```

### Pattern: Guardrails

Use bullet points with "Do not" prefix:

```markdown
## Guardrails

- Do not draft the final skill before reading the current workspace.
- Do not claim research happened unless the comparison table appears inline in output.
- Do not compare sources mentally and hide the table.
- Do not copy a source skill wholesale.
```

## Example 5: MCP-enhanced skill (Category 3)

This example shows a skill that enhances an MCP server with workflow expertise.

### Structure (conceptual)

```
sentry-code-review/
├── SKILL.md                              # ~200 lines
└── references/
    ├── error-analysis.md
    ├── pr-workflow.md
    └── troubleshooting.md
```

### Description

```yaml
description: Automatically analyzes and fixes detected bugs in GitHub Pull
  Requests using Sentry's error monitoring data via their MCP server.
```

### Why it works

| Pattern | Implementation | Effect |
|---|---|---|
| **MCP + expertise** | Coordinates Sentry MCP calls with code analysis | Goes beyond raw tool access |
| **Sequential workflow** | Fetch errors → analyze → suggest fixes → create PR | Clear, predictable process |
| **Domain intelligence** | Embeds error triage knowledge | Adds value MCP alone can't |
| **Error handling** | Handles Sentry API failures gracefully | Robust in production |

### Key takeaway

The skill doesn't just call the MCP — it knows *how* to interpret Sentry errors and *what* constitutes a good fix. This is the "recipes on top of the kitchen" pattern.

## Example 6: Document creation skill (Category 1)

This example shows a standalone skill that creates output using only Claude's built-in capabilities.

### Structure (conceptual)

```
frontend-design/
├── SKILL.md                              # ~300 lines
└── references/
    ├── design-principles.md
    ├── component-library.md
    ├── responsive-patterns.md
    └── accessibility.md
```

### Description

```yaml
description: Create distinctive, production-grade frontend interfaces with
  high design quality. Use when building web components, pages, artifacts,
  posters, or applications.
```

### Why it works

| Pattern | Implementation | Effect |
|---|---|---|
| **No MCP needed** | Uses Claude's built-in code execution | Works for any user instantly |
| **Embedded style guide** | Design principles baked into instructions | Consistent visual quality |
| **Quality checklist** | Validation steps before finalizing | Prevents common design mistakes |
| **Progressive disclosure** | Core patterns in SKILL.md, detail in references | Fast loading, deep when needed |

### Key takeaway

Not every skill needs MCP. Category 1 skills add value through embedded expertise and consistent methodology, using only Claude's built-in capabilities.

## Sizing reference

| Skill type | SKILL.md lines | Reference files | Total files |
|---|---|---|---|
| Micro-skill | 50-120 | 1-3 | 2-4 |
| Standard skill | 150-250 | 4-8 | 5-10 |
| Comprehensive skill | 250-400 | 10-40 | 12-45 |
| This skill (build-skills) | ~310 | 27 | 29 |
| Model skill (copilot-sdk) | ~340 | 40+ | 45+ |
