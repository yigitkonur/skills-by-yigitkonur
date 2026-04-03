# Testing

Patterns for testing MCP servers: evaluation-driven development with realistic workflows, using MCP Inspector for isolated debugging, auto-refactoring from transcripts, LLM-based usability evaluation, systematic tool selection evals with PromptFoo, and file hashing to prevent agent reprocessing loops.

---

## 1. Use Evaluation-Driven Development with Realistic Multi-Step Tasks

Do not test MCP tools in isolation. Build an evaluation suite that tests complete user workflows through the agent-tool interaction loop.

**The eval loop:**

```python
import anthropic

def run_eval(task: dict, tools: list) -> dict:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task["prompt"]}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            system="You are testing MCP tools. Think step by step before each tool call.",
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return {
                "success": verify_against_ground_truth(response, task["expected"]),
                "tool_calls": count_tool_calls(messages),
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "transcript": messages
            }

        # Process tool calls and continue the loop
        for block in response.content:
            if block.type == "tool_use":
                result = execute_mcp_tool(block.name, block.input)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                }]})
```

**What to measure beyond accuracy:**
- Total number of tool calls (fewer = better design)
- Token consumption per task
- Error rate and recovery rate
- Time to completion
- Whether the model chose the right tool on the first try

**Pro tip -- CoT before tool calls:** Include reasoning/feedback blocks in the system prompt before any tool-call block to trigger chain-of-thought. This surfaces the model's decision-making and helps you spot tool selection confusion.

**Pro tip -- auto-refactoring:** Feed the full evaluation transcript back to Claude and ask it to suggest description tweaks, parameter clarifications, and schema fixes based on where the model struggled.

