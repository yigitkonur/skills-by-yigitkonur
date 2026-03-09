# Content Collections

> Documents the MDX/content side of the marketing app. Consult this when adding blog posts, legal pages, or locale-specific public content.

## Where content lives

- `apps/web/content/posts/**/*.mdx`
- `apps/web/content/legal/**`
- Next.js content integration is enabled through the Content Collections plugin in `apps/web/next.config.ts`

## Practical notes

- marketing routes can render MDX-backed content such as blog and legal pages
- locale-aware content is supported by file naming/layout conventions
- this content system is distinct from the SaaS app’s authenticated UI modules

---

**Related references:**
- `references/setup/next-config.md` — Content Collections plugin wiring
- `references/marketing/pages.md` — Layout that wraps public content
- `references/routing/routing-marketing.md` — Marketing route structure
