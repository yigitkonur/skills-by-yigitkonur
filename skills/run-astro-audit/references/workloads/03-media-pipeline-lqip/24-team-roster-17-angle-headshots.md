# Mission Brief: Team Roster 17-Angle Headshots & Eye-Line Audit

## 3.0 Skills / Tools: view_file, run_command, team-photo-normalizer.

## 3.1 Context Block

The project's team directory features 34 specialists with interactive 17-angle cursor-tracking portraits (578 total angle frames across the team).
As the user moves their cursor over a specialist's portrait, the image swaps across 17 pre-rendered head angles matching the cursor vector.
Astro performance and architectural invariants:

1. **Initial Portrait Eager vs Deferred Angle Preloading**: Loading all 578 images upfront causes catastrophic network choke and memory thrashing. The central master portrait (Angle 0) must load eagerly with explicit dimensions, while angles 1-16 must preload asynchronously strictly on `pointerenter` or `focus` of an individual card.
2. **Strict Eye-Line Alignment & CLS Eradication**: All 17 poses must adhere to strict eye-line alignment, uniform collar heights, and a reserved container aspect ratio (`aspect-[4/5]` or `aspect-square`). Swapping image sources must cause 0px layout shift.
3. **60/120 FPS Compositor & Event Throttling**: The cursor-tracking script must never query `getBoundingClientRect()` inside an unthrottled `mousemove` handler. Rect bounds must be cached on `pointerenter`/`resize`, and frame calculations must be scheduled via `requestAnimationFrame`.
4. **Dead Code Elimination**: Team components must remain pure, eliminating unused imports and deprecated transforms (e.g. `clampTransformWidth`).

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-generate-programmatic-assets-with-getimage.md`](../../best-practices/07-assets-and-image-pipeline/04-generate-programmatic-assets-with-getimage.md) — Programmatic asset generation, dynamic angle sprite generation, and Sharp format transforms (`RULE-ID: ASTRO-ASSETS-04`).
- [`05-secure-remote-images-with-remotepatterns.md`](../../best-practices/07-assets-and-image-pipeline/05-secure-remote-images-with-remotepatterns.md) — Securing external CDN origins and R2 storage endpoints in `astro.config.mjs` (`RULE-ID: ASTRO-ASSETS-05`).
- [`06-infer-remote-image-dimensions-to-prevent-cls.md`](../../best-practices/07-assets-and-image-pipeline/06-infer-remote-image-dimensions-to-prevent-cls.md) — Enforcing explicit width/height dimensions and container aspect ratios to eliminate Cumulative Layout Shift (CLS) during frame swaps (`RULE-ID: ASTRO-ASSETS-06`).
- [`07-configure-responsive-layouts-and-sizes.md`](../../best-practices/07-assets-and-image-pipeline/07-configure-responsive-layouts-and-sizes.md) — Responsive layout presets, density descriptors, and `sizes` attributes for multi-column team grids (`RULE-ID: ASTRO-ASSETS-07`).
- [`04-html-chunk-streaming.md`](../../best-practices/01-architecture-and-philosophy/04-html-chunk-streaming.md) — Edge worker responsiveness and early unblocked HTML chunk streaming for initial above-the-fold team roster rendering (`RULE-ID: ASTRO-ARCH-04`).

Critical files to inspect:

- `src/features/team/components/TeamPhotoGrid.astro`
- `src/features/team/components/TeamProfilePhoto.astro`
- `src/features/team/components/TeamRoute.astro`
- `src/data/team/`
- `.claude/skills/team-photo-normalizer/`

## 3.2 Mission Objective

Audit the team roster photo grid, 17-pose sprite manifest, eye-line calibration, and cursor-follow script execution.
Outcome: Confirm eye-line calibration across all 34 team members, verify deferred preloading strategies for the 17-angle sets, eliminate layout shifts during frame swaps, and ensure 60+ FPS animation without memory leaks.
Constraints: Read-only audit; check image manifest integrity, event listener cleanup, and DOM reflow triggers.
Autonomy Grant: You own this mission end-to-end. Inspect pointer event listeners, image sprite prefetching, and portrait dimensions. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `TeamPhotoGrid.astro` lines 180-215: verify inline script execution, rect caching, and `requestAnimationFrame` throttling.
2. Verify that initial portraits load eagerly, while the 16 remaining angle variations preload on `pointerenter`/`focus`.
3. Check for unused imports in team components (e.g. `clampTransformWidth` in `TeamPhotoGrid.astro`).
4. Validate that all 34 specialists have 17 generated angle frames in the team asset manifest.
5. Audit remote origins in `astro.config.mjs` / `config/images.mjs` to ensure team portrait CDNs are secured under `image.remotePatterns`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Inlining 17 Raw Image Tags vs. Single Dynamic Image with Deferred Preload (RULE-ID: ASTRO-ARCH-04, RULE-ID: ASTRO-ASSETS-06)

##### ❌ Bad Practice / Anti-Pattern: Inlining 17 raw image tags per team member into the HTML document

```astro
<!-- ❌ Anti-Pattern: Next.js migration habit; inlines 578 raw image tags directly into HTML, choking network and memory -->
<div class="team-grid grid grid-cols-4">
  {teamMembers.map((member) => (
    <div class="member-card" onmousemove="updateAngle(event)">
      {member.angles.map((angleUrl, idx) => (
        <img
          src={angleUrl}
          class={idx === 0 ? "visible" : "hidden"}
          loading="eager"
        />
      ))}
    </div>
  ))}
