# Prompt Engineering

Prompts are the LLM-facing surface. Treat them like API contracts: small, named, parameterized, and stable.

## Prompt vs tool

| You want the LLM to | Use |
|---|---|
| **Do** something with side effects | Tool |
| **Read** data | Resource |
| **Think** in a particular way | Prompt |

Prompts shape *how the model reasons*. Tools execute. Resources supply context. If your "prompt" is fetching data and acting on it, you actually want a tool that takes the same arguments and returns a structured result.

## Best practices

1. **Reusable templates only.** If a prompt only ever runs once, it doesn't need to exist — paste the text into your usage instead.
2. **Minimal arguments.** Each argument adds friction in the picker UI. Cap at 3–5; collapse related toggles into a single enum.
3. **Always `.describe()` arguments.** This is the only label users see in the picker.
4. **Use enums for choices.** Free strings invite typos; enums document the allowed set.
5. **Reference resources by URI.** Mention `users://{id}`, `config://app` — clients fetch them and include in context.
6. **System + user split for non-trivial flows.** Use `{ messages: [...] }` instead of stuffing role-mixing into a single string.
7. **Prompt arguments, not branches.** If your handler has if/else picking between three completely different texts, that is three different prompts.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| One prompt with 12 optional arguments | Split into 2–3 focused prompts |
| Free-text `style: z.string()` | `style: z.enum(["concise", "detailed"])` |
| Prompt that fetches and writes data | That's a tool |
| Prompt body changes based on time of day | Move that branching into a tool |
| Resource content embedded inline as a giant string | Reference the resource URI; let the client fetch |
| Prompt named `do-thing` with no description | Always supply `description` — pickers depend on it |
| Schema arguments without `.describe()` | Add `.describe(...)` to every field |

## Few-shot patterns

Embed examples in `system` content. Keep them short and structurally identical to the expected output:

```typescript
server.prompt(
  {
    name: "categorize-issue",
    description: "Categorize a GitHub issue title",
    schema: z.object({ title: z.string() }),
  },
  async ({ title }) => ({
    messages: [
      {
        role: "system",
        content: `Classify the issue title as one of: bug | feature | chore | question.
Examples:
"App crashes on launch" -> bug
"Add dark mode" -> feature
"Update README typos" -> chore
"How do I configure X?" -> question
Respond with the single label only.`,
      },
      { role: "user", content: title },
    ],
  }),
);
```

## Multi-turn seeds

Use multi-message returns to set the *shape* of the conversation, not to pre-bake the answer:

```typescript
server.prompt(
  {
    name: "debug-session",
    schema: z.object({ error: z.string() }),
  },
  async ({ error }) => ({
    messages: [
      { role: "system", content: "You are a senior SRE. Lead with the most likely cause." },
      { role: "user", content: `Error: ${error}` },
      { role: "assistant", content: "Likely causes, ranked. Then I'll ask one diagnostic question." },
    ],
  }),
);
```

The seeded `assistant` message acts as a structural commitment — the model continues in that shape.

## Naming

Use `verb-object` — `code-review`, `analyze-config`, `debug-session`. Same convention as tool names. The prompt name appears in client UI; users scan by verb.

| Bad | Good |
|---|---|
| `prompt1` | `analyze-config` |
| `helper` | `debug-session` |
| `do_review_code` | `code-review` |
| `MyAwesomePrompt` | `code-review` |

## Validation order

The server validates arguments against the Zod schema **before** calling your handler. You never need to revalidate inside the handler — invalid input is rejected upstream.

If validation succeeds but the resolved values are semantically invalid (e.g., user not found, project archived), throw from the handler. The client surfaces the error.

## Performance

Prompts are cheap — they return text. Don't fetch data inside the prompt handler unless you genuinely need it for the seed; instead, reference resource URIs in the prompt text and let the client fetch them lazily.

```typescript
// Wasteful — refetches every time the prompt is opened
async ({ userId }) => {
  const user = await db.getUser(userId); // unnecessary
  return text(`Analyze user: ${JSON.stringify(user)}`);
}

// Lean — client fetches the resource only if needed
async ({ userId }) => text(`Analyze the user at users://${userId}.`);
```
