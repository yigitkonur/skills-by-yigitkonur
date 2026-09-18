#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { z } from 'zod';

const PALETTE = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
  '#f97316', // orange
  '#6366f1', // indigo
];

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
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

function printUsage() {
  console.log(`
Usage:
  node scripts/scaffold-matrix.mjs --slug <slug> --title "<title>" --items "Item 1, Item 2, Item 3" [options]
  node scripts/scaffold-matrix.mjs --from <draft-file.json> [--slug <slug>]

Options:
  --slug        Unique identifier for the matrix (e.g. vector-databases)
  --title       Human readable title (e.g. "Vector Databases Comparison")
  --description Short summary paragraph of the benchmark / evaluation
  --subject     Singular/plural subject label (e.g. "Databases", default: "Items")
  --items       Comma-separated item names (e.g. "Pinecone, Qdrant, Weaviate, Milvus")
  --from        Path to a draft or seed JSON file to normalize and scaffold
  --output      Target output file (defaults to content/matrix/<slug>.json)
`);
}

function main() {
  const args = parseArgs();

  if (args.help || (!args.slug && !args.from)) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  let matrixData;

  if (args.from) {
    const seedPath = path.resolve(process.cwd(), args.from);
    if (!fs.existsSync(seedPath)) {
      console.error(`❌ Seed file not found: ${seedPath}`);
      process.exit(1);
    }
    const raw = JSON.parse(fs.readFileSync(seedPath, 'utf-8'));
    matrixData = raw;
    if (args.slug) matrixData.id = slugify(args.slug);
    if (args.title) matrixData.title = args.title;
  } else {
    const slug = slugify(args.slug);
    const title = args.title || slug.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join(' ') + ' Comparison';
    const subject = args.subject || 'Items';
    const itemNames = (args.items || 'Candidate A, Candidate B, Candidate C')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const defaultGroups = [
      { id: 'general', label: 'General & Architecture', defaultExpanded: true },
      { id: 'capabilities', label: 'Core Capabilities', defaultExpanded: true },
      { id: 'performance', label: 'Performance & Scale', defaultExpanded: true },
      { id: 'pricing', label: 'Pricing & Licensing', defaultExpanded: true },
    ];

    const defaultCriteria = [
      {
        key: 'isOpenSource',
        label: 'Open Source',
        groupId: 'general',
        type: 'boolean',
        booleanBest: true,
        defaultWeight: 6,
        description: 'Available under a permissive open source license',
      },
      {
        key: 'deploymentModel',
        label: 'Deployment Model',
        groupId: 'general',
        type: 'select',
        options: [
          { value: 'cloud-managed', label: 'Cloud Managed', rank: 9 },
          { value: 'hybrid', label: 'Hybrid / Self-Hosted', rank: 8 },
          { value: 'embedded', label: 'Embedded / Local', rank: 7 },
        ],
        defaultWeight: 5,
      },
      {
        key: 'supportedRuntimes',
        label: 'SDK Support',
        groupId: 'capabilities',
        type: 'multiselect',
        options: [
          { value: 'typescript', label: 'TypeScript / Node' },
          { value: 'python', label: 'Python' },
          { value: 'go', label: 'Go' },
          { value: 'rust', label: 'Rust' },
        ],
        defaultWeight: 6,
      },
      {
        key: 'p99LatencyMs',
        label: 'P99 Latency',
        groupId: 'performance',
        type: 'number',
        unit: 'ms',
        higherIsBetter: false,
        defaultWeight: 8,
        description: 'Query latency at 99th percentile under load',
      },
      {
        key: 'monthlyPrice',
        label: 'Base Monthly Price',
        groupId: 'pricing',
        type: 'price',
        unit: '/mo',
        higherIsBetter: false,
        defaultWeight: 7,
      },
    ];

    const items = itemNames.map((name, index) => {
      const id = slugify(name);
      return {
        id,
        name,
        accent: PALETTE[index % PALETTE.length],
        website: `https://${id}.example.com`,
        summary: `${name} is an enterprise-grade solution for modern engineering stacks.`,
        tags: ['Cloud', 'Production'],
        values: {
          isOpenSource: index % 2 === 0,
          deploymentModel: index === 0 ? 'cloud-managed' : 'hybrid',
          supportedRuntimes: ['typescript', 'python'],
          p99LatencyMs: 12 + index * 8,
          monthlyPrice: index === 0 ? 0 : 49 + index * 20,
        },
      };
    });

    matrixData = {
      id: slug,
      title,
      description: args.description || `Empirical benchmark and feature comparison matrix for leading ${subject.toLowerCase()}.`,
      subjectLabel: subject,
      groups: defaultGroups,
      criteria: defaultCriteria,
      items,
      metadata: {
        lastUpdatedAt: new Date().toISOString().split('T')[0],
        version: '1.0.0',
        curator: 'Antigravity Automated Benchmark',
      },
    };
  }

  const outPath = args.output
    ? path.resolve(process.cwd(), args.output)
    : path.resolve(process.cwd(), `content/matrix/${matrixData.id}.json`);

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(matrixData, null, 2) + '\n');

  console.log(`✅ Scaffolding complete!`);
  console.log(`   Target file : ${outPath}`);
  console.log(`   Matrix ID   : ${matrixData.id}`);
  console.log(`   Candidates  : ${matrixData.items.map(it => it.name).join(', ')}`);
  console.log(`\nTo validate, run:`);
  console.log(`   node .agents/skills/compare-anything/scripts/validate-matrix-schema.mjs ${outPath}`);
  console.log(`\nTo view in browser, start dev server and open:`);
  console.log(`   http://127.0.0.1:4321/compare/${matrixData.id}/\n`);
}

main();
