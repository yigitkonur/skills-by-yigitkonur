# Mission Brief: Academy LMS & Educational Funnel Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

The Academy platform houses interactive structured curricula, lesson modules, progress tracking, and video lectures.
Current routes: `AcademyHubRoute.astro`, `AcademyModuleRoute.astro`, and `AcademyLessonRoute.astro`.
A previous audit revealed a dense cluster of `client:load` directives in Academy routes (`ModuleLessonsIsland`, video controllers). In Astro, loading entire course syllabi with `client:load` degrades mobile Time to Interactive (TTI) and inflates Total Blocking Time (TBT).

Astro Architectural & Best Practice Rules:

- **Route Specificity & Collision Resolution ([03-route-priority-and-collision-resolution.md](../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md))**:
  Astro enforces a strict 8-tier route priority matrix. Static routes (`academy/index.astro`, `academy/certificates.astro`) take precedence over dynamic routes (`academy/[course].astro`), which in turn take precedence over nested dynamic routes (`academy/[course]/[lesson].astro`). Route collision ambiguity must be eliminated by ensuring static hubs are never shadowed by dynamic slug parameters.
- **Built-in Pagination & Navigation Metadata ([06-built-in-pagination-and-nested-pagination.md](../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md))**:
  Academy course catalogs and category archives must use Astro's native `paginate()` helper. For nested category pagination (`academy/category/[cat]/[page].astro`), use `paginate(courses, { params: { cat }, pageSize: 12 })` to inject typed `Page<T>` contracts rather than rolling manual array chunking (`slice((page-1)*limit, ...)`).
- **SSR On-Demand vs Static Prerendering ([07-ssr-on-demand-routes-vs-prerendering.md](../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md))**:
  Course content and syllabus pages pre-render statically at build time. Any personalized live student dashboard or examination verification route must explicitly declare `export const prerender = false` and resolve dynamic user state via `Astro.params` and `Astro.locals`, never combining `prerender = false` with `getStaticPaths()`.
- **Prerender Boundary for Dynamic Endpoints ([02-prerender-boundary-dynamic-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md))**:
  Interactive Academy endpoints (e.g. `/api/academy/progress.json.ts`, quiz submissions, and certificate generators) must explicitly declare `export const prerender = false;`. Without this flag, endpoints execute once at build time and reject incoming HTTP POST requests in production.
- **APIRoute Signature & Standard Web Response ([03-apiroute-signature-and-web-response.md](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md))**:
  All Academy mutation and status endpoints must use Astro's `APIRoute` type and return standard Web API `Response` or `Response.json(...)`. Returning raw objects or Express-style `res.json()` causes fatal runtime errors.
- **Explicit HTTP Method Handlers & Method Guards ([06-http-method-handlers-and-method-guards.md](../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md))**:
  Export explicit uppercase method handlers (`export const GET: APIRoute`, `export const POST: APIRoute`). Never use monolithic `switch (request.method)` handlers under `ALL`. Explicit exports ensure automatic `HEAD` handling and clean 405 Method Not Allowed semantics.
- **Static Leaf Islands over Mega-Islands**: In LMS curricula with multi-tiered modules, wrapping entire lesson lists in interactive React mega-islands (`ModuleLessonsIsland`) forces Astro to serialize and ship the entire syllabus data tree and DOM markup to the client. The syllabus structure must render as zero-JS native Astro HTML, embedding only isolated interactive leaf islands (e.g. lesson completion toggles or video progress bookmarks).
- **Hydration Rule**: Never default blindly to `client:load`. Heavy educational media widgets and below-the-fold lesson quizzes must utilize `client:visible={{ rootMargin: '200px' }}` or `client:idle`, eliminating main-thread contention during initial page paint.
- **Memory Scaling Rule**: In `getStaticPaths()` for large course catalogs (hundreds of modules and lessons), only return lightweight identifiers (`{ moduleId, lessonSlug }`) in route props. Avoid passing uncompressed video transcripts or relational graphs in `props`, fetching detailed lesson data on-demand during individual page compilation to avoid Node.js heap exhaustion (`ERR_WORKER_OUT_OF_MEMORY`).

