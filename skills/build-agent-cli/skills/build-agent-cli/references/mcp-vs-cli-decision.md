# MCP vs CLI Decision Guide

## 1. Executive Summary

**The answer is not MCP vs CLI — it's knowing when to use which.**

Most successful production setups use both strategically:
- **CLI** for dev workflows, one-shot operations, token efficiency
- **MCP** for enterprise governance, stateful sessions, multi-agent interop

---

## 2. Token Economics

| Scenario | MCP Tokens | CLI Tokens | Ratio |
|----------|-----------|-----------|-------|
| Simple "get repo info" | ~10,000 | ~200 | **50x** |
| Stack 4 MCP servers | ~150,000+ | ~800 | **187x** |
| Per query (amortized, 10+ queries) | ~880 | ~750 | 17% |

**Key Insight:** MCP token cost is paid once per session. After 8-10 queries, overhead amortizes. But with many tools (93 GitHub tools = 55k tokens), it's catastrophic.

**The Real Problem:** Bloated MCP servers, not the protocol itself.

---

## 3. Reliability Comparison

From production benchmarks:
- **CLI reliability:** 100% (75 runs)
- **MCP reliability:** 72% (28% failing/wrong results)

The gap comes from:
- Tool selection confusion with many options
- Schema parsing failures
- Connection stability issues

---

## 4. When CLI Wins

**One-shot stateless operations:**
- `git status`, `npm test`, `curl`, `jq`
- No schema loading, no connection overhead
- Direct output, no marshalling

**Token-constrained environments:**
- 50x cheaper for simple operations
- No ambient cost of tool definitions

**Known CLI tools:**
- LLMs trained on `gh`, `kubectl`, `aws`, `docker` man pages
- Native comprehension without schemas
- 50+ years of Unix composability

**High reliability requirements:**
- 100% vs 72% in benchmarks
- Process isolation (crash one ≠ crash all)
- Instant debugging (stderr visible)

---

## 5. When MCP Wins

**Stateful sessions:**
- Playwright browser automation (persistent browser, page context)
- Database connections (connection pools, transactions)
- OAuth token management (refresh, session continuity)

**Enterprise governance:**
- OAuth/OIDC flows with proper token handling
- Audit trails (structured logging of tool invocations)
- Scoped permissions (tool-level RBAC)
- Multi-tenant isolation

**Dynamic tool discovery:**
- Typed parameters with rich docstrings
- Structured JSON I/O parsed natively
- Registry-based server discovery

**Multi-agent interoperability:**
- Single protocol works with Claude, GPT, Gemini
- Standardized capability negotiation

---

## 6. Decision Tree

```
START: Do you need agent tooling?
│
├─→ Is it a one-shot, stateless operation?
│   ├─ YES → Use CLI
│   └─ NO → Continue
│
├─→ Does the tool require state between calls?
│   ├─ YES → Use MCP
│   └─ NO → Continue
│
├─→ Do you need enterprise governance?
│   │   (OAuth, audit trails, scoped permissions)
│   ├─ YES → Use MCP (with gateway)
│   └─ NO → Continue
│
├─→ Is this a known CLI tool with good LLM training?
│   │   (gh, kubectl, aws, docker, git, jq)
│   ├─ YES → Use CLI
│   └─ NO → Continue
│
├─→ Are you token-constrained?
│   ├─ YES → Use CLI or minimal MCP (5-10 tools max)
│   └─ NO → Continue
│
├─→ Do you need multi-agent interoperability?
│   ├─ YES → Use MCP
│   └─ NO → Use CLI or Skills
│
└─→ DEFAULT: Start with CLI, add MCP when you hit a wall
```

---

## 7. Hybrid Patterns

**MCP Server Wrapping CLI:**
```
Agent → MCP Server → CLI Wrapper → Tool
```

Benefits:
- CLI composability under MCP governance
- Restricted surface area
- Security boundary without shell access

**CLI with --mcp-server flag:**
```bash
# Use as CLI
mycli deploy --env prod

# Or as MCP server
mycli --mcp-server
```

Same tool, both interfaces.

**Progressive Tool Disclosure:**
1. Default: 5-10 core tools loaded
2. On-demand: Additional tools via `more_tools` call
3. Semantic router: Cheap LLM matches request to tool metadata

---

## 8. MCP Best Practices (When You Use It)

**Keep tools < 20 per server:**
- 93 tools = 55k tokens = context catastrophe
- Task-scoped servers (PR review: 5 tools, not 93)

**Use gateways for:**
- Dynamic filtering (only relevant tools reach context)
- Health checks and routing
- Audit logging
- Rate limiting

**Handle reliability:**
- Reconnection logic with state recovery
- Timeout handling
- Fallback to CLI on MCP failure

---

## 9. The Production Pattern

```
Main Orchestrator: MCP (5-10 tools max, gateway-filtered)
Sub-agents: CLI or Skills
Enterprise features: MCP gateway (auth, audit, rate limits)
Dev workflows: Pure CLI
```

---

## 10. Migration Paths

**CLI → MCP:**
1. Build CLI first (well-tested, reliable)
2. Add MCP wrapper when governance needed
3. Use `--mcp-server` flag pattern

**MCP → CLI:**
1. Identify high-frequency, stateless operations
2. Extract to CLI with same semantics
3. Keep MCP for stateful/governance operations

---

## 11. Summary Matrix

| Factor | CLI | MCP |
|--------|-----|-----|
| Token cost | Low | High (amortizes) |
| Reliability | 100% | ~72% |
| Stateful ops | No | Yes |
| Enterprise governance | Weak | Strong |
| LLM familiarity | High (trained) | Lower |
| Setup complexity | None | Server deployment |
| Debugging | Easy (stderr) | Complex (two processes) |
