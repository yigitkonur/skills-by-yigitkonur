# Recipe 01 — Weather Dashboard

**What it demonstrates:** server-side async data fetch, refresh button via `useCallTool`, theme-aware rendering, CSP for the image origin, skeleton loading.

## File layout

```
resources/weather-dashboard/
└── widget.tsx
src/tools/weather.ts
```

## Server tool — `src/tools/weather.ts`

```typescript
import { widget } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerWeatherTools(server: MCPServer) {
  server.tool(
    {
      name: "get-weather",
      description: "Get current weather conditions for a city",
      schema: z.object({
        city: z.string().describe("City name (e.g., 'San Francisco')"),
        units: z.enum(["metric", "imperial"]).default("metric").describe("Temperature units"),
      }),
      widget: {
        name: "weather-dashboard",
        invoking: "Fetching weather data...",
        invoked: "Weather loaded",
      },
    },
    async ({ city, units }) => {
      const apiKey = process.env.OPENWEATHER_API_KEY;
      const res = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=${units}&appid=${apiKey}`
      );
      const data = await res.json();

      return widget({
        props: {
          city: data.name,
          country: data.sys.country,
          temperature: Math.round(data.main.temp),
          feelsLike: Math.round(data.main.feels_like),
          humidity: data.main.humidity,
          windSpeed: data.wind.speed,
          conditions: data.weather[0].main,
          description: data.weather[0].description,
          icon: data.weather[0].icon,
          units,
        },
        message: `Weather in ${data.name}: ${Math.round(data.main.temp)}°${units === "metric" ? "C" : "F"}, ${data.weather[0].description}`,
      });
    }
  );
}
```

## Widget — `resources/weather-dashboard/widget.tsx`

```tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays current weather conditions with temperature, humidity, and wind data",
  props: z.object({
    city: z.string(),
    country: z.string(),
    temperature: z.number(),
    feelsLike: z.number(),
    humidity: z.number(),
    windSpeed: z.number(),
    conditions: z.string(),
    description: z.string(),
    icon: z.string(),
    units: z.enum(["metric", "imperial"]),
  }),
  metadata: {
    csp: {
      resourceDomains: ["https://openweathermap.org"],
    },
    prefersBorder: true,
  },
};

interface WeatherProps {
  city: string;
  country: string;
  temperature: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  conditions: string;
  description: string;
  icon: string;
  units: "metric" | "imperial";
}

function WeatherContent() {
  const { props, isPending, theme } = useWidget<WeatherProps>();
  const { callTool: refresh, isPending: refreshing } = useCallTool("get-weather");

  if (isPending) {
    return (
      <div className="animate-pulse p-6 space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const unitSymbol = props.units === "metric" ? "°C" : "°F";
  const windUnit = props.units === "metric" ? "m/s" : "mph";
  const isDark = theme === "dark";

  return (
    <div className={`p-6 rounded-lg ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold">{props.city}, {props.country}</h2>
          <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>{props.description}</p>
        </div>
        <button
          onClick={() => refresh({ city: props.city, units: props.units })}
          disabled={refreshing}
          className={`p-2 rounded-full ${refreshing ? "animate-spin" : ""} ${isDark ? "hover:bg-gray-800" : "hover:bg-gray-100"}`}
        >
          ↻
        </button>
      </div>

      <div className="flex items-center gap-4 my-4">
        <img
          src={`https://openweathermap.org/img/wn/${props.icon}@2x.png`}
          alt={props.conditions}
          className="w-16 h-16"
        />
        <span className="text-5xl font-light">{props.temperature}{unitSymbol}</span>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Feels Like</div>
          <div className="text-lg font-semibold">{props.feelsLike}{unitSymbol}</div>
        </div>
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Humidity</div>
          <div className="text-lg font-semibold">{props.humidity}%</div>
        </div>
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Wind</div>
          <div className="text-lg font-semibold">{props.windSpeed} {windUnit}</div>
        </div>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <WeatherContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| External API fetch | Server tool, behind `process.env.OPENWEATHER_API_KEY` — never the widget |
| CSP for image host | `widgetMetadata.metadata.csp.resourceDomains`; the OpenWeather API call stays server-side and needs no widget CSP |
| Refresh action | `useCallTool("get-weather")`, passes the same args back |
| Theme | `theme === "dark"` from `useWidget()`, applied via Tailwind classes |
| Skeleton | Matches the real layout — header, hero, three-card grid |
