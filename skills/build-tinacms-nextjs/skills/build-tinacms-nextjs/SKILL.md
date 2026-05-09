---
name: build-tinacms-nextjs
description: Use skill if you are building or extending TinaCMS-backed Next.js App Router sites with MDX/git-backed content, schema modeling, visual editing, or editorial deployment.
---

# Build TinaCMS Next.js

Build or extend a Next.js App Router site where TinaCMS is the git-backed content layer. The job is usually schema modeling, MDX/rich-text rendering, visual editing, TinaCloud/self-hosted deployment, or TinaCMS-specific debugging.

Use this skill as a router first. Load the smallest reference lane that matches the user goal, then expand only when the implementation needs it. Use [references/00-reference-map.md](references/00-reference-map.md) as the exhaustive catalog for broad research or reference discovery, not as the first stop for ordinary tasks.

## Trigger Boundary

Use this skill for:

- Building or extending a TinaCMS-backed Next.js App Router site.
- Adding TinaCMS to an existing App Router site without rebuilding the whole UI.
- Modeling TinaCMS collections, fields, blocks, MDX/rich-text, media, or SEO content.
- Wiring App Router rendering, metadata, caching, draft mode, or visual editing for TinaCMS data.
- Deploying TinaCMS with TinaCloud or a self-hosted Node.js backend.
- Debugging TinaCMS build, content, rendering, visual editing, Cloud, or self-hosted failures.

Do not use this skill for:

- Generic Next.js work with no TinaCMS surface.
- Converting a live URL, HTML snapshot, or existing website into Next.js before CMS modeling; use `convert-url-to-nextjs`.
- Design-system extraction or SaaS visual analysis without TinaCMS implementation; use `extract-saas-design`.
- Pages Router as the main target. App Router is this skill's trigger; Pages Router references are legacy/fallback only.
- Vite, Astro, Hugo, Gatsby, Remix, or framework-agnostic TinaCMS setup unless the task is only comparing against the App Router path.
- Edge-runtime TinaCMS backend deployment. TinaCMS backend code requires Node.js.

## Check Versions First

Before copying any implementation pattern into a user project:

1. Inspect `package.json`, lockfiles, package manager, `tina/config.*`, `tina/tina-lock.json`, `app/` or `src/app/`, and any `pages/` fallback.
2. Identify installed `tinacms`, `@tinacms/cli`, `next`, `react`, and `react-dom` versions.
3. Check whether the project is App Router, mixed App/Pages, or legacy Pages Router.
4. Check whether it already uses TinaCloud (`clientId`, `token`) or self-hosted (`contentApiUrlOverride`, `/api/tina/gql`, `tina/database.*`).
5. Anchor Next.js-sensitive patterns to the installed version: async `params`, async `draftMode()`, `proxy.ts`, caching APIs, and metadata behavior differ across Next 14/15/16.

Read first:

- [references/setup/01-prerequisites.md](references/setup/01-prerequisites.md)
- [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md)
- [references/setup/05-env-vars.md](references/setup/05-env-vars.md)
- [references/cli/01-overview.md](references/cli/01-overview.md)

Optional read-only helpers:

- `bash scripts/check-tina-versions.sh /path/to/project` - package versions, package manager, App/Pages Router shape, scripts, and next routes. See [scripts/check-tina-versions.md](scripts/check-tina-versions.md).
- `bash scripts/check-tina-env.sh /path/to/project` - env names, config files, generated client, preview/admin/API files, and likely TinaCloud vs self-hosted lane. See [scripts/check-tina-env.md](scripts/check-tina-env.md).

Prefer `pnpm` for greenfield work because the official TinaCMS App Router docs recommend it, but respect an existing project's package manager if its lockfile is consistent. Do not claim npm/yarn are unsupported; treat module-resolution failures as a known failure mode to diagnose.

## Choose Backend Lane Early

