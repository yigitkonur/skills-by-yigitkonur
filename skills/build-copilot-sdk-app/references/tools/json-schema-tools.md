# JSON Schema Tool Definition

## When to Use Raw JSON Schema Instead of Zod

Use raw JSON Schema when:
- Tools are generated at runtime from external sources (API specs, database schemas, config files).
- You need to consume a JSON Schema that already exists (OpenAPI spec, JSON Schema file).
- You are building a tool proxy that forwards schemas from an MCP server or other external source.
- You want to avoid the Zod dependency entirely.
- You need JSON Schema features Zod does not expose (e.g., `$ref`, `allOf`, `additionalProperties: false`).

Use Zod when you want TypeScript type inference in the handler. With raw JSON Schema, handler args are typed as `unknown` — you must cast or validate manually.

## `Tool` Interface

```typescript
import type { Tool } from "@github/copilot-sdk";

interface Tool<TArgs = unknown> {
    name: string;
    description?: string;
    parameters?: ZodSchema<TArgs> | Record<string, unknown>; // raw JSON Schema is Record<string, unknown>
    handler: ToolHandler<TArgs>;
    overridesBuiltInTool?: boolean;
}
```

When `parameters` is `Record<string, unknown>`, `TArgs` defaults to `unknown`. Cast inside the handler.

## Minimal Raw JSON Schema Tool

```typescript
import type { Tool } from "@github/copilot-sdk";

const getWeather: Tool = {
    name: "get_weather",
    description: "Get the current weather for a city",
    parameters: {
        type: "object",
        properties: {
            city: { type: "string", description: "The city name" },
        },
        required: ["city"],
    },
    handler: async (args) => {
        const { city } = args as { city: string }; // manual cast required
        return { city, temperature: "72°F", condition: "sunny" };
    },
};
```

## Full JSON Schema Object Structure

```typescript
const complexTool: Tool = {
    name: "search_records",
    description: "Search database records with filters",
    parameters: {
        type: "object",
        properties: {
            table: {
                type: "string",
                description: "Table to search",
                enum: ["users", "orders", "products"],
            },
            filters: {
                type: "object",
                description: "Key-value filter pairs",
                additionalProperties: { type: "string" },
            },
            limit: {
                type: "integer",
                description: "Max results to return",
                minimum: 1,
                maximum: 100,
                default: 10,
            },
            sortBy: {
                type: "string",
                description: "Field to sort by",
            },
            sortDirection: {
                type: "string",
                enum: ["asc", "desc"],
                default: "asc",
            },
            includeDeleted: {
                type: "boolean",
                description: "Include soft-deleted records",
                default: false,
            },
        },
        required: ["table"],
        additionalProperties: false,
    },
    handler: (args) => {
        const { table, filters, limit, sortBy, sortDirection, includeDeleted } =
            args as {
                table: "users" | "orders" | "products";
                filters?: Record<string, string>;
                limit?: number;
                sortBy?: string;
                sortDirection?: "asc" | "desc";
                includeDeleted?: boolean;
            };
        return { table, count: 0, results: [] };
    },
};
```

## Array Schema

```typescript
const batchProcess: Tool = {
    name: "batch_process",
    description: "Process a list of items",
    parameters: {
        type: "object",
        properties: {
            items: {
                type: "array",
                items: {
                    type: "object",
                    properties: {
                        id: { type: "string" },
                        value: { type: "number" },
                    },
                    required: ["id", "value"],
                },
                minItems: 1,
                maxItems: 50,
                description: "Items to process",
            },
            operation: {
                type: "string",
                enum: ["sum", "average", "max", "min"],
                description: "Aggregation operation",
            },
        },
        required: ["items", "operation"],
    },
    handler: (args) => {
        const { items, operation } = args as {
            items: Array<{ id: string; value: number }>;
            operation: "sum" | "average" | "max" | "min";
        };
        const values = items.map((i) => i.value);
        switch (operation) {
            case "sum": return values.reduce((a, b) => a + b, 0);
            case "average": return values.reduce((a, b) => a + b, 0) / values.length;
            case "max": return Math.max(...values);
            case "min": return Math.min(...values);
        }
    },
};
```

## Dynamic Tool Generation at Runtime

Generate tools from external schema sources without Zod:

```typescript
import type { Tool } from "@github/copilot-sdk";

interface OpenAPIOperation {
    operationId: string;
    summary?: string;
    requestBody?: { content: { "application/json": { schema: Record<string, unknown> } } };
}

function toolFromOpenAPI(operation: OpenAPIOperation): Tool {
    return {
        name: operation.operationId,
        description: operation.summary,
        parameters: operation.requestBody?.content["application/json"]?.schema ?? {
            type: "object",
            properties: {},
        },
        handler: async (args) => {
            const response = await fetch(`https://api.example.com/${operation.operationId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(args),
            });
            return response.json();
        },
    };
}

