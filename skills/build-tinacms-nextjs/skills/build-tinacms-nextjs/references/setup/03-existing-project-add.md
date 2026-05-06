# Adding TinaCMS to an Existing Next.js Project

For projects that already use Next.js App Router and want to add a CMS layer.

## Prerequisites for the existing project

- Next.js `>= 15` (Next.js 16 strongly recommended)
- App Router (Pages Router works but is a legacy path — see `references/rendering/02-pages-router-pattern.md`)
- TypeScript (works with JS but TS gives you generated types)
- React `>= 18.3.1` and `< 20`

## Add TinaCMS

```bash
pnpm dlx @tinacms/cli@latest init
```

The CLI detects the existing Next.js install and only adds the TinaCMS bits:

- Installs `tinacms` and `@tinacms/cli` if not present
- Creates `tina/config.ts` with a minimal schema
- Adds `app/admin/[[...index]]/page.tsx`
- Updates `package.json` scripts

## What you may need to merge manually

If the init prompts conflict with your existing setup:

| Conflict | Fix |
|---|---|
| `app/admin/` already exists | Move your existing route or pick a different admin path via `build.outputFolder` in `tina/config.ts` |
| `package.json` scripts have a custom `dev`/`build` | Wrap your existing commands: `tinacms dev -c "<your-dev-command>"`, `tinacms build && <your-build-command>` |
| `next.config.{ts,js}` uses CommonJS | TinaCMS 3.x is ESM-only. Rename to `next.config.ts` or set `"type": "module"` in `package.json` |

## Migrate existing markdown to TinaCMS

If you already have `content/` markdown files:

1. Define a collection in `tina/config.ts` whose `path` matches your existing folder.
2. Set the `format` to match your file extension (`md`, `mdx`, or `markdown`).
3. Define `fields` matching the YAML/TOML frontmatter your files use.
4. Run `pnpm dlx @tinacms/cli@latest audit` to see field-name conflicts (hyphens, etc).
5. Fix conflicts (rename `hero-image:` to `hero_image:` in frontmatter — see `references/troubleshooting/04-content-errors.md`).

```typescript
// Example: existing files at content/blog/*.md with frontmatter { title, date, body }
{
  name: 'post',
  label: 'Blog Posts',
  path: 'content/blog',
  format: 'md',
  fields: [
    { name: 'title', type: 'string', isTitle: true, required: true },
    { name: 'date', type: 'datetime', required: true },
    { name: 'body', type: 'rich-text', isBody: true },
  ],
}
```

## Add the admin route only

If you don't want every page editable yet, you can add TinaCMS as a "back office" without touching your existing pages:

- Keep `tina/config.ts` minimal (no `ui.router`)
- Editors visit `/admin` to manage content
- Your existing pages stay unchanged
- Add visual editing per page later when you want it (`references/rendering/01-app-router-pattern.md`)

## Things to verify after init

```bash
# 1. Build types
pnpm tinacms build

# 2. Check generated client exists
ls tina/__generated__/

# 3. Try a query in your code
# In a server component:
import { client } from '@/tina/__generated__/client'
const result = await client.queries.<yourCollection>({ relativePath: '<file>.md' })
console.log(result.data)
```

If the import fails, the build didn't complete. Read the `tinacms build` output for the actual error — usually a schema mismatch with existing files.

## Rollback if it doesn't work

TinaCMS init is reversible — remove `tina/`, the admin route, the script changes, and the new dependencies:

```bash
rm -rf tina/ app/admin/
git checkout package.json  # revert script changes
pnpm install  # rewrite lockfile
```
