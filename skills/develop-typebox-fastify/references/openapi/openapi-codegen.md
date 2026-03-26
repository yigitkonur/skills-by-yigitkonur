# Client SDK Generation from OpenAPI Spec

## Overview

With TypeBox schemas powering your Fastify API, the generated OpenAPI spec can drive
client SDK generation. This gives frontend teams typed API clients that stay in sync
with backend schemas automatically.

## Extracting the OpenAPI Spec

```typescript
// scripts/generate-openapi.ts
import { buildApp } from '../src/app.js'
import { writeFileSync } from 'node:fs'

async function main() {
  const app = await buildApp()
  await app.ready()

  const spec = app.swagger()
  writeFileSync('openapi.json', JSON.stringify(spec, null, 2))
  console.log('OpenAPI spec written to openapi.json')

  await app.close()
}

main()
```

```json
// package.json
{
  "scripts": {
    "generate:spec": "tsx scripts/generate-openapi.ts",
    "generate:client": "npm run generate:spec && openapi-typescript openapi.json -o src/client/api.d.ts"
  }
}
```

## openapi-typescript (Type-Only Generation)

Generates TypeScript types from your spec -- no runtime code, pairs with `openapi-fetch`:

```bash
npm install -D openapi-typescript
npm install openapi-fetch
```

```bash
npx openapi-typescript openapi.json -o src/client/api.d.ts
```

```typescript
// src/client/index.ts
import createClient from 'openapi-fetch'
import type { paths } from './api.js'

const client = createClient<paths>({
  baseUrl: 'https://api.example.com'
})

// Fully typed -- params, body, and response are inferred
const { data, error } = await client.GET('/users/{id}', {
  params: { path: { id: '123' } }
})

if (data) {
  console.log(data.name)  // typed as string
  console.log(data.email) // typed as string
}

// POST with typed body
const { data: newUser } = await client.POST('/users', {
  body: {
    name: 'Alice',
    email: 'alice@example.com',
    role: 'user'
  }
})
```

## openapi-generator (Full SDK Generation)

Generates complete client libraries in many languages:

```bash
npm install -D @openapitools/openapi-generator-cli
```

```bash
# TypeScript Axios client
npx openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o src/generated/client \
  --additional-properties=supportsES6=true,npmName=my-api-client

# Python client
npx openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o python-client/
```

## orval (React Query / SWR Integration)

Generates typed hooks for React Query, SWR, or Angular:

```bash
npm install -D orval
```

```typescript
// orval.config.ts
import { defineConfig } from 'orval'

export default defineConfig({
  api: {
    input: './openapi.json',
    output: {
      target: './src/client/api.ts',
      client: 'react-query',
      mode: 'tags-split',
      override: {
        mutator: {
          path: './src/client/custom-fetch.ts',
          name: 'customFetch'
        },
        query: {
          useQuery: true,
          useMutation: true
        }
      }
    }
  }
})
```

```bash
npx orval
```

```typescript
// Usage in React component
import { useGetUsers, useCreateUser } from './client/api'

function UserList() {
  const { data: users, isLoading } = useGetUsers({ page: 1, limit: 20 })
  const createUser = useCreateUser()

  const handleCreate = () => {
    createUser.mutate({
      data: { name: 'Bob', email: 'bob@example.com', role: 'user' }
    })
  }

  return (/* render users */)
}
```

## CI Pipeline for Client Generation

```yaml
# .github/workflows/generate-client.yml
name: Generate API Client
on:
  push:
    paths: ['src/routes/**', 'src/schemas/**']

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npm run generate:spec
      - run: npx openapi-typescript openapi.json -o packages/client/src/api.d.ts
      - name: Commit generated types
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add packages/client/src/api.d.ts openapi.json
          git diff --cached --quiet || git commit -m "chore: regenerate API client types"
          git push
```

## Validating Spec Correctness

```bash
# Lint the generated OpenAPI spec
npm install -D @redocly/cli
npx redocly lint openapi.json
```

## Key Points

- Extract OpenAPI spec programmatically with `app.swagger()` after `app.ready()`
- `openapi-typescript` + `openapi-fetch` = lightweight, type-only approach
- `orval` generates React Query/SWR hooks directly
- `openapi-generator` supports 40+ languages for broader ecosystem
- Automate generation in CI when schema files change
- TypeBox descriptions and examples carry through to generated client docs
- Keep `openapi.json` in version control as a contract artifact
