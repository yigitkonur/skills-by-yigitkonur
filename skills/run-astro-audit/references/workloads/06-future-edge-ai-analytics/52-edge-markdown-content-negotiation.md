# Mission Brief: Edge Markdown Content Negotiation (Accept: text/markdown) Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

AI agents, LLMs, and terminal clients frequently query web pages with `Accept: text/markdown` or `Accept: text/plain`.
Rather than forcing AI crawlers to parse heavy HTML and strip navigation menus, Cloudflare Worker (`src/worker.ts`) and Astro dynamic endpoints can negotiate content: if `Accept: text/markdown` is present, it returns Sätteri's raw markdown body directly.

### Authoritative Astro Architectural & Best Practice Rules

- **APIRoute Signature & Standard Web Responses** — [`[03-apiroute-signature-and-web-response.md]`](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md): Runtime markdown endpoints must implement Astro's typed `APIRoute` returning standard Web API `Response` instances. Proprietary framework wrappers or naked JS objects trigger fatal runtime exceptions on Cloudflare Workers.
- **ClientRouter SPA Navigation Architecture** — [`[12-client-router-spa-navigation-architecture.md]`](../../best-practices/03-routing-and-pages/12-client-router-spa-navigation-architecture.md): When AI clients fetch markdown via HTTP `Accept: text/markdown`, the edge worker must bypass the ClientRouter HTML document pipeline entirely, while preserving standard client-side routing for browser interactions.
- **ClientRouter Lifecycle Events Sequence** — [`[13-client-router-lifecycle-events-sequence.md]`](../../best-practices/03-routing-and-pages/13-client-router-lifecycle-events-sequence.md): Client-side markdown previewers and interactive reader islands must respect Astro's 5-stage lifecycle events to ensure event handlers and scroll positions remain synchronized across soft navigations.
- **Custom DOM Swap and State Carryover on before-swap** — [`[18-custom-dom-swap-and-state-carryover-on-before-swap.md]`](../../best-practices/03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap.md): Direct text/markdown responses bypass DOM rendering, but any linked interactive previews or documentation readers must safely manage state carryover and avoid FOUC.
- **Leverage transition:persist for Persistent State** — [`[08-leverage-transition-persist-for-persistent-state.md]`](../../best-practices/09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state.md): Embedded markdown reader islands, split-pane diff viewports, and audio narrators must use `transition:persist="player"` or `transition:persist="reader"` to prevent UI remounting and lost state during client transitions.

Key Astro Best Practice contracts for Edge Markdown Content Negotiation:

1. **Dynamic Endpoints & Prerender Boundary**: Any runtime content negotiation endpoint must declare `export const prerender = false;` to evaluate incoming HTTP request headers dynamically.
2. **APIRoute Signature & Standard Web Responses**: Return standard Web API `Response` instances. Proprietary framework wrappers or naked objects are forbidden.
3. **Response Headers Immutability & Edge Caching**: Response headers—most critically `Vary: Accept`—must be committed at the route root or edge worker entry before streaming commences. Omitting `Vary: Accept` causes catastrophic edge cache pollution where standard browser users receive raw markdown or AI agents receive cached HTML.
4. **Streaming Delivery**: For expansive guides and whitepapers, pipe markdown via `ReadableStream` to minimize time-to-first-token (TTFT) for AI consumers.

Critical files to inspect:

- `src/worker.ts` (edge routing and header inspection)
- `edge/policy/` (Cloudflare Worker cache rules and Vary headers)
- `src/content/articles/` (Sätteri raw markdown repositories)
- `config/markdown.mjs`
- `src/pages/api/` (Astro endpoint routing)

## 3.2 Mission Objective

