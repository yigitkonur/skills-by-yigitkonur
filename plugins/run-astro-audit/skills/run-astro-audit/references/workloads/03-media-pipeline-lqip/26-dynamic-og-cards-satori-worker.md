# Mission Brief: Dynamic OG Social Cards & Satori Worker Audit

## 3.0 Skills / Tools: view_file, run_command, og-card-generator.

## 3.1 Context Block

Social media sharing cards (1200x630 Open Graph images) are generated dynamically by `workers/og` using Satori (HTML/CSS to SVG) and Resvg (SVG to PNG).
Astro edge architecture and social metadata standards:

1. **Edge Runtime Execution Without Native Sharp**: The Cloudflare Workers edge runtime lacks native Node.js C++ bindings required by Sharp. The OG worker operates strictly via Satori and WebAssembly Resvg, requiring pure V8 JavaScript and WASM compilation.
2. **Worker Bundle Budget (<1 MB) & Font Buffering**: Gilroy and Akagi font files must be subsetted or streamed efficiently to prevent `workers/og` from exceeding the strict 1 MB Cloudflare Workers script size limit.
3. **Multilingual Unicode Coverage**: Typography must render localized primary locale special characters (`ğ, ü, ş, ı, ö, ç`) and localized secondary locale glyphs without glyph dropouts (tofu).
4. **Rich Social Player Metadata for Video Detail Routes**: Video talk detail pages (Digitalzone, Meetups) must emit Twitter player card tags (`twitter:card: "player"`, `twitter:player`, `twitter:player:width`, `twitter:player:height`) and `og:video` / `og:video:secure_url` alongside `og:image` to enable inline playback on X and LinkedIn feeds.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-generate-programmatic-assets-with-getimage.md`](../../best-practices/07-assets-and-image-pipeline/04-generate-programmatic-assets-with-getimage.md) — Programmatic asset generation, canonical `og:image` URL formulation, and static preview extraction via `getImage()` (`RULE-ID: ASTRO-ASSETS-04`).
- [`05-secure-remote-images-with-remotepatterns.md`](../../best-practices/07-assets-and-image-pipeline/05-secure-remote-images-with-remotepatterns.md) — Securing external asset origins and edge worker proxy fetches via strict origin whitelisting (`RULE-ID: ASTRO-ASSETS-05`).
- [`06-infer-remote-image-dimensions-to-prevent-cls.md`](../../best-practices/07-assets-and-image-pipeline/06-infer-remote-image-dimensions-to-prevent-cls.md) — Enforcing explicit 1200x630 social card dimensions and crawler metadata (`og:image:width`, `og:image:height`) (`RULE-ID: ASTRO-ASSETS-06`).
- [`07-configure-responsive-layouts-and-sizes.md`](../../best-practices/07-assets-and-image-pipeline/07-configure-responsive-layouts-and-sizes.md) — High-DPI 2x social card resolution standards and crisp SVG text rasterization (`RULE-ID: ASTRO-ASSETS-07`).
- [`04-html-chunk-streaming.md`](../../best-practices/01-architecture-and-philosophy/04-html-chunk-streaming.md) — Unblocked edge HTML streaming, immediate `<head>` emission with social meta tags, and worker latency optimization (`RULE-ID: ASTRO-ARCH-04`).

Critical files to inspect:

- `workers/og/`
- `workers/og/src/`
- `scripts/release/og/`
- `src/layouts/SiteLayout.astro`
- `src/features/community/components/DigitalzoneRoute.astro`
- `.claude/skills/og-card-generator/`

## 3.2 Mission Objective

Audit dynamic OG card generation, edge font buffer allocations, social meta tag emissions, and video player metadata.
Outcome: Confirm 1200x630 layout parity across all page types, ensure WOFF/TTF fonts load within worker memory limits, verify absolute canonical HTTPS `og:image` tags, and ensure video detail pages include Twitter player card and `og:video` metadata.
Constraints: Read-only audit; verify Satori CSS subset compatibility and meta tag structures.
Autonomy Grant: You own this mission end-to-end. Test Satori rendering, inspect font buffer allocations, and check social crawler tags. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `workers/og`: verify that font files (Gilroy, Akagi) are bundled efficiently without exceeding the 1 MB Cloudflare Workers bundle limit.
2. Check `SiteLayout.astro`: ensure `og:image` URLs emit absolute HTTPS URLs pointing to the canonical OG worker endpoint or pre-rendered R2 asset.
3. Verify that localized primary locale special characters (ğ, ü, ş, ı, ö, ç) and localized secondary locale glyphs render without tofu (missing glyph blocks).
4. Check video routes: ensure `og:video:url`, `og:video:secure_url`, and `twitter:player` tags are emitted for Digitalzone and Meetup talks.
5. Audit remote origins in `astro.config.mjs` / `config/images.mjs` to ensure dynamic OG proxy targets are secured under `image.remotePatterns`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Heavy Headless Puppeteer Chromium Instances vs. Lightweight Edge Satori + Resvg Worker (RULE-ID: ASTRO-ARCH-04, RULE-ID: ASTRO-ASSETS-04)

##### ❌ Bad Practice / Anti-Pattern: Running heavy Puppeteer chromium instances to generate OG cards on demand

```typescript
// ❌ Anti-Pattern: Node.js / Next.js migration habit; launches heavy Chromium browser per request
import puppeteer from 'puppeteer'