| Lane | Choose when | First references | Success check |
|---|---|---|---|
| TinaCloud | Managed auth/API/editorial hosting, standard git-backed path, GitHub integration, fastest setup | [references/concepts/03-tinacloud-vs-self-hosted.md](references/concepts/03-tinacloud-vs-self-hosted.md), [references/tinacloud/01-overview.md](references/tinacloud/01-overview.md), [references/deployment/01-vercel-tinacloud.md](references/deployment/01-vercel-tinacloud.md) | Admin loads, auth works, saves commit to GitHub, queries refresh with `revalidate` or deploy hooks |
| Self-hosted | Full ownership, custom auth, custom storage, private network, enterprise hosting control, or avoiding TinaCloud dependency | [references/self-hosted/00-overview.md](references/self-hosted/00-overview.md), [references/self-hosted/01-architecture.md](references/self-hosted/01-architecture.md), [references/deployment/02-vercel-self-hosted.md](references/deployment/02-vercel-self-hosted.md) | `/api/tina/gql` responds on Node runtime, auth gates writes, DB/git provider configured, no Edge runtime |
| Unknown | User has not supplied constraints | Default to TinaCloud for greenfield unless compliance, auth, storage, or network constraints point to self-hosted | State the lane assumption and verify env/config before implementation |

Do not split this skill into Cloud and self-hosted variants. If the reference set keeps growing, that is a future product decision; this spine routes both lanes inside one skill.

## Detect Intent

