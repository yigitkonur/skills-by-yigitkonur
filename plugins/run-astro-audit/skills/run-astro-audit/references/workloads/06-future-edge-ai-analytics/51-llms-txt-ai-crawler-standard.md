# Mission Brief: LLM Readiness & llms.txt / llms-full.txt Standard Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

Modern AI search engines and LLM agents (ChatGPT, Perplexity, Claude, Google Gemini) ingest site context directly via the emerging RFC standard `llms.txt` and `llms-full.txt`.
As a market leader in Generative Engine Optimization (GEO), The application must provide a structured, machine-readable summary of its core capabilities, services, research publications, and case studies at `public/llms.txt` and dynamic endpoints.

### Authoritative Astro Architectural & Best Practice Rules

- **APIRoute Signature & Standard Web Responses** — [`[03-apiroute-signature-and-web-response.md]`](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md): Dynamic LLM endpoints (`/llms-full.txt` or `/api/llm-manifest`) must strictly implement Astro's typed `APIRoute` contract (`export const GET: APIRoute`) and return standard Web API `Response` objects with explicit `Content-Type: text/plain; charset=utf-8`. Returning naked JS objects or importing proprietary Next.js wrappers (`NextResponse.json()`) throws fatal Astro runtime errors.
- **ClientRouter SPA Navigation Architecture** — [`[12-client-router-spa-navigation-architecture.md]`](../../best-practices/03-routing-and-pages/12-client-router-spa-navigation-architecture.md): Astro 5's `<ClientRouter />` intercepts internal `<a>` tags for SPA transitions. Dedicated raw endpoints (`/llms.txt`, `/llms-full.txt`) must bypass client routing with `data-astro-reload` or server-level routing rules to guarantee standard browser and crawler downloads without SPA DOM hijacking.
- **ClientRouter Lifecycle Events Sequence** — [`[13-client-router-lifecycle-events-sequence.md]`](../../best-practices/03-routing-and-pages/13-client-router-lifecycle-events-sequence.md): Understanding the 5-stage lifecycle sequence (`astro:before-preparation`, `astro:after-preparation`, `astro:before-swap`, `astro:after-swap`, `astro:page-load`) ensures that interactive documentation readers and AI manifest link checkers initialize cleanly without race conditions.
- **Custom DOM Swap and State Carryover on before-swap** — [`[18-custom-dom-swap-and-state-carryover-on-before-swap.md]`](../../best-practices/03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap.md): Direct text/crawler manifests bypass DOM rendering, but any linked interactive previews or documentation readers must safely manage state carryover and avoid FOUC.
- **Leverage transition:persist for Persistent State** — [`[08-leverage-transition-persist-for-persistent-state.md]`](../../best-practices/09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state.md): Interactive AI console demonstrators, audio narration players, or streaming markdown previewers embedded across documentation must leverage `transition:persist="player"` to prevent unmounting and audio stutter across client navigations.

Key Astro Best Practice contracts for AI ingestion endpoints:

1. **Endpoint Prerender Boundary**: Static files live under `public/`, but on-demand/dynamic feeds must declare `export const prerender = false;` to allow live updates without full site rebuilds.
2. **APIRoute Signature & Standard Web Responses**: Dynamic LLM endpoints must use Astro's `APIRoute` contract and return a standard Web API `Response` with explicit `Content-Type: text/plain; charset=utf-8`.
3. **ReadableStream for Massive Full-Text Feeds**: For `/llms-full.txt` (which aggregates all research articles and services into a multi-megabyte corpus), never buffer the entire text in memory. Construct a standard Web API `ReadableStream` with `TextEncoder` to stream chunks incrementally, preventing memory crashes on Cloudflare Workers.
4. **Header Immutability at Route Root**: Cache-Control and Content-Type headers must be set at the root of the endpoint handler before streaming commences.

Critical files to inspect:

- `public/llms.txt` (RFC-standard AI crawler entrypoint)
- `public/robots.txt` (crawler permissions and sitemap declarations)
- `src/pages/llms.txt.ts` or `src/pages/llms-full.txt.ts` (dynamic aggregation feeds)
- `src/lib/routes/public.ts`
- `edge/policy/runtime-routes.mjs`
- `src/worker.ts`

