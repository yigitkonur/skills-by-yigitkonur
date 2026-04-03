# Minimal Interactive Widget Pattern

Use this when you need the smallest end-to-end `mcp-use` app that proves the full loop:

- a widget-bound tool opens a React widget
- the widget keeps temporary form state locally
- the widget calls a plain MCP tool with `useCallTool()`
- shared business logic lives in `src/lib/`

This is the safest first slice for calculator-style widgets, forms, and simple follow-up UI.

## First build gate

Start from the scaffold:

```bash
npx create-mcp-use-app my-app --template mcp-apps --no-skills
cd my-app
npm install
npm run build
npx mcp-use generate-types
```

If the generated demo widget or demo tool fails to build on current dependencies, replace that demo before adding product code. Do not keep building on top of a broken scaffold.

## File layout

```text
my-app/
├── index.ts
├── src/
│   └── lib/
│       └── math.ts
├── resources/
│   └── calculator/
│       └── widget.tsx
├── package.json
└── tsconfig.json
```

## 1. Shared logic: `src/lib/math.ts`

Put server-owned business logic in `src/lib/`. When the root entrypoint imports it, use a Node ESM `.js` path from `index.ts`.

```typescript
export const operations = ["add", "subtract", "multiply"] as const;

export type Operation = (typeof operations)[number];

export function calculate(input: {
  left: number;
  right: number;
  operation: Operation;
}) {
  switch (input.operation) {
    case "add":
      return { value: input.left + input.right, symbol: "+" };
    case "subtract":
      return { value: input.left - input.right, symbol: "-" };
    case "multiply":
      return { value: input.left * input.right, symbol: "x" };
  }
}
```

## 2. Server entry: `index.ts`

The widget-bound tool opens the UI. The plain tool does the follow-up computation.

```typescript
import { MCPServer, object, text, widget } from "mcp-use/server";
import { z } from "zod";

import { calculate, operations } from "./src/lib/math.js";

const operationSchema = z.enum(operations);

const server = new MCPServer({
  name: "calculator-app",
  version: "1.0.0",
  description: "Minimal interactive calculator widget",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "show-calculator",
    description: "Open a calculator widget with editable inputs",
    schema: z.object({
      left: z.number().default(2).describe("First number"),
      right: z.number().default(3).describe("Second number"),
      operation: operationSchema.default("add").describe("Math operation"),
    }),
    widget: {
      name: "calculator",
      invoking: "Opening calculator...",
      invoked: "Calculator ready",
    },
  },
  async ({ left, right, operation }, ctx) => {
    const result = calculate({ left, right, operation });

    if (!ctx.client.supportsApps()) {
      return text(`${left} ${result.symbol} ${right} = ${result.value}`);
    }

    return widget({
      props: {
        left,
        right,
        operation,
        initialResult: result.value,
      },
      output: text(`${left} ${result.symbol} ${right} = ${result.value}`),
    });
  }
);

server.tool(
  {
    name: "calculate",
    description: "Calculate a result for the calculator widget",
    schema: z.object({
      left: z.number().describe("First number"),
      right: z.number().describe("Second number"),
      operation: operationSchema.describe("Math operation"),
    }),
    outputSchema: z.object({
      value: z.number(),
      symbol: z.string(),
    }),
  },
  async ({ left, right, operation }) => object(calculate({ left, right, operation }))
);

await server.listen();
```

## 3. Widget: `resources/calculator/widget.tsx`

The widget owns temporary form state. It never re-implements the math on the client; it asks the `calculate` tool for the current result.

