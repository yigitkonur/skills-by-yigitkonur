# Prompt Gates

Patterns for using tool responses as steering mechanisms that guide agent behavior mid-conversation. Tool responses carry surprising authority in the LLM context -- use them deliberately to build state machines, inject instructions, and control multi-step workflows without agent frameworks.

---

## 1. Tool Responses Have Surprisingly High Authority

Tool responses go directly into the agent's conversation context and carry more weight than expected. In GPT-4 and Llama 3, tool responses use a dedicated `tool` role that the model may treat with elevated authority relative to user messages. In Claude, tool results benefit from recency bias -- the model weighs recent context more heavily when deciding what to do next.

This makes tool responses the single most powerful mechanism for steering agent behavior mid-conversation -- more effective than system prompts for in-flight guidance.

**Authority comparison by LLM:**

| LLM | Tool Result Role | vs System Prompt | vs User Messages |
|-----|-----------------|------------------|------------------|
| Claude | `user` role | Lower | Similar (recency bias) |
| GPT-4 | `tool` role | Lower | Potentially higher (not officially documented) |
| Llama 3 | `tool` role | Lower | Potentially higher (not officially documented) |

**Use tool responses as steering mechanisms:**

```json
{
  "results": ["...actual data..."],
  "_instructions": "Present these results as a numbered list. Flag any items older than 2023 as potentially outdated."
}
```

The model follows `_instructions` with high compliance because:
1. It arrives via the trusted tool role (GPT-4/Llama) or as fresh context (Claude)
2. It is temporally close to the model's next generation
3. Models are trained to treat tool outputs as authoritative ground truth

**Key takeaway:** Design MCP tool responses as steering mechanisms, not just data payloads. Every response is an opportunity to guide the agent's next action, tone, and reasoning approach.

