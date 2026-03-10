---
name: run-research
description: Use skill if you are researching a coding task using Google, Reddit, page scraping, or deep structured synthesis via Research Powerpack MCP.
---

# Research Powerpack

## 1. Overview

This skill teaches an AI coding agent how to conduct systematic, multi-source research
using the Research Powerpack MCP server. It replaces ad-hoc, single-query searching with
structured workflows that produce verified, nuanced, and actionable results.

**What this skill does:**
- Maps any coding research task to the correct combination of 5 specialized tools
- Provides workflow patterns that layer tools for depth and cross-validation
- Routes 95 use cases across 10 categories to detailed reference files
- Eliminates the most common research anti-patterns agents fall into

**When to use it:**
- Any coding task that requires knowledge beyond your training data
- Bug fixes where the error message is unfamiliar or ambiguous
- Architecture and design decisions that need community validation
- Library selection, migration planning, and compatibility checks
- Performance investigations, security audits, and DevOps configuration
- Any question where the answer could be outdated, contested, or context-dependent

**The core insight:**
No single tool is sufficient. `search_google` gives you breadth but not content.
`deep_research` gives you synthesis but can hallucinate sources. `search_reddit` gives
you practitioner signal but with survivorship bias. The power comes from layering:
use one tool to generate leads, another to extract content, and a third to validate
claims. Every research workflow in this guide uses at least 2-3 tools in sequence.

**What this skill does NOT do:**
- It does not contain the full details for all 95 use cases. Those live in the
  `references/` directory. This file is the routing layer and methodology guide.
- It does not replace reading official documentation. It helps you find and extract
  the right parts of official documentation faster.

---

## 2. The Five Tools — Quick Reference

### Tool Summary Table

| Tool | Purpose | Input | Output | When to Use |
|---|---|---|---|---|
| `search_google` | Breadth-first discovery | 3-100 keywords | URLs only (10 per keyword) | Usually first. Find where answers live. |
| `search_reddit` | Community signal | 3-50 queries | Post titles + URLs | Find practitioner experiences, warnings, regrets. |
| `fetch_reddit` | Deep opinion mining | 2-50 URLs | Full post + comment threads | Extract exact recommendations, code, config values. |
| `deep_research` | Structured synthesis | 1-10 questions | 32K tokens of analysis | Complex questions needing multi-angle analysis. |
| `scrape_pages` | Content extraction | 1-50 URLs | Structured page content | Get actual content from URLs found by other tools. |

### Tool Details

**search_google** — The starting point for most web research workflows.
- Runs 3-100 parallel Google searches. Recommended: 5-7 keywords.
- Returns ~10 URLs per keyword. 7 keywords = 70 candidate URLs.
- CRITICAL: Returns URLs only, never content. You MUST follow up with `scrape_pages`.
- Supports operators: `site:`, `"exact phrase"`, `-exclude`, `filetype:`, `OR`.
- Each keyword must target a different angle. Never repeat the same query reworded.

**search_reddit** — The community pulse check.
- Runs 3-50 parallel Reddit searches. Recommended: 5-7 queries.
- Returns post titles and URLs sorted by relevance.
- Supports subreddit targeting: include `r/rust`, `r/typescript` in queries.
- Supports operators: `intitle:`, `"exact"`, `OR`, `-exclude`.
- Best for: finding real-world war stories, failure modes, and migration regrets.

**fetch_reddit** — The opinion deep dive.
- Fetches full post and comment threads from 2-50 Reddit URLs.
- Auto-allocates comment budget: 1000 total (2 posts = 500 each, 10 = 100 each).
- Set `use_llm=false` to preserve exact quotes, code, version numbers, and config values.
- Set `use_llm=true` only when synthesizing many posts and the user explicitly wants a summary.
- Best for: extracting specific numbers, config snippets, and dissenting opinions.

**deep_research** — The structured analyst.
- Runs 2-10 parallel research questions. 32K token budget split across questions.
- 2 questions = 16K tokens each (deep). 5 questions = 6.4K each (balanced).
- MUST use the structured template (Section 5 details this).
- MUST attach relevant code files for bug/code questions, or answers will be generic.
- Best for: architecture decisions, complex debugging, technology evaluation.