```tsx
import { useEffect, useState } from "react";
import {
  McpUseProvider,
  useCallTool,
  useWidget,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

const operationSchema = z.enum(["add", "subtract", "multiply"]);
const propsSchema = z.object({
  left: z.number(),
  right: z.number(),
  operation: operationSchema,
  initialResult: z.number(),
});

type Props = z.infer<typeof propsSchema>;
type Operation = z.infer<typeof operationSchema>;
type Calculation = { value: number; symbol: string };

export const widgetMetadata: WidgetMetadata = {
  description: "Calculator form that edits inputs locally and calls a tool for the result",
  props: propsSchema,
  metadata: { prefersBorder: true },
};

function symbolFor(operation: Operation) {
  switch (operation) {
    case "add":
      return "+";
    case "subtract":
      return "-";
    case "multiply":
      return "x";
  }
}

function CalculatorContent() {
  const { props, isPending, theme } = useWidget<Props>();
  const { callToolAsync, error, isPending: isCalculating } = useCallTool("calculate");

  const [initialized, setInitialized] = useState(false);
  const [left, setLeft] = useState("0");
  const [right, setRight] = useState("0");
  const [operation, setOperation] = useState<Operation>("add");
  const [result, setResult] = useState<Calculation | null>(null);

  useEffect(() => {
    if (!initialized && !isPending) {
      setLeft(String(props.left));
      setRight(String(props.right));
      setOperation(props.operation);
      setResult({ value: props.initialResult, symbol: symbolFor(props.operation) });
      setInitialized(true);
    }
  }, [initialized, isPending, props.initialResult, props.left, props.operation, props.right]);

  if (isPending) {
    return <div className="animate-pulse p-4">Loading calculator...</div>;
  }

  const isDark = theme === "dark";

  const handleCalculate = async () => {
    const response = await callToolAsync({
      left: Number(left),
      right: Number(right),
      operation,
    });

    const next = response.structuredContent as Calculation | undefined;
    if (next) {
      setResult(next);
    }
  };

  const inputClass = `rounded border px-3 py-2 ${
    isDark
      ? "border-gray-700 bg-gray-800 text-white"
      : "border-gray-300 bg-white text-gray-900"
  }`;

  return (
    <div className={`space-y-4 p-4 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <input
          className={inputClass}
          type="number"
          value={left}
          onChange={(event) => setLeft(event.target.value)}
        />
        <select
          className={inputClass}
          value={operation}
          onChange={(event) => setOperation(event.target.value as Operation)}
        >
          <option value="add">+</option>
          <option value="subtract">-</option>
          <option value="multiply">x</option>
        </select>
        <input
          className={inputClass}
          type="number"
          value={right}
          onChange={(event) => setRight(event.target.value)}
        />
      </div>

      <button
        className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        disabled={isCalculating}
        onClick={handleCalculate}
      >
        {isCalculating ? "Calculating..." : "Calculate"}
      </button>

      {result && (
        <div className={`rounded border p-3 ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}>
          <div className="text-sm opacity-70">Result</div>
          <div className="text-xl font-semibold">
            {left} {result.symbol} {right} = {result.value}
          </div>
        </div>
      )}

      {error && <div className="text-sm text-red-500">{error.message}</div>}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <CalculatorContent />
    </McpUseProvider>
  );
}
```

## 4. Why this pattern is the right first slice

- The scaffold is verified before custom work starts.
- The business logic has one home: `src/lib/math.ts`.
- The widget proves `useWidget`, local state, `useCallTool`, and result rendering without adding auth, CSP, or deployment complexity too early.
- Non-widget clients still get a useful text result because the opening tool returns `output: text(...)`.

## 5. What to add next

- External API calls from the widget: add CSP in `widgetMetadata.metadata.csp`.
- Host-visible confirmations: use `sendFollowUpMessage()` only when the chat should show a new user turn.
- Persistent preferences: use `setState()` for widget-owned state, or a dedicated server tool for cross-conversation storage.
- Production verification: run `npx mcp-use dev`, open `/inspector`, and call `show-calculator`.

## Related references

- Scaffold and build gates: `references/guides/quick-start.md`
- Larger widget examples: `references/examples/widget-recipes.md`
- Tool and schema details: `references/guides/tools-and-schemas.md`
- Widget API details: `references/guides/widget-components.md`
