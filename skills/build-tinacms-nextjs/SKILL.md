---
name: build-tinacms-nextjs
description: Use skill if you are building or extending a TinaCMS-backed Next.js App Router site with tina/config.ts, MDX/git-backed content, schema modeling, useTina visual editing, or TinaCloud/self-hosted deploys.
---

# Build TinaCMS Next.js

Build, extend, and debug a Next.js **App Router** site whose content layer is **TinaCMS** (git-backed MDX/JSON, GraphQL on top, optional visual editing). This file is the router: detect the project shape, pick the lane, jump to the smallest reference set, deliver the change, verify it.

## When To Use

- *"Add TinaCMS to my Next.js 14/15/16 App Router site."*
- *"Model a `posts` / `pages` / `blocks` collection in `tina/config.ts`."*
- *"Render an MDX/`rich-text` body via `useTina` and `<TinaMarkdown>` in `app/[slug]/page.tsx`."*
- *"Wire visual editing, draft mode, `data-tina-field`, `proxy.ts`, or live preview."*
- *"Deploy a TinaCloud site to Vercel"* or *"self-host the Tina backend with Clerk + MongoDB."*
- *"Debug `tinacms build` failures, missing generated client, schema/MDX errors, stale Vercel cache, or admin auth."*
- *"Migrate from Pages Router or from TinaCloud to self-hosted."*

Do **NOT** use this skill for:

- Plain Next.js work with **no** TinaCMS surface (no `tina/`, no `tinacms` in `package.json`).
- Converting a live URL or HTML snapshot to Next.js *before* CMS modeling — use `convert-url-to-nextjs`.
- Pages Router as the primary target — App Router is the trigger; Pages references here are legacy.
- Edge-runtime backend deploys (Cloudflare Workers, Vercel Edge). Tina backend requires Node.js.

## Detect TinaCMS In The Repo (First Hop)

Before drafting any code, run these scans against the user's project. Strong signals mean the skill is correctly engaged:

| Signal | Meaning |
|---|---|
| `tina/config.ts` or `tina/config.tsx` | TinaCMS project — required |
| `tina/tina-lock.json` | Schema lockfile — must be committed |
| `tina/__generated__/` or `.tina/__generated__/` | Generated client — must be **gitignored** |
| `tinacms`, `@tinacms/cli` in `package.json` | TinaCMS install |
| `tinacms dev -c "next dev"` in scripts | App Router + Tina dev script |
| `import { useTina } from "tinacms/dist/react"` | Visual-editing hook — Client Component only |
| `import { client } from "@/tina/__generated__/client"` | Generated GraphQL client |
| `app/api/tina/[...routes]/route.ts` | Self-hosted backend route |
| `NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`, `NEXT_PUBLIC_TINA_BRANCH` | TinaCloud env |
| `proxy.ts` (Next 16+) or `middleware.ts` | May block `/admin`, `/api/tina/*` — inspect |

Optional read-only helpers (do not modify the project):

- `bash scripts/check-tina-versions.sh /path/to/project` — package versions, package manager, App/Pages Router shape, scripts, routes. See [scripts/check-tina-versions.md](scripts/check-tina-versions.md).
- `bash scripts/check-tina-env.sh /path/to/project` — env names, config files, generated client, preview/admin/API files, likely lane. See [scripts/check-tina-env.md](scripts/check-tina-env.md).

Read first: [references/setup/01-prerequisites.md](references/setup/01-prerequisites.md), [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md), [references/setup/05-env-vars.md](references/setup/05-env-vars.md), [references/cli/01-overview.md](references/cli/01-overview.md), [references/setup/07-agent-automation.md](references/setup/07-agent-automation.md).

## Hard Rules (Top-Loaded)

These rules cause the most expensive failures. Honor them before chasing framework bugs.