**scrape_pages** — The content extractor.
- Scrapes 1-50 URLs with AI extraction. Recommended: 3-5 URLs.
- 32K token budget: 3 URLs = 10K each, 5 = 6K each, 10 = 3K each.
- Use pipe-separated extraction targets: `"pricing|features|limits|auth|rate-limits"`.
- Default `use_llm=true` strips navigation, ads, footers and returns the requested content.
- Best for: extracting structured data from docs, pricing pages, and GitHub READMEs.

---

## 3. Research Workflow Patterns

These three patterns cover 90% of coding research tasks. Pick the one that matches
your situation, then adapt as needed.

### Pattern A: Bug Fix Research (most common)

Use when: runtime error, compiler error, crash, unexpected behavior, deprecation warning.

```
Step 1: search_google (5-7 keywords)
   - Exact error message in "quotes"
   - Error message + framework/language version
   - Error message + "fix" or "solution"
   - Error code (if any) + library name
   - Simplified error description without project-specific paths

Step 2: scrape_pages (top 3-5 URLs from Step 1)
   - Extract: "error cause | fix steps | code example | version affected | workarounds"

Step 3: search_reddit (3-5 queries)
   - "[error message]" in relevant subreddit
   - "[library] [symptom]" for broader matches
   - "[library] breaking change [version]" if version-related

Step 4: DONE for most bugs.
   If still unresolved → deep_research with the buggy code file attached.
```

**Total time: 3-4 tool calls. Covers: StackOverflow, GitHub Issues, blogs, Reddit.**

### Pattern B: Decision / Architecture Research (second most common)

Use when: choosing between options, designing a system, evaluating tradeoffs.

```
Step 1: deep_research (2-3 structured questions)
   - Use the full template (Section 5)
   - Attach relevant code files showing current architecture
   - Ask about tradeoffs, failure modes, and scaling concerns

Step 2: search_reddit (5-7 queries)
   - "[option A] vs [option B]" in relevant subreddits
   - "[option A] production experience"
   - "[option A] regret" or "switched from [option A]"
   - "best [category] for [your constraints]"

Step 3: fetch_reddit (5-7 best threads from Step 2)
   - use_llm=false to get raw opinions with exact reasoning
   - Look for dissenting comments and experience-based warnings

Step 4: search_google (3-5 queries for official sources)
   - Official benchmarks, documentation, migration guides
   - Site-targeted: site:docs.x.com, site:github.com/x

Step 5: scrape_pages (3-5 authoritative URLs from Step 4)
   - Extract: "features | limitations | pricing | compatibility | migration path"
```

**Total time: 5 tool calls. Covers: expert analysis, community validation, official docs.**

### Pattern C: Library / Dependency Research

Use when: evaluating a library, finding alternatives, checking maintenance health.

```
Step 1: search_google (5-7 queries)
   - "[lib A] vs [lib B] [year]"
   - "best [category] library [language] [year]"
   - "[lib] alternatives"
   - "[lib] benchmark" or "[lib] performance"
   - site:github.com "[lib]" stars

Step 2: search_reddit (5-7 queries)
   - "[lib] production experience" in language-specific subreddits
   - "[lib] problems" or "[lib] issues"
   - "switched from [lib]" or "migrated from [lib]"
   - "r/[language] [category] recommendation"

Step 3: scrape_pages (3-5 URLs)
   - GitHub repos: extract "stars | last commit | open issues | contributors"
   - Package pages: extract "downloads | version | dependencies | size"
   - Doc sites: extract "features | API surface | examples | limitations"

Step 4: deep_research (1-2 questions)
   - Synthesize all findings into a recommendation with your constraints
   - Attach your code to get integration-specific advice
```

**Total time: 4 tool calls. Covers: comparisons, community trust, maintenance health, fit.**

---

## 4. The Category Router

Use this table to route the user's task to the correct reference file and tool sequence.

