# Caching and economics

Two distinct cache surfaces meet in every MCP deployment: **provider-side prompt caching** (the tokens the model provider charges for) and **tool-level result caching** (the bytes your handler computes). They compose; they don't substitute. This file covers both. Sourced from `optimize-agentic-mcp/.../patterns/caching-economics.md`.

The math is unambiguous once the prefix stays byte-identical; the hard part is keeping it that way across MCP tool edits, reconnects, and dynamic system prompts. The hard part on the tool-result side is correct invalidation.

---

## Provider-side prompt caching — what each vendor charges

The first decision is which cache surface you are optimizing against. Mins, TTLs, write premiums, and invalidation triggers differ materially across vendors.

| Dimension | Anthropic (docs.claude.com, 2026-04) | OpenAI (developers.openai.com, 2026-04) | Gemini API (ai.google.dev, 2026-03) | Vertex AI (cloud.google.com, 2026-04) | Bedrock (aws.amazon.com, 2026-01) |
|---|---|---|---|---|---|
| **Min prefix** | 1024 tok (Sonnet 4/4.5/3.7, Opus 4/4.1); 2048 tok (Sonnet 4.6, Haiku 3/3.5); 4096 tok (Opus 4.5/4.6, Haiku 4.5) | 1024 tok; cache hits accrue in 128-tok increments | 1024 tok (2.5 Flash, 3 Flash); 2048 tok (2.5 Pro implicit); 4096 tok (3 Pro Preview) | 2048 tok (2.0/2.5); 4096 tok (Gemini 3/3.1) | Inherits Anthropic mins for Claude models |
| **TTL options** | 5 min default (auto-refreshed on hit); 1 hour extended | In-memory 5-10 min inactivity (up to 1h); `prompt_cache_retention: "24h"` on gpt-5.x and gpt-4.1 | Default 1h; any custom TTL ≥ 1 min | ≥ 1 min, no upper bound for explicit caches; implicit deleted within 24h | 5 min default; 1 hour GA 2026-01-26 for Sonnet 4.5 / Haiku 4.5 / Opus 4.5 |
| **Write multiplier** | 5m: 1.25× input; 1h: 2.0× input | **No write premium** | Implicit: free. Explicit: standard input rate + hourly storage | Implicit: free; explicit: standard + per-minute storage | Same as Anthropic |
| **Read discount** | 0.1× (90% off) | ~0.5× on legacy GPT-4o / o-series; 0.1× (90%) on GPT-5.x per openai.com pricing 2026-04 | 2.5+: 0.1× (90%); 2.0: 0.25× (75%) | Matches Gemini API tier | Same as Anthropic |
| **Breakpoint limit** | Max 4 per request, `cache_control: {type:"ephemeral"}`; canonical prefix order `tools → system → messages`; 20-block lookback | Implicit; route hash derived from first ~256 tokens | Implicit + explicit `cachedContent` name; no hard block limit | Same as Gemini API | Inherits Anthropic |
| **Storage fee** | None | None | $4.50 / 1M tok / hour (2.5 Pro ≤200K); $1.00 / 1M tok / hour (2.5 Flash) | Hourly, prorated by minute for explicit caches; 0 for implicit | None |
| **Primary invalidators** | Tool-def change (name/desc/params); toggling `web_search`, `citations`, or `speed:"fast"`; adding/removing images; `tool_choice` change (messages only); extended-thinking setting change; any byte change at or before a breakpoint | Prefix change; tool list change; image/detail change; model or version change; inactivity; spillover above ~15 rpm at a single `prompt_cache_key` | Anything beyond `ttl` / `expire_time` updates is unsupported; implicit caches require identical prefix + temporal locality | Same as Gemini API | Same as Anthropic |

Sources pulled 2026-04-14: Anthropic prompt caching (platform.claude.com/docs/en/build-with-claude/prompt-caching); Anthropic pricing; OpenAI prompt caching; Gemini caching; Gemini pricing; Vertex context cache; Bedrock 1h caching GA.

---

## Cost math — 20-tool MCP server, 10-turn agent session

Reference workload for every finding: 20 MCP tools in the stable tool block, 10 agentic turns inside one TTL window, a 30K-token prefix (system + tool definitions + shared CLAUDE.md), 2K output per turn, a tail user+assistant suffix that grows ~1.5K per turn to ~12K by turn 10.

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
| Sonnet 4.6, 5m cache | $0.575 | −60% |
| Sonnet 4.6, 1h cache | $0.642 | −55% |
| Opus 4.6, 5m cache | $0.958 | −58% |
| GPT-5.4, auto-cache | $0.510 | −56% |
| Gemini 2.5 Pro, explicit 1h | $0.440 | −30% (storage dominates at 30K) |
| Gemini 2.5 Flash, explicit 1h | $0.087 | −50% |

