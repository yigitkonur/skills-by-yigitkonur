# Naming Rules

TinaCMS imposes strict rules on field and collection names. Breaking them produces obscure errors. Knowing the rules upfront saves an afternoon.

## Allowed characters

```
✅  letters (a-z, A-Z)
✅  digits (0-9)
✅  underscores (_)

❌  hyphens (-)
❌  spaces ( )
❌  dots (.)
❌  any other special character
```

## Examples

```typescript
// Good
{ name: 'heroImage', ... }       // camelCase
{ name: 'hero_image', ... }      // snake_case
{ name: 'imageURL', ... }        // mixed case OK
{ name: 'item2', ... }           // digits OK after a letter

// Breaks the schema
{ name: 'hero-image', ... }      // hyphens forbidden
{ name: 'hero image', ... }      // spaces forbidden
{ name: '2nd-place', ... }       // hyphens + leading digit
{ name: 'my.field', ... }        // dot forbidden
```

## Pick a convention

camelCase or snake_case both work. Pick one and stay consistent within a project. Mixing creates a maintenance footgun.

The auto-generated GraphQL types use whatever you pick — `heroImage` becomes `data.page.heroImage`, `hero_image` becomes `data.page.hero_image`.

## Reserved names — never use

| Name | Reason |
|---|---|
| `children` | Conflicts with React's `children` prop and TinaMarkdown rendering |
| `mark` | Conflicts with rich-text markup internals |
| `_template` | Reserved for multi-shape collection discriminator |
| `_sys` | Reserved for TinaCMS document metadata (`_sys.filename`, `_sys.breadcrumbs`) |
| `__typename` | GraphQL internal |
| `id` | Internal — Tina manages document IDs |

If you try to use one, the schema build fails with cryptic errors.

## Field names within an `object`

Same rules apply to nested object fields:

```typescript
// Good
{
  name: 'cta',
  type: 'object',
  fields: [
    { name: 'text', type: 'string' },
    { name: 'url', type: 'string' },
    { name: 'openInNewTab', type: 'boolean' },
  ],
}

// Breaks
{
  name: 'cta',
  type: 'object',
  fields: [
    { name: 'open-in-new-tab', type: 'boolean' },  // hyphen
  ],
}
```

## Field names within rich-text templates

Inside a rich-text template (MDX-embeddable component), the `name` becomes the JSX tag:

```typescript
{
  type: 'rich-text',
  templates: [
    { name: 'Cta', fields: [...] },        // editor inserts <Cta>
    { name: 'CodeBlock', fields: [...] },  // editor inserts <CodeBlock>
  ],
}
```

Same naming rules — but case matters. By convention, MDX-embedded component names start with an uppercase letter (PascalCase) to match React component naming.

`children` is doubly-reserved inside rich-text templates because it conflicts with the rich-text `children` AST property.

## Collection names

Collection `name` becomes the GraphQL query name:

```typescript
{ name: 'post', ... }
// → client.queries.post()
// → client.queries.postConnection()
```

Pluralization is up to you (Tina pluralizes by appending `Connection`). `post` and `posts` both work, but pick one and stick with it.

## Field labels can be anything

The `label` (display name in admin) has no character restrictions:

```typescript
{
  name: 'hero_image',
  label: "Hero Image (1920x1080 recommended — won't crop)",
  type: 'image',
}
```

Use `label` for human-readable, descriptive text. Use `name` for the machine-readable identifier.

## Field name vs MDX template name (case)

Inside rich-text fields, the `name` becomes the JSX tag exactly as written. If you register a `Cta` template, editors insert `<Cta />`. If you register `cta`, editors insert `<cta />` (which doesn't conform to JSX component naming).

**Rule:** PascalCase for rich-text templates, camelCase or snake_case for everything else.

## Migrating from a CMS with hyphens (Forestry, etc.)

If you're migrating from Forestry.io which allowed hyphens:

```bash
# Find all hyphenated frontmatter keys and convert to underscores
find content -name '*.md' -exec sed -i '' 's/^hero-image:/hero_image:/' {} \;
find content -name '*.md' -exec sed -i '' 's/^cover-photo:/cover_photo:/' {} \;
# Repeat for each hyphenated field
```

Then update your schema with the new names. Otherwise content won't resolve.

## Validation tools

```bash
pnpm dlx @tinacms/cli@latest audit
```

Reports invalid field names. Run after schema changes.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `name: 'hero-image'` | "Field name contains invalid characters" | Use `heroImage` or `hero_image` |
| `name: 'children'` | Conflict with rich-text internals | Rename |
| Mixed conventions in same schema | Confusing for editors and devs | Pick one convention, refactor |
| Frontmatter has hyphens but schema has underscores | Documents fail to parse | Run sed migration above |
| MDX template named `cta` (lowercase) | Editor's JSX is `<cta />` (invalid React) | Rename to `Cta` |