| If the task involves... | Reference file | Primary tool flow |
|---|---|---|
| Runtime errors, compiler errors, crashes | `references/bug-fixing.md` | search_google -> scrape_pages -> search_reddit |
| Library selection, migration, compatibility | `references/library-research.md` | search_google -> search_reddit -> scrape_pages |
| System design, patterns, database choice | `references/architecture.md` | deep_research -> search_reddit -> fetch_reddit |
| Async, type systems, macros, FFI, idioms | `references/language-idioms.md` | search_google -> deep_research -> fetch_reddit |
| CI/CD, Docker, K8s, monitoring, infra | `references/devops.md` | search_google -> scrape_pages -> search_reddit |
| OWASP, auth, encryption, input validation | `references/security.md` | deep_research -> scrape_pages -> search_google |
| Profiling, query optimization, caching | `references/performance.md` | deep_research -> search_reddit -> scrape_pages |
| Third-party APIs, webhooks, OAuth, payments | `references/api-integration.md` | search_google -> scrape_pages -> deep_research |
| Test frameworks, mocking, E2E, load testing | `references/testing.md` | search_reddit -> deep_research -> search_google |
| Framework migration, SSR/SSG, accessibility | `references/frontend.md` | search_google -> search_reddit -> scrape_pages |

### Category Use Cases

**Bug Fixing** (`references/bug-fixing.md`)
- Decoding cryptic runtime errors and stack traces
- Resolving dependency conflicts and version mismatches
- Debugging memory leaks and resource exhaustion
- Fixing race conditions and concurrency bugs
- Handling deprecation warnings and breaking changes
- Diagnosing environment-specific failures (CI vs local, OS-specific)
- Fixing build and compilation errors
- Debugging network and timeout issues
- Resolving ORM and database driver errors
- Handling encoding, locale, and timezone bugs

**Library Research** (`references/library-research.md`)
- Evaluating competing libraries for the same task
- Checking library maintenance health and bus factor
- Planning major version migrations with breaking changes
- Assessing bundle size impact for frontend dependencies
- Verifying license compatibility for commercial projects
- Finding libraries that meet specific compliance requirements
- Comparing ORMs, HTTP clients, validators, and serializers
- Evaluating framework plugin and extension ecosystems
- Checking cross-platform and cross-runtime compatibility
- Assessing community size and support quality

**Architecture** (`references/architecture.md`)
- Choosing between monolith, microservices, and modular monolith
- Selecting databases for specific access patterns
- Designing event-driven and message-based systems
- Planning CQRS and event sourcing implementations
- Evaluating caching strategies and layers
- Designing multi-tenant systems
- Planning API versioning and evolution strategies
- Choosing between REST, GraphQL, gRPC, and tRPC
- Designing for horizontal scaling and sharding
- Evaluating serverless vs container-based architectures

**Language Idioms** (`references/language-idioms.md`)
- Understanding async patterns (promises, futures, goroutines, tokio)
- Navigating advanced type system features (generics, traits, HKTs)
- Using macros, metaprogramming, and code generation
- FFI and cross-language interop patterns
- Error handling idioms across languages
- Concurrency primitives and memory models
- Package and module system best practices
- Language-specific performance patterns
- Compiler/interpreter configuration and optimization flags
- Understanding borrow checkers, lifetimes, and ownership

**DevOps** (`references/devops.md`)
- Writing and debugging CI/CD pipelines (GitHub Actions, GitLab CI)
- Optimizing Docker images and multi-stage builds
- Configuring Kubernetes deployments, services, and ingress
- Setting up monitoring, alerting, and observability (Prometheus, Grafana)
- Managing infrastructure as code (Terraform, Pulumi, CDK)
- Configuring reverse proxies and load balancers (nginx, Caddy, Traefik)
- Managing secrets and environment configuration
- Setting up log aggregation and structured logging
- Planning deployment strategies (blue-green, canary, rolling)
- Debugging DNS, networking, and certificate issues

**Security** (`references/security.md`)
- Implementing authentication flows (OAuth2, OIDC, SAML, passkeys)
- Preventing OWASP Top 10 vulnerabilities
- Securing API endpoints and rate limiting
- Implementing encryption at rest and in transit
- Input validation and output encoding
- Configuring CSP, CORS, and security headers
- Managing secrets and credential rotation
- Auditing dependencies for known vulnerabilities
- Implementing RBAC and ABAC authorization models
- Securing file uploads and user-generated content

