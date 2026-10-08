#!/usr/bin/env node
/**
 * skill-research.mjs — End-to-end multi-angle discovery, downloading, and corpus inspection.
 * Node.js ES Module (MJS) implementation for the build-skill research phase.
 */

import { spawnSync, execSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SKILL_DL = path.join(__dirname, 'skill-dl.mjs');

function printHelp() {
  console.log(`skill-research.mjs — Multi-angle skill research runner

USAGE
  node scripts/skill-research.mjs "<keyword1>,<keyword2>,..." [output-dir] [top-n]

ARGUMENTS
  "<keywords>"     Comma-separated list of 2-20 search keywords/phrases
  [output-dir]     Corpus output directory (default: ./skill-research-corpus)
  [top-n]          Maximum candidate skills to download (default: 5)

EXAMPLES
  node scripts/skill-research.mjs "typescript,mcp,server,testing" ./corpus 3
  node scripts/skill-research.mjs "react,state,performance" ./research-corpus 5
`);
}

async function run() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args[0] === '-h' || args[0] === '--help') {
    printHelp();
    return;
  }

  const rawKeywords = args[0];
  const outputDir = path.resolve(args[1] || './skill-research-corpus');
  const topN = parseInt(args[2] || '5', 10);

  const keywords = rawKeywords.split(',').map(k => k.trim()).filter(Boolean);
  if (keywords.length < 2) {
    console.error('Error: Please provide at least 2 distinct keywords separated by commas.');
    process.exit(1);
  }

  console.log(`\n=== Starting Skill Research Pipeline ===`);
  console.log(`Keywords: [${keywords.join(', ')}]`);
  console.log(`Output Corpus: ${outputDir}`);
  console.log(`Top Candidates to Download: ${topN}\n`);

  // Step 1: Run multi-angle search via skill-dl.mjs
  console.log(`[Phase 1] Executing multi-angle discovery...`);
  const searchArgs = [SKILL_DL, 'search', ...keywords, '--top', String(topN * 2), '--json'];
  const searchRes = spawnSync('node', searchArgs, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] });

  let candidates = [];
  try {
    candidates = JSON.parse(searchRes.stdout);
  } catch (err) {
    console.warn('[WARN] Could not parse structured search JSON. Falling back to stdout preview.');
  }

  if (!candidates || candidates.length === 0) {
    console.log('No matching remote skills found on skills.sh registry.');
    return;
  }

  console.log(`Found ${candidates.length} candidate skills.`);
  const toDownload = candidates.slice(0, topN);

  // Step 2: Download candidates
  console.log(`\n[Phase 2] Downloading top ${toDownload.length} candidates into corpus...`);
  fs.mkdirSync(outputDir, { recursive: true });

  const specs = toDownload.map(c => `${c.owner}/${c.repo}/${c.skill}`);
  const dlRes = spawnSync('node', [SKILL_DL, 'download', ...specs, '-o', outputDir, '-f'], {
    stdio: 'inherit'
  });

  // Step 3: Inspect downloaded corpus
  console.log(`\n[Phase 3] Inspecting downloaded corpus...`);
  const corpusEntries = fs.readdirSync(outputDir, { withFileTypes: true });

  for (const entry of corpusEntries) {
    if (!entry.isDirectory()) continue;
    const skillPath = path.join(outputDir, entry.name);
    const skillMdPath = path.join(skillPath, 'SKILL.md');
    if (!fs.existsSync(skillMdPath)) continue;

    console.log(`\n--- Inspecting: ${entry.name} ---`);
    spawnSync('node', [SKILL_DL, 'inspect', skillPath], { stdio: 'inherit' });
  }

  console.log(`\n=== Skill Research Pipeline Completed Successfully ===\n`);
}

run().catch(err => {
  console.error('Pipeline failed:', err);
  process.exit(1);
});
