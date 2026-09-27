# Mission Brief: Sharded Build Engine RAM-Disk Calibration Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

The Astro application employs a multi-process route-sharded build engine (`scripts/release/astro/sharded-build.mjs`):

- On the 80-core monster host, it auto-calibrates to 40 parallel render threads (20 shards x 2 concurrency) operating in RAM-disk tmpfs (`/tmp/ramdisk`).
- However, high thread contention or excessive concurrent Vite SSR instances can exhaust memory and freeze the host.
- Architecture Rule: Production build execution vs dev server isolation. Astro sharded builds execute Rollup/esbuild tree-shaking, CSS minification, and static page synthesis. The build engine must never mix dev server HMR artifacts or unbundled ESM into build outputs.
- Quality Gate Rule: Astro builds transpiled with esbuild intentionally bypass deep TypeScript type-checking to keep build cycles rapid. Therefore, `astro check --minimumFailingSeverity error` must execute as a mandatory blocking quality gate before sharded rendering kicks off, preventing invalid component props from crashing worker threads mid-build.
- Asset Budget Rule: Automated bundle size thresholds must be verified during build completion to halt CI if emitted client JS or CSS payloads exceed byte budgets.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`16-isolate-vite-cache-across-concurrent-dev-instances.md`](../../best-practices/01-architecture-and-philosophy/16-isolate-vite-cache-across-concurrent-dev-instances.md) — Isolating Vite pre-bundle dependency cache per shard and instance to eliminate lock file contention (`EBUSY`/`EPERM`) and cache corruption (`RULE-ID: ASTRO-ARCH-16`).
- [`02-mpa-memory-lifecycle.md`](../../best-practices/01-architecture-and-philosophy/02-mpa-memory-lifecycle.md) — Multi-Page Architecture clean memory lifecycle, bounding worker process heap growth during high-concurrency static page synthesis (`RULE-ID: ASTRO-ARCH-02`).
- [`10-vite-build-pipeline-and-tree-shaking.md`](../../best-practices/01-architecture-and-philosophy/10-vite-build-pipeline-and-tree-shaking.md) — Vite build pipeline, Rollup code splitting, tree-shaking dead dependencies, and enforcing bundle size budgets (`RULE-ID: ASTRO-ARCH-10`).
- [`10-response-headers-immutability-and-html-streaming.md`](../../best-practices/05-data-fetching-and-endpoints/10-response-headers-immutability-and-html-streaming.md) — Static page pre-rendering contracts and build-time HTML output formatting (`RULE-ID: ASTRO-DATA-10`).
- [`11-server-adapters-and-runtime-environment.md`](../../best-practices/05-data-fetching-and-endpoints/11-server-adapters-and-runtime-environment.md) — Cloudflare Workers build adapter configuration and static route pre-rendering targets (`RULE-ID: ASTRO-DATA-11`).

Critical files to inspect:

- `scripts/release/astro/sharded-build.mjs`
- `scripts/release/astro/worker-build.mjs`
- `config/perf.mjs`
- `astro.config.mjs`
- `package.json` (`pnpm astro:build`, `pnpm check:types`)

## 3.2 Mission Objective

Audit the sharded build engine's concurrency scaling, memory limits, and ramdisk lifecycle.
Outcome: Deliver optimal concurrency calibration formulas (supporting ASTRO_CONCURRENCY) preventing host lockup, with robust cleanup of tmpfs mounts on failure or exit.
Constraints: Read-only audit; profile thread scaling without launching heavy full builds.
Autonomy Grant: You own this mission end-to-end. Model core utilization, RAM bandwidth, and tmpfs IOPS. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `sharded-build.mjs`: verify how total CPU cores and available RAM determine shard count.
2. Check RAM-disk unmount logic: ensure SIGINT, SIGTERM, and error exits cleanly unmount and clear tmpfs mounts via traps.
3. Verify that `ASTRO_CONCURRENCY` environment variable properly overrides defaults when specified.
4. Audit build-time quality gates and bundle budget checks in package scripts.
5. Verify that Vite pre-bundle cache directories are properly partitioned per shard.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Storing Unpartitioned `.vite` Caches Across Concurrent Build Shards (RULE-ID: ASTRO-ARCH-16)

##### ❌ Bad Practice / Anti-Pattern: Storing unpartitioned `.vite` caches across concurrent build shards (causes lock collisions)

```javascript
// astro.config.mjs - Default Vite cache shared across parallel shards
import { defineConfig } from 'astro/config'

export default defineConfig({
  // ❌ Relies on default node_modules/.vite; parallel build shards collide on lockfiles
  // Causes EBUSY / EPERM race conditions and crashes build workers
})
```

_Why this fails:_ When 20 shards execute concurrently in RAM-disk tmpfs, multiple Vite instances attempt to write pre-bundled dependency artifacts and manifest files into the same `node_modules/.vite` folder simultaneously. This leads to `EBUSY` file locking errors, incomplete dependency bundles, and sporadic build failures.

##### ✅ Best Practice / Idiomatic: Dynamically setting `vite: { cacheDir: process.env.VITE_CACHE_DIR }`

