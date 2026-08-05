# Detect: image-optimization

**Corpus lineage:** image-optimization/00-overview-feature-inventory.md, image-optimization/02-fluidity-when-to-use.md, image-optimization/07-pitfalls-antipatterns.md, image-optimization/08-platform-seo-practitioner.md

## Applicability gate

`images.*` keys are `next.config` entries — probe them against `config-schema.js` per
`references/gating/capability-probe.md`. Component props (`priority`, `preload`,
`fetchPriority`, `loading`, `sizes`, `fill`, `placeholder`, `blurDataURL`, `unoptimized`,
`getImageProps`) are **not** config-schema entries — gate those against the installed
`node_modules/next/package.json` version only, never against the schema file.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `<Image priority>` | Core prop, pre-16 | none | n/a — **deprecated in 16.0.0, still functional** | Below 16.0.0: current recommended API, not a finding. At/above 16.0.0: present-and-working but deprecated — never REMOVE-severity; route to the `priority` → successor recipe at `minor`. |
| `preload` | v16.0.0 | installed next ≥16.0.0 | n/a | NOT APPLICABLE if installed next <16.0.0 — the prop does not exist; do not propose adding it. |
| `fetchPriority` | Pass-through landed v13.3.0 | installed next ≥13.3.0 | n/a | NOT APPLICABLE if installed next <13.3.0 (rare on a 16-targeted repo; check pinned overrides in monorepos). |
| `loading="lazy" \| "eager"` | Core API | none | n/a | Always available; no version gate. Gate the *finding* (missing early-load signal on the confirmed LCP image; `eager` misused on offscreen images), not the feature. |
| `sizes` | Core responsive API | none | n/a | Always available. Required in practice whenever `fill` is used or the image renders narrower than the viewport — flag its absence, not its existence. |
| `fill` | Current form since v13.0.0 | positioned parent (`position: relative\|fixed\|absolute`) + reserved height/`aspect-ratio` | n/a | Always available on a 16.x install; the real prerequisite is parent CSS, not the Next.js version — flag `fill` lacking adjacent `sizes` or lacking parent geometry as a pitfall. |
| `placeholder="blur"` / `blurDataURL` | v11.0.0 | static import for automatic `blurDataURL`; manual `blurDataURL` prop for remote/dynamic `src` | n/a | Always available. Treat as broken (not just missing) when `placeholder="blur"` is set on a non-static-import `src` with no `blurDataURL` supplied. |
| `images.remotePatterns` vs deprecated `images.domains` | `remotePatterns` stable v12.3.0 (URL objects v15.3.0); `domains` deprecated since v14, reiterated v16 | installed next ≥12.3.0 for `remotePatterns` | `domains`: n/a — deprecated, not confirmed hard-removed in 16.3.0 per corpus; still parses | Probe `remotePatterns` in `config-schema.js` (present on any 16.x install). `images.domains` found → migration finding, severity per rubric below. A remote `<Image src>` host with **no** matching `remotePatterns` entry → `critical` (400 risk), independent of whether `domains` exists. |
| `images.localPatterns` | v14.2.15; query-string enforcement added v16.0.0 | installed next ≥14.2.15 for the key; ≥16.0.0 for enforcement to be load-bearing | n/a | NOT APPLICABLE (no runtime enforcement) if installed next <16.0.0. At ≥16.0.0: any local `<Image src>` with a query string and no matching `localPatterns.search` entry is `critical` — it 400s at request time. |
| `images.qualities` | Added v14.2.23; allowlist enforced + default `[75]` since v16.0.0 | installed next ≥14.2.23 for the key; ≥16.0.0 for enforcement | n/a | NOT APPLICABLE (unrestricted 1–100 quality) if installed next <14.2.23. At ≥16.0.0: `quality={n}` values outside the configured (or default `[75]`) allowlist are silently coerced to the nearest allowed value — `minor`/`informational`, never a build error. |
| `images.formats` | v12.0.0 | installed next ≥12.0.0 | n/a | Always available on a 16.x install. Default is `['image/webp']` **only** — do not assume AVIF is on unless explicitly configured. |
| `images.minimumCacheTTL` | Existing key; default changed v16.0.0 (60s → 14400s/4h) | none | n/a | Always available. A repo upgrading 15→16 with no explicit value silently jumps from a 60s to a 14400s default — `informational` during an upgrade review, never an auto-"fix" back to 60s unless the repo states a freshness requirement. |
| `next/legacy/image` | Pre-13 legacy compatibility import; formally named deprecated in 16 upgrade docs | none | n/a — deprecated, not confirmed hard-removed in 16.3.0 | Any import is a migration candidate at any installed version; severity rises from `minor` (pre-16) toward `major` (≥16.0.0, since current docs now name it deprecated). |
| `getImageProps()` | Stable v14.1.0 | installed next ≥14.1.0 | n/a | NOT APPLICABLE if installed next <14.1.0 — do not propose it as a fix on older installs. |
| `unoptimized` | Stable since v12.3.0 | installed next ≥12.3.0 | n/a | Always available on a 16.x install. Deliberate use on SVG/GIF/sub-10KB assets is `informational`, not drift. |

