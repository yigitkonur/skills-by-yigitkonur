# Tool Results and Error Handling

## `ToolResultObject` Type

```typescript
type ToolResultType = "success" | "failure" | "rejected" | "denied";

type ToolBinaryResult = {
    data: string;       // base64-encoded binary data
    mimeType: string;   // e.g., "image/png", "application/pdf"
    type: string;       // content block type identifier
    description?: string;
};

type ToolResultObject = {
    textResultForLlm: string;              // primary text shown to the model
    binaryResultsForLlm?: ToolBinaryResult[]; // binary attachments (images, files)
    resultType: ToolResultType;            // outcome classification
    error?: string;                        // error detail (use with "failure" resultType)
    sessionLog?: string;                   // debug log not shown to model
    toolTelemetry?: Record<string, unknown>; // arbitrary telemetry metadata
};

type ToolResult = string | ToolResultObject;
```

Import: `import type { ToolResultObject } from "@github/copilot-sdk";`

## Returning Simple Strings

The simplest return type. The SDK passes the string directly to the model as the tool result.

```typescript
const tool = defineTool("get_time", {
    description: "Get the current time",
    handler: () => new Date().toISOString(),
});

// Or with parameters
const tool2 = defineTool("encrypt_string", {
    description: "Encrypts a string",
    parameters: z.object({ input: z.string() }),
    handler: ({ input }) => input.toUpperCase(), // returns string
});
```

## Returning Structured Objects

Return any serializable object. The SDK serializes it to a JSON string before passing to the model.

```typescript
const tool = defineTool("get_weather", {
    description: "Gets weather for a city",
    parameters: z.object({ city: z.string() }),
    handler: ({ city }) => ({
        city,
        temperature: "72°F",
        humidity: "45%",
        condition: "sunny",
        forecast: ["sunny", "cloudy", "rainy"],
    }),
    // serialized as JSON: {"city":"Paris","temperature":"72°F",...}
});
```

## Returning `ToolResultObject` for Success

Use `ToolResultObject` when you need to attach binary data, include debug logs, or send telemetry alongside the result.

```typescript
import type { ToolResultObject } from "@github/copilot-sdk";

const tool = defineTool("get_weather", {
    description: "Gets weather for a city",
    parameters: z.object({ city: z.string() }),
    handler: ({ city }): ToolResultObject => ({
        textResultForLlm: `The weather in ${city} is sunny and 72°F`,
        resultType: "success",
        sessionLog: `API call completed at ${Date.now()}ms`,
        toolTelemetry: { source: "openweathermap", latencyMs: 140 },
    }),
});
```

## Returning Errors from Tools

### Option 1: Return `ToolResultObject` with `resultType: "failure"`

This is the **preferred approach** for expected failures (API unavailable, resource not found, validation error). The model sees the error text and can respond gracefully.

```typescript
const tool = defineTool("check_status", {
    description: "Checks the status of a service",
    handler: (): ToolResultObject => ({
        textResultForLlm: "Service unavailable — API timed out after 5000ms",
        resultType: "failure",
        error: "ETIMEDOUT: connect to api.example.com:443",
        sessionLog: "Attempted 3 retries before giving up",
    }),
});
```

The model receives `textResultForLlm` and treats the call as failed. The `error` field is for structured error classification; `textResultForLlm` is what influences the model's response.

### Option 2: Throw an exception

When a handler throws, the SDK catches the error and reports it as a tool failure. **The exception message is NOT exposed to the model** — this is intentional to prevent leaking internal details.

```typescript
const tool = defineTool("get_user_location", {
    description: "Gets the user's location",
    handler: () => {
        throw new Error("Melbourne"); // model does NOT see "Melbourne"
    },
});
// The model receives a generic error response and may say "I couldn't determine your location"
```

Use `throw` for truly unexpected runtime errors (null dereference, network timeout with no graceful path). Use `ToolResultObject` with `resultType: "failure"` when you want the model to see a meaningful error message.

### Option 3: `resultType: "rejected"` and `resultType: "denied"`

Use `rejected` when the tool determined the request is semantically invalid:

```typescript
handler: ({ userId }): ToolResultObject => {
    if (userId <= 0) {
        return {
            textResultForLlm: `Invalid userId: ${userId}. Must be a positive integer.`,
            resultType: "rejected",
            error: "INVALID_INPUT",
        };
    }
    return { textResultForLlm: "User found", resultType: "success" };
}
```

Use `denied` when a policy or permission check blocks the operation:

```typescript
handler: ({ filePath }): ToolResultObject => {
    if (filePath.includes("/etc/")) {
        return {
            textResultForLlm: "Access denied: cannot read system files",
            resultType: "denied",
        };
    }
    return { textResultForLlm: readFile(filePath), resultType: "success" };
}
```

## Returning Images and Binary Data

Attach base64-encoded binary data using `binaryResultsForLlm`. The model receives both the text description and the binary content.