Critical files to inspect:

- `src/features/academy/components/AcademyHubRoute.astro`
- `src/features/academy/components/AcademyModuleRoute.astro`
- `src/features/academy/components/AcademyLessonRoute.astro`
- `src/features/academy/data/academy.ts`

## 3.2 Mission Objective

Examine all Academy LMS route controllers, lesson player components, dynamic endpoints, and course catalogs.
Outcome: Deliver a concrete hydration migration plan to transition Academy islands from `client:load` to `client:visible` or `client:idle` without degrading user interactive state, enforce route priority invariants, verify endpoint prerender boundaries, and optimize `getStaticPaths` props payload.
Constraints: Read-only audit; ensure interactive course progress tracking remains responsive.
Autonomy Grant: You own this mission end-to-end. Profile island hydration timing, interactive state transitions, and lesson navigation. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `AcademyModuleRoute.astro` line 190: analyze why `ModuleLessonsIsland` was set to `client:load`.
2. Inspect `AcademyLessonRoute.astro` lines 220-275: analyze lesson player and quiz island hydration points.
3. Determine if lesson navigation can be pre-rendered statically with zero-JS and hydrated only upon user interaction.
4. Audit `getStaticPaths()` implementations in academy routes to ensure route `props` do not leak uncompressed course transcripts.
5. Audit route specificity: verify that static academy paths (`/academy/certificates`, `/academy/faq`) are not shadowed by `src/pages/academy/[course].astro`.
6. Audit dynamic endpoints: check that progress tracking and quiz submission APIs declare `export const prerender = false`.

### ❌ Bad Practice / Anti-Pattern: Mega-Island Hydration & Bloated getStaticPaths Props

```astro
---
// src/pages/academy/[course]/[lesson].astro - Mega-island with client:load & bloated props
export async function getStaticPaths() {
  const fullCourses = await fetchAllCoursesWithTranscripts(); // Heavy multi-MB payload
  return fullCourses.flatMap(course =>
    course.lessons.map(lesson => ({
      params: { course: course.slug, lesson: lesson.slug },
      props: { course, lesson } // OOM hazard: retains all transcripts in Node memory!
    }))
  );
}
const { course, lesson } = Astro.props;
---
<!-- Mega-island: Hydrates entire syllabus tree and static content on critical load -->
<ModuleLessonsIsland course={course} currentLesson={lesson} client:load />
```

_Why this fails:_ Retaining full course curricula across hundreds of routes in `props` causes Node.js heap exhaustion (`ERR_WORKER_OUT_OF_MEMORY`). Using `client:load` on `ModuleLessonsIsland` ships entire course syllabus markup as client JS, destroying mobile TTI.

### ✅ Best Practice / Idiomatic: Lightweight Props & Static Leaf Islands

```astro
---
// src/pages/academy/[course]/[lesson].astro - Lightweight props & static leaf island
// Reference: ../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md
import type { GetStaticPaths } from "astro";
import LessonProgressToggle from "../components/LessonProgressToggle.tsx";

export const getStaticPaths = (async () => {
  const courseIndex = await fetchCourseRouteIndex(); // Lightweight slug & ID only
  return courseIndex.flatMap(c =>
    c.lessons.map(l => ({
      params: { course: c.slug, lesson: l.slug },
      props: { lessonId: l.id } // Only lightweight primitive passed
    }))
  );
}) satisfies GetStaticPaths;

const { lessonId } = Astro.props;
const lesson = await fetchLessonById(lessonId); // Resolved per page & garbage-collected
---
<article class="lesson-layout">
  <!-- Static zero-JS syllabus rendered by Astro -->
  <nav class="syllabus-nav">
    <ul>{lesson.syllabus.map(item => <li><a href={item.url}>{item.title}</a></li>)}</ul>
  </nav>
  <!-- Surgical leaf island hydrated with rootMargin before entering viewport -->
  <LessonProgressToggle lessonId={lesson.id} client:visible={{ rootMargin: '200px' }} />
</article>
```