| User intent | First hop | Essential follow-ups | Success check |
|---|---|---|---|
| Greenfield TinaCMS + App Router site | [references/workflows/01-greenfield-blog.md](references/workflows/01-greenfield-blog.md) or [references/workflows/02-greenfield-marketing-site.md](references/workflows/02-greenfield-marketing-site.md) | [references/setup/02-new-project-scaffold.md](references/setup/02-new-project-scaffold.md), [references/concepts/03-tinacloud-vs-self-hosted.md](references/concepts/03-tinacloud-vs-self-hosted.md), [references/setup/06-gitignore-and-lockfile.md](references/setup/06-gitignore-and-lockfile.md) | `tinacms dev -c "next dev"` runs, `/admin/index.html` loads, generated client exists, one route renders Tina content |
| Add TinaCMS to existing App Router site | [references/workflows/03-add-cms-to-existing-site.md](references/workflows/03-add-cms-to-existing-site.md) | [references/setup/03-existing-project-add.md](references/setup/03-existing-project-add.md), [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md), [references/schema/01-collections.md](references/schema/01-collections.md), [references/troubleshooting/04-content-errors.md](references/troubleshooting/04-content-errors.md) | Existing routes still work; one migrated content type audits, builds, and renders through Tina |
| Model collections/schema | [references/schema/00-schema-overview.md](references/schema/00-schema-overview.md) | [references/schema/01-collections.md](references/schema/01-collections.md), [references/schema/03-naming-rules.md](references/schema/03-naming-rules.md), [references/schema/04-blocks-pattern.md](references/schema/04-blocks-pattern.md), [references/schema/08-default-collection-set.md](references/schema/08-default-collection-set.md) | `tinacms audit` and `tinacms build` pass; content paths match schema |
| Choose or implement fields | [references/field-types/00-overview.md](references/field-types/00-overview.md) | [references/field-types/06-reference.md](references/field-types/06-reference.md), [references/field-types/07-object.md](references/field-types/07-object.md), [references/toolkit-fields/00-toolkit-overview.md](references/toolkit-fields/00-toolkit-overview.md) when custom widgets are required | Editor form matches the content model; list labels/defaults prevent empty editor states |
| MDX or rich-text body/components | [references/field-types/09-rich-text-mdx.md](references/field-types/09-rich-text-mdx.md) | [references/rendering/04-tinamarkdown.md](references/rendering/04-tinamarkdown.md), [references/rendering/05-mdx-component-mapping.md](references/rendering/05-mdx-component-mapping.md), [references/visual-editing/04-tinamarkdown-tinafield.md](references/visual-editing/04-tinamarkdown-tinafield.md) | MDX renders with expected component mapping in App Router, including nested `children`, not just compile success |
| Dynamic rendering/data fetching/metadata | [references/rendering/01-app-router-pattern.md](references/rendering/01-app-router-pattern.md) | [references/data-fetching/01-overview.md](references/data-fetching/01-overview.md), [references/rendering/09-static-params.md](references/rendering/09-static-params.md), [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md), [references/seo/01-generate-metadata.md](references/seo/01-generate-metadata.md) | Server Component fetches Tina data, Client Component receives `{ data, query, variables }`, route and metadata render under the installed Next version |
| Caching/revalidation | [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md) | [references/data-fetching/04-fetch-options-revalidate.md](references/data-fetching/04-fetch-options-revalidate.md), [references/rendering/10-caching-use-cache.md](references/rendering/10-caching-use-cache.md), [references/deployment/03-deploy-hooks.md](references/deployment/03-deploy-hooks.md) | Deployed edits refresh within the chosen TTL or via webhook-driven revalidation |
| Visual editing and draft/preview | [references/visual-editing/01-overview.md](references/visual-editing/01-overview.md) | [references/visual-editing/02-router-config.md](references/visual-editing/02-router-config.md), [references/visual-editing/05-draft-mode.md](references/visual-editing/05-draft-mode.md), [references/visual-editing/08-proxy-ts.md](references/visual-editing/08-proxy-ts.md), [references/visual-editing/07-debugging-checklist.md](references/visual-editing/07-debugging-checklist.md) | Draft Mode cookie sets, `useTina` updates preview, `data-tina-field` targets DOM, `proxy.ts` or legacy middleware does not block admin/API |
| Deploy with TinaCloud | [references/deployment/01-vercel-tinacloud.md](references/deployment/01-vercel-tinacloud.md) | [references/tinacloud/03-dashboard-registration.md](references/tinacloud/03-dashboard-registration.md), [references/tinacloud/12-vercel-deployment.md](references/tinacloud/12-vercel-deployment.md), [references/deployment/04-team-env-vars.md](references/deployment/04-team-env-vars.md) | Vercel build uses `tinacms build && next build`, env vars exist in deploy target, admin auth and save flow work |
| Self-host TinaCMS | [references/workflows/04-self-host-clerk-mongodb.md](references/workflows/04-self-host-clerk-mongodb.md) or [references/self-hosted/02-nextjs-vercel-starter.md](references/self-hosted/02-nextjs-vercel-starter.md) | [references/self-hosted/tina-backend/01-nextjs-app-route.md](references/self-hosted/tina-backend/01-nextjs-app-route.md), [references/self-hosted/auth-provider/01-overview.md](references/self-hosted/auth-provider/01-overview.md), [references/self-hosted/database-adapter/01-overview.md](references/self-hosted/database-adapter/01-overview.md), [references/self-hosted/git-provider/01-overview.md](references/self-hosted/git-provider/01-overview.md) | Node route handles `/api/tina/gql`, auth provider rejects unauthorized writes, DB and git provider persist edits |
| Team editorial workflow | [references/workflows/05-editorial-workflow-team.md](references/workflows/05-editorial-workflow-team.md) | [references/tinacloud/06-editorial-workflow.md](references/tinacloud/06-editorial-workflow.md), [references/tinacloud/07-webhooks.md](references/tinacloud/07-webhooks.md), [references/tinacloud/09-git-co-authoring.md](references/tinacloud/09-git-co-authoring.md) | Editors save to branches/PRs, preview URL resolves, GitHub write access is verified |
| Static/no-runtime CMS | [references/workflows/06-static-build-no-runtime.md](references/workflows/06-static-build-no-runtime.md) | [references/cli/03-tinacms-build.md](references/cli/03-tinacms-build.md), [references/rendering/09-static-params.md](references/rendering/09-static-params.md), [references/deployment/03-deploy-hooks.md](references/deployment/03-deploy-hooks.md) | All CMS pages pre-render; updates publish through git plus rebuild |
| Debug failures | [references/troubleshooting/01-error-catalog.md](references/troubleshooting/01-error-catalog.md) | Use the symptom table below, then jump to the exact file | Root cause named, fix applied, verification rung stated |

## Preview/Draft Checkpoint

For visual editing or editorial preview tasks, verify all of these before chasing framework bugs:

- `NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`, branch env, and any self-hosted auth/storage env vars are present in the right environment.
- `tina/config.*` has `ui.router` or `ui.previewUrl` where the task needs live URLs.
- App Router has a Draft Mode route and uses async `draftMode()` for Next 15+.
- The page uses the two-component split: Server Component fetches, Client Component calls `useTina(props)`.
- `query`, `variables`, and `data` are all passed to the Client Component.
- `data-tina-field` lands on DOM elements or is forwarded by custom components.
- `proxy.ts` in Next 16, or older `middleware.ts`, does not redirect `/admin`, `/api/preview`, or `/api/tina/*` incorrectly.

## Debug by Symptom