```typescript
import { readFileSync } from "fs";

const tool = defineTool("capture_screenshot", {
    description: "Captures a screenshot of the current browser window",
    parameters: z.object({
        selector: z.string().optional().describe("CSS selector to screenshot"),
    }),
    handler: async ({ selector }): Promise<ToolResultObject> => {
        const screenshotBuffer = await captureScreenshot(selector);
        const base64Data = screenshotBuffer.toString("base64");

        return {
            textResultForLlm: "Screenshot captured successfully",
            resultType: "success",
            binaryResultsForLlm: [
                {
                    type: "image",
                    data: base64Data,
                    mimeType: "image/png",
                    description: `Screenshot of ${selector ?? "full page"}`,
                },
            ],
        };
    },
});
```

### Reading a file as binary

```typescript
const tool = defineTool("read_pdf", {
    description: "Read and extract content from a PDF file",
    parameters: z.object({ path: z.string().describe("Path to PDF file") }),
    handler: async ({ path }): Promise<ToolResultObject> => {
        const buffer = readFileSync(path);
        return {
            textResultForLlm: `PDF file at ${path} (${buffer.length} bytes)`,
            resultType: "success",
            binaryResultsForLlm: [
                {
                    type: "document",
                    data: buffer.toString("base64"),
                    mimeType: "application/pdf",
                    description: `PDF: ${path}`,
                },
            ],
        };
    },
});
```

## Tool Execution Events

Listen for tool lifecycle events on the session to track execution:

```typescript
session.on((event) => {
    switch (event.type) {
        case "tool.execution_start":
            // Fired when a tool call begins
            console.log(`Running: ${event.data.toolName} [${event.data.toolCallId}]`);
            break;
        case "tool.execution_complete":
            // Fired when a tool call finishes
            console.log(`Completed: ${event.data.toolCallId}`);
            break;
    }
});
```

The `tool.execution_start` event fires before the handler runs. The `tool.execution_complete` event fires after the handler returns (whether success or failure).

These events are visible in the cookbook recipe for managing local files:
```typescript
session.on((event) => {
    switch (event.type) {
        case "tool.execution_start":
            console.log(`  → Running: ${event.data.toolName} ${event.data.toolCallId}`);
            break;
        case "tool.execution_complete":
            console.log(`  ✓ Completed: ${event.data.toolCallId}`);
            break;
    }
});
```

## Error Propagation in Tool Chains

When a tool returns `resultType: "failure"`, the model sees the failure text and decides what to do next. It may:
- Retry with different parameters.
- Call a different tool.
- Ask the user for clarification.
- Report the failure in its response.

Design `textResultForLlm` to be actionable — tell the model what failed and what it might try instead:

```typescript
handler: async ({ query }): Promise<ToolResultObject> => {
    try {
        const result = await database.query(query);
        return {
            textResultForLlm: JSON.stringify(result),
            resultType: "success",
        };
    } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
            textResultForLlm: `Query failed: ${message}. Check the SQL syntax and try again.`,
            resultType: "failure",
            error: message,
            sessionLog: `Query: ${query}\nError: ${message}`,
        };
    }
}
```

## Long-Running Tool Patterns

For tools that may take significant time, return an immediate acknowledgment and use session state for async updates. Since `sendAndWait` blocks until the model produces its final response (which waits for all tool calls), avoid blocking the handler unnecessarily.

### Timeout pattern

```typescript
const tool = defineTool("run_tests", {
    description: "Run the test suite",
    parameters: z.object({
        timeout: z.number().optional().describe("Timeout in milliseconds, default 30000"),
    }),
    handler: async ({ timeout = 30_000 }): Promise<ToolResultObject> => {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeout);

        try {
            const result = await runTestSuite({ signal: controller.signal });
            clearTimeout(timer);
            return {
                textResultForLlm: `Tests completed: ${result.passed} passed, ${result.failed} failed`,
                resultType: result.failed > 0 ? "failure" : "success",
                toolTelemetry: { durationMs: result.durationMs },
            };
        } catch (err) {
            clearTimeout(timer);
            if (controller.signal.aborted) {
                return {
                    textResultForLlm: `Test run timed out after ${timeout}ms. Consider running a subset of tests.`,
                    resultType: "failure",
                    error: "TIMEOUT",
                };
            }
            throw err; // re-throw unexpected errors
        }
    },
});
```

### Progress reporting via sessionLog

Use `sessionLog` to log intermediate state that does NOT influence the model but aids debugging:

```typescript
handler: async ({ url }): Promise<ToolResultObject> => {
    const log: string[] = [];

    log.push(`Starting crawl of ${url}`);
    const pages = await crawl(url, { onPage: (p) => log.push(`Crawled: ${p}`) });
    log.push(`Crawl complete: ${pages.length} pages`);

    return {
        textResultForLlm: `Crawled ${pages.length} pages from ${url}`,
        resultType: "success",
        sessionLog: log.join("\n"),
        toolTelemetry: { pageCount: pages.length, startUrl: url },
    };
}
```
