#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

function printUsage() {
  console.log(`
Usage:
  node scripts/validate-wave2-research.mjs --tool-data <path-to-tool.json> --criteria <path-to-criteria.json>

Options:
  --tool-data   Path to the subagent's extracted JSON for one tool
  --criteria    Path to the frozen criteria schema definition for this matrix
  --strict      Enforce strict evidence citation on all non-null claims (exit code 1 on missing citations)
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

export function validateToolResearch(toolData, criteriaList, options = {}) {
  const issues = [];
  const warnings = [];

  if (!toolData.id || typeof toolData.id !== 'string') {
    issues.push({ path: 'id', message: 'Missing or invalid candidate tool ID slug' });
  }
  if (!toolData.name || typeof toolData.name !== 'string') {
    issues.push({ path: 'name', message: 'Missing or invalid candidate tool display name' });
  }
  if (!toolData.values || typeof toolData.values !== 'object') {
    issues.push({ path: 'values', message: 'Missing values dictionary' });
    return { success: false, issues, warnings };
  }

  for (const criterion of criteriaList) {
    const raw = toolData.values[criterion.key];
    if (raw === undefined) {
      issues.push({
        path: `values.${criterion.key}`,
        message: `Criterion "${criterion.label}" (${criterion.key}) is missing from tool values`,
      });
      continue;
    }

    // Extract value & detail fields
    const isDetailObject = typeof raw === 'object' && raw !== null && 'value' in raw;
    const value = isDetailObject ? raw.value : raw;
    const confidence = isDetailObject ? raw.confidence : undefined;
    const uncertainty = isDetailObject ? raw.uncertainty : undefined;
    const evidence = isDetailObject ? raw.evidence : undefined;
    const sourceUrl = isDetailObject ? raw.sourceUrl : undefined;

    if (value === null || value === undefined) {
      if (!uncertainty?.isUncertain && !options.allowUnknown) {
        warnings.push({
          path: `values.${criterion.key}`,
          message: `Value is unknown or null without explicit uncertainty flag`,
        });
      }
      continue;
    }

    // Validate Types
    if (criterion.type === 'boolean') {
      if (typeof value !== 'boolean') {
        issues.push({
          path: `values.${criterion.key}.value`,
          message: `Expected boolean (true/false) for "${criterion.label}", got ${typeof value}`,
        });
      }
    } else if (criterion.type === 'number' || criterion.type === 'price') {
      if (typeof value !== 'number' || !Number.isFinite(value)) {
        issues.push({
          path: `values.${criterion.key}.value`,
          message: `Expected finite number for "${criterion.label}", got ${typeof value} (${value})`,
        });
      }
    } else if (criterion.type === 'select') {
      const allowedValues = criterion.options?.map(o => o.value) ?? [];
      if (!allowedValues.includes(value)) {
        issues.push({
          path: `values.${criterion.key}.value`,
          message: `Invalid option "${value}" for "${criterion.label}". Allowed: ${allowedValues.join(', ')}`,
        });
      }
    } else if (criterion.type === 'multiselect') {
      const allowedValues = criterion.options?.map(o => o.value) ?? [];
      if (!Array.isArray(value)) {
        issues.push({
          path: `values.${criterion.key}.value`,
          message: `Expected array of options for multiselect "${criterion.label}"`,
        });
      } else {
        for (const item of value) {
          if (!allowedValues.includes(item)) {
            issues.push({
              path: `values.${criterion.key}.value`,
              message: `Invalid multiselect item "${item}" for "${criterion.label}". Allowed: ${allowedValues.join(', ')}`,
            });
          }
        }
      }
    }

    // Anti-Hallucination Evidence & Confidence Checks
    const confidenceScore =
      typeof confidence === 'number'
        ? confidence
        : typeof confidence === 'object' && confidence !== null
        ? confidence.score
        : undefined;

    if (confidenceScore !== undefined && (confidenceScore < 0 || confidenceScore > 1)) {
      issues.push({
        path: `values.${criterion.key}.confidence`,
        message: `Confidence score must be between 0.0 and 1.0, got ${confidenceScore}`,
      });
    }

    // If claiming high confidence (> 0.8), require a citation URL or evidence quote
    if (confidenceScore !== undefined && confidenceScore >= 0.8) {
      const hasSourceUrl = sourceUrl || (typeof evidence === 'object' && evidence?.sourceUrl);
      const hasQuote = (typeof evidence === 'string' && evidence.length > 5) || (typeof evidence === 'object' && evidence?.quote);

      if (!hasSourceUrl && !hasQuote) {
        issues.push({
          path: `values.${criterion.key}.evidence`,
          message: `High confidence claim (${(confidenceScore * 100).toFixed(0)}%) for "${criterion.label}" requires citation sourceUrl or evidence quote to prevent hallucination`,
        });
      }
    }

    // If uncertain, must explain why
    if (uncertainty?.isUncertain && !uncertainty?.reason) {
      warnings.push({
        path: `values.${criterion.key}.uncertainty`,
        message: `Marked uncertain without explanatory reason in uncertainty.reason`,
      });
    }
  }

  return {
    success: issues.length === 0,
    issues,
    warnings,
  };
}

function main() {
  const args = parseArgs();
  if (!args['tool-data'] || !args.criteria) {
    printUsage();
    process.exit(1);
  }

  const toolDataPath = path.resolve(process.cwd(), args['tool-data']);
  const criteriaPath = path.resolve(process.cwd(), args.criteria);

  if (!fs.existsSync(toolDataPath)) {
    console.error(`❌ Tool data file not found: ${toolDataPath}`);
    process.exit(1);
  }
  if (!fs.existsSync(criteriaPath)) {
    console.error(`❌ Criteria definition file not found: ${criteriaPath}`);
    process.exit(1);
  }

  const toolData = JSON.parse(fs.readFileSync(toolDataPath, 'utf-8'));
  const criteriaData = JSON.parse(fs.readFileSync(criteriaPath, 'utf-8'));
  const criteriaList = Array.isArray(criteriaData) ? criteriaData : criteriaData.criteria ?? [];

  const result = validateToolResearch(toolData, criteriaList, { allowUnknown: !args.strict });

  if (!result.success) {
    console.error(`❌ Validation FAILED for tool "${toolData.name ?? toolData.id}" with ${result.issues.length} error(s):`);
    for (const issue of result.issues) {
      console.error(`   - [${issue.path}]: ${issue.message}`);
    }
    if (result.warnings.length > 0) {
      console.warn(`⚠️ Warnings:`);
      for (const w of result.warnings) {
        console.warn(`   - [${w.path}]: ${w.message}`);
      }
    }
    process.exit(1);
  }

  console.log(`✅ Wave 2 research validation PASSED for "${toolData.name}" (${toolData.id})!`);
  if (result.warnings.length > 0) {
    console.log(`   Warnings: ${result.warnings.length}`);
  }
}

// Run CLI when invoked directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
