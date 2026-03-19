# Context Engineering Patterns

6 patterns for optimizing token usage, managing context windows, and reducing the hidden cost of MCP tool definitions.

---

## 1. Tool Descriptions Eat ~15% of Your Context Budget

Every MCP tool you register injects its full definition -- name, description, and input schema -- into the system prompt on **every single message**, not only when the tool is invoked. Community measurement puts MCP tool definitions at roughly 15% of Claude Code's total input tokens in a typical session. A single complex tool like Playwright MCP can push that share to 50%.

The math compounds fast: each tool definition costs 50-150 tokens depending on schema complexity. Twenty tools at 100 tokens each is 2,000 tokens per message. Across a 30-turn conversation that's 60,000 tokens gone to definitions alone.

Claude Code v1.0.86+ ships a `/context` command that breaks down token usage by source. For raw traffic inspection, `claude-code-proxy` intercepts all requests and logs the full payload.

```typescript
// Bad -- 140+ tokens for this one tool
server.tool(
  "search_documents",
  {
    description: "Searches through all documents in the repository using full-text search. " +
      "Supports boolean operators, phrase matching, and field-specific queries. " +
      "Returns paginated results with relevance scores and highlighted snippets.",
    inputSchema: { /* ... */ }
  }
);

// Good -- under 100 tokens, same capability
server.tool(
  "search_documents",
  {
    description: "Full-text search across repo docs. Supports boolean, phrase, field queries. Returns paginated results.",
    inputSchema: { /* ... */ }
  }
);
```

```typescript
// Audit your tool token budget before registering
function estimateToolTokens(tools: Tool[]): void {
  for (const tool of tools) {
    const raw = JSON.stringify(tool);
    const estimate = Math.ceil(raw.length / 4); // rough chars-to-tokens
    if (estimate > 100) {
      console.warn(`[token-audit] ${tool.name}: ~${estimate} tokens — consider trimming`);
    }
  }
}
```

Trimming descriptions is one of the highest-ROI context optimizations you can make -- it requires no architecture changes and compounds across the entire conversation.

