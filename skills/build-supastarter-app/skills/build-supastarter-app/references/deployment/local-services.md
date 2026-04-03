# Local Services

> Documents the local infrastructure used during development. Consult this when booting the app locally or reproducing storage/database features.

## Docker compose services

The repo ships `docker-compose.yml` for:

- PostgreSQL 16 on port `5432`
- MinIO on ports `9000` and `9001`
- a setup container that creates the `avatars` bucket

## Typical flow

```bash
docker compose up -d
pnpm generate
pnpm db:push
pnpm dev
```

This gives the web app a local database plus S3-compatible object storage for avatar uploads.

---

**Related references:**
- `references/setup/environment-setup.md` — Full local setup walkthrough
- `references/storage/bucket-config.md` — The `avatars` bucket configuration
- `references/cheatsheets/commands.md` — Common local-dev commands
- `references/storage/s3-provider.md` — S3 provider configuration
