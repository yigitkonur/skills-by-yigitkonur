# Recipe 08 — Conversational Chatbot Widget

**What it demonstrates:** persistent chat history via `setState`, follow-up messages threaded through `sendFollowUpMessage`, server tool that hands back assistant replies.

Synthesized example. The widget is a side-panel companion: each user message goes through a server tool that produces an assistant turn; the LLM in the host chat is invited to take over via `sendFollowUpMessage` for deeper questions.

## File layout

```
resources/chatbot/
└── widget.tsx
src/tools/chatbot.ts
```

## Server tools — `src/tools/chatbot.ts`

```typescript
import { widget, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

const messageSchema = z.object({
  id: z.string(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  ts: z.number(),
});

export function registerChatbotTools(server: MCPServer) {
  server.tool(
    {
      name: "open-chatbot",
      description: "Open a focused chatbot widget for a given topic",
      schema: z.object({
        topic: z.string().describe("Subject the chatbot should help with"),
      }),
      widget: {
        name: "chatbot",
        invoking: "Opening chatbot...",
        invoked: "Chatbot ready",
      },
    },
    async ({ topic }) => {
      const greeting = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        content: `Hi! I'm focused on "${topic}". Ask me anything — or use "Hand off to AI" to escalate to the main chat.`,
        ts: Date.now(),
      };
      return widget({
        props: { topic, history: [greeting] },
        message: `Chatbot on "${topic}" is ready.`,
      });
    }
  );

  server.tool(
    {
      name: "chatbot-reply",
      description: "Generate a chatbot reply for a single user message",
      schema: z.object({
        topic: z.string(),
        userMessage: z.string().min(1),
      }),
    },
    async ({ topic, userMessage }) => {
      // Replace with a real model call. Keep the reply short to keep the widget snappy.
      const reply = `On "${topic}": ${userMessage.length > 60 ? "That's a deep one — try the hand-off button." : "Here's a quick answer based on what I know."}`;
      return object({
        message: {
          id: crypto.randomUUID(),
          role: "assistant",
          content: reply,
          ts: Date.now(),
        },
      });
    }
  );

  // Make message schema discoverable for resource consumers
  void messageSchema;
}
```

## Widget — `resources/chatbot/widget.tsx`

```tsx
import { useEffect, useRef, useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Topic-focused chatbot with persistent history and AI hand-off",
  props: z.object({
    topic: z.string(),
    history: z.array(z.object({
      id: z.string(),
      role: z.enum(["user", "assistant", "system"]),
      content: z.string(),
      ts: z.number(),
    })),
  }),
  metadata: { prefersBorder: true },
};

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  ts: number;
}

interface ChatProps {
  topic: string;
  history: ChatMessage[];
}

interface ChatState {
  history: ChatMessage[];
}

function ChatbotContent() {
  const { props, isPending, theme, state, setState, sendFollowUpMessage } =
    useWidget<ChatProps, ChatState>();
  const { callToolAsync: reply, isPending: replying } = useCallTool("chatbot-reply");

  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const isDark = theme === "dark";

  const history = state?.history ?? props.history ?? [];

  // Scroll to the bottom whenever the history grows
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history.length]);

  if (isPending) {
    return (
      <div className="p-6 animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`h-10 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        ))}
      </div>
    );
  }

  const send = async () => {
    const text = draft.trim();
    if (!text || replying) return;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text, ts: Date.now() };
    const nextHistory = [...history, userMsg];
    await setState({ history: nextHistory });
    setDraft("");

    try {
      const res = await reply({ topic: props.topic, userMessage: text });
      await setState({ history: [...nextHistory, (res.structuredContent as { message: ChatMessage }).message] });
    } catch (err) {
      await setState({ history: [...nextHistory, {
        id: crypto.randomUUID(),
        role: "system",
        content: err instanceof Error ? err.message : "Reply failed",
        ts: Date.now(),
      }] });
    }
  };

  const handoff = () => {
    const last = [...history].reverse().find((m) => m.role === "user");
    const prefix = `Continue the chatbot conversation in the main thread. Topic: "${props.topic}".`;
    sendFollowUpMessage(last ? `${prefix} Last user question: "${last.content}".` : prefix);
  };

  const bubble = (m: ChatMessage) =>
    m.role === "user"
      ? "bg-blue-500 text-white"
      : m.role === "system"
      ? "bg-red-500/20 text-red-500"
      : isDark ? "bg-gray-800" : "bg-gray-100";

  return (
    <div className={`flex flex-col h-96 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className={`px-4 py-2 border-b flex justify-between items-center ${isDark ? "border-gray-800" : "border-gray-200"}`}>
        <h2 className="text-sm font-bold">Chatbot — {props.topic}</h2>
        <button onClick={handoff} className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600">
          Hand off to AI →
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {history.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${bubble(m)}`}>
              {m.content}
            </div>
          </div>
        ))}
        {replying && (
          <div className={`px-3 py-2 rounded-lg text-sm animate-pulse w-fit ${isDark ? "bg-gray-800" : "bg-gray-100"}`}>...</div>
        )}
      </div>

      <div className={`p-3 border-t flex gap-2 ${isDark ? "border-gray-800" : "border-gray-200"}`}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Type a message..."
          className={`flex-1 px-3 py-2 rounded border text-sm ${isDark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-300"}`}
        />
        <button onClick={send} disabled={replying || !draft.trim()} className="px-3 py-2 bg-blue-500 text-white rounded text-sm disabled:opacity-50">
          Send
        </button>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <ChatbotContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Persistent history | `setState({ history })` after every user/assistant turn |
| Optimistic user message | `setState` runs before `callToolAsync` so the user sees their message immediately |
| Server-generated assistant turn | `chatbot-reply` returns `object({ message })`; widget appends it to history |
| Hand-off to main chat | `sendFollowUpMessage` quotes the last user message so the host LLM can take over with context |
| Errors as system messages | Failed `reply()` becomes a `role: "system"` entry in history rather than a popup |
| Auto-scroll | `useEffect([history.length])` scrolls a fixed-height pane to the bottom |
| `state ?? props` | First render reads `props.history` (greeting); later renders read accumulated `state.history` |
