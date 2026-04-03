# Quality Checklist — Capture, Extraction, and Build

This checklist has three parts:

- Part A: Capture quality
- Part B: Extraction quality
- Part C: Build and visual fidelity quality

Run only the parts relevant to the current scope. If the source started from a live URL, Part A is mandatory.

> `N/A` is acceptable only when the source genuinely lacks the feature. Add a short note.

---

# PART A: CAPTURE QUALITY

Run after the Capture Wave completes.

## A1. Route Inventory Completeness

- [ ] working root, root URL, and scope are documented
- [ ] candidate routes were discovered from nav, footer, sitemap, and internal links when available
- [ ] route normalization rules were applied consistently
- [ ] every in-scope route appears in `route-manifest.json`
- [ ] every route is classified into exactly one page family
- [ ] at least one canonical exemplar exists for every family
- [ ] excluded routes are explicitly marked excluded with reason

## A2. Route Artifact Completeness

For every canonical route:

- [ ] final hydrated `dom.html` exists
- [ ] `headings.json` exists with title, H1, and ordered headings
- [ ] `runtime-metadata.json` exists when runtime data was recoverable
- [ ] route-level asset discovery exists
- [ ] `mirror/` exists with local asset copies or the absence is documented with reason
- [ ] desktop screenshot exists
- [ ] tablet screenshot exists
- [ ] mobile screenshot exists
- [ ] scroll slices or full-page capture exist for long pages
- [ ] route-level `done.signal` exists

## A3. Runtime and Asset Grounding

- [ ] stylesheet URLs were recorded
- [ ] script/chunk URLs were recorded
- [ ] font URLs were recorded when present
- [ ] image URLs were recorded when present
- [ ] framework runtime data such as `__NEXT_DATA__` or `self.__next_f` was captured when exposed
- [ ] build IDs or manifest hints were recorded when exposed
- [ ] runtime-discovered assets were mirrored locally or explicitly called out as missing

## A4. Capture Hygiene

- [ ] original raw artifacts were preserved before normalization
- [ ] browser sessions were isolated enough to avoid cross-route contamination
- [ ] screenshot naming is deterministic and route-scoped
- [ ] blocked or flaky routes are documented in `capture-summary.md`
- [ ] `.design-soul/capture/done.signal` exists only after the capture set is complete

---

# PART B: EXTRACTION QUALITY

Run after Waves 0–2 complete.

## B0. File Discovery and Input Integrity

- [ ] all `.html` / `.htm` files discovered and listed in the inventory
- [ ] each page's artifact context is documented and mapped to its parent HTML file or capture route (`_files/`, adjacent local assets, inline-only mode, or `mirror/`)
- [ ] all CSS files were inventoried with file sizes and content-hash deduplication
- [ ] all inline `<style>` blocks were extracted from each HTML file when present
- [ ] input mode was detected and documented (live capture / browser snapshot / adjacent-asset snapshot / SingleFile / source fallback)

## B1. Wave 0 Completeness

- [ ] every in-scope route/page has a `wave0/{page}/done.signal`
- [ ] `exploration.md` exists for every route/page
- [ ] `deobfuscated.css` exists for every route/page with readable traceability
- [ ] `behavior-spec.md` exists where behavior evidence exists
- [ ] `assets/asset-manifest.json` exists where assets were discovered
- [ ] evidence audit in `exploration.md` states whether the source was live-captured or snapshot-based
- [ ] screenshot-grounded completeness notes exist for routes with screenshots

## B2. Wave 0 Grounding

- [ ] all CSS custom properties were extracted and resolved where possible
- [ ] all major sections visible in screenshots appear in the section inventory
- [ ] typography values were extracted from CSS/HTML, not eyeballed
- [ ] color values and gradients were extracted from CSS/HTML, not eyeballed
- [ ] spacing and breakpoint values were extracted from CSS/HTML, not guessed
- [ ] JS-driven behaviors were documented declaratively when evidence existed
- [ ] missing values are marked `UNVERIFIED` instead of replaced with defaults

## B3. Wave 1 Family Integrity

- [ ] every route belongs to exactly one family
- [ ] canonical exemplar choice is documented for each family
- [ ] shared shell is documented explicitly
- [ ] shared blocks are tagged `GLOBAL-SHARED` or `SHARED` where justified
- [ ] route-level overrides are documented instead of erased
- [ ] no family was flattened into a generic template that ignores real structure
- [ ] `wave1/{group}/done.signal` exists only after the anti-drift check passes

## B4. Wave 2 Brief Quality

