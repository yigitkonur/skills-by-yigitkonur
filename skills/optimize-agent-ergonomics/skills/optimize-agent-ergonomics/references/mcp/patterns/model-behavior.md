# Model behavior — designing for the model behind the client

The same MCP server, called from the same client, behaves differently depending on which model the client routes to. Schema dialects, tool-call idioms, parallel-call semantics, and response budgets all vary. The CLIENT compatibility matrix in `client-compatibility.md` is one axis; this file is the other — the per-MODEL behavior the tool author should design for.

The headline rule: **design for the most permissive model, test on the most strict.** Most permissive = "Claude Sonnet 4.5 with full JSON Schema and 200K context." Most strict = "Gemini 2.5 with no `anyOf`, ≤3 nesting levels, ≤20 tools." A server that runs cleanly on both will run cleanly on everything in between.

Cross-link `client-compatibility.md` for the client-side matrix, `tools.md` for response shape, `schema-design.md` for input schema patterns, `caching-economics.md` for prompt-cache mechanics.

---

## The late-2025 / 2026 landscape

There is no single tool-use champion. Four leaderboards, four winners:

- **BFCL v3** (single-turn function-calling accuracy) — GLM-4.5 leads at 77.8%. Source: [gorilla.cs.berkeley.edu/leaderboard.html](https://gorilla.cs.berkeley.edu/leaderboard.html) (retrieved 2026-04-14).
- **MCP-Atlas** (real MCP workflow pass rate) — Claude Opus 4.5 leads at 62.3%. Source: [scale.com/blog/open-sourcing-mcp-atlas](https://scale.com/blog/open-sourcing-mcp-atlas).
- **MCPMark** (multi-step MCP Pass@1) — GPT-5 high leads at 57.5%. Source: [mcpmark.ai/leaderboard](https://mcpmark.ai/leaderboard).
- **τ²-bench telecom** is saturated at ~99% by GLM-4.7 and 5; no longer discriminates. Source: [artificialanalysis.ai/evaluations/tau2-bench](https://artificialanalysis.ai/evaluations/tau2-bench).

Three baseline facts to assume:

1. **OpenAI's own function-calling guide recommends ≤20 active tools.** Source: [platform.openai.com/docs/guides/function-calling](https://platform.openai.com/docs/guides/function-calling).
2. **Google's Gemini docs recommend 10–20 active tools.** Source: [ai.google.dev/gemini-api/docs/function-calling](https://ai.google.dev/gemini-api/docs/function-calling).
3. **Microsoft Research (2025-09)** measured up to 85% accuracy loss from tool-space interference at large surfaces; in a 1,312-tool corpus the top tool averaged 557,766 tokens of response, and 16 tools exceeded 128,000 tokens. Cited in Klavis AI 2025-10-25 analysis at [klavis.ai](https://klavis.ai).

The old "Claude can do 30, GPT 15–20, Gemini 10" rule of thumb is superseded by these numbers. Treat ≤20 as the cross-vendor cap.

---

## Claude — Anthropic's tendencies (Sonnet 4.5, Opus 4.5)

**Schema adherence is tight.** Claude reads the JSON Schema and tries hard to fill it correctly. Full JSON Schema features work — `oneOf`, `anyOf`, `allOf`, `$ref`, deeply nested objects, complex enums. Claude reads parameter `description` fields carefully — that's where you put format hints, examples, and edge-case warnings.

**Description reading is careful.** Claude weights description text disproportionately during tool selection. Front-load verb + resource in the first five words; descriptions over ~200 tokens cause Claude to call the tool *less* often. Cross-link `tools.md` § "Tool descriptions."

**Prefers structured content.** Claude handles `structuredContent` cleanly when paired with a text content block. Returns YAML or JSON in code blocks; doesn't lose the structure on copy.

**Parallel tool use is default-on for the 4.x family.** All `tool_result` blocks for a parallel batch must arrive in **one subsequent user message** — splitting them across messages is the #1 Claude parallel-call bug in the wild. Disable parallel calls when strict step-by-step is required: set `disable_parallel_tool_use: true` inside `tool_choice`.

**Prompt cache is the biggest cost lever.** Up to 4 cache breakpoints, 20-block lookback, 1-hour TTL at 2× base input on write and 10% of base on hit. Tool definitions (typically the largest repeating payload in an MCP session) belong in a cached block at the top of the prompt:

```python
messages = [
    {"role": "system", "content": [
        {"type": "text", "text": SYSTEM_PROMPT},
        {"type": "text",
         "text": TOOL_DEFINITIONS,
         "cache_control": {"type": "ephemeral", "ttl": "1h"}},
    ]},
    # ... per-request messages
]
```

Cross-link `caching-economics.md` for the full caching playbook.

**Output efficiency.** Opus 4.5 produces 65–76% fewer output tokens at equal quality vs Sonnet 4.5 (Anthropic 2025-11-24 launch post). For tool-heavy loops where the assistant emits long messages, Opus pays back its higher per-token price.

**Source:** [platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use); [platform.claude.com/docs/en/build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

---

## GPT — OpenAI's tendencies (GPT-5, GPT-4.1, o3, o4-mini)

**Two tool-calling modes.**

1. **Classic JSON tool calls**, optionally `strict: true`. Strict mode supports `oneOf`/`anyOf`/`allOf`/`$ref` but requires `additionalProperties: false` and every field listed in `required` (use a nullable type for optional fields).
2. **Freeform tool calling (GPT-5 only, 2025-08-22)** — raw text payloads, no JSON. Result returns via `function_call_output`. Use for shells, code, SQL, regex, DSLs — any input where JSON escaping is the wrong shape. Source: [devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling](https://devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/).

**Tool-chaining tendency.** GPT-5 is the strongest model on real MCP workflows (MCPMark 57.5% high) — willing to chain 8–12 calls on complex tasks. Pair with the `next_action` HATEOAS pattern from `agentic-patterns.md` for best results.

**Looser schema policing.** GPT models occasionally hallucinate parameter values or produce slightly off-spec JSON. Validate inputs strictly server-side; return structured errors rather than letting bad input crash the handler.

**Reasoning rounds-trip.** When models like o3, o4-mini return reasoning items alongside tool calls, those items must be passed back on the next request or behavior degrades. Don't strip them.

**Quirks.** `gpt-4.1-nano-2025-04-14` has a duplicate-call bug — set `parallel_tool_calls: false` for that specific model. OpenAI's own guidance: "aim for fewer than 20 functions at any one time."

**Source:** [platform.openai.com/docs/guides/function-calling](https://platform.openai.com/docs/guides/function-calling); [developers.openai.com/api/docs/guides/structured-outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

---

## Gemini — Google's tendencies (Gemini 2.5, 3 Pro)

**Schema dialect is restrictive.**

- **No `anyOf`** in function calling. Confirmed via [zod issue #5807](https://github.com/colinhacks/zod/issues/5807) (2026-03). Substitute `discriminatedUnion()` so Zod emits `oneOf`, which Gemini handles.
- **No `$ref`.** Inline the referenced schema.
- **API rejects "very large or deeply nested schemas"** — flatten to ≤3 levels, keep property names <20 chars.

**Tool count guidance: 10–20 active tools.** Microsoft Research's Composio flattening technique delivered +47% tool-calling improvement on Gemini at large surfaces. Cross-link `progressive-discovery.md` for tool-list filtering patterns.

**Context caching is unusual.** Priced per **hour of storage** ($4.50 per 1M tokens per hour on 2.5 Pro). Estimate storage-hours, not just read count. Cross-link `caching-economics.md`.

**MCP-Atlas: Gemini 3 Pro is competitive (54.1%)**; Gemini 2.5 Pro is poor (8.8%). When targeting Gemini, prefer 3 Pro; fall back to 2.5 Flash only when cost dominates and you accept low MCP pass rates.

```typescript
// Breaks on Gemini — z.union() emits anyOf
const breaks = z.object({
  target: z.union([
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});

// Works on Gemini — discriminatedUnion() emits oneOf
const works = z.object({
  target: z.discriminatedUnion("kind", [
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});
```

**Source:** [ai.google.dev/gemini-api/docs/function-calling](https://ai.google.dev/gemini-api/docs/function-calling).

---

## DeepSeek — V3, V3.2, R1

- **No published official chat template for tool use.** Fireworks reverse-engineered one (2025-02-14 blog) — pin a provider that uses a known template; don't roll your own.
- **DeepSeek's own docs:** weak at multi-turn function calling. Performs best with **one user message triggering multiple tool calls in a single assistant turn**. Source: [api-docs.deepseek.com/guides/function_calling](https://api-docs.deepseek.com/guides/function_calling).
- **R1-0528 (May 2025) shipped tool-calling fixes.** Use R1-0528 or newer; older R1 has material regressions.
- **JSON Schema support is the most generous after OpenAI strict** — `object`, `string`, `number`, `integer`, `boolean`, `array`, `enum`, `anyOf`, `$ref`, `$def` all work in strict mode.

Design implication: structure DeepSeek workflows as one-shot batch calls, not interleaved multi-turn dialogues.

---

## Llama 4 — Maverick, Scout

No first-party function-calling training. The ecosystem uses Hermes-style tags or host-provided adapters. **MCP-Atlas: 0.8% for Maverick** — the worst among frontier models. Plan for heavy scaffolding if Llama 4 is in your matrix:

- Explicit planner tool returning the workflow as structured guidance.
- Tightest possible tool shapes — `type/object/properties/required/string` only.
- Examples in every description.
- Action-routed enums instead of `oneOf`.

For most production MCP servers, treating Llama 4 as a poor citizen is the right call. When support is mandatory, pair with a stronger advisor model.

---

## Qwen 3 — Max, Coder-Plus

Native Hermes-style tool use; vLLM + Qwen-Agent emits multiple `tool_calls` in one assistant message. Tops BFCL v3 single-turn (aside from GLM) but falls off on multi-step MCP (Qwen3-Max 17.7% MCPMark). Schema-wise: `enum` is safe; `oneOf`/`anyOf`/`$ref` are not documented — assume unsupported.

---

## Mistral — Large 2

`parallel_tool_calls: true` is default; flip to `false` when steps must be sequential. Schema support is minimal: `type/object/properties/required/string` only — no `oneOf`/`anyOf`/`$ref`/`format`. Treat Mistral as an even more restrictive Gemini.

---

## Patterns that work across models vs patterns that don't

### Works everywhere

- **Action enum substitutes for polymorphism.** `action: "create" | "update" | "delete"` plus a generic `payload` object. Every model handles enum + record.
- **≤20 active tools.** Below the cross-vendor cap; no model degrades materially in this range.
- **≤3 schema nesting levels.** Even Gemini's restrictive parser accepts this.
- **Plain `properties`/`required`/`enum`/`description`.** The lowest common denominator JSON Schema. No polymorphic features.
- **Server-side validation.** Re-check every input. Models hallucinate; treat each tool call as adversarial input.
- **Text content block alongside `structuredContent`.** Clients and models disagree on rendering; the text block is the universal floor.
- **Action-routed facade tools.** One tool, an `action` enum, branch server-side. Substitutes for `oneOf` in input schemas.
- **Compact responses with `next_step` hints.** Every model benefits from response-encoded HATEOAS.

### Breaks somewhere

- **`anyOf` and `$ref`.** Breaks Gemini, Mistral, Llama 4, Qwen 3.
- **Deeply nested input schemas.** Breaks Gemini at >3 levels; degrades all models above ~5 levels.
- **20+ tools active simultaneously.** Up to 85% accuracy loss measured by Microsoft Research at large surfaces.
- **Tool responses >25,000 tokens.** Claude Code default cap; degrades all models above 50K; some studies show up to 91% performance loss.
- **Long descriptions (>200 tokens).** Claude calls the tool less often; other models read past the signal and emit hallucinated answers from description text.
- **Splitting parallel `tool_result` blocks across user messages.** Breaks Claude parallel-call tracking.
- **Multi-turn DeepSeek dialogues.** Use one-shot batch calls instead.
- **Skipping reasoning items round-trip on o3 / o4-mini.** Behavior degrades.

### Quick portability test

```typescript
function validateCrossModelSchema(schema: any): string[] {
  const issues: string[] = [];
  if (schema.anyOf) issues.push("anyOf: breaks Gemini, Mistral, Llama 4, Qwen 3");
  if (schema.$ref) issues.push("$ref: breaks Gemini, Mistral, Qwen 3");
  if (countNestingDepth(schema) > 3) issues.push("nesting >3: breaks Gemini");
  if (Array.isArray(schema.enum) && schema.enum.length > 20)
    issues.push("enum >20: degrades all non-Claude models");
  return issues;
}
```

Run this at server registration time. If any issue surfaces and the model matrix includes the affected vendor, refactor before shipping.

---

## Adjustment rules for MCP server authors

Concise, numbered. Each is a server-side decision the model behavior dictates.

**1. Cap active tools at ≤20 regardless of vendor.** Partition across scoped MCP servers; filter per request; advisor/executor split with a stronger model picking and a cheaper model executing.

**2. For Gemini, emit `oneOf` not `anyOf`, flatten nesting to ≤3.** Pre-process Zod with `discriminatedUnion`; refactor any `z.union()` into `z.discriminatedUnion("kind", [...])`.

**3. For Claude, batch all `tool_result` blocks into ONE user message and cache tool definitions on the 1h TTL.** ~83% input-cost reduction over a multi-turn session at typical sizes.

**4. For GPT-5 + non-JSON DSLs, switch to freeform tool calling.** Shells, SQL, regex, code, custom DSLs — JSON escaping is the wrong shape. Set classic strict mode for genuinely structured inputs.

**5. For DeepSeek, prefer one-shot multi-call over multi-turn.** Pin R1-0528 or newer; never pre-0528 R1.

**6. Treat `$ref`, `oneOf`/`anyOf`, recursive schemas as hostile terrain.** Author tools in lowest-common-denominator JSON Schema; opt into polymorphism only on OpenAI-only or DeepSeek-only paths.

**7. Cap individual tool responses at ≤25,000 tokens; trim chatty tools to ≤1,000.** Matches Claude Code default; paginate built-in; expose a `more` or `page` tool.

**8. Size tool-response caps against the actual context window.** GPT-5 400K, GPT-4o 128K, Qwen3 32K, Phi-4 16K. Short-context hosts need ≤5,000-token caps; document as a deployment constraint.

**9. Compact or prune tool-call history past ~50K input tokens.** Chroma's 2025 "Context Rot" study shows monotone degradation; keep last N raw, summarize older.

**10. Pick the model tier by real-MCP benchmarks (MCP-Atlas / MCPMark), not BFCL.** GLM-4.5 wins BFCL but scores 15.6% MCPMark.

**11. Disable parallel tool calls on known-buggy pairs.** `gpt-4.1-nano-2025-04-14`; older Claude 3.5 SDKs; Mistral when ordering matters; Grok 4 until measured.

**12. Server-side retry/backoff with explicit budget; terminal `isError: true` after N attempts.** Models do not self-limit — they retry with the same arguments or invent escalating ones.

**13. Prefer `action` enums over `oneOf` for schema polymorphism.** Portable across every vendor.

---

## Cross-references

- `client-compatibility.md` — the client-side compatibility matrix; this file is the model-side complement.
- `tools.md` — tool design, descriptions, response shapes; the design choices these patterns inform.
- `schema-design.md` — input schema details; lowest-common-denominator JSON Schema.
- `caching-economics.md` — provider-side caching mechanics (Claude 1h, OpenAI implicit, Gemini context cache).
- `agentic-patterns.md` — HATEOAS, parameter-dependency chains, server-enforced workflow stages.
- `progressive-discovery.md` — tool-list filtering to stay under the ≤20 cap on large surfaces.
- `error-handling.md` — terminal-error pattern that prevents model retry loops.
