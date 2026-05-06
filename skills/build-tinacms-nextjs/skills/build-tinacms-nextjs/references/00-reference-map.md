# Reference Map

The full structured index of every reference file in this skill. Use it when SKILL.md routes are not enough — find the deeper file directly.

## Concepts

| File | Topic |
|---|---|
| [concepts/01-what-is-tinacms.md](concepts/01-what-is-tinacms.md) | Mental model: git-backed CMS + GraphQL |
| [concepts/02-tina-folder-anatomy.md](concepts/02-tina-folder-anatomy.md) | `/tina` folder + every generated file |
| [concepts/03-tinacloud-vs-self-hosted.md](concepts/03-tinacloud-vs-self-hosted.md) | Decision matrix |
| [concepts/04-data-layer-architecture.md](concepts/04-data-layer-architecture.md) | Auth + DB + Git provider design |

## Setup

| File | Topic |
|---|---|
| [setup/01-prerequisites.md](setup/01-prerequisites.md) | Node, pnpm, TinaCloud account |
| [setup/02-new-project-scaffold.md](setup/02-new-project-scaffold.md) | `create-next-app` + `tinacms init` |
| [setup/03-existing-project-add.md](setup/03-existing-project-add.md) | Brownfield add |
| [setup/04-package-scripts.md](setup/04-package-scripts.md) | `dev` / `build` / `start`, build order |
| [setup/05-env-vars.md](setup/05-env-vars.md) | `.env` vs `.env.local`, build-time embedding |
| [setup/06-gitignore-and-lockfile.md](setup/06-gitignore-and-lockfile.md) | What to commit, what to ignore |
| [setup/07-claude-code-automations.md](setup/07-claude-code-automations.md) | Hooks + MCP servers |

## Config

| File | Topic |
|---|---|
| [config/01-config-anatomy.md](config/01-config-anatomy.md) | `defineConfig` top-level options |
| [config/02-build-and-server.md](config/02-build-and-server.md) | `build` + `server` sections |
| [config/03-admin-and-ui.md](config/03-admin-and-ui.md) | Admin route, `previewUrl`, `cmsCallback` |
| [config/04-branch-resolution.md](config/04-branch-resolution.md) | Branch waterfall |
| [config/05-client-and-content-api.md](config/05-client-and-content-api.md) | `contentApiUrlOverride` for self-hosted |
| [config/06-typescript-path-aliases.md](config/06-typescript-path-aliases.md) | `@/` aliases in config |

## Schema

| File | Topic |
|---|---|
| [schema/00-schema-overview.md](schema/00-schema-overview.md) | Collections + Fields + Templates |
| [schema/01-collections.md](schema/01-collections.md) | Folder vs singleton, all properties |
| [schema/02-collection-templates.md](schema/02-collection-templates.md) | Multi-shape collections |
| [schema/03-naming-rules.md](schema/03-naming-rules.md) | Naming constraints, reserved names |
| [schema/04-blocks-pattern.md](schema/04-blocks-pattern.md) | Page builder pattern |
| [schema/05-reusable-field-groups.md](schema/05-reusable-field-groups.md) | DRY field groups |
| [schema/06-content-hooks.md](schema/06-content-hooks.md) | `beforeSubmit` |
| [schema/07-list-ui-customization.md](schema/07-list-ui-customization.md) | `ui.itemProps` |
| [schema/08-default-collection-set.md](schema/08-default-collection-set.md) | Starter pages/posts/global/navigation |

## Field Types

| File | Topic |
|---|---|
| [field-types/00-overview.md](field-types/00-overview.md) | Type matrix |
| [field-types/01-string.md](field-types/01-string.md) | string + variants |
| [field-types/02-number.md](field-types/02-number.md) | number |
| [field-types/03-boolean.md](field-types/03-boolean.md) | boolean |
| [field-types/04-datetime.md](field-types/04-datetime.md) | datetime |
| [field-types/05-image.md](field-types/05-image.md) | image |
| [field-types/06-reference.md](field-types/06-reference.md) | reference + 503 mitigation |
| [field-types/07-object.md](field-types/07-object.md) | object + list |
| [field-types/08-rich-text-markdown.md](field-types/08-rich-text-markdown.md) | rich-text body |
| [field-types/09-rich-text-mdx.md](field-types/09-rich-text-mdx.md) | rich-text + MDX templates |
| [field-types/10-markdown-shortcodes.md](field-types/10-markdown-shortcodes.md) | `match: { start, end }` shortcodes |
| [field-types/11-reserved-names.md](field-types/11-reserved-names.md) | `children`, `mark`, `_template` etc. |

## Toolkit Fields

