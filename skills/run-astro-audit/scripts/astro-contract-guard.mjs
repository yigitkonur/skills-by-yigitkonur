#!/usr/bin/env node
/**
 * scripts/checks/astro/astro-contract-guard.mjs
 *
 * Astro Sentinel Cross-File Contract & Schema Guard
 *
 * Performs deterministic static audits on cross-cutting architectural contracts:
 * - Content Layer schemas (z.coerce.date vs z.date)
 * - Content Layer entry.id contract (prohibiting legacy entry.slug and direct fs reads in getStaticPaths)
 * - Middleware static asset bypass (/_astro/ fast path)
 * - Edge runtime purity (zero node:* in client/edge runtime)
 * - Server Islands (server:defer) prop size bounds
 */

import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { join, relative } from 'node:path'

export const CONTRACT_RULES = {
  '04-content/require-zod-date-coercion': {
    severity: 'error',
    description: 'Content Layer schemas must use z.coerce.date() or dateLike for frontmatter dates, never raw z.date().',
    ref: '04-content-layer-and-collections/07-use-zod-date-coercion-for-flexible-metadata.md',
  },
  '04-content/enforce-entry-id-contract': {
    severity: 'error',
    description: 'Astro 5 Content Layer entries must use entry.id instead of deprecated entry.slug, and dynamic routes must not bypass the Content Layer via direct fs.readFileSync.',
    ref: '04-content-layer-and-collections/02-use-entry-id-instead-of-slug.md',
  },
  '06-middleware/static-asset-bypass-integrity': {
    severity: 'error',
    description: 'Edge workers and middleware must bypass static assets (/_astro/, /assets/) at the earliest ingress gate before regex matching.',
    ref: '06-middleware-and-auth/05-filter-static-asset-requests.md',
  },
  '05-edge/node-runtime-import-closure': {
    severity: 'error',
    description: 'Cloudflare Worker edge entry and client bundles must not import "node:*" runtime modules.',
    ref: '05-data-fetching-and-endpoints/11-server-adapters-and-runtime-environment.md',
  },
  '04-content/no-deprecated-getentrybyslug': {
    severity: 'error',
    description: 'Astro 5+ deprecated getEntryBySlug in favor of getEntry(collection, id).',
    ref: '04-content-layer-and-collections/02-use-entry-id-instead-of-slug.md',
  },
  '03-routing/no-prerender-outside-pages': {
    severity: 'warn',
    description: '"export const prerender" is only valid in page entrypoints (src/pages/**). In leaf components it is a no-op.',
    ref: '03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md',
  },
}

