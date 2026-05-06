# What is TinaCMS

TinaCMS is a **git-backed, schema-driven, headless CMS** with a visual editor. The mental model has four parts:

1. **Content lives as files in a git repo.** Markdown, MDX, JSON, YAML, or TOML — your choice per collection. There is no separate "content database" as the source of truth.
2. **A schema describes those files.** `tina/config.ts` defines collections (content types) and fields (the editing UI). The schema is also the contract for the GraphQL API.
3. **A GraphQL data layer reads them.** Queries return typed documents. The client is auto-generated from the schema. In production this hits TinaCloud (or a self-hosted Node.js backend) which indexes the git repo into a database for fast lookups.
4. **A visual editor lets non-technical users edit those files.** The admin SPA reads/writes through the GraphQL API. Edits commit back to git via the configured backend.

## Why git-backed matters

- **Version control.** Every edit is a git commit. Diff, blame, revert work normally.
- **Pull-request-driven content.** Editorial Workflow (TinaCloud Team Plus+) creates a branch per editor, opens a draft PR, and publishes on merge.
- **No vendor lock-in.** Your content is plain text in a repo. Stop using TinaCMS and the files keep working with any static-site generator or SSR framework.
- **Local-first dev.** `tinacms dev -c "next dev"` runs a local GraphQL server that reads/writes files directly. No cloud dependency for development.

## Why schema-driven matters

- **Typed GraphQL out of the box.** No hand-written queries; the client knows your shape.
- **Editor UI is generated from the schema.** Each field type maps to a widget (string→text, rich-text→markdown editor, image→media picker).
- **One source of truth.** `tina/config.ts` is consumed by the editor UI, the GraphQL types, and the runtime client.

## What you write vs what TinaCMS generates

| You write | TinaCMS generates |
|---|---|
| `tina/config.ts` (schema + config) | `tina/__generated__/client.{ts,js}` (GraphQL client) |
| `content/**/*.{md,mdx,json}` (your data) | `tina/__generated__/types.{ts,js}` (TS types) |
| `tina-lock.json` (commit this — pinned schema) | `tina/__generated__/{schema,graphql,lookup}.json` |
| Block components, page renderers, UI | `tina/__generated__/{frags,queries,schema}.gql` |

## What TinaCMS is not

- **Not a database.** It's a thin layer over a git repo. The "data layer" caches content in a DB (KV/Mongo) for fast reads, but the source of truth is the file in git.
- **Not real-time collaborative.** Editors save full documents, and conflicts resolve as merge conflicts. For Google-Docs-style co-editing use a different tool.
- **Not for highly dynamic data.** Inventory, user-generated content, real-time dashboards belong in a database, not a git-backed CMS.

## When TinaCMS fits

- Marketing sites and landing pages
- Documentation sites
- Blogs and content-heavy sites
- Editorial workflows where content reviewers want PR-style approval
- Sites where developers and editors want a shared, typed schema

## When TinaCMS does NOT fit

- High-frequency writes (e-commerce inventory, comments, reactions)
- Real-time collaborative editing
- Apps where most data is structured and relational, not document-shaped
- Edge-runtime-only deployments (TinaCMS backend is Node.js)

Read `references/concepts/03-tinacloud-vs-self-hosted.md` for hosting decisions and `references/concepts/04-data-layer-architecture.md` for the under-the-hood architecture.