| File | Topic |
|---|---|
| [toolkit-fields/00-toolkit-overview.md](toolkit-fields/00-toolkit-overview.md) | Plugin system overview |
| [toolkit-fields/01-text-textarea-number.md](toolkit-fields/01-text-textarea-number.md) | Text widgets |
| [toolkit-fields/02-image-color.md](toolkit-fields/02-image-color.md) | Image and color pickers |
| [toolkit-fields/03-toggle-radio-select.md](toolkit-fields/03-toggle-radio-select.md) | Boolean / choice widgets |
| [toolkit-fields/04-tags-list.md](toolkit-fields/04-tags-list.md) | List variants |
| [toolkit-fields/05-group-and-group-list.md](toolkit-fields/05-group-and-group-list.md) | Grouped fields |
| [toolkit-fields/06-date-markdown-html.md](toolkit-fields/06-date-markdown-html.md) | Date / markdown / HTML |
| [toolkit-fields/07-custom-field-component.md](toolkit-fields/07-custom-field-component.md) | Custom React components |

## Rendering

| File | Topic |
|---|---|
| [rendering/01-app-router-pattern.md](rendering/01-app-router-pattern.md) | Server/Client split (default) |
| [rendering/02-pages-router-pattern.md](rendering/02-pages-router-pattern.md) | Pages Router (legacy) |
| [rendering/03-usetina-hook.md](rendering/03-usetina-hook.md) | The hook in detail |
| [rendering/04-tinamarkdown.md](rendering/04-tinamarkdown.md) | TinaMarkdown component |
| [rendering/05-mdx-component-mapping.md](rendering/05-mdx-component-mapping.md) | Template → React component |
| [rendering/06-overriding-builtins.md](rendering/06-overriding-builtins.md) | h1, code_block, image, etc. |
| [rendering/07-mermaid-diagrams.md](rendering/07-mermaid-diagrams.md) | Mermaid via code_block |
| [rendering/08-block-renderer.md](rendering/08-block-renderer.md) | __typename mapping |
| [rendering/09-static-params.md](rendering/09-static-params.md) | generateStaticParams |
| [rendering/10-caching-use-cache.md](rendering/10-caching-use-cache.md) | `"use cache"` + cacheLife |
| [rendering/11-vercel-cache-caveat.md](rendering/11-vercel-cache-caveat.md) | The revalidate fix |

## Visual Editing

| File | Topic |
|---|---|
| [visual-editing/01-overview.md](visual-editing/01-overview.md) | End-to-end flow |
| [visual-editing/02-router-config.md](visual-editing/02-router-config.md) | `ui.router` |
| [visual-editing/03-tinafield-helper.md](visual-editing/03-tinafield-helper.md) | `tinaField` on DOM |
| [visual-editing/04-tinamarkdown-tinafield.md](visual-editing/04-tinamarkdown-tinafield.md) | tinaField inside MDX |
| [visual-editing/05-draft-mode.md](visual-editing/05-draft-mode.md) | `/api/preview` |
| [visual-editing/06-edit-state-hook.md](visual-editing/06-edit-state-hook.md) | `useEditState` |
| [visual-editing/07-debugging-checklist.md](visual-editing/07-debugging-checklist.md) | 9-step debug |
| [visual-editing/08-proxy-ts.md](visual-editing/08-proxy-ts.md) | Next.js 16 proxy |

## Data Fetching

| File | Topic |
|---|---|
| [data-fetching/01-overview.md](data-fetching/01-overview.md) | client vs databaseClient |
| [data-fetching/02-generated-client.md](data-fetching/02-generated-client.md) | API surface |
| [data-fetching/03-custom-queries.md](data-fetching/03-custom-queries.md) | tina/queries/ |
| [data-fetching/04-fetch-options-revalidate.md](data-fetching/04-fetch-options-revalidate.md) | Cache control |
| [data-fetching/05-graphql-cli.md](data-fetching/05-graphql-cli.md) | CLI commands |

## GraphQL

| File | Topic |
|---|---|
| [graphql/01-overview.md](graphql/01-overview.md) | Generated schema |
| [graphql/02-get-document.md](graphql/02-get-document.md) | Single doc fetch |
| [graphql/03-query-documents.md](graphql/03-query-documents.md) | Connection queries |
| [graphql/04-filter-documents.md](graphql/04-filter-documents.md) | Filter operators |
| [graphql/05-sorting.md](graphql/05-sorting.md) | Sort by indexed fields |
| [graphql/06-pagination.md](graphql/06-pagination.md) | Cursor pagination |
| [graphql/07-performance.md](graphql/07-performance.md) | Query cost |
| [graphql/08-limitations.md](graphql/08-limitations.md) | What's not supported |
| [graphql/09-add-document.md](graphql/09-add-document.md) | createDocument |
| [graphql/10-update-document.md](graphql/10-update-document.md) | updateDocument |