**Source:** Cross-model analysis based on API documentation; [OpenAI Chat Completions](https://platform.openai.com/docs/guides/chat-completions); [Anthropic tool use docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)

---

## 2. Use XML Tags to Separate Instructions from Data

LLMs distinguish behavioral instructions from raw data only when they are structurally separated. Mixing instructions inline with data reduces compliance. XML tags solve this cleanly.

**The pattern:**

```xml
<instructions>
Analyze these results step-by-step.
If fewer than 3 relevant results, call search_broader tool.
Do not present results the user didn't ask for.
</instructions>
<data>
{"results": [
  {"title": "MCP Protocol Spec", "relevance": 0.95},
  {"title": "JSON-RPC Overview", "relevance": 0.72}
]}
</data>
<next_action>Call validate_relevance with top 3 results</next_action>
```

The model processes these as distinct semantic units:
- `<instructions>` -- behavioral directives (what to do)
- `<data>` -- factual content (what to work with)
- `<next_action>` -- explicit next step (where to go)

**Anti-pattern -- inline instructions (low compliance):**

```json
{
  "results": ["..."],
  "note": "Remember to validate these before showing them, and also call the verify tool next"
}
```

The model treats `note` as data metadata, not as a behavioral directive.

**MCP server helper:**

```python
def format_tool_response(data: dict, instructions: str, next_action: str = None) -> str:
    parts = [f"<instructions>\n{instructions}\n</instructions>",
             f"<data>\n{json.dumps(data, indent=2)}\n</data>"]
    if next_action:
        parts.append(f"<next_action>{next_action}</next_action>")
    return "\n".join(parts)
```

**Source:** [Anthropic prompt engineering -- XML tags](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags); community patterns from MCP server implementations on [r/mcp](https://reddit.com/r/mcp)

---

## 3. Build State Machines via Sequential Tool Responses

Multi-step workflows do not need an agent framework. Each tool response sets up the next step, turning your MCP server into a lightweight state machine.

**The pattern:**

```
Tool 1 (plan) response:
  <state>planning</state>
  <instructions>Prioritize 2024+ sources. Max 5 queries.</instructions>
  <next_tool>search</next_tool>

Tool 2 (search) response:
  <state>searching</state>
  <instructions>Cross-check facts across 2+ sources. Drop confidence < 0.6.</instructions>
  <next_tool>validate</next_tool>

Tool 3 (validate) response:
  <state>complete</state>
  <instructions>Present with confidence scores. Cite sources inline.</instructions>
```

Each tool response acts as a prompt gate that:
1. Declares current state (so the model knows where it is)
2. Injects step-specific instructions (so behavior adapts per phase)
3. Points to the next tool (so the model does not wander)

The MCP server becomes a workflow orchestrator -- "flattening the agent back into the model." Deterministic multi-step behavior without any agent framework.

**Server-side helper:**

```typescript
function buildStateResponse(state: string, data: any,
    instructions: string, nextTool?: string): string {
  return [`<state>${state}</state>`,
    `<instructions>${instructions}</instructions>`,
    `<data>${JSON.stringify(data)}</data>`,
    nextTool ? `<next_tool>${nextTool}</next_tool>` : ""]
    .filter(Boolean).join("\n");
}
```

**Source:** u/Biggie_2018 on [r/mcp](https://reddit.com/r/mcp) -- "flattening the agent back into the model"

---

## 4. Namespace Injected Instructions to Prevent Conflicts

When multiple tools inject instructions, they can contradict each other. Namespacing solves this and prevents workflow hijacking.

**The pattern:**

```json
{
  "result": {"data": "..."},
  "_agent_guidance": {
    "source": "search_tool",
    "instructions": "Cross-reference these results before presenting to the user.",
    "next_action": {
      "tool": "validate",
      "required": true
    },
    "allowed_next_tools": ["validate", "summarize", "export"]
  }
}
```

**Why namespace:**
1. **Attribution** -- `source` tells the model (and debuggers) which tool issued the instruction
2. **Conflict resolution** -- when two tools disagree, the model can weigh by source
3. **Security** -- `allowed_next_tools` prevents a compromised tool from redirecting the agent to unintended tools

**Preventing workflow hijacking with a server-side tool graph:**

```python
TOOL_GRAPH = {
    "search":   {"allowed_next": ["validate", "search_broader"]},
    "validate": {"allowed_next": ["summarize", "search"]},
    "summarize": {"allowed_next": ["export", "refine"]},
}

def validate_next_tool(current_tool: str, requested_next: str) -> bool:
    allowed = TOOL_GRAPH.get(current_tool, {}).get("allowed_next", [])
    if requested_next not in allowed:
        raise ValueError(f"'{current_tool}' cannot invoke '{requested_next}'. Allowed: {allowed}")
    return True
```

Every tool response should include `_agent_guidance` with a consistent shape. The model learns the pattern quickly and follows it reliably.

**Note:** The `_agent_guidance` convention and `TOOL_GRAPH` validation are proposed patterns, not established standards. They represent a reasonable defense-in-depth approach but have not been widely adopted yet.

**Source:** Proposed pattern inspired by prompt injection research; [Palo Alto Unit 42 MCP research](https://unit42.paloaltonetworks.com); [Invariant Labs -- MCP tool poisoning](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)

---

## 5. Recommend the Next Tool or Query Frontier Explicitly

Recommending the next tool in the tool response is not a smell by itself. It is often the correct design, especially for research, search, SEO, and investigation tools where the agent would otherwise waste turns deciding what obvious follow-up to run.

The rule is: **recommend aggressively, execute conservatively**.

Good response shape:

```json
{
  "results": ["...current evidence..."],
  "_agent_guidance": {
    "source": "research_serp",
    "mode": "advisory",
    "next_action": {
      "tool": "fetch_pages",
      "reason": "The current SERP has enough signal to open the top two authoritative sources."
    },
    "recommended_queries": [
      {
        "query": "seo research mcp examples",
        "reason": "Current results are heavy on general AI search posts and light on concrete MCP implementations.",
        "confidence": 0.83
      },
      {
        "query": "agentic cli seo workflow",
        "reason": "Current results do not cover the CLI translation of the same steering pattern.",
        "confidence": 0.78
      }
    ],
    "stop_conditions": [
      "Stop expanding when two consecutive waves add fewer than 2 novel authoritative domains.",
      "Stop after 12 total searches."
    ],
    "server_actions_taken": [
      {
        "type": "internal_planner_turn",
        "purpose": "generate the next query frontier from the current SERP"
      }
    ]
  }
}
```

**Why this is powerful:**
- It turns each tool call into a local planner checkpoint.
- It reduces drift in open-ended workflows.
- It keeps the model focused on evidence gaps instead of generic "what should I do next?" behavior.

**Strong example:** a research MCP does one search wave, then uses a bounded internal model call to identify the next highest-signal keywords. Instead of returning only the top 10 links, it returns:
- the current SERP
- the missing angles
- the best next queries
- the stop conditions for continued expansion

That is much better steering than "here are 10 links, good luck."

**Guardrails:**
- `mode: advisory` means the server is steering, not silently taking external actions.
- If the server already spent an internal planning turn, say so in `server_actions_taken`.
- If the next action is mandatory for safety, mark it required and validate it against a server-side graph.
- Keep recommended queries or next tools short and ranked. Five good options beats twenty mediocre ones.

This is the right mental model for agentic MCPs: the response is not just the answer. It is the answer plus the best available continuation.