**Performance** (`references/performance.md`)
- Profiling CPU, memory, and I/O bottlenecks
- Optimizing database queries and indexes
- Implementing caching strategies (Redis, CDN, in-memory)
- Reducing bundle size and improving frontend load times
- Optimizing API response times and throughput
- Diagnosing and fixing N+1 query problems
- Connection pooling and resource management
- Lazy loading, pagination, and streaming patterns
- Memory leak detection and garbage collection tuning
- Load testing and capacity planning

**API Integration** (`references/api-integration.md`)
- Integrating payment processors (Stripe, PayPal, Square)
- Setting up OAuth2 flows with third-party providers
- Handling webhooks reliably (idempotency, retry, verification)
- Working with rate-limited APIs (backoff, queuing, caching)
- Integrating email services (SendGrid, SES, Postmark)
- Working with cloud storage APIs (S3, GCS, Azure Blob)
- Consuming GraphQL APIs from external services
- Handling API versioning and deprecation from providers
- Integrating search services (Algolia, Elasticsearch, Meilisearch)
- Setting up real-time integrations (WebSockets, SSE, polling)

**Testing** (`references/testing.md`)
- Choosing and configuring test frameworks
- Writing effective unit tests with proper isolation
- Mocking external services, databases, and APIs
- Setting up E2E testing (Playwright, Cypress, Selenium)
- Implementing contract testing for microservices
- Load testing and stress testing (k6, Artillery, Locust)
- Snapshot testing and visual regression testing
- Testing async code, timers, and event-driven systems
- Measuring and improving code coverage meaningfully
- Setting up test databases and fixtures

**Frontend** (`references/frontend.md`)
- Migrating between frontend frameworks or major versions
- Choosing between SSR, SSG, and CSR strategies
- Implementing accessibility (WCAG compliance, screen readers)
- Optimizing Core Web Vitals (LCP, FID, CLS)
- State management patterns and library selection
- Responsive design, mobile-first, and cross-browser issues
- Implementing design systems and component libraries
- Handling forms, validation, and complex user inputs
- Internationalization and localization (i18n/l10n)
- Progressive web apps and offline-first patterns

---

## 5. Tool Best Practices

### search_google

- **Minimum 3 queries, recommended 5-7.** Each query MUST target a different angle.
- **Always quote exact error messages** with `"double quotes"` to avoid partial matches.
- **Add the current year** for fast-moving ecosystems: `"Next.js middleware 2026"`.
- **Use `site:` for precision:** `site:github.com`, `site:stackoverflow.com`, `site:docs.rs`.
- **Cover 7 angles:** broad topic, specific technical term, problems/debugging, best practices,
  comparison (A vs B), tutorial/guide, advanced patterns.
- **NEVER stop at search_google.** It returns URLs, not content. Always follow with `scrape_pages`.
- **Use `-exclude` to filter noise:** `-site:pinterest.com -site:medium.com` for technical queries.

### search_reddit

- **Minimum 3 queries, recommended 5-7.** Each query targets a different facet.
- **Target specific subreddits:** Include `r/rust`, `r/typescript`, `r/devops` in queries.
- **Search for NEGATIVE signal:** `"regret"`, `"switched from"`, `"problems with"`, `"don't use"`,
  `"wish I had known"`. Negative experiences are more informative than praise.
- **Use `intitle:` for focused results:** `intitle:"postgres vs mysql" r/database`.
- **Search for failure modes,** not just success stories. "X broke in production" is gold.
- **Follow up** with `fetch_reddit` on the 5-7 highest-signal threads.
- **Use `date_after`** to filter for recent posts when technology changes rapidly.

### fetch_reddit

- **Always set `fetch_comments=true`.** Comments contain the best insights.
- **Default `use_llm=false` is correct** for most cases. Raw comments preserve exact quotes,
  code snippets, version numbers, and config values that LLM summarization loses.
- **Only use `use_llm=true`** when processing 20+ posts and the user explicitly wants synthesis.
- **Fetch 5-10 posts** for broad consensus (balanced depth). Fetch 2-3 for deep dives (max depth).
- **Read dissenting comments.** The second or third reply that disagrees with the top answer
  often contains crucial corrections, edge cases, or updated information.
- **Check comment timestamps.** A top-voted answer from 3 years ago may be outdated.

