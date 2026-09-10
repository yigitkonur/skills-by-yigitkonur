# Research MCP Protocol for Sentry Stack Research

When initializing Sentry in an unfamiliar stack or architecture (Mode 1), use `research-mcp` (or fallback web search) to identify framework-specific patterns, transport caveats, and lifecycle hooks before writing configuration.

## Research Budget & Constraints

- **Maximum Keywords:** Dispatch a focused query batch of at most 20 keywords per research wave.
- **Tools:** Use `web-search` with targeted queries, then `extract-evidence` on authoritative documentation URLs.
- **Primary Target:** Official Sentry SDK docs (`docs.sentry.io`), GitHub repositories, or authoritative release notes.

## Protocol Steps

1. **Stack Identification:**
   Detect runtime, framework, and deployment topology from `package.json`, `go.mod`, `requirements.txt`, or Dockerfiles.

2. **Query Formulation:**
   Assemble a search query using up to 20 precise keywords combining:
   - Sentry SDK name / version (e.g. `@sentry/node`, `@sentry/nextjs`, `sentry-sdk`)
   - Framework / runtime (e.g. Fastify, Next.js App Router, Gin, Playwright)
   - Feature requirements (e.g. envelope tunnel, AsyncLocalStorage, trace propagation, CLI flush)

3. **Evidence Extraction:**
   - Verify SDK initialization signature (`Sentry.init(...)`).
   - Identify recommended transport or tunnel options (`tunnel: '/api/sentry-tunnel'`).
   - Identify context propagation helpers (e.g. `trace()`, `startSpan()`).
   - Check process exit requirements (e.g. `await Sentry.close(2000)` or `Sentry.flush(2000)`).

4. **Integration Blueprint:**
   Synthesize extracted evidence into the Mode 1 setup plan before generating code.
