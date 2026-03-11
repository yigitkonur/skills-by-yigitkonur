# MCP Enhancement Patterns

How to design skills that enhance MCP server integrations, turning raw tool access into reliable workflows.

## The kitchen analogy

**MCP** provides the professional kitchen: access to tools, data, and operations across external services.

**Skills** provide the recipes: step-by-step instructions on how to create something valuable using those tools.

Together, they enable users to accomplish complex tasks without figuring out every step themselves.

## Why MCP alone is not enough

| Without skills | With skills |
|---|---|
| Users connect MCP but don't know what to do next | Pre-built workflows activate automatically |
| Support tickets: "how do I do X?" | Consistent, reliable tool usage |
| Each conversation starts from scratch | Best practices embedded in every interaction |
| Inconsistent results across users | Lower learning curve for the integration |
| Users blame the connector for workflow gaps | Clear separation of access vs. expertise |

## Designing a skill for an existing MCP

### Step 1: Identify the top 3 workflows

Before writing anything, list the 2-3 most common things users do with the MCP server. These become your skill's core workflows.

```
Example: Linear MCP
1. Sprint planning (most common)
2. Bug triage and assignment
3. Project status reporting
```

### Step 2: Map each workflow to MCP calls

For each workflow, list the MCP tools needed and their sequence:

```
Sprint Planning Workflow:
1. list_projects → get project ID
2. get_team_members → check capacity
3. list_issues → find unassigned work
4. create_issue → create sprint tasks
5. update_issue → assign and label tasks
```

### Step 3: Embed domain expertise

The skill should know things the MCP doesn't:

- **Business rules**: "Tasks over 8 story points should be split"
- **Best practices**: "Always assign a reviewer before moving to In Review"
- **Conventions**: "Use the format `[TEAM]-NNN: Description` for task titles"
- **Error prevention**: "Check for duplicate tasks before creating new ones"

### Step 4: Add error handling for MCP failures

MCP calls can fail. The skill should handle common failures:

```markdown
### Error Handling

If `list_projects` returns empty:
- Ask user to verify the Linear workspace URL
- Check if API key has project read permissions

If `create_issue` fails with 403:
- API key may lack write permissions
- Ask user to verify token scopes in Linear settings

If connection times out:
- Verify MCP server is running (Settings > Extensions)
- Try reconnecting: Settings > Extensions > Linear > Reconnect
```

## Multi-MCP coordination

When a workflow spans multiple services, coordinate MCP calls carefully.

### Data flow between MCPs

Each MCP call produces output that may feed into the next:

```
Phase 1: Figma MCP → export design specs → capture asset URLs
Phase 2: Drive MCP → upload assets → capture shareable links
Phase 3: Linear MCP → create tasks → attach asset links
Phase 4: Slack MCP → post summary → include all links
```

### Coordination rules

| Rule | Why |
|---|---|
| Validate output before passing to next MCP | Prevents cascade failures |
| Capture IDs and URLs from each phase | Needed for linking across services |
| Handle partial completion | What if Phase 2 succeeds but Phase 3 fails? |
| Log the full chain | Debugging requires end-to-end visibility |

### Error recovery in multi-MCP workflows

```markdown
### Recovery Strategy

If any phase fails:
1. Stop the workflow — do not proceed to next phase
2. Report which phase failed and why
3. Show what completed successfully
4. Offer options:
   - Retry the failed phase
   - Skip and continue (if the phase is optional)
   - Rollback completed phases (if destructive)
```

## Testing MCP-enhanced skills

### Independent MCP test

Before testing the skill, verify the MCP works alone:

```
"Use [Service] MCP to fetch my projects"
```

If this fails, the issue is the MCP connection, not the skill.

### Skill + MCP integration test

Then test the skill workflow:

```
"Help me plan the next sprint" (should trigger skill + call MCP)
```

### What to verify

| Test | Expected |
|---|---|
| MCP connected | Settings shows "Connected" |
| Tool names match | Skill references correct MCP tool names |
| Auth valid | API keys not expired, correct scopes |
| Data flows | Output from one call feeds correctly into next |
| Error messages | Skill shows helpful errors, not raw MCP errors |

## MCP-specific description patterns

When writing descriptions for MCP-enhanced skills, mention the service name and common workflows:

```yaml
# Good — names the service AND workflows
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".

# Good — names multiple MCPs
description: Design-to-development handoff workflow. Exports from Figma,
  stores in Google Drive, creates tasks in Linear, and notifies via Slack.
  Use when user says "handoff", "design specs", or "developer handoff".
```

## When to embed MCP knowledge vs. generic workflow

| Embed MCP knowledge when | Keep generic workflow when |
|---|---|
| Tool names and parameters are stable | MCP server is in early development |
| Users always use the same service | Users might swap services |
| Error handling is service-specific | Generic error patterns apply |
| Best practices are service-specific | Domain expertise is universal |

## Skill-level architecture decisions

### Single-MCP skill

```
skill-name/
├── SKILL.md          # Workflow + MCP tool usage
└── references/
    ├── api-guide.md   # MCP tool reference
    └── errors.md      # Service-specific errors
```

### Multi-MCP skill

```
skill-name/
├── SKILL.md          # Orchestration workflow
└── references/
    ├── phase-1-figma.md
    ├── phase-2-drive.md
    ├── phase-3-linear.md
    └── troubleshooting.md
```

### MCP + standalone hybrid

```
skill-name/
├── SKILL.md          # Core workflow (works without MCP)
└── references/
    ├── standalone.md  # Built-in tool workflow
    └── with-mcp.md    # Enhanced MCP workflow
```

## Common MCP skill anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Hardcoded tool names without verification | MCP tools may be renamed | Reference tool names from docs |
| No connection check before calling MCP | Raw error messages confuse users | Add "verify MCP connected" step |
| Assuming auth never expires | Token expiry causes silent failures | Add auth verification step |
| Ignoring rate limits | Bulk operations hit API limits | Add pagination and throttling guidance |
| No fallback for MCP-down scenarios | Skill is useless without MCP | Provide manual alternative steps |