| Symptom | Go directly to | Also check |
|---|---|---|
| Generated client or `tina/__generated__` missing | [references/troubleshooting/02-build-and-types.md](references/troubleshooting/02-build-and-types.md) | [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md) |
| Schema validation/build failure | [references/troubleshooting/03-schema-errors.md](references/troubleshooting/03-schema-errors.md) | [references/schema/03-naming-rules.md](references/schema/03-naming-rules.md) |
| Content missing, `_template`, bad frontmatter | [references/troubleshooting/04-content-errors.md](references/troubleshooting/04-content-errors.md) | [references/schema/02-collection-templates.md](references/schema/02-collection-templates.md) |
| MDX/rich-text rendering failure | [references/field-types/09-rich-text-mdx.md](references/field-types/09-rich-text-mdx.md) | [references/rendering/05-mdx-component-mapping.md](references/rendering/05-mdx-component-mapping.md) |
| Draft/preview mode not enabling | [references/visual-editing/05-draft-mode.md](references/visual-editing/05-draft-mode.md) | [references/troubleshooting/06-visual-editing-issues.md](references/troubleshooting/06-visual-editing-issues.md) |
| Visual editing overlay not appearing | [references/visual-editing/07-debugging-checklist.md](references/visual-editing/07-debugging-checklist.md) | [references/troubleshooting/06-visual-editing-issues.md](references/troubleshooting/06-visual-editing-issues.md) |
| Content stale after save/deploy | [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md) | [references/data-fetching/04-fetch-options-revalidate.md](references/data-fetching/04-fetch-options-revalidate.md) |
| TinaCloud auth/project/token/index errors | [references/troubleshooting/08-tinacloud-issues.md](references/troubleshooting/08-tinacloud-issues.md) | [references/tinacloud/13-troubleshooting.md](references/tinacloud/13-troubleshooting.md) |
| Self-hosted auth/storage/API failures | [references/troubleshooting/05-runtime-errors.md](references/troubleshooting/05-runtime-errors.md) | [references/self-hosted/00-overview.md](references/self-hosted/00-overview.md) |
| Edge runtime incompatibility | [references/deployment/05-edge-runtime-not-supported.md](references/deployment/05-edge-runtime-not-supported.md) | [references/self-hosted/tina-backend/01-nextjs-app-route.md](references/self-hosted/tina-backend/01-nextjs-app-route.md) |
| Corporate firewall/admin network failure | [references/troubleshooting/07-network-and-firewall.md](references/troubleshooting/07-network-and-firewall.md) | [references/tinacloud/02-network-requirements.md](references/tinacloud/02-network-requirements.md) |

Debugging should take at most two hops from this file to the specific troubleshooting document.

## Defaults

- Default to TinaCloud + Vercel + MDX for greenfield App Router projects unless constraints indicate self-hosting.
- Keep Pages Router content as legacy/fallback only. If a project is Pages Router-first, use official docs and do not imply full support from this skill.
- Prefer exact TinaCMS package pins and update `tinacms`, `@tinacms/cli`, and related `@tinacms/*` packages together.
- Respect the existing package manager if the repo already has a clean lockfile; prefer pnpm for new TinaCMS App Router projects.
- Use `tinacms dev -c "next dev"` for local dev and `tinacms build && next build` for production builds.
- Commit `tina/tina-lock.json`; do not commit `tina/__generated__/` or `.tina/__generated__/`.
- Always pass explicit `fetchOptions: { next: { revalidate: N } }` for TinaCMS client queries on Vercel unless the route is intentionally static-only.
- Use `ui.router` for collections that need live preview or visual editing.
- Use `defaultItem` for block templates and `ui.itemProps` for list fields that editors will manipulate.

## Hard Rules

- Do not call `useTina()` in a Server Component; put it in a `"use client"` component.
- Do not place `data-tina-field` on React component wrappers unless the component forwards it to a DOM element.
- Do not import frontend-only code into `tina/config.*`.
- Do not use collection `templates` unless documents genuinely have multiple shapes; use `fields` for one shape.
- Do not ship a dev admin build. CI must run `tinacms build`, not `tinacms dev`.
- Do not access `cookies()`, `headers()`, or `searchParams` inside a `"use cache"` scope.
- Do not deploy TinaCMS under a sub-path such as `example.com/blog`; route admin at the domain root or separate domain.
- Do not install with `--no-optional` or `--omit=optional` when debugging TinaCMS module resolution.
- Do not deploy self-hosted TinaCMS to Cloudflare Workers, Vercel Edge Functions, or any V8-isolate runtime.
- Do not use hyphens, spaces, or special characters in field names. Use alphanumeric and underscores.
- Do not use reserved names: `children` in the wrong context, `mark`, `_template`, `_sys`, `id`, `__typename`.
- Do not put Tina build-required env vars only in `.env.local`; Tina build reads `.env` or host-provided env.
- Do not manually edit generated Tina files.
- Do not commit raw passwords for self-hosted users; hash them.

