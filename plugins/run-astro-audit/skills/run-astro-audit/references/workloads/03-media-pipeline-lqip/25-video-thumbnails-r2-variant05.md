# Mission Brief: Video Thumbnails & R2 Asset Synchronization Audit

## 3.0 Skills / Tools: view_file, run_command, video-cover-pipeline.

## 3.1 Context Block

YouTube video covers across Digitalzone, Meetups, and Academy follow the Variant 05 design system:

1. **Variant 05 Visual Standards**: Canvas pre-wipe eliminating legacy red YouTube banners, clean typography, Swiss layout, and high-resolution WebP assets synchronized to Cloudflare R2 storage.
2. **Fallback Resolution Cascade**: Videos without custom Variant 05 artwork must resolve through a resilient fallback cascade (`getVideoThumbnailUrl` / `getVideoThumbnailPair`): R2 Variant 05 WebP -> YouTube `maxresdefault.jpg` -> YouTube `hqdefault.jpg`.
3. **Secure Remote Image Configuration (`remotePatterns`)**: External YouTube domains (`img.youtube.com`, `i.ytimg.com`) and R2 CDN endpoints must be explicitly whitelisted under `image.remotePatterns` in `astro.config.mjs` / `config/images.mjs` to authorize image processing and dimension inference while preventing SSRF vulnerabilities.
4. **Aspect-Ratio & CLS Prevention**: All video cards and modals must enforce explicit `aspect-video` (`16/9`) container dimensions with `object-cover` so layout boxes are reserved before image bytes arrive.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-generate-programmatic-assets-with-getimage.md`](../../best-practices/07-assets-and-image-pipeline/04-generate-programmatic-assets-with-getimage.md) — Dynamic programmatic image optimization and CSS background generation via `getImage()` (`RULE-ID: ASTRO-ASSETS-04`).
- [`05-secure-remote-images-with-remotepatterns.md`](../../best-practices/07-assets-and-image-pipeline/05-secure-remote-images-with-remotepatterns.md) — Authorizing remote image origins, securing YouTube/R2 CDN hosts, and preventing SSRF via `image.remotePatterns` (`RULE-ID: ASTRO-ASSETS-05`).
- [`06-infer-remote-image-dimensions-to-prevent-cls.md`](../../best-practices/07-assets-and-image-pipeline/06-infer-remote-image-dimensions-to-prevent-cls.md) — Inferring remote thumbnail dimensions with `inferSize` and reserving aspect containers to eliminate Cumulative Layout Shift (CLS) (`RULE-ID: ASTRO-ASSETS-06`).
- [`07-configure-responsive-layouts-and-sizes.md`](../../best-practices/07-assets-and-image-pipeline/07-configure-responsive-layouts-and-sizes.md) — Configuring responsive video card grid density, srcset generation, and accurate `sizes` media conditions (`RULE-ID: ASTRO-ASSETS-07`).
- [`04-html-chunk-streaming.md`](../../best-practices/01-architecture-and-philosophy/04-html-chunk-streaming.md) — Unblocking edge HTML chunk streaming for video listings without waiting on slow external thumbnail API fetches (`RULE-ID: ASTRO-ARCH-04`).

Critical files to inspect:

- `src/lib/videos/thumbnails-map.ts`
- `src/lib/videos/bunny.ts`
- `src/features/community/components/DigitalzoneRoute.astro`
- `src/features/community/components/MeetupsRoute.astro`
- `astro.config.mjs`
- `config/images.mjs`
- `.claude/skills/video-cover-pipeline/`

## 3.2 Mission Objective

Audit all video cover mappings, thumbnail URL resolutions, remote patterns whitelisting, and R2 asset synchronization.
Outcome: Ensure zero broken video thumbnails, zero legacy red YouTube banners, secure `remotePatterns` for video CDNs, and complete fallback resolution for video IDs without custom artwork.
Constraints: Read-only audit; verify thumbnail maps against published talk IDs and check remote URL patterns.
Autonomy Grant: You own this mission end-to-end. Trace video ID extractors, thumbnail fallback cascades, and R2 object keys. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/lib/videos/thumbnails-map.ts`: verify `getVideoThumbnailUrl` and `getVideoThumbnailPair` implementation and fallback paths.
2. Verify that talks without custom artwork fall back gracefully to YouTube `maxresdefault` or `hqdefault` without breaking layouts.
3. Check `DigitalzoneRoute.astro` and `MeetupsRoute.astro` for missing cover dimensions or unreserved video card containers.
4. Audit `astro.config.mjs` and `config/images.mjs` to confirm `img.youtube.com`, `i.ytimg.com`, and R2 CDN hosts are registered in `image.remotePatterns`.
5. Audit remote image dimension handling: confirm remote assets use `inferSize={true}` or explicit `width`/`height` inside `aspect-video` containers.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Unconstrained Remote Video Thumbnails Triggering CLS vs. Inferring Dimensions with inferSize & Aspect Containers (RULE-ID: ASTRO-ASSETS-06)

