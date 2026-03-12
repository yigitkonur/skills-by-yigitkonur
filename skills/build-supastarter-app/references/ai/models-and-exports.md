# AI Models & Exports

> Documents the `@repo/ai` package entry points. Consult this when changing the default model provider or importing shared AI utilities in API routes or server functions.
>
> The package centralizes model selection so the rest of the app can depend on a stable `textModel`, `imageModel`, and `audioModel` interface.

## Main Entry Point

```ts
// packages/ai/index.ts
export const textModel = openai("gpt-4o-mini");
export const imageModel = openai("dall-e-3");
export const audioModel = openai("whisper-1");

export * from "ai";
export * from "./lib";
```

## Client Entry Point

`packages/ai/client.ts` re-exports React hooks from `@ai-sdk/react`:

```ts
export * from "@ai-sdk/react";
```

Use this split when you need:

- server-side model instances or AI SDK helpers → `@repo/ai`
- client-side hooks like `useChat()` → `@repo/ai/client`

---

**Related references:**
- `references/ai/prompt-helpers.md` — Shared prompt helpers exported from the package
- `references/setup/environment-setup.md` — `OPENAI_API_KEY` and other environment context
- `references/api/root-router.md` — AI endpoints are mounted alongside other API modules
- `references/cheatsheets/env-vars.md` — Environment variable reference