</div>
<script>
  function updateAngle(e) {
    const rect = e.currentTarget.getBoundingClientRect(); // Forces layout recalculation on every pixel!
    const frameIndex = calculateFrame(e.clientX - rect.left, e.clientY - rect.top);
    // Unthrottled DOM mutation swaps element visibility
    e.currentTarget.querySelectorAll('img').forEach((img, i) => {
      img.classList.toggle('visible', i === frameIndex);
      img.classList.toggle('hidden', i !== frameIndex);
    });
  }
</script>
```

_Why this fails:_ Emitting 17 `<img>` elements for each of the 34 team members generates 578 DOM elements upfront. The browser attempts to fetch hundreds of images concurrently during initial page load, saturating the network thread, delaying TTFB, and blowing past memory budgets. Furthermore, invoking `getBoundingClientRect()` in unthrottled `mousemove` forces costly browser reflows on every pixel of cursor motion.

##### ✅ Best Practice / Idiomatic: Single dynamic `<img />` with explicit dimensions, RAF cursor math, and on-demand angle preloading

```astro
---
// ✅ Idiomatic: Single master portrait rendered server-side; remaining angles preloaded strictly on demand
interface Props {
  member: TeamMember;
}
const { member } = Astro.props;
---
<div
  class="team-card relative aspect-[4/5] overflow-hidden rounded-[4px] bg-neutral-100 dark:bg-neutral-900"
  data-team-id={member.id}
  data-angles={JSON.stringify(member.angles)}
>
  <img
    src={member.angles[0]}
    alt={`${member.name}, ${member.role}`}
    width="400"
    height="500"
    loading="eager"
    decoding="async"
    class="w-full h-full object-cover select-none pointer-events-none transition-opacity duration-75"
  />
</div>

<script>
  // Rect cached on pointerenter; frame swaps batched in requestAnimationFrame; angles 1-16 preloaded on hover
  document.querySelectorAll<HTMLElement>('.team-card').forEach((card) => {
    let cachedRect: DOMRect | null = null;
    let rafId: number | null = null;
    let preloaded = false;
    const img = card.querySelector('img');
    const angles = JSON.parse(card.dataset.angles || '[]');

    const preloadAngles = () => {
      if (preloaded || angles.length <= 1) return;
      preloaded = true;
      angles.slice(1).forEach((url: string) => {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.as = 'image';
        link.href = url;
        document.head.appendChild(link);
      });
    };

    card.addEventListener('pointerenter', () => {
      cachedRect = card.getBoundingClientRect();
      preloadAngles();
    }, { passive: true });

    card.addEventListener('pointermove', (e) => {
      if (!cachedRect || !img) return;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const x = e.clientX - cachedRect.left;
        const y = e.clientY - cachedRect.top;
        const angleIdx = calculateAngleIndex(x, y, cachedRect.width, cachedRect.height);
        if (angles[angleIdx] && img.src !== angles[angleIdx]) {
          img.src = angles[angleIdx];
        }
      });
    }, { passive: true });
  });