**Source:** [u/TheNickmaster21 and u/violet_mango on r/ClaudeAI](https://reddit.com/r/ClaudeAI/comments/1lnr1a5/); [claude-code-proxy](https://github.com/seifghazi/claude-code-proxy)

---

## 2. The Code Execution Pattern Saves 98% of Tool-Related Tokens

Instead of registering every tool definition upfront, expose a single `execute_code()` tool that runs scripts inside a sandbox. The model calls `list_servers()` to get names only, then `list_tools(server)` for names plus one-line descriptions, then `get_tool_schema(server, tool)` only when it actually needs a specific tool. Full schemas are fetched on demand and discarded after the call rather than injected permanently into the context.

**Benchmarks (Anthropic Engineering blog):** A session with 1,000 tool definitions and a 2-hour transcript drops from 150k tokens to 2k (98.7% reduction). A 10,000-row spreadsheet filter task falls from 10k to 0.5k (95%). Loop-based Slack polling compresses to a single script call (80%).

**Production caveat:** This pattern works cleanly with stdio-based local servers, but most production deployments use remote HTTP/SSE servers where OAuth flows and session management make dynamic discovery more complex.

```python
# Single gateway tool registered in the MCP server
@server.tool()
async def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code in sandbox. Use list_servers(), list_tools(server),
    get_tool_schema(server, tool) to discover capabilities on demand.
    """
    sandbox_globals = {
        "list_servers": lambda: ["filesystem", "github", "slack"],
        "list_tools": _list_tools_brief,       # returns name + 1-line desc only
        "get_tool_schema": _get_schema_on_demand,  # full JSON schema on request
        "call_tool": _call_tool,
    }
    exec(compile(code, "<sandbox>", "exec"), sandbox_globals)
    return sandbox_globals.get("__result__", "")

async def _list_tools_brief(server: str) -> list[dict]:
    # Returns minimal shape -- no full schemas injected into context
    tools = await registry.get_tools(server)
    return [{"name": t.name, "summary": t.description[:80]} for t in tools]

async def _get_schema_on_demand(server: str, tool: str) -> dict:
    # Full schema fetched only when the model explicitly requests it
    return await registry.get_full_schema(server, tool)
```

```python
# Model usage pattern -- lazy discovery in practice
code = """
servers = list_servers()                     # → ["filesystem", "github"]
tools   = list_tools("github")               # → [{"name": "create_pr", "summary": "..."}]
schema  = get_tool_schema("github", "create_pr")  # → full JSON schema
result  = call_tool("github", "create_pr", {"title": "Fix bug", "body": "..."})
__result__ = result
"""
```

**Source:** [Anthropic — Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp); [u/elusznik on r/mcp](https://reddit.com/r/mcp/comments/1oxmjzw/); [mcp-server-code-execution-mode](https://github.com/elusznik/mcp-server-code-execution-mode)

---

## 3. Shrink Tool Responses as Context Fills Up (Tiered Verbosity)

A tool that returns full pagination, rich metadata, and verbose field names makes sense early in a session when the context window is mostly empty. That same payload near the end of a long session can push the model into truncation territory. The fix: make verbosity a function of how much context remains.

**Three tiers keyed to remaining context fraction:**
- **Above 70% remaining:** Return everything -- full records, all fields, pagination metadata.
- **Between 40-70%:** Summary mode -- a count, top 5 items, and a `detail_available` flag with a hint to call `get_details(id)`.
- **Below 40%:** Only the count and a directive to narrow the query.

```python
from dataclasses import dataclass

CONTEXT_THRESHOLDS = {"full": 0.70, "summary": 0.40}

@dataclass
class ContextBudget:
    session_tokens: int
    total_window: int

    @property
    def remaining_fraction(self) -> float:
        return max(0.0, 1.0 - self.session_tokens / self.total_window)

    @property
    def tier(self) -> str:
        r = self.remaining_fraction
        if r >= CONTEXT_THRESHOLDS["full"]:
            return "full"
        if r >= CONTEXT_THRESHOLDS["summary"]:
            return "summary"
        return "minimal"

def tiered_response(records: list[dict], budget: ContextBudget) -> dict:
    tier = budget.tier

    if tier == "full":
        return {"results": records, "total": len(records)}

    if tier == "summary":
        return {
            "total": len(records),
            "sample": records[:5],
            "detail_available": True,
            "hint": f"Showing 5 of {len(records)}. Call get_details(id) for full records.",
        }

    # minimal -- only count + directive
    return {
        "total": len(records),
        "hint": "Context low. Narrow your query or call get_details(id) for a specific record.",
    }
```

A tool that blindly returns 10,000 rows at turn 40 of a 50-turn session will silently degrade model performance; a tiered response gives the model a graceful off-ramp.

**Source:** Production patterns from context-aware MCP server design; community reports on [r/ClaudeAI](https://reddit.com/r/ClaudeAI) and [r/mcp](https://reddit.com/r/mcp)

---

## 4. Strip ANSI Codes and Progress Bars Before Returning CLI Output

MCP servers that wrap command-line tools inherit everything those tools emit -- ANSI color codes, carriage-return-based progress bars, Unicode box-drawing characters, and alignment padding designed for human terminal rendering. None of that is meaningful to an LLM. It is pure token waste, and it is significant.

**Measured reductions (Pare MCP project):**
- `docker build` (multi-stage): 373 to 20 tokens (95%)
- `git log --stat` (5 commits): 4,992 to 382 tokens (92%)
- `npm install` (487 packages): 241 to 41 tokens (83%)
- `vitest run` (28 tests): 196 to 39 tokens (80%)
- `cargo build` (2 errors): 436 to 138 tokens (68%)

```python
import re
import subprocess

# Patterns to strip from CLI output
_ANSI_ESCAPE   = re.compile(r'\x1b\[[0-9;]*[mGKHF]')   # colors, cursor movement
_ANSI_ERASE    = re.compile(r'\x1b\[[0-9]*[JK]')         # screen/line erase
_CR_PROGRESS   = re.compile(r'[^\n]*\r')                  # carriage-return redraws
_SPINNER_CHARS = re.compile(r'[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]')           # spinner frames
_BOX_DRAWING   = re.compile(r'[─│┌┐└┘├┤┬┴┼╭╮╯╰]')       # box-drawing unicode

def clean_cli_output(raw: str) -> str:
    s = _ANSI_ESCAPE.sub('', raw)
    s = _ANSI_ERASE.sub('', s)
    s = _CR_PROGRESS.sub('', s)
    s = _SPINNER_CHARS.sub('', s)
    s = _BOX_DRAWING.sub('', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def run_cli_tool(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"},  # suppress at source too
    )
    combined = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return clean_cli_output(combined)

# Usage in an MCP tool handler
@server.tool()
async def git_log(n: int = 10) -> str:
    """Recent git log with stats."""
    return run_cli_tool(["git", "log", f"-{n}", "--stat", "--no-color"])
```

```typescript
// TypeScript equivalent -- used in Node-based MCP servers
const ANSI_RE = /\x1b\[[0-9;]*[mGKHFJK]/g;
const CR_RE   = /[^\n]*\r/g;

function cleanOutput(raw: string): string {
  return raw.replace(ANSI_RE, '').replace(CR_RE, '').replace(/\n{3,}/g, '\n\n').trim();
}
```

ANSI decoration can inflate CLI output by 5-95x in token terms -- stripping it is a zero-logic-change optimization that pays back immediately.

**Source:** [Pare MCP project](https://github.com/Dave-London/Pare); [u/Dave-London on r/ClaudeAI](https://reddit.com/r/ClaudeAI/comments/1r1tgxy/)

---

## 5. Use the Right Data Delivery Strategy for Each Tool Type

The three common strategies -- pagination, truncation, and streaming -- each have distinct cost and quality profiles.

**Pagination** suits lists, database queries, and anything likely to exceed 100 items. Per-page token cost is low and bounded, but adds 2-3 extra turns. No data is lost.

**Truncation** suits one-shot responses and logs where the model needs a quick look. Enforces a hard token ceiling with zero latency overhead, but quality degrades past ~5,000 items -- the model never knows what was cut.

**Streaming** suits live data and real-time log tailing. Each chunk is cheap, delivery is real-time, but the model receives an incomplete context view until the stream closes.

**Best pattern in practice -- hybrid first-page-plus-summary:**

```typescript
interface PaginatedResponse<T> {
  results:       T[];
  total_results: number;
  page:          number;
  total_pages:   number;
  has_more:      boolean;
  hint?:         string;   // only included when has_more === true
}

function paginateResults<T>(
  items:    T[],
  page:     number = 1,
  pageSize: number = 20,
): PaginatedResponse<T> {
  const total_pages = Math.ceil(items.length / pageSize);
  const start  = (page - 1) * pageSize;
  const slice  = items.slice(start, start + pageSize);
  const has_more = page < total_pages;

  return {
    results:       slice,
    total_results: items.length,
    page,
    total_pages,
    has_more,
    ...(has_more && {
      hint: `Showing ${slice.length} of ${items.length}. Use page=${page + 1} for more.`,
    }),
  };
}

// Truncation helper -- always tell the model what was cut
function truncateWithSignal(text: string, maxChars = 8000): string {
  if (text.length <= maxChars) return text;
  const dropped = text.length - maxChars;
  return text.slice(0, maxChars) +
    `\n\n[...truncated — ${dropped} chars omitted. Use a narrower query for more.]`;
}
```

Pagination without a summary forces extra turns; truncation without a signal causes silent data loss; hybrid gives the model full agency over whether to pay the cost of fetching more.

**Source:** [Anthropic — Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [r/mcp](https://reddit.com/r/mcp)

---

## 6. Each LLM Has a Tool Limit Beyond Which Accuracy Collapses

Registering more tools does not make a model more capable -- past a model-specific threshold it makes it less capable. Performance degradation hits a cliff, not a slope.

**Per-model profiles:**

| Model | Sweet Spot | Hard Degradation | Observed Behaviour |
|---|---|---|---|
| Claude 3.5 / 4 | 20-30 tools | ~50 tools | Ignores tools beyond position 30; accuracy drops ~15% past 128k context |
| GPT-4 / 4.1 | 15-20 tools | 128 (API hard limit) | Hallucinated tool calls appear above 50; latency roughly doubles above 15 |
| Gemini 1.5 Pro | 10 tools | ~100 tools | Optimised for single-call patterns; measurable quality degradation above 10 |

OpenAI explicitly recommends a maximum of 20 tools. Community consensus: "There is no standard solution. Disable the ones you don't need."

```typescript
// Tool group registry -- expose only tools relevant to the current task
const TOOL_GROUPS: Record<string, string[]> = {
  "code-review":   ["read_file", "search_code", "get_diff", "add_comment"],
  "deployment":    ["run_pipeline", "get_logs", "rollback", "set_env"],
  "data-analysis": ["query_db", "export_csv", "run_notebook", "plot_chart"],
};

function getToolsForTask(allTools: Map<string, Tool>, hint: string): Tool[] {
  for (const [group, names] of Object.entries(TOOL_GROUPS)) {
    if (hint.toLowerCase().includes(group.replace("-", " "))) {
      return names.map(n => allTools.get(n)!).filter(Boolean);
    }
  }
  return [...allTools.values()].slice(0, 20); // safe universal cap
}

// Progressive disclosure -- start with 3 always-on tools, expand on request
const ALWAYS_ON = ["help", "search", "read_file"];
const perModelLimit: Record<string, number> = { claude: 30, "gpt-4": 20, gemini: 10 };

function enableTool(active: string[], model: string, name: string): boolean {
  const limit = perModelLimit[model] ?? 20;
  if (active.length >= limit || active.includes(name)) return false;
  active.push(name);
  return true;
}
```

Every tool past the model's sweet spot adds token cost and degrades routing accuracy -- tool roster hygiene is a first-class correctness concern.

**Source:** [u/Rotemy-x10 on r/mcp](https://reddit.com/r/mcp) (271 upvotes); [u/Brief-Horse-454 on r/mcp](https://reddit.com/r/mcp); [OpenAI function-calling docs](https://platform.openai.com/docs/guides/function-calling); Claude model card context notes