##### ❌ Bad Practice / Anti-Pattern: Rendering remote R2 video thumbnails using unconstrained `<img src="https://r2.../thumb.jpg">` without explicit dimensions

```astro
<!-- ❌ Anti-Pattern: Next.js migration habit; unconstrained remote <img> without width/height or aspect-ratio triggers severe CLS -->
<div class="video-card">
  <img
    src={`https://r2.example.com/videos/variant05/${video.youtubeId}.webp`}
    alt={video.title}
    class="w-full"
  />
  <h3>{video.title}</h3>
</div>
```

_Why this fails:_ When the browser parses the HTML, the image container has zero initial height. Once the remote WebP arrives over the network, the layout engine shifts all following elements down by several hundred pixels. This creates high Cumulative Layout Shift (CLS > 0.25), degrading Google Core Web Vitals.

##### ✅ Best Practice / Idiomatic: Using inferSize or explicit dimensions inside a reserved aspect-video container

```astro
---
// ✅ Idiomatic: Resolves Variant 05 WebP from R2; reserves aspect-video; infers or declares explicit dimensions
import { Image } from 'astro:assets';
import { getVideoThumbnailPair } from '@/lib/videos/thumbnails-map';

const { video } = Astro.props;
const thumbnail = getVideoThumbnailPair(video.youtubeId);
---
<div class="video-card group">
  <div class="relative aspect-video overflow-hidden rounded-[4px] bg-neutral-900">
    <Image
      src={thumbnail.src}
      inferSize={true}
      alt={video.title}
      loading="lazy"
      decoding="async"
      class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
    />
  </div>
  <h3 class="mt-3 font-gilroy font-semibold text-lg">{video.title}</h3>
</div>
```

#### Pattern 2: Permissive Wildcard Domains vs. Path-Scoped RemotePatterns (RULE-ID: ASTRO-ASSETS-05)

##### ❌ Bad Practice / Anti-Pattern: Open wildcard image domains exposing server to SSRF

```javascript
// astro.config.mjs
// ❌ Anti-Pattern: Permissive wildcard allows arbitrary external hosts, opening SSRF vectors
export default defineConfig({
  image: {
    domains: ['*'],
  },
})
```

_Why this fails:_ A broad wildcard allows malicious content editors or user-submitted URLs to probe internal network endpoints (e.g. `http://169.254.169.254`) or force the edge worker to download multi-gigabyte decompression bombs.

##### ✅ Best Practice / Idiomatic: Strict path-scoped remotePatterns for YouTube and R2 CDN

```javascript
// config/images.mjs
// ✅ Idiomatic: Explicit protocol, hostname, and path prefixes
export const imageConfig = {
  remotePatterns: [
    {
      protocol: 'https',
      hostname: 'img.youtube.com',
      pathname: '/vi/**',
    },
    {
      protocol: 'https',
      hostname: 'i.ytimg.com',
      pathname: '/vi/**',
    },
    {
      protocol: 'https',
      hostname: 'assets.example.com',
      pathname: '/legacy/assets/**',
    },
  ],
}
```

