#!/usr/bin/env node
/**
 * skill-dl.mjs — Skill discovery, download, and spec inspection tool for build-skill.
 * Node.js ES Module (MJS) implementation conforming to agentskills.io specifications.
 */

import { execSync, spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const VERSION = '3.0.0-mjs';

function printHelp() {
  console.log(`skill-dl.mjs — Skill discovery, download & spec inspection (v${VERSION})

USAGE
  node scripts/skill-dl.mjs <command> [options]

COMMANDS
  search <kw1> [kw2...]        Search skills across skills.sh & GitHub with consensus ranking
  download <source...>         Download one or more skills from skills.sh or GitHub
  inspect <path>               Inspect and validate a downloaded skill against agentskills.io spec
  --where                      Print script location and dependency status as JSON
  --version                    Print version
  --help, -h                   Show this help message

SEARCH OPTIONS
  --top <N>                    Limit output to top N results (default: 20)
  --min-match <N>              Minimum keyword match count (default: 1)
  --json                       Emit results as JSON instead of Markdown table

DOWNLOAD OPTIONS
  -o, --output <dir>           Output directory (default: ./skills-collection)
  -f, --force                  Overwrite existing target directories
  --dry-run                    Preview downloads without cloning

EXAMPLES
  node scripts/skill-dl.mjs search "typescript" "mcp" "testing" --top 10
  node scripts/skill-dl.mjs download https://skills.sh/anthropics/skills/skill-creator -o ./corpus
  node scripts/skill-dl.mjs download anthropics/skills/mcp-builder -o ./corpus
  node scripts/skill-dl.mjs inspect ./corpus/mcp-builder
`);
}

function checkDependencies() {
  const deps = {
    node: process.version,
    git: null,
    npx: null,
    gh: null
  };

  try {
    deps.git = execSync('git --version', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {}
  try {
    deps.npx = execSync('npx --version', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {}
  try {
    deps.gh = execSync('gh --version', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).split('\n')[0].trim();
  } catch {}

  return deps;
}

function stripAnsi(str) {
  return str.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '');
}

function parseSkillsFindOutput(stdout) {
  const clean = stripAnsi(stdout);
  const lines = clean.split('\n');
  const results = [];
  let current = null;

  for (const line of lines) {
    const trimmed = line.trim();
    const headerMatch = trimmed.match(/^([a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+)@([a-zA-Z0-9._-]+)(?:\s+([\d.]+[KkMm]?\s+installs))?/);
    if (headerMatch) {
      if (current) results.push(current);
      const [, ownerRepo, skillName, installs] = headerMatch;
      const [owner, repo] = ownerRepo.split('/');
      current = {
        owner,
        repo,
        skill: skillName,
        installs: installs ? installs.trim() : 'N/A',
        url: `https://skills.sh/${owner}/${repo}/${skillName}`,
        source: 'skills.sh'
      };
      continue;
    }

    const urlMatch = trimmed.match(/https:\/\/skills\.sh\/([^\s]+)/);
    if (urlMatch && current) {
      current.url = urlMatch[0];
    }
  }

  if (current) results.push(current);
  return results;
}

async function searchKeyword(kw) {
  try {
    const res = spawnSync('npx', ['-y', 'skills', 'find', kw], {
      input: '\n',
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
      timeout: 15000
    });
    if (res.stdout) {
      return parseSkillsFindOutput(res.stdout);
    }
  } catch (err) {
    // fallback or fail gracefully
  }
  return [];
}

async function doSearch(args) {
  let top = 20;
  let minMatch = 1;
  let asJson = false;
  const keywords = [];

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--top' && args[i + 1]) {
      top = parseInt(args[++i], 10);
    } else if (args[i] === '--min-match' && args[i + 1]) {
      minMatch = parseInt(args[++i], 10);
    } else if (args[i] === '--json') {
      asJson = true;
    } else if (args[i] === '-h' || args[i] === '--help') {
      printHelp();
      return;
    } else if (!args[i].startsWith('-')) {
      keywords.push(args[i]);
    }
  }

  if (keywords.length === 0) {
    console.error('Error: At least one search keyword is required.');
    process.exit(1);
  }

  const consensusMap = new Map();

  for (const kw of keywords) {
    const hits = await searchKeyword(kw);
    for (const hit of hits) {
      const key = `${hit.owner}/${hit.repo}/${hit.skill}`;
      if (!consensusMap.has(key)) {
        consensusMap.set(key, {
          ...hit,
          matchedKeywords: new Set([kw]),
          matchCount: 1
        });
      } else {
        const item = consensusMap.get(key);
        item.matchedKeywords.add(kw);
        item.matchCount = item.matchedKeywords.size;
        if (hit.installs && hit.installs !== 'N/A') {
          item.installs = hit.installs;
        }
      }
    }
  }

  let ranked = Array.from(consensusMap.values())
    .filter(item => item.matchCount >= minMatch)
    .sort((a, b) => {
      if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount;
      return a.skill.localeCompare(b.skill);
    });

  if (top > 0) {
    ranked = ranked.slice(0, top);
  }

  if (asJson) {
    console.log(JSON.stringify(ranked.map(r => ({
      ...r,
      matchedKeywords: Array.from(r.matchedKeywords)
    })), null, 2));
    return;
  }

  if (ranked.length === 0) {
    console.log('No skills found matching the criteria.');
    return;
  }

  console.log(`\n### Skill Discovery Results (${ranked.length} candidates)\n`);
  console.log('| Rank | Skill | Repository | Matches | Keywords | Installs | URL |');
  console.log('|---|---|---|---|---|---|---|');
  ranked.forEach((r, idx) => {
    const kws = Array.from(r.matchedKeywords).join(', ');
    console.log(`| ${idx + 1} | **${r.skill}** | \`${r.owner}/${r.repo}\` | ${r.matchCount}/${keywords.length} | ${kws} | ${r.installs} | [View](${r.url}) |`);
  });
  console.log('');
}

function parseUrlOrSpec(raw) {
  let clean = raw.trim().replace(/\/$/, '');
  clean = clean.replace(/^https?:\/\/skills\.sh\//, '');
  clean = clean.replace(/^https?:\/\/github\.com\//, '');

  const parts = clean.split('/');
  if (parts.length >= 3) {
    return {
      owner: parts[0],
      repo: parts[1],
      skill: parts[2]
    };
  } else if (parts.length === 2) {
    const [ownerRepo, skill] = clean.split('@');
    if (skill) {
      const [owner, repo] = ownerRepo.split('/');
      return { owner, repo, skill };
    }
  }
  return null;
}

function copyDirectory(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  let fileCount = 0;
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      if (entry.name === '.git' || entry.name === 'node_modules') continue;
      fileCount += copyDirectory(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
      fileCount++;
    }
  }
  return fileCount;
}

function findSkillInRepo(cloneDir, skillName) {
  // 1. Direct skills/<skillName>
  const p1 = path.join(cloneDir, 'skills', skillName);
  if (fs.existsSync(p1) && fs.statSync(p1).isDirectory()) return p1;

  // 2. Direct .agents/skills/<skillName>
  const p2 = path.join(cloneDir, '.agents', 'skills', skillName);
  if (fs.existsSync(p2) && fs.statSync(p2).isDirectory()) return p2;

  // 3. Direct .claude/skills/<skillName>
  const p3 = path.join(cloneDir, '.claude', 'skills', skillName);
  if (fs.existsSync(p3) && fs.statSync(p3).isDirectory()) return p3;

  // 4. Root level if root is the skill
  const rootSkillMd = path.join(cloneDir, 'SKILL.md');
  if (fs.existsSync(rootSkillMd)) return cloneDir;

  // 5. Recursive search
  const candidates = [];
  function search(dir, depth = 0) {
    if (depth > 4) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        if (entry.name === '.git' || entry.name === 'node_modules') continue;
        if (entry.name === skillName) {
          candidates.push(path.join(dir, entry.name));
        } else {
          search(path.join(dir, entry.name), depth + 1);
        }
      }
    } catch {}
  }
  search(cloneDir);
  if (candidates.length > 0) return candidates[0];

  return null;
}

async function doDownload(args) {
  let outputDir = './skills-collection';
  let force = false;
  let dryRun = false;
  const sources = [];

  for (let i = 0; i < args.length; i++) {
    if ((args[i] === '-o' || args[i] === '--output') && args[i + 1]) {
      outputDir = args[++i];
    } else if (args[i] === '-f' || args[i] === '--force') {
      force = true;
    } else if (args[i] === '--dry-run') {
      dryRun = true;
    } else if (!args[i].startsWith('-')) {
      sources.push(args[i]);
    }
  }

  if (sources.length === 0) {
    console.error('Error: At least one skill source or URL is required.');
    process.exit(1);
  }

  fs.mkdirSync(outputDir, { recursive: true });

  console.log(`\nskill-dl.mjs: Downloading ${sources.length} skill(s) into: ${outputDir}`);

  // Group by owner/repo to minimize git clones
  const repoGroups = new Map();
  for (const src of sources) {
    const parsed = parseUrlOrSpec(src);
    if (!parsed) {
      console.warn(`[WARN] Invalid skill spec or URL: ${src}`);
      continue;
    }
    const repoKey = `${parsed.owner}/${parsed.repo}`;
    if (!repoGroups.has(repoKey)) repoGroups.set(repoKey, []);
    repoGroups.get(repoKey).push(parsed.skill);
  }

  for (const [repoKey, skills] of repoGroups.entries()) {
    console.log(`\n[REPO] Cloning https://github.com/${repoKey}.git ...`);
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-dl-'));

    try {
      if (!dryRun) {
        execSync(`git clone --depth 1 "https://github.com/${repoKey}.git" "${tempDir}"`, {
          stdio: ['ignore', 'ignore', 'pipe']
        });
      }

      for (const skillName of skills) {
        const destFolder = path.join(outputDir, skillName);
        if (fs.existsSync(destFolder) && !force) {
          console.log(`  [SKIP] ${skillName} already exists in output (use -f to overwrite)`);
          continue;
        }

        if (dryRun) {
          console.log(`  [DRY-RUN] Would extract ${skillName} -> ${destFolder}`);
          continue;
        }

        const skillSrc = findSkillInRepo(tempDir, skillName);
        if (!skillSrc) {
          console.error(`  [ERR] Skill '${skillName}' not found in repo ${repoKey}`);
          continue;
        }

        const copied = copyDirectory(skillSrc, destFolder);
        console.log(`  [OK] Extracted '${skillName}' (${copied} files) -> ${destFolder}`);
      }
    } catch (err) {
      console.error(`  [FAIL] Failed cloning or processing repo ${repoKey}:`, err.message);
    } finally {
      try {
        fs.rmSync(tempDir, { recursive: true, force: true });
      } catch {}
    }
  }
  console.log('\nDownload complete.\n');
}

function inspectSkill(targetPath) {
  const absPath = path.resolve(targetPath);
  if (!fs.existsSync(absPath)) {
    console.error(`Error: Path does not exist: ${absPath}`);
    process.exit(1);
  }

  const skillMdPath = path.join(absPath, 'SKILL.md');
  if (!fs.existsSync(skillMdPath)) {
    console.error(`Error: SKILL.md not found in ${absPath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(skillMdPath, 'utf8');
  const lines = content.split('\n');

  // Parse frontmatter
  let frontmatter = null;
  let bodyLines = [];
  if (content.startsWith('---')) {
    const parts = content.split('---');
    if (parts.length >= 3) {
      const rawFm = parts[1];
      frontmatter = {};
      rawFm.split('\n').forEach(l => {
        const m = l.match(/^([a-zA-Z0-9._-]+):\s*(.*)$/);
        if (m) {
          frontmatter[m[1].trim()] = m[2].trim().replace(/^["']|["']$/g, '');
        }
      });
      bodyLines = parts.slice(2).join('---').trim().split('\n');
    }
  }

  // Count references
  const refDir = path.join(absPath, 'references');
  let refFiles = [];
  if (fs.existsSync(refDir) && fs.statSync(refDir).isDirectory()) {
    function walk(d) {
      for (const e of fs.readdirSync(d, { withFileTypes: true })) {
        const full = path.join(d, e.name);
        if (e.isDirectory()) walk(full);
        else if (e.name.endsWith('.md')) refFiles.push(path.relative(absPath, full));
      }
    }
    walk(refDir);
  }

  // Count scripts
  const scriptDir = path.join(absPath, 'scripts');
  let scriptFiles = [];
  if (fs.existsSync(scriptDir) && fs.statSync(scriptDir).isDirectory()) {
    scriptFiles = fs.readdirSync(scriptDir).filter(f => !f.startsWith('.'));
  }

  console.log(`\n=== Skill Inspection Report: ${path.basename(absPath)} ===`);
  console.log(`Path: ${absPath}`);
  console.log(`Lines: ${lines.length} (Body: ${bodyLines.length})`);
  console.log(`Size: ${(content.length / 1024).toFixed(1)} KB (~${Math.round(content.length / 4)} tokens)`);
  console.log(`Frontmatter:`, frontmatter);
  console.log(`References (${refFiles.length}):`, refFiles.slice(0, 10));
  if (refFiles.length > 10) console.log(`  ... and ${refFiles.length - 10} more`);
  console.log(`Scripts (${scriptFiles.length}):`, scriptFiles);

  // Spec checks
  const issues = [];
  const ALLOWED_FIELDS = ['name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'];
  if (frontmatter) {
    if (!frontmatter.name) issues.push("Missing required field 'name'");
    if (!frontmatter.description) issues.push("Missing required field 'description'");
    for (const key of Object.keys(frontmatter)) {
      if (!ALLOWED_FIELDS.includes(key)) {
        issues.push(`Non-spec frontmatter field '${key}' (Agent Skills spec allows only: ${ALLOWED_FIELDS.join(', ')})`);
      }
    }
  } else {
    issues.push('Missing YAML frontmatter delimiters (---)');
  }

  if (lines.length > 500) {
    issues.push(`SKILL.md exceeds recommended 500 lines (${lines.length} lines)`);
  }

  if (issues.length > 0) {
    console.log(`\n⚠️  Specification & Quality Notices:`);
    issues.forEach(i => console.log(`  - ${i}`));
  } else {
    console.log(`\n✅ Conforms cleanly to agentskills.io specification guidelines.`);
  }
  console.log('');
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === '--help' || command === '-h') {
    printHelp();
    return;
  }

  if (command === '--version' || command === '-v') {
    console.log(`skill-dl.mjs v${VERSION}`);
    return;
  }

  if (command === '--where') {
    console.log(JSON.stringify({
      version: VERSION,
      scriptPath: __filename,
      nodeVersion: process.version,
      dependencies: checkDependencies()
    }, null, 2));
    return;
  }

  if (command === 'search') {
    await doSearch(args.slice(1));
  } else if (command === 'download') {
    await doDownload(args.slice(1));
  } else if (command === 'inspect') {
    inspectSkill(args[1] || '.');
  } else {
    // Treat bare arguments as search or download
    if (args[0].includes('/') || args[0].includes('http')) {
      await doDownload(args);
    } else {
      await doSearch(args);
    }
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