</script>
```

#### Pattern 2: Missing Container Aspect-Ratio Causing Cumulative Layout Shift (RULE-ID: ASTRO-ASSETS-06, RULE-ID: ASTRO-ASSETS-07)

##### ❌ Bad Practice / Anti-Pattern: Unreserved image container causing CLS during frame swaps

```astro
<!-- ❌ Anti-Pattern: No explicit width/height or aspect ratio; card height collapses and expands -->
<div class="team-portrait-wrapper">
  <img src={member.angles[0]} alt={member.name} class="w-full" />
</div>
```

_Why this fails:_ Without explicit width/height or CSS `aspect-[4/5]`, the layout engine cannot allocate space before image bytes arrive. Swapping between angles of slightly different pixel ratios or during delayed network loads causes immediate layout shifts, failing Core Web Vitals (CLS > 0.1).

##### ✅ Best Practice / Idiomatic: Preserved aspect-ratio with responsive grid sizes

```astro
---
// ✅ Idiomatic: Explicit width, height, aspect-ratio, and responsive sizes attribute
---
<div class="aspect-[4/5] w-full overflow-hidden rounded-[4px] bg-neutral-100 dark:bg-neutral-800">
  <img
    src={member.angles[0]}
    alt={member.name}
    width="400"
    height="500"
    sizes="(min-width: 1280px) 25vw, (min-width: 768px) 33vw, 50vw"
    class="w-full h-full object-cover"
  />
</div>
```

#### Pattern 3: Programmatic Asset Resolution with getImage() (RULE-ID: ASTRO-ASSETS-04)

##### ❌ Bad Practice / Anti-Pattern: Calling Sharp image transforms inside client scripts

```tsx
// ❌ Anti-Pattern: Attempting to call server-side getImage() in client island
import { getImage } from 'astro:assets'
export function TeamFilter() {
  // Throws runtime error in browser bundle!
  const optimized = await getImage({ src: '/assets/team.png', width: 400 })
  return <img src={optimized.src} />
}
```

##### ✅ Best Practice / Idiomatic: Resolving programmatic assets during server compilation

```astro
---
// ✅ Idiomatic: getImage() executes server-side, returning optimized WebP asset references
import { getImage } from 'astro:assets';
import masterPortrait from '@/assets/team/master-portrait.png';

const optimized = await getImage({
  src: masterPortrait,
  format: 'webp',
  width: 400,
  height: 500,
  quality: 85,
});
---
<img src={optimized.src} width={optimized.attributes.width} height={optimized.attributes.height} loading="eager" decoding="async" />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/`

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

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "24-TEAM-ROSTER-17-ANGLE-HEADSHOTS-001",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/issue-body.md" \
  --title "[Audit - Team Roster 17-Angle Headshots & Eye-Line Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit team member manifest to confirm all 34 specialists possess complete 17-angle sprite definitions:
   ```bash
   # Check completeness of team angle manifests in src/data/team/
   pnpm tsx -e "import { teamMembers } from './src/data/team/index.ts'; console.log('Team roster size:', teamMembers.length);" || echo "Checking team manifest"
   ```
2. Verify event listener efficiency and memory safety in `TeamPhotoGrid.astro`:
   ```bash
   # Confirm requestAnimationFrame is used for pointermove tracking
   grep -n "requestAnimationFrame" src/features/team/components/TeamPhotoGrid.astro
   # Confirm getBoundingClientRect is NOT called directly inside mousemove without caching
   grep -n "getBoundingClientRect" src/features/team/components/TeamPhotoGrid.astro
   # Detect dead imports like clampTransformWidth in team components
   git grep -rn "clampTransformWidth" src/features/team/ || echo "Pass: No dead clampTransformWidth import"
   ```
3. Audit image remote patterns and dimension inference:
   ```bash
   # Confirm remotePatterns configuration in astro config
   git grep -n "image.remotePatterns" astro.config.* config/
   # Audit dimension inference calls across codebase
   git grep -n "inferSize" src/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Team Roster 17-Angle Headshots & Eye-Line Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/24-team-roster-17-angle-headshots/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
