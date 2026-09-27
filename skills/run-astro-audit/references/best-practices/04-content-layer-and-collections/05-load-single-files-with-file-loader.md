# Ingest Datasets from Single Files with the file Loader and Custom Parsers

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Many datasets exist naturally as a single consolidated file rather than hundreds of individual files—such as author profiles, navigation taxonomies, or product catalogs. The built-in `file()` loader in `astro/loaders` ingests a single JSON, YAML, or TOML file into individual collection entries. It enforces that every entry possesses a unique `id` property, validates each item against your Zod schema, and allows custom parsing logic for non-standard formats (such as CSV or custom delimiters).

## 2. How It Differs From Classic React / Next.js

In Next.js, importing a large JSON file directly (`import catalog from './products.json'`) embeds the entire JSON payload into the build bundle and page props. If only three fields of ten products are displayed, the entire multi-megabyte payload is serialized into `__NEXT_DATA__`. In Astro 5, `file()` stores parsed entries into the server-side datastore; pages query only the exact entries or fields they need, shipping zero unneeded JSON bytes to the client.

## 3. Common Mistakes & Anti-Patterns

Supplying a JSON or YAML file whose array items lack a unique `id` property causes the `file()` loader to fail during content synchronization. Another anti-pattern is directly importing raw JSON files across components rather than querying them via `getCollection()`.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/components/AuthorsList.astro (Direct JSON import)
// ❌ Imports unvalidated JSON; bypasses schema checks, relations, and caching
import authorsRaw from '../data/authors.json'

interface Author {
  name: string
  bio?: string
}
const authors = authorsRaw as Author[]
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Built-in file loader with validation)
import { defineCollection, z } from 'astro:content'
import { file } from 'astro/loaders'

const authors = defineCollection({
  // ✅ Loads and indexes items from a single JSON file
  loader: file('src/data/authors.json'),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    role: z.string(),
    bio: z.string().optional(),
    avatar: z.string().url(),
  }),
})

export const collections = { authors }
```

```json
// src/data/authors.json (Each entry must contain a unique "id")
[
  {
    "id": "sarah-connor",
    "name": "Sarah Connor",
    "role": "Lead Architect",
    "avatar": "https://example.com/sarah.jpg"
  },
  {
    "id": "john-doe",
    "name": "John Doe",
    "role": "Senior Engineer",
    "avatar": "https://example.com/john.jpg"
  }
]
```

## 4. Verification & Audit

Run `pnpm astro sync` to verify that the file loader can parse your data file and that every record has a unique `id`:

```bash
pnpm astro sync
```

If an entry lacks an `id` or violates the Zod schema, the command terminates with an explicit validation error pointing to the exact item.
