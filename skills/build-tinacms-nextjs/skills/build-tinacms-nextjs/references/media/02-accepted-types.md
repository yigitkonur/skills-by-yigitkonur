# Overriding Accepted Media Types

Restrict the file types editors can upload.

## Default accepted types

The default accept list covers common web image formats: JPG, PNG, WEBP, GIF, SVG. Plus PDFs, fonts, and video in some configurations.

To restrict (or expand):

```typescript
media: {
  tina: {
    mediaRoot: 'uploads',
    publicFolder: 'public',
    accept: 'image/jpeg,image/png,image/webp',  // images only
  },
}
```

## `accept` syntax

Same as HTML `<input type="file" accept="...">`:

```typescript
// Specific MIMEs
accept: 'image/jpeg,image/png'

// MIME wildcards
accept: 'image/*'        // any image
accept: 'image/*,application/pdf'  // images + PDFs

// File extensions
accept: '.jpg,.png,.webp'  // by extension
```

For most projects, MIME wildcards are clearest:

```typescript
accept: 'image/jpeg,image/png,image/webp'
```

## Per-field accept (override globally)

Currently TinaCMS doesn't support per-field accept config — `accept` is global to the media store.

Workaround: add validation on the field:

```typescript
{
  name: 'avatar',
  type: 'image',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      if (!/\.(jpg|jpeg|png|webp)$/i.test(value)) return 'Avatars must be JPG/PNG/WEBP'
      return undefined
    },
  },
}
```

## Use cases

| Project type | Recommended accept |
|---|---|
| Marketing site (images only) | `image/jpeg,image/png,image/webp` |
| Blog (images + occasional PDFs) | `image/*,application/pdf` |
| Documentation (images + diagrams) | `image/*,image/svg+xml` |
| Media library (everything) | `*/*` (or omit `accept`) |

## SVG warning

SVGs can contain `<script>` tags — XSS risk if served untrusted. If editors are trusted, allow SVG. If not, block:

```typescript
accept: 'image/jpeg,image/png,image/webp'  // exclude svg
```

For SVGs needing strict sanitization, use a library like `dompurify` server-side before serving.

## File size limits

`accept` is type-only. For size limits:

- Repo-based: limited by git practical limits (>~100MB causes problems)
- Cloudinary: 100MB free, more on paid
- S3: virtually no limit

Add validation manually if you want to enforce:

```typescript
ui: {
  validate: (value) => {
    // Validate via custom upload hook — not first-class TinaCMS feature
  },
}
```

## External providers

For external media providers, the `accept` config still applies — TinaCMS validates file types client-side before upload.

```typescript
media: {
  loadCustomStore: async () => {
    const pack = await import('next-tinacms-cloudinary')
    return pack.TinaCloudCloudinaryMediaStore
  },
  // accept still works at the global level
}
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `accept: 'images'` (not a real MIME) | All files allowed | Use `'image/*'` |
| Tried to restrict by file size via accept | Not possible | Use field-level validation or external provider's settings |
| Forgot to allow PDFs when needed | Editor can't upload | Add `application/pdf` |
| Allowed SVG without sanitization | XSS risk | Sanitize or block SVG |
| `accept: '*'` (single asterisk) | Allows everything | Use `'*/*'` for "all" |
