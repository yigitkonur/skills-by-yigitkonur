#!/usr/bin/env node
/**
 * scripts/checks/astro/astro-sentinel-guard.mjs
 *
 * Astro Sentinel Component & Template AST Guard
 *
 * Performs ultra-fast, deterministic AST static analysis across all .astro
 * files in the repository using the native @astrojs/compiler parser.
 * Enforces 12 core architectural rules derived from the authoritative
 * Astro Best Practices knowledge base.
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { join, relative } from 'node:path'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)

// Lazy-resolve compiler via target projectRoot or local dependency tree
let compilerInstance = null
function getCompiler(projectRoot = process.cwd()) {
  if (!compilerInstance) {
    const candidateBases = [
      join(projectRoot, 'node_modules', 'astro', 'package.json'),
      join(projectRoot, 'package.json'),
      import.meta.url,
    ]
    for (const base of candidateBases) {
      try {
        const req = createRequire(base)
        try {
          const astroPath = req.resolve('astro')
          const compilerPath = req.resolve('@astrojs/compiler', { paths: [astroPath] })
          compilerInstance = req(compilerPath)
          break
        } catch {
          const direct = req.resolve('@astrojs/compiler')
          compilerInstance = req(direct)
          break
        }
      } catch {
        // continue to next base
      }
    }
    if (!compilerInstance) {
      throw new Error(`Could not resolve @astrojs/compiler from ${projectRoot} or runtime environment.`)
    }
  }
  return compilerInstance
}

// ─── Rule Definitions & Metadata ─────────────────────────────────────────────
export const AST_RULES = {
  '01-arch/no-virtual-dom-handlers': {
    severity: 'error',
    description: 'Do not use inline JSX DOM event handlers (onClick, onChange, onSubmit) in .astro templates. Use Web Components or client scripts.',
    ref: '01-architecture-and-philosophy/12-no-virtual-dom-in-astro-templates.md',
  },
  '01-arch/no-unscoped-global-styles': {
    severity: 'warn',
    description: 'Avoid <style is:global> in leaf marketing components. Component styles should be scoped.',
    ref: '01-architecture-and-philosophy/07-scoped-styles-encapsulation.md',
  },
  '02-islands/no-blind-client-load': {
    severity: 'warn',
    description: 'Avoid client:load on below-the-fold or non-critical components. Use client:visible, client:idle, or client:media.',
    ref: '02-islands-and-hydration/02-never-default-blindly-to-client-load.md',
  },
  '02-islands/no-client-only-without-fallback': {
    severity: 'error',
    description: 'Components using client:only must provide a fallback slot or loading placeholder.',
    ref: '02-islands-and-hydration/05-use-client-only-for-browser-dependent-widgets.md',
  },
  '02-islands/no-raw-body-in-island-props': {
    severity: 'error',
    description: 'Do not pass raw markdown .body to client hydrated islands; it bloats HTML size and leaks uncompiled markdown.',
    ref: '02-islands-and-hydration/15-island-props-payload-bloat.md',
  },
  '02-islands/no-sensitive-props-leak': {
    severity: 'error',
    description: 'Do not pass gated download URLs, secret IDs, or auth tokens as props to client hydrated islands.',
    ref: '01-architecture-and-philosophy/03-frontmatter-security-boundary.md',
  },
  '03-routing/catch-all-undefined-home': {
    severity: 'error',
    description: 'Catch-all root routes ([...home].astro or [...rest].astro) must return { params: { home: undefined } } in getStaticPaths, never empty string "" or "/".',
    ref: '03-routing-and-pages/02-rest-parameters-and-catch-all.md',
  },
  '03-routing/no-uncleaned-listeners': {
    severity: 'warn',
    description: 'Scripts adding window/document event listeners on astro:page-load should register cleanup on astro:before-swap to prevent memory leaks.',
    ref: '03-routing-and-pages/15-astro-page-load-vs-domcontentloaded-and-listener-leaks.md',
  },
  '07-assets/prefer-astro-image': {
    severity: 'warn',
    description: 'Prefer <Image /> from "astro:assets" over raw <img> tags in components to benefit from build-time optimization.',
    ref: '07-assets-and-image-pipeline/01-prefer-astro-image-over-native-img.md',
  },
  '07-assets/require-image-dimensions': {
    severity: 'warn',
    description: 'Raw <img> elements must specify width and height attributes to prevent Cumulative Layout Shift (CLS).',
    ref: '07-assets-and-image-pipeline/06-infer-remote-image-dimensions-to-prevent-cls.md',
  },
  '09-perf/no-blanket-viewport-prefetch': {
    severity: 'warn',
    description: 'Avoid data-astro-prefetch="viewport" on heavy dynamic or media routes. Prefer hover or tap prefetching.',
    ref: '09-performance-prefetch-and-transitions/01-avoid-blanket-viewport-prefetching.md',
  },
  '10-migration/no-nextjs-ghost-imports': {
    severity: 'error',
    description: 'Do not import legacy Next.js packages (next/router, next/navigation, next/image, next/link).',
    ref: '10-auditing-testing-and-nextjs-migration/13-replace-next-navigation-with-native-web-standards.md',
  },
  '01-arch/no-process-env': {
    severity: 'warn',
    description: 'Avoid legacy process.env.* in Astro frontmatter. Use standard import.meta.env.* for safe bundling.',
    ref: '01-architecture-and-philosophy/02-import-meta-env-over-process-env.md',
  },
  '06-security/no-set-html-directive': {
    severity: 'warn',
    description: 'Raw set:html bypasses HTML escaping and introduces XSS risks. Ensure input is sanitized or use standard Astro expressions.',
    ref: '06-middleware-and-auth/10-sanitize-raw-html-in-dynamic-rendering.md',
  },
  '07-assets/require-image-alt': {
    severity: 'error',
    description: '<img> elements must specify an alt attribute for accessibility (WCAG 2.2 SC 1.1.1). Use alt="" for decorative images.',
    ref: '07-assets-and-image-pipeline/01-prefer-astro-image-over-native-img.md',
  },
}

// ─── Path Allowlists ─────────────────────────────────────────────────────────
const ALLOWLIST = {
  '01-arch/no-unscoped-global-styles': [
    'src/layouts/BaseLayout.astro',
    'src/layouts/Layout.astro',
    'src/components/common/ThemeScript.astro',
    'src/components/common/GlobalStyleLoader.astro',
    'src/styles/',
  ],
  '02-islands/no-blind-client-load': [
    'src/components/header/',
    'src/features/navigation/',
    'src/components/navigation/',
    'src/features/theme/',
  ],
  '07-assets/prefer-astro-image': [
    'src/components/icons/',
    'src/features/proof/components/marquee/',
  ],
  '07-assets/require-image-dimensions': [
    'src/components/icons/',
  ],
}

function isPathAllowed(ruleId, relPath) {
  const allowed = ALLOWLIST[ruleId]
  if (!allowed) return false
  const normalized = relPath.replace(/\\/g, '/')
  return allowed.some((prefix) => normalized.startsWith(prefix) || normalized.includes(prefix))
}

function hasSuppression(lines, lineIdx, ruleId) {
  const needle = `@astro-allow ${ruleId}`
  const nextLineNeedle = `@astro-allow-next-line ${ruleId}`
  const prevLineNeedle = `@astro-allow-prev-line ${ruleId}`

  // Check current line
  if (lines[lineIdx]?.includes(needle)) return true
  // Check previous line
  if (lineIdx > 0 && (lines[lineIdx - 1]?.includes(needle) || lines[lineIdx - 1]?.includes(nextLineNeedle))) return true
  // Check next line
  if (lineIdx < lines.length - 1 && (lines[lineIdx + 1]?.includes(needle) || lines[lineIdx + 1]?.includes(prevLineNeedle))) return true

  return false
}

// ─── AST Inspection Engine ───────────────────────────────────────────────────
export async function lintAstroFile(filePath, projectRoot = process.cwd()) {
  const relPath = relative(projectRoot, filePath)
  const content = readFileSync(filePath, 'utf8')
  const lines = content.split('\n')
  const compiler = getCompiler(projectRoot)
  const diagnostics = []

  let ast
  try {
    const res = await compiler.parse(content)
    ast = res.ast
  } catch (err) {
    diagnostics.push({
      ruleId: '01-arch/syntax-error',
      severity: 'error',
      filePath: relPath,
      line: 1,
      column: 1,
      message: `Failed to parse Astro AST: ${err.message}`,
    })
    return diagnostics
  }

  // 1. Frontmatter inspection
  let frontmatterValue = ''
  let hasCatchAllHome = relPath.includes('[...home]') || relPath.includes('[...rest]')

  function checkFrontmatter(fmNode) {
    frontmatterValue = fmNode.value || ''
    const fmLines = frontmatterValue.split('\n')

    // Rule: 10-migration/no-nextjs-ghost-imports
    const nextImportRegex = /from\s+['"](next\/[a-zA-Z0-9_-]+)['"]/g
    let match
    while ((match = nextImportRegex.exec(frontmatterValue)) !== null) {
      const lineNum = fmNode.position?.start?.line ?? 1
      if (!hasSuppression(lines, lineNum - 1, '10-migration/no-nextjs-ghost-imports')) {
        diagnostics.push({
          ruleId: '10-migration/no-nextjs-ghost-imports',
          severity: AST_RULES['10-migration/no-nextjs-ghost-imports'].severity,
          filePath: relPath,
          line: lineNum,
          column: 1,
          message: `Residual Next.js import detected: "${match[1]}". Migrate to native Astro APIs.`,
          ref: AST_RULES['10-migration/no-nextjs-ghost-imports'].ref,
        })
      }
    }

    // Rule: 03-routing/catch-all-undefined-home
    if (hasCatchAllHome && frontmatterValue.includes('getStaticPaths')) {
      if (frontmatterValue.includes("home: ''") || frontmatterValue.includes('home: ""') || frontmatterValue.includes("home: '/'")) {
        diagnostics.push({
          ruleId: '03-routing/catch-all-undefined-home',
          severity: AST_RULES['03-routing/catch-all-undefined-home'].severity,
          filePath: relPath,
          line: fmNode.position?.start?.line ?? 1,
          column: 1,
          message: 'Root catch-all route returns empty string or "/" for home param. Must return undefined to match root.',
          ref: AST_RULES['03-routing/catch-all-undefined-home'].ref,
        })
      }
    }

    // Rule: 01-arch/no-process-env
    const processEnvRegex = /\bprocess\.env\.([A-Z0-9_]+)\b/g
    let peMatch
    while ((peMatch = processEnvRegex.exec(frontmatterValue)) !== null) {
      const matchIdx = peMatch.index
      const relLine = frontmatterValue.slice(0, matchIdx).split('\n').length
      const lineNum = (fmNode.position?.start?.line ?? 1) + relLine - 1
      if (!hasSuppression(lines, lineNum - 1, '01-arch/no-process-env')) {
        diagnostics.push({
          ruleId: '01-arch/no-process-env',
          severity: AST_RULES['01-arch/no-process-env'].severity,
          filePath: relPath,
          line: lineNum,
          column: 1,
          message: `Legacy "process.env.${peMatch[1]}" used in Astro frontmatter. Migrate to standard "import.meta.env.${peMatch[1]}".`,
          ref: AST_RULES['01-arch/no-process-env'].ref,
        })
      }
    }
  }

  // 2. Recursive Template AST Walker
  function walk(node, parent) {
    if (!node) return

    if (node.type === 'frontmatter') {
      checkFrontmatter(node)
    }

    // Rule: 01-arch/no-unscoped-global-styles
    if (node.type === 'element' && node.name === 'style') {
      const isGlobal = (node.attributes || []).some(
        (a) => a.name === 'is:global' || a.name === 'global'
      )
      if (isGlobal && !isPathAllowed('01-arch/no-unscoped-global-styles', relPath)) {
        const line = node.position?.start?.line ?? 1
        if (!hasSuppression(lines, line - 1, '01-arch/no-unscoped-global-styles')) {
          diagnostics.push({
            ruleId: '01-arch/no-unscoped-global-styles',
            severity: AST_RULES['01-arch/no-unscoped-global-styles'].severity,
            filePath: relPath,
            line,
            column: node.position?.start?.column ?? 1,
            message: 'Unscoped <style is:global> detected in component. Encapsulate CSS or move to layout.',
            ref: AST_RULES['01-arch/no-unscoped-global-styles'].ref,
          })
        }
      }
    }

    // Element / Component checks
    if (node.type === 'element' || node.type === 'component') {
      const attrs = node.attributes || []
      const isComponent = node.type === 'component' || /^[A-Z]/.test(node.name)

      // Rule: 01-arch/no-virtual-dom-handlers (Only in native Astro HTML elements, not React islands)
      const hasClientDirective = attrs.some((a) => a.name.startsWith('client:'))
      if (!isComponent && !hasClientDirective) {
        const jsxHandler = attrs.find((a) => /^on[A-Z]/.test(a.name))
        if (jsxHandler) {
          const line = jsxHandler.position?.start?.line ?? node.position?.start?.line ?? 1
          if (!hasSuppression(lines, line - 1, '01-arch/no-virtual-dom-handlers')) {
            diagnostics.push({
              ruleId: '01-arch/no-virtual-dom-handlers',
              severity: AST_RULES['01-arch/no-virtual-dom-handlers'].severity,
              filePath: relPath,
              line,
              column: jsxHandler.position?.start?.column ?? 1,
              message: `Inline JSX handler "${jsxHandler.name}" on <${node.name}> is a no-op in Astro templates. Use a Web Component or bundled script.`,
              ref: AST_RULES['01-arch/no-virtual-dom-handlers'].ref,
            })
          }
        }
      }

      // Rule: 02-islands/no-blind-client-load
      const clientLoadAttr = attrs.find((a) => a.name === 'client:load')
      if (clientLoadAttr && !isPathAllowed('02-islands/no-blind-client-load', relPath)) {
        const line = clientLoadAttr.position?.start?.line ?? node.position?.start?.line ?? 1
        if (!hasSuppression(lines, line - 1, '02-islands/no-blind-client-load')) {
          diagnostics.push({
            ruleId: '02-islands/no-blind-client-load',
            severity: AST_RULES['02-islands/no-blind-client-load'].severity,
            filePath: relPath,
            line,
            column: clientLoadAttr.position?.start?.column ?? 1,
            message: `Component <${node.name}> uses client:load. If below the fold, downgrade to client:visible or client:idle.`,
            ref: AST_RULES['02-islands/no-blind-client-load'].ref,
          })
        }
      }

      // Rule: 02-islands/no-client-only-without-fallback
      const clientOnlyAttr = attrs.find((a) => a.name === 'client:only')
      if (clientOnlyAttr) {
        const hasFallbackSlot = (node.children || []).some((child) => {
          if (child.type === 'element' || child.type === 'component') {
            return (child.attributes || []).some((a) => a.name === 'slot' && a.value === 'fallback')
          }
          return false
        })
        if (!hasFallbackSlot) {
          const line = clientOnlyAttr.position?.start?.line ?? node.position?.start?.line ?? 1
          if (!hasSuppression(lines, line - 1, '02-islands/no-client-only-without-fallback')) {
            diagnostics.push({
              ruleId: '02-islands/no-client-only-without-fallback',
              severity: AST_RULES['02-islands/no-client-only-without-fallback'].severity,
              filePath: relPath,
              line,
              column: clientOnlyAttr.position?.start?.column ?? 1,
              message: `<${node.name} client:only> lacks a slot="fallback" placeholder, risking layout shift (CLS).`,
              ref: AST_RULES['02-islands/no-client-only-without-fallback'].ref,
            })
          }
        }
      }

      // Rules on Island Props
      if (hasClientDirective) {
        // Rule: 02-islands/no-raw-body-in-island-props
        const rawBodyProp = attrs.find((a) => a.name === 'body' || a.value === 'entry.body' || a.value?.includes('.body'))
        if (rawBodyProp) {
          const line = rawBodyProp.position?.start?.line ?? node.position?.start?.line ?? 1
          if (!hasSuppression(lines, line - 1, '02-islands/no-raw-body-in-island-props')) {
            diagnostics.push({
              ruleId: '02-islands/no-raw-body-in-island-props',
              severity: AST_RULES['02-islands/no-raw-body-in-island-props'].severity,
              filePath: relPath,
              line,
              column: rawBodyProp.position?.start?.column ?? 1,
              message: `Passing unrendered markdown .body as prop to client island <${node.name}> serializes raw text into HTML. Pass rendered HTML or excerpt.`,
              ref: AST_RULES['02-islands/no-raw-body-in-island-props'].ref,
            })
          }
        }

        // Rule: 02-islands/no-sensitive-props-leak
        const SENSITIVE_PROPS = ['bookfileurl', 'downloadurl', 'secret', 'apikey', 'authkey', 'privatetoken']
        const sensitiveProp = attrs.find((a) => SENSITIVE_PROPS.includes(a.name.toLowerCase()))
        if (sensitiveProp) {
          const line = sensitiveProp.position?.start?.line ?? node.position?.start?.line ?? 1
          if (!hasSuppression(lines, line - 1, '02-islands/no-sensitive-props-leak')) {
            diagnostics.push({
              ruleId: '02-islands/no-sensitive-props-leak',
              severity: AST_RULES['02-islands/no-sensitive-props-leak'].severity,
              filePath: relPath,
              line,
              column: sensitiveProp.position?.start?.column ?? 1,
              message: `Gated/sensitive prop "${sensitiveProp.name}" passed to client island <${node.name}> is exposed in public HTML astro-island props attribute.`,
              ref: AST_RULES['02-islands/no-sensitive-props-leak'].ref,
            })
          }
        }
      }

      // Rule: 07-assets/prefer-astro-image
      if (node.name === 'img' && !isPathAllowed('07-assets/prefer-astro-image', relPath)) {
        const line = node.position?.start?.line ?? 1
        if (!hasSuppression(lines, line - 1, '07-assets/prefer-astro-image')) {
          diagnostics.push({
            ruleId: '07-assets/prefer-astro-image',
            severity: AST_RULES['07-assets/prefer-astro-image'].severity,
            filePath: relPath,
            line,
            column: node.position?.start?.column ?? 1,
            message: 'Raw <img> tag used. Consider using <Image /> or <Picture /> from "astro:assets" for automated WebP and responsive sizes.',
            ref: AST_RULES['07-assets/prefer-astro-image'].ref,
          })
        }

        // Rule: 07-assets/require-image-dimensions
        const hasWidth = attrs.some((a) => a.name === 'width')
        const hasHeight = attrs.some((a) => a.name === 'height')
        if ((!hasWidth || !hasHeight) && !isPathAllowed('07-assets/require-image-dimensions', relPath)) {
          if (!hasSuppression(lines, line - 1, '07-assets/require-image-dimensions')) {
            diagnostics.push({
              ruleId: '07-assets/require-image-dimensions',
              severity: AST_RULES['07-assets/require-image-dimensions'].severity,
              filePath: relPath,
              line,
              column: node.position?.start?.column ?? 1,
              message: 'Raw <img> lacks explicit width and height attributes, which causes Cumulative Layout Shift (CLS).',
              ref: AST_RULES['07-assets/require-image-dimensions'].ref,
            })
          }
        }

        // Rule: 07-assets/require-image-alt
        const hasAlt = attrs.some((a) => a.name === 'alt')
        if (!hasAlt && !isPathAllowed('07-assets/require-image-alt', relPath)) {
          if (!hasSuppression(lines, line - 1, '07-assets/require-image-alt')) {
            diagnostics.push({
              ruleId: '07-assets/require-image-alt',
              severity: AST_RULES['07-assets/require-image-alt'].severity,
              filePath: relPath,
              line,
              column: node.position?.start?.column ?? 1,
              message: '<img> element missing required "alt" attribute. Provide descriptive alt text or alt="" for decorative images (WCAG 2.2 SC 1.1.1).',
              ref: AST_RULES['07-assets/require-image-alt'].ref,
            })
          }
        }
      }

      // Rule: 06-security/no-set-html-directive
      const setHtmlAttr = attrs.find((a) => a.name === 'set:html')
      const isJsonScript = node.name === 'script' && attrs.some((a) => a.name === 'type' && a.value?.includes('json'))
      if (setHtmlAttr && !isJsonScript && !isPathAllowed('06-security/no-set-html-directive', relPath)) {
        const line = setHtmlAttr.position?.start?.line ?? node.position?.start?.line ?? 1
        if (!hasSuppression(lines, line - 1, '06-security/no-set-html-directive')) {
          diagnostics.push({
            ruleId: '06-security/no-set-html-directive',
            severity: AST_RULES['06-security/no-set-html-directive'].severity,
            filePath: relPath,
            line,
            column: setHtmlAttr.position?.start?.column ?? 1,
            message: `Raw "set:html" directive on <${node.name}> bypasses Astro HTML escaping and poses an XSS risk. Ensure input is sanitized or use standard Astro expressions.`,
            ref: AST_RULES['06-security/no-set-html-directive'].ref,
          })
        }
      }

      // Rule: 09-perf/no-blanket-viewport-prefetch
      if (node.name === 'a') {
        const prefetchAttr = attrs.find((a) => a.name === 'data-astro-prefetch')
        if (prefetchAttr && (prefetchAttr.value === 'viewport' || prefetchAttr.kind === 'empty')) {
          const line = prefetchAttr.position?.start?.line ?? node.position?.start?.line ?? 1
          if (!hasSuppression(lines, line - 1, '09-perf/no-blanket-viewport-prefetch')) {
            diagnostics.push({
              ruleId: '09-perf/no-blanket-viewport-prefetch',
              severity: AST_RULES['09-perf/no-blanket-viewport-prefetch'].severity,
              filePath: relPath,
              line,
              column: prefetchAttr.position?.start?.column ?? 1,
              message: 'Blanket viewport prefetching detected on link. Prefer data-astro-prefetch="hover" or "tap" to conserve mobile bandwidth.',
              ref: AST_RULES['09-perf/no-blanket-viewport-prefetch'].ref,
            })
          }
        }
      }
    }

    // Children traversal
    if (Array.isArray(node.children)) {
      for (const child of node.children) {
        walk(child, node)
      }
    }
  }

  walk(ast, null)
  return diagnostics
}

// ─── Directory Walker ────────────────────────────────────────────────────────
export function walkAstroFiles(dir, fileList = []) {
  if (!existsSync(dir)) return fileList
  const entries = readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'dist' || entry.name === '.worktrees') {
        continue
      }
      walkAstroFiles(fullPath, fileList)
    } else if (entry.isFile() && entry.name.endsWith('.astro')) {
      fileList.push(fullPath)
    }
  }
  return fileList
}

// ─── Standalone CLI Invocation ───────────────────────────────────────────────
if (process.argv[1] && process.argv[1].endsWith('astro-sentinel-guard.mjs')) {
  async function main() {
    const root = process.cwd()
    const targetDir = join(root, 'src')
    const files = walkAstroFiles(targetDir)
    console.log(`\n🔍 Astro Sentinel AST Guard: Scanning ${files.length} .astro components...\n`)

    const start = performance.now()
    let totalErrors = 0
    let totalWarnings = 0

    for (const file of files) {
      const diags = await lintAstroFile(file, root)
      for (const d of diags) {
        if (d.severity === 'error') totalErrors++
        else totalWarnings++
        const prefix = d.severity === 'error' ? '\x1b[31m✖ ERROR\x1b[0m' : '\x1b[33m▲ WARN\x1b[0m'
        console.log(`${prefix} ${d.filePath}:${d.line}:${d.column} - [${d.ruleId}] ${d.message}`)
      }
    }

    const duration = ((performance.now() - start) / 1000).toFixed(2)
    console.log(`\n── Scanned ${files.length} components in ${duration}s. Found ${totalErrors} error(s), ${totalWarnings} warning(s).\n`)
    process.exit(totalErrors > 0 ? 1 : 0)
  }

  main().catch((err) => {
    console.error('Fatal sentinel guard error:', err)
    process.exit(1)
  })
}