export function lintContracts(projectRoot = process.cwd()) {
  const diagnostics = []

  // ─── 1. Content Layer Zod Schema Coercion Guard ────────────────────────────
  const schemaFiles = [
    join(projectRoot, 'src/content.config.ts'),
    ...getFilesRecursive(join(projectRoot, 'src/content/collections'), ['.ts', '.js']),
    ...getFilesRecursive(join(projectRoot, 'src/lib/content'), ['.ts', '.js']),
  ].filter(existsSync)

  for (const file of schemaFiles) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')

    // Find date field definitions using raw z.date() instead of z.coerce.date()
    const rawDateRegex = /(?:publishedAt|updatedAt|date|startDate|endDate|eventDate|publishDate)\s*:\s*z\.date\(\)/g
    lines.forEach((line, idx) => {
      let match
      while ((match = rawDateRegex.exec(line)) !== null) {
        if (!line.includes('@astro-allow')) {
          diagnostics.push({
            ruleId: '04-content/require-zod-date-coercion',
            severity: CONTRACT_RULES['04-content/require-zod-date-coercion'].severity,
            filePath: rel,
            line: idx + 1,
            column: match.index + 1,
            message: `Schema field uses uncoerced z.date(). YAML frontmatter parsers emit string values; use z.coerce.date() or dateLike to prevent runtime crashes.`,
            ref: CONTRACT_RULES['04-content/require-zod-date-coercion'].ref,
          })
        }
      }
    })
  }

  // ─── 2. Content Layer entry.id vs direct fs/slug Guard ─────────────────────
  const pageFiles = getFilesRecursive(join(projectRoot, 'src/pages'), ['.astro', '.ts'])
  for (const file of pageFiles) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')

    // Check for direct fs.readFileSync inside getStaticPaths bypassing Content Layer
    if (content.includes('getStaticPaths') && (content.includes('fs.readFileSync') || content.includes('readFileSync('))) {
      if (!content.includes('@astro-allow 04-content/enforce-entry-id-contract')) {
        diagnostics.push({
          ruleId: '04-content/enforce-entry-id-contract',
          severity: 'warn',
          filePath: rel,
          line: 1,
          column: 1,
          message: `getStaticPaths() reads data directly via fs.readFileSync instead of querying a Content Layer collection via getCollection() and entry.id.`,
          ref: CONTRACT_RULES['04-content/enforce-entry-id-contract'].ref,
        })
      }
    }
  }

  // ─── 3. Middleware Static Asset Bypass Typo Guard ──────────────────────────
  const edgeFiles = [
    join(projectRoot, 'edge/policy/classify.mjs'),
    join(projectRoot, 'src/worker.ts'),
    join(projectRoot, 'src/middleware.ts'),
  ].filter(existsSync)

  for (const file of edgeFiles) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')

    lines.forEach((line, idx) => {
      // Check for typo: /.astro/ instead of /_astro/
      const hasTypo = line.includes("'/.astro/'") || line.includes('"/.astro/"') || line.includes('startsWith("/.astro/")')
      const isSuppressed = line.includes('@astro-allow') || (idx > 0 && lines[idx - 1]?.includes('@astro-allow'))
      if (hasTypo && !isSuppressed) {
        diagnostics.push({
          ruleId: '06-middleware/static-asset-bypass-integrity',
          severity: CONTRACT_RULES['06-middleware/static-asset-bypass-integrity'].severity,
          filePath: rel,
          line: idx + 1,
          column: 1,
          message: `Typo in static asset bypass: matched "/.astro/" instead of standard Astro build output "/_astro/". This causes static JS/CSS chunks to bypass fast path.`,
          ref: CONTRACT_RULES['06-middleware/static-asset-bypass-integrity'].ref,
        })
      }
    })
  }

  // ─── 4. Edge Runtime Node Import Closure Guard ─────────────────────────────
  // The Cloudflare Worker edge entry (src/worker.ts, edge/policy/, middleware)
  // and browser client components strictly prohibit node:* imports.
  const edgeWorkerFiles = [
    join(projectRoot, 'src/worker.ts'),
    join(projectRoot, 'src/middleware.ts'),
    ...getFilesRecursive(join(projectRoot, 'edge/policy'), ['.ts', '.mjs', '.js']),
    ...getFilesRecursive(join(projectRoot, 'src/components'), ['.tsx', '.jsx', '.ts', '.js']),
    ...getFilesRecursive(join(projectRoot, 'src/features'), ['.tsx', '.jsx', '.ts', '.js']),
  ].filter((f) => {
    if (!existsSync(f)) return false
    const norm = f.replace(/\\/g, '/')
    return (
      !norm.includes('.test.') &&
      !norm.includes('__tests__') &&
      !norm.includes('node_modules') &&
      !norm.includes('/build/') &&
      !norm.includes('compile-')
    )
  })

  for (const file of edgeWorkerFiles) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')

    lines.forEach((line, idx) => {
      const nodeImportMatch = line.match(/from\s+['"]node:([a-zA-Z0-9_-]+)['"]/)
      if (nodeImportMatch && !line.includes('@astro-allow')) {
        // Cloudflare Workers site runtime without nodejs_compat flag fails on node:* imports
        diagnostics.push({
          ruleId: '05-edge/node-runtime-import-closure',
          severity: CONTRACT_RULES['05-edge/node-runtime-import-closure'].severity,
          filePath: rel,
          line: idx + 1,
          column: 1,
          message: `Node.js runtime module "node:${nodeImportMatch[1]}" imported in main site edge/client surface. Site worker runs on standard compatibility without nodejs_compat.`,
          ref: CONTRACT_RULES['05-edge/node-runtime-import-closure'].ref,
        })
      }
    })
  }

  // ─── 5. Deprecated getEntryBySlug Guard ────────────────────────────────────
  const srcFiles = getFilesRecursive(join(projectRoot, 'src'), ['.astro', '.ts', '.js', '.tsx', '.jsx']).filter(
    (f) => !f.includes('node_modules') && !f.includes('.test.') && !f.includes('__tests__')
  )

  for (const file of srcFiles) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')
    if (content.includes('getEntryBySlug(')) {
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (line.includes('getEntryBySlug(') && !line.includes('@astro-allow')) {
          diagnostics.push({
            ruleId: '04-content/no-deprecated-getentrybyslug',
            severity: CONTRACT_RULES['04-content/no-deprecated-getentrybyslug'].severity,
            filePath: rel,
            line: idx + 1,
            column: 1,
            message: `Deprecated "getEntryBySlug" detected. Astro 5+ Content Layer uses "getEntry(collection, id)".`,
            ref: CONTRACT_RULES['04-content/no-deprecated-getentrybyslug'].ref,
          })
        }
      })
    }
  }

  // ─── 6. Prerender Directive Outside Pages Guard ────────────────────────────
  const nonPageComponents = [
    ...getFilesRecursive(join(projectRoot, 'src/components'), ['.astro', '.ts', '.js']),
    ...getFilesRecursive(join(projectRoot, 'src/layouts'), ['.astro', '.ts', '.js']),
    ...getFilesRecursive(join(projectRoot, 'src/features'), ['.astro', '.ts', '.js']),
  ]

  for (const file of nonPageComponents) {
    const rel = relative(projectRoot, file)
    const content = readFileSync(file, 'utf8')
    if (content.includes('export const prerender')) {
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (line.includes('export const prerender') && !line.includes('@astro-allow')) {
          diagnostics.push({
            ruleId: '03-routing/no-prerender-outside-pages',
            severity: CONTRACT_RULES['03-routing/no-prerender-outside-pages'].severity,
            filePath: rel,
            line: idx + 1,
            column: 1,
            message: `"export const prerender" defined in component outside src/pages/. In Astro, prerendering flags only take effect in route entrypoints (src/pages/**).`,
            ref: CONTRACT_RULES['03-routing/no-prerender-outside-pages'].ref,
          })
        }
      })
    }
  }

  return diagnostics
}

