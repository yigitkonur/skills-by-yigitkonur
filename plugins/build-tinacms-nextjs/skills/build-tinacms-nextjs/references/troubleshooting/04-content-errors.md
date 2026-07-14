# Content Errors

Errors related to content files, frontmatter, paths, and editor uploads.

## Documents not appearing in admin

**Cause:** Collection `path` doesn't match where files live.

**Fix:**

```bash
pnpm dlx @tinacms/cli@latest audit
```

Common path mistakes:

```typescript
// Files at content/posts/launch.md

// ✅ Correct
{ path: 'content/posts' }

// ❌ Missing parent
{ path: 'posts' }

// ❌ Trailing slash
{ path: 'content/posts/' }

// ❌ Absolute
{ path: '/Users/.../content/posts' }
```

## `template name was not provided`

**Cause:** Collection uses `templates: [...]` (multiple shapes), but a document is missing `_template:` in frontmatter.

**Fix:**

Add `_template` to existing docs:

```yaml
---
_template: landing
title: My Page
---
```

Or batch:

```bash
find content/pages -name '*.md' -exec sed -i '' '1a\
_template: landing\
' {} \;
```

Or restructure to use `fields` instead of `templates` if you only have one shape — see `references/schema/02-collection-templates.md`.

## Field name conflict (hyphenated frontmatter)

**Cause:** Existing docs have hyphenated keys (`hero-image: foo.jpg`); schema uses underscores.

**Fix:**

```bash
find content -name '*.md' -exec sed -i '' 's/^hero-image:/hero_image:/' {} \;
find content -name '*.md' -exec sed -i '' 's/^cover-photo:/cover_photo:/' {} \;
```

Check all hyphenated fields in your existing content and migrate.

## Ghost upload (toast shows error, but file uploaded)

**Cause:** Known TinaCloud media UX bug — error toast despite successful upload.

**Fix:**

- Refresh the media browser before retrying
- Don't re-upload — duplicates the file
- Check the file actually appears in the media library

This is upstream; no permanent fix yet.

## Reference field 503 / dropdown times out

**Cause:** Referenced collection has > 500 documents.

**Fix:**

Three options:

1. Split the collection:
   ```typescript
   { name: 'active_author', path: 'content/authors/active' }
   { name: 'archived_author', path: 'content/authors/archived' }
   ```

2. Replace with `string + options`:
   ```typescript
   { type: 'string', options: ['author1', 'author2', ...] }
   ```

3. Custom field component with pagination (advanced).

See `references/field-types/06-reference.md`.

## Image saved but not loading

**Cause:** Image path mismatch or media store config wrong.

**Diagnostic:**

- File path in document: `/uploads/hero.jpg`
- File should exist at: `public/uploads/hero.jpg` (for repo-based)
- For external: URL like `https://res.cloudinary.com/...`

**Fix:**

If repo-based but file missing → editor's upload didn't actually save. Re-upload.

If `next/image` fails: check `images.remotePatterns` in `next.config.ts` for external URLs.

## Save fails with "Branch not found"

**Cause:** `branch` in `tina/config.ts` doesn't match an actual branch in the repo.

**Fix:**

- Check what branch you're saving from (`process.env.NEXT_PUBLIC_TINA_BRANCH` or fallback)
- Verify the branch exists in GitHub
- For Editorial Workflow, save to a new branch first (TinaCloud creates it)

## Save fails with "GitHub API error"

**Cause:** GitHub PAT expired, scope wrong, or rate-limited.

**Fix:**

- Regenerate PAT with full `repo` scope
- Update Vercel env var
- Redeploy

## Date in frontmatter is not parsing

**Cause:** Date format isn't ISO 8601.

**Fix:**

Schema is `datetime`. Frontmatter should be:

```yaml
date: '2026-05-08T00:00:00.000Z'    # ISO 8601 with timezone
```

Not:

```yaml
date: 'May 8, 2026'                  # ❌ free-form
date: '2026-05-08'                   # OK if dateFormat is YYYY-MM-DD
```

## Empty frontmatter rich-text body

**Cause:** Rich-text `isBody: true` field is in frontmatter instead of the body.

**Fix:**

For markdown/MDX with body content, the body should NOT be in frontmatter:

```mdx
---
title: My Post
date: '2026-05-08T...'
---

# This is the body content (not in frontmatter)
```

If you see body content inside the `---` block, the schema is misconfigured (probably missing `isBody: true`).

## Common mistakes

| Mistake | Fix |
|---|---|
| Path mismatch | Run `audit`, fix path |
| Missed `_template` for multi-shape | Add to frontmatter |
| Hyphenated field names | Sed-migrate to underscores |
| Image upload "succeeded" but not visible | Refresh; ghost-upload bug |
| Date in wrong format | Use ISO 8601 |
| Reference dropdown 503 | Split collection or use string + options |