Audit and blueprint HTTP Content Negotiation for Markdown in `src/worker.ts` and Astro endpoints.
Outcome: Enable Cloudflare Worker to serve clean, raw Markdown when requested with `Accept: text/markdown`, ensuring `Vary: Accept` cache safety, bypassing HTML shells, and saving 90% bandwidth for AI consumers.
Constraints: Read-only audit; verify edge routing contracts, header immutability, and CDN cache key safety.
Autonomy Grant: You own this mission end-to-end. Trace HTTP request headers, Content-Type negotiation, and edge caching rules. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/worker.ts` `handleRequest()`: check how `request.headers.get('accept')` is processed.
2. Determine how Sätteri raw markdown bodies can be cached on Cloudflare Edge with `Vary: Accept`.
3. Ensure frontmatter metadata (title, author, date, canonical URL) is preserved at the top of the returned Markdown.
4. Audit content negotiation against anti-patterns and Next.js legacy migrations:

### Comparison 1: Content Negotiation Endpoint Architecture

❌ Bad Practice: Hand-rolling custom markdown negotiation in page frontmatter, creating duplicate endpoints:

```astro
---
// src/pages/resources/[slug].astro
// ❌ FAILS: Inspects accept header in frontmatter of HTML route, causing duplicate logic and edge cache bugs
const accept = Astro.request.headers.get("accept");
if (accept?.includes("text/markdown")) {
  const post = await getEntry("articles", Astro.params.slug!);
  // ❌ Missing Vary: Accept causes CDN to cache markdown response for standard HTML browsers!
  return new Response(post.body, {
    headers: { "Content-Type": "text/markdown" },
  });
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
    const rawMarkdown = await loadMarkdownWithFrontmatter(url.pathname)

    // ✅ Always set Vary: Accept and charset=utf-8 at the route root:
    return new Response(rawMarkdown, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        Vary: 'Accept',
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      },
    })
  }

  // Fallback to standard HTML pipeline
  return new Response(null, { status: 404 })
}
```

### Comparison 2: Persistent Media & Island State Across Client Transitions

❌ Bad Practice: Storing persistent audio or video state in global React context that resets during client transitions:

```tsx
// src/components/MarkdownAudioNarrator.tsx
// ❌ FAILS: Re-mounted on every client transition, resetting playback and causing audio drops:
export function MarkdownAudioNarrator() {
  const { isPlaying, progress } = useAudioContext() // Resets to initial state on page navigation!
  return <div className="narrator-bar">Progress: {progress}%</div>
}
```

✅ Best Practice: Using `transition:persist="player"` to keep elements alive across DOM swaps:

```astro
---
// src/components/MarkdownAudioNarrator.astro
import NarratorIsland from './MarkdownAudioNarrator.tsx';
---
<!-- ✅ Keeps audio playback element and state completely alive across SPA navigations -->
<div class="fixed top-0 right-0 z-50" transition:persist="player" transition:persist-props>
  <NarratorIsland client:idle />
</div>
```

### Comparison 3: BFCache & Background Activity Lifecycle

❌ Bad Practice: Neglecting BFCache eviction handlers, leaving frozen WebSockets and timers running in the background:

```ts
// src/scripts/live-content-stream.ts
// ❌ FAILS: Keeps live websocket connection active during pagehide, causing BFCache eviction
const socket = new WebSocket('wss://api.example.com/stream')
socket.onmessage = (msg) => updateUI(msg.data)
```

✅ Best Practice: Pausing background activities on `pagehide` and restoring on `pageshow` with `event.persisted`:

```ts
// src/scripts/live-content-stream.ts
// ✅ Pauses websocket/timers during pagehide and restores when navigating back via BFCache:
window.addEventListener('pagehide', (event) => {
  if (event.persisted) {
    socket.close()
  }
})

window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    reconnectSocket()
  }
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 03-routing-and-pages/12-client-router-spa-navigation-architecture`, `RULE-ID: 03-routing-and-pages/13-client-router-lifecycle-events-sequence`, `RULE-ID: 03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap`, `RULE-ID: 09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "52-EDGE-MARKDOWN-CONTENT-NEGOTIATION-001",
    "rule_id": "RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response",
    "file": "src/worker.ts",
    "line": 42,
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
  --body "docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/issue-body.md" \
  --title "[Audit - Edge Markdown Content Negotiation (Accept: text/markdown) Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Verify that standard browser requests (`Accept: text/html`) continue to receive full HTML:
   ```bash
   curl -sI -H "Accept: text/html" http://localhost:4321/resources/ | grep -i "content-type: text/html"
   ```
2. Verify that markdown requests receive clean Markdown with `Vary: Accept`:
   ```bash
   curl -H "Accept: text/markdown" http://localhost:4321/
   curl -sI -H "Accept: text/markdown" http://localhost:4321/resources/ | grep -E -i "(content-type: text/markdown|vary: accept)"
   ```
3. Confirm zero HTML tags in negotiated markdown payload:
   ```bash
   curl -s -H "Accept: text/markdown" http://localhost:4321/resources/ | head -n 20
   ```
4. Verify crawler manifests and persistent elements:
   ```bash
   curl http://localhost:4321/llms.txt
   git grep -n "transition:persist" src/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Edge Markdown Content Negotiation (Accept: text/markdown) Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/06-future-edge-ai-analytics/52-edge-markdown-content-negotiation/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