The storage drag on Gemini 2.5 Pro at this prefix size is why explicit caching only pays off once the prefix is ≥ 100K tokens or reuse rate is high.

### Break-even — how many reads before a write pays off

For multiplier-style pricing the formula is `N = (M − 1) / (1 − R)` where `M` is the write multiplier and `R` is the read multiplier.

| Provider / TTL | M | R | Reads to break even |
|---|---|---|---|
| Anthropic 5m | 1.25 | 0.10 | 0.28 → pays off after **1 hit** |
| Anthropic 1h | 2.00 | 0.10 | 1.11 → pays off after **2 hits** |
| OpenAI auto-cache | 1.00 | 0.10 | 0 → always a win at ≥ 1024 tok |
| Gemini 2.5 implicit | 1.00 | 0.10 | 0 → always a win |
| Gemini 2.5 Pro explicit 1h (30K prefix) | 1.00 + storage | 0.10 | Storage dominates. 30K × $4.50/M/hr = $0.135/hr; each hit saves ~$0.0338. Break-even ≈ **4 hits/hour** |

Boris Cherny (Anthropic) on The Register, 2026-04-13: *"Prompt cache misses when using the 1M-token context window are expensive. If you leave your computer for over an hour and then continue a stale session, it's often a full cache miss."*

---

## The cache-hit-rate metric

The single most useful operational signal. Compute it per session per model:

```
hit_rate = cache_read_input_tokens / (cache_read_input_tokens + cache_creation_input_tokens + non_cached_input_tokens)
```

Healthy ranges by workload (community telemetry, 2025-12 → 2026-04):

| Workload | Hit rate target |
|---|---|
| Long-horizon coding agent, stable tools | ≥ 80% |
| Research agent, 20+ tools | ≥ 70% |
| Customer-support bot | ≥ 60% |
| One-off Q&A | n/a (caching not worth the write premium) |

Anthropic exposes both `cache_creation_input_tokens_5m` and `cache_creation_input_tokens_1h`. The ratio is the canary that something silently changed upstream — Anthropic flipped Claude Code's default TTL from 1h to 5m around 2026-03-06; the ratio diverged before any user noticed the bill. Source: github.com/anthropics/claude-code/issues/46829 (2026-04-12); theregister.com/2026/04/13/claude_code_cache_confusion.

---

## Provider-side patterns

### Freeze tool descriptions before enabling caching

Any change to a tool name, description, JSON schema, or parameter list invalidates the cache for the entire block containing it — and because tool definitions live at the front of the canonical prefix (`tools → system → messages`), a single edit cascades forward and invalidates every block after it.

Do:

- Version MCP tool surfaces in the repo (e.g. `schema_version: 3` in server metadata) and freeze that version before the caching campaign starts.
- Audit every PR that touches tool files — treat a description tweak the same as a code change to a critical path.
- Ship schema changes as a coordinated roll: bump the version, rotate all callers, accept the one-time cache wipe.

Don't:

- A/B test tool descriptions in production by flipping the field per request.
- Normalize whitespace, re-order schema keys, or auto-format tool definitions on server startup — deterministic serialization is a correctness requirement once caching is on.
- Regenerate tool schemas from Pydantic / Zod models at request time if the generator is non-deterministic.

A single capitalization change ("senior" → "Senior") in a Claude Code system prompt invalidated 2,727 cached tokens (claudecodecamp.com, 2026-02-25).

### Stable-before-breakpoint, volatile-after

Anthropic allows 4 `cache_control` breakpoints and matches against a 20-block lookback window. Canonical order: `tools → system → messages`. Everything cached must sit at or before the last breakpoint; everything volatile must sit after.

Target order for an MCP agent:

1. System prompt (stable persona + product rules).
2. Tool block — static tools first, dynamic / subagent tools last.
3. Shared project context (CLAUDE.md / AGENTS.md / repo conventions).
4. [BREAKPOINT 1]
5. Conversation history (older than current turn).
6. [BREAKPOINT 2 — sliding window]
7. Current user query and any just-fetched tool results.

Do:

- Place the `cache_control` marker on the last static tool, not the first.
- Keep current tool results out of the prefix — they belong after the last breakpoint.
- Log prefix bytes per turn and alert if the running SHA of the first 30K tokens changes for non-release reasons.

Don't:

- Put "current date", request IDs, or user identifiers inside the system prompt block.
- Inline the latest retrieval chunk inside the cached prefix.

ProjectDiscovery moved volatile working memory out of the prefix and into a tail user message. Cache hit rate climbed from **7% to 84%** and the bill dropped **59%**. Source: projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching (2026-04-10).

