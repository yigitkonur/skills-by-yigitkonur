# Mission Brief: Cloudflare Worker Runtime Purity Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

In The project's hosting boundary:

- Staging and production workers run on the Cloudflare Workers runtime (`compatibility_date: 2026-09-02`).
- Zero `nodejs_compat` flag on the site worker; ZERO `node:` runtime imports (`fs`, `path`, `crypto`, `os`, `buffer`, `stream`) permitted in emitted edge bundles.
- `src/worker.ts` is the edge entrypoint handling routing, security headers, redirects, and on-demand SSR.
  Architectural invariants and runtime purity rules:
- Standard Cloudflare Workers Runtime Purity: Cloudflare Workers run on V8 isolates. Emitted server bundles (`_worker.js`, `dist/server/`) must contain ZERO `node:` runtime imports.
- Web Standards API Exclusivity: All server logic must strictly use standard Web APIs: `fetch()`, `Request`, `Response`, `Headers`, `ReadableStream`, `TransformStream`, `TextEncoder`, and `crypto.subtle` / `crypto.randomUUID()`.
- Adapter & Static Output Architecture: In Astro 5, `output: 'static'` natively supports on-demand routes via `@astrojs/cloudflare` with `export const prerender = false;`. Monolithic Node server features (`process.env`, file-system access) are strictly disallowed at edge runtime.
- V8 Memory & Cold-Start Limits: Edge worker initialization must execute within <10ms cold start, with bundle memory overhead fitting comfortably within Cloudflare V8 limits (128 MB default). Heavy synchronous processing or blocking loops in `src/worker.ts` are prohibited.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`11-server-adapters-and-runtime-environment.md`](../../best-practices/05-data-fetching-and-endpoints/11-server-adapters-and-runtime-environment.md) — Cloudflare Workers adapter contracts, static output with on-demand routes, and runtime environment variable bindings (`RULE-ID: ASTRO-DATA-11`).
- [`10-vite-build-pipeline-and-tree-shaking.md`](../../best-practices/01-architecture-and-philosophy/10-vite-build-pipeline-and-tree-shaking.md) — Vite build pipeline, rollup tree-shaking, and preventing Node.js built-ins from leaking into edge and client bundles (`RULE-ID: ASTRO-ARCH-10`).
- [`02-mpa-memory-lifecycle.md`](../../best-practices/01-architecture-and-philosophy/02-mpa-memory-lifecycle.md) — Multi-page architecture memory lifecycle, V8 isolate memory boundaries (<128MB), and deterministic cleanup (`RULE-ID: ASTRO-ARCH-02`).
- [`16-isolate-vite-cache-across-concurrent-dev-instances.md`](../../best-practices/01-architecture-and-philosophy/16-isolate-vite-cache-across-concurrent-dev-instances.md) — Isolating Vite pre-bundle cache directories across ports and edge build workers (`RULE-ID: ASTRO-ARCH-16`).
- [`10-response-headers-immutability-and-html-streaming.md`](../../best-practices/05-data-fetching-and-endpoints/10-response-headers-immutability-and-html-streaming.md) — Configuring edge response headers before HTML chunk streaming begins (`RULE-ID: ASTRO-DATA-10`).

Critical files to inspect:

- `src/worker.ts`
- `astro.config.mjs`
- `wrangler.toml` & `package.json`
- `edge/`
- `dist/server/` or `dist/_worker.js`

## 3.2 Mission Objective

Audit the Cloudflare Worker entrypoint and emitted bundle for absolute runtime purity.
Outcome: Prove zero node:* module leaks in the edge worker, verify that all crypto uses standard Web Crypto API (crypto.subtle), profile edge cold-start latency across global regions (Frankfurt, Istanbul, London, Dubai), and confirm edge execution operates within Cloudflare V8 memory constraints.
Constraints: Read-only audit; inspect emitted worker code.
Autonomy Grant: You own this mission end-to-end. Analyze bundle dependencies, globals, and runtime imports. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `pnpm check:worker-exports` to verify worker entrypoint contracts.
2. Inspect `dist/server/bundle.js` / `dist/_worker.js`: search for `require('node:...')` or `import ... from 'node:...'`.
3. Verify that `crypto.randomUUID()` and `crypto.subtle` are used instead of `node:crypto`.
4. Measure edge worker cold-start duration and ensure isolate initialization remains under 10ms.
5. Audit third-party packages to ensure transitive dependencies do not inject Node polyfills.
6. Verify absence of `nodejs_compat` in `wrangler.toml` and edge worker builds.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Importing Node.js Built-ins into Cloudflare Worker Runtime vs. Standard Web APIs (RULE-ID: ASTRO-DATA-11, RULE-ID: ASTRO-ARCH-10)

