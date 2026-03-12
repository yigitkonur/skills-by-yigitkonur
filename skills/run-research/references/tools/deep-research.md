# deep_research — Structured Synthesis Engine

## What It Does

Runs 2–10 parallel structured research questions with AI-powered analysis. Distributes a 32K token budget across questions. Each question receives multi-source synthesis — not just a search, but a comprehensive analysis with reasoning, evidence, and recommendations.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `questions` | `object[]` | Yes | — | 1–10 research questions. Each has a `question` string. |
| `questions[].question` | `string` | Yes | — | Structured research question (see template below). Min 10 chars. |
| `questions[].file_attachments` | `object[]` | No | — | Code files to attach for context. |
| `questions[].file_attachments[].path` | `string` | Yes | — | Absolute file path. |
| `questions[].file_attachments[].description` | `string` | No | — | What the file is and what to inspect. |
| `questions[].file_attachments[].start_line` | `int` | No | — | Start line (1-indexed). |
| `questions[].file_attachments[].end_line` | `int` | No | — | End line (1-indexed). |

## Token Budget

Total budget: 32K tokens distributed across questions.

| Questions | Tokens per Question | Depth Level |
|-----------|-------------------|-------------|
| 1 | 32,000 | Maximum — exhaustive single-topic analysis |
| 2 | 16,000 | Deep — comprehensive with full evidence |
| 3 | ~10,700 | Thorough — solid analysis with key evidence |
| 5 | 6,400 | Balanced — good coverage, selective evidence |
| 10 | 3,200 | Rapid scan — high-level answers, key points only |

**Recommendation:** 2–5 questions for most tasks. 2 for deep dives, 5 for multi-faceted analysis.

## The Structured Question Template

This template is MANDATORY for high-quality results. Without it, answers are shallow and generic.

```
GOAL: [What you need to accomplish — clear, specific]
WHY: [Decision context — what problem are you solving?]
KNOWN: [What you already know — so research fills gaps, not basics]
APPLY: [How you'll use the answer — implementation, debugging, architecture]
SPECIFIC QUESTIONS:
1) [Precise question targeting a specific aspect]
2) [Another angle or facet]
3) [A third dimension — failure modes, alternatives, edge cases]
PREFERRED SOURCES: [Optional — specific docs, sites, standards]
FOCUS: [Optional — performance, security, simplicity, cost]
```

### Why Each Section Matters

| Section | Without It | With It |
|---------|-----------|---------|
| GOAL | Vague, unfocused response | Targeted, actionable analysis |
| WHY | Generic textbook answer | Context-specific recommendation |
| KNOWN | Wastes tokens on basics you know | Fills actual knowledge gaps |
| APPLY | Theoretical advice | Implementation-ready guidance |
| SPECIFIC QUESTIONS | Scattered coverage | Precise, structured analysis |
| PREFERRED SOURCES | Random source selection | Authoritative, relevant sources |
| FOCUS | Balanced but shallow | Deep on what matters most |

## When to Use

- Architecture decisions requiring multi-dimensional analysis
- Complex debugging that spans multiple systems or layers
- Technology evaluation with many trade-off dimensions
- Any question needing synthesis across multiple domains
- When you need reasoning, not just facts

## When NOT to Use

- Simple factual questions → `search_google` + `scrape_pages` is faster
- Finding a specific error fix → `search_google` first
- Getting community opinions → `search_reddit` + `fetch_reddit`
- When you already know the answer and just need confirmation
- Quick lookups (version numbers, API endpoints, config syntax)

## File Attachments: When and How

### When to Attach Files

File attachments are **MANDATORY** for these question types:
- Bug diagnosis or debugging
- Performance optimization
- Code review or architecture review
- Configuration consistency checks
- Migration planning with existing code

### How to Attach Files

```python
questions = [{
    "question": "GOAL: Diagnose why API response time degrades under load...",
    "file_attachments": [
        {
            "path": "/absolute/path/to/server.ts",
            "description": "Express server entry point — inspect middleware chain and DB connection handling",
            "start_line": 1,
            "end_line": 150
        },
        {
            "path": "/absolute/path/to/db.ts",
            "description": "Database connection pool configuration — check pool size and timeout settings"
        }
    ]
}]
```

### Attachment Best Practices

- Use `description` to tell deep_research what to focus on
- Use `start_line`/`end_line` to scope large files
- Attach 2–4 files maximum per question — more dilutes focus
- Include the file that contains the problem AND its dependencies
- For config issues, attach ALL config files (they interact)

## Composing with Other Tools

### deep_research First (Architecture/Design)

```
1. deep_research: 2-3 structured questions about trade-offs
2. search_reddit: Validate claims with practitioner experience
3. fetch_reddit: Deep dive into dissenting opinions
4. scrape_pages: Verify specific facts against official docs
```

Best when the question requires reasoning and synthesis before fact-gathering.

### deep_research Last (Bug Fixing)

```
1. search_google: Find candidate solutions
2. scrape_pages: Extract fix details
3. search_reddit: Check for edge cases
4. deep_research: Synthesize all findings with your code attached
```

Best when you have partial information and need integration.

### deep_research for Verification

```
1. search_reddit: Gather opinions
2. fetch_reddit: Extract specific claims
3. deep_research: Cross-reference claims with attached code
   "Which of these recommendations apply to MY codebase?"
```

