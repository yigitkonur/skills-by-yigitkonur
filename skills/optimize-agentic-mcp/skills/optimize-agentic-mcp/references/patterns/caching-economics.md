# Prompt Caching and MCP Cost Economics

11 patterns for driving per-turn MCP cost down 55-92% with provider-side prompt caching. The math is unambiguous once the prefix stays byte-identical; the hard part is keeping it that way across MCP tool edits, reconnects, and dynamic system prompts.

The sibling doc `context-engineering.md` covers tool-definition token budgets, tiered verbosity, and ANSI stripping. `session-and-state.md` covers application-level response caching (L1/L2/L3, Redis, ETag). `progressive-discovery.md` warns in one line that dynamic tool lists invalidate the cache. This file is the deep-dive on the **provider** cache: what each vendor charges, what invalidates it, and how to design MCP tool surfaces so the prefix stays stable.

---

## Per-Provider Mechanics Reference

The first decision is which cache surface you are optimizing against. Mins, TTLs, write premiums, and invalidation triggers differ materially across vendors.

| Dimension | Anthropic (docs.claude.com, 2026-04) | OpenAI (developers.openai.com, 2026-04) | Gemini API (ai.google.dev, 2026-03) | Vertex AI (cloud.google.com, 2026-04) | Bedrock (aws.amazon.com, 2026-01) |
|---|---|---|---|---|---|
| **Min prefix** | 1024 tok (Sonnet 4/4.5/3.7, Opus 4/4.1); 2048 tok (Sonnet 4.6, Haiku 3/3.5); 4096 tok (Opus 4.5/4.6, Haiku 4.5) | 1024 tok; cache hits accrue in 128-tok increments | 1024 tok (2.5 Flash, 3 Flash); 2048 tok (2.5 Pro implicit); 4096 tok (3 Pro Preview) | 2048 tok (2.0/2.5); 4096 tok (Gemini 3/3.1) | Inherits Anthropic mins for Claude models |
| **TTL options** | 5 min default (auto-refreshed on hit); 1 hour extended | In-memory 5-10 min inactivity (up to 1h); `prompt_cache_retention: "24h"` on gpt-5.x and gpt-4.1 | Default 1h; any custom TTL ≥ 1 min | ≥ 1 min, no upper bound for explicit caches; implicit deleted within 24h | 5 min default; 1 hour GA 2026-01-26 for Sonnet 4.5 / Haiku 4.5 / Opus 4.5 |
| **Write multiplier** | 5m: 1.25× input; 1h: 2.0× input | **No write premium** | Implicit: free. Explicit: standard input rate + hourly storage | Implicit: free; explicit: standard + per-minute storage | Same as Anthropic |
| **Read discount** | 0.1× (90% off) | ~0.5× on legacy GPT-4o / o-series; 0.1× (90%) on GPT-5.x per openai.com pricing 2026-04 | 2.5+: 0.1× (90%); 2.0: 0.25× (75%) | Matches Gemini API tier | Same as Anthropic |
| **Breakpoint limit** | Max 4 per request, `cache_control: {type:"ephemeral"}`; canonical prefix order `tools → system → messages`; 20-block lookback | Implicit; route hash derived from first ~256 tokens | Implicit + explicit `cachedContent` name; no hard block limit | Same as Gemini API | Inherits Anthropic |
| **Storage fee** | None | None | **$4.50 / 1M tok / hour** (2.5 Pro ≤200K); **$1.00 / 1M tok / hour** (2.5 Flash) | Hourly, prorated by minute for explicit caches; 0 for implicit | None |
| **Primary invalidators** | Tool-def change (name/desc/params); toggling `web_search`, `citations`, or `speed:"fast"`; adding/removing images; `tool_choice` change (messages only); extended-thinking setting change; any byte change at or before a breakpoint | Prefix change; tool list change; image/detail change; model or version change; inactivity; spillover above ~15 rpm at a single `prompt_cache_key` | Anything beyond `ttl` / `expire_time` updates is unsupported; implicit caches also require identical prefix + temporal locality | Same as Gemini API | Same as Anthropic |

