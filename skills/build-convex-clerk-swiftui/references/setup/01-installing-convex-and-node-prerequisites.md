# Installing Convex and Node Prerequisites

## Use This When
- Starting a new Convex project alongside an Xcode workspace.
- Setting up the TypeScript backend tooling for the first time.
- Onboarding a teammate who has never run `npx convex dev`.

## Prerequisites

The Convex backend is TypeScript. Node.js 18+ is required for the CLI:

```bash
node --version   # must be 18+
npm --version    # comes with Node
```

Install via Homebrew if missing:

```bash
brew install node
```

## Initialize Convex

From the project root (where `.xcodeproj` or `.xcworkspace` lives):

```bash
npm init -y            # creates package.json if absent
npm install convex     # installs the SDK and CLI
npx convex dev         # starts the development server
```

First run prompts for login, project creation, and deployment. The result is a URL like `https://happy-animal-123.convex.cloud`. **Keep this terminal running** -- it watches `convex/` and hot-deploys on every save.

## Directory Structure After Init

```
YourProject/
  convex/                  # backend directory -- create files here
    _generated/            # auto-generated types -- never edit
  package.json
  node_modules/
  .env.local               # contains CONVEX_DEPLOYMENT=dev:happy-animal-123
```

## First File: schema.ts

Always create `convex/schema.ts` first. This defines the database:

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  messages: defineTable({
    body: v.string(),
    author: v.string(),
  }),
});
```

Save it and watch the terminal -- Convex validates and deploys instantly.

## Environment Variables

Store secrets in the Convex dashboard, not `.env.local`:

1. [dashboard.convex.dev](https://dashboard.convex.dev) -> your project -> Settings -> Environment Variables.
2. Add keys like `CLERK_JWT_ISSUER_DOMAIN`.
3. Access them in TypeScript with `process.env.VARIABLE_NAME`.

## Dev vs Production

| Command | Purpose |
|---|---|
| `npx convex dev` | Local development -- auto-deploys on save |
| `npx convex deploy` | Production -- atomic push of schema, functions, indexes |

Run `npx convex deploy` in CI/CD for production deployments.

## Avoid
- Committing `node_modules/` or `.env.local` to version control.
- Running `npx convex deploy` during active development -- use `npx convex dev` instead.
- Storing secrets in `.env.local` -- they belong in the Convex dashboard environment variables.
- Skipping `schema.ts` -- without it, the database has no validation and `_generated/` types are incomplete.

## Read Next
- [02-xcode-spm-setup-convexmobile.md](02-xcode-spm-setup-convexmobile.md)
- [05-first-run-npx-convex-dev.md](05-first-run-npx-convex-dev.md)
- [../backend/01-schema-document-model-and-relationships.md](../backend/01-schema-document-model-and-relationships.md)