##### ❌ Bad Practice / Anti-Pattern: Importing Node.js built-ins (`fs`, `path`, `crypto`) into Cloudflare Worker runtime paths

```typescript
// src/worker.ts - Leaking Node built-ins into Cloudflare edge bundle
import fs from 'node:fs'
import { createHash } from 'node:crypto'
import path from 'node:path'

export default {
  async fetch(request: Request, env: any) {
    // ❌ FATAL: Crashes in production Worker without nodejs_compat!
    const filePath = path.join(process.cwd(), 'config.json')
    const data = fs.readFileSync(filePath, 'utf-8')
    const hash = createHash('sha256').update(data).digest('hex')
    return new Response(hash)
  },
}
```

_Why this fails:_ Standard Cloudflare Workers runtime throws unhandled runtime reference errors (`Module not found: node:fs` or `process is not defined`). Adding `nodejs_compat` bloats worker bundle size, degrades cold starts, and breaks runtime purity invariants.

##### ✅ Best Practice / Idiomatic: Pure Web Standards implementation on Cloudflare V8 isolate

```typescript
// src/worker.ts - Pure Web Standards implementation on Cloudflare V8 isolate
export default {
  async fetch(request: Request, env: any): Promise<Response> {
    // ✅ Pure Web Crypto API and standard URL handling without Node built-ins
    const url = new URL(request.url)
    const data = new TextEncoder().encode(url.pathname)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')

    return new Response(hashHex, {
      headers: { 'Content-Type': 'text/plain' },
    })
  },
}
```

#### Pattern 2: Shared Utility Barrel Leaking Server Dependencies into Edge Bundle (RULE-ID: ASTRO-ARCH-10)

##### ❌ Bad Practice / Anti-Pattern: Shared barrel file dragging Node dependencies into edge worker

```typescript
// src/lib/utils.ts - Dangerous barrel file mixing Node modules with edge helpers
import { readFileSync } from 'node:fs' // Server-only Node module
export function readServerConfig() {
  return JSON.parse(readFileSync('config.json', 'utf-8'))
}
export function sanitizeSlug(input: string) {
  return input.toLowerCase().replace(/[^a-z0-9]/g, '-')
}

// src/worker.ts - Importing sanitizeSlug drags node:fs into edge bundle!
import { sanitizeSlug } from './lib/utils'
```

_Why this fails:_ Vite's bundler bundles the entire barrel file into the worker module, pulling `node:fs` into the Cloudflare Worker bundle and causing runtime crashes or build failures.

##### ✅ Best Practice / Idiomatic: Isolated, single-responsibility edge-safe utility files

```typescript
// src/lib/edge/sanitize.ts - Pure zero-dependency edge utility
export function sanitizeSlug(input: string): string {
  return input.toLowerCase().replace(/[^a-z0-9]/g, '-')
}

// src/worker.ts - Clean, pure edge import
import { sanitizeSlug } from './lib/edge/sanitize'
```

#### Pattern 3: Monolithic Node `process.env` Access vs. Cloudflare Worker `env` Bindings (RULE-ID: ASTRO-DATA-11)

##### ❌ Bad Practice / Anti-Pattern: Relying on Node `process.env` in edge worker

```typescript
// src/worker.ts - Next.js habit: reading process.env at edge runtime
export default {
  async fetch(request: Request) {
    // ❌ Fails: process is not globally defined in standard V8 worker isolates
    const apiKey = process.env.API_SECRET_KEY
    return new Response(`Key length: ${apiKey?.length ?? 0}`)
  },
}
```

_Why this fails:_ `process.env` is an artifact of Node.js runtimes. In Cloudflare Workers, environment variables and KV/D1/R2 bindings are injected via the second parameter `env` of the `fetch` handler.

##### ✅ Best Practice / Idiomatic: Cloudflare Worker `env` parameter & Astro Env

