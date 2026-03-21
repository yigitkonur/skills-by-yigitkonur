# Sub-Agent Patterns

Patterns for spawning, managing, and coordinating sub-agents in OpenClaw. Each pattern addresses a different coordination topology.

## Core tool: sessions_spawn

```
sessions_spawn agent_id=AGENT_ID task="task description" tool_profile=PROFILE
```

**Risk level: HIGH.** Creates a new agent instance with tool access determined by the profile.

**Required parameters:**
- `agent_id` -- the agent to spawn (discover with `agents_list`)
- `task` -- clear description of what the sub-agent should accomplish
- `tool_profile` -- the tool access level (see Tool profiles section)

## Tool profiles

Profiles constrain what a sub-agent can do. Always choose the narrowest profile that allows the task to complete.

| Profile | Capabilities | Example tasks |
|---|---|---|
| `minimal` | Read-only access to files and data, no writes, no network calls, no tool execution | Summarize a document, analyze code, answer questions from context |
| `coding` | File read/write, shell execution, git operations | Generate code, run tests, refactor, create PRs |
| `messaging` | `message` tool, `sessions_send` | Send notifications, relay information between platforms |
| Full (unrestricted) | All available tools | Tasks requiring multiple capability domains simultaneously |

**Profile selection rules:**
1. Start with `minimal` unless the task clearly requires writes or execution
2. Use `coding` for any task that produces or modifies files
3. Use `messaging` only for tasks whose primary purpose is communication
4. Use full access only when the task spans multiple domains and restricting would cause failure
5. Never use full access "just in case" -- profile escalation should be deliberate

**Escalation pattern:**
If a sub-agent fails with permission errors from a restricted profile:
1. Inspect the error to understand which capability was missing
2. Confirm the capability is genuinely needed (not just a suboptimal approach)
3. Re-spawn with the next-level profile
4. Document the escalation reason

## Pattern: Simple delegation

The most basic pattern. Spawn one sub-agent, wait for its result, continue.

**When to use:**
- A single well-defined task that another agent can handle better or in parallel
- Tasks that benefit from a different tool profile or agent specialization
- Offloading work while the main session handles other concerns

**Sequence:**
1. `agents_list` -- find the right agent for the task
2. `sessions_spawn agent_id=AGENT task="clear task description" tool_profile=minimal`
3. `sessions_yield session_id=SUB_AGENT_SESSION`
4. Process the result
5. Clean up: verify sub-agent is completed via `subagents`

**Task description quality matters.** The sub-agent has no shared context with the parent. Include:
- What to accomplish (concrete outcome, not vague direction)
- Relevant context the sub-agent needs (file paths, data, constraints)
- Definition of done (what constitutes a complete result)
- Constraints (what NOT to do, boundaries)

**Bad task description:** "Look at the code and fix bugs"
**Good task description:** "Read /src/auth/login.ts and fix the race condition in the token refresh logic. The refresh token is being used after expiry because the check on line 47 uses a stale timestamp. Return the corrected file content and explain the fix."

## Pattern: Fan-out (parallel delegation)

Spawn multiple sub-agents for independent tasks, then collect all results.

**When to use:**
- Multiple independent tasks that can run simultaneously
- Workloads that benefit from parallelism (e.g., analyzing multiple files, running tests across modules)
- Tasks where each sub-agent produces an independent result that gets aggregated

**Sequence:**
1. Identify independent task units
2. For each task: `sessions_spawn` with appropriate agent and profile
3. Collect session IDs
4. For each session: `sessions_yield` (or poll via `subagents` for non-blocking progress)
5. Aggregate results
6. Clean up all sub-agent sessions

**Fan-out sizing:**
- 2-5 parallel sub-agents is typical and manageable
- More than 10 increases coordination overhead and resource pressure
- If you need more than 10, consider batching into waves

**Result aggregation:**
After yielding all results, the parent session is responsible for:
- Checking that all sub-agents completed successfully
- Handling partial failures (some succeeded, some failed)
- Merging or synthesizing results into a coherent output
- Resolving conflicts if sub-agents produced contradictory outputs

## Pattern: Pipeline (sequential chain)

Output from one sub-agent feeds as input to the next.

**When to use:**
- Multi-stage transformations where each stage has different requirements
- Workflows where intermediate results need different tool profiles
- Processing chains: extract, transform, validate, deploy

**Sequence:**
1. Spawn stage 1 sub-agent
2. `sessions_yield` for stage 1 result
3. Use stage 1 result to formulate stage 2 task
4. Spawn stage 2 sub-agent with stage 1 result in the task description
5. Repeat for each stage
6. Clean up all sessions

**Pipeline design rules:**
- Each stage should have a clear input/output contract
- Pass only the necessary data between stages (not entire histories)
- Use the narrowest tool profile per stage
- If a stage fails, decide whether to retry that stage or abort the pipeline

## Pattern: Supervisor

A parent session acts as supervisor: delegates, monitors, re-delegates, and aggregates.

**When to use:**
- Complex workflows where sub-tasks may need re-routing based on intermediate results
- Quality control: supervisor inspects sub-agent output before accepting it
- Adaptive workflows where the next step depends on previous results

**Sequence:**
1. Supervisor analyzes the overall task and decomposes into sub-tasks
2. For each sub-task: `sessions_spawn` with clear definition of done
3. Poll `subagents` periodically or yield on each
4. Inspect results via `sessions_history` for quality
5. If a result is insufficient: stop the sub-agent, refine the task, re-spawn
6. Aggregate accepted results
7. Clean up all sessions

**Supervisor discipline:**
- Set clear acceptance criteria before spawning sub-agents
- Inspect sub-agent output, do not blindly accept
- Limit re-spawn attempts (typically 2-3 per sub-task before escalating to the user)
- Track which sub-agents were re-spawned and why, for debugging

## Pattern: Chain of responsibility

Route a task through a sequence of agents until one can handle it.

**When to use:**
- Tasks where the best-suited agent is not known upfront
- Fallback chains: try the specialist first, then the generalist
- Routing based on task characteristics that only become clear at runtime

**Sequence:**
1. `agents_list` -- identify candidate agents in priority order
2. Spawn the highest-priority candidate
3. `sessions_yield` with a timeout
4. If the result is satisfactory: done
5. If the result is unsatisfactory or the agent cannot handle it: stop, try next candidate
6. If no candidate succeeds: escalate to the user

## Common sub-agent pitfalls

| Pitfall | Prevention |
|---|---|
| Vague task descriptions | Include concrete outcome, context, constraints, and definition of done |
| Over-privileged profiles | Start with `minimal`, escalate only on evidence |
| No result collection | Always `sessions_yield` or poll; never fire-and-forget |
| Too many parallel agents | Cap at 5-10; batch into waves if more are needed |
| Re-spawning indefinitely | Limit retries to 2-3 per sub-task |
| Passing entire context | Send only what the sub-agent needs, not the full parent history |
| Not inspecting sub-agent work | Use `sessions_history` to audit, especially for HIGH risk operations |
