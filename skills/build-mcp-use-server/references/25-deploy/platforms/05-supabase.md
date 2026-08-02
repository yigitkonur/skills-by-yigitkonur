# Supabase Edge Functions

*Read this when deploying an mcp-use server and Views to Supabase Edge Functions.*

Use the vendor's Supabase deployment example. It packages Views without Docker, a Storage bucket, project mutation, or an interactive script.

## Deploy

Install project dependencies, then run the example's deployment script with the public function URLs:

```bash
npm install

MCP_URL=https://<ref>.supabase.co/functions/v1/mcp \
MCP_ASSETS_URL=https://<ref>.supabase.co/functions/v1 \
npm run deploy:edge -- --project-ref <ref>
```

Use a current Supabase CLI. This path uses the CLI's API deployment mode; Docker is not a prerequisite.

## Handler and Assets

The deployment workflow:

1. Builds `.mcp-use/build/views/`.
2. Stages the generated View tree beneath the Edge Function directory.
3. Includes the tree through the function's `static_files` configuration.
4. Maps `/functions/v1/mcp/_mcp-use/*` to the staged View files.
5. Forwards every other request to `server.fetch`.

The public MCP endpoint is:

```text
https://<ref>.supabase.co/functions/v1/mcp
```

Do not replace this with an old Docker or Storage-bucket workflow; neither is required by the grounded example.

## Verify

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://<ref>.supabase.co/functions/v1/mcp \
  --tool <tool-name> \
  --output supabase-live-view.png
```

Confirm the rendered View, not only the function's HTTP status. A missing `static_files` entry can leave tool calls working while View assets return 404.
