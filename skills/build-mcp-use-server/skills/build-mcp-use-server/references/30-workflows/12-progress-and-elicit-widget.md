# Workflow: Progress Widget (Polling Pattern)

**Goal:** kick off a long-running job from a tool, return a widget *immediately* with a job id, and let the widget poll a custom HTTP endpoint to show live progress. The tool also calls `ctx.reportProgress` so non-widget MCP clients get the same updates. Modeled on `mcp-use/mcp-progress-demo`.

## Prerequisites

- mcp-use 1.26.0 or newer.

## Layout

```
progress-mcp/
├── package.json
├── index.ts
└── resources/
    └── progress-view/
        └── widget.tsx
```

## `index.ts`

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

interface Job {
  dataset: string;
  totalSteps: number;
  steps: { step: number; name: string; status: string; duration: number }[];
  status: "running" | "complete" | "error";
}

const jobs = new Map<string, Job>();

const STEP_NAMES = [
  "Validating",
  "Parsing",
  "Transforming",
  "Analyzing",
  "Finalizing",
];

const server = new MCPServer({
  name: "progress-demo",
  version: "1.0.0",
  description: "Long-running tool with widget polling and MCP progress",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

// ── Custom polling endpoint that the widget hits ────────────────────────────

server.get("/api/progress/:jobId", async (c) => {
  const job = jobs.get(c.req.param("jobId"));
  if (!job) return c.json({ error: "not found" }, 404);
  return c.json(job, 200, { "Cache-Control": "no-cache" });
});

// ── Tool: kicks off the work, returns immediately ──────────────────────────

server.tool(
  {
    name: "process-data",
    description:
      "Run a multi-step pipeline. Returns immediately with a jobId; the widget " +
      "polls /api/progress/:jobId for live updates.",
    schema: z.object({
      dataset: z.string().describe("Dataset name to process"),
      steps: z.number().int().min(2).max(STEP_NAMES.length).default(5),
    }),
    widget: {
      name: "progress-view",
      invoking: "Starting pipeline...",
      invoked: "Pipeline started",
    },
  },
  async ({ dataset, steps }, ctx) => {
    const id = crypto.randomUUID();
    const job: Job = { dataset, totalSteps: steps, steps: [], status: "running" };
    jobs.set(id, job);

    // Run in the background — DO NOT await.
    (async () => {
      for (let i = 0; i < steps; i++) {
        const name = STEP_NAMES[i] ?? `Step ${i + 1}`;
        const ms = 800 + Math.random() * 1200;
        await new Promise((r) => setTimeout(r, ms));
        job.steps.push({
          step: i + 1,
          name,
          status: "complete",
          duration: Math.round(ms),
        });
        // Also send via the MCP progress channel for non-widget clients.
        try {
          await ctx.reportProgress?.(i + 1, steps, `${name} complete`);
        } catch {
          /* progressToken absent — fine */
        }
      }
      job.status = "complete";
      // Drop the job after 5 minutes.
      setTimeout(() => jobs.delete(id), 5 * 60 * 1000);
    })();

    return widget({
      props: { jobId: id, dataset, totalSteps: steps, status: "running" },
      output: text(`Started "${dataset}" (${steps} steps). Job ${id}`),
    });
  }
);

server.listen();
```

## `resources/progress-view/widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { useEffect, useState } from "react";
import { z } from "zod";

interface JobState {
  dataset: string;
  totalSteps: number;
  steps: { step: number; name: string; status: string; duration: number }[];
  status: "running" | "complete" | "error";
}

interface Props {
  jobId: string;
  dataset: string;
  totalSteps: number;
  status: string;
}

export const widgetMetadata: WidgetMetadata = {
  description: "Live multi-step progress, polled via /api/progress/:jobId",
  props: z.object({
    jobId: z.string(),
    dataset: z.string(),
    totalSteps: z.number(),
    status: z.string(),
  }),
  metadata: { prefersBorder: true },
};

function ProgressInner() {
  const { props, mcp_url } = useWidget<Props>();
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll until complete. mcp_url points back at this MCP server when available.
  useEffect(() => {
    if (!props?.jobId) return;
    let stopped = false;
    const base = mcp_url ?? "";

    async function poll() {
      if (stopped) return;
      try {
        const res = await fetch(`${base}/api/progress/${props.jobId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const next = (await res.json()) as JobState;
        if (stopped) return;
        setJob(next);
        if (next.status !== "running") stopped = true;
      } catch (e) {
        if (!stopped) setError((e as Error).message);
      }
    }
    poll();
    const interval = setInterval(poll, 600);
    return () => {
      stopped = true;
      clearInterval(interval);
    };
  }, [props?.jobId, mcp_url]);

  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  const completed = job?.steps.length ?? 0;
  const total = props?.totalSteps ?? 0;
  const pct = total ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="p-4 bg-white dark:bg-gray-950">
      <div className="mb-3">
        <div className="text-sm text-gray-500">{props?.dataset}</div>
        <div className="text-xs text-gray-400">job {props?.jobId.slice(0, 8)}</div>
      </div>
      <div className="h-2 rounded bg-gray-200 dark:bg-gray-800 overflow-hidden">
        <div
          className={`h-full transition-all ${
            job?.status === "complete" ? "bg-emerald-500" : "bg-blue-500"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {completed} / {total} steps · {job?.status ?? "starting"}
      </div>
      <ul className="mt-3 space-y-1 text-sm">
        {job?.steps.map((s) => (
          <li key={s.step} className="flex justify-between">
            <span>
              {s.step}. {s.name}
            </span>
            <span className="text-gray-400 text-xs">{s.duration}ms</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ProgressView() {
  return (
    <McpUseProvider autoSize>
      <ProgressInner />
    </McpUseProvider>
  );
}
```

## Run: `npm install && npm run dev`

## Test

1. Open http://localhost:3000/inspector.
2. Call `process-data` with `{ "dataset": "users", "steps": 5 }`.
3. The widget appears immediately and the bar fills as steps complete.
4. The Inspector's notifications panel will also show `notifications/progress` if you passed a `progressToken` in `_meta`.

## Pattern recap

| Concern | Choice |
|---|---|
| Long-running work | Run in background via fire-and-forget IIFE |
| Job state | Module-scope `Map` (per-process). Use Redis for multi-pod |
| Widget update | Custom HTTP endpoint + polling via `mcp_url` |
| Non-widget clients | `ctx.reportProgress` works in parallel |
| Cleanup | `setTimeout` to drop the job after 5 min |

## See also

- Canonical: `../31-canonical-examples/05-mcp-progress-demo.md`
- Notifications: `../14-notifications/`
- SSE-based push instead of polling: `08-real-time-stock-ticker.md`
