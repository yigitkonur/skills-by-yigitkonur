# Mission Brief: Cloudflare R2 Remote Media Manifest & Asset Shipping Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

In The project's edge hosting boundary and Astro asset architecture:

1. **Zero Media in Git Bundle**: `public/assets/` is strictly gitignored and NEVER committed to version control or packaged into the Cloudflare Worker deployment bundle. Shipping binary assets directly inside worker bundles bloats edge deployment times and risks exceeding Cloudflare deployment limits.
2. **Canonical R2 Remote Storage**: Every media asset is stored remotely in Cloudflare R2 object storage and referenced exclusively through `resolveAssetUrl()` or `transformImageUrl()`.
3. **Edge Image Passthrough & Security Whitelist**: In `astro.config.mjs`, `passthroughImageService()` must be configured for the Cloudflare adapter to avoid runtime Sharp crashes, while `image.remotePatterns` must explicitly authorize the R2 CDN domain to prevent SSRF vulnerabilities.
4. **Asset Shipping Protocol**: Assets must be published to R2 using `pnpm assets:ship <jobs.jsonl>` before production merges, ensuring that all published URLs in content collections are backed by real CDN objects.

Astro Architectural & Best Practice Rules:

- **Remote Asset Optimization & LCP ([14-optimize-largest-contentful-paint-lcp.md](../../best-practices/09-performance-prefetch-and-transitions/14-optimize-largest-contentful-paint-lcp.md))**: LCP candidate images served from Cloudflare R2 must be annotated with `loading="eager"`, `decoding="async"`, and `fetchpriority="high"`. Never lazy-load above-the-fold media or wrap hero graphics in client-side framework islands.
- **Media Dimension Reservation & CLS Prevention ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Every remote image and media container resolved via `resolveAssetUrl()` must declare explicit `width`, `height`, or CSS `aspect-ratio` tokens (`aspect-[1200/630]`, `aspect-[16/9]`) or `contain-intrinsic-size` skeletons to guarantee zero layout shift (CLS < 0.05) when remote assets load.
- **Font & Asset Delivery Hygiene ([09-self-host-and-preload-critical-web-fonts.md](../../best-practices/07-assets-and-image-pipeline/09-self-host-and-preload-critical-web-fonts.md))**: Avoid external asset CDNs and unverified origins; all static assets and critical font files must be self-hosted or served via authenticated R2 edge caching with immutable HTTP headers.
- **Layout Shift Elimination ([10-eliminate-font-cls-with-metric-overrides.md](../../best-practices/07-assets-and-image-pipeline/10-eliminate-font-cls-with-metric-overrides.md))**: Asset loading waterfalls must not cause layout reflows or disrupt the Swiss typography layout grid.

Critical files to inspect:

- `src/lib/assets/asset-url.ts`
- `src/lib/assets/asset-manifest.ts`
- `astro.config.mjs`
- `.gitignore`
- `scripts/assets/`
- `src/layouts/SiteLayout.astro`

## 3.2 Mission Objective

Audit remote media asset resolution, manifest synchronization, and asset shipping integrity.
Outcome: Prove that zero binary media files are committed to git tracking, all asset URLs resolve through CDN domains via `resolveAssetUrl()`, `remotePatterns` secures R2 hosts, and the local asset manifest matches remote R2 storage.
Constraints: Read-only audit; check git tracking and URL resolvers.
Autonomy Grant: You own this mission end-to-end. Audit asset manifests, hash verification, and URL rewriting logic. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `git status` and check `.gitignore`: confirm `public/assets/` remains strictly ignored with zero staged binary files.
2. Inspect `src/lib/assets/asset-url.ts`: verify CDN base URL resolution and query parameter transforms across development and production environments.
3. Check for any hardcoded localhost, raw `/public/`, or direct local `/assets/` paths in markdown content collections and Astro components.
4. Audit `astro.config.mjs`: confirm `image.remotePatterns` whitelists the R2 CDN hostname and `passthroughImageService()` is configured.
5. Contrast Next.js asset handling (`next/image` with automatic remote loaders) with Astro's edge passthrough and explicit container dimension contracts.

### ❌ Bad Practice / Anti-Pattern (Committed Binaries & Hardcoded Relative Asset Paths)

```astro
---
// ❌ Anti-Pattern: Hardcoded relative path to git-tracked public asset; bypasses R2 CDN
---
<article class="case-study">
  <img
    src="/assets/case-studies/enterprise-audit-hero.png"
    alt="Enterprise Audit Diagram"
  />
</article>
```

### ✅ Best Practice / Idiomatic (Canonical R2 CDN Resolver with RemotePatterns)

