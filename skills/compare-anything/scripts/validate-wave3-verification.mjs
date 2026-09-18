#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

function printUsage() {
  console.log(`
Usage:
  node scripts/validate-wave3-verification.mjs --tool-data <path-to-verified-tool.json>

Options:
  --tool-data   Path to the subagent's verified JSON for one tool
`);
}

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith('--')) {
        options[key] = next;
        i++;
      } else {
        options[key] = true;
      }
    }
  }
  return options;
}

export function validateToolVerification(toolData) {
  const issues = [];
  const warnings = [];

  if (!toolData.values || typeof toolData.values !== 'object') {
    issues.push({ path: 'values', message: 'Missing values dictionary' });
    return { success: false, issues, warnings };
  }

  let auditedCount = 0;
  let correctedCount = 0;
  let uncertaintyCount = 0;

  for (const [key, raw] of Object.entries(toolData.values)) {
    if (typeof raw !== 'object' || raw === null) continue;

    const audit = raw.verificationAudit;
    const uncertainty = raw.uncertainty;

    if (audit) {
      auditedCount++;
      if (audit.status === 'corrected' && !audit.notes) {
        issues.push({
          path: `values.${key}.verificationAudit`,
          message: `Audit status marked as 'corrected' but missing explanation notes`,
        });
      }
      if (audit.status === 'corrected') {
        correctedCount++;
      }
    }

    if (uncertainty?.isUncertain) {
      uncertaintyCount++;
      if (!uncertainty.reason) {
        warnings.push({
          path: `values.${key}.uncertainty`,
          message: `Uncertainty flag is true but reason is empty`,
        });
      }
    }
  }

  return {
    success: issues.length === 0,
    issues,
    warnings,
    stats: {
      auditedCount,
      correctedCount,
      uncertaintyCount,
    },
  };
}

function main() {
  const args = parseArgs();
  if (!args['tool-data']) {
    printUsage();
    process.exit(1);
  }

  const toolDataPath = path.resolve(process.cwd(), args['tool-data']);
  if (!fs.existsSync(toolDataPath)) {
    console.error(`❌ Tool data file not found: ${toolDataPath}`);
    process.exit(1);
  }

  const toolData = JSON.parse(fs.readFileSync(toolDataPath, 'utf-8'));
  const result = validateToolVerification(toolData);

  if (!result.success) {
    console.error(`❌ Wave 3 verification audit failed for "${toolData.name ?? toolData.id}":`);
    for (const issue of result.issues) {
      console.error(`   - [${issue.path}]: ${issue.message}`);
    }
    process.exit(1);
  }

  console.log(`✅ Wave 3 verification audit PASSED for "${toolData.name ?? toolData.id}"!`);
  console.log(`   Audited Cells     : ${result.stats.auditedCount}`);
  console.log(`   Corrected Entries : ${result.stats.correctedCount}`);
  console.log(`   Unresolved Items  : ${result.stats.uncertaintyCount}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
