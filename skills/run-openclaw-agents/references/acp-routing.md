# ACP Routing

Guide to discovering, selecting, and coordinating with ACP (Advanced Control Protocol) agents in OpenClaw.

## What are ACP agents

ACP agents are specialized coordination agents within the OpenClaw ecosystem. They handle domain-specific orchestration tasks that would be complex or error-prone to build from scratch. Think of them as pre-built orchestration modules for common multi-agent patterns.

ACP agents differ from regular agents in that they:
- Are purpose-built for specific coordination patterns
- Have their own internal state management and tool access
- Can coordinate multiple sub-agents internally
- Expose a higher-level interface to the calling agent

## Discovering ACP agents

Use `agents_list` to see all available agents, including ACP agents:

```
agents_list
```

ACP agents are identified by their agent type or naming convention in the listing. Look for agents whose descriptions mention coordination, orchestration, routing, or specialized domain handling.

**Selection criteria:**
- Match the ACP agent's described purpose to your coordination need
- Prefer an ACP agent over building custom coordination when one exists
- If multiple ACP agents could handle the task, choose the more specialized one

## When to route to ACP vs. build custom

| Situation | Approach |
|---|---|
| A purpose-built ACP agent exists for this coordination pattern | Route to the ACP agent |
| The coordination pattern is novel or highly specific to your workflow | Build custom using sub-agent patterns |
| An ACP agent handles 80% of the need but misses edge cases | Use the ACP agent and handle edge cases in the parent session |
| Multiple ACP agents need to work together | Orchestrate them as sub-agents from a supervisor pattern |

**Rule of thumb:** If you find yourself implementing multi-step coordination logic that reads like "spawn agent A, pass result to agent B, check condition, then spawn agent C" -- check if an ACP agent already handles that sequence.

## Invoking ACP agents

ACP agents are invoked through the same `sessions_spawn` mechanism as regular agents:

```
sessions_spawn agent_id=ACP_AGENT_ID task="coordination task description" tool_profile=APPROPRIATE_PROFILE
```

**Key differences from regular sub-agents:**
- ACP agents may spawn their own sub-agents internally (nested orchestration)
- ACP agents may take longer to complete due to multi-step internal coordination
- The result from an ACP agent is typically a high-level summary of the coordination outcome

**Task description for ACP agents:**
Be explicit about:
- The overall goal of the coordination
- The inputs and data the ACP agent needs
- The expected output format
- Any constraints on which tools or agents it should use internally

## ACP coordination patterns

### Single ACP delegation

The simplest use: delegate an entire coordination workflow to an ACP agent.

1. Identify the coordination need
2. Find the matching ACP agent via `agents_list`
3. Spawn with a clear task description
4. Yield for the result
5. Process the high-level outcome

### ACP as a stage in a pipeline

Use an ACP agent as one stage in a larger pipeline:

1. Earlier stages produce intermediate results
2. Spawn the ACP agent with those results as input
3. Yield for the ACP agent's coordination outcome
4. Use the outcome in subsequent stages

### Multiple ACP agents

When the workflow spans multiple coordination domains:

1. Identify which ACP agents cover which parts of the workflow
2. Determine dependencies between them (sequential or parallel)
3. Orchestrate them as sub-agents using fan-out or pipeline patterns
4. Aggregate their results

**Caution:** Multiple ACP agents may spawn their own sub-agents, creating nested orchestration. Monitor resource usage and session counts.

## Monitoring ACP agents

Because ACP agents may run complex internal workflows:

- Use `session_status` for quick health checks
- Use `sessions_history` to understand what the ACP agent is doing internally
- Set reasonable expectations for completion time (ACP agents doing multi-step coordination take longer than simple sub-agents)
- If an ACP agent appears stuck, inspect its history before stopping it -- it may be waiting for its own sub-agents

## ACP agent pitfalls

| Pitfall | Prevention |
|---|---|
| Bypassing an existing ACP agent to build custom coordination | Always check `agents_list` first for matching ACP agents |
| Treating ACP agents as simple sub-agents | Account for their internal complexity in timeout and monitoring |
| Not providing enough context in the task description | ACP agents need clear goals, inputs, expected outputs, and constraints |
| Nesting too many ACP agents | Keep nesting depth shallow (max 2-3 levels); deep nesting is hard to debug |
| Ignoring ACP agent internal failures | Inspect `sessions_history` even when the top-level result looks successful |
