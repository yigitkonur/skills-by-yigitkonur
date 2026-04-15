# Model-Specific Tool-Use Behavior and Benchmarks

Current-generation empirical per-model reference for MCP server authors. Covers late-2025 frontier and open-weight models: their measured tool-use accuracy, JSON Schema quirks, parallel-call idioms, pricing, and the adjustment rules that determine whether your MCP server works across them.

The outdated "Claude 20–30 / GPT 15–20 / Gemini 10" rules-of-thumb from `context-engineering.md` and the cross-model schema matrix in `schema-design.md` Pattern 8 are superseded by the numbers and idioms below. Read this file when designing for multi-client deployment, picking a default model, estimating cost-per-workload, or debugging model-specific tool-call failures.

## The Late-2025 Landscape

There is no single tool-use champion. Four different models lead four different leaderboards, and the gap between benchmark wins and production MCP workflows is large.

- **BFCL v3** (single-turn function-calling accuracy) — **GLM-4.5 leads at 77.8%**. Source: https://gorilla.cs.berkeley.edu/leaderboard.html (retrieved 2026-04-14).
- **MCP-Atlas** (real-MCP workflow pass rate across heterogeneous servers) — **Claude Opus 4.5 leads at 62.3%**. Source: https://scale.com/blog/open-sourcing-mcp-atlas and arxiv.org/abs/2602.00933 (retrieved 2026-04-14).
- **MCPMark** (multi-step MCP Pass@1) — **GPT-5 high leads at 57.5%**. Source: https://mcpmark.ai/leaderboard (retrieved 2026-04-14).
- **τ²-bench telecom** is effectively saturated at ~99% by GLM-4.7-Flash and GLM-5 Turbo (see https://artificialanalysis.ai/evaluations/tau2-bench), so τ²-telecom no longer discriminates between top models — use τ²-airline, MCP-Atlas, and MCPMark for real signal.

Three additional baseline facts every MCP author should assume:

1. **OpenAI's own function-calling guide now recommends ≤20 active tools** (https://platform.openai.com/docs/guides/function-calling, retrieved 2026-04-14).
2. **Google's Gemini function-calling docs recommend 10–20 active tools** (https://ai.google.dev/gemini-api/docs/function-calling, retrieved 2026-04-14).
3. **Microsoft Research (2025-09-11)** measured up to **85% accuracy loss** from tool-space interference when large tool surfaces are exposed, and found that in a 1,312-tool corpus the top tool averaged **557,766 tokens** with 16 tools exceeding 128,000 tokens. Source cited in Klavis AI analysis (https://klavis.ai, "Function Calling and Agentic AI in 2025", 2025-10-25).

The rest of this file converts those facts into actionable patterns.

---

## Master Model-Capability Table

One row per model, one place to look up everything. All benchmark scores carry a leaderboard URL and retrieval date above. Pricing in USD per 1M tokens; "Cache hit" is the input-cached read price where publicly documented.

| Model | Release | BFCL v3 | τ²-bench airline | MCP-Atlas pass | MCPMark Pass@1 | Parallel tools | JSON Schema caveats | Input $/M | Output $/M | Cache hit $/M |
|---|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 4.5 | 2025-11-24 | n/a | n/a | **62.3%** | 42.3% | Default on | Full JSON Schema | $5 | $25 | $0.50 |
| Claude Sonnet 4.5 | 2025-09-29 | n/a | n/a | 43.8% | 32.1% | Default on | Full | $3 | $15 | $0.30 |
| Claude Sonnet 4 | 2025-05 | 70.3% | 44.0% | 35.6% | 28.1% | Default on | Full | $3 | $15 | $0.30 |
| Claude Opus 4.1 | 2025-08 | 70.4% | 54.0% | 40.9% | 29.9% | Default on | Full | $15 | $75 | $1.50 |
| Claude Haiku 4.5 | 2025-10-15 | n/a | n/a | n/a | n/a | Default on | Full | $1 | $5 | $0.10 |
| Claude 3.7 Sonnet | 2025-02 | n/a | 56.0% | n/a | n/a | Default on | Full | $3 | $15 | $0.30 |
| GPT-5 | 2025-08-07 | 59.2% | 48.0% | 44.5% | **57.5%** high | Default on | Strict: oneOf/anyOf/allOf/$ref OK; freeform mode bypasses JSON | $1.25 | $10 | $0.125 |
| GPT-5 mini | 2025-08-07 | n/a | n/a | n/a | 27.4–30.3% | Yes | Same as GPT-5 | ~$0.25 | ~$2 | ~$0.025 |
| GPT-4.1 | 2025-04-14 | n/a | 36–68% | n/a | 8.1% | Yes; nano duplicate-call bug | Strict: `additionalProperties:false` + every field required | $2 | $8 | $0.50 |
| o3 medium | 2025-04 | n/a | 54.0% | 43.6% | 25.4% | Yes | Same as GPT-5 strict | ~$2 | ~$8 | — |
| o4-mini high | 2025-04 | n/a | 56.0% | n/a | 17.3% | Yes | Same | ~$1.1 | ~$4.4 | — |
| Gemini 3 Pro Preview | 2025-11 | n/a | n/a | **54.1%** | 53.9% | Yes | No `anyOf`; no `$ref`; rejects deep nesting | $2 | $12 | $0.20 |
| Gemini 2.5 Pro | 2025-03 | n/a | n/a | 8.8% | 15.8% | Yes | Same Gemini limits | $1.25 / $2.50 >200k | $10 / $15 >200k | $0.125 |
| Gemini 2.5 Flash | 2025 | n/a | n/a | 3.4% | 9.1% | Yes | Same | $0.30 | $2.50 | $0.03 |
| Grok 4 | 2025-07-09 | n/a | n/a | n/a | 31.7% | Advertised; undocumented | None published | $3 | $15 | $0.75 |
| Llama 4 Maverick | 2025-04-05 | n/a | n/a | **0.8%** | n/a | Partial | No first-party tool-use training | ~$0.20 / $0.60 | — | — |
| Llama 4 Scout | 2025-04-05 | 55.7% | n/a | n/a | n/a | Partial | Same | — | — | — |
| GLM-4.5 | 2025 | **77.8%** (#1) | n/a | n/a | 15.6% | Yes | — | $0.40 | $1.60 | — |
| Qwen3-Max | 2025 | n/a | n/a | 12.0% (235B) | 17.7% | Yes | `enum` OK; oneOf/$ref undocumented | ~$0.15 | ~$3 | — |
| Qwen3-Coder-Plus | 2025 | 480B: 68.7% | n/a | n/a | 24.8% | Yes | Same | ~$0.30 | ~$1.50 | — |
| DeepSeek V3.2 thinking | 2025 | n/a | n/a | n/a | 36.8% | Yes (single-user-msg-many-calls idiom) | Strict: `anyOf` + `$ref` supported | $0.27 / $0.07 cache | $1.10 | $0.07 |
| DeepSeek R1 | 2025-01 | n/a | 36.0% | n/a | n/a | R1-0528 improved tools | Same | $0.55 / $0.14 cache | $2.19 | $0.14 |
| Mistral Large 2 (2024-11) | — | n/a | n/a | n/a | n/a | `parallel_tool_calls=true` default | Only `type/object/properties/required/string` | $2 | $6 | — |

Source index: BFCL https://gorilla.cs.berkeley.edu/leaderboard.html · τ²-airline https://hal.cs.princeton.edu/taubench_airline and https://sierra.ai/blog/t-bench-leaderboard · τ² live https://artificialanalysis.ai/evaluations/tau2-bench · MCP-Atlas https://scale.com/blog/open-sourcing-mcp-atlas (arxiv 2602.00933) · MCPMark https://mcpmark.ai/leaderboard · Pricing via https://llm-stats.com and https://pricepertoken.com · Klavis AI 2025-10-25 analysis at https://klavis.ai. All retrieved 2026-04-14.

---

## Per-Family Idioms

Short notes on the call-shape idiom each family prefers. These are the details that break MCP clients when left wrong, not the ones benchmarks capture.

### Claude (4, 4.5, 4.6)

- **Parallel tool use is default-on** starting with the 4.x family. See https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use.
- **All `tool_result` blocks for a parallel batch must be in a single subsequent user message.** Splitting them across messages is the #1 Claude parallel-call bug in the wild.
- Disable parallel tool use when strict step-by-step is required: set `disable_parallel_tool_use=true` inside `tool_choice`.
- Sonnet 4.5 converges faster than Sonnet 4 on agentic loops per Glean (2026-01-27): **1.61 tool calls/turn** (vs 2.08), **1.34 parallel calls/turn** (vs 1.00), **2.19 adaptive-planning cycles** (vs 3.08).
- **Prompt cache is the biggest MCP cost lever.** Up to 4 cache breakpoints, 20-block lookback, 1h extended TTL at **2× base input** on write and **10% of base** on hit. See https://platform.claude.com/docs/en/build-with-claude/prompt-caching.
- Opus 4.5 produces **65–76% fewer output tokens at equal quality vs Sonnet 4.5** (Anthropic 2025-11-24 launch post) — a material factor when the tool loop emits long assistant messages.

### GPT (5, 4.1, o3, o4-mini)

Two tool-calling modes:

1. **Classic JSON tool calls**, optionally `strict: true`. Strict mode supports `oneOf`/`anyOf`/`allOf`/`$ref` but requires `additionalProperties: false` and every field in `required` (use nullable type for optional). See https://developers.openai.com/api/docs/guides/structured-outputs.
2. **Freeform tool calling (GPT-5 only, 2025-08-22)** — raw text payloads, no JSON. Result comes back via `function_call_output`. Best for shells, code, SQL, regex, DSLs. Source: https://devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/.

OpenAI's own guidance: "aim for fewer than 20 functions at any one time" (https://platform.openai.com/docs/guides/function-calling). `gpt-4.1-nano-2025-04-14` has a duplicate-call bug with parallel tool calls — disable parallel on that model specifically. Reasoning items returned alongside tool calls **must** be round-tripped on the next request or behavior degrades.

### Gemini (2.5, 3)

- Parallel function calling supported across 2.5 and 3.
- **`anyOf` not supported** in function calling; confirmed by the Zod issue https://github.com/colinhacks/zod/issues/5807 (2026-03). Substitute `discriminatedUnion()` so Zod emits `oneOf`, which Gemini handles.
- **`$ref` not supported.**
- API rejects "very large or deeply nested schemas" — flatten to ≤3 levels, keep property names <20 chars.
- Google explicitly recommends ≤10–20 active tools (https://ai.google.dev/gemini-api/docs/function-calling).
- Context caching priced per **hour of storage** ($4.50 per 1M tokens per hour on 2.5 Pro) — unusual among providers. Estimate storage-hours, not just read count.

### Llama 4

No first-party function-calling training. The ecosystem uses Hermes-style tags (Nous Research) or host adapters. **MCP-Atlas 0.8% for Maverick** is the lowest among frontier models, so plan for heavy scaffolding (explicit planner tool, tight tool shapes, examples in descriptions) if you must support Llama 4.

### Qwen 3

Native Hermes-style tool use; vLLM + Qwen-Agent emit multiple `tool_calls` in one assistant message. Qwen3 tops BFCL v3 single-turn (aside from GLM) but falls off on multi-step MCP (Qwen3-Max 17.7% MCPMark). Schema-wise, `enum` is safe; `oneOf`/`anyOf`/`$ref` are not documented — assume unsupported.

### DeepSeek (V3, R1, V3.2)

- DeepSeek never published an official chat template for tool use; Fireworks reverse-engineered one in their 2025-02-14 blog, which is why many hosts still hit parser fragility. Pin provider hosting.
- DeepSeek's own docs state the model is "not great at multi-turn function calling" and performs best with **one user message triggering multiple tool calls in a single assistant turn**. Source: https://api-docs.deepseek.com/guides/function_calling.
- R1-0528 (May 2025) ships tool-calling fixes — use R1-0528 or newer, never pre-0528.
- Strict mode supports `object/string/number/integer/boolean/array/enum/anyOf/$ref/$def`, making DeepSeek the most JSON-Schema-friendly provider aside from OpenAI strict.

### Mistral

`parallel_tool_calls: true` is default. Flip to `false` for single-tool discipline. Schema support is minimal — only `type/object/properties/required/string`; no `oneOf`/`anyOf`/`$ref`/`format`.

### Grok (xAI)

Neither Grok 4's release post nor model card publishes BFCL, τ-bench, or MCP numbers. Treat Grok as `no-public-benchmark-2025-12`. MCPMark reports Grok 4 at 31.7% Pass@1. Advertised features include agentic tool calling, cached-token pricing, and remote MCP tools, but parallel-call semantics are undocumented — test empirically before relying on them.

---

## Adjustment Rules for MCP Server Authors

Numbered patterns, each with the rule, the quantitative why, a short example, and a source. These are the rules that change what `SKILL.md` Phase 3 findings should recommend in 2025/2026.

### Pattern 1: Cap active tools at ≤20 regardless of vendor

OpenAI's function-calling guide says "aim for fewer than 20 functions at any one time"; Google's Gemini docs recommend 10–20; Microsoft Research (Sep 2025) measured **up to 85% accuracy loss** from tool-space interference at larger surfaces. The old "Claude can do 30" rule no longer reflects vendor guidance or empirical degradation.

How to achieve it on a large MCP surface:

- Partition tools across scoped MCP servers (one per intent cluster).
- Filter tools per request based on the stated goal.
- Use an advisor/executor split — Claude Opus 4.5 or Gemini 3 Pro picks the workflow; a cheaper model (Haiku 4.5, GPT-5 mini, Gemini 2.5 Flash) executes it with only the filtered subset.

**Source:** https://platform.openai.com/docs/guides/function-calling, https://ai.google.dev/gemini-api/docs/function-calling, Klavis AI 2025-10-25 analysis citing Microsoft Research.

### Pattern 2: For Gemini, emit `oneOf` not `anyOf`, and flatten nesting to ≤3 levels

Gemini silently rejects `anyOf` and `$ref` in function calling, and API calls fail on deeply nested schemas. The Composio tool-schema flattening technique delivered **+47% tool-calling improvement** on Gemini in Microsoft Research's tests. Any `z.union()` in your Zod input types breaks on Gemini — migrate to `z.discriminatedUnion()` (which emits `oneOf`) before shipping to Gemini clients.

```typescript
// Breaks on Gemini — z.union emits anyOf
const input = z.object({
  target: z.union([
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});

// Works on Gemini — discriminatedUnion emits oneOf
const input = z.object({
  target: z.discriminatedUnion("kind", [
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});
```

**Source:** https://ai.google.dev/gemini-api/docs/function-calling; https://github.com/colinhacks/zod/issues/5807 (2026-03); Composio flattening cited in Microsoft Research / Klavis analysis.

### Pattern 3: For Claude, batch all `tool_result` blocks into ONE user message and cache tool definitions on the 1h TTL

The single-user-message-for-parallel-results rule is a hard requirement — violating it breaks Claude's tracking of parallel tool state. On top of that, route your entire tool-definitions block (typically the biggest repeating payload in an MCP session) through the 1h prompt cache. A 5,000-token tool block priced at $3/1M input costs **$0.015 uncached per request**; with 1h caching it costs **$0.03 once on write then $0.0015 per hit** — roughly **83% input-cost reduction** over a multi-turn session.

```python
# Put tool definitions in one cached block at the top of the system/tools payload.
messages = [
  {"role": "system", "content": [
    {"type": "text", "text": SYSTEM_PROMPT},
    {"type": "text", "text": TOOL_DEFINITIONS,
     "cache_control": {"type": "ephemeral", "ttl": "1h"}},
  ]},
  # ...then per-request messages
]
```

**Source:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use; https://platform.claude.com/docs/en/build-with-claude/prompt-caching.

### Pattern 4: For GPT-5 + non-JSON DSLs, switch to freeform tool calling

Shells, SQL, regex, code blocks, and custom DSLs all pay a JSON-escape tax in classic tool calls — every newline becomes `\n`, every quote `\"`, and the model often gets the escaping wrong. GPT-5's freeform tool-calling mode (2025-08-22) emits raw text payloads directly. Use it for any tool whose input is code or a DSL. For tools whose input is genuinely structured, keep classic JSON but set `strict: true`, `additionalProperties: false`, and mark every parameter required (nullable type for optional).

**Source:** https://devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/; https://developers.openai.com/api/docs/guides/structured-outputs.

### Pattern 5: For DeepSeek, prefer "one user message → many tool calls in one assistant turn"

DeepSeek's own docs mark multi-turn tool dialogues as weak. Design your MCP tool sequences so the agent emits multiple `tool_calls` in a single assistant message whenever possible, then consumes all results together. Avoid long interleaved turns. Pin R1-0528 or newer; older R1 revisions have material tool-calling regressions.

**Source:** https://api-docs.deepseek.com/guides/function_calling; Fireworks 2025-02-14 template reverse-engineering post.

### Pattern 6: Treat `$ref`, `oneOf`/`anyOf`, and recursive schemas as hostile terrain

Only **OpenAI strict** and **DeepSeek** reliably handle polymorphic JSON Schema features. Everyone else either rejects or silently degrades. Author tools in "lowest common denominator JSON Schema" — `type`/`properties`/`required`/`enum`/`description`/`format` only — and only opt into `oneOf`/`$ref` on an OpenAI-only or DeepSeek-only code path.

Quick portability test (extend the snippet from `schema-design.md` Pattern 8):

```typescript
function validateCrossClientSchema(schema: any): string[] {
  const issues: string[] = [];
  if (schema.anyOf) issues.push("anyOf: breaks Gemini, Mistral, Llama 4");
  if (schema.$ref) issues.push("$ref: breaks Gemini, Mistral, Qwen 3");
  if (countNestingDepth(schema) > 3) issues.push("nesting >3: breaks Gemini");
  if (Array.isArray(schema.enum) && schema.enum.length > 20)
    issues.push("enum >20: degrades all non-Claude models");
  return issues;
}
```

**Source:** see per-family notes above; cross-model testing in r/mcp and Klavis AI 2025-10-25.

### Pattern 7: Cap individual tool responses at ≤25,000 tokens; trim chatty tools to ≤1,000

Microsoft Research (Sep 2025) measured a 1,312-tool corpus: the top tool averaged **557,766 tokens per response** and 16 tools exceeded **128,000 tokens**. Anthropic's default Claude Code limit is **25,000 tokens per tool response**, and studies cited by Klavis show overly long responses costing up to **91% of performance** in worst cases. Hard-cap response size, paginate built-in, default to small, and expose a `more` or `page` tool for deeper fetches.

```python
MAX_TOKENS = 25_000   # matches Claude Code default
DEFAULT_PAGE_SIZE = 50

def list_records(filters: dict, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
    rows = db.query(filters, offset=(page-1)*page_size, limit=page_size)
    body = render(rows)
    if approx_tokens(body) > MAX_TOKENS:
        body = render(rows[:page_size // 2])
    return {"page": page, "rows": body,
            "has_more": len(rows) == page_size,
            "next_step": f"Call list_records(page={page+1}) for more."}
```

**Source:** Microsoft Research 2025-09-11 tool-space interference study; Klavis AI 2025-10-25.

### Pattern 8: Size tool-response caps against the actual context window of the target model

The same 1,312-tool corpus, projected across 6–10 tool-call sessions, produced:

- **25 overflows** against GPT-5's 400K window,
- **40 overflows** against GPT-4o's 128K window,
- **90 overflows** against Qwen3's 32K window,
- **109 overflows** against Phi-4's 16K window.

Short-context open-weight models (Qwen3 32K, Phi-4 16K, older Llama variants) are unusable as MCP hosts without tighter per-tool caps than the 25K default. If your target includes short-context hosts, cap individual tool responses at **≤5,000 tokens** and document it as a deployment constraint.

**Source:** Microsoft Research 2025-09-11, as summarized by Klavis AI 2025-10-25.

### Pattern 9: Compact or prune tool-call history past ~50K input tokens

Chroma's 2025 "Context Rot" study found all frontier models show monotone context-length degradation: LongMemEval **focused** prompts (~300 tokens) significantly outperform **full** prompts (~113K tokens), and the Repeated-Words stress test shows consistent degradation as input grows. MCP sessions that accumulate tool-response history without trimming hit this wall predictably.

Practical shape for an MCP host:

- After ~50K input tokens, summarize older tool results into a "history_summary" tool block and drop raw content.
- Keep the last N tool results raw (N=3 is a reasonable default) for local coherence.
- For Claude, put the stable summary behind a cache breakpoint.

**Source:** Chroma 2025 Context Rot study.

### Pattern 10: Pick model tier by real-MCP benchmarks (MCP-Atlas / MCPMark), not BFCL

BFCL v3 measures single-turn function-calling accuracy; winning it does not imply winning real MCP workflows. GLM-4.5 tops BFCL at 77.8% but scores only 15.6% on MCPMark Pass@1. Use MCP-Atlas + MCPMark for production tier decisions:

- **Quality-first MCP host** → Claude Opus 4.5 (62.3% MCP-Atlas).
- **Balanced cost/quality** → GPT-5 high (57.5% MCPMark) or Gemini 3 Pro (54.1% MCP-Atlas).
- **Budget executor under a stronger planner** → Claude Haiku 4.5, GPT-5 mini, or DeepSeek V3.2 thinking (36.8% MCPMark at ~$0.27/M input).

**Source:** https://scale.com/blog/open-sourcing-mcp-atlas; https://mcpmark.ai/leaderboard.

### Pattern 11: Disable parallel tool calls on known-buggy model/version pairs

A small but real list of pairs where parallel calls misbehave:

- `gpt-4.1-nano-2025-04-14` — duplicate-call bug; set `parallel_tool_calls: false`.
- Claude 3.5 on older SDKs — parallel results split across messages silently drop results; upgrade to current Anthropic SDK or disable parallel.
- Mistral Large for any workflow where ordering matters — parallel is default on; flip to `false` when steps must be sequential.
- Grok 4 — undocumented parallel semantics; ship with parallel off until you've measured it yourself.

**Source:** https://platform.openai.com/docs/guides/function-calling; vendor release notes and issue trackers.

### Pattern 12: Prefer built-in retry with explicit tool-call budget over model-driven retries

Models do not self-limit well when a tool returns an error: they will retry with the same arguments, or worse, invent new arguments that escalate damage. Implement a server-side retry/backoff policy on transient failures and return a terminal `isError: true` with clear guidance after N attempts, so the model does not keep calling. Pair with `references/patterns/error-handling.md` for error-shape details.

### Pattern 13: For schema polymorphism, prefer `action` enums over `oneOf`

Gemini, Mistral, Qwen, and Llama 4 all have weak or missing polymorphic-schema support. The Action-Routed Facade from `tool-design.md` Pattern 7 (combined CRUD) is the portable substitute for `oneOf` — one tool, one `action` enum, branch server-side. Keep `oneOf` only where you're OpenAI strict or DeepSeek exclusive.

---

## Cost Analysis: Reference Workloads

Workload assumptions: **20 active tools**, **10-step average conversation**, **30K static context** (system + tool definitions), **1K tool-result tokens per turn**, **2K output tokens per turn**, **10 sessions**. Prices from the master table. "Best cache" uses each provider's documented cache mechanics (Claude 1h prompt cache, OpenAI implicit cache, Gemini context cache, DeepSeek cache-hit pricing).

| Model | No caching | With best cache | Notes |
|---|---|---|---|
| Claude Sonnet 4.5 | ≈ $4.05 | ≈ $2.00 (1h tool-block cache saves ~$2.05) | Strongest when MCP surface is stable and session-bursty |
| Claude Opus 4.5 | ≈ $6.75 | ≈ $3.35 | Use when Opus-quality arbitration and 65–76% output compression pay for themselves |
| Claude Haiku 4.5 | ≈ $1.35 | ≈ $0.90 | Cheapest Anthropic route — ideal executor under an Opus planner |
| GPT-5 | ≈ $2.06 | ≈ $1.50 (implicit cache) | Very strong with freeform mode on code/DSL tools |
| GPT-5 mini | ≈ $0.41 | ≈ $0.30 | ~10× cheaper than GPT-5; useful as a default for non-critical sessions |
| Gemini 2.5 Pro | ≈ $2.06 | ≈ $1.30 (context cache ≥10 min) | Watch per-hour storage fee on long idle caches |
| Gemini 2.5 Flash | ≈ $0.51 | ≈ $0.35 | Cheapest top-tier, but accept 3.4% MCP-Atlas |
| DeepSeek V3.2 thinking | ≈ $0.34 | ≈ $0.22 | Best price/quality for single-turn-many-call idiom |
| Grok 4 | ≈ $4.05 | ≈ $2.75 | No public MCP benchmark — measure before committing |
| Llama 4 Maverick (Fireworks) | ≈ $0.23 | no standard cache | MCP-Atlas 0.8%, plan for heavy scaffolding |

Three concrete picks:

- **Cheap broad-MCP**: Gemini 2.5 Flash at ~$0.35 / 10-session — only if you can tolerate 3–9% MCP-Atlas pass rate and you've hard-flattened schemas.
- **Best quality/dollar for real MCP workflows**: GPT-5 + caching + freeform tool calling at ~$1.50 / 10-session with **57.5% MCPMark Pass@1**.
- **Best absolute quality**: Claude Opus 4.5 at ~$3.35 cached / 10-session with **62.3% MCP-Atlas**, amplified by the 65–76% output-token reduction over Sonnet 4.5.

---

## Quick Cross-Reference to Sibling Patterns

- **Tool count decisions, progressive discovery** → `references/patterns/progressive-discovery.md` and `references/decision-trees/tool-count.md` (now read together with Pattern 1 above).
- **Schema portability details** → `references/patterns/schema-design.md` Pattern 8, extended by Patterns 2, 6, and 13 above.
- **Context budget math** → `references/patterns/context-engineering.md` (the "old" per-model tool cliffs there are superseded by Patterns 1, 7, 8, and 9 above).
- **Error-shape guidance for retries** → `references/patterns/error-handling.md` referenced by Pattern 12.
- **Facade/action-routed tools** → `references/patterns/tool-design.md` Patterns 7 and 8 referenced by Pattern 13.

---

## Key Sources

- BFCL v3: https://gorilla.cs.berkeley.edu/leaderboard.html
- τ²-bench: https://taubench.com, https://hal.cs.princeton.edu/taubench_airline, https://artificialanalysis.ai/evaluations/tau2-bench, https://sierra.ai/blog/t-bench-leaderboard
- MCP-Atlas: https://scale.com/blog/open-sourcing-mcp-atlas (arxiv.org/abs/2602.00933)
- MCPMark: https://mcpmark.ai/leaderboard
- Anthropic parallel tools: https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use
- Anthropic prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic Opus 4.5 launch (2025-11-24): token-reduction numbers cited in-page
- OpenAI function calling: https://platform.openai.com/docs/guides/function-calling
- OpenAI structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- GPT-5 freeform tool calling (2025-08-22): https://devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/
- Gemini function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Gemini `anyOf` Zod bug: https://github.com/colinhacks/zod/issues/5807
- DeepSeek function calling: https://api-docs.deepseek.com/guides/function_calling
- Klavis AI 2025 analysis ("Function Calling and Agentic AI in 2025", 2025-10-25): https://klavis.ai
- Microsoft Research tool-space interference (2025-09-11): as cited by Klavis AI
- Chroma 2025 "Context Rot" study
- Glean Sonnet 4.5 efficiency measurements (2026-01-27)

All URLs and dated measurements retrieved on 2026-04-14.
