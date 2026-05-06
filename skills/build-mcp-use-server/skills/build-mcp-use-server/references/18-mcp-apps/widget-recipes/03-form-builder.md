# Recipe 03 — Multi-Step Form

**What it demonstrates:** multi-field form, `useCallTool` on submit (`callToolAsync`), client-side validation with errors, success/error states, step indicator.

Lifted from the source contact-form recipe. The form opens with `show-contact-form`, submits via `submit-contact-form`.

## File layout

```
resources/contact-form/
└── widget.tsx
src/tools/forms.ts
```

## Server tools — `src/tools/forms.ts`

```typescript
import { widget, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerFormTools(server: MCPServer) {
  server.tool(
    {
      name: "show-contact-form",
      description: "Show a contact form for user input",
      schema: z.object({
        topic: z.string().optional().describe("Pre-filled topic"),
      }),
      widget: {
        name: "contact-form",
        invoking: "Loading form...",
        invoked: "Form ready",
      },
    },
    async ({ topic }) => {
      return widget({ props: { topic: topic ?? "", departments: ["Sales", "Support", "Engineering", "Billing"] }, message: "Contact form is ready for input." });
    }
  );

  server.tool(
    {
      name: "submit-contact-form",
      description: "Submit a contact form",
      schema: z.object({
        name: z.string().min(1).describe("Contact name"),
        email: z.string().email().describe("Contact email"),
        department: z.string().describe("Target department"),
        message: z.string().min(10).describe("Message body"),
        priority: z.enum(["low", "medium", "high"]).default("medium").describe("Priority level"),
      }),
    },
    async ({ name, email, department, message, priority }) => {
      const ticketId = `TICKET-${Date.now().toString(36).toUpperCase()}`;
      return object({ ticketId, status: "submitted", message: `Thank you, ${name}. Your ${priority}-priority ticket ${ticketId} has been sent to ${department}.` });
    }
  );
}
```

## Widget — `resources/contact-form/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Multi-step contact form with validation and submission",
  props: z.object({ topic: z.string(), departments: z.array(z.string()) }),
  metadata: { prefersBorder: true },
};

interface FormProps {
  topic: string;
  departments: string[];
}

interface FormData {
  name: string;
  email: string;
  department: string;
  message: string;
  priority: "low" | "medium" | "high";
}

type FormStep = "info" | "message" | "review";