- **Server vs Client split.** `useTina()` is a Client hook. The page (Server Component) fetches `{ data, query, variables }` from the generated client; a `"use client"` child receives those three props and calls `useTina(props)`. See [references/rendering/01-app-router-pattern.md](references/rendering/01-app-router-pattern.md), [references/rendering/03-usetina-hook.md](references/rendering/03-usetina-hook.md).
- **`data-tina-field` lands on DOM elements**, not React component wrappers. Custom components must forward the attribute to a real DOM node, or the visual-editing overlay misses.
- **`tinacms build` precedes `next build`.** CI runs `tinacms build && next build`. Never ship a `tinacms dev` artifact. See [references/cli/03-tinacms-build.md](references/cli/03-tinacms-build.md).
- **Pin `tinacms`, `@tinacms/cli`, and all `@tinacms/*` to the same version** and update them together.
- **Commit `tina/tina-lock.json`. Never commit `tina/__generated__/`.** See [references/setup/06-gitignore-and-lockfile.md](references/setup/06-gitignore-and-lockfile.md).
- **No frontend imports in `tina/config.*`.** Tina builds the config in a separate Node bundle; UI imports break the build.
- **Field-name discipline.** Alphanumeric + underscore only. No hyphens, spaces, or reserved names: `children` (in wrong context), `mark`, `_template`, `_sys`, `id`, `__typename`. See [references/field-types/11-reserved-names.md](references/field-types/11-reserved-names.md), [references/schema/03-naming-rules.md](references/schema/03-naming-rules.md).
- **Use `fields:` for one document shape; `templates:` only when documents genuinely have multiple shapes.** See [references/schema/02-collection-templates.md](references/schema/02-collection-templates.md).
- **Vercel + TinaCMS clients must pass explicit revalidation.** Pass `fetchOptions: { next: { revalidate: N } }` on every Tina query, or content goes stale forever. See [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md), [references/data-fetching/04-fetch-options-revalidate.md](references/data-fetching/04-fetch-options-revalidate.md).
- **Next 15+: `params`, `searchParams`, `draftMode()`, `cookies()`, `headers()` are async.** Await them. Never use them inside a `"use cache"` scope.
- **No `proxy.ts` / `middleware.ts` rewrites that touch `/admin`, `/api/preview`, or `/api/tina/*`.** See [references/visual-editing/08-proxy-ts.md](references/visual-editing/08-proxy-ts.md).
- **Self-hosted Tina backend = Node runtime only.** Never deploy to Cloudflare Workers, Vercel Edge, or any V8 isolate. See [references/deployment/05-edge-runtime-not-supported.md](references/deployment/05-edge-runtime-not-supported.md).
- **Admin must live at the domain root or its own subdomain.** Never `example.com/blog/admin`.
- **Hash self-hosted user passwords. Never commit raw credentials.**
- **Never edit `tina/__generated__/*` or `.tina/__generated__/*` by hand.**
- **Tina build env reads `.env` / host env, not `.env.local`.** Build env vars must exist where the build actually runs.
- **Never install with `--no-optional` / `--omit=optional`** when debugging Tina module resolution.

## Choose Backend Lane Early

| Lane | Choose when | First references | Success check |
|---|---|---|---|
| **TinaCloud** | Managed auth/API, fastest path, GitHub integration, greenfield default | [references/concepts/03-tinacloud-vs-self-hosted.md](references/concepts/03-tinacloud-vs-self-hosted.md), [references/tinacloud/01-overview.md](references/tinacloud/01-overview.md), [references/deployment/01-vercel-tinacloud.md](references/deployment/01-vercel-tinacloud.md) | Admin loads, edits commit to GitHub, queries refresh via `revalidate`/deploy hook |
| **Self-hosted** | Custom auth, custom storage, private network, enterprise control, no TinaCloud dependency | [references/self-hosted/00-overview.md](references/self-hosted/00-overview.md), [references/self-hosted/01-architecture.md](references/self-hosted/01-architecture.md), [references/deployment/02-vercel-self-hosted.md](references/deployment/02-vercel-self-hosted.md) | `/api/tina/gql` responds on Node runtime, auth gates writes, DB + git provider configured |
| **Unknown** | User has not specified | Default to **TinaCloud** for greenfield unless compliance / auth / storage / network constraints point to self-hosted | State the assumption before scaffolding |

Do not split this skill into Cloud and self-hosted variants. One spine; two lanes.

## Detect Intent → First Reference Hop

