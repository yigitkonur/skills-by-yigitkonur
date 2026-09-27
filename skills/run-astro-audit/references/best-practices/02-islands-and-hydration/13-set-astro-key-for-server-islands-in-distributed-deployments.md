# Set ASTRO_KEY for Server Islands in Distributed Deployments

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

Astro encrypts props passed to `server:defer` components to ensure sensitive internal variables cannot be manipulated or inspected on the client. By default, Astro generates a random encryption key at build time. In multi-region deployments, Kubernetes clusters, rolling deployment environments, or CDN setups, the static frontend HTML might be served with one build key while the backend island function decrypts with a newly deployed build key. If keys mismatch, prop decryption fails and the server island returns HTTP 500 errors.

## 2. How It Differs From Classic React / Next.js

Next.js RSC relies on server actions encryption tied to `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`. In Astro 5, Server Islands provide a first-class CLI command (`astro create-key`) to generate a stable, persistent secret key (`ASTRO_KEY`) passed via environment variables.

## 3. Common Mistakes & Anti-Patterns

Deploying Server Islands to rolling cloud environments (e.g. Kubernetes, AWS ECS, Cloudflare Workers multi-version deployments) without defining `ASTRO_KEY`, causing transient decryption failures during rollout transitions.

### ❌ Bad Practice / Anti-Pattern

```bash
# Relying on auto-generated build-time ephemeral key
# Server A builds with Key-1; Server B deploys with Key-2
# Client requests island from Server B using props encrypted by Server A:
# Result: Error: Failed to decrypt server island props (HTTP 500)
npx astro build
```

### ✅ Best Practice / Idiomatic

Generate a durable encryption key and persist it across your CI/CD pipeline and runtime environment:

```bash
# Generate key once
npx astro create-key
```

Output:

```
ASTRO_KEY=d7a9b0c1...
```

Add to `.env` / CI/CD secrets:

```env
# .env / Production secret manager
ASTRO_KEY="d7a9b0c1e8f2345a90123456789abcdef0123456789abcdef0123456789abcdef"
```

During build and runtime, Astro automatically detects `ASTRO_KEY` and reuses the constant encryption secret across all instances and builds.

## 4. Verification & Audit

Verify that the `ASTRO_KEY` environment variable is loaded in both the build step and the production runtime:

```bash
node -e "if (!process.env.ASTRO_KEY) throw new Error('Missing ASTRO_KEY in environment');"
```

Test rolling deployments by ensuring an encrypted server island URL generated in Build N decrypts successfully on Build N+1.