## SEO

| File | Topic |
|---|---|
| [seo/01-generate-metadata.md](seo/01-generate-metadata.md) | generateMetadata |
| [seo/02-description-waterfall.md](seo/02-description-waterfall.md) | Description fallback |
| [seo/03-og-image-waterfall.md](seo/03-og-image-waterfall.md) | OG image fallback |
| [seo/04-json-ld-structured-data.md](seo/04-json-ld-structured-data.md) | Schema.org markup |
| [seo/05-dynamic-og-images.md](seo/05-dynamic-og-images.md) | next/og |
| [seo/06-sitemap-and-robots.md](seo/06-sitemap-and-robots.md) | MetadataRoute |
| [seo/07-rss-feed.md](seo/07-rss-feed.md) | app/feed.xml/route.ts |

## Media

| File | Topic |
|---|---|
| [media/01-repo-based-default.md](media/01-repo-based-default.md) | Default repo-based |
| [media/02-accepted-types.md](media/02-accepted-types.md) | MIME whitelist |
| [media/03-cloudinary.md](media/03-cloudinary.md) | next-tinacms-cloudinary |
| [media/04-s3.md](media/04-s3.md) | AWS S3 |
| [media/05-do-spaces.md](media/05-do-spaces.md) | DigitalOcean Spaces |
| [media/06-vercel-blob.md](media/06-vercel-blob.md) | Vercel Blob |
| [media/07-external-auth.md](media/07-external-auth.md) | @tinacms/auth |

## TinaCloud

| File | Topic |
|---|---|
| [tinacloud/01-overview.md](tinacloud/01-overview.md) | Default backend |
| [tinacloud/02-network-requirements.md](tinacloud/02-network-requirements.md) | Domain allowlist |
| [tinacloud/03-dashboard-registration.md](tinacloud/03-dashboard-registration.md) | Account setup |
| [tinacloud/04-projects.md](tinacloud/04-projects.md) | Project config tab |
| [tinacloud/05-users-and-orgs.md](tinacloud/05-users-and-orgs.md) | User management |
| [tinacloud/06-editorial-workflow.md](tinacloud/06-editorial-workflow.md) | Branch-based PR review |
| [tinacloud/07-webhooks.md](tinacloud/07-webhooks.md) | content.* events |
| [tinacloud/08-search.md](tinacloud/08-search.md) | Built-in fuzzy search |
| [tinacloud/09-git-co-authoring.md](tinacloud/09-git-co-authoring.md) | Editor identity |
| [tinacloud/10-api-versioning.md](tinacloud/10-api-versioning.md) | API version pinning |
| [tinacloud/11-github-enterprise.md](tinacloud/11-github-enterprise.md) | GHE integration |
| [tinacloud/12-vercel-deployment.md](tinacloud/12-vercel-deployment.md) | Vercel-specific deploy |
| [tinacloud/13-troubleshooting.md](tinacloud/13-troubleshooting.md) | TinaCloud-specific issues |

## Self-hosted

| File | Topic |
|---|---|
| [self-hosted/00-overview.md](self-hosted/00-overview.md) | When to self-host |
| [self-hosted/01-architecture.md](self-hosted/01-architecture.md) | Three-module design |
| [self-hosted/02-nextjs-vercel-starter.md](self-hosted/02-nextjs-vercel-starter.md) | Official starter |
| [self-hosted/03-existing-site-add.md](self-hosted/03-existing-site-add.md) | Brownfield add |
| [self-hosted/04-manual-setup.md](self-hosted/04-manual-setup.md) | From scratch |
| [self-hosted/05-migrating-from-tinacloud.md](self-hosted/05-migrating-from-tinacloud.md) | Migration guide |
| [self-hosted/06-querying-data.md](self-hosted/06-querying-data.md) | client vs databaseClient |
| [self-hosted/07-user-management.md](self-hosted/07-user-management.md) | User collection |
| [self-hosted/08-limitations.md](self-hosted/08-limitations.md) | What you give up |

### Self-hosted: tina-backend

| File | Topic |
|---|---|
| [self-hosted/tina-backend/01-nextjs-app-route.md](self-hosted/tina-backend/01-nextjs-app-route.md) | App Router backend route |
| [self-hosted/tina-backend/02-vercel-functions.md](self-hosted/tina-backend/02-vercel-functions.md) | Vercel Functions deploy |

### Self-hosted: git-provider