### deep_research

- **Always use the structured template.** Without it, answers are shallow and generic:
  ```
  WHAT I NEED: [clear goal]
  WHY: [decision or problem context]
  WHAT I KNOW: [current understanding — so research fills gaps, not basics]
  HOW I'LL USE: [implementation, debugging, architecture]
  SPECIFIC QUESTIONS: 1) ... 2) ... 3) ...
  PRIORITY SOURCES: [optional — preferred docs/sites]
  FOCUS: [optional — performance, security, simplicity]
  ```
- **Attach relevant code files.** This is MANDATORY for bug, performance, and code review
  questions. Without attached code, deep_research gives generic textbook answers.
- **Use 2-5 parallel questions** for comprehensive coverage. Each question should target a
  different facet of the problem.
- **State your constraints:** tech stack, team size, timeline, compliance requirements.
- **2 questions = deep dive (16K tokens each).** 5 questions = balanced. 10 = rapid scan.

### scrape_pages

- **Recommended 3-5 URLs** for balanced depth (6-10K tokens per URL).
- **Use pipe-separated extraction targets.** Be specific:
  - Good: `"pricing tiers | free tier limits | API rate limits | auth methods | SDKs"`
  - Bad: `"extract all pricing information"`
- **Default `use_llm=true`** for structured extraction. It strips nav bars, ads, footers.
- **Set `use_llm=false` only** when you need raw HTML for debugging layout or scraping issues.
- **3 URLs = deep extraction (10K each).** 10 URLs = balanced. 50 = scan mode (640 each).
- **Pair with search_google results.** The standard workflow is: search_google -> pick URLs -> scrape_pages.

---

## 6. Anti-Patterns

These are the most common mistakes agents make during research. Avoid all of them.

**Shallow Research (most common)**
- Using only `search_google` and stopping. You have URLs but no content and no validation.
  Fix: Always follow `search_google` with `scrape_pages`, and add `search_reddit` for validation.

**Generic Deep Research**
- Using `deep_research` without attaching code files. The answers will be textbook-generic.
  Fix: Always attach the relevant source files with descriptions of what to focus on.

**Single-Source Trust**
- Trusting a single Reddit comment or a single blog post as ground truth.
  Fix: Cross-validate with at least 2 sources. Check if the comment is recent and upvoted.

**URL Hoarding**
- Running `search_google` and collecting many URLs but never scraping any of them.
  Fix: Pick the top 3-5 most relevant URLs and run `scrape_pages` immediately.

**Vague Questions**
- Asking `deep_research` a vague question like "How do I set up auth?"
  Fix: Use the structured template. Specify your stack, constraints, and specific questions.

**Losing Exact Values**
- Using `fetch_reddit` with `use_llm=true` when you need exact config values or code.
  Fix: Keep `use_llm=false` (the default). Only use LLM synthesis for 20+ post overviews.

**Positive-Only Search Bias**
- Searching only for "best X" and "X tutorial" while ignoring failure signals.
  Fix: Always include negative queries: "problems with X", "X regret", "switched from X".

**Unverified Citations**
- Treating `deep_research` output as fully cited fact. It can hallucinate sources.
  Fix: When a claim matters, verify it by running `search_google` + `scrape_pages` on the source.

**Stale Information**
- Accepting answers without checking recency. A 2022 answer about a 2026 framework is risky.
  Fix: Add year to queries. Check `date_after` on Reddit. Verify against official changelogs.

**Over-Researching**
- Running all 5 tools for a simple factual question that `search_google` + `scrape_pages` answers.
  Fix: Match research depth to question complexity. Simple bug = Pattern A. Architecture = Pattern B.

---

## Quick Start

If you are an agent reading this for the first time:

1. **Identify the task category** using the router table in Section 4.
2. **Pick the workflow pattern** (A, B, or C) from Section 3.
3. **Open the reference file** listed in Section 4 for detailed use-case guidance.
4. **Follow the best practices** in Section 5 for each tool you invoke.
5. **Check yourself** against the anti-patterns in Section 6 before finishing.

For any research task, the minimum viable workflow is:
`search_google` (find URLs) -> `scrape_pages` (get content) -> validate with one more tool.

Never ship research based on a single tool's output.