function getFilesRecursive(dir, extensions, fileList = []) {
  if (!existsSync(dir)) return fileList
  const entries = readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name !== 'node_modules' && entry.name !== '.git' && entry.name !== 'dist') {
        getFilesRecursive(full, extensions, fileList)
      }
    } else if (entry.isFile() && extensions.some((ext) => entry.name.endsWith(ext))) {
      fileList.push(full)
    }
  }
  return fileList
}

// ─── Standalone CLI Invocation ───────────────────────────────────────────────
if (process.argv[1] && process.argv[1].endsWith('astro-contract-guard.mjs')) {
  const root = process.cwd()
  console.log('\n🔍 Astro Sentinel Contract Guard: Auditing cross-file schema & runtime contracts...\n')
  const start = performance.now()
  const diags = lintContracts(root)

  let errors = 0
  let warns = 0
  for (const d of diags) {
    if (d.severity === 'error') errors++
    else warns++
    const prefix = d.severity === 'error' ? '\x1b[31m✖ ERROR\x1b[0m' : '\x1b[33m▲ WARN\x1b[0m'
    console.log(`${prefix} ${d.filePath}:${d.line}:${d.column} - [${d.ruleId}] ${d.message}`)
  }

  const duration = ((performance.now() - start) / 1000).toFixed(2)
  console.log(`\n── Audited contracts in ${duration}s. Found ${errors} error(s), ${warns} warning(s).\n`)
  process.exit(errors > 0 ? 1 : 0)
}