## Failure Modes

| Failure | Symptoms | Fix |
|---------|----------|-----|
| Generic answers | Textbook content, no specificity | Use the structured template; attach code files |
| Hallucinated sources | Citations to non-existent papers or docs | Verify claims with search_google + scrape_pages |
| Shallow analysis | Surface-level answers for complex questions | Reduce question count (2 instead of 5) for deeper analysis |
| Missed context | Answer ignores your tech stack constraints | Add KNOWN and APPLY sections to template |
| Contradictory claims | Different parts of answer conflict | Ask follow-up with narrower focus |
| Token exhaustion | Truncated answers | Reduce question count or narrow scope |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|---------------|-----|
| Vague questions | "How do I set up auth?" → generic answer | Use structured template with constraints |
| No code attachments for bugs | Generic debugging advice, not specific to your code | Always attach relevant code files |
| 10 questions at once | 3.2K tokens each = surface-level answers | Use 2-5 questions for meaningful depth |
| Trusting all claims | deep_research can hallucinate sources | Verify key claims with search_google + scrape_pages |
| Asking what you already know | Wastes tokens on basics | Include KNOWN section to skip intro content |
| Using for simple lookups | Overkill for "what version supports X?" | Use search_google + scrape_pages instead |

## Question Examples

### Architecture Decision (2 questions, deep)

```python
questions = [
    {
        "question": """GOAL: Choose between PostgreSQL + TimescaleDB vs ClickHouse for IoT analytics.
WHY: Building SaaS ingesting 50K sensor readings/second, need sub-second dashboards.
KNOWN: PostgreSQL works for current 5K/s. TimescaleDB is a PG extension. ClickHouse is column-oriented.
APPLY: Must decide before next sprint. Team knows PostgreSQL, not ClickHouse.
SPECIFIC QUESTIONS:
1) Can TimescaleDB handle 50K inserts/sec with concurrent dashboard queries?
2) What is the real operational cost of ClickHouse vs staying in PostgreSQL ecosystem?
3) What happens at 500K/sec — which scales further?
FOCUS: Operational complexity and team ramp-up, not just benchmarks"""
    },
    {
        "question": """GOAL: Design the data retention and aggregation strategy for chosen DB.
WHY: Raw data at 50K/s = 4TB/day. Need hot/warm/cold tiers.
KNOWN: Most queries hit last 24h. Weekly reports need 90-day data. Compliance needs 7-year raw.
APPLY: Designing table partitioning and aggregation jobs.
SPECIFIC QUESTIONS:
1) Optimal partition interval for this write rate?
2) Continuous aggregation vs batch materialization?
3) Cold storage integration (S3/GCS) with query capability?"""
    }
]
```

### Bug Diagnosis (1 question, maximum depth)

```python
questions = [
    {
        "question": """GOAL: Diagnose intermittent 502 errors on Node.js API behind nginx.
WHY: 0.5% of requests return 502 under normal load. Increases to 5% during peaks.
KNOWN: nginx proxies to Node.js cluster (4 workers). Connection: keep-alive. No memory leaks detected.
APPLY: Need specific diagnostic steps and likely root causes for our setup.
SPECIFIC QUESTIONS:
1) What are the top 5 causes of intermittent 502 behind nginx + Node.js?
2) Which nginx and Node.js settings should I check first?
3) How to correlate nginx error logs with Node.js worker state?
4) Could keep-alive timeout mismatch between nginx and Node.js cause this?
FOCUS: Diagnostic methodology, not generic advice""",
        "file_attachments": [
            {"path": "/app/nginx.conf", "description": "nginx reverse proxy config"},
            {"path": "/app/server.ts", "description": "Express server with cluster setup"}
        ]
    }
]
```

## Key Insight

deep_research is your synthesis tool. It excels when the question has multiple dimensions, conflicting sources, or requires reasoning about trade-offs. The structured template isn't optional polish — it's the difference between a generic textbook answer and a specific, actionable analysis tailored to your situation. Always attach code when the question involves your codebase.

## Steering notes from production testing

### KNOWN field is the single biggest quality lever

**Bad:** `KNOWN: I need to choose a WebSocket library.`

**Good:** `KNOWN: Comparing Socket.io (14.2M npm downloads), Pusher ($49/mo starter), Ably (99.999% SLA). Next.js 15 App Router, Vercel hosting (serverless). Socket.io needs dedicated server (conflicts with serverless). Reddit reports Pusher rate limits at scale.`

### Hallucination risk areas

Verify these against scraped official docs: version numbers, pricing tiers, API signatures, deprecation status, performance benchmarks.

### Output structure

Typical sections: CURRENT STATE, KEY INSIGHTS, TRADE-OFFS, PRACTICAL IMPLICATIONS, WHAT'S CHANGING, Next Steps (tool suggestion -- follow skill workflow instead).

### Question count guidance

32K token budget split across questions. 1-2 focused questions with rich KNOWN produce better results than 5+ scattered questions.

### File attachment by task type

| Task type | Attach | Why |
|---|---|---|
| Bug fix | Error source file, stack trace, config | Code-specific diagnosis |
| Library choice | `package.json`, framework config | Stack constraints |
| Architecture | Design docs, deployment config | Constraint context |
| Performance | Profiler output, benchmark code | Targeted analysis |
| Security | Auth middleware, route handlers | Attack surface |
