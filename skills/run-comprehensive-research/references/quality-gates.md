# Quality Gates

Decision points where the orchestrator checks agent results and decides whether to retry, supplement, or proceed.

## Agent Completion Gate

| Signal | Verdict | Action |
|---|---|---|
| Comprehensive output covering all requested sections | PASS | Write docs immediately |
| Output covers most sections, minor gaps | PASS with gaps | Write what exists, note gaps in synthesis |
| Agent reports "tools denied" | TOOL FAILURE | Relaunch with `bypassPermissions` + fallback instructions |
| Agent returns shallow/surface output | QUALITY FAIL | Send follow-up with specific gaps and pressure |
| Agent output is off-topic | SCOPE FAIL | Do not relaunch — write what's usable |
| Agent times out | TIMEOUT | Relaunch with narrowed scope (split the domain) |
| Agent output file is empty | CRASH | Relaunch once with identical prompt |

## Tool Denial Recovery

The #1 failure mode is agents stopping because MCP research tools are denied. The fix:

1. **First attempt:** Include fallback chain in the original prompt: "If MCP tools fail, use WebFetch/WebSearch. If those fail, use curl."
2. **On denial:** Relaunch with `mode: "bypassPermissions"` and explicit fallback instructions
3. **On second denial:** The tools are genuinely unavailable. Switch to `Bash` curl-based research

**Relaunch prompt template:**
```
[Original mission brief, unchanged]

IMPORTANT ADDITION: Previous attempt failed because research tools
were denied permission. Use these tools in order of preference:
1. WebFetch/WebSearch (built-in tools)
2. Bash with curl for fetching URLs directly
3. Bash with gh api for GitHub data
4. Bash with curl for Reddit JSON API

Do NOT stop working if a tool is denied. Try the next one.
```

## Depth Gate

After collecting all agent outputs, before synthesis:

| Signal | Verdict | Action |
|---|---|---|
| All planned files have substantive content | PASS | Proceed to synthesis |
| 1-2 files are thin (<50 lines) | MINOR GAP | Supplement during synthesis (orchestrator fills inline) |
| A full domain is missing or empty | MAJOR GAP | Dispatch a focused follow-up agent for that domain only |
| Community feedback has <5 sources | THIN COMMUNITY | Accept if topic is niche; note in synthesis |
| No code examples in implementation docs | QUALITY GAP | Add examples during doc writing (from agent's prose) |

## Retry Budget

| Resource | Max | After exhaustion |
|---|---|---|
| Agent relaunches per domain | 2 | Proceed with what exists, document the gap |
| Follow-up messages to running agents | 1 per agent | Accept their output as-is |
| Total researcher agents across all waves | 12 | Hard cap — synthesize what you have |
| Total session cost guard | Check with user | Inform user of agent count and estimated scope |

## When to Stop Researching

Stop and synthesize when ANY of these is true:
- All planned documentation files have substantive content
- Retry budget is exhausted for all failing domains
- User says "that's enough" or "move on"
- Additional agents would not cover new ground (diminishing returns)
- 12+ agents dispatched across all waves

## When to NOT Retry

- Agent output is partially off-topic but contains useful findings → extract the useful parts, discard the rest
- Agent produced different structure than planned → adapt the file structure to match what the agent found (reality > plan)
- Agent found the topic is smaller than expected → fewer files is fine (don't pad to match the plan)

## The Orchestrator's Final Check

Before declaring research complete, the orchestrator personally verifies:

- [ ] Every file in the planned structure exists
- [ ] No file is a placeholder or stub
- [ ] Source attribution is present throughout
- [ ] Platform/domain differences are explicit
- [ ] The master summary cross-references all files
- [ ] Each file is independently actionable
- [ ] Gaps are documented (not hidden)
