# OpenAPI → MCP

*Read this when generating MCP tools from an OpenAPI/Swagger spec, or deciding whether to use fromOpenAPI() or hand-write tools.*

`MCPServer.fromOpenAPI()` creates an MCP server from a parsed OpenAPI document. Each operation is registered as a tool that calls the matching HTTP endpoint.

## Basic usage

```typescript
import { MCPServer } from "mcp-use";

const response = await fetch("https://api.example.com/openapi.json");
const spec = (await response.json());

const server = MCPServer.fromOpenAPI({
  spec,
  baseUrl: "https://api.example.com",
});

await server.listen(3000);
```

Tool names come from `operationId`; descriptions from `summary` and route. Input schemas are mapped from parameters and JSON bodies.

## Options (FromOpenAPIOptions)

```typescript
MCPServer.fromOpenAPI({
  spec: openapi,
  baseUrl?: "https://api.example.com", // defaults to spec.servers[0].url
  name?: "my-server",                   // defaults to spec.info.title
  version?: "1.0.0",                    // defaults to spec.info.version
  auth?: {
    type: "bearer",
    token: process.env.API_TOKEN,
  },
  // OR
  auth?: {
    type: "header",
    name: "x-api-key",
    value: process.env.API_KEY,
  },
  headers?: { "User-Agent": "my-app/1.0" },
  tags?: ["weather", "forecast"],       // include only these
  exclude?: [
    { operationId: "deleteUser" },      // exclude by operationId
    { path: "/admin/*" },               // or path glob
    { method: "DELETE" },               // or HTTP method
    { tag: "deprecated" },              // or OpenAPI tag
  ],
  fetch?: customFetch,
});
```

## Parameter mapping

OpenAPI parameters become tool input schema fields:

| Parameter type | Input field | Notes |
|---|---|---|
| Path parameter | required top-level | e.g., `/users/{id}` → `id: string` |
| Query parameter | optional/required top-level | preserved from spec |
| Header parameter | top-level field | sent as HTTP header |
| Cookie parameter | ignored | not supported |
| JSON body | `body` field | object fields merged if primitive body |

Example: `GET /weather?city=Seattle&unit=celsius` generates schema with `city` (required) and `unit` (optional).

## Response handling

Successful (2xx) responses return `object()` helper for JSON or `text()` for plain text. Non-2xx responses return MCP error envelope.

## Hard limitations

- **No automatic `$ref` bundling** — remote schema refs are not bundled; pass a dereferenced spec.
- **JSON bodies only** — form-encoded, multipart, and binary uploads are not supported.
- **No cookie parameters** — cookies cannot be mapped as fields.
- **No automatic model-friendly workflows** — generated tools call the API 1:1 without combining calls or filtering response fields.

## When to use fromOpenAPI()

✅ **Use it for:**
- Rapid prototyping or testing API integration
- Small internal APIs for trusted users
- Bootstrap before hand-writing a custom server
- APIs with simple, clear operations

❌ **Don't use it for production without review:**
- High-volume user-facing servers — hand-write tools
- APIs requiring complex multi-call workflows — combine calls in server
- APIs with noisy or confusing field names — curate descriptions
- APIs with large response objects — filter to only relevant fields

## When to hand-write tools

For production, prefer `server.tool()` definitions that:

```typescript
// Custom workflow: combine multiple API calls
export const getUserProfile = server.tool(
  {
    name: "get-user-profile",
    description: "Get complete user profile with organizations",
    inputSchema: z.object({
      userId: z.string().describe("User ID"),
    }),
  },
  async ({ userId }) => {
    const user = await fetch(`/users/${userId}`).then(r => r.json());
    const orgs = await fetch(`/users/${userId}/organizations`).then(r => r.json());
    return object({ user, organizations: orgs });
  }
);
```

- Combine multiple operations into one tool (reducing round-trips)
- Filter and curate response fields
- Add clear, model-friendly descriptions
- Handle auth, retries, and error scenarios

## Vendor workflow: openapi-to-mcp skill

For structured OpenAPI-to-MCP generation with schema curation, see `build-mcp-use-server` sister skill `openapi-to-mcp` (in `/tmp/mcp-use-beta/skills/`). It provides:

1. Step-by-step spec acquisition and dereferencing
2. Zod schema mapping with descriptions
3. Multi-step HTTP client wiring
4. Deployment-ready structure

Use `fromOpenAPI()` for quick prototypes; use the vendor skill for production servers from OpenAPI specs.

## Example: weather API

```typescript
const spec = {
  openapi: "3.0.0",
  info: { title: "Weather", version: "1.0" },
  paths: {
    "/forecast": {
      get: {
        operationId: "getForecast",
        parameters: [
          { name: "city", in: "query", required: true, schema: { type: "string" } },
          { name: "days", in: "query", required: false, schema: { type: "integer" } },
        ],
        responses: { "200": { ... } },
      },
    },
  },
};

const server = MCPServer.fromOpenAPI({
  spec,
  baseUrl: "https://api.weather.example.com",
});

await server.listen(3000);
// Tool "getForecast" is now available; takes city (required) and days (optional)
```

## Debugging generated tools

Use the inspector (`npm run dev` → `http://localhost:3000/mcp/inspector`) to verify:
- Tool names and descriptions are correct
- Input schemas match your expectations
- Calls succeed and return expected data
