# Sub-Agent Patterns

Patterns for spawning, managing, and coordinating sub-agents in OpenClaw. Each pattern addresses a different coordination topology.

## Core tool: sessions_spawn

```
sessions_spawn task="task description" agentId="AGENT_ID" runTimeoutSeconds=900 cleanup="keep"
```

**Risk level: HIGH.** Creates a new agent instance with tool access determined by the runtime configuration.

**Required parameters:**
- `task` -- clear description of what the sub-agent should accomplish

**Common optional parameters:**
- `agentId` -- target agent to spawn under, if `agents_list` shows an allowed better fit than the requester agent
- `runTimeoutSeconds` -- abort the run after N seconds when a bounded window matters
- `thread` / `mode` -- request a persistent thread-bound session when the channel supports it
- `cleanup` -- `delete` for disposable runs, `keep` for reusable or inspectable sessions
- `sandbox` -- `inherit` or `require` when sandbox guarantees matter

Before every `sessions_spawn`, use the HIGH-risk confirmation protocol from `SKILL.md` / `references/risk-and-security.md`: state the target agent/runtime, task, and side effects, then wait for explicit approval.

## Tool profiles

Profiles constrain what a child session can do, but `sessions_spawn` does not set them directly. The actual child tool surface comes from the target agent configuration plus the runtime's `tools.subagents.tools` policy.

| Profile | Capabilities | Example tasks |
|---|---|---|
| `minimal` | `session_status` only unless config adds more tools | Nearly tool-less canaries, health-check children |
| `coding` | File I/O, runtime, sessions, memory, image | Generate code, run tests, refactor, inspect a repo |
| `messaging` | `message`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` | Send notifications, relay information between sessions or platforms |
| Full (unrestricted) | All available tools | Tasks requiring multiple capability domains simultaneously |

**Profile selection rules:**
1. Start by asking which target agent or sub-agent policy already exposes the minimum safe surface
2. Use `coding` for any task that produces or modifies files
3. Use `messaging` only for tasks whose primary purpose is communication
4. Use `minimal` only when a nearly empty child is genuinely enough or your config adds explicit read-only tools
5. Use full access only when the task spans multiple domains and restricting would cause failure
6. Never use full access "just in case" -- scope expansion should be deliberate and visible to the user

**Escalation pattern:**
If a child fails with permission errors from a restricted surface:
1. Inspect the error to understand which capability was missing
2. Confirm the capability is genuinely needed (not just a suboptimal approach)
3. Re-spawn under a better-suited target agent or broader configured child policy
4. Document the escalation reason

**Default behavior that trips people up:**

- OpenClaw child runs are broad by default: children normally inherit most non-session, non-system tools unless the runtime narrows them
- Nested orchestration is not automatic: `maxSpawnDepth` defaults to `1`, so child sessions are leaf workers unless the runtime explicitly allows depth `2+`
- `sessions_spawn` is always non-blocking; capture the returned `childSessionKey` and use session inspection paths to collect results

## Pattern: Simple delegation

The most basic pattern. Spawn one sub-agent, wait for its result, continue.

**When to use:**
- A single well-defined task that another agent can handle better or in parallel
- Tasks that benefit from a different configured child tool surface or agent specialization
- Offloading work while the main session handles other concerns

**Sequence:**
1. `agents_list` -- find the right agent for the task
2. `sessions_spawn task="clear task description"` (and `agentId="..."` only if `agents_list` shows a better target)
3. Capture the returned `childSessionKey`
4. Wait for the announce reply or inspect `session_status` / `sessions_history`
5. Process the result
6. Decide whether to keep, reuse, or delete the child session

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
2. For each task: `sessions_spawn` with the appropriate agent and runtime constraints
3. Collect `childSessionKey` values
4. For each child: monitor announce replies, `session_status`, or `sessions_history`
5. Aggregate results
6. Clean up all sub-agent sessions

**Fan-out sizing:**
- 2-5 parallel sub-agents is typical and manageable
- More than 10 increases coordination overhead and resource pressure
- If you need more than 10, consider batching into waves

**Result aggregation:**
After collecting all results, the parent session is responsible for:
- Checking that all sub-agents completed successfully
- Handling partial failures (some succeeded, some failed)
- Merging or synthesizing results into a coherent output
- Resolving conflicts if sub-agents produced contradictory outputs

## Pattern: Pipeline (sequential chain)

Output from one sub-agent feeds as input to the next.

**When to use:**
- Multi-stage transformations where each stage has different requirements
- Workflows where intermediate results need different child tool surfaces
- Processing chains: extract, transform, validate, deploy

**Sequence:**
1. Spawn stage 1 sub-agent
2. Capture stage 1 `childSessionKey` and collect its result via announce/status/history
3. Use stage 1 result to formulate stage 2 task
4. Spawn stage 2 sub-agent with stage 1 result in the task description
5. Repeat for each stage
6. Clean up all sessions

**Pipeline design rules:**
- Each stage should have a clear input/output contract
- Pass only the necessary data between stages (not entire histories)
- Use the narrowest child tool surface per stage
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
3. Poll `session_status` periodically or inspect announce replies/history on each child
4. Inspect results via `sessions_history` for quality
5. If a result is insufficient: stop the sub-agent, refine the task, re-spawn
6. Aggregate accepted results
7. Clean up all sessions

**Supervisor discipline:**
- Set clear acceptance criteria before spawning sub-agents
- Inspect sub-agent output, do not blindly accept
- Limit re-spawn attempts (typically 2-3 per sub-task before escalating to the user)
- Track which sub-agents were re-spawned and why, for debugging
- Keep the supervisor in the parent session unless the runtime explicitly enables `maxSpawnDepth >= 2`

## Pattern: Chain of responsibility

Route a task through a sequence of agents until one can handle it.

**When to use:**
- Tasks where the best-suited agent is not known upfront
- Fallback chains: try the specialist first, then the generalist
- Routing based on task characteristics that only become clear at runtime

**Sequence:**
1. `agents_list` -- identify candidate agents in priority order
2. Spawn the highest-priority candidate
3. Set `runTimeoutSeconds` if needed, then inspect the announce reply or `session_status`
4. If the result is satisfactory: done
5. If the result is unsatisfactory or the agent cannot handle it: stop, try next candidate
6. If no candidate succeeds: escalate to the user

## Common sub-agent pitfalls

| Pitfall | Prevention |
|---|---|
| Vague task descriptions | Include concrete outcome, context, constraints, and definition of done |
| Over-privileged child surfaces | Verify the target agent and child policy instead of assuming a safe default |
| No result collection | Always capture `childSessionKey` and collect via announce, status, or history; never fire-and-forget |
| Too many parallel agents | Cap at 5-10; batch into waves if more are needed |
| Re-spawning indefinitely | Limit retries to 2-3 per sub-task |
| Passing entire context | Send only what the sub-agent needs, not the full parent history |
| Not inspecting sub-agent work | Use `sessions_history` to inspect actual behavior, especially for HIGH risk operations |