## Detection commands

Read-only only. Every command maps 1:1 to a gate row or a pitfall signature below.

```bash
# 1. Raw <img> in JSX/TSX — migration candidates to next/image (see false-positive filters)
rg -n '<img[\s>]' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' -g '!**/*.test.*' -g '!**/*.spec.*' <target-repo-root>
```

```bash
# 2. `priority` prop usage — deprecated-but-functional; confirm it is a JSX prop, not an unrelated identifier
rg -n '\bpriority\b' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' -g '!**/*.test.*' -g '!**/*.spec.*' <target-repo-root>
```

```bash
# 3. `fill` present without `sizes` in the same <Image> tag (heuristic — cannot see through {...spread} props)
rg -nU -P '<Image\b(?:(?!\bsizes\b|/>).)*?\bfill\b(?:(?!\bsizes\b|/>).)*?/>' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 4. next/legacy/image imports — deprecated in 16, migrate to next/image
rg -n "from ['\"]next/legacy/image['\"]" --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 5. `images.domains` in next.config — deprecated since v14 in favor of remotePatterns
rg -n '\bdomains\s*:' --glob 'next.config.*' <target-repo-root>
```

```bash
# 6. quality={n} literals in JSX — cross-check each distinct value against images.qualities
rg -n 'quality=\{?\s*\d+' -P --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 7. images.qualities / images.formats / images.minimumCacheTTL configured values, for cross-reference against #6 and cost review
rg -n '(qualities|formats|minimumCacheTTL)\s*:' -A2 --glob 'next.config.*' <target-repo-root>
```