| User intent | First hop | Essential follow-ups | Success check |
|---|---|---|---|
| Greenfield TinaCMS + App Router | [references/workflows/01-greenfield-blog.md](references/workflows/01-greenfield-blog.md) or [references/workflows/02-greenfield-marketing-site.md](references/workflows/02-greenfield-marketing-site.md) | [references/setup/02-new-project-scaffold.md](references/setup/02-new-project-scaffold.md), [references/concepts/03-tinacloud-vs-self-hosted.md](references/concepts/03-tinacloud-vs-self-hosted.md), [references/setup/06-gitignore-and-lockfile.md](references/setup/06-gitignore-and-lockfile.md) | `tinacms dev -c "next dev"` runs, `/admin/index.html` loads, generated client exists, one Tina-backed route renders |
| Add Tina to existing App Router site | [references/workflows/03-add-cms-to-existing-site.md](references/workflows/03-add-cms-to-existing-site.md) | [references/setup/03-existing-project-add.md](references/setup/03-existing-project-add.md), [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md), [references/schema/01-collections.md](references/schema/01-collections.md), [references/troubleshooting/04-content-errors.md](references/troubleshooting/04-content-errors.md) | Existing routes intact; one migrated content type audits, builds, renders through Tina |
| Model collections / schema | [references/schema/00-schema-overview.md](references/schema/00-schema-overview.md) | [references/schema/01-collections.md](references/schema/01-collections.md), [references/schema/03-naming-rules.md](references/schema/03-naming-rules.md), [references/schema/04-blocks-pattern.md](references/schema/04-blocks-pattern.md), [references/schema/05-reusable-field-groups.md](references/schema/05-reusable-field-groups.md), [references/schema/06-content-hooks.md](references/schema/06-content-hooks.md), [references/schema/07-list-ui-customization.md](references/schema/07-list-ui-customization.md), [references/schema/08-default-collection-set.md](references/schema/08-default-collection-set.md) | `tinacms audit` and `tinacms build` pass; content paths match schema |
| Choose / implement fields | [references/field-types/00-overview.md](references/field-types/00-overview.md) | [references/field-types/01-string.md](references/field-types/01-string.md), [references/field-types/02-number.md](references/field-types/02-number.md), [references/field-types/03-boolean.md](references/field-types/03-boolean.md), [references/field-types/04-datetime.md](references/field-types/04-datetime.md), [references/field-types/05-image.md](references/field-types/05-image.md), [references/field-types/06-reference.md](references/field-types/06-reference.md), [references/field-types/07-object.md](references/field-types/07-object.md), [references/toolkit-fields/00-toolkit-overview.md](references/toolkit-fields/00-toolkit-overview.md) when custom widgets are required | Editor form matches the model; `defaultItem` and `ui.itemProps` prevent empty editor states |
| MDX / rich-text body + custom components | [references/field-types/09-rich-text-mdx.md](references/field-types/09-rich-text-mdx.md) | [references/field-types/08-rich-text-markdown.md](references/field-types/08-rich-text-markdown.md), [references/field-types/10-markdown-shortcodes.md](references/field-types/10-markdown-shortcodes.md), [references/rendering/04-tinamarkdown.md](references/rendering/04-tinamarkdown.md), [references/rendering/05-mdx-component-mapping.md](references/rendering/05-mdx-component-mapping.md), [references/rendering/06-overriding-builtins.md](references/rendering/06-overriding-builtins.md), [references/rendering/07-mermaid-diagrams.md](references/rendering/07-mermaid-diagrams.md), [references/rendering/08-block-renderer.md](references/rendering/08-block-renderer.md), [references/visual-editing/04-tinamarkdown-tinafield.md](references/visual-editing/04-tinamarkdown-tinafield.md) | MDX renders with mapped components in App Router, including nested `children` |
| Dynamic page rendering / data fetching / metadata | [references/rendering/01-app-router-pattern.md](references/rendering/01-app-router-pattern.md) | [references/rendering/03-usetina-hook.md](references/rendering/03-usetina-hook.md), [references/data-fetching/01-overview.md](references/data-fetching/01-overview.md), [references/data-fetching/02-generated-client.md](references/data-fetching/02-generated-client.md), [references/data-fetching/03-custom-queries.md](references/data-fetching/03-custom-queries.md), [references/rendering/09-static-params.md](references/rendering/09-static-params.md), [references/seo/01-generate-metadata.md](references/seo/01-generate-metadata.md) | Server fetches Tina data, Client receives `{ data, query, variables }`, route + metadata render under installed Next version |
| Caching / revalidation | [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md) | [references/data-fetching/04-fetch-options-revalidate.md](references/data-fetching/04-fetch-options-revalidate.md), [references/rendering/10-caching-use-cache.md](references/rendering/10-caching-use-cache.md), [references/deployment/03-deploy-hooks.md](references/deployment/03-deploy-hooks.md) | Deployed edits refresh within chosen TTL or via webhook revalidation |
| Visual editing + draft / preview | [references/visual-editing/01-overview.md](references/visual-editing/01-overview.md) | [references/visual-editing/02-router-config.md](references/visual-editing/02-router-config.md), [references/visual-editing/03-tinafield-helper.md](references/visual-editing/03-tinafield-helper.md), [references/visual-editing/05-draft-mode.md](references/visual-editing/05-draft-mode.md), [references/visual-editing/06-edit-state-hook.md](references/visual-editing/06-edit-state-hook.md), [references/visual-editing/07-debugging-checklist.md](references/visual-editing/07-debugging-checklist.md), [references/visual-editing/08-proxy-ts.md](references/visual-editing/08-proxy-ts.md) | Draft Mode cookie sets, `useTina` updates preview, `data-tina-field` targets DOM, `proxy.ts`/middleware does not block admin/API |
| Tina config (provider, branch, admin, client, paths) | [references/config/01-config-anatomy.md](references/config/01-config-anatomy.md) | [references/config/02-build-and-server.md](references/config/02-build-and-server.md), [references/config/03-admin-and-ui.md](references/config/03-admin-and-ui.md), [references/config/04-branch-resolution.md](references/config/04-branch-resolution.md), [references/config/05-client-and-content-api.md](references/config/05-client-and-content-api.md), [references/config/06-typescript-path-aliases.md](references/config/06-typescript-path-aliases.md) | `tina/config.*` parses, build server resolves, admin route serves, branch resolves correctly |
| GraphQL queries / pagination / sorting | [references/graphql/01-overview.md](references/graphql/01-overview.md) | [references/graphql/02-get-document.md](references/graphql/02-get-document.md), [references/graphql/03-query-documents.md](references/graphql/03-query-documents.md), [references/graphql/04-filter-documents.md](references/graphql/04-filter-documents.md), [references/graphql/05-sorting.md](references/graphql/05-sorting.md), [references/graphql/06-pagination.md](references/graphql/06-pagination.md), [references/graphql/07-performance.md](references/graphql/07-performance.md), [references/graphql/08-limitations.md](references/graphql/08-limitations.md), [references/graphql/09-add-document.md](references/graphql/09-add-document.md), [references/graphql/10-update-document.md](references/graphql/10-update-document.md), [references/data-fetching/05-graphql-cli.md](references/data-fetching/05-graphql-cli.md) | Query returns expected shape; `tinacms graphql` reproduces it |
| SEO / OG / sitemap / RSS | [references/seo/01-generate-metadata.md](references/seo/01-generate-metadata.md) | [references/seo/02-description-waterfall.md](references/seo/02-description-waterfall.md), [references/seo/03-og-image-waterfall.md](references/seo/03-og-image-waterfall.md), [references/seo/04-json-ld-structured-data.md](references/seo/04-json-ld-structured-data.md), [references/seo/05-dynamic-og-images.md](references/seo/05-dynamic-og-images.md), [references/seo/06-sitemap-and-robots.md](references/seo/06-sitemap-and-robots.md), [references/seo/07-rss-feed.md](references/seo/07-rss-feed.md) | `generateMetadata` resolves, sitemap/RSS render at runtime |
| Media (Cloudinary / S3 / Vercel Blob / DO Spaces) | [references/media/01-repo-based-default.md](references/media/01-repo-based-default.md) | [references/media/02-accepted-types.md](references/media/02-accepted-types.md), [references/media/03-cloudinary.md](references/media/03-cloudinary.md), [references/media/04-s3.md](references/media/04-s3.md), [references/media/05-do-spaces.md](references/media/05-do-spaces.md), [references/media/06-vercel-blob.md](references/media/06-vercel-blob.md), [references/media/07-external-auth.md](references/media/07-external-auth.md) | Media uploads land in store, public URL renders, types enforced |
| Custom field components / toolkit | [references/toolkit-fields/00-toolkit-overview.md](references/toolkit-fields/00-toolkit-overview.md) | [references/toolkit-fields/01-text-textarea-number.md](references/toolkit-fields/01-text-textarea-number.md), [references/toolkit-fields/02-image-color.md](references/toolkit-fields/02-image-color.md), [references/toolkit-fields/03-toggle-radio-select.md](references/toolkit-fields/03-toggle-radio-select.md), [references/toolkit-fields/04-tags-list.md](references/toolkit-fields/04-tags-list.md), [references/toolkit-fields/05-group-and-group-list.md](references/toolkit-fields/05-group-and-group-list.md), [references/toolkit-fields/06-date-markdown-html.md](references/toolkit-fields/06-date-markdown-html.md), [references/toolkit-fields/07-custom-field-component.md](references/toolkit-fields/07-custom-field-component.md) | Custom widget loads in admin, value round-trips to content file |
| Concepts / architecture refresher | [references/concepts/01-what-is-tinacms.md](references/concepts/01-what-is-tinacms.md) | [references/concepts/02-tina-folder-anatomy.md](references/concepts/02-tina-folder-anatomy.md), [references/concepts/04-data-layer-architecture.md](references/concepts/04-data-layer-architecture.md) | Mental model confirmed before structural decisions |
| CLI commands / init / graphql | [references/cli/01-overview.md](references/cli/01-overview.md) | [references/cli/02-tinacms-dev.md](references/cli/02-tinacms-dev.md), [references/cli/03-tinacms-build.md](references/cli/03-tinacms-build.md), [references/cli/04-graphql-commands.md](references/cli/04-graphql-commands.md), [references/cli/05-init-and-init-backend.md](references/cli/05-init-and-init-backend.md) | Right command for the lifecycle stage |
| Deploy with TinaCloud | [references/deployment/01-vercel-tinacloud.md](references/deployment/01-vercel-tinacloud.md) | [references/tinacloud/01-overview.md](references/tinacloud/01-overview.md), [references/tinacloud/02-network-requirements.md](references/tinacloud/02-network-requirements.md), [references/tinacloud/03-dashboard-registration.md](references/tinacloud/03-dashboard-registration.md), [references/tinacloud/04-projects.md](references/tinacloud/04-projects.md), [references/tinacloud/05-users-and-orgs.md](references/tinacloud/05-users-and-orgs.md), [references/tinacloud/08-search.md](references/tinacloud/08-search.md), [references/tinacloud/10-api-versioning.md](references/tinacloud/10-api-versioning.md), [references/tinacloud/11-github-enterprise.md](references/tinacloud/11-github-enterprise.md), [references/tinacloud/12-vercel-deployment.md](references/tinacloud/12-vercel-deployment.md), [references/deployment/04-team-env-vars.md](references/deployment/04-team-env-vars.md) | Vercel build runs `tinacms build && next build`, env vars set, admin auth + save flow work |
| Self-host TinaCMS | [references/workflows/04-self-host-clerk-mongodb.md](references/workflows/04-self-host-clerk-mongodb.md) or [references/self-hosted/02-nextjs-vercel-starter.md](references/self-hosted/02-nextjs-vercel-starter.md) | [references/self-hosted/03-existing-site-add.md](references/self-hosted/03-existing-site-add.md), [references/self-hosted/04-manual-setup.md](references/self-hosted/04-manual-setup.md), [references/self-hosted/05-migrating-from-tinacloud.md](references/self-hosted/05-migrating-from-tinacloud.md), [references/self-hosted/06-querying-data.md](references/self-hosted/06-querying-data.md), [references/self-hosted/07-user-management.md](references/self-hosted/07-user-management.md), [references/self-hosted/08-limitations.md](references/self-hosted/08-limitations.md), [references/self-hosted/tina-backend/01-nextjs-app-route.md](references/self-hosted/tina-backend/01-nextjs-app-route.md), [references/self-hosted/tina-backend/02-vercel-functions.md](references/self-hosted/tina-backend/02-vercel-functions.md), [references/self-hosted/auth-provider/01-overview.md](references/self-hosted/auth-provider/01-overview.md), [references/self-hosted/auth-provider/02-authjs.md](references/self-hosted/auth-provider/02-authjs.md), [references/self-hosted/auth-provider/03-tinacloud-auth.md](references/self-hosted/auth-provider/03-tinacloud-auth.md), [references/self-hosted/auth-provider/04-clerk-auth.md](references/self-hosted/auth-provider/04-clerk-auth.md), [references/self-hosted/auth-provider/05-bring-your-own.md](references/self-hosted/auth-provider/05-bring-your-own.md), [references/self-hosted/database-adapter/01-overview.md](references/self-hosted/database-adapter/01-overview.md), [references/self-hosted/database-adapter/02-vercel-kv.md](references/self-hosted/database-adapter/02-vercel-kv.md), [references/self-hosted/database-adapter/03-mongodb.md](references/self-hosted/database-adapter/03-mongodb.md), [references/self-hosted/database-adapter/04-make-your-own.md](references/self-hosted/database-adapter/04-make-your-own.md), [references/self-hosted/git-provider/01-overview.md](references/self-hosted/git-provider/01-overview.md), [references/self-hosted/git-provider/02-github.md](references/self-hosted/git-provider/02-github.md), [references/self-hosted/git-provider/03-make-your-own.md](references/self-hosted/git-provider/03-make-your-own.md) | Node route handles `/api/tina/gql`, auth provider rejects unauthorized writes, DB and git provider persist edits |
| Team editorial workflow | [references/workflows/05-editorial-workflow-team.md](references/workflows/05-editorial-workflow-team.md) | [references/tinacloud/06-editorial-workflow.md](references/tinacloud/06-editorial-workflow.md), [references/tinacloud/07-webhooks.md](references/tinacloud/07-webhooks.md), [references/tinacloud/09-git-co-authoring.md](references/tinacloud/09-git-co-authoring.md) | Editors save to branches/PRs, preview URL resolves, GitHub write access verified |
| Static / no-runtime CMS | [references/workflows/06-static-build-no-runtime.md](references/workflows/06-static-build-no-runtime.md) | [references/cli/03-tinacms-build.md](references/cli/03-tinacms-build.md), [references/rendering/09-static-params.md](references/rendering/09-static-params.md), [references/rendering/02-pages-router-pattern.md](references/rendering/02-pages-router-pattern.md) for legacy fallback only, [references/deployment/03-deploy-hooks.md](references/deployment/03-deploy-hooks.md) | All CMS pages pre-render; updates publish via git + rebuild |
| Debug / triage failures | [references/troubleshooting/01-error-catalog.md](references/troubleshooting/01-error-catalog.md) | Use the symptom table below | Root cause named, fix applied, verification rung stated |

