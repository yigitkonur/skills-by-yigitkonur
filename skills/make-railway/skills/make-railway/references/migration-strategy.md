# Migration strategy

Schema changes on Railway need an idempotent boot script. The pattern: `prisma migrate deploy` runs on every container start, applies pending migrations, then hands off to `npm start`.

## The `start.sh` pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "→ Prisma migrate deploy ($(date -u +%H:%M:%S))"
npx prisma migrate deploy

echo "→ migrations done; handing off"
```

In `Dockerfile`:

```Dockerfile
CMD ["sh", "-c", "./scripts/start.sh && npm start"]
```

`migrate deploy` is **idempotent** — it only applies migrations not yet recorded in `_prisma_migrations`. Safe to re-run on every boot.

## Legacy `db push`-provisioned DB

If the prod DB was provisioned via `prisma db push` (no migration history), `migrate deploy` will refuse because the schema state doesn't match any migration.

Bootstrap with `migrate resolve` to mark the existing schema as "applied":

```bash
# In start.sh, before migrate deploy:
echo "→ baselining legacy migrations"
npx prisma migrate resolve --applied 20260101000000_initial    || true
npx prisma migrate resolve --applied 20260201000000_add_users  || true
# ... one per legacy migration
echo "→ applying new migrations"
npx prisma migrate deploy
```

Each `resolve` is idempotent (errors if already applied; the `|| true` swallows). After the first successful boot, future boots skip the resolves and go straight to `migrate deploy`.

## Force-replay an idempotent migration

If a post-`db push` migration was already applied via `db push` but exists as a migration file (DDL is idempotent), force replay:

```bash
# In start.sh:
psql "$DATABASE_URL" -c "DELETE FROM _prisma_migrations WHERE migration_name = '20260301000000_add_indexes';" 2>/dev/null || true
npx prisma migrate deploy   # will re-apply the deleted row's migration
```

Only works if the migration's DDL is `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` style. Otherwise you'll get duplicate-object errors.

## Web vs worker timing

If both web and worker boot simultaneously and both call `migrate deploy`, Postgres advisory locks (Prisma's default) serialize them. Safe.

But: if migration takes >30s and the web service has a faster health-check timeout, web will be killed mid-migration. Mitigate by running migrations in a separate one-shot service before web/worker:

```bash
# Or skip worker's migrate call if web handles it:
[ "$ZEO_ROLE" = "worker" ] && {
  # Wait for migrations to complete (poll)
  until psql "$DATABASE_URL" -c "SELECT 1 FROM _prisma_migrations LIMIT 1" >/dev/null 2>&1; do sleep 2; done
} || npx prisma migrate deploy
```

## Don't `db push` to prod, ever

`prisma db push` writes the schema directly without recording a migration. Catastrophic for shared prod DBs:

- No history of changes
- Can't roll back
- Other contributors can't reproduce

Only `db push` to a private dev DB (your local docker postgres). For shared anything: `prisma migrate dev` locally, commit the migration, `migrate deploy` on Railway.

## Migration drift detection

If someone hot-fixed prod via SQL outside of migrations, the schema drifts from the migration history. Detect:

```bash
npx prisma migrate status
# Database schema is out of sync with the migration history.
```

Recover:

1. Capture the drift: `prisma db pull` writes the live schema to `prisma/schema.prisma`
2. Generate a new migration: `prisma migrate dev --name capture_drift`
3. Review the generated SQL, edit if needed, commit

This re-aligns history with reality.

## Staging-first deploys

For risky migrations:

1. Deploy migration + code to `staging` first
2. Verify nothing broke
3. Then deploy to `production`

The Makefile pattern: separate `make prod-staging` and `make prod` targets, each with their own `railway environment` switch:

```makefile
prod-staging: _check-prod-prereqs
	@railway environment staging
	@$(MAKE) prod

prod: _check-prod-prereqs
	@railway environment production
	@... (deploy logic)
```