```bash
# 8. Local <Image src> paths carrying a query string — candidates needing images.localPatterns.search on 16.x
rg -n 'src=["\x27]/[^"\x27]*\?[^"\x27]*["\x27]' -P --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 9. getImageProps / unoptimized usage — informational, confirms deliberate adoption
rg -n '\b(getImageProps|unoptimized)\b' --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
  - Remote `<Image src>` host with no matching `images.remotePatterns` entry → runtime 400 on that page.
  - Local `<Image src>` with a query string and no matching `images.localPatterns.search` entry on Next.js ≥16.0.0 → runtime 400.
  - `remotePatterns: [{ hostname: '**' }]` or an equivalently broad wildcard pattern → open-proxy security exposure (any origin can route images through your optimizer).
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
  - `fill` used in a responsive grid/card with no `sizes` (or `sizes="100vw"` on a multi-column desktop layout) → oversized downloads.
  - No intrinsic `width`/`height` and no `fill`+reserved-`aspect-ratio` on a repeated content image → measurable CLS.
  - The confirmed LCP image carries no early-load signal at all (default `loading="lazy"`, no `fetchPriority`, no `preload`) → LCP regression.
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
  - `priority` still used on an install where it is present-and-functional — migrate opportunistically, not urgently.
  - `next/legacy/image` import present — schedule migration to `next/image`.
  - `images.domains` used instead of `remotePatterns`, but current hosts still resolve correctly — deprecated surface, not a breakage.
  - `quality={n}` values outside the configured `images.qualities` allowlist — silently coerced to nearest, not an error.
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself
  - `unoptimized` deliberately set on SVG/GIF/sub-10KB assets.
  - A deliberately tuned `qualities`/`minimumCacheTTL`/`formats` block with an adjacent explanatory comment.
  - `getImageProps` used for an intentional art-direction/`<picture>` pattern.
  - Raw `<img>` correctly used inside an RSS route handler or an `ImageResponse`/Satori render context.

## False-positive filters

- Comments/docstrings mentioning `priority`, `fill`, `domains`, etc. do not count as live usage.
- Test files (`*.test.*`, `*.spec.*`, `__tests__/**`) are excluded from every command above.
- **Raw `<img>` inside an RSS/XML route handler (`app/api/rss/**/route.ts` or similar) is correct, not a finding** — RSS/Atom output is not rendered HTML and `next/image` does not apply there.
- **Raw `<img>` inside an `api/og` route, an `ImageResponse` render, or any Satori-based render context is REQUIRED, not a finding to fix** — `next/image` does not work inside `ImageResponse`/Satori; flagging it for migration is itself the false positive.
- **When many call sites pass `priority` (or `fill`, `sizes`, etc.) through a shared wrapper component** (e.g. `components/project-image.tsx` re-exporting `next/image`), **file ONE finding against the wrapper**, not N findings against every caller. Grep the wrapper's own prop-forwarding logic, not each usage site, to confirm the actual behavior.
- **A deliberately tuned `images` config is `informational`, not drift to "correct" back to defaults.** Example: `qualities: [75, 85]`, `minimumCacheTTL: 31536000`, `formats: ['image/avif', 'image/webp']` with an adjacent comment explaining the choice (e.g. a photography site accepting the AVIF cost tradeoff) is a deliberate decision — do not propose reverting it to the framework default.
- `\bpriority\b` and `\bfill\b` matches that are not JSX props on an `<Image`/`<img` element (e.g. a `task.priority` data field, a CSS custom property named `--fill`) are not findings — confirm the literal matched line before writing a finding.
- `images.domains` matches outside a top-level `images: { ... }` block (an unrelated `domains` key elsewhere in config) are not findings.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/image-optimization/` must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/image-optimization.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| `/_next/image` returns 400 for a remote URL | URL does not exactly match `remotePatterns` protocol/hostname/port/path/search | Add the narrowest matching `remotePatterns` object; do not re-enable broad `domains` | `16.x next.config images block` |
| `/_next/image` returns 400 for a local `src` with a query string on Next.js ≥16 | Queried local source lacks a matching `images.localPatterns.search` entry | Add `{ pathname: '...', search: '?v=1' }` or drop the query string | `16.x next.config images block` |
| Browser downloads a 1920/3840px candidate for a small card | Missing or overestimated `sizes`; browser defaults to `100vw` | Author `sizes` from the real CSS grid breakpoints | `Responsive grid/card image` |
| Image is blurry after adding `sizes` | The new `sizes` value underestimates the actual rendered CSS width | Widen the matching slot; account for DPR and container max-width | `Responsive grid/card image` |
| Layout shifts when a remote image loads | Missing intrinsic `width`/`height`, or `fill` parent has no reserved height | Supply real dimensions, or reserve height/`aspect-ratio` on the `fill` parent | `fill + positioned parent + aspect-ratio` |
| `placeholder="blur"` shows no blur (or warns) for a remote image | `blurDataURL` not supplied | Generate/store a tiny data URL; only static imports get it automatically | `Blur placeholder` |
| Blur overlay appears to linger in `next dev` | App Router dev hydration delay, not a production defect | Verify in a production build (`next build && next start`) before adding a CSS workaround | `Blur placeholder` |
| SVG optimizer response is unsafe or downloads unexpectedly | `dangerouslyAllowSVG` enabled without matching CSP/content-disposition policy | Prefer `unoptimized` for SVG; if enabling, set `contentDispositionType: 'attachment'` and a strict `contentSecurityPolicy` | `16.x next.config images block` |
| Image request cannot authenticate to upstream | Default loader does not forward headers | Use `unoptimized`, signed public URLs, or a custom loader | n/a — outside the seven core recipes; file as `informational` with the upstream auth requirement stated |
| Hobby deployment returns 402 for new images | Image Optimization usage exceeded Hobby included limits | Upgrade plan or reduce variant count (`qualities`/`formats`/`deviceSizes`) | `16.x next.config images block` (cost subsection) |
| Self-hosted `next start`/standalone reports Sharp missing | Production Image Optimization lacks `sharp` | `npm i sharp`, rebuild, restart — not needed on Vercel | n/a — self-hosting only, no code recipe |

## Cross-domain interactions

1. Depends on `measurement-regression-guardrails` to confirm the *actual* LCP element before recommending any priority signal — never assume the hero is LCP on every viewport.
2. Interacts with `seo-metadata`: `alt` text and `overrideSrc` affect crawlability; do not let a strict `remotePatterns`/`localPatterns` allowlist 400 on a crawlable image page.
3. Interacts with `vercel-platform-deployment`'s cost model: variant count (`width × quality × format`) maps directly to Image Transformation and Image Cache Write billing — coordinate `images.qualities`/`deviceSizes`/`formats` tuning with whoever owns the cost budget.

## Reference pointer

Fix recipes for this domain live in `references/fix/image-optimization.md`.
