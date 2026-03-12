# Feedback Signals and Iteration

How to interpret user behavior, fix triggering problems, and evolve a skill after deployment.

## Skills are living documents

A shipped skill is not finished. It needs iteration based on real-world usage signals. The best skills go through 3-5 revision cycles before stabilizing.

## Signal category 1: Under-triggering

The skill exists but Claude doesn't load it when it should.

### Symptoms

| Signal | What it means |
|---|---|
| Users manually invoke with `/skill-name` | Description doesn't match user language |
| Users ask "how do I use X?" | Skill existence is unclear |
| Skill loads on direct request only | Missing trigger phrases |
| Users re-explain the workflow each time | Skill fails to auto-activate |

### Diagnosis

Ask Claude: "When would you use the [skill-name] skill?"

Compare Claude's answer to your intended trigger scenarios. The gap reveals what's missing from the description.

### Fixes

| Fix | When to apply |
|---|---|
| Add more trigger phrases to description | Users phrase requests differently than expected |
| Add technology keywords | Users mention tool/framework names |
| Add action verbs | Users say "create", "set up", "plan" |
| Broaden the "when to use" section | Skill scope is wider than description suggests |
| Add file type mentions | Users work with specific formats |

### Example fix

```yaml
# Before — under-triggers
description: Manages project workflows in Linear.

# After — better trigger coverage
description: Manages Linear project workflows including sprint planning,
  task creation, bug triage, and status tracking. Use when user mentions
  "sprint", "Linear tasks", "project planning", "create tickets",
  or "bug triage".
```

## Signal category 2: Over-triggering

The skill loads when it shouldn't, interfering with other tasks.

### Symptoms

| Signal | What it means |
|---|---|
| Skill loads for unrelated queries | Description too broad |
| Users disable the skill | It interferes with other work |
| Confusion about skill purpose | Scope is unclear |
| Conflicts with other skills | Overlapping trigger phrases |

### Diagnosis

Run 10 unrelated queries and check if the skill loads. If it fires on more than 1, the description is too broad.

### Fixes

| Fix | When to apply |
|---|---|
| Add negative triggers | Skill overlaps with another skill |
| Narrow the scope | Generic keywords cause false positives |
| Remove broad terms | "data", "project", "file" are too generic alone |
| Clarify the context | Add domain/service name to narrow scope |

### Example fix

```yaml
# Before — over-triggers on any "data" query
description: Processes data files for analysis.

# After — scoped with negative triggers
description: Advanced statistical analysis for CSV files including
  regression, clustering, and hypothesis testing. Use for statistical
  modeling. Do NOT use for simple data exploration or visualization
  (use data-viz skill instead).
```

### Negative trigger patterns

```yaml
# Redirect to another skill
"Do NOT use for X (use [other-skill] instead)."

# Exclude by scope
"Not for general financial queries — only PayFlow transactions."

# Exclude by file type
"Only for CSV and TSV files, not JSON or XML."

# Exclude by action
"Not for reading or exploring data — only for statistical analysis."
```

## Signal category 3: Execution issues

The skill triggers correctly but produces bad results.

### Symptoms

| Signal | What it means |
|---|---|
| Inconsistent results across runs | Instructions are ambiguous |
| Users correct Claude mid-workflow | Steps are unclear or wrong |
| API/MCP calls fail | Tool names, parameters, or auth are wrong |
| Output format varies | No format specification in instructions |
| Skill skips steps | Instructions are too verbose or buried |

### Fixes by root cause

| Root cause | Fix |
|---|---|
| Ambiguous instructions | Replace "validate properly" with specific checks |
| Buried critical steps | Move critical instructions to the top |
| Too many rules | Keep ≤7 in SKILL.md, move rest to references |
| No examples | Add at least one complete input/output example |
| No error handling | Add explicit failure recovery steps |
| Model laziness | Use validation scripts instead of prose instructions |
| Wrong tool names | Verify against MCP server documentation |

## Iteration strategy

### Version 0.1 → 0.5: Fix triggering

Focus entirely on the description field until the skill triggers correctly on 90%+ of relevant queries and 0% of unrelated queries.

### Version 0.5 → 1.0: Fix execution

Iterate on the instructions until the workflow completes without user correction in 3+ consecutive runs.

### Version 1.0 → 1.x: Expand coverage

Add reference files for edge cases, advanced workflows, and troubleshooting. Reorganize into subdirectories if file count exceeds 6.

### Version 2.0: Major restructure

Rethink the decision tree. Split the skill if workflows have diverged. Rebuild the description from scratch if the skill's scope has shifted.

## When to revise what

| Problem | Revise |
|---|---|
| Wrong trigger behavior | `description` in frontmatter |
| Wrong workflow steps | Body instructions in SKILL.md |
| Missing edge case handling | Add/update reference files |
| Wrong tool calls | Verify MCP docs, update instructions |
| Structural confusion | Decision tree or reference routing |
| Scope creep | Consider splitting the skill |

## Feedback collection

### Active collection

- Ask beta users: "Did the skill trigger when you expected?"
- Ask beta users: "Did you need to correct Claude at any point?"
- Ask beta users: "What was missing from the output?"

### Passive signals

- Monitor for `/skill-name` manual invocations (under-triggering)
- Monitor for skill disabling (over-triggering)
- Track MCP error rates during skill execution
- Count user clarification messages per workflow

## Maintenance schedule

| Frequency | Action |
|---|---|
| After each use (early) | Note what worked and what didn't |
| Weekly (first month) | Review and fix triggering/execution issues |
| Monthly (after stable) | Check for outdated API references |
| Quarterly | Review metrics, update based on usage patterns |
| On dependency update | Verify examples still work with new versions |
| On user report | Fix confirmed issues within a week |

## Deprecation

When retiring a skill:

1. Add deprecation notice to description
2. Update SKILL.md body with migration guidance
3. Keep the skill available for 6 months
4. Archive after the grace period

```yaml
---
name: old-skill
description: "[DEPRECATED] Use new-skill instead. This skill is no longer maintained."
---
```


---

> **Steering tip:** Under-triggering and over-triggering require different fixes. Check `references/iteration/troubleshooting.md` for diagnostic steps before adjusting the description.
