# Adding TinaCMS to an Existing Next.js Site

The brownfield path. Less risky than greenfield rebuild.

## When this fits

- You have a Next.js App Router site with content baked into code (or markdown files)
- You want non-technical editors to manage content
- You want to keep most of your existing UI and gradually wrap pieces

## Strategy options

| Strategy | Effort | When |
|---|---|---|
| **Back-office only** | Low | Editors visit `/admin`; you manually update pages | Small site, infrequent edits |
| **Wrap one page at a time** | Medium | Migrate one page from hardcoded → CMS-driven | Phased migration |
| **Full migration** | High | Rebuild data layer fresh on TinaCMS | Greenfield-style do-over |

For most projects, "wrap one page at a time" is the realistic path.

## Steps

### 1. Add TinaCMS

```bash
pnpm dlx @tinacms/cli@latest init
```

The CLI detects your existing Next.js setup and only adds the TinaCMS bits.

### 2. Set up TinaCloud

Create project at app.tina.io, add env vars:

```env
NEXT_PUBLIC_TINA_CLIENT_ID=<...>
TINA_TOKEN=<...>
NEXT_PUBLIC_TINA_BRANCH=main
```

### 3. Define a single collection (e.g. blog)

Don't try to convert everything at once. Pick one content type:

```typescript
{
  name: 'post',
  label: 'Blog',
  path: 'content/posts',
  format: 'mdx',
  fields: [
    { name: 'title', type: 'string', isTitle: true },
    { name: 'date', type: 'datetime' },
    { name: 'body', type: 'rich-text', isBody: true },
  ],
}
```

### 4. Create one CMS-driven page

Replace one hardcoded page with a TinaCMS-driven one. Follow the App Router pattern (`references/rendering/01-app-router-pattern.md`).

Test locally → deploy → editor can manage that one page.

### 5. Iteratively migrate other pages

Repeat for each page type. The other pages keep working untouched while you migrate.

### 6. Migrate existing content

For markdown content already in `content/`:

1. Define the schema to match the existing frontmatter
2. Run `pnpm dlx @tinacms/cli@latest audit` — surfaces field-name issues
3. Fix any (rename `hero-image:` to `hero_image:` etc.)
4. Editors can now manage the existing files via the admin

## Things to watch out for

### Existing routes

If you have `app/blog/[slug]/page.tsx` already serving from a different source (DB, CMS, hardcoded), the migration needs careful coordination. Either:

- Run both old + new in parallel during transition
- Switch over in a single deploy

### URL preservation

Don't change URLs during migration. Editors depend on stable links. If the existing URL is `/blog/my-post`, ensure the TinaCMS route renders at the same URL.

### Image handling

If existing images live in `public/` already, TinaCMS' repo-based media adapter works seamlessly:

```typescript
media: {
  tina: {
    mediaRoot: 'images',  // or wherever your existing images live
    publicFolder: 'public',
  },
}
```

For external media providers (Cloudinary), migrate gradually — new uploads go to Cloudinary, old images stay in `public/`.

### Existing auth

If your app already has auth (Clerk, NextAuth), use the same provider for the CMS:

- Clerk app → use `tinacms-clerk`
- NextAuth app → use `tinacms-authjs`

This way editors use the same identity for both.

## Migrating from Forestry / other CMSs

If existing content is from Forestry.io with hyphenated frontmatter:

```bash
find content -name '*.md' -exec sed -i '' 's/^hero-image:/hero_image:/' {} \;
find content -name '*.md' -exec sed -i '' 's/^cover-photo:/cover_photo:/' {} \;
```

Then update the schema to use underscored field names.

## Rolling back

If TinaCMS doesn't work out:

1. Keep the existing app code (untouched during migration)
2. Remove the TinaCMS additions: `tina/`, `app/admin/`, package scripts
3. Revert env vars
4. Redeploy

The migration is reversible if you preserved the old routes.

## Common mistakes

| Mistake | Fix |
|---|---|
| Migrated everything at once | Slow rollback if issues | Migrate one page type at a time |
| Changed URLs during migration | Broken links | Preserve URL structure |
| Schema doesn't match existing frontmatter | Documents fail to parse | Run `audit`, fix mismatches |
| Forgot to update `package.json` scripts | Build fails | Wrap commands with `tinacms build &&` |
| Mixed auth providers | Editors confused | Use one provider |
