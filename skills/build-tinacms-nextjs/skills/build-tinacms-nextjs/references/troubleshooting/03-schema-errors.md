# Schema Errors

Errors during schema bundling or content validation.

## `Schema Not Successfully Built`

**Cause:** `tina/config.ts` imports something that breaks esbuild bundling. Common offenders:

- React components (anything using JSX runtime, hooks)
- CSS / SCSS / image imports
- Code using `window`, `document`, `localStorage`
- Component libraries with browser-only deps

**Diagnosis:**

```bash
pnpm tinacms build --verbose
# Read the esbuild error — it'll point at the problematic import
```

**Fix:** Remove the import or replace with a Node-safe alternative:

```typescript
// ❌ Bad
import { Hero } from '../components/Hero'  // pulls JSX

// ✅ Good — type-only
import type { HeroProps } from '../components/Hero'

// ✅ Good — schema fragment
import { heroBlock } from '../tina/blocks/hero'
```

## `Field name contains invalid characters`

**Cause:** Field name has hyphens, spaces, dots, or special chars.

**Fix:**

```typescript
// ❌
{ name: 'hero-image', ... }
{ name: 'hero image', ... }

// ✅
{ name: 'heroImage', ... }
{ name: 'hero_image', ... }
```

If migrating from a CMS that allowed hyphens, run a sed migration:

```bash
find content -name '*.md' -exec sed -i '' 's/^hero-image:/hero_image:/' {} \;
```

## `Reserved field name`

**Cause:** Used `children`, `mark`, `_template`, `_sys`, or `id` where reserved.

**Fix:** Pick a different name. See `references/field-types/11-reserved-names.md`.

## `Schema validation failed: <field>`

**Cause:** Schema definition has a TypeScript-level error (wrong type discriminator).

**Fix:** Use `as const` for inline arrays:

```typescript
{ name: 'foo', type: 'string' as const, options: ['a', 'b'] }
```

Or type the whole array:

```typescript
import type { TinaField } from 'tinacms'
const fields: TinaField[] = [...]
```

## Collections with mismatched paths

**Cause:** `path: 'posts'` but files at `content/posts/`. Collection finds nothing.

**Fix:**

```bash
pnpm dlx @tinacms/cli@latest audit
```

The audit reports path mismatches.

## `Duplicate field name`

**Cause:** Two fields with the same `name` in the same collection.

**Fix:** Rename one. Field names must be unique within the collection (or within the same `object` field group).

## `Could not infer type for field`

**Cause:** Field is missing a `type` discriminator.

**Fix:**

```typescript
// ❌
{ name: 'foo' }  // no type

// ✅
{ name: 'foo', type: 'string' }
```

## Schema bundle bigger than expected

**Cause:** Imports pulling in more code than necessary.

**Fix:**

- Use `import type` for type-only imports
- Avoid `import * as X` (pulls everything)
- Extract block schemas to leaf files

```typescript
// ❌ Bigger bundle
import * as Components from '../components'

// ✅ Smaller
import { Hero } from '../components/Hero'

// ✅ Smallest (type-only)
import type { HeroProps } from '../components/Hero'
```

## Schema works locally but fails in CI

**Cause:** Different Node.js versions or different `tinacms` versions.

**Fix:**

```yaml
# GitHub Actions
- uses: actions/setup-node@v4
  with:
    node-version: '20.9'  # match local

- run: pnpm install --frozen-lockfile  # use lockfile
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Imported a React component into `tina/config.ts` | Use type-only or schema fragment |
| Field with hyphens | Replace with underscores or camelCase |
| Forgot `as const` | Add it for inline literals |
| Path mismatch between schema and disk | Run `audit`, fix |
| Reserved names (children, mark, _template) | Pick another name |