Sources pulled 2026-04-14: [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing), [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Gemini caching](https://ai.google.dev/gemini-api/docs/caching), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Vertex context cache](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview), [Bedrock 1h caching GA](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-one-hour-duration-prompt-caching).

---

## Cost Math Worksheet — 20-Tool MCP Server, 10-Turn Agent Session

Reference workload for every finding: 20 MCP tools in the stable tool block, 10 agentic turns inside one TTL window, a 30K-token prefix (system prompt + tool definitions + shared CLAUDE.md), 2K output per turn, a tail user+assistant suffix that grows ~1.5K per turn to ~12K by turn 10.

### Turn-1 cache-miss row (one-off cost of seeding the cache)

| Provider / Model | Prefix cost | Cache-write premium | Output cost | Turn-1 total |
|---|---|---|---|---|
| Claude Sonnet 4.6 — 5m TTL | 30K × $3/M = $0.0900 | +25% of prefix = $0.0225 | 2K × $15/M = $0.0300 | **$0.143** |
| Claude Sonnet 4.6 — 1h TTL | $0.0900 | +100% = $0.0900 | $0.0300 | **$0.210** |
| Claude Opus 4.6 — 5m TTL | 30K × $5/M = $0.1500 | +$0.0375 | 2K × $25/M = $0.0500 | **$0.238** |
| GPT-5.4 (auto-cache) | 30K × $2.50/M = $0.0750 | $0 | 2K × $15/M = $0.0300 | **$0.105** |
| Gemini 2.5 Pro — explicit 1h | 30K × $1.25/M = $0.0375 | $0 (storage tracked separately) | 2K × $10/M = $0.0200 | **$0.058** + storage |

### Full 10-turn session totals (all cache hits inside one TTL window)

| Strategy | 10-turn total | Savings vs. no cache |
|---|---|---|
| Sonnet 4.6, no cache | ~$1.43 | baseline |
| **Sonnet 4.6, 5m cache** | **$0.575** | **−60%** |
| Sonnet 4.6, 1h cache | $0.642 | −55% |
| Opus 4.6, no cache | ~$2.30 | baseline |
| Opus 4.6, 5m cache | $0.958 | −58% |
| GPT-5.4, no cache | ~$1.15 | baseline |
| GPT-5.4, auto-cache | $0.510 | −56% |
| Gemini 2.5 Pro, no cache | ~$0.63 | baseline |
| Gemini 2.5 Pro, explicit 1h | $0.440 | −30% (storage dominates at 30K) |
| Gemini 2.5 Flash, explicit 1h | $0.087 | −50% |

The storage drag on Gemini 2.5 Pro at this prefix size is why explicit caching only pays off once the prefix is ≥ 100K tokens or reuse rate is high. See Pattern 4.

---

## Break-Even Analysis — How Many Reads Before a Write Pays Off

For multiplier-style pricing the formula is `N = (M − 1) / (1 − R)` where `M` is the write multiplier (expressed against the base input rate) and `R` is the read multiplier. `N` is the number of cache reads needed before the writer recoups the premium.

| Provider / TTL | M | R | Reads to break even |
|---|---|---|---|
| Anthropic 5m | 1.25 | 0.10 | 0.28 → pays off after **1 hit** |
| Anthropic 1h | 2.00 | 0.10 | 1.11 → pays off after **2 hits** (Anthropic docs state this exactly) |
| OpenAI auto-cache | 1.00 | 0.10 | 0 → **always a win** at ≥ 1024 tok |
| Gemini 2.5 implicit | 1.00 | 0.10 | 0 → **always a win** |
| Gemini 2.5 Pro explicit 1h (30K prefix) | 1.00 + storage | 0.10 | Storage dominates. 30K × $4.50/M/hr = $0.135/hr storage; each hit saves ~$0.0338. Break-even ≈ **4 hits/hour** |

Source: [oneuptime.com prompt caching analysis, 2026-02-17](https://oneuptime.com), Anthropic pricing docs, ai.google.dev/pricing 2026-04-14.

Practitioner reality check — Boris Cherny (Anthropic) on The Register, 2026-04-13: *"Prompt cache misses when using the 1M-token context window are expensive. If you leave your computer for over an hour and then continue a stale session, it's often a full cache miss."* Source: [theregister.com/2026/04/13/claude_code_cache_confusion](https://theregister.com/2026/04/13/claude_code_cache_confusion).

---

## Pattern 1: Freeze Tool Descriptions Before You Enable Caching

Any change to a tool name, description, JSON schema, or parameter list invalidates the cache for the entire block containing it — and because tool definitions live at the front of the canonical prefix (`tools → system → messages`), a single edit cascades forward and invalidates every block after it.

**Do:**
- Version MCP tool surfaces in the repo (e.g. `schema_version: 3` in server metadata) and freeze that version before the caching campaign starts.
- Audit every PR that touches tool files — treat a description tweak the same as a code change to a critical path. Require a release note entry for each.
- Ship schema changes as a coordinated roll: bump the version, rotate all callers, accept the one-time cache wipe.

**Don't:**
- A/B test tool descriptions in production by flipping the field per request.
- Normalize whitespace, re-order schema keys, or auto-format tool definitions on server startup — deterministic serialization is a correctness requirement once caching is on.
- Regenerate tool schemas from Pydantic / Zod models at request time if the generator is non-deterministic.

**Case evidence:** A single capitalization change ("senior" → "Senior") in a Claude Code system prompt invalidated 2,727 cached tokens (claudecodecamp.com, 2026-02-25).

---

## Pattern 2: Put Stable Content Before the Breakpoint, Volatile After

Anthropic allows 4 `cache_control` breakpoints and matches against a 20-block lookback window. The canonical order is `tools → system → messages`. Everything you want cached must sit at or before your last breakpoint; everything volatile must sit after.

**Target order for an MCP agent:**
1. System prompt (stable persona + product rules).
2. Tool block — static tools first, dynamic / subagent tools last.
3. Shared project context (CLAUDE.md / AGENTS.md / repo conventions).
4. [BREAKPOINT 1]
5. Conversation history (older than current turn).
6. [BREAKPOINT 2 — sliding window]
7. Current user query and any just-fetched tool results.

**Do:**
- Place the `cache_control` marker on the last static tool, not the first.
- Keep current tool results out of the prefix — they belong after the last breakpoint.
- Log prefix bytes per turn and alert if the running SHA of the first 30K tokens changes for non-release reasons.

**Don't:**
- Put "current date", request IDs, or user identifiers inside the system prompt block.
- Inline the latest retrieval chunk inside the cached prefix. It forces a fresh write every turn.

**Case evidence:** ProjectDiscovery moved volatile working memory out of the prefix and into a tail user message. Cache hit rate climbed from **7% to 84%** and the overall bill dropped **59%** ([projectdiscovery.io blog, 2026-04-10](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching)).

---

## Pattern 3: Never Renegotiate the MCP Tool List Mid-Session

Adding, removing, or re-ordering one tool rewrites the entire tools block, which forces a fresh cache write for the whole conversation. The progressive-discovery reference mentions this in a sentence; here is the full cost consequence.

**Do:**
- Register every tool at session start. If some tools are feature-flagged, register thin stubs with `defer_loading: true` — see Pattern 9.
- Use a stable, alphabetical or topological sort of tools so re-registration yields byte-identical output.
- If a tool must be hidden from the model mid-session, suppress it at the **routing layer**, not by unregistering.

**Don't:**
- Lazily attach MCP servers based on user intent detected at turn 3. That detonates turns 1-2 of cache.
- Trust that "removing one unused tool" is free — it relocates every subsequent tool's byte offset.

Claude Code forbids post-session tool registration precisely for this reason (claudecodecamp.com, 2026-02-25).

---

## Pattern 4: Match TTL to Content Lifetime, Not Convenience

Anthropic 5m is cheap (+25% write). Anthropic 1h is 8× the premium (+100%). Gemini explicit 1h has no write premium but charges hourly storage. Picking the right TTL per block matters more than picking the right TTL overall.

**Do:**
- Use **1h TTL** only for genuinely static content: system prompt + tool block + shared project context. Those rarely change within an hour.
- Use **5m TTL** for the sliding conversation window. Agent loops usually tick in seconds.
- Respect the 4-breakpoint cap: BP1 on the last static tool (1h), BP2 on the last turn of prior conversation (5m). Don't stack more than you need.
- For Gemini 2.5 Pro explicit caches, only enable when prefix ≥ 100K tokens **or** when hit rate exceeds 4/hour per the break-even table above.

**Don't:**
- Put the conversation history on a 1h TTL. You'll pay the 2× premium for a block that rewrites every 2-3 minutes.
- Assume vendor-side default TTL is stable — monitor the ratio (see Pattern 11).

---

## Pattern 5: Eliminate Every Byte-Varying Element From the Cacheable Prefix

Silent invalidators kill more cache than explicit API changes. The top offenders: datetime strings, request IDs, user IDs, and non-deterministic schema serialization.

**Do:**
- Freeze the current date **once per task** and format as `YYYY-MM-DD`, not `ISO 8601` with seconds.
- Render system prompts from templates with stable placeholders — if the template interpolates the user's name inside the prefix, move the name into the first user message instead.
- Canonicalize CLAUDE.md / AGENTS.md / tool lists in a deterministic order at the server boundary (sort keys, strip trailing whitespace).
- If you must embed per-user context, put it in the tail message, not the cached prefix.

**Don't:**
- Include build SHA, deploy timestamp, or server hostname in the system prompt.
- Let the agent's own "Current time: ..." preamble land before the breakpoint.
- Trust `JSON.stringify` object key ordering — older V8 and Python dict iteration differ between runs.

ProjectDiscovery explicitly called out "freezing datetime to date-only" as one of the five changes that lifted their cache hit rate from 7% to 84%.

---

## Pattern 6: Pin One Provider Route Per Session

Caches are per-model **and** per-provider region. Switching from Anthropic Direct to Bedrock mid-session — even for the same Claude model — is a guaranteed 0% hit rate on the new route.

**Do:**
- Route all traffic for a given session to one provider, one region, one model ID.
- Reserve alternate routes (Bedrock, Vertex, fallback regions) strictly for outage failover.
- If you must support multi-region for latency, shard users by region at signup — not per request.
- Treat "switching to a cheaper model" (Haiku instead of Sonnet) as a cache wipe. Do it at session boundaries only.

**Don't:**
- Load-balance requests round-robin across Anthropic Direct + Bedrock. You pay the 5m write premium on every route flip.
- A/B test model versions within a single session.

ProjectDiscovery pins Anthropic Direct first and only falls back to Bedrock/Vertex during outages, which is what kept their hit rate steady during the 1M-context rollout.

---

## Pattern 7: Treat Tool Results as a Separate Cache Problem

Prompt caching saves on the 30K fixed prefix. It does not dedup repeated tool results across turns — the model still spends input tokens reading the same repository file every time it asks for it. That is a separate, compounding cost.

**Do:**
- Return stable URIs via MCP Resources (timkellogg.me, 2025-06-05) so the client can dedup across turns. A resource reference is a few tokens; the resolved content lives outside the prompt window on clients that support it.
- Pair a Redis / Durable Object / in-memory result cache keyed by `hash(tool_name + sorted(args))`. See `session-and-state.md` for the L1/L2/L3 layering.
- For idempotent read tools (file read, search, metadata fetch), add a `cache_ttl` hint to the response so the client knows when it's safe to reuse.

**Don't:**
- Conflate provider prompt caching with application response caching. Both matter; they don't substitute.
- Ignore the tail — even with 90% off on the prefix, 10 turns of fat tool results can still dominate the bill.

---

## Pattern 8: Budget the 4-Breakpoint Cap Across Features, Not Data Types

Anthropic gives you 4 breakpoints per request. System prompt, parallel tool bundles, conversation chunks, extended-thinking blocks — every feature competes for the same slots.

**Do:**
- Plan the 4 slots as a feature-level budget. Typical allocation: BP1 system + tools (1h), BP2 prior conversation (5m), BP3 reserved for parallel tool call bundle, BP4 held for extended-thinking continuity.
- If extended thinking is enabled and you pass non-tool results during thinking, the API strips all previously-cached thinking blocks. Keep non-tool content out of thinking turns.
- Drop breakpoints you don't actively save on; an unused `cache_control` still counts against the 4.

**Don't:**
- Let the SDK sprinkle breakpoints automatically. Make placement explicit.
- Enable extended thinking and parallel tool use simultaneously without measuring — the two features fight for the cap.

---

## Pattern 9: Ship Thin Tool Stubs by Default, Hydrate Schemas on Demand

When you have 20+ MCP tools, the tool block alone can be 3-10K tokens. Sending a thin stub first and fetching full schemas on demand keeps the cached prefix small **and** keeps it byte-stable — as long as hydration happens through a message, not a tool edit.

**Do:**
- Register stubs like `{"name":"mcp__slack__read_channel","description":"Read messages from Slack","defer_loading":true}` — a few tokens each.
- Append the full JSON schema as a **user or assistant message** when the model asks for it. Messages sit after the breakpoint and don't invalidate cache.
- Combine with the `execute_code` pattern from `context-engineering.md` §2 — the model discovers tool schemas through code, not tool re-registration.

**Don't:**
- Load the schema back into the tool block after the model asks. That rewrites the prefix.
- Leave hydrated schemas in context after the call — they inflate the tail. Let the model discard them.

Claude Code's deferred-loading strategy is the canonical reference (claudecodecamp.com, 2026-02-25).

---

## Pattern 10: Monitor Cache Creation Ratios — Vendor Defaults Drift

Anthropic exposes both `cache_creation_input_tokens_5m` and `cache_creation_input_tokens_1h` in the usage response. The ratio of those two numbers is the single most useful signal that something has silently changed upstream.

**Do:**
- Log both counters per request alongside `cache_read_input_tokens`.
- Compute a rolling 7-day ratio of 1h-writes to 5m-writes, grouped by model. Alert when the ratio drops by more than 30% vs. trailing baseline.
- Expose the ratio on an internal dashboard next to per-model cost.
- Re-run the break-even math after any alert and confirm the route is still winning.

**Don't:**
- Trust that your SDK default TTL is the vendor default TTL.
- Assume the cost anomaly is your fault before checking the vendor's recent changelog.

**Case evidence:** Anthropic silently flipped Claude Code's default TTL from 1h to 5m around 2026-03-06. A developer filed [anthropics/claude-code #46829, 2026-04-12](https://github.com/anthropics/claude-code/issues/46829) after discovering 119,866 calls across two machines were overbilled: Sonnet 4.6 actual $5,561 vs. $4,612 on the intended 1h TTL (17.1% waste = $949), Opus 4.6 $9,269 vs. $7,687 (+$1,582). The Register covered the blowup the next day.

---

## Pattern 11: Pair Prompt Caching With Batch and Code-Execution for Compounding Wins

Prompt caching is multiplicative with other cost levers, not alternative to them. The largest documented savings stack at least two strategies on top of prompt caching.

**Do:**
- Compose prompt caching with Anthropic Message Batches — caching discounts apply to batch requests (llmindset.co.uk, 2024-10-15).
- Compose prompt caching with the code-execution pattern from `context-engineering.md` — the model uses `execute_code` to navigate tool indices without expanding the cached tool block.
- Compose prompt caching with response-level caching from `session-and-state.md` — prompt cache cuts prefix cost; response cache removes duplicate tool round-trips entirely.

**Don't:**
- Treat caching as a silver bullet. The 1M-context Claude Code sessions stay expensive on the first turn no matter what — only batch + cache + code-execution together keep long tasks affordable.

---

## Case Studies

Real numbers from published post-mortems. Use these as upper-bound references, not promises.

### Case 1 — ProjectDiscovery "Neo" agent: 7% → 84% hit rate, −59% cost

Five changes, compounding effect:
1. Relocated dynamic content from the system prompt into a tail user message.
2. Switched the system prompt + tool block to 1h TTL.
3. Froze datetime to `YYYY-MM-DD`.
4. Reordered tools so static tools come first; placed `cache_control` on the last static tool; dynamic subagent tools went after.
5. Pinned Anthropic Direct as the primary route.

Aggregate result: overall cost **−59%**; last 10 days **−70%**; 9.8B tokens served from cache. Complex tasks (20+ steps, 3.7M avg input tokens) hit 74% cache rates. Extreme tasks hit 91.8% on 67.5M tokens across 1,225 steps. Source: [projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching, 2026-04-10](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching).

### Case 2 — Bifrost "Code Mode" with 508 MCP tools: 92% cost reduction

Raw baseline: 508 MCP tools, 75.1M input tokens, **$377/run**. After switching to code-execution mode (no tool schemas sent; the model generates code against a lightweight tool index): 5.4M tokens, **$29/run**, 100% test pass. Savings scale with tool count: 96 tools → 58%, 251 tools → 84%, 508 tools → 92%. Source: [r/Anthropic thread, 2025-11](https://reddit.com/r/Anthropic/comments/1skmbyp).

### Case 3 — Claude Code practical session: 96% hit rate, ~80% cheaper

A 100-turn Opus coding session that would cost **$50–100** without caching runs at **$10–19** with caching on. Documented 96% cache hit rate. A single-case change ("senior" → "Senior") invalidated 2,727 cached tokens. Claude Code reuses ~18K tokens of prefix cache across compaction and fork operations. Source: [claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code, 2026-02-25](https://claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code).

### Case 4 — MCP caching SaaS rebuild: 73% per-analysis cost cut

Full stack: prompt caching + L1 in-memory + L2 Redis + data-type-specific TTLs (stock quote 300s, financials 86400s, SEC filings 604800s). Per-analysis API cost **$0.40 → $0.11 (−73%)**. At enterprise scale (1M requests/day) that's **$912,500/year saved**. Cache-hit latency 84ms; miss 256ms. Source: [medium.com/@parichay2406/advanced-caching-strategies-for-mcp-servers, 2025-10-14](https://medium.com/@parichay2406/advanced-caching-strategies-for-mcp-servers).

### Case 5 — Long-horizon agent benchmark (arXiv 2601.06007v2, 2026-01)

500 agent sessions × 10,000-token system prompts:

| Model | Cost savings | TTFT improvement |
|---|---|---|
| Claude Sonnet 4.5 | 78.5% | 22.9% |
| GPT-5.2 | 79.6% | 13.0% |
| GPT-4o | 45.9% | 30.9% |
| Gemini 2.5 Pro | 41.4% | 6.1% |

At 50K-token prompts: GPT-5.2 cuts cost from $0.253 → $0.029 (−89%); Sonnet 4.5 from $0.667 → $0.080 (−88%). At 500-token prompts (below the 1024-min floor), every provider showed a 10-18% TTFT **regression** — caching pays off only above the minimum prefix. Source: [arxiv.org/html/2601.06007v2, 2026-01](https://arxiv.org/html/2601.06007v2).

### Case 6 — Claude Code TTL regression: $2,531 overpaid across two machines

Anthropic silently flipped Claude Code's default TTL from 1h to 5m around 2026-03-06. Across 119,866 calls on two machines: Sonnet 4.6 actual $5,561 vs. $4,612 on 1h (+$949, 17.1% waste). Opus 4.6 $9,269 vs. $7,687 (+$1,582). Total: $2,531 overpaid in ~5 weeks. Takeaway: vendor-side TTL defaults are not stable — instrument the `cache_creation_input_tokens_5m` / `_1h` ratio per Pattern 10. Sources: [github.com/anthropics/claude-code/issues/46829, 2026-04-12](https://github.com/anthropics/claude-code/issues/46829); [theregister.com/2026/04/13/claude_code_cache_confusion](https://theregister.com/2026/04/13/claude_code_cache_confusion).

---

## Key Sources

- [Anthropic — Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — canonical rules, breakpoints, 20-block lookback
- [Anthropic — Pricing](https://platform.claude.com/docs/en/about-claude/pricing) — 2026-04
- [Anthropic news — Prompt caching GA](https://anthropic.com/news/prompt-caching) — 2024-08-14
- [Anthropic news — Message Batches API](https://anthropic.com/news/message-batches-api) — 2024-10-08
- [OpenAI — Prompt Caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) — auto-cache mechanics, `prompt_cache_key`
- [OpenAI pricing](https://openai.com/api/pricing) — 2026-04
- [Gemini API — Context Caching](https://ai.google.dev/gemini-api/docs/caching) — 2026-03-24
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) — 2026-04-14
- [Vertex AI — Context caching overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview) — 2026-04-10
- [Vertex AI blog — Context caching](https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-context-caching) — 2025-10-15
- [Google Developers — Gemini 2.5 implicit caching](https://developers.googleblog.com/gemini-2-5-models-now-support-implicit-caching) — 2025-05-08
- [AWS — Bedrock 1h caching GA](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-one-hour-duration-prompt-caching) — 2026-01-26
- [ProjectDiscovery — How we cut LLM cost with prompt caching](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching) — 2026-04-10
- [r/Anthropic — Code Mode with 508 MCP tools](https://reddit.com/r/Anthropic/comments/1skmbyp) — 2025-11
- [Claude Code Camp — How prompt caching works in Claude Code](https://claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code) — 2026-02-25
- [Advanced caching for MCP servers](https://medium.com/@parichay2406/advanced-caching-strategies-for-mcp-servers) — 2025-10-14
- [GitHub anthropics/claude-code #46829](https://github.com/anthropics/claude-code/issues/46829) — 2026-04-12
- [The Register — Claude Code cache confusion](https://theregister.com/2026/04/13/claude_code_cache_confusion) — 2026-04-13
- [arXiv 2601.06007v2 — Long-horizon agent caching](https://arxiv.org/html/2601.06007v2) — 2026-01
- [llmindset.co.uk — Batch + cache composability](https://llmindset.co.uk/posts/2024/10/anthropic-batch-pricing) — 2024-10-15
- [Tim Kellogg — MCP Resources and caching](https://timkellogg.me/blog/2025/06/05/mcp-resources) — 2025-06-05
- [oneuptime.com — Prompt caching break-even analysis](https://oneuptime.com) — 2026-02-17
