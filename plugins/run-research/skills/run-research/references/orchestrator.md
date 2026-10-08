# Subagent-First Research & Parallel Evidence Lenses

Preserve the primary orchestrator's context window by delegating deep multi-dimensional research to isolated subagents. The primary agent coordinates, tests high-level hypotheses, and reconciles findings; subagents absorb the token-heavy scraping dumps, search retries, and iterative probe loops.

---

## 1. Why Subagent-First? (Context Hygiene)

Running 10 search queries, parsing 40+ lead snippets, and executing multiple `extract-evidence` calls generates tens of thousands of tokens of ephemeral noise. When done in the main orchestrator, this noise degrades subsequent reasoning, causes context truncation, and leads to review fatigue.

### The Two-Phase Decision Rule
1. **Quick Recon (Orchestrator):** The primary agent executes 1–2 rapid `web-search` queries to assess problem complexity, test vocabulary, and determine whether the question is narrow.
   - If narrow (single fact, known URL, or <3 queries needed): **Finish directly in the main context.**
   - If multi-faceted, contested, or requiring deep verification: **Fork immediately to subagents.**
2. **Subagent Delegation:** Delegate the deep research work to isolated subagents, each assigned an orthogonal evidence lens.

---

## 2. Hard Limits & Compute Hygiene

### A. The 3-Subagent Cap
- **Maximum 3 parallel subagents.**
- More than 3 subagents creates orchestration chaos, saturates MCP/browser tool concurrency, increases rate-limit failures, and fragments evidence.
- Split strictly by **orthogonal evidence lenses**, never by arbitrary report sections or synonymous query buckets.

### B. Model Selection & Reasoning Level
- **Use Mid-Tier Models:** Subagents should run on mid-tier models (e.g., Claude 3.5 Sonnet, Gemini Flash, GPT-4o-mini / balanced mid-weight).
- **Cap Reasoning Effort at Medium:** Do NOT run extreme/maximum reasoning models on subagents performing web search and evidence extraction. Burning high-tier reasoning tokens on reading SERP snippets or checking HTTP statuses is wasteful and slow.
- **Top-Tier Reserved for Orchestrator:** The top-tier model and deep reasoning should be reserved for the primary orchestrator, which reconciles cross-lens contradictions and performs the final synthesis.

---

## 3. Orthogonal Lens Partitioning

Never partition by document sections (e.g., "Introduction agent", "Conclusion agent") or by search keywords. Partition strictly by **independent authority classes and truth models**:

| Lens | Purpose & Primary Source Classes | Example Research Target |
|---|---|---|
| **Theoretical / Specifications** | Official docs, RFCs, formal proofs, academic papers, architecture specs | Core algorithms, mathematical bounds, supported features |
| **Empirical / Benchmarks** | Independent benchmark suites, comparative studies, reproducible evaluations | Real-world throughput, latency, accuracy, false positive rates |
| **Practitioner / Field Realities** | Production post-mortems, issue trackers, migration logs, Reddit/forum threads | Real-world failure modes, workarounds, operational debt, hidden costs |

---

## 4. Subagent Briefing Contract

Every subagent brief must be bounded, explicit, and self-contained. Include:

1. **Mandatory Skill Directive:** Explicitly instruct the subagent: *"You must use the `run-research` skill to conduct this research."*
2. **The Core Question & User Constraints:** The exact problem statement, version/freshness bounds, and known facts to skip.
3. **Assigned Lens & Boundaries:** Exactly which dimension this agent owns (and what adjacent domains it must ignore).
4. **Target Authority Classes:** Which sources to seek (e.g., academic arXiv/proceedings, official vendor docs, or GitHub issue discussions) and noise to reject (SEO blogs, content farms).
5. **Checkable Evidence Requirements:** 2–4 specific, falsifiable questions to answer.
6. **Zero-Hallucination & Anti-Slop Rules:** Citable findings must be backed by verified verbatim quotations and locators from `extract-evidence`. Search snippets are leads only.
7. **Resumable Extraction Directive:** The subagent must follow any `continuation.next_call` exactly in its own session until settled or its round budget ends.
8. **Compact Structured Return Shape:**
   - Summary of findings for its lens.
   - Verified quotations with exact URLs and block/line locators.
   - Genuine negative evidence (`not-found`) and blocked sources.
   - Identified internal contradictions or ambiguities.

---

## 5. Session Isolation & Context Boundaries

- **No Shared Session State:** MCP research ledgers and continuation checkpoints are isolated to each subagent's session. Do not attempt to pass an uncompleted continuation token from one subagent to another.
- **Subagents Absorb Scraping Noise:** Large markdown dumps, failed scrape retries (e.g. Scrape.do JS fallbacks), and raw SERP lists remain trapped inside the subagent's conversation.
- **Only Distilled Evidence Ascends:** The subagent returns only its structured final report (findings + citations) to the orchestrator.

---

## 6. Orchestrator Merge & Synthesis Protocol

When subagents report back:
1. **Deduplicate Sources:** Identify canonical sources referenced across multiple subagents.
2. **Surface Cross-Lens Contradictions:** Explicitly contrast findings where lenses diverge (e.g., vendor benchmark claims 99% accuracy, but academic study proves 61% false positive rate on ESL writers, and practitioner forums report widespread disabling of the tool).
3. **Validate Provenance:** Ensure every substantive assertion in the final synthesis links to a verified quotation and source URL provided by a subagent.
4. **Identify Critical Gaps:** If a high-priority question remains unanswered across all subagents, decide whether a single targeted follow-up query is needed or if the limitation should be reported.
5. **Write Unified Synthesis:** Deliver one cohesive, authoritative report that directly answers the user's initial objective.