## Preview / Draft Checkpoint

For visual-editing or editorial-preview tasks, verify all of these *before* chasing framework bugs:

- `NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`, branch env, and any self-hosted auth/storage env vars exist in the right environment.
- `tina/config.*` declares `ui.router` or `ui.previewUrl` for collections that need live URLs.
- App Router has a Draft Mode route; Next 15+ uses async `draftMode()`.
- Page uses the two-component split: Server fetches, Client calls `useTina(props)`.
- All three of `query`, `variables`, and `data` flow to the Client Component.
- `data-tina-field` lands on DOM elements (or is forwarded by custom components).
- `proxy.ts` (Next 16) or `middleware.ts` does not redirect `/admin`, `/api/preview`, or `/api/tina/*`.

## Debug By Symptom

| Symptom | Go directly to | Also check |
|---|---|---|
| Generated client / `tina/__generated__` missing | [references/troubleshooting/02-build-and-types.md](references/troubleshooting/02-build-and-types.md) | [references/setup/04-package-scripts.md](references/setup/04-package-scripts.md) |
| Schema validation / build failure | [references/troubleshooting/03-schema-errors.md](references/troubleshooting/03-schema-errors.md) | [references/schema/03-naming-rules.md](references/schema/03-naming-rules.md) |
| Content missing, `_template`, bad frontmatter | [references/troubleshooting/04-content-errors.md](references/troubleshooting/04-content-errors.md) | [references/schema/02-collection-templates.md](references/schema/02-collection-templates.md) |
| MDX / rich-text rendering failure | [references/field-types/09-rich-text-mdx.md](references/field-types/09-rich-text-mdx.md) | [references/rendering/05-mdx-component-mapping.md](references/rendering/05-mdx-component-mapping.md) |
| Draft / preview mode not enabling | [references/visual-editing/05-draft-mode.md](references/visual-editing/05-draft-mode.md) | [references/troubleshooting/06-visual-editing-issues.md](references/troubleshooting/06-visual-editing-issues.md) |
| Visual-editing overlay missing | [references/visual-editing/07-debugging-checklist.md](references/visual-editing/07-debugging-checklist.md) | [references/troubleshooting/06-visual-editing-issues.md](references/troubleshooting/06-visual-editing-issues.md) |
| Content stale on Vercel after save / deploy | [references/rendering/11-vercel-cache-caveat.md](references/rendering/11-vercel-cache-caveat.md) | [references/data-fetching/04-fetch-options-revalidate.md](references/data-fetching/04-fetch-options-revalidate.md) |
| TinaCloud auth / project / token / index errors | [references/troubleshooting/08-tinacloud-issues.md](references/troubleshooting/08-tinacloud-issues.md) | [references/tinacloud/13-troubleshooting.md](references/tinacloud/13-troubleshooting.md) |
| Self-hosted auth / storage / API failures | [references/troubleshooting/05-runtime-errors.md](references/troubleshooting/05-runtime-errors.md) | [references/self-hosted/00-overview.md](references/self-hosted/00-overview.md) |
| Edge runtime incompatibility | [references/deployment/05-edge-runtime-not-supported.md](references/deployment/05-edge-runtime-not-supported.md) | [references/self-hosted/tina-backend/01-nextjs-app-route.md](references/self-hosted/tina-backend/01-nextjs-app-route.md) |
| Corporate firewall / admin network failure | [references/troubleshooting/07-network-and-firewall.md](references/troubleshooting/07-network-and-firewall.md) | [references/tinacloud/02-network-requirements.md](references/tinacloud/02-network-requirements.md) |

