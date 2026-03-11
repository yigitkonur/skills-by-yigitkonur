# Prompt Helpers

> Documents the small prompt library shipped with the AI package. Consult this when adding reusable prompt templates instead of embedding prompt strings inline everywhere.

## Key file

- `packages/ai/lib/prompts.ts`

## Representative code

```ts
export const promptListProductNames = (topic: string): string => {
  return `List me five funny product names that could be used for ${topic}`;
};
```

## Practical rule

If a prompt is meant to be reused across routes or features, move it into `packages/ai/lib/prompts.ts` so the wording stays centralized.

---

**Related references:**
- `references/ai/models-and-exports.md` — Model package entry point
- `references/setup/import-conventions.md` — Package import patterns
- `references/conventions/naming.md` — Naming conventions