### Never renegotiate the tool list mid-session

Adding, removing, or re-ordering one tool rewrites the entire tools block, which forces a fresh cache write for the whole conversation.

Do:

- Register every tool at session start. If some tools are feature-flagged, register thin stubs with `defer_loading: true`.
- Use a stable, alphabetical or topological sort so re-registration yields byte-identical output.
- If a tool must be hidden from the model mid-session, suppress it at the routing layer (FastMCP visibility transforms), not by unregistering. See `progressive-discovery.md` for the visibility patterns.

Don't:

- Lazily attach MCP servers based on user intent detected at turn 3.
- Trust that "removing one unused tool" is free — it relocates every subsequent tool's byte offset.

Claude Code forbids post-session tool registration precisely for this reason.

### Match TTL to content lifetime

Anthropic 5m is cheap (+25% write). Anthropic 1h is 8× the premium (+100%). Gemini explicit 1h has no write premium but charges hourly storage. Picking the right TTL per block matters more than picking the right TTL overall.

- Use 1h TTL only for genuinely static content: system prompt + tool block + shared project context.
- Use 5m TTL for the sliding conversation window.
- Respect the 4-breakpoint cap: BP1 on the last static tool (1h), BP2 on the last turn of prior conversation (5m).
- For Gemini 2.5 Pro explicit caches, only enable when prefix ≥ 100K tokens or hit rate exceeds 4/hour per the break-even table.

### Eliminate every byte-varying element from the prefix

Silent invalidators kill more cache than explicit API changes. Top offenders: datetime strings, request IDs, user IDs, and non-deterministic schema serialization.

- Freeze the current date once per task and format as `YYYY-MM-DD`, not ISO 8601 with seconds.
- Render system prompts from templates with stable placeholders. If a template interpolates the user's name inside the prefix, move the name into the first user message instead.
- Canonicalize CLAUDE.md / AGENTS.md / tool lists in a deterministic order at the server boundary (sort keys, strip trailing whitespace).
- Don't include build SHA, deploy timestamp, or server hostname in the system prompt.
- Don't trust `JSON.stringify` object key ordering — older V8 and Python dict iteration differ between runs.

### Pin one provider route per session

Caches are per-model **and** per-provider region. Switching from Anthropic Direct to Bedrock mid-session — even for the same Claude model — is a guaranteed 0% hit rate on the new route.

- Route all traffic for a given session to one provider, one region, one model ID.
- Reserve alternate routes (Bedrock, Vertex, fallback regions) for outage failover only.
- Treat "switching to a cheaper model" (Haiku instead of Sonnet) as a cache wipe. Do it at session boundaries only.

### Ship thin tool stubs, hydrate schemas on demand

When you have 20+ MCP tools, the tool block alone can be 3-10K tokens. Sending a thin stub first and fetching full schemas on demand keeps the cached prefix small **and** keeps it byte-stable — as long as hydration happens through a message, not a tool edit.

- Register stubs like `{"name":"mcp__slack__read_channel","description":"Read messages from Slack","defer_loading":true}` — a few tokens each.
- Append the full JSON schema as a user or assistant message when the model asks for it. Messages sit after the breakpoint and don't invalidate cache.
- Combine with `execute_code` patterns from `tools.md` § Expose a code execution sandbox — the model discovers tool schemas through code, not tool re-registration.

See `progressive-discovery.md` for the patterns that map onto this.

---

## Tool-level result caching — when safe, when not

Prompt caching saves on the 30K fixed prefix. It does not dedup repeated tool results across turns — the model still spends input tokens reading the same repository file every time it asks for it. Tool-level caching is the second cost lever.

### When tool-level caching is safe

The only safe target is **deterministic, idempotent reads with a stable cache key**.

| Tool kind | Cacheable? | TTL guidance |
|---|---|---|
| Static doc fetch (`get_methodology_v2`) | yes | hours / days |
| Cross-tenant config (`get_pricing_tiers`) | yes | minutes |
| Per-user current state (`get_my_open_tickets`) | yes, per-user key | seconds |
| Search across user-specific data | per-user key, with invalidation hook | seconds |
| Anything that writes (create, update, delete) | no | never |
| Anything where the model is reasoning over a "fresh" view | no | never |

Cache key shape:

```python
import hashlib, json

def cache_key(tool_name: str, args: dict, user_sub: str | None = None) -> str:
    payload = {
        "tool": tool_name,
        "args": dict(sorted(args.items())),
        "user": user_sub,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
```

Three layers in production:

| Layer | Where | Use |
|---|---|---|
| L1 | In-process (LRU) | Hot reads inside a single session |
| L2 | Redis / Memcached | Shared across processes; per-tenant; per-user |
| L3 | Application / DB | Long-lived; backs the L1/L2 layers; subject to invalidation |

