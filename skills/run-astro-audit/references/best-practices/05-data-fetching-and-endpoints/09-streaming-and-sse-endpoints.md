# Return ReadableStream Responses for Server-Sent Events and Real-Time Feeds

> **Context:** Data Fetching & Endpoints | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Modern applications increasingly require streaming responses—such as AI/LLM token streaming, live progress updates, or Server-Sent Events (SSE). Buffering the entire payload before returning `Response.json(...)` introduces severe user-perceived latency and can exceed memory limits on serverless runtimes (Cloudflare Workers, Netlify Functions). Astro endpoints support the standard Web API `ReadableStream`, allowing bytes to be flushed incrementally to the client with low memory overhead.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers often use the Vercel AI SDK (`toDataStreamResponse`) or custom wrapper streams. In Astro, you construct a standard Web API `ReadableStream` directly. No specialized external libraries are required; standard browser `TextEncoder` and standard `new Response(stream, { headers })` work natively across all supported Astro SSR adapters.

## 3. Common Mistakes & Anti-Patterns

Buffering streaming chunks in an array instead of streaming through a `ReadableStream`.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/stream.ts
import type { APIRoute } from 'astro'
export const prerender = false

// ❌ Buffers everything in server memory before sending response:
export const GET: APIRoute = async () => {
  const chunks: string[] = []
  for await (const chunk of upstreamAiStream()) {
    chunks.push(chunk) // Stalls client until complete!
  }
  return Response.json({ result: chunks.join('') })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/stream.ts
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async () => {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      try {
        for (let i = 1; i <= 5; i++) {
          const payload = `data: ${JSON.stringify({ tick: i, time: Date.now() })}\n\n`
          controller.enqueue(encoder.encode(payload))
          await new Promise((r) => setTimeout(r, 500))
        }
        controller.close()
      } catch (err) {
        controller.error(err)
      }
    },
  })

  return new Response(stream, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  })
}
```

## 4. Verification & Audit

Verify streaming delivery via curl without response buffering:

```bash
# --no-buffer ensures curl prints each chunk as it arrives
curl -N -i http://localhost:4321/api/stream
```

You should observe incremental chunks arriving in the terminal every 500ms rather than a single delayed dump.
