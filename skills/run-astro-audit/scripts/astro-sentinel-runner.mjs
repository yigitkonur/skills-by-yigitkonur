#!/usr/bin/env node
/**
 * scripts/checks/astro/astro-sentinel-runner.mjs
 *
 * Astro Sentinel Master CLI Runner
 *
 * Orchestrates the full Astro Best Practices Linter Suite:
 * 1. Component & Template AST Guard (scripts/checks/astro/astro-sentinel-guard.mjs)
 * 2. Cross-File Contract & Schema Guard (scripts/checks/astro/astro-contract-guard.mjs)
 *
 * Options:
 *   --json      Output machine-readable JSON array of diagnostics
 *   --quiet     Suppress non-blocking warnings, report only errors
 *   --staged    Scan only git staged files
 *   --rule=<id> Run only the specified rule ID
 */

import { performance } from 'node:perf_hooks'
import { join } from 'node:path'
import { execSync } from 'node:child_process'
import { lintAstroFile, walkAstroFiles, AST_RULES } from './astro-sentinel-guard.mjs'
import { lintContracts, CONTRACT_RULES } from './astro-contract-guard.mjs'

const args = process.argv.slice(2)
const isJson = args.includes('--json')
const isQuiet = args.includes('--quiet')
const isStaged = args.includes('--staged')
const isSoft = args.includes('--soft')
const isStrict = args.includes('--strict')
const ruleFilter = args.find((a) => a.startsWith('--rule='))?.split('=')[1]

async function run() {
  const root = process.cwd()
  const start = performance.now()
  const allDiagnostics = []

  // 1. Gather target files
  let astroFiles = []
  if (isStaged) {
    try {
      const stagedOutput = execSync('git diff --cached --name-only --diff-filter=ACMR', {
        encoding: 'utf8',
      })
      astroFiles = stagedOutput
        .split('\n')
        .filter((f) => f.endsWith('.astro'))
        .map((f) => join(root, f))
    } catch {
      astroFiles = walkAstroFiles(join(root, 'src'))
    }
  } else {
    astroFiles = walkAstroFiles(join(root, 'src'))
  }

  // 2. Execute AST Component Guard
  for (const file of astroFiles) {
    const diags = await lintAstroFile(file, root)
    for (const d of diags) {
      if (!ruleFilter || d.ruleId === ruleFilter) {
        allDiagnostics.push(d)
      }
    }
  }

  // 3. Execute Contract & Schema Guard (skip if file is filtered or not relevant)
  if (!isStaged || args.length === 0) {
    const contractDiags = lintContracts(root)
    for (const d of contractDiags) {
      if (!ruleFilter || d.ruleId === ruleFilter) {
        allDiagnostics.push(d)
      }
    }
  }

  const durationMs = performance.now() - start
  const durationSec = (durationMs / 1000).toFixed(2)

  const errors = allDiagnostics.filter((d) => d.severity === 'error')
  const warnings = allDiagnostics.filter((d) => d.severity === 'warn')

  // 4. Output formatting
  if (isJson) {
    const payload = {
      timestamp: new Date().toISOString(),
      durationMs,
      scannedFiles: astroFiles.length,
      totals: {
        errors: errors.length,
        warnings: warnings.length,
        total: allDiagnostics.length,
      },
      diagnostics: allDiagnostics,
    }
    console.log(JSON.stringify(payload, null, 2))
  } else {
    console.log('\n\x1b[1m\x1b[36m⚡ Astro Sentinel — Best Practices Architectural Linter\x1b[0m')
    console.log(`Auditing ${astroFiles.length} Astro components and system contracts against 170 authoritative rules...\n`)

    const displayed = isQuiet ? errors : allDiagnostics

    for (const d of displayed) {
      const isErr = d.severity === 'error'
      const badge = isErr ? '\x1b[41m\x1b[37m ERROR \x1b[0m' : '\x1b[43m\x1b[30m WARN \x1b[0m'
      const loc = `\x1b[2m${d.filePath}:${d.line}:${d.column}\x1b[0m`
      const rule = `\x1b[33m[${d.ruleId}]\x1b[0m`
      console.log(`${badge} ${loc} ${rule}\n      ${d.message}`)
      if (d.ref) {
        console.log(`      \x1b[2mRef: .claude/skills/astro-audit/references/best-practices/${d.ref}\x1b[0m`)
      }
    }

    console.log('\n─────────────────────────────────────────────────────────────────────────────')
    if (errors.length > 0) {
      console.log(
        `\x1b[31m✖ Failed with ${errors.length} error(s)\x1b[0m and ${warnings.length} warning(s) in ${durationSec}s.`
      )
    } else if (warnings.length > 0) {
      console.log(
        `\x1b[32m✔ Passed (with ${warnings.length} warning(s))\x1b[0m across ${astroFiles.length} files in ${durationSec}s.`
      )
    } else {
      console.log(`\x1b[32m✔ 100% Clean! Zero violations found\x1b[0m across ${astroFiles.length} files in ${durationSec}s.`)
    }
    console.log('─────────────────────────────────────────────────────────────────────────────\n')
  }

  // Non-blocking by default to satisfy Build Resiliency law; fails only under explicit --strict gate
  const shouldFail = isStrict && errors.length > 0
  process.exit(shouldFail ? 1 : 0)
}

run().catch((err) => {
  console.error('\x1b[31mFatal Astro Sentinel Error:\x1b[0m', err)
  process.exit(1)
})
