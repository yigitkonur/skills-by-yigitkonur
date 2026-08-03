# Prompt Engineering Guidance

*Read this when crafting prompt content, deciding between prompts and tools, or naming your prompts.*

Prompts are the LLM-facing surface. Treat them like API contracts: small, named, parameterized, and stable.

---

## Prompt vs tool

| LLM should | Use |
|---|---|
| **Think** in a particular way (reason, analyze, decide) | Prompt (user-invoked instruction) |
| **Do** something with side effects (call an API, write data) | Tool (LLM-driven execution) |
| **Read** static or slowly-changing data | Resource (pre-fetched context) |

Prompts shape *how the model reasons*. Tools execute deterministically. Resources supply context. If your "prompt" is fetching data and acting on it, you want a tool — tools take parameters, execute code, and return structured results.

---

## Best practices

1. **Reusable templates only.** If a prompt runs once, don't register it — paste the text into a tool description instead.

2. **Minimal arguments.** Each argument adds friction to the picker UI. Aim for 3–5 max; collapse related toggles into a single enum.

3. **Always `.describe()` arguments.** This is the only label users see in the picker when browsing arguments.

4. **Use enums for choices.** Free strings invite typos; enums document the valid set and guide the model.

5. **Reference resources by URI.** Mention `users://{id}`, `config://app` in prompt text — clients fetch them and include in context.

6. **Multiple messages for non-trivial flows.** Use `{ messages: [...] }` with several `user`/`assistant` messages instead of cramming everything into one giant string. There is no `"system"` role — put system-style framing in the first `user` message (see `03-prompt-templates.md`).

7. **Prompt arguments, not branches.** If your handler has if/else picking between three different texts, that's three different prompts.

---

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| One prompt with 12 optional arguments | Split into 2–3 focused prompts |
| Free-text `style: z.string()` | Use `style: z.enum(["concise", "detailed"])` |
| Prompt that fetches data and writes back | That should be a tool |
| Prompt behavior changes based on time | Move branching into a tool; prompts stay static |
| Resource content baked into prompt as giant string | Reference the resource URI; let the client fetch it |
| Prompt named `do-thing` with no description | Always supply `description` — pickers depend on it |
| Schema arguments without `.describe()` | Add `.describe(...)` to every field |

---

## Few-shot examples

Embed examples in system content. Keep them short and structurally identical to expected output:

```typescript
server.prompt(
  {
    name: "categorize-issue",
    description: "Categorize a GitHub issue title",
    schema: z.object({ title: z.string() }),
  },
  async ({ title }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Classify this issue title as one of: bug | feature | chore | question.

Examples:
- "App crashes on launch" -> bug
- "Add dark mode" -> feature
- "Update README typos" -> chore
- "How do I configure X?" -> question

Issue: ${title}
Respond with the single label only.`,
      },
    }],
  })
);
```

---

## Multi-turn conversation seeds

Use multi-message returns to set the *shape* of the conversation, not to pre-answer the question:

```typescript
server.prompt(
  {
    name: "debug-session",
    description: "Start a debugging workflow",
    schema: z.object({ error: z.string() }),
  },
  async ({ error }, ctx) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Error: ${error}\n\nLead with the most likely cause, ranked. Then ask one diagnostic question.`,
        },
      },
    ],
  })
);
```

The seeded structure acts as a commitment — the model continues in that shape.

---

## Naming

Use `verb-object` — `code-review`, `analyze-config`, `debug-session`. Same convention as tools. The prompt name appears in client UI; users scan by the verb.

| Poor | Good |
|---|---|
| `prompt1` | `analyze-config` |
| `helper` | `debug-session` |
| `do_review_code` | `code-review` |
| `MyAwesomePrompt` | `code-review` |

---

## Validation order

The server validates arguments against the schema **before** calling your handler. You never revalidate inside the handler — invalid input is rejected upstream.

If validation succeeds but the resolved values are semantically invalid (e.g., user not found, project archived), throw from the handler. The client surfaces the error.

---

## Performance

Prompts are cheap — they return text. Don't fetch data inside the prompt handler unless you genuinely need it for the seed. Instead, reference resource URIs in the prompt text and let the client fetch them lazily:

```typescript
// Wasteful — refetches every time the prompt is opened
async ({ userId }, ctx) => {
  const user = await db.getUser(userId); // unnecessary!
  return {
    messages: [{
      role: "user",
      content: { type: "text", text: `Analyze user: ${JSON.stringify(user)}` },
    }],
  };
}

// Lean — client fetches the resource only if needed
async ({ userId }, ctx) => ({
  messages: [{
    role: "user",
    content: { type: "text", text: `Analyze the user at users://${userId}.` },
  }],
});
```