- [ ] every in-scope page has a `wave2/{page}/agent-brief.md`
- [ ] each brief is self-contained
- [ ] each brief lists route identity and metadata
- [ ] each brief documents sections in actual render order
- [ ] each brief includes tokens, assets, interactions, and responsive rules
- [ ] each brief includes acceptance criteria tied to visual QA
- [ ] `wave2/{page}/done.signal` exists only after completeness review

## B5. Grounding Test

Sample at least 10 values across the extraction:

- 2 colors
- 2 font sizes
- 2 spacing values
- 1 breakpoint
- 1 motion value
- 1 radius or shadow value
- 1 route-family generalization

For each sampled item:

- [ ] it traces to a specific CSS/HTML/runtime artifact
- [ ] the value is exact
- [ ] no rounding or normalization changed the original value
- [ ] the documentation cites or clearly points to the evidence

If any sample fails, extraction is not done.

---

# PART C: BUILD AND VISUAL FIDELITY QUALITY

Run after Waves 3–4 complete.

## C1. Foundation Integrity

- [ ] `nextjs-project/package.json` contains only the allowed baseline dependencies
- [ ] `tokens.ts` covers the extracted token set
- [ ] `globals.css` and Tailwind config use extracted values, not defaults
- [ ] self-hosted fonts and assets exist locally
- [ ] `traceability-matrix.md` exists and is coherent
- [ ] `.design-soul/wave3/foundation-ready.signal` exists only after checks pass

## C2. Build Integrity

- [ ] `npx tsc --noEmit` passes
- [ ] `npm run build` passes
- [ ] no `UNVERIFIED` markers remain in shipped code unless the user explicitly accepted them
- [ ] no forbidden external asset URLs remain in app code or styles
- [ ] no forbidden convenience dependencies were introduced

## C3. Route Coverage

- [ ] every in-scope route resolves to a built page
- [ ] shared shell elements are actually shared in code
- [ ] route families are implemented through reusable blocks where appropriate
- [ ] no family was rebuilt as bespoke duplicated JSX for every sibling route without reason

## C4. Visual QA Artifact Completeness

For every verified route:

- [ ] source desktop screenshot exists
- [ ] build desktop screenshot exists
- [ ] desktop diff artifact exists
- [ ] source tablet screenshot exists
- [ ] build tablet screenshot exists
- [ ] tablet diff artifact exists
- [ ] source mobile screenshot exists
- [ ] build mobile screenshot exists
- [ ] mobile diff artifact exists
- [ ] full-page or scroll-segment compare artifacts exist for long pages
- [ ] `summary.json` exists with measured results and notes

## C5. Visual Fidelity Gates

For every verified route:

- [ ] desktop structure matches the source route
- [ ] tablet structure matches the source route
- [ ] mobile structure matches the source route
- [ ] below-the-fold sections are present and ordered correctly
- [ ] typography is materially faithful
- [ ] spacing rhythm is materially faithful
- [ ] major visuals, illustrations, trust/logo bands, and CTA treatments are faithful
- [ ] header and footer behavior/appearance are faithful
- [ ] known remaining drift is documented explicitly

If the user set a similarity threshold, hit it. If not, use the measured visual summary and document the gap honestly.

## C6. Interaction and Runtime Quality

- [ ] hover and focus states match the extracted behavior
- [ ] scroll-triggered reveals or sticky header changes match the extracted behavior
- [ ] forms and nav interactions are functional, not inert placeholders
- [ ] no console errors appear during route load
- [ ] no missing asset 404s occur during route load
- [ ] no external network requests remain for shipped assets

## C7. Common Failure Modes

Check specifically for these:

- [ ] homepage-only reconstruction disguised as multi-page recovery
- [ ] generic hero/card/CTA systems replacing the real route family structure
- [ ] above-the-fold accuracy with broken or missing lower sections
- [ ] wrong header shell carried across all pages
- [ ] runtime-discovered assets omitted from the rebuild
- [ ] typography approximated instead of extracted
- [ ] button/form interactions visually present but functionally inert
- [ ] customer/story or card links pointing to routes that were never implemented
- [ ] screenshot comparisons run only once with no iteration on obvious failures

---

# Completion Criteria

## Extraction Ready

Extraction is ready for Wave 3 only when:

1. Part B passes
2. all relevant `done.signal` files exist
3. the grounding test passes
4. route families and canonical exemplars are documented

## Build Ready to Claim Success

The build is ready to claim fidelity only when:

1. Part C passes
2. build and type-check pass
3. visual QA artifacts exist for the claimed routes
4. any remaining drift is documented explicitly

> `Looks good` is not a pass condition.
> `Builds successfully` is not a fidelity claim.
> Measured evidence beats confidence.
