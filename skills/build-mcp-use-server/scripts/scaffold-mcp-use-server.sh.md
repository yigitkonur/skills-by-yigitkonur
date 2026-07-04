# `scaffold-mcp-use-server.sh`

Conservative scaffolder for a minimal HTTP `mcp-use/server` project. Use only for greenfield HTTP tool servers.

## Run

```bash
bash scripts/scaffold-mcp-use-server.sh ./my-mcp-server
```

The output directory must be empty. To overwrite scaffold-managed files intentionally:

```bash
bash scripts/scaffold-mcp-use-server.sh ./my-mcp-server --force
```

## Writes

```text
package.json
tsconfig.json
src/server.ts
```

The scaffold includes:

- `"type": "module"`
- `mcp-use` and `zod` dependencies
- `@mcp-use/cli`, `typescript`, `@types/node`, and `tsx` dev dependencies
- `dev`, `build`, `start`, `generate-types`, and `typecheck` scripts
- minimal Streamable HTTP server with `/health`, `echo-message`, and `server-info`

## Refusal rules

- Missing output directory argument exits `2`.
- Existing non-directory output path exits `2`.
- Non-empty output directory exits `2` unless `--force` is passed.
- Existing scaffold-managed files are not overwritten unless `--force` is passed.

## Validate after scaffolding

```bash
cd ./my-mcp-server
npm install
npm run typecheck
npm run dev
```

Then use Inspector and the curl handshake in `references/22-validate/02-curl-handshake.md`.