export async function handleOgRequest(req: Request) {
  // Spawns 500MB+ Chromium instance on every social crawler request!
  const browser = await puppeteer.launch()
  const page = await browser.newPage()
  await page.setContent(`<div class="og-card"><h1>${title}</h1></div>`)
  const screenshot = await page.screenshot({ type: 'png' })
  await browser.close()
  return new Response(screenshot, { headers: { 'Content-Type': 'image/png' } })
}
```

_Why this fails:_ Running headless Chromium instances requires multi-gigabyte memory pools, cannot run inside lightweight Cloudflare Workers edge runtimes (which enforce a 128MB memory ceiling and 1MB bundle cap), and introduces 2,000ms–5,000ms TTFB latency, causing social crawlers like LinkedIn and Twitter to time out.

##### ✅ Best Practice / Idiomatic: Pure edge Satori + WASM Resvg pipeline with font buffering

```typescript
// workers/og/src/index.ts
// ✅ Idiomatic: Converts virtual DOM JSX to SVG with Satori, rasterizing to PNG via WASM in <50ms
import satori from 'satori'
import { Resvg, initWasm } from '@resvg/resvg-wasm'

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { searchParams } = new URL(request.url)
    const title = searchParams.get('title') || 'The application'

    // Fonts subsetted and cached in memory (<1MB worker bundle)
    const fontData = await env.ASSETS.get('fonts/Gilroy-Bold.ttf', { type: 'arrayBuffer' })

    const svg = await satori(
      {
        type: 'div',
        props: {
          style: {
            width: '1200px',
            height: '630px',
            display: 'flex',
            backgroundColor: '#0F111A',
            color: '#FFFFFF',
            fontFamily: 'Gilroy',
            padding: '80px',
          },
          children: title,
        },
      },
      {
        width: 1200,
        height: 630,
        fonts: [{ name: 'Gilroy', data: fontData, weight: 700, style: 'normal' }],
      },
    )

    const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } })
    const pngData = resvg.render().asPng()

    return new Response(pngData, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=604800, s-maxage=2592000, stale-while-revalidate=86400',
      },
    })
  },
}
```

#### Pattern 2: Absolute Canonical HTTPS OG Image URLs vs. Broken Relative Paths (RULE-ID: ASTRO-ASSETS-04, RULE-ID: ASTRO-ASSETS-06)

##### ❌ Bad Practice / Anti-Pattern: Relative image path and missing dimensions in social tags

```astro
<!-- ❌ Anti-Pattern: Relative URL fails on external social crawlers (Twitter, LinkedIn, WhatsApp) -->
<meta property="og:image" content="/images/default-og.png" />
<!-- Missing og:image:width, og:image:height, and twitter:image -->
```

_Why this fails:_ Social crawlers do not resolve relative URLs against your domain; they silently discard relative `og:image` tags. Omitting explicit `width` and `height` causes platforms like Facebook and iMessage to delay card rendering until image bytes are completely parsed.

##### ✅ Best Practice / Idiomatic: Canonical absolute HTTPS URL with explicit dimensions

```astro
---
// src/layouts/SiteLayout.astro
// ✅ Idiomatic: Fully qualified HTTPS URL guaranteed by Astro.site configuration
const { title, image } = Astro.props;
const ogImageUrl = image
  ? new URL(image, Astro.site).href
  : new URL(`/og?title=${encodeURIComponent(title)}`, Astro.site).href;