function FormContent() {
  const { props, isPending, theme } = useWidget<FormProps>();
  const { callToolAsync: submit, isPending: submitting } = useCallTool("submit-contact-form");

  const [step, setStep] = useState<FormStep>("info");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [formData, setFormData] = useState<FormData>({ name: "", email: "", department: props.departments?.[0] ?? "Support", message: props.topic ? `Regarding: ${props.topic}\n\n` : "", priority: "medium" });

  const isDark = theme === "dark";
  if (isPending) return <div className="animate-pulse p-6 h-48" />;

  const inputClass = `w-full px-3 py-2 rounded border ${isDark ? "bg-gray-800 border-gray-600 text-white" : "bg-white border-gray-300 text-gray-900"} focus:outline-none focus:ring-2 focus:ring-blue-500`;

  const validateStep = (s: FormStep): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};
    if (s === "info") {
      if (!formData.name.trim()) newErrors.name = "Name is required";
      if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) newErrors.email = "Valid email required";
    }
    if (s === "message") {
      if (formData.message.trim().length < 10) newErrors.message = "Message must be at least 10 characters";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    try {
      const res = await submit(formData);
      setResult(res.structuredContent as Record<string, unknown>);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    }
  };

  if (result) {
    return (
      <div className={`p-6 text-center ${isDark ? "bg-gray-900 text-white" : "bg-white"}`}>
        <h3 className="text-lg font-bold mb-2">Submitted Successfully</h3>
        <p className="mb-1">Ticket: <code className="font-mono">{String(result.ticketId)}</code></p>
        <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>{String(result.message)}</p>
      </div>
    );
  }

  const stepOrder: FormStep[] = ["info", "message", "review"];
  const stepDot = (s: FormStep, i: number) => {
    const idx = stepOrder.indexOf(step);
    if (step === s) return "bg-blue-500 text-white";
    return i < idx ? "bg-green-500 text-white" : isDark ? "bg-gray-700 text-gray-400" : "bg-gray-200 text-gray-500";
  };

  return (
    <div className={`p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex gap-2 mb-6">
        {stepOrder.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${stepDot(s, i)}`}>{i + 1}</div>
            {i < 2 && <div className={`w-8 h-0.5 ${isDark ? "bg-gray-700" : "bg-gray-300"}`} />}
          </div>
        ))}
      </div>

      {step === "info" && (
        <div className="space-y-4">
          {(["name", "email"] as const).map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium mb-1 capitalize">{field}</label>
              <input
                className={inputClass}
                type={field === "email" ? "email" : "text"}
                value={formData[field]}
                onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                placeholder={field === "email" ? "you@example.com" : "Your name"}
              />
              {errors[field] && <p className="text-red-500 text-xs mt-1">{errors[field]}</p>}
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium mb-1">Department</label>
            <select className={inputClass} value={formData.department} onChange={(e) => setFormData({ ...formData, department: e.target.value })}>
              {props.departments?.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <button onClick={() => validateStep("info") && setStep("message")} className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Next →</button>
        </div>
      )}

      {step === "message" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Message</label>
            <textarea className={`${inputClass} h-32`} value={formData.message} onChange={(e) => setFormData({ ...formData, message: e.target.value })} placeholder="Describe your issue..." />
            {errors.message && <p className="text-red-500 text-xs mt-1">{errors.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <div className="flex gap-2">
              {(["low", "medium", "high"] as const).map((p) => (
                <button key={p} onClick={() => setFormData({ ...formData, priority: p })} className={`flex-1 py-2 rounded capitalize ${formData.priority === p ? "bg-blue-500 text-white" : isDark ? "bg-gray-700" : "bg-gray-200"}`}>{p}</button>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep("info")} className={`flex-1 py-2 rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>← Back</button>
            <button onClick={() => validateStep("message") && setStep("review")} className="flex-1 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Review →</button>
          </div>
        </div>
      )}

      {step === "review" && (
        <div className="space-y-4">
          <div className={`p-4 rounded text-sm space-y-1 ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
            {(["name", "email", "department", "priority"] as const).map((k) => (
              <div key={k} className="flex gap-2">
                <span className={`w-20 capitalize ${isDark ? "text-gray-400" : "text-gray-500"}`}>{k}:</span>
                <span className="capitalize">{formData[k]}</span>
              </div>
            ))}
            <div className={`mt-2 ${isDark ? "text-gray-400" : "text-gray-500"}`}>Message:</div>
            <p className="whitespace-pre-wrap">{formData.message}</p>
          </div>
          {submitError && <p className="text-red-500 text-sm">{submitError}</p>}
          <div className="flex gap-2">
            <button onClick={() => setStep("message")} className={`flex-1 py-2 rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>← Edit</button>
            <button onClick={handleSubmit} disabled={submitting} className="flex-1 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50">{submitting ? "Submitting..." : "Submit ✓"}</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <FormContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Two tools, one widget | `show-*` opens with `widget()`, `submit-*` returns `object()` and is called from the form |
| Step state machine | `useState<FormStep>("info")` + `validateStep` gate transitions |
| Field-level validation | Local `errors` map, populated in `validateStep`, cleared on next render |
| Async submit | `callToolAsync(formData)` inside `handleSubmit`, with try/catch around server errors |
| Success view | Replace the form body when `result` is set; show ticket ID inline |
| Pre-fill from props | `props.topic` seeds the textarea on mount |
