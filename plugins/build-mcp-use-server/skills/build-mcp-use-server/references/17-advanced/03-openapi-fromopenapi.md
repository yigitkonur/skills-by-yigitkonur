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
    { operationId: "deleteUser" },      // exact match or RegExp
    { path: "/admin/.*" },              // exact match or RegExp (not a glob)
    { method: "DELETE" },               // HTTP method, case-insensitive
    { tags: ["deprecated"] },           // matches if operation has any of these tags
  ],
  fetch?: customFetch,
});
```

Fields within one `exclude` rule are ANDed together; a rule with both `method` and `tags` only excludes operations matching both. `operationId` and `path` accept an exact string or a `RegExp` — there is no glob syntax, so `"/admin/*"` would not match `/admin/users` as a path prefix.

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

- Non-2xx upstream responses return `{ isError: true, content: [{ type: "text", text: <response body> }] }`.
- 2xx responses with a JSON content type (`application/json` or `*+json`) return `{ content: [{ type: "text", text: <JSON.stringify(data)> }], structuredContent: data }`. If the body fails to parse as JSON, it falls back to a plain text block.
- 2xx responses with any other content type return `{ content: [{ type: "text", text: <response body> }] }`.

Generated tools build these results directly — they do not go through the deprecated `object()`/`text()` helpers from `mcp-use` (see the hand-write example below for the current recommended shape).

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
    const data = { user, organizations: orgs };
    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
      structuredContent: data,
    };
  }
);
```

- Combine multiple operations into one tool (reducing round-trips)
- Filter and curate response fields
- Add clear, model-friendly descriptions
- Handle auth, retries, and error scenarios

## End-to-end workflow

For the full scaffold-load-inspect-verify sequence (including scaffolding with `create-mcp-use-app`, resolving `$ref`s before calling `fromOpenAPI()`, and inspecting generated tools), see `references/30-workflows/06-openapi-to-mcp.md`.

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
