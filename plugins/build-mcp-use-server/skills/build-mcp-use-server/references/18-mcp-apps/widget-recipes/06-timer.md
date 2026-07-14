# Recipe 06 — Countdown Timer

**What it demonstrates:** local interval state, cleanup on unmount, async tool callback when the timer reaches zero.

Synthesized example. Shows how to combine local React state (the ticking display) with an async server tool call once the local timer fires — without any state ever touching `setState`/host.

## File layout

```
resources/timer/
└── widget.tsx
src/tools/timer.ts
```

## Server tools — `src/tools/timer.ts`

```typescript
import { widget, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerTimerTools(server: MCPServer) {
  server.tool(
    {
      name: "start-timer",
      description: "Start a countdown timer for the given number of seconds",
      schema: z.object({
        seconds: z.number().int().min(1).max(3600).describe("How many seconds to count down"),
        label: z.string().default("Timer").describe("Label shown on the timer"),
      }),
      widget: {
        name: "timer",
        invoking: "Starting timer...",
        invoked: "Timer started",
      },
    },
    async ({ seconds, label }) => {
      return widget({
        props: { seconds, label, startedAt: Date.now() },
        message: `Started a ${seconds}s timer "${label}".`,
      });
    }
  );

  server.tool(
    {
      name: "timer-finished",
      description: "Notify that a timer reached zero",
      schema: z.object({
        label: z.string().describe("Label of the timer that finished"),
        seconds: z.number().describe("Original duration in seconds"),
      }),
    },
    async ({ label, seconds }) => {
      return object({
        label,
        seconds,
        finishedAt: new Date().toISOString(),
        message: `Timer "${label}" finished after ${seconds}s.`,
      });
    }
  );
}
```

## Widget — `resources/timer/widget.tsx`

```tsx
import { useEffect, useRef, useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Live countdown timer with finish callback to the server",
  props: z.object({
    seconds: z.number(),
    label: z.string(),
    startedAt: z.number(),
  }),
  metadata: { prefersBorder: true },
};

interface TimerProps {
  seconds: number;
  label: string;
  startedAt: number;
}

function pad(n: number) {
  return n.toString().padStart(2, "0");
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${pad(m)}:${pad(sec)}`;
}

function TimerContent() {
  const { props, isPending, theme } = useWidget<TimerProps>();
  const { callToolAsync: notifyFinished } = useCallTool("timer-finished");

  const [remaining, setRemaining] = useState<number>(props.seconds ?? 0);
  const [paused, setPaused] = useState(false);
  const firedRef = useRef(false);
  const isDark = theme === "dark";

  // Drive the countdown from a single 1Hz interval. Cleanup on unmount.
  useEffect(() => {
    if (isPending || paused) return;
    const id = setInterval(() => {
      setRemaining((r) => Math.max(0, r - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [isPending, paused]);

  // When the timer fires zero, call the server tool exactly once.
  useEffect(() => {
    if (remaining === 0 && !firedRef.current && !isPending) {
      firedRef.current = true;
      notifyFinished({ label: props.label, seconds: props.seconds }).catch(() => {
        // Reset so user can retry by pressing reset
        firedRef.current = false;
      });
    }
  }, [remaining, isPending, props.label, props.seconds, notifyFinished]);

  if (isPending) {
    return (
      <div className="p-6 animate-pulse">
        <div className={`h-16 w-32 rounded mx-auto ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
      </div>
    );
  }

  const reset = () => {
    setRemaining(props.seconds);
    firedRef.current = false;
    setPaused(false);
  };

  const progress = props.seconds === 0 ? 0 : (1 - remaining / props.seconds) * 100;
  const finished = remaining === 0;

  return (
    <div className={`p-6 text-center ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <p className={`text-sm mb-2 ${isDark ? "text-gray-400" : "text-gray-500"}`}>{props.label}</p>
      <p className={`text-6xl font-mono font-light tabular-nums ${finished ? "text-red-500" : ""}`}>
        {formatTime(remaining)}
      </p>

      <div className={`mt-4 h-2 rounded-full overflow-hidden ${isDark ? "bg-gray-800" : "bg-gray-200"}`}>
        <div
          className={`h-full transition-all duration-1000 ${finished ? "bg-red-500" : "bg-blue-500"}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-4 flex gap-2 justify-center">
        {!finished && (
          <button
            onClick={() => setPaused((p) => !p)}
            className={`px-4 py-2 rounded text-sm ${isDark ? "bg-gray-800" : "bg-gray-100"}`}
          >
            {paused ? "Resume" : "Pause"}
          </button>
        )}
        <button
          onClick={reset}
          className="px-4 py-2 rounded text-sm bg-blue-500 text-white hover:bg-blue-600"
        >
          Reset
        </button>
      </div>

      {finished && (
        <p className={`mt-3 text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
          Done. The server has been notified.
        </p>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <TimerContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Local interval ticker | `useEffect` setting `setInterval`; **always** `clearInterval` in the cleanup |
| Don't tick during `isPending` | `if (isPending || paused) return;` inside the effect |
| One-shot async callback | `firedRef = useRef(false)` guards a single `callToolAsync` even if effect re-runs |
| Reset on user action | Resets `remaining` and clears `firedRef` so the timer is reusable |
| `tabular-nums` | Stops layout shift as digits change |
| No `setState` | This timer is ephemeral — nothing persists to the host |
