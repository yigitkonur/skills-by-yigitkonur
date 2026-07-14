# Unit Testing Tool Handlers

Tool handlers are async functions that take `(args, ctx)` and return `text()` / `object()` / `widget()` / `binary()` outputs. Test them in isolation with Vitest, Jest, or `node --test` — no MCP server, no network, no Inspector.

The two mechanics that need care: **mocking `ctx`** (logger, progress, sampling, elicitation) and **asserting the output helpers**.

---

## Extract the handler

The cleanest pattern is to define the handler as an exported function, then pass it into `server.tool({...}, handler)`. This makes the handler a plain async function you can call from a test.

```typescript
// src/tools/greet.ts
import { text } from "mcp-use/server";
import { z } from "zod";

export const greetSchema = z.object({ name: z.string() });
export type GreetArgs = z.infer<typeof greetSchema>;

export async function greetHandler(args: GreetArgs, ctx: any) {
  await ctx.log("debug", `greeting ${args.name}`);
  return text(`Hello, ${args.name}!`);
}

// src/server.ts
server.tool({ name: "greet", schema: greetSchema }, greetHandler);
```

---

## Minimal test (Vitest)

```typescript
// src/tools/greet.test.ts
import { describe, it, expect, vi } from "vitest";
import { greetHandler } from "./greet";

function mockCtx() {
  return {
    log: vi.fn(async () => {}),
    reportProgress: vi.fn(async () => {}),
    client: { supportsApps: () => false, supportsSampling: () => false },
  };
}

describe("greet tool", () => {
  it("returns greeting text", async () => {
    const ctx = mockCtx();
    const result = await greetHandler({ name: "World" }, ctx);

    expect(result.content[0].type).toBe("text");
    expect(result.content[0].text).toBe("Hello, World!");
    expect(ctx.log).toHaveBeenCalledWith("debug", "greeting World");
  });
});
```

---

## Asserting output shapes

`text()`, `object()`, `widget()`, `binary()` all return `{ content: [...], structuredContent?, _meta? }`. Assert against the surface the host actually consumes.

```typescript
import { text, object } from "mcp-use/server";

// text()
const t = text("hi");
// { content: [{ type: "text", text: "hi" }] }
expect(t.content[0].text).toBe("hi");

// object() — produces both text (JSON) and structuredContent
const o = object({ score: 42 }, "Score: 42");
// { content: [{ type: "text", text: "Score: 42" }], structuredContent: { score: 42 } }
expect(o.structuredContent).toEqual({ score: 42 });
expect(o.content[0].text).toBe("Score: 42");
```

For tools that declare an `outputSchema`, assert that `structuredContent` matches; the host treats `structuredContent` as the canonical machine-readable surface.

---

## Mocking ctx surface area

`ctx` (the second argument to a tool handler) carries the per-call host context. A focused mock covers the methods your handler actually uses — don't over-mock.

| ctx method | Mock with | Notes |
|---|---|---|
| `ctx.log(level, msg, [name])` | `vi.fn(async () => {})` | Fire-and-forget; assert calls if logging is part of the contract |
| `ctx.reportProgress({ progress, total })` | `vi.fn(async () => {})` | Verify cadence by call count |
| `ctx.requestSampling(...)` | `vi.fn(async () => mockResponse)` | Stub the LLM's reply directly |
| `ctx.elicit(...)` | `vi.fn(async () => userInput)` | Stub the user's answer |
| `ctx.client.supportsApps()` | `() => true / false` | Drives widget vs text fallback |
| `ctx.client.supportsSampling()` | `() => true / false` | Drives gracefully-degrade paths |
| `ctx.session.id` | `"test-session"` | Only matters if the tool uses session ID for keying |

```typescript
function richMockCtx({ apps = false, sampling = false } = {}) {
  return {
    log: vi.fn(async () => {}),
    reportProgress: vi.fn(async () => {}),
    requestSampling: vi.fn(async () => ({ content: [{ type: "text", text: "stub" }] })),
    elicit: vi.fn(async () => ({ value: "stub" })),
    client: {
      supportsApps: () => apps,
      supportsSampling: () => sampling,
    },
    session: { id: "test-session" },
  };
}
```

---

## Testing branches that depend on the host

```typescript
it("returns widget when client supports apps", async () => {
  const ctx = richMockCtx({ apps: true });
  const result = await getWeatherHandler({ city: "Tokyo" }, ctx);
  expect(result.structuredContent).toBeDefined(); // widget path
});

it("falls back to text when client doesn't support apps", async () => {
  const ctx = richMockCtx({ apps: false });
  const result = await getWeatherHandler({ city: "Tokyo" }, ctx);
  expect(result.content[0].type).toBe("text");
  expect(result.structuredContent).toBeUndefined(); // text fallback
});
```

---

## Schema validation

Tool input is validated by the runtime via Zod before reaching the handler. To test schema correctness, validate directly:

```typescript
import { greetSchema } from "./greet";

it("rejects missing name", () => {
  expect(() => greetSchema.parse({})).toThrow();
});

it("accepts valid input", () => {
  expect(greetSchema.parse({ name: "Alice" })).toEqual({ name: "Alice" });
});
```

---

## Mocking external APIs

Keep tests deterministic. Mock fetch, axios, or whatever HTTP client the handler uses.

```typescript
import { vi } from "vitest";

global.fetch = vi.fn(async () => ({
  ok: true,
  json: async () => ({ tempC: 22 }),
})) as any;

it("calls weather API", async () => {
  const ctx = richMockCtx();
  const result = await getWeatherHandler({ city: "Tokyo" }, ctx);
  expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("Tokyo"));
});
```

---

## What NOT to unit test

| Skip | Why |
|---|---|
| The MCP server itself | Tested by the SDK; integration-test via curl or Inspector |
| JSON-RPC plumbing | Same |
| Transport layer | Same |
| `list_changed` notification firing | Verify in Inspector's Notifications pane, not in unit tests |

Unit tests cover handler logic. Integration tests (curl + Inspector) cover the wire.

---

## Test file layout

```text
src/
├── tools/
│   ├── greet.ts
│   ├── greet.test.ts
│   ├── get-weather.ts
│   └── get-weather.test.ts
└── server.ts
```

Co-locate `*.test.ts` next to handler files — Vitest and Jest pick them up automatically. CI runs them via `npm test`.