| File | Topic |
|---|---|
| [self-hosted/git-provider/01-overview.md](self-hosted/git-provider/01-overview.md) | Provider interface |
| [self-hosted/git-provider/02-github.md](self-hosted/git-provider/02-github.md) | GitHub provider (default) |
| [self-hosted/git-provider/03-make-your-own.md](self-hosted/git-provider/03-make-your-own.md) | Custom impl |

### Self-hosted: database-adapter

| File | Topic |
|---|---|
| [self-hosted/database-adapter/01-overview.md](self-hosted/database-adapter/01-overview.md) | createDatabase factory |
| [self-hosted/database-adapter/02-vercel-kv.md](self-hosted/database-adapter/02-vercel-kv.md) | Vercel KV |
| [self-hosted/database-adapter/03-mongodb.md](self-hosted/database-adapter/03-mongodb.md) | MongoDB Atlas |
| [self-hosted/database-adapter/04-make-your-own.md](self-hosted/database-adapter/04-make-your-own.md) | Custom adapter |

### Self-hosted: auth-provider

| File | Topic |
|---|---|
| [self-hosted/auth-provider/01-overview.md](self-hosted/auth-provider/01-overview.md) | Auth provider interface |
| [self-hosted/auth-provider/02-authjs.md](self-hosted/auth-provider/02-authjs.md) | Auth.js (default) |
| [self-hosted/auth-provider/03-tinacloud-auth.md](self-hosted/auth-provider/03-tinacloud-auth.md) | TinaCloud as auth-only |
| [self-hosted/auth-provider/04-clerk-auth.md](self-hosted/auth-provider/04-clerk-auth.md) | Clerk |
| [self-hosted/auth-provider/05-bring-your-own.md](self-hosted/auth-provider/05-bring-your-own.md) | Custom auth |

## CLI

| File | Topic |
|---|---|
| [cli/01-overview.md](cli/01-overview.md) | Command summary |
| [cli/02-tinacms-dev.md](cli/02-tinacms-dev.md) | dev options |
| [cli/03-tinacms-build.md](cli/03-tinacms-build.md) | build flags |
| [cli/04-graphql-commands.md](cli/04-graphql-commands.md) | audit, schema |
| [cli/05-init-and-init-backend.md](cli/05-init-and-init-backend.md) | Init flows |

## Deployment

| File | Topic |
|---|---|
| [deployment/01-vercel-tinacloud.md](deployment/01-vercel-tinacloud.md) | Default stack |
| [deployment/02-vercel-self-hosted.md](deployment/02-vercel-self-hosted.md) | Self-hosted on Vercel |
| [deployment/03-deploy-hooks.md](deployment/03-deploy-hooks.md) | Hooks + webhooks |
| [deployment/04-team-env-vars.md](deployment/04-team-env-vars.md) | Vercel team env |
| [deployment/05-edge-runtime-not-supported.md](deployment/05-edge-runtime-not-supported.md) | Why no edge |

## Workflows

| File | Topic |
|---|---|
| [workflows/01-greenfield-blog.md](workflows/01-greenfield-blog.md) | New blog from zero |
| [workflows/02-greenfield-marketing-site.md](workflows/02-greenfield-marketing-site.md) | Marketing site with blocks |
| [workflows/03-add-cms-to-existing-site.md](workflows/03-add-cms-to-existing-site.md) | Brownfield add |
| [workflows/04-self-host-clerk-mongodb.md](workflows/04-self-host-clerk-mongodb.md) | Self-host Clerk + Mongo |
| [workflows/05-editorial-workflow-team.md](workflows/05-editorial-workflow-team.md) | Multi-editor team |
| [workflows/06-static-build-no-runtime.md](workflows/06-static-build-no-runtime.md) | Static-only build |

## Troubleshooting

| File | Topic |
|---|---|
| [troubleshooting/01-error-catalog.md](troubleshooting/01-error-catalog.md) | Top-level index |
| [troubleshooting/02-build-and-types.md](troubleshooting/02-build-and-types.md) | Build / type errors |
| [troubleshooting/03-schema-errors.md](troubleshooting/03-schema-errors.md) | Schema errors |
| [troubleshooting/04-content-errors.md](troubleshooting/04-content-errors.md) | Content / frontmatter errors |
| [troubleshooting/05-runtime-errors.md](troubleshooting/05-runtime-errors.md) | Runtime issues |
| [troubleshooting/06-visual-editing-issues.md](troubleshooting/06-visual-editing-issues.md) | Click-to-edit debug |
| [troubleshooting/07-network-and-firewall.md](troubleshooting/07-network-and-firewall.md) | Corp firewall |
| [troubleshooting/08-tinacloud-issues.md](troubleshooting/08-tinacloud-issues.md) | TinaCloud-specific |