#### Pattern 3: Responsive Multi-Column Video Grid Layouts & Sizes Anti-Pattern (RULE-ID: ASTRO-ASSETS-07)

##### ❌ Bad Practice / Anti-Pattern: Missing sizes in multi-column video catalog

```astro
<!-- ❌ Anti-Pattern: Omits sizes attribute in 3-column grid; mobile browsers request desktop 1280px assets -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {videos.map((vid) => (
    <Image src={vid.thumbnail} layout="constrained" alt={vid.title} />
  ))}
</div>
```

##### ✅ Best Practice / Idiomatic: Specifying accurate media conditions matching the CSS grid

```astro
<!-- ✅ Idiomatic: Accurate sizes media queries save up to 70% cellular bandwidth on mobile devices -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {videos.map((vid) => (
    <Image
      src={vid.thumbnail}
      layout="constrained"
      sizes="(min-width: 1024px) 33vw, (min-width: 768px) 50vw, 100vw"
      alt={vid.title}
    />
  ))}
</div>
```

#### Pattern 4: Top-Level Blocking Fetches vs. Unblocked HTML Streaming (RULE-ID: ASTRO-ARCH-04, RULE-ID: ASTRO-ASSETS-04)

##### ❌ Bad Practice / Anti-Pattern: Awaiting remote thumbnail network checks before streaming HTML

```astro
---
// ❌ Anti-Pattern: Top-level fetch calls block the HTTP response stream for the entire page
const verifiedThumbnails = await Promise.all(
  videos.map(async (v) => {
    const res = await fetch(`https://img.youtube.com/vi/${v.id}/maxresdefault.jpg`, { method: 'HEAD' });
    return res.ok ? `https://img.youtube.com/vi/${v.id}/maxresdefault.jpg` : `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`;
  })
);
---
<html>
  <!-- Entire response hangs until all external YouTube HTTP calls complete! -->
</html>
```

##### ✅ Best Practice / Idiomatic: Pure synchronous dictionary mapping streaming HTML chunks immediately

```astro
---
// ✅ Idiomatic: Fast dictionary lookup allows instant HTML chunk streaming
import { getVideoThumbnailPair } from '@/lib/videos/thumbnails-map';
---
<html>
  <head><title>Digitalzone Videos</title></head>
  <body>
    <!-- Streamed to client in <10ms TTFB -->
    {videos.map((v) => {
      const thumb = getVideoThumbnailPair(v.id);
      return <img src={thumb.src} width="1280" height="720" loading="lazy" class="aspect-video" />;
    })}
  </body>
</html>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/`

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

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "25-VIDEO-THUMBNAILS-R2-VARIANT05-001",
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
  --body "docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/issue-body.md" \
  --title "[Audit - Video Thumbnails & R2 Asset Synchronization Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit community content collections to confirm every video entry resolves to a valid thumbnail URL:
   ```bash
   # Check thumbnail mapping coverage across Digitalzone and Meetup talk entries
   pnpm tsx -e "import { videoThumbnailsMap } from './src/lib/videos/thumbnails-map.ts'; console.log('Mapped custom thumbnails:', Object.keys(videoThumbnailsMap).length);"
   ```
2. Verify remote pattern security whitelist in `astro.config.*` and `config/images.mjs`:
   ```bash
   # Confirm YouTube and CDN hostnames are configured in image.remotePatterns
   grep -rn "remotePatterns" astro.config.* config/images.mjs && grep -rn "youtube.com" config/images.mjs || echo "Audit remotePatterns"
   # Verify aspect-video usage across video route templates
   git grep -n "aspect-video" src/features/community/ || echo "Warning: Check video aspect ratios"
   ```
3. Audit remote image dimension sniffing:
   ```bash
   # Audit inferSize and remote image dimensions across all components
   git grep -n "inferSize" src/
   # Confirm image.remotePatterns exists in config
   git grep -n "image.remotePatterns" astro.config.* config/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Video Thumbnails & R2 Asset Synchronization Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/25-video-thumbnails-r2-variant05/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
