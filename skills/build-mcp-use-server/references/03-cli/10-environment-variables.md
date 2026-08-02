# Environment Variables

*Read this to understand which env vars the CLI and server respect.*

## CLI-respected variables

These affect CLI command behavior:

| Variable | Used by | Default | Effect |
|----------|---------|---------|--------|
| `$PORT` | dev, start | `3000` | HTTP listener port (flag `--port` takes precedence) |
| `$HOST` | dev, start | `127.0.0.1` | HTTP listener address (flag `--host` takes precedence) |
| `$NODE_ENV` | start | set to `production` | Forced by start command; not read from env |
| `$MCP_URL` | dev | auto-set | Public URL for tunnel or override; set by CLI if `--tunnel` used |
| `$npm_config_user_agent` | create-mcp-use-app | auto-detect | Detects package manager (npm/pnpm/bun) from invocation |

## Server-respected variables

Your MCP server receives all environment variables at runtime. Common patterns:

```bash
# Auth
export DATABASE_URL=postgres://user:pass@host/db
export OPENAI_API_KEY=sk-...
export OAUTH_CLIENT_ID=client123
export OAUTH_CLIENT_SECRET=secret456

# Deployment
export NODE_ENV=production
export PORT=8080
export LOG_LEVEL=debug

# Then run your server
mcp-use dev
mcp-use start
mcp-use deploy --env DATABASE_URL=$DATABASE_URL
```

## deploy: passing env to cloud

Use `--env` or `--env-file` to set runtime env vars on the cloud deployment:

```bash
# Individual vars
mcp-use deploy --env API_KEY=secret --env DB_URL=postgres://...

# Load from file
mcp-use deploy --env-file .env.production
```

Vars passed via `--env` or `--env-file` override defaults and are stored in Manufact Cloud; your code reads them via `process.env` at runtime.

## Securing secrets

**Do not:**
- Commit `.env` files to git (add `.env*` to `.gitignore`)
- Pass API keys as command-line args where they appear in shell history

**Do:**
- Use CI secrets (GitHub Actions `secrets.MY_KEY`)
- Store in `.env.production` (git-ignored) for local deploys
- Use Manufact Cloud env var UI for persistent secrets

**Example CI workflow (GitHub Actions):**
```yaml
- name: Deploy to Manufact
  env:
    MANUFACT_API_KEY: ${{ secrets.MANUFACT_API_KEY }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    mcp-use login --api-key "$MANUFACT_API_KEY"
    mcp-use deploy --env DATABASE_URL="$DATABASE_URL"
```

## Priority order

For a given env var, the precedence is:

1. Flag (e.g., `--port 8000`)
2. Environment variable (e.g., `$PORT=8000`)
3. Default (e.g., `3000`)

Example:

```bash
# $PORT is set but flag overrides
PORT=9000 mcp-use dev --port 8000
# → listens on 8000

# Only $PORT is set
PORT=9000 mcp-use dev
# → listens on 9000

# Neither set
mcp-use dev
# → listens on 3000
```

## Accessing env vars in your server code

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Read env at startup
const dbUrl = process.env.DATABASE_URL;
const apiKey = process.env.OPENAI_API_KEY;

server.tool({
  name: "query",
  description: "Query database",
  inputSchema: { /* ... */ },
  async handler(input) {
    // dbUrl is available in handler closure
    const result = await db.query(dbUrl, input.sql);
    return { text: result };
  },
});

server.listen(parseInt(process.env.PORT || "3000"));
```

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Cannot find API key" | Env var not set | `export KEY=value` before running CLI |
| Port already in use | `$PORT` or default conflicts | `PORT=8000 mcp-use dev` or use `--port` |
| Build fails with `undefined` | Env var referenced but not defined | Check `.env` or pass via `--env` |
| Cloud deploy missing secret | Env var not passed to deploy | Use `--env` or `--env-file` |

## Deployment example

```bash
# Local development (reads from shell env)
export DATABASE_URL=localhost
mcp-use dev

# Production deploy (passes env to cloud)
mcp-use deploy \
  --env DATABASE_URL=postgres://prod-db/... \
  --env OPENAI_API_KEY=sk-prod-key \
  --env NODE_ENV=production
```