// Build tool list from API spec at runtime
async function buildToolsFromSpec(specUrl: string): Promise<Tool[]> {
    const spec = await fetch(specUrl).then((r) => r.json());
    return Object.entries(spec.paths as Record<string, Record<string, OpenAPIOperation>>)
        .flatMap(([, methods]) => Object.values(methods))
        .filter((op) => op.operationId)
        .map(toolFromOpenAPI);
}

// Register dynamically built tools
const dynamicTools = await buildToolsFromSpec("https://api.example.com/openapi.json");
const session = await client.createSession({
    onPermissionRequest: approveAll,
    tools: dynamicTools,
});
```

## Converting Between Zod and JSON Schema

Zod schemas expose `toJSONSchema()`. Extract the JSON Schema when you need to inspect, log, or forward it:

```typescript
import { z } from "zod";
import { defineTool } from "@github/copilot-sdk";

const schema = z.object({
    city: z.string().describe("City name"),
    units: z.enum(["celsius", "fahrenheit"]).optional(),
});

// Get the raw JSON Schema representation
const jsonSchema = schema.toJSONSchema();
console.log(JSON.stringify(jsonSchema, null, 2));
// {
//   "type": "object",
//   "properties": {
//     "city": { "type": "string", "description": "City name" },
//     "units": { "type": "string", "enum": ["celsius", "fahrenheit"] }
//   },
//   "required": ["city"]
// }
```

Convert a raw JSON Schema back to a typed tool by wrapping it in an object that satisfies `ZodSchema<T>`:

```typescript
// Wrap a raw JSON Schema to satisfy ZodSchema<T> interface
function wrapSchema<T>(schema: Record<string, unknown>) {
    return {
        _output: undefined as unknown as T,
        toJSONSchema: () => schema,
    };
}

type MyArgs = { city: string; units?: "celsius" | "fahrenheit" };

const tool = defineTool<MyArgs>("get_weather", {
    description: "Get weather",
    parameters: wrapSchema<MyArgs>({
        type: "object",
        properties: {
            city: { type: "string" },
            units: { type: "string", enum: ["celsius", "fahrenheit"] },
        },
        required: ["city"],
    }),
    handler: ({ city, units }) => {
        // city: string, units: "celsius" | "fahrenheit" | undefined — fully typed
        return `${city}: 72${units === "celsius" ? "°C" : "°F"}`;
    },
});
```

## Tool Arrays and Registration Patterns

Register raw JSON Schema tools alongside Zod tools — the `tools` array accepts both:

```typescript
import { CopilotClient, defineTool, approveAll } from "@github/copilot-sdk";
import type { Tool } from "@github/copilot-sdk";
import { z } from "zod";

// Zod tool — typed handler
const zodTool = defineTool("encrypt", {
    description: "Encrypt a string",
    parameters: z.object({ input: z.string() }),
    handler: ({ input }) => input.split("").reverse().join(""),
});

// Raw JSON Schema tool — untyped handler
const rawTool: Tool = {
    name: "format_date",
    description: "Format a date string",
    parameters: {
        type: "object",
        properties: {
            date: { type: "string", description: "ISO 8601 date string" },
            format: { type: "string", description: "Output format pattern" },
        },
        required: ["date"],
    },
    handler: (args) => {
        const { date, format } = args as { date: string; format?: string };
        return new Date(date).toLocaleString();
    },
};

const session = await client.createSession({
    onPermissionRequest: approveAll,
    tools: [zodTool, rawTool], // mixed array — both work
});
```

## Type Safety Considerations

Raw JSON Schema tools trade compile-time safety for runtime flexibility. Mitigate the risk:

### Option 1: Cast with validation

```typescript
handler: (args) => {
    if (typeof args !== "object" || args === null) {
        throw new Error("Invalid args: expected object");
    }
    const { city } = args as { city: string };
    if (typeof city !== "string") {
        throw new Error("Invalid args: city must be a string");
    }
    return fetchWeather(city);
},
```

### Option 2: Use a runtime validator (zod.parse after the fact)

```typescript
import { z } from "zod";

const ArgsSchema = z.object({ city: z.string(), units: z.enum(["celsius", "fahrenheit"]).optional() });

const rawTool: Tool = {
    name: "get_weather",
    description: "Get weather for a city",
    parameters: ArgsSchema.toJSONSchema(), // use Zod to generate schema
    handler: (args) => {
        const { city, units } = ArgsSchema.parse(args); // validate at runtime
        return fetchWeather(city, units);
    },
};
```

### Option 3: Use `defineTool` with the `wrapSchema` helper above for full type safety

This is the recommended pattern when you have a JSON Schema from an external source but want type inference in your handler.