### ❌ Bad Practice / Anti-Pattern: Manual Catalog Pagination & Query Math

```astro
---
// src/pages/academy/courses/[page].astro
// Rolling custom pagination logic with manual URL query math instead of Astro's native paginate()
export async function getStaticPaths() {
  const courses = await fetchAllCourses();
  const limit = 12;
  const pages = Math.ceil(courses.length / limit);
  return Array.from({ length: pages }, (_, i) => ({
    params: { page: String(i + 1) },
    props: { courses: courses.slice(i * limit, (i + 1) * limit) }
  }));
}
---
```

### ✅ Best Practice / Idiomatic: Native paginate() Helper with Typed Page

```astro
---
// src/pages/academy/courses/[page].astro
// Reference: ../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md
import type { GetStaticPaths, Page } from "astro";
import { getCourseList } from "@/features/academy/data/academy";

export const getStaticPaths = (async ({ paginate }) => {
  const courses = await getCourseList();
  return paginate(courses, { pageSize: 12 });
}) satisfies GetStaticPaths;

interface Props {
  page: Page<CourseItem>;
}
const { page } = Astro.props;
---
<nav aria-label="Course Pagination">
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  <span>Page {page.currentPage} of {page.lastPage}</span>
  {page.url.next && <a href={page.url.next}>Next</a>}
</nav>
```

### ❌ Bad Practice / Anti-Pattern: Missing SSR Prerender Boundary on Progress Mutation

```ts
// src/pages/api/academy/progress.ts
// Missing prerender = false: In Astro static mode, executes ONCE at build time!
import type { APIRoute } from 'astro'

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json()
  // Fails in production: live user progress is never saved!
  return new Response(JSON.stringify({ updated: true }))
}
```

### ✅ Best Practice / Idiomatic: Explicit prerender = false & Typed APIRoute

```ts
// src/pages/api/academy/progress.ts
// Reference: ../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md
import type { APIRoute } from 'astro'

export const prerender = false

export const POST: APIRoute = async ({ request, locals }) => {
  if (request.headers.get('Content-Type') !== 'application/json') {
    return Response.json({ error: 'Invalid Content-Type' }, { status: 400 })
  }

  const payload = await request.json()
  const saved = await updateStudentProgress(payload)

  return Response.json(
    { success: true, progress: saved },
    {
      status: 200,
      headers: { 'Cache-Control': 'private, no-cache, no-store' },
    },
  )
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`, `RULE-ID: 03-routing-and-pages/06-built-in-pagination-and-nested-pagination`, `RULE-ID: 03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering`, `RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "08-ACADEMY-LMS-LEARNING-PLATFORM-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, validates the checklist (<= 200 items, <= 3 levels nesting), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/issue-body.md" \
  --title "[Audit - Academy LMS & Educational Funnel Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Document each `client:load` call site in academy templates with its payload size and downgrade recommendation (`client:visible={{ rootMargin: '200px' }}` or `client:idle`).
2. Run `grep -rn "client:load" src/features/academy/` to identify all critical-path hydration points.
3. Run `git grep -n "prerender = false" src/pages/` to audit all on-demand SSR routes and dynamic progress endpoints.
4. Run `git grep -n "paginate(" src/pages/` to verify native Astro pagination in course listing archives.
5. Run `git grep -n "export const POST\|export const GET" src/pages/api/` to audit dynamic endpoint method handlers.
6. Verify that course schema JSON-LD matches Google Course Schema specification (`curl -s http://localhost:4321/academy | grep -i '"@type": "Course"'`).
7. Profile memory during build generation via `NODE_OPTIONS="--max-old-space-size=4096" pnpm astro check && pnpm astro build`.
8. Check emitted client chunks: verify that static syllabus markup is not leaked into client JS bundles (`grep -rn "ModuleLessonsIsland" dist/_astro/*.js || true`).

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Academy LMS & Educational Funnel Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/findings.json` (N defects logged)
   - `file://docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/08-academy-lms-learning-platform/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