The MCP caching SaaS rebuild documented per-analysis API cost dropping $0.40 → $0.11 (−73%) by combining L1 in-memory + L2 Redis + data-type-specific TTLs (stock quote 300s, financials 86400s, SEC filings 604800s). Source: medium.com/@parichay2406/advanced-caching-strategies-for-mcp-servers (2025-10-14).

### Invalidation — per-tool TTLs, headers, manual purge

Three invalidation strategies, in increasing strength:

1. **TTL.** The default. Pick a TTL based on staleness tolerance. `cache-control: max-age=300` for stock quotes; `max-age=86400` for product catalogs.
2. **Conditional-fetch headers.** Attach `etag` or `last_modified` to cached responses; the next handler can re-validate cheaply with `If-None-Match`.
3. **Manual purge.** Write tools that call `cache.invalidate(key)` after every write. Pair this with a tag-based purge so `update_user(id=42)` invalidates every cache entry tagged `user:42`.

Return the cache hint to the agent so the model knows the data is fresh:

```json
{
  "result": {"price": 187.42, "currency": "USD"},
  "_meta": {
    "cache": {
      "status": "hit",
      "fetched_at": "2026-05-08T12:00:00Z",
      "ttl_remaining_s": 287
    }
  }
}
```

### When NOT to cache

- Any write tool (create/update/delete) — caching the response means the next read reflects a stale state.
- Tools that depend on real-time external state (live stock quote, "is the user online right now?", "what's the build status?").
- Tools whose response includes timestamps or request IDs that vary every call (cache the underlying data, project the timestamps fresh).
- Tools where the user explicitly invoked "force refresh" — accept a `_no_cache: true` arg and bypass the layer.

---

## Bad-vs-good examples

### Bad — non-deterministic tool definition serialization

```python
# Different runs serialize the same Pydantic model with different key order.
# Each cold start invalidates the prompt cache.
@mcp.tool()
def search(query: str, filters: SearchFilters) -> dict:
    ...
```

The fix: normalize at the server boundary.

```python
# Pin a deterministic JSON serializer for tool schemas.
def emit_schema(model) -> dict:
    schema = model.schema()
    # canonicalize: sort keys, strip whitespace
    return json.loads(json.dumps(schema, sort_keys=True, separators=(",", ":")))
```

### Good — caching with explicit invalidation tags

```python
@mcp.tool()
async def get_user(user_id: str) -> dict:
    key = f"user:{user_id}"
    if cached := await redis.get(key):
        return {"user": json.loads(cached), "_meta": {"cache": "hit"}}
    user = await db.get_user(user_id)
    await redis.setex(key, ttl=300, value=json.dumps(user))
    await redis.sadd(f"tags:user:{user_id}", key)  # tag for batch purge
    return {"user": user, "_meta": {"cache": "miss"}}

@mcp.tool()
async def update_user(user_id: str, data: dict) -> dict:
    user = await db.update_user(user_id, data)
    # Purge every cache entry tagged for this user
    keys = await redis.smembers(f"tags:user:{user_id}")
    if keys:
        await redis.delete(*keys)
    await redis.delete(f"tags:user:{user_id}")
    return {"user": user}
```

### Bad — caching a write

```python
# Caching here corrupts the next read; multiple agents see the same stale outcome.
@cache(ttl=60)
async def create_invoice(...) -> dict:
    ...
```

Never cache writes. Cache only the reads downstream of the write, and purge them when the write completes.

---

## Compose with batch and code-execution

Prompt caching is multiplicative with other cost levers, not alternative to them. The largest documented savings stack at least two strategies on top of prompt caching.

- **Batch + cache.** Compose with Anthropic Message Batches — caching discounts apply to batch requests (llmindset.co.uk, 2024-10-15).
- **Cache + code-execution.** Compose with the `execute_code` pattern from `tools.md` — the model uses code to navigate tool indices without expanding the cached tool block. Bifrost's "Code Mode" with 508 MCP tools went from $377/run to $29/run (92% savings) by switching tool dispatch into a single code-execution tool. Source: r/Anthropic (2025-11).
- **Prompt cache + response cache.** Prompt cache cuts prefix cost; tool-level response cache removes duplicate tool round-trips entirely.

---

## Cross-references

- `agentic-patterns.md` — multi-step workflows where caching pays the most
- `progressive-discovery.md` — thin stubs and visibility transforms for cache stability
- `tools.md` — the `execute_code` pattern, response shapes that cache cleanly
- `session-and-state.md` — application-level response caching layers (L1/L2/L3)
- `transport-and-ops.md` — keeping stdout pure so cache stays warm across reconnects