```typescript
// src/worker.ts - Typed environment bindings passed via worker context
export interface Env {
  API_SECRET_KEY: string
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // ✅ Properly accessing edge environment bindings
    const apiKey = env.API_SECRET_KEY
    return new Response(`Authenticated edge request`, {
      headers: { 'X-Auth-Status': apiKey ? 'configured' : 'missing' },
    })
  },
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-DATA-11`, `RULE-ID: ASTRO-ARCH-10`, `RULE-ID: ASTRO-ARCH-02`, `RULE-ID: ASTRO-ARCH-16`, `RULE-ID: ASTRO-DATA-10`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "41-CLOUDFLARE-WORKER-RUNTIME-PURITY-001",
    "rule_id": "RULE-ID: ASTRO-DATA-11 (Pair On-Demand Routes with Verified Adapter Runtimes and Output Modes)",
    "file": "src/worker.ts",
    "line": 42,
    "severity": "critical",
    "category": "security",
    "defect": "Precise description of what is broken or violating invariants",
    "remediation": "Concrete, actionable instruction on how to fix it"
  }
]
```

2. **`evidence.md`**: Comprehensive investigative research log:
   - Full command outputs, vitest runs, grep matches, AST dumps.
   - Analysis of confirmed facts vs assumptions.
   - Step-by-step reproduction proof.

3. **`handoff.md`**: The executive, action-oriented implementation blueprint for the next subagent:
   - **Executive Summary:** Overall health of this domain (Clean / Minor Defects / Blockers).
   - **Architectural Invariants:** Rules that the fixing agent must NEVER violate while remediating.
   - **Step-by-Step Remediation Checklist:** Prioritized action items (ordered from highest to lowest severity).
   - **Exact Code Replacements:** File paths, line numbers, current faulty snippet, and drop-in replacement snippet.
   - **Verification Battery:** The exact commands the fixing agent must run post-remediation to prove 100% success.

4. **`issue-body.md`**: The publication-ready GitHub Issue markdown body adhering to the two-tier structure:
   - **Checklist Header**: The verified nested checklist of up to 200 items (3 levels max).
   - **Outer Tier (localized primary locale)**: Conversational human summary (1-2 sentences), affected URLs/routes table, surface area table (viewports, themes, components), observed defect vs expected behavior (WITHOUT prescribing code fixes).
   - **Inner Tier (English `<details>`)**: Collapsed block titled `<details><summary><strong>Agent implementation brief — scope, source map, behavior contracts, and verification</strong></summary>...</details>`. Contains exact `file:line` citations, quoted 3-8 lines of code, defect classification (`bug` | `by-design` | `drift` | `reversal`), required behavioral invariants, known traps, acceptance checklist, and embeds the structured `findings.json` table and `handoff.md` remediation steps.

5. **Publication via GitHub CLI (`gh`) & Sub-Issue Creation**:
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (max 200 items, 3 levels deep), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and pushes the JSON deliverables to `origin main` directly:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/issue-body.md" \
  --title "[Audit - Cloudflare Worker Runtime Purity Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit source code and edge entrypoints for forbidden Node built-in imports:
   ```bash
   git grep -n "node:" src/worker.ts edge/ || echo "PASS: Zero node: runtime imports in source"
   ```
2. Audit emitted worker bundle for disallowed `node:` imports:
   ```bash
   grep -E "(require\(['\"]node:)|(from ['\"]node:)" dist/_worker.js dist/server/*.mjs 2>/dev/null || echo "PASS: Zero node: runtime imports in build"
   ```
3. Verify absence of nodejs_compat in worker configuration:
   ```bash
   grep -rn 'nodejs_compat' wrangler.toml edge/ || echo "PASS: nodejs_compat is not enabled"
   ```
4. Run runtime dependencies purity gate:
   ```bash
   pnpm check:tracked-runtime-deps
   ```
5. Verify edge worker entrypoint contracts and exports:
   ```bash
   pnpm check:worker-exports
   ```
6. Dry-run wrangler bundle analysis to verify zero Node polyfill warnings:
   ```bash
   pnpm exec wrangler deploy --dry-run --outdir /tmp/wrangler-dry-run
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Cloudflare Worker Runtime Purity Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/05-edge-workers-and-qa/41-cloudflare-worker-runtime-purity/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