## 3.2 Mission Objective

Audit and design the LLM ingestion architecture across the site.
Outcome: Ensure `/llms.txt` and `/llms-full.txt` exist, follow the llmstxt.org specification, provide a clean Markdown table of contents for AI agents with links to canonical service and research pages, and serve with correct `text/plain; charset=utf-8` headers with zero memory buffering.
Constraints: Read-only audit; verify content curation for AI agents and endpoint streaming contracts.
Autonomy Grant: You own this mission end-to-end. Structure the LLM ontology, curated links, and markdown summary blocks. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Check if `public/llms.txt` exists; if not, design its schema following llmstxt.org specification.
2. Ensure `llms.txt` highlights The project's 7 core services, 238 customer references, and key research articles.
3. Verify that `robots.txt` does not block verified search AI crawlers (GPTBot, ClaudeBot, PerplexityBot).
4. Audit endpoint streaming architecture against anti-patterns and Next.js legacy migrations:

### Comparison 1: Memory Buffering & Framework Wrappers vs. Web API Streaming

❌ Bad Practice: Memory buffering entire corpus or importing proprietary Next.js / Node response wrappers:

```ts
// src/pages/llms-full.txt.ts
import type { APIRoute } from 'astro'

// ❌ Missing export const prerender = false; in dynamic mode
export const GET: APIRoute = async () => {
  const articles = await getFullArticleCorpus()
  // ❌ Buffering tens of megabytes into memory stalls the event loop and risks Worker OOM:
  let fullText = '# The application Full Knowledge Base\n\n'
  for (const doc of articles) {
    fullText += `## ${doc.title}\n${doc.body}\n\n`
  }
  return new Response(fullText, {
    // ❌ Missing charset=utf-8 causes non-ASCII character corruption in LLM parsers
    headers: { 'Content-Type': 'text/plain' },
  })
}
```

✅ Best Practice: Using Astro `APIRoute` with standard Web API `ReadableStream` and chunked encoding:

```ts
// src/pages/llms-full.txt.ts
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async () => {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        controller.enqueue(encoder.encode('# The application Knowledge Base (llms-full.txt)\n\n'))
        for await (const chunk of streamKnowledgeBaseCorpus()) {
          controller.enqueue(encoder.encode(chunk))
        }
        controller.close()
      } catch (err) {
        controller.error(err)
      }
    },
  })

  return new Response(stream, {
    status: 200,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
    },
  })
}
```

### Comparison 2: Persistent Media & Island State Across Client Transitions

❌ Bad Practice: Storing persistent audio or video state in global React context that resets during client transitions:

```tsx
// src/components/PodcastPlayer.tsx
// ❌ FAILS: Re-mounted on every client transition, resetting playback and causing audio drops:
export function PodcastPlayer() {
  const { currentTrack, currentTime } = useAudioContext() // Resets on page transition
  return <audio src={currentTrack} autoPlay />
}
```

✅ Best Practice: Using `transition:persist="player"` to keep elements alive across DOM swaps:

```astro
---
// src/components/PodcastPlayer.astro
import AudioIsland from './AudioIsland.tsx';
---
<!-- ✅ Keeps audio playback element and state completely alive across SPA navigations -->
<div class="fixed bottom-0 w-full bg-slate-900" transition:persist="player" transition:persist-props>
  <AudioIsland client:load />
