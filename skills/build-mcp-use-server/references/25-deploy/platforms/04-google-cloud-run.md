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
RUN npm run build
ENV NODE_ENV=production
EXPOSE $PORT
CMD ["npm", "start"]
```

The generated `start` script runs `mcp-use start`, which reads Cloud Run's `PORT` environment variable. Keep `.mcp-use/build/` in the image so Views remain available at runtime.

## Deploy

```bash
gcloud run deploy my-mcp-server \
  --no-allow-unauthenticated \
  --region europe-west1 \
  --source=.
```

`--no-allow-unauthenticated` requires callers to hold the Cloud Run Invoker role. Omit it only when a public MCP endpoint is intentional and you provide authentication inside the MCP server.

## Call an IAM-Protected Service

```bash
TOKEN=$(gcloud auth print-identity-token)

curl -H "Authorization: Bearer $TOKEN" \
  https://<service-url>/mcp
```

Assign a dedicated service account to the Cloud Run service when tools access other Google Cloud resources. Grant only the roles those tools need.

## Verify

```bash
gcloud run services logs read my-mcp-server \
  --region europe-west1
```

Then connect an MCP client using the Cloud Run service URL plus `/mcp`. Test the same authenticated path clients will use.

See `references/25-deploy/03-docker.md` for the grounded container baseline.