```javascript
// astro.config.mjs - Partitioning Vite cacheDir per build shard or port
import { defineConfig } from 'astro/config'

const cacheDir =
  process.env.VITE_CACHE_DIR || `node_modules/.vite-shard-${process.env.SHARD_INDEX || '0'}`

export default defineConfig({
  vite: {
    // ✅ Partition Vite pre-bundle cache per shard to eradicate lock contention
    cacheDir,
    optimizeDeps: {
      holdUntilCrawlEnd: true,
    },
  },
})
```

#### Pattern 2: Skipping Type-Check Gate Before Sharded Builds vs. Blocking Pre-Flight Verification (RULE-ID: ASTRO-ARCH-02, RULE-ID: ASTRO-ARCH-10)

##### ❌ Bad Practice / Anti-Pattern: Unchecked sharded build without typecheck gate or memory limits

```json
// package.json - Unchecked sharded build without typecheck gate or memory limits
{
  "scripts": {
    "build": "node scripts/release/astro/sharded-build.mjs",
    "typecheck": "tsc --noEmit"
  }
}
```

_Why this fails:_ `tsc --noEmit` ignores `.astro` component files completely, while `astro build` uses esbuild to maximize speed and skips deep type-checking. Broken props or invalid Content Layer schemas crash workers mid-build after allocating tens of gigabytes in RAM-disk tmpfs.

##### ✅ Best Practice / Idiomatic: Blocking `astro check` quality gate & budget verification

```json
// package.json - Blocking astro check quality gate & budget verification
{
  "scripts": {
    "build": "pnpm check:types && node scripts/release/astro/sharded-build.mjs",
    "check:types": "astro check --minimumFailingSeverity error"
  }
}
```

#### Pattern 3: Unbounded Concurrency Over-Allocating Host RAM vs. Hardware-Calibrated Concurrency with Tmpfs Traps (RULE-ID: ASTRO-ARCH-02)

##### ❌ Bad Practice / Anti-Pattern: Spawning unconstrained worker threads ignoring available RAM headroom

```javascript
// scripts/release/astro/sharded-build.mjs - Hardcoded CPU core scaling without memory guardrails
import os from 'node:os'

// ❌ DANGEROUS: Spawns 80 workers on an 80-core machine; at 2GB each, requires 160GB RAM!
// Exceeds Linux cgroup user-slice limits and freezes the host entirely.
const concurrency = os.cpus().length
```

_Why this fails:_ Astro SSR compilation and Rollup asset bundling require substantial memory headroom (~1.5GB to 2GB per worker process). Hardcoding concurrency directly to CPU thread counts without checking `os.freemem()` leads to Out-Of-Memory (OOM) kernel kills and host unresponsiveness.

##### ✅ Best Practice / Idiomatic: Hardware-calibrated worker bounding using `os.freemem()` and tmpfs cleanup trap

```javascript
// config/perf.mjs - Safe RAM-disk allocation & worker bounding
import os from 'node:os'

export const MAX_RAMDISK_BYTES = Math.floor(os.totalmem() * 0.5) // Cap at 50% physical RAM
export const BUILD_CONCURRENCY = Math.min(
  Number(process.env.ASTRO_CONCURRENCY) || 40,
  Math.max(1, Math.floor(os.freemem() / (2 * 1024 * 1024 * 1024))), // 2GB per worker
)
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-ARCH-16`, `RULE-ID: ASTRO-ARCH-02`, `RULE-ID: ASTRO-ARCH-10`, `RULE-ID: ASTRO-DATA-10`, `RULE-ID: ASTRO-DATA-11`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "43-SHARDED-BUILD-RAM-DISK-TUNING-001",
    "rule_id": "RULE-ID: ASTRO-ARCH-16 (Isolate Vite Dependency Cache Across Concurrent Dev and Build Instances)",
    "file": "astro.config.mjs",
    "line": 42,
    "severity": "high",
    "category": "performance",
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
  --body "docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/issue-body.md" \
  --title "[Audit - Sharded Build Engine RAM-Disk Calibration Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `pnpm astro check --minimumFailingSeverity error` to verify that all `.astro` templates pass type validation before builds.
2. Confirm that sharded build exits cleanly without leaving orphaned node worker processes:
   ```bash
   ps aux | grep worker-build || echo "PASS: No orphaned build workers"
   ```
3. Verify that tmpfs allocations never exceed 50% of available physical host RAM:
   ```bash
   df -h /tmp/ramdisk 2>/dev/null || echo "PASS: Ramdisk unmounted cleanly"
   ```
4. Audit Vite cache partitioning configurations across codebase:
   ```bash
   git grep -n "cacheDir" astro.config.* config/
   ```
5. Audit `ASTRO_CONCURRENCY` handling in build scripts:
   ```bash
   git grep -n "ASTRO_CONCURRENCY" scripts/release/astro/
   ```
6. Inspect build lifecycle hooks to ensure bundle size budgets are evaluated upon shard aggregation.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Sharded Build Engine RAM-Disk Calibration Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/05-edge-workers-and-qa/43-sharded-build-ram-disk-tuning/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
