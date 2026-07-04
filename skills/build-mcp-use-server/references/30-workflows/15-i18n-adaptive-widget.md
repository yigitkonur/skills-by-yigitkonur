# Workflow: i18n / Adaptive Widget

**Goal:** build a widget that reads host-supplied client context — locale, timezone, max width/height, safe-area insets, user agent — and adapts both layout (column count) and formatting (Intl.NumberFormat, Intl.DateTimeFormat). The server adds a `detect-caller` tool that returns the same context as JSON for non-widget clients. Modeled on `mcp-use/mcp-i18n-adaptive`.

## Prerequisites

- mcp-use 1.26.0 or newer.

## Layout

```
i18n-mcp/
├── package.json
├── index.ts
└── resources/
    └── context-display/
        ├── widget.tsx
        └── types.ts
```

## `index.ts`

```typescript
import { MCPServer, text, widget, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "i18n-adaptive",
  version: "1.0.0",
  description: "Locale, timezone, layout constraints, device detection",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "show-context",
    description:
      "Display the host context inspector — locale, timezone, layout, device, " +
      "and adaptive number/date formatting.",
    schema: z.object({}),
    widget: {
      name: "context-display",
      invoking: "Loading context…",
      invoked: "Context ready",
    },
  },
  async () => {
    return widget({
      props: {
        greeting: "Hello!",
        timestamp: new Date().toISOString(),
        sampleNumbers: [1234.56, 9876543.21, 0.005],
        sampleDates: [
          new Date().toISOString(),
          new Date(Date.now() - 86_400_000).toISOString(),
        ],
      },
      output: text("Context display loaded"),
    });
  }
);

server.tool(
  {
    name: "detect-caller",
    description:
      "Return the calling client's context — userId, conversationId, locale, " +
      "location, client name and version. Useful for non-widget MCP clients.",
    schema: z.object({}),
  },
  async (_, ctx) => {
    const user = ctx.client.user();
    const info = ctx.client.info();
    return object({
      userId: user?.subject ?? null,
      conversationId: user?.conversationId ?? null,
      locale: user?.locale ?? null,
      location: user?.location ?? null,
      client: {
        name: info?.name ?? "unknown",
        version: info?.version ?? "unknown",
      },
    });
  }
);

server.listen();
```

## `resources/context-display/types.ts`

```typescript
import { z } from "zod";

export const propSchema = z.object({
  greeting: z.string(),
  timestamp: z.string(),
  sampleNumbers: z.array(z.number()),
  sampleDates: z.array(z.string()),
});

export type ContextDisplayProps = z.infer<typeof propSchema>;
```

## `resources/context-display/widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { useMemo, type ReactNode } from "react";
import { propSchema, type ContextDisplayProps } from "./types";

export const widgetMetadata: WidgetMetadata = {
  description: "Host context inspector — locale, timezone, layout, device",
  props: propSchema,
  exposeAsTool: false,
  metadata: { prefersBorder: true },
};

function ContextDisplay() {
  const {
    props,
    isPending,
    locale,
    timeZone,
    userAgent,
    safeArea,
    maxWidth,
    maxHeight,
    hostInfo,
    theme,
  } = useWidget<ContextDisplayProps>();

  const cols = useMemo(() => {
    if (!maxWidth || maxWidth < 400) return 1;
    if (maxWidth < 800) return 2;
    return 3;
  }, [maxWidth]);

  const formattedNumbers = useMemo(() => {
    const values = props.sampleNumbers ?? [];
    try {
      const fmt = new Intl.NumberFormat(locale || undefined);
      return values.map((n) => ({ raw: n, formatted: fmt.format(n) }));
    } catch {
      return values.map((n) => ({ raw: n, formatted: String(n) }));
    }
  }, [props.sampleNumbers, locale]);

  const formattedDates = useMemo(() => {
    const values = props.sampleDates ?? [];
    try {
      const fmt = new Intl.DateTimeFormat(locale || undefined, {
        dateStyle: "full",
        timeStyle: "long",
        timeZone: timeZone || undefined,
      });
      return values.map((iso) => ({ raw: iso, formatted: fmt.format(new Date(iso)) }));
    } catch {
      return values.map((iso) => ({ raw: iso, formatted: iso }));
    }
  }, [props.sampleDates, locale, timeZone]);

  if (isPending) return <div className="p-4 text-sm text-gray-500">Detecting context...</div>;

  const device = userAgent?.device?.type ?? "unknown";
  const insets = safeArea?.insets ?? { top: 0, right: 0, bottom: 0, left: 0 };

  return (
    <div
      className="bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
      style={{
        paddingTop: insets.top,
        paddingRight: insets.right,
        paddingBottom: insets.bottom,
        paddingLeft: insets.left,
      }}
    >
      <div
        className="p-4 grid gap-3"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0,1fr))` }}
      >
        <Card title="Identity">
          <KV k="locale" v={locale ?? "—"} />
          <KV k="timezone" v={timeZone ?? "—"} />
          <KV k="device" v={device} />
        </Card>
        <Card title="Layout">
          <KV k="maxWidth" v={`${maxWidth ?? "—"}px`} />
          <KV k="theme" v={theme ?? "light"} />
          <KV k="cols" v={String(cols)} />
        </Card>
        <Card title="Host">
          <KV k="name" v={hostInfo?.name ?? "—"} />
          <KV k="version" v={hostInfo?.version ?? "—"} />
        </Card>
        <Card title="Numbers (Intl)">
          {formattedNumbers.map((n) => <KV key={n.raw} k={String(n.raw)} v={n.formatted} />)}
        </Card>
        <Card title="Dates (Intl)">
          {formattedDates.map((d) => <KV key={d.raw} k={d.raw.slice(0, 10)} v={d.formatted} />)}
        </Card>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded border border-gray-200 dark:border-gray-700 p-3">
      <div className="text-xs uppercase tracking-wider text-gray-500 mb-2">{title}</div>
      {children}
    </div>
  );
}

function KV({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="flex justify-between text-xs py-0.5">
      <span className="text-gray-500">{k}</span>
      <span className="font-mono truncate">{v}</span>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <ContextDisplay />
    </McpUseProvider>
  );
}
```

## Run: `npm install && npm run dev`

## Test and adaptation fields

1. Resize the Inspector; column count and safe-area padding update.
2. Switch locale settings; number and date formats follow.
3. Call `detect-caller` from a non-widget client to confirm server-side parity.

Use `locale` and `timeZone` for `Intl`, `userAgent.device.type` for coarse layout, `safeArea.insets` for padding, `maxWidth` / `maxHeight` for responsive grids, `theme` for visual variants, and `hostInfo` for client identity.

## See also

- Canonical: `../31-canonical-examples/08-mcp-i18n-adaptive.md`
- Client introspection reference: `../16-client-introspection/`
- Widget metadata reference: `../18-mcp-apps/widget-react/`