**Source:** [Anthropic -- Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [modelcontextprotocol.io -- writing effective tools](https://modelcontextprotocol.io)

---

## 2. Test Tools with MCP Inspector Before Involving an LLM

Do not debug tool behavior through the LLM. Use the MCP Inspector to call tools directly and inspect raw JSON-RPC payloads.

**Quick launch:**

```bash
npx @modelcontextprotocol/inspector@latest
# Opens http://localhost:5173
```

**What to verify with Inspector:**
1. Tool discovery: Does `tools/list` return correct schemas?
2. Input validation: Do bad parameters produce clear errors?
3. Response format: Are responses structured as expected?
4. Error handling: Do failures return `isError: true` with guidance?
5. No stdout pollution: Does the server write only JSON-RPC to stdout?

**The debugging loop:**

```
1. REPRODUCE  -> Capture exact input that triggers the bug
2. CHECK LOGS -> Pull stderr logs for stack traces
3. ISOLATE    -> Disable all but one tool to narrow scope
4. INSPECTOR  -> Send crafted JSON-RPC payloads
5. FIX        -> Run the reproduced case + full test suite
```

**Three layers of testing:**
1. **Unit tests**: Test business logic functions directly (no MCP overhead)
2. **Integration tests**: Spin up the MCP server, call tools via the protocol
3. **Eval tests**: Run multi-step agent workflows with an actual LLM

Start from layer 1 and only involve the LLM (layer 3) after layers 1-2 pass. This saves time and API costs.

**Non-obvious tip:** Temporarily disable all but one tool to see if an issue persists. This isolates whether the problem is tool-specific or systemic.

**Source:** [Stainless -- Error Handling And Debugging MCP Servers](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers); [NearForm -- Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/); [MCP Inspector](https://www.npmjs.com/package/@modelcontextprotocol/inspector)

---

## 3. Feed Evaluation Transcripts Back for Auto-Refactoring

After running evaluation tasks, concatenate the full tool call transcripts and feed them back to Claude. The model can spot description ambiguities, schema inconsistencies, and naming issues that humans miss.

**The workflow:**

```python
# 1. Run eval and capture transcripts
eval_results = []
for task in eval_tasks:
    result = run_eval(task, tools)
    eval_results.append({
        "task": task["description"],
        "success": result["success"],
        "transcript": result["transcript"],
        "tool_calls": result["tool_calls"],
        "tokens": result["tokens_used"]
    })

# 2. Feed transcripts to Claude for analysis
analysis_prompt = f"""
Analyze these MCP tool evaluation transcripts and suggest improvements:

{json.dumps(eval_results, indent=2)}

For each failure or inefficiency, identify:
1. Which tool description was ambiguous
2. What parameter naming caused confusion
3. Where the response format led the model astray
4. Specific text changes to fix each issue

Output as a structured list of changes to make.
"""
```

**What Claude typically catches:**
- Tool descriptions that overlap, causing selection confusion
- Parameter names that do not match how the model thinks about the concept
- Missing examples in descriptions that would prevent common mistakes
- Response formats that bury important information
- Error messages that do not provide actionable recovery guidance

**Iterate until stable:** Repeat the prototype -> evaluate -> refine cycle until held-out test set performance stabilizes. Typically 3-5 rounds are enough.

**Source:** [Anthropic -- Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [modelcontextprotocol.io -- writing effective tools](https://modelcontextprotocol.io)

---

## 4. Ask the LLM to Evaluate Your Server's Usability

The LLM is your user. Ask it directly how to improve usability and tool documentation. AI UX is massively underappreciated and trivially easy to measure by simply asking.

**The feedback loop:**

```
You are using these MCP tools: [paste tool schemas]

1. Which tool descriptions are confusing or ambiguous?
2. Which parameter names don't match how you'd naturally think about the task?
3. Where do you feel uncertain about what a tool does or when to use it?
4. If you could redesign this interface from scratch, what would you change?
5. Here are two versions of a description -- which is more pleasant to use?
```

**A/B test descriptions in-context:**

```python
# Present two description variants and ask the model to pick
prompt = """
Version A: "Searches the database for matching records."
Version B: "Find records matching your criteria. Returns up to 50 results
sorted by relevance. Use filters to narrow: status, date_range, owner."

Which description would help you use this tool more effectively? Why?
"""
```

**What this catches that evals miss:**
- Subtle usability gap: the model "works around" a bad description instead of failing
- Missing context: the model wishes it knew what format a parameter expects
- Naming mismatch: the model's mental model does not match your parameter names
- Ambiguous boundaries: the model cannot tell when to use tool A vs tool B

**When to run this:**
- After every significant schema change
- When you notice the model using workarounds or extra tool calls
- Before finalizing tool descriptions for production

**Key insight:** The model will not complain unprompted -- it adapts silently. You have to explicitly ask for critique. Treat it like a user interview, not a bug report.

**Source:** [u/jimmiebfulton on r/mcp](https://reddit.com/r/mcp) (260 upvotes thread); [u/jbr on r/mcp](https://reddit.com/r/mcp)

---

## 5. Use PromptFoo for Systematic Tool Selection Evals

The only way to know if tool descriptions actually work is to measure tool selection accuracy across models. Use PromptFoo or similar frameworks to test: given a user intent, does the model pick the right tool with the right parameters?

**Basic PromptFoo config:**

```yaml
# promptfoo.yaml
prompts:
  - "You have access to these tools: {{tools}}. User request: {{request}}"

providers:
  - openai:gpt-4o
  - anthropic:messages:claude-sonnet-4-20250514
  - ollama:llama3.1

tests:
  # Positive case: correct tool should be selected
  - vars:
      request: "Find all orders from last week"
      tools: "{{tool_schemas}}"
    assert:
      - type: contains
        value: "search_orders"
      - type: contains
        value: "date_range"

  # Negative case: tool should NOT be selected
  - vars:
      request: "What's the weather today?"
      tools: "{{tool_schemas}}"
    assert:
      - type: not-contains
        value: "search_orders"
```

**What to eval:** selection accuracy, parameter correctness, ambiguity handling (two tools could apply), and refusal (tools that should not be selected).

**Run it:**

```bash
npx promptfoo@latest eval
npx promptfoo@latest view  # opens comparison dashboard
```

**Cross-model gotchas:** Claude is conservative (asks before calling), GPT hallucinates param values, smaller models (Llama, Mistral) struggle with >10 tools. Run evals in CI -- a tweak that helps Claude can break Llama.

**Source:** [u/AchillesDev on r/mcp](https://reddit.com/r/mcp); [Anthropic -- Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [PromptFoo MCP integration](https://www.promptfoo.dev/docs/integrations/mcp/)

---

## 6. Use File Hashing to Prevent Agent Reprocessing Loops

Hash the full execution state -- not just the action -- so the agent can detect "I already downloaded and parsed this exact file 30 seconds ago." This kills the common loop where agents re-download, re-parse, or re-process the same data repeatedly.

**Server-side execution cache:**

```python
import hashlib, time, json

execution_cache: dict[str, dict] = {}
CACHE_TTL = 60  # seconds

def get_cache_key(tool_name: str, params: dict) -> str:
    """Hash tool name + all params including file refs."""
    state = json.dumps({"tool": tool_name, "params": params}, sort_keys=True)
    return hashlib.sha256(state.encode()).hexdigest()

def call_tool_with_cache(tool_name: str, params: dict) -> dict:
    force = params.pop("force_refresh", False)
    key = get_cache_key(tool_name, params)
    if not force and key in execution_cache:
        entry = execution_cache[key]
        age = time.time() - entry["timestamp"]
        if age < CACHE_TTL:
            return {"result": entry["result"], "cached": True,
                    "note": f"Cached {int(age)}s ago. Use force_refresh=true to bypass."}
    result = execute_tool(tool_name, params)
    execution_cache[key] = {"result": result, "timestamp": time.time()}
    return {"result": result, "cached": False}
```

**Hash inputs:** tool name, all parameters, file URLs/paths, filter/query values.
**Do not hash:** timestamps, request IDs, auth tokens, pagination cursors.

**The `force_refresh` escape hatch -- always expose as an optional param:**

```json
{
  "name": "download_report",
  "description": "Downloads and parses the report. Cached 60s. Use force_refresh=true for fresh data.",
  "inputSchema": {
    "properties": {
      "url": { "type": "string" },
      "force_refresh": { "type": "boolean", "default": false }
    }
  }
}
```

**Source:** [u/Main_Payment_6430 on r/AI_Agents](https://reddit.com/r/AI_Agents); [MotherDuck -- Dev Diary: Building MCP](https://motherduck.com/blog/dev-diary-building-mcp/)