Debugging should take at most two hops from this file to the specific troubleshooting document.

## Defaults

- Greenfield: TinaCloud + Vercel + MDX, App Router, `pnpm`. Respect the project's existing package manager when its lockfile is consistent.
- Legacy: Pages Router content is fallback only. If the project is Pages-first, defer to official docs.
- Local dev: `tinacms dev -c "next dev"`. Production build: `tinacms build && next build`.
- Always pass `fetchOptions: { next: { revalidate: N } }` for Tina client queries on Vercel unless the route is intentionally static.
- Use `ui.router` for collections that need live preview.
- Use `defaultItem` for block templates and `ui.itemProps` for list fields editors will manipulate.

## Output Contract

For greenfield / build tasks, deliver:

- Code changes for setup, schema, rendering, and deploy lane.
- Commands run with results: install, `tinacms build`, typecheck/build, local dev when feasible.
- Validation showing generated client, admin route, and at least one rendered Tina-backed route.

For migration / add-to-existing tasks, deliver:

- Touched routes, components, content paths, package scripts, env/config names.
- Version, package-manager, App Router, and backend-lane assumptions.
- Regression checks for existing routes plus the new Tina route.

For deployment tasks, deliver:

- Lane decision and reason.
- Env vars / config names verified without exposing secret values.
- Provider-specific build/runtime checks (Node runtime for self-hosted).

For debugging tasks, deliver:

- Symptom, root cause, exact reference used, fix, verification rung.
- If only static checks passed, say runtime was not exercised.

## Verification Rungs

- **Skill edit** → run `python3 scripts/validate-skills.py`; report only target-skill errors.
- **Static** → package versions, lockfile, App Router files, `tina/config.*`, env names, `.gitignore`, `tina/tina-lock.json`.
- **Tina** → `tinacms audit` where relevant, then `tinacms build`; verify `tina/__generated__/client.*` exists.
- **App** → repo's typecheck/lint/build; verify `tinacms build` precedes `next build`.
- **Runtime** → `tinacms dev -c "next dev"`, open `/admin/index.html`, render at least one App Router route.
- **Visual editing** → enable Draft Mode, observe `useTina` updates, click `data-tina-field` targets, verify `proxy.ts`/middleware does not block admin or Tina APIs.
- **Deployment** → env vars at the provider, build logs, Node runtime for self-hosted, content save path, cache/revalidation behavior.

## Reference Routing (Exhaustive Catalog)

Use these globs as the catalog. Load only the lane the task needs. Topic catalog: [references/00-reference-map.md](references/00-reference-map.md).

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