## Output Contract

For greenfield/build tasks, deliver:

- Code changes for setup, schema, content model, rendering, and deployment lane.
- Commands run and their results: install, `tinacms build`, typecheck/build, and local dev when feasible.
- Validation result showing generated client, admin route, and at least one rendered content route.

For migration/add-to-existing tasks, deliver:

- Touched routes, components, content paths, package scripts, and env/config names.
- Version, package-manager, App Router, and backend-lane assumptions.
- Regression checks for existing routes plus the new TinaCMS route.

For deployment tasks, deliver:

- TinaCloud or self-hosted lane decision and why.
- Env vars/config names verified without exposing secret values.
- Provider-specific build/runtime checks, including Node runtime for self-hosted.

For debugging tasks, deliver:

- Symptom, root cause, exact reference used, fix, and verification rung.
- If only static checks passed, say runtime was not exercised.

## Verification Rungs

- Skill edit: run `python3 scripts/validate-skills.py`; if unrelated repo-wide failures exist, report them separately and verify no new target-skill errors.
- Package/static checks: inspect package versions, lockfile, App Router files, `tina/config.*`, env var names, `.gitignore`, and `tina/tina-lock.json`.
- Tina checks: run `tinacms audit` where relevant, then `tinacms build`; verify `tina/__generated__/client.*` exists.
- App checks: run the repo's typecheck/lint/build command; verify `tinacms build` precedes `next build`.
- Runtime checks: run local dev with `tinacms dev -c "next dev"`, open `/admin/index.html`, render at least one App Router route.
- Visual editing checks: enable Draft Mode, observe `useTina` updates, click `data-tina-field` targets, and verify `proxy.ts`/middleware does not block admin or Tina APIs.
- Deployment checks: verify env vars in the provider, build logs, Node runtime for self-hosted backend, content save path, and cache/revalidation behavior.

## Reference Routing

Use these globs as the exhaustive reference catalog. Load only the lane you need:

- Topic catalog: [references/00-reference-map.md](references/00-reference-map.md)
- Concepts and architecture: [references/concepts/*.md](references/concepts/*.md)
- Setup and project integration: [references/setup/*.md](references/setup/*.md)
- Tina config: [references/config/*.md](references/config/*.md)
- Schema modeling: [references/schema/*.md](references/schema/*.md)
- Field types and MDX: [references/field-types/*.md](references/field-types/*.md)
- Custom field toolkit: [references/toolkit-fields/*.md](references/toolkit-fields/*.md)
- App Router rendering: [references/rendering/*.md](references/rendering/*.md)
- Visual editing and preview: [references/visual-editing/*.md](references/visual-editing/*.md)
- Data fetching and generated clients: [references/data-fetching/*.md](references/data-fetching/*.md)
- GraphQL operations: [references/graphql/*.md](references/graphql/*.md)
- SEO and metadata: [references/seo/*.md](references/seo/*.md)
- Media storage: [references/media/*.md](references/media/*.md)
- TinaCloud lane: [references/tinacloud/*.md](references/tinacloud/*.md)
- Self-hosted lane: [references/self-hosted/*.md](references/self-hosted/*.md), [references/self-hosted/tina-backend/*.md](references/self-hosted/tina-backend/*.md), [references/self-hosted/auth-provider/*.md](references/self-hosted/auth-provider/*.md), [references/self-hosted/database-adapter/*.md](references/self-hosted/database-adapter/*.md), [references/self-hosted/git-provider/*.md](references/self-hosted/git-provider/*.md)
- CLI: [references/cli/*.md](references/cli/*.md)
- Deployment: [references/deployment/*.md](references/deployment/*.md)
- End-to-end workflows: [references/workflows/*.md](references/workflows/*.md)
- Troubleshooting: [references/troubleshooting/*.md](references/troubleshooting/*.md)
