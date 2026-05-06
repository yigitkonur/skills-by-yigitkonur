# Tool `widget` Config

The `widget` field on `server.tool()` links a tool to a widget and supplies the status text the host shows during/after the tool call.

## Shape

```typescript
server.tool(
  {
    name: string,
    description?: string,
    schema: ZodSchema,
    widget: {
      name: string;        // required — must match a widget in resources/
      invoking?: string;   // status while running
      invoked?: string;    // status after success
      widgetAccessible?: boolean;
      resultCanProduceWidget?: boolean;
    },
  },
  async (params, ctx) => widget({ ... })
);
```

## Field reference

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `string` | **Yes** | — | Widget identifier. Must match `resources/<name>/widget.tsx` directory or a `server.uiResource({ name: ... })` call. |
| `invoking` | `string` | No | `"Loading {name}..."` | Status text shown while the tool runs. Surfaces in the host UI and in ChatGPT/Inspector. |
| `invoked` | `string` | No | `"{name} ready"` | Status text shown after the tool completes successfully. |
| `widgetAccessible` | `boolean` | No | `true` | Maps to ChatGPT `openai/widgetAccessible`; lets widgets initiate tool calls. |
| `resultCanProduceWidget` | `boolean` | No | `true` | Maps to ChatGPT `openai/resultCanProduceWidget`. |

The defaults are auto-generated from `name`, so you can omit `invoking`/`invoked` for prototypes. Override them for production-quality copy.

## Example

```typescript
import { widget, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({ city: z.string().describe("City name") }),
    widget: {
      name: "weather-display",
      invoking: "Fetching weather data...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const data = await fetchWeather(city);
    return widget({
      props: { city, ...data },
      output: text(`Current weather in ${city}: ${data.conditions}, ${data.temperature}°C`),
    });
  }
);
```

## The `name` must match exactly

mcp-use looks up `widget.name` against:
1. The set of `resources/<dir>/widget.tsx` directories discovered at startup.
2. Names registered via explicit `server.uiResource({ name })` calls.

A typo here is the most common cause of a "widget renders blank" error. The Inspector surfaces this — see the troubleshooting cluster.

## Status text — invoking and invoked

These map to host UI signals:

| Host | invoking shown as | invoked shown as |
|---|---|---|
| ChatGPT | Inline status pill while tool runs | Final status text after success |
| MCP Inspector | Loading banner above widget | Status badge after render |
| Claude Desktop | Spinner caption | Persisted status after completion |

Keep them short and progress-y. `"Loading..."` is a smell — say what's loading.

## When NOT to set `widget`

Don't set `widget` on a tool that returns plain `text()` or `object()`. The host will allocate iframe space expecting a widget result and show "loading" forever. The widget config is a contract: by setting it, you promise the handler will return `widget({...})`.

If a tool sometimes returns a widget and sometimes plain text (capability fallback — see `../05-host-capability-detection.md`), still set `widget` — the helper handles fallback through the `output` channel.

## Related

- The `widget()` helper that the handler must return: `01-widget-helper.md`.
- Widget filesystem convention: `07-resources-folder-conventions.md`.
- Standalone-tool widget registration via `exposeAsTool`: `02-uiresource-registration.md`.
