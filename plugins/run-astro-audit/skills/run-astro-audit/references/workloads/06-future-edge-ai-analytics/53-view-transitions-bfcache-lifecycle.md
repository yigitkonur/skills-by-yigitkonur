# Mission Brief: View Transitions & bfcache Event Listener Lifecycle Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

Astro 5's `<ClientRouter />` (formerly `<ViewTransitions />` in Astro 4) transforms standard multi-page applications into client-side routed apps with smooth SPA-like transitions while maintaining an MPA foundation.
However, soft navigations introduce two major architectural hazards:

1. **Event Listener Duplication & Memory Leaks**: Scripts listening to `astro:page-load` or `DOMContentLoaded` run on every navigation. Without proper cleanup on `astro:before-swap`, listeners multiply exponentially, causing duplicate tracking beacons, memory leaks, and sluggish UI.
2. **Back/Forward Cache (bfcache) & State Restoration**: When navigating via browser back/forward buttons, `pageshow` and `pagehide` events must restore state cleanly without freezing continuous marquee tickers (`MarqueeRail.tsx`) or causing theme flicker.

### Authoritative Astro Architectural & Best Practice Rules

- **ClientRouter SPA Navigation Architecture** — [`[12-client-router-spa-navigation-architecture.md]`](../../best-practices/03-routing-and-pages/12-client-router-spa-navigation-architecture.md): Astro 5's `<ClientRouter fallback="animate" />` provides smooth SPA navigations while maintaining an MPA foundation. Using deprecated `<ViewTransitions />` from Astro 4 triggers obsolescence warnings and misses key router improvements.
- **ClientRouter Lifecycle Events Sequence** — [`[13-client-router-lifecycle-events-sequence.md]`](../../best-practices/03-routing-and-pages/13-client-router-lifecycle-events-sequence.md): Master the exact 5-stage lifecycle sequence (`astro:before-preparation` → `astro:after-preparation` → `astro:before-swap` → `astro:after-swap` → `astro:page-load`) to manage progress bars, cleanup event listeners, and initialize client scripts without race conditions.
- **Custom DOM Swap and State Carryover on before-swap** — [`[18-custom-dom-swap-and-state-carryover-on-before-swap.md]`](../../best-practices/03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap.md): Hook into `astro:before-swap` to mutate `event.newDocument` before DOM insertion (such as theme classes or authentication flags), completely eliminating theme flashing (FOUC) and visual jitter.
- **APIRoute Signature & Standard Web Responses** — [`[03-apiroute-signature-and-web-response.md]`](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md): Edge analytics beacons, session telemetry, and prefetch endpoints invoked during router transitions must return standard Web API `Response` objects (`Response.json()`) conforming to Astro's `APIRoute` contract.
- **Leverage transition:persist for Persistent State** — [`[08-leverage-transition-persist-for-persistent-state.md]`](../../best-practices/09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state.md): Persistent media players, ticker banners, and interactive canvas components must use `transition:persist="player"` to prevent unmounting and audio stutter across client navigations.

Key Astro 5 ClientRouter Lifecycle Sequence (Strict Chronological Order):

1. `astro:before-preparation`: Navigation initiated; show progress bars/spinners; intercept `event.loader`.
2. `astro:after-preparation`: HTML fetched and parsed into document object; hide progress indicators.
3. `astro:before-swap`: Snapshot taken; inspect/mutate `event.newDocument` before DOM insertion; clean up previous page event listeners, observers, and timers.
4. `astro:after-swap`: DOM replaced and history set; override scroll restore or sync theme classes.
5. `astro:page-load`: Transition complete and new scripts active; run page initialization logic.

Critical files to inspect:

- `src/components/TransitionLifecycle.astro`
- `src/lib/navigation/client-navigation.ts`
- `src/components/ThemeScript.astro`
- `src/components/common/MarqueeRail.tsx`
- `src/layouts/BaseLayout.astro`

## 3.2 Mission Objective

Audit all client-side event listeners and Astro lifecycle hooks across soft navigations.
Outcome: Ensure all window/document event listeners clean up on `astro:before-swap`, verify zero duplicate listeners after 10 back/forward navigations, eliminate deprecated `<ViewTransitions />` imports, and confirm 100% bfcache restoration.
Constraints: Read-only audit; inspect event listener bindings and cleanup hooks.
Autonomy Grant: You own this mission end-to-end. Trace lifecycle events (`astro:page-load`, `astro:before-swap`, `pageshow`), memory profiles, and listener registries. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `TransitionLifecycle.astro` and layouts: verify `<ClientRouter fallback="animate" />` is used instead of deprecated `<ViewTransitions />`.
2. Check `ThemeScript.astro`: ensure theme attributes mutate `event.newDocument` in `astro:before-swap` to prevent light flashes.
3. Check `MarqueeRail.tsx` and continuous tickers: ensure CSS animations do not freeze after back/forward navigation.
4. Audit event listener registration against lifecycle anti-patterns and Next.js legacy migrations:

### Comparison 1: Lifecycle Orchestration & Event Teardown

❌ Bad Practice: Uncleaned listeners multiplying exponentially on `astro:page-load` without teardown in `astro:before-swap`:

```astro
---
// ❌ Deprecated Astro 4 import:
import { ViewTransitions } from "astro:transitions";
---
<head>
  <ViewTransitions />
</head>

<script>
  // ❌ FAILS: Adds a new listener on EVERY soft navigation without teardown!
  // After 5 navigations, the scroll handler executes 5 times per frame!
  document.addEventListener("astro:page-load", () => {
    window.addEventListener("scroll", () => {
      console.log("Scrolled");
    });
  });

  // ❌ FAILS: Accessing new document elements before HTML is fetched/parsed:
  document.addEventListener("astro:before-preparation", () => {
    document.querySelector(".new-banner")?.classList.add("visible"); // null error!
  });
</script>
```

