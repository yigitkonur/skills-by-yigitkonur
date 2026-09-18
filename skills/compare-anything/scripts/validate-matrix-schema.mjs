#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { z } from 'zod';

const criterionTypeSchema = z.enum([
  'boolean',
  'number',
  'price',
  'select',
  'select-text',
  'multiselect',
  'text',
  'url',
  'date',
  'computed',
]);

const criterionOptionSchema = z.object({
  value: z.string(),
  label: z.string(),
  rank: z.number().optional(),
});

const criterionDefinitionSchema = z.object({
  key: z.string().regex(/^[a-zA-Z0-9_-]+$/),
  label: z.string(),
  groupId: z.string(),
  type: criterionTypeSchema,
  unit: z.string().optional(),
  description: z.string().optional(),
  placeholder: z.string().optional(),
  options: z.array(criterionOptionSchema).optional(),
  required: z.boolean().optional(),
  scoreable: z.boolean().default(true),
  higherIsBetter: z.boolean().optional(),
  booleanBest: z.boolean().optional(),
  defaultWeight: z.number().min(0).max(10).default(5),
  isHardRequirement: z.boolean().optional(),
  evidenceRequired: z.boolean().optional(),
});

const criteriaGroupSchema = z.object({
  id: z.string(),
  label: z.string(),
  description: z.string().optional(),
  defaultExpanded: z.boolean().default(true),
  parentGroupId: z.string().optional(),
});

const confidenceDetailSchema = z.object({
  score: z.number().min(0).max(1),
  level: z.enum(['high', 'medium', 'low']).optional(),
  tier: z.enum(['verified', 'vendor-claimed', 'community', 'unverified']).default('unverified'),
});

const uncertaintyDetailSchema = z.object({
  isUncertain: z.boolean().default(false),
  reason: z.string().optional(),
  conflictingSources: z.array(z.string()).optional(),
});

const predictionDetailSchema = z.object({
  isEstimate: z.boolean().default(false),
  range: z.tuple([z.number(), z.number()]).optional(),
  rationale: z.string().optional(),
});

const evidenceDetailSchema = z.object({
  quote: z.string().optional(),
  sourceUrl: z.string().url().optional(),
  verifiedAt: z.string().optional(),
  verifierAgent: z.string().optional(),
});

const verificationAuditSchema = z.object({
  status: z.enum(['confirmed', 'corrected', 'unresolvable']).default('confirmed'),
  notes: z.string().optional(),
  auditedAt: z.string().optional(),
  verifierAgent: z.string().optional(),
});

const comparisonItemSchema = z.object({
  id: z.string().regex(/^[a-zA-Z0-9_-]+$/),
  name: z.string(),
  website: z.string().url().optional(),
  accent: z.string().regex(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/),
  icon: z.string().optional(),
  summary: z.string().optional(),
  tags: z.array(z.string()).default([]),
  values: z.record(z.string(), z.unknown()),
});

const comparisonMatrixSchema = z.object({
  id: z.string().regex(/^[a-zA-Z0-9_-]+$/),
  title: z.string(),
  description: z.string(),
  subjectLabel: z.string().default('Items'),
  groups: z.array(criteriaGroupSchema),
  criteria: z.array(criterionDefinitionSchema),
  items: z.array(comparisonItemSchema),
  scoring: z
    .object({
      algorithm: z.enum(['linear-normalized', 'weighted-sum']).default('linear-normalized'),
      defaultWeights: z.record(z.string(), z.number()).optional(),
    })
    .optional(),
  metadata: z
    .object({
      lastUpdatedAt: z.string().optional(),
      version: z.string().optional(),
      curator: z.string().optional(),
      sourceDocumentCount: z.number().optional(),
      methodologyUrl: z.string().optional(),
      waveStats: z
        .object({
          discoveredCandidates: z.number().optional(),
          expandedCriteriaCount: z.number().optional(),
          verifiedEvidenceRatio: z.number().optional(),
          uncertaintyCount: z.number().optional(),
        })
        .optional(),
    })
    .optional(),
});

function main() {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('Usage: node validate-matrix-schema.mjs <path-to-matrix.json>');
    process.exit(1);
  }

  const resolved = path.resolve(process.cwd(), filePath);
  if (!fs.existsSync(resolved)) {
    console.error(`❌ File not found: ${resolved}`);
    process.exit(1);
  }

  let data;
  try {
    const raw = fs.readFileSync(resolved, 'utf-8');
    data = JSON.parse(raw);
  } catch (err) {
    console.error(`❌ Invalid JSON syntax in ${resolved}:`, err.message);
    process.exit(1);
  }

  const result = comparisonMatrixSchema.safeParse(data);
  if (!result.success) {
    console.error(`❌ Schema validation FAILED with ${result.error.issues.length} issue(s):`);
    for (const issue of result.error.issues) {
      console.error(`   - [${issue.path.join('.')}] ${issue.message}`);
    }
    process.exit(1);
  }

  // Cross-reference integrity check:
  const groupIds = new Set(data.groups.map(g => g.id));
  const criteriaKeys = new Set(data.criteria.map(c => c.key));

  let crossRefErrors = 0;
  for (const criterion of data.criteria) {
    if (!groupIds.has(criterion.groupId)) {
      console.error(`❌ Criterion "${criterion.key}" references non-existent groupId: "${criterion.groupId}"`);
      crossRefErrors++;
    }
  }

  let totalCells = 0;
  let evidencedCells = 0;
  let uncertainCells = 0;

  for (const item of data.items) {
    for (const [key, val] of Object.entries(item.values)) {
      if (!criteriaKeys.has(key)) {
        console.warn(`⚠️ Warning: Item "${item.id}" defines unknown value key "${key}" not in criteria`);
      }
      totalCells++;
      if (typeof val === 'object' && val !== null) {
        if ('evidence' in val || 'sourceUrl' in val) evidencedCells++;
        if ('uncertainty' in val && val.uncertainty?.isUncertain) uncertainCells++;
      }
    }
  }

  if (crossRefErrors > 0) {
    process.exit(1);
  }

  console.log(`✅ Matrix schema VALID!`);
  console.log(`   Title          : ${data.title}`);
  console.log(`   Items          : ${data.items.length}`);
  console.log(`   Groups         : ${data.groups.length}`);
  console.log(`   Criteria       : ${data.criteria.length}`);
  console.log(`   Evidenced Cells: ${evidencedCells}/${totalCells} (${totalCells > 0 ? ((evidencedCells / totalCells) * 100).toFixed(1) : 0}%)`);
  console.log(`   Uncertain Cells: ${uncertainCells}`);
}

main();