```astro
---
// ✅ Idiomatic: Resolves to R2 CDN URL; authorized by remotePatterns; edge-safe passthrough
import { resolveAssetUrl } from '@/lib/assets/asset-url';
const heroCdnUrl = resolveAssetUrl('case-studies/enterprise-audit-hero.webp');
---
<article class="case-study">
  <img
    src={heroCdnUrl}
    alt="Enterprise Audit Diagram"
    width="1200"
    height="630"
    loading="lazy"
    decoding="async"
    class="w-full h-auto aspect-[1200/630] rounded-[4px]"
  />
</article>
```

### ❌ Bad Practice / Anti-Pattern (Elements Expanding Dynamically Without Reserved Aspect-Ratio)

```astro
---
// ❌ Anti-Pattern: Unconstrained remote image container without aspect-ratio or reserved dimensions
import { resolveAssetUrl } from '@/lib/assets/asset-url';
const promoUrl = resolveAssetUrl('promos/seasonal-campaign.webp');
---
<div class="promo-container">
  <!-- Missing width/height & aspect-ratio: causes severe layout push (CLS > 0.1) when remote R2 image loads -->
  <img src={promoUrl} alt="Campaign Details" />
</div>
```

### ✅ Best Practice / Idiomatic (Reserving Container Dimensions via CSS aspect-ratio & contain-intrinsic-size)

```astro
---
// ✅ Idiomatic: Explicit aspect-ratio container with reserved dimensions guarantees 0 CLS
import { resolveAssetUrl } from '@/lib/assets/asset-url';
const promoUrl = resolveAssetUrl('promos/seasonal-campaign.webp');
---
<div class="promo-container relative aspect-[16/9] w-full overflow-hidden rounded-[4px] contain-intrinsic-size-[auto_450px]">
  <img
    src={promoUrl}
    alt="Campaign Details"
    width="1200"
    height="675"
    loading="lazy"
    decoding="async"
    class="w-full h-full object-cover"
  />
</div>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-09-14`, `ASTRO-BP-09-16`, `ASTRO-BP-07-09`, `ASTRO-BP-07-10`, `ASTRO-BP-01-08`).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "27-CLOUDFLARE-R2-REMOTE-MEDIA-MANIFEST-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-09-14 / ASTRO-BP-09-16 / ASTRO-BP-07-09 / ASTRO-BP-07-10 / ASTRO-BP-01-08)",
    "file": "path/to/file.ext",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "syntax" | "hydration" | "parity" | "performance" | "security",
    "defect": "Precise description of what is broken or violating invariants (must reference RULE-ID)",
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
  --body "docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/issue-body.md" \
  --title "[Audit - Cloudflare R2 Remote Media Manifest & Asset Shipping Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit git status to confirm zero tracked binaries in `public/assets/`:
   ```bash
   # Confirm public/assets/ is untracked by git
   git ls-files public/assets/ | wc -l | grep -q '^0$' && echo "Pass: Zero binaries in git" || echo "Fail: Untracked assets committed"
   grep -rn "public/assets" .gitignore
   ```
2. Prove that `resolveAssetUrl()` returns absolute HTTPS CDN URLs in production mode:
   ```bash
   # Test asset-url resolution helper under production environment flag
   NODE_ENV=production pnpm tsx -e "import { resolveAssetUrl } from './src/lib/assets/asset-url.ts'; console.log('Resolved URL:', resolveAssetUrl('test.png'));"
   # Detect any raw hardcoded localhost or /assets/ strings in content files
   git grep -rn 'src="/assets/' src/content/ src/pages/ || echo "Pass: Zero raw /assets/ references"
   ```
3. Verify `<head>` preloading and inline script placement invariants:
   ```bash
   # Audit preload directives in layouts
   git grep -n "preload" src/layouts/
   # Audit synchronous inline scripts in layouts
   git grep -n "is:inline" src/layouts/
   ```
4. Verify remote media containers declare explicit dimensions or aspect ratios:
   ```bash
   # Check for unconstrained <img> tags without aspect-ratio or dimension tokens
   git grep -n "<img" src/features/ src/components/ | grep -v -E "width=|aspect-|contain-intrinsic-size" || echo "Pass: All remote images dimensioned"
   ```
5. Run Playwright automated CLS and remote media layout stability checks:
   ```bash
   npx playwright test tests/e2e/media-remote-patterns.spec.ts || pnpm vitest run tests/int/asset-url.test.ts
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Cloudflare R2 Remote Media Manifest & Asset Shipping Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/27-cloudflare-r2-remote-media-manifest/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
