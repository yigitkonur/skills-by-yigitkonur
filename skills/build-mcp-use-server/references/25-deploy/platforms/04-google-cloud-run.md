# Google Cloud Run

*Read this when deploying an mcp-use server as an authenticated Cloud Run service.*

Cloud Run builds a Node container, scales it automatically, and can enforce Google Cloud IAM at the HTTPS boundary.

## Prerequisites

Set the target project, enable billing, and enable the required services:

```bash
gcloud config set project <PROJECT_ID>

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## Dockerfile

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run typecheck && npm run build
ENV NODE_ENV=production
CMD ["npm", "start"]
```

Run `typecheck` before `build` so a broken build never ships. `npm start` (`mcp-use start`) serves `.mcp-use/build/`, binds to the server's configured host (must be `0.0.0.0` — set `host: "0.0.0.0"` in `new MCPServer({...})`), and reads Cloud Run's injected `PORT`. Do not hardcode `EXPOSE $PORT`; Cloud Run injects the port at runtime rather than reading a static Dockerfile `EXPOSE`.

## Create a Runtime Service Account

Create a dedicated service account for the Cloud Run service rather than using the default compute identity:

```bash
gcloud iam service-accounts create my-mcp-runtime \
  --display-name="My MCP Cloud Run runtime"
```

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="europe-west1"
RUNTIME_SA="my-mcp-runtime@${PROJECT_ID}.iam.gserviceaccount.com"
```

Grant the service account only the IAM roles the server's tools actually need (e.g. a specific bucket or dataset role) — never a broad project-editor role.

## Deploy

```bash
gcloud run deploy my-mcp-server \
  --source=. \
  --region="${REGION}" \
  --service-account="${RUNTIME_SA}" \
  --no-allow-unauthenticated
```

`--no-allow-unauthenticated` requires callers to hold the Cloud Run Invoker role. Omit it only when a public MCP endpoint is intentional and you provide authentication inside the MCP server. Keep `--region`, `--service-account`, and `--no-allow-unauthenticated` on every subsequent deploy of the same revision so the IAM posture stays explicit and doesn't silently drift.

Grant your own identity invoker access so you can test the service:

```bash
ACCOUNT="$(gcloud config get-value account)"
gcloud run services add-iam-policy-binding my-mcp-server \
  --region="${REGION}" \
  --member="user:${ACCOUNT}" \
  --role="roles/run.invoker"
```

## Connect with a Materialized ID Token

Cloud Run ID tokens expire. Generate the client settings file immediately before use rather than embedding a shell variable name in JSON:

```bash
SERVICE_URL="$(
  gcloud run services describe my-mcp-server \
    --region="${REGION}" \
    --format="value(status.url)"
)"
ID_TOKEN="$(gcloud auth print-identity-token)"

curl -i -X POST "${SERVICE_URL}/mcp" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cloud-run-smoke","version":"1.0"}}}'
```

If a client returns `401 Unauthorized`, the token expired — regenerate it and refresh the client config.

## Verify

```bash
gcloud run services logs read my-mcp-server \
  --region="${REGION}" \
  --limit=20
```

Then connect an MCP client using the Cloud Run service URL plus `/mcp`. Test the same authenticated path clients will use.

See `references/25-deploy/03-docker.md` for the grounded container baseline.
