# Google Cloud Run

Container-based, auto-scaling deploy with built-in IAM authentication.

---

## 1. Prerequisites

- Personal Google account (work/school accounts may have API restrictions).
- GCP project with billing enabled. Free trial: $300 credit. Codelab cost: < $1.
- `gcloud` CLI (the official tutorial uses Cloud Shell which has it preinstalled).

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

---

## 2. Create the project

```bash
npx create-mcp-use-app mcp-on-cloudrun
cd mcp-on-cloudrun
npm install
```

Server entry must read `PORT` from env — Cloud Run injects it:

```typescript
const port = parseInt(process.env.PORT || "8080", 10);
await server.listen(port);
```

---

## 3. Dockerfile

```dockerfile
FROM node:22-slim
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

ENV NODE_ENV=production
EXPOSE $PORT
CMD ["npm", "start"]
```

`.dockerignore`:

```
node_modules
.git
.gitignore
*.md
.env
.env.local
```

---

## 4. Service account and IAM

```bash
# Create dedicated service account
gcloud iam service-accounts create mcp-server-sa \
  --display-name="MCP Server Service Account"

# Grant Cloud Build access to Artifact Registry
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

---

## 5. Deploy

```bash
gcloud run deploy zoo-mcp-server \
  --service-account=mcp-server-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --region=europe-west1 \
  --source=. \
  --labels=dev-tutorial=codelab-mcp
```

`--no-allow-unauthenticated` requires IAM auth. Without it, **anyone** can call your MCP server.

First-time deploy will prompt to create the Artifact Registry repository. Type `Y`.

After ~2-3 min:

```
Service [zoo-mcp-server] revision [...] has been deployed and is serving 100 percent of traffic.
```

---

## 6. Client authentication

Grant invoker role to your account:

```bash
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member=user:$(gcloud config get-value account) \
  --role='roles/run.invoker'

export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
export ID_TOKEN=$(gcloud auth print-identity-token)
```

Gemini CLI `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "zoo-remote": {
      "httpUrl": "https://zoo-mcp-server-$PROJECT_NUMBER.europe-west1.run.app/mcp",
      "headers": {
        "Authorization": "Bearer $ID_TOKEN"
      }
    }
  }
}
```

> Gemini CLI uses `httpUrl`. Standard MCP clients (Claude Desktop, Inspector) use `url`.

`ID_TOKEN` expires hourly — refresh with `gcloud auth print-identity-token` and update the client config, or use a long-lived service-account key for stable tooling.

---

## 7. Multi-replica sessions

Cloud Run scales to multiple replicas. The default in-memory session store is per-replica — sessions break when traffic shifts. Use `RedisSessionStore`:

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

const server = new MCPServer({
  name: "cloud-run-mcp",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
});
```

Set `--min-instances=1` to avoid cold starts on every deploy.

---

## 8. Verify

```bash
gcloud run services logs read zoo-mcp-server --region europe-west1 --limit=5
```

Expected output:

```
"POST /mcp HTTP/1.1" 200 OK
Processing request of type CallToolRequest
```

---

**Canonical doc:** https://manufact.com/docs/typescript/server/deployment/google