---
<meta property="og:image" content={ogImageUrl} />
<meta property="og:image:secure_url" content={ogImageUrl} />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:type" content="image/png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content={ogImageUrl} />
```

#### Pattern 3: Video Player Card Metadata Alongside OG Images (RULE-ID: ASTRO-ARCH-04)

##### ❌ Bad Practice / Anti-Pattern: Missing player card tags on video detail routes

```astro
<!-- ❌ Anti-Pattern: Video detail route lacks player tags; users cannot play video in social feeds -->
<meta name="twitter:card" content="summary" />
```

##### ✅ Best Practice / Idiomatic: Emitting Twitter player card and og:video tags for video talks

```astro
---
// src/features/community/components/DigitalzoneRoute.astro
const { talk } = Astro.props;
const videoEmbedUrl = `https://www.youtube.com/embed/${talk.youtubeId}`;
---
<meta name="twitter:card" content="player" />
<meta name="twitter:player" content={videoEmbedUrl} />
<meta name="twitter:player:width" content="1280" />
<meta name="twitter:player:height" content="720" />
<meta property="og:video" content={videoEmbedUrl} />
<meta property="og:video:secure_url" content={videoEmbedUrl} />
<meta property="og:video:type" content="text/html" />
<meta property="og:video:width" content="1280" />
<meta property="og:video:height" content="720" />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-ASSETS-04`, `RULE-ID: ASTRO-ASSETS-05`, `RULE-ID: ASTRO-ASSETS-06`, `RULE-ID: ASTRO-ASSETS-07`, `RULE-ID: ASTRO-ARCH-04`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "26-DYNAMIC-OG-CARDS-SATORI-WORKER-001",
    "rule_id": "RULE-ID: ASTRO-ASSETS-06 (Infer Remote Image Dimensions to Prevent CLS)",
    "file": "path/to/file.ext",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical and high severity defects, and pushes the JSON deliverables directly to `origin main` without PR:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/issue-body.md" \
  --title "[Audit - Dynamic OG Social Cards & Satori Worker Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify edge worker bundle size remains strictly under 1 MB:
   ```bash
   # Inspect workers/og build output size
   if [ -d "workers/og" ]; then ls -lh workers/og/dist/ || echo "Check workers/og build directory"; fi
   ```
2. Verify social meta tags and video player card tags across rendered routes:
   ```bash
   # Confirm absolute HTTPS URLs in og:image tags
   git grep -rn 'property="og:image"' src/layouts/
   # Audit video player tags on community video detail routes
   git grep -rn 'twitter:player' src/ || echo "Audit twitter:player tag coverage"
   git grep -rn 'property="og:video"' src/ || echo "Audit og:video tag coverage"
   ```
3. Audit image remote patterns and dimension inference:
   ```bash
   # Confirm image.remotePatterns configuration in astro config
   git grep -n "image.remotePatterns" astro.config.* config/
   # Audit dimension inference calls across codebase
   git grep -n "inferSize" src/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Dynamic OG Social Cards & Satori Worker Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/26-dynamic-og-cards-satori-worker/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