</div>
```

### Comparison 3: Content Negotiation Endpoints

❌ Bad Practice: Hand-rolling custom markdown negotiation in page frontmatter, creating duplicate endpoints:

```astro
---
// src/pages/services/[slug].astro
// ❌ FAILS: Checks accept header in frontmatter of HTML route, causing duplicate logic and edge cache bugs
const accept = Astro.request.headers.get("accept");
if (accept?.includes("text/markdown")) {
  return new Response(rawMarkdown); // Missing Vary: Accept, corrupts CDN cache!
}
---
```

✅ Best Practice: Inspecting `Accept: text/markdown` in middleware or APIRoute endpoints and streaming precomputed content:

```ts
// src/pages/api/content-negotiate.ts
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async ({ request, url }) => {
  const accept = request.headers.get('accept') ?? ''
  if (accept.includes('text/markdown')) {
    const markdownStream = await streamPrecomputedMarkdown(url.pathname)
    return new Response(markdownStream, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        Vary: 'Accept',
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      },
    })
  }
  return new Response(null, { status: 404 })
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 03-routing-and-pages/12-client-router-spa-navigation-architecture`, `RULE-ID: 03-routing-and-pages/13-client-router-lifecycle-events-sequence`, `RULE-ID: 03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap`, `RULE-ID: 09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "51-LLMS-TXT-AI-CRAWLER-STANDARD-001",
    "rule_id": "RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response",
    "file": "public/llms.txt",
    "line": 1,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "syntax" | "hydration" | "parity" | "performance" | "security",
    "defect": "Precise description of what is broken or violating invariants",
    "remediation": "Concrete, actionable instruction on how to fix it"
  }
]
```

2. **`evidence.md`**: Comprehensive investigative research log:
   - Full command outputs, vitest runs, grep matches, AST dumps.
   - Analysis of confirmed facts vs assumptions.
   - Step-by-step reproduction proof.

3. **`handoff.md`**: The executive, action-oriented implementation blueprint for the next subagent:
   - **Executive Summary:** Overall health of this domain (Clean / Minor Defects / Blockers).
   - **Architectural Invariants:** Rules that the fixing agent must NEVER violate while remediating.
   - **Step-by-Step Remediation Checklist:** Prioritized action items (ordered from highest to lowest severity).
   - **Exact Code Replacements:** File paths, line numbers, current faulty snippet, and drop-in replacement snippet.
   - **Verification Battery:** The exact commands the fixing agent must run post-remediation to prove 100% success.

4. **`issue-body.md`**: The publication-ready GitHub Issue markdown body adhering to the two-tier structure:
   - **Checklist Header**: The verified nested checklist of up to 200 items (3 levels max).
   - **Outer Tier (localized primary locale)**: Conversational human summary (1-2 sentences), affected URLs/routes table, surface area table (viewports, themes, components), observed defect vs expected behavior (WITHOUT prescribing code fixes).
   - **Inner Tier (English `<details>`)**: Collapsed block titled `<details><summary><strong>Agent implementation brief — scope, source map, behavior contracts, and verification</strong></summary>...</details>`. Contains exact `file:line` citations, quoted 3-8 lines of code, defect classification (`bug` | `by-design` | `drift` | `reversal`), required behavioral invariants, known traps, acceptance checklist, and embeds the structured `findings.json` table and `handoff.md` remediation steps.

5. **Publication via GitHub CLI (`gh`) & Sub-Issue Creation**:
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, validates the checklist (<= 200 items, <= 3 levels nesting), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/issue-body.md" \
  --title "[Audit - LLM Readiness & llms.txt / llms-full.txt Standard Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Validate that `/llms.txt` adheres strictly to standard Markdown structure with HTTP 200 status:
   ```bash
   curl http://localhost:4321/llms.txt
   curl -sI http://localhost:4321/llms.txt | grep -i "content-type"
   ```
2. Confirm dynamic full manifest endpoint streams with `text/plain; charset=utf-8`:
   ```bash
   curl -N -i http://localhost:4321/llms-full.txt | head -n 30
   ```
3. Test edge content negotiation response:
   ```bash
   curl -H "Accept: text/markdown" http://localhost:4321/
   ```
4. Search for persistent elements across client navigation:
   ```bash
   git grep -n "transition:persist" src/
   ```
5. Confirm that `robots.txt` permits search-oriented AI user-agents while maintaining scrapers discipline:
   ```bash
   rg -i "(GPTBot|ClaudeBot|PerplexityBot)" public/robots.txt
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** LLM Readiness & llms.txt / llms-full.txt Standard Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/06-future-edge-ai-analytics/51-llms-txt-ai-crawler-standard/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
