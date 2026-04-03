# Database Migration Patterns

## Overview

Migrations manage database schema evolution over time. Both Drizzle and Prisma provide
migration tools that integrate well with Fastify + TypeBox projects. This covers
patterns for both ORMs plus CI/CD considerations.

## Drizzle Migrations

### Configuration

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!
  },
  verbose: true,
  strict: true
})
```

### Generating Migrations

```bash
# Generate migration from schema diff
npx drizzle-kit generate --name add_posts_table

# Generated file: drizzle/migrations/0001_add_posts_table.sql
```

```sql
-- drizzle/migrations/0001_add_posts_table.sql
CREATE TABLE IF NOT EXISTS "posts" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "title" varchar(200) NOT NULL,
  "content" text NOT NULL,
  "author_id" uuid NOT NULL REFERENCES "users"("id"),
  "published" boolean NOT NULL DEFAULT false,
  "created_at" timestamp NOT NULL DEFAULT now()
);

CREATE INDEX "posts_author_id_idx" ON "posts" ("author_id");
```

### Applying Migrations

```typescript
// src/db/migrate.ts
import { drizzle } from 'drizzle-orm/postgres-js'
import { migrate } from 'drizzle-orm/postgres-js/migrator'
import postgres from 'postgres'

async function runMigrations() {
  const client = postgres(process.env.DATABASE_URL!, { max: 1 })
  const db = drizzle(client)

  console.log('Running migrations...')
  await migrate(db, { migrationsFolder: './drizzle/migrations' })
  console.log('Migrations complete')

  await client.end()
}

runMigrations().catch(console.error)
```

### Run Migrations on Fastify Startup

```typescript
// src/plugins/database.ts
import fp from 'fastify-plugin'
import { drizzle } from 'drizzle-orm/postgres-js'
import { migrate } from 'drizzle-orm/postgres-js/migrator'
import postgres from 'postgres'

export default fp(async (app) => {
  const client = postgres(app.config.DATABASE_URL)
  const db = drizzle(client)

  // Run migrations before serving traffic
  if (app.config.RUN_MIGRATIONS) {
    app.log.info('Running database migrations...')
    await migrate(db, { migrationsFolder: './drizzle/migrations' })
    app.log.info('Migrations complete')
  }

  app.decorate('db', db)
  app.addHook('onClose', () => client.end())
})
```

## Prisma Migrations

### Generating Migrations

```bash
# Create migration (development)
npx prisma migrate dev --name add_posts_table

# Apply in production (no prompts, no generation)
npx prisma migrate deploy
```

### Custom Migration Scripts

```sql
-- prisma/migrations/20240101000000_add_fulltext_index/migration.sql
-- Prisma generates the base, you can edit before applying

CREATE INDEX "posts_search_idx" ON "posts"
USING GIN (to_tsvector('english', "title" || ' ' || "content"));
```

### Prisma Migrate in CI

```yaml
# .github/workflows/migrate.yml
jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Migration Best Practices

### Always Use Transactions

```sql
-- drizzle/migrations/0002_add_email_verified.sql
BEGIN;

ALTER TABLE "users" ADD COLUMN "email_verified" boolean NOT NULL DEFAULT false;
ALTER TABLE "users" ADD COLUMN "verified_at" timestamp;

COMMIT;
```

### Data Migrations

For data transformations, write a separate script:

```typescript
// scripts/backfill-slugs.ts
import { drizzle } from 'drizzle-orm/postgres-js'
import { sql } from 'drizzle-orm'
import postgres from 'postgres'

async function backfillSlugs() {
  const client = postgres(process.env.DATABASE_URL!)
  const db = drizzle(client)

  // Process in batches to avoid locking
  const BATCH_SIZE = 1000
  let processed = 0

  while (true) {
    const result = await db.execute(sql`
      UPDATE posts SET slug = lower(replace(title, ' ', '-'))
      WHERE slug IS NULL
      LIMIT ${BATCH_SIZE}
    `)

    processed += result.length
    if (result.length < BATCH_SIZE) break
    console.log(`Processed ${processed} rows...`)
  }

  console.log(`Backfill complete: ${processed} rows updated`)
  await client.end()
}
```

### Zero-Downtime Migration Strategy

1. **Add phase**: Add new column as nullable, deploy code that writes to both
2. **Backfill phase**: Run data migration script
3. **Switch phase**: Deploy code that reads from new column
4. **Cleanup phase**: Drop old column

```sql
-- Step 1: Add nullable column
ALTER TABLE users ADD COLUMN display_name varchar(200);

-- Step 2: Backfill (run as script)
UPDATE users SET display_name = name WHERE display_name IS NULL;

-- Step 3: After code deploy, make NOT NULL
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;

-- Step 4: Drop old column (after grace period)
ALTER TABLE users DROP COLUMN name;
```

## Package Scripts

```json
{
  "scripts": {
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx src/db/migrate.ts",
    "db:studio": "drizzle-kit studio",
    "db:reset": "drizzle-kit drop && npm run db:migrate",
    "db:seed": "tsx scripts/seed.ts"
  }
}
```

## Key Points

- Generate migrations from schema diffs, never write DDL by hand
- Run migrations before serving traffic or in a separate CI step
- Use transactions for multi-statement migrations
- Separate schema migrations from data backfills
- Follow add-backfill-switch-cleanup for zero-downtime changes
- Keep migrations in version control -- they are part of the deployment artifact
- Test migrations against a staging database before production