✅ Best Practice: Clean lifecycle management using `AbortController` aborted on `astro:before-swap` and signal-bound listeners on `astro:page-load`:

```astro
---
// Canonical Astro 5 ClientRouter import:
import { ClientRouter } from "astro:transitions";
---
<head>
  <ClientRouter fallback="animate" />
</head>

<script>
  // ✅ Clean lifecycle management using AbortController:
  let pageAbortController: AbortController | null = null;

  // 3. Clean up old page resources before DOM swap:
  document.addEventListener("astro:before-swap", (event) => {
    pageAbortController?.abort();

    // Apply incoming theme directly to new document before swap:
    const theme = localStorage.getItem("theme") ?? "light";
    event.newDocument.documentElement.dataset.theme = theme;
  });

  // 5. Initialize client logic with signal-bound listeners:
  document.addEventListener("astro:page-load", () => {
    pageAbortController = new AbortController();
    const { signal } = pageAbortController;

    window.addEventListener("scroll", handleScroll, { signal, passive: true });
  });
</script>
```

### Comparison 2: Persistent Media & Island State Across Client Transitions

❌ Bad Practice: Storing persistent audio or video state in global React context that resets during client transitions:

```tsx
// src/components/GlobalMediaContext.tsx
// ❌ FAILS: React Context resets when page DOM swaps, dropping active audio or video stream:
export function MediaPlayer() {
  const { isPlaying, trackId } = useMediaState() // Unmounts and drops playback
  return <audio src={`/media/${trackId}.mp3`} autoPlay={isPlaying} />
}
```

✅ Best Practice: Using `transition:persist="player"` to keep elements alive across DOM swaps:

```astro
---
// src/components/GlobalMediaPlayer.astro
import MediaPlayerIsland from './MediaPlayerIsland.tsx';
---
<!-- ✅ Native Astro directive retains the live DOM node and audio playback across soft navigations -->
<aside class="media-dock" transition:persist="player" transition:persist-props>
  <MediaPlayerIsland client:load />
</aside>
```

### Comparison 3: BFCache Eviction & Background Activities

❌ Bad Practice: Neglecting BFCache eviction handlers, leaving frozen WebSockets and timers running in the background:

```ts
// src/scripts/telemetry-streamer.ts
// ❌ FAILS: Continuous interval and open socket prevent browser BFCache storage or freeze in limbo:
const interval = setInterval(() => {
  fetch('/api/beacon')
}, 5000)
```

✅ Best Practice: Pausing background activities on `pagehide` and restoring on `pageshow` with `event.persisted`:

```ts
// src/scripts/telemetry-streamer.ts
let tickerTimer: number | null = null

window.addEventListener('pagehide', (event) => {
  // Clear timers so page qualifies for BFCache without memory churn:
  if (tickerTimer) clearInterval(tickerTimer)
})

window.addEventListener('pageshow', (event) => {
  // Check event.persisted to safely resume background loops and unpause tickers:
  if (event.persisted) {
    document.querySelectorAll<HTMLElement>('[data-marquee-rail]').forEach((el) => {
      el.style.animationPlayState = 'running'
    })
    tickerTimer = window.setInterval(sendHeartbeat, 5000)
  }
})
```

### Comparison 4: Content Negotiation Endpoints

❌ Bad Practice: Hand-rolling custom markdown negotiation in page frontmatter, creating duplicate endpoints:

```astro
---
// src/pages/[slug].astro
// ❌ FAILS: Inspecting accept headers inside page template mixes concerns and breaks client-router transitions
if (Astro.request.headers.get("accept")?.includes("text/markdown")) {
  return new Response("# Markdown Body");
}
---
```

✅ Best Practice: Inspecting `Accept: text/markdown` in middleware or APIRoute endpoints and streaming precomputed content:

```ts
// src/pages/api/markdown/[slug].ts
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async ({ request, params }) => {
  const accept = request.headers.get('accept') ?? ''
  if (accept.includes('text/markdown')) {
    const content = await getMarkdownForSlug(params.slug)
    return new Response(content, {
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        Vary: 'Accept',
      },
    })
  }
  return new Response('Not Found', { status: 404 })
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/12-client-router-spa-navigation-architecture`, `RULE-ID: 03-routing-and-pages/13-client-router-lifecycle-events-sequence`, `RULE-ID: 03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 09-performance-prefetch-and-transitions/08-leverage-transition-persist-for-persistent-state`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "53-VIEW-TRANSITIONS-BFCACHE-LIFECYCLE-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/13-client-router-lifecycle-events-sequence",
    "file": "src/components/TransitionLifecycle.astro",
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
  --body "docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/issue-body.md" \
  --title "[Audit - View Transitions & bfcache Event Listener Lifecycle Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Search for persistent elements across client navigation:
   ```bash
   git grep -n "transition:persist" src/
   ```
2. Verify zero occurrences of deprecated `ViewTransitions` in codebase:
   ```bash
   rg "ViewTransitions" src/
   ```
3. Test edge content negotiation response and crawler standard:
   ```bash
   curl -H "Accept: text/markdown" http://localhost:4321/
   curl http://localhost:4321/llms.txt
   ```
4. Verify the chronological 5-stage lifecycle sequence fires in exact order:
   ```bash
   # Run Playwright navigation lifecycle test
   pnpm vitest run test/navigation/client-router-lifecycle.test.ts
   ```
5. Confirm `data-astro-reload` and `data-astro-history="replace"` attributes function correctly on specified links.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** View Transitions & bfcache Event Listener Lifecycle Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/06-future-edge-ai-analytics/53-view-transitions-bfcache-lifecycle/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
