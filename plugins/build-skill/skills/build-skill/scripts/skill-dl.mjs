#!/usr/bin/env node
/**
 * skill-dl.mjs — Skill discovery, download, and spec inspection tool for build-skill.
 * Node.js ES Module (MJS) implementation conforming to agentskills.io specifications.
 */

import { spawnSync, execSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const VERSION = '3.2.0-mjs';

function printHelp() {
  console.log(`skill-dl.mjs — Skill discovery, download & spec inspection (v${VERSION})

USAGE
  node scripts/skill-dl.mjs <command> [options]

COMMANDS
  search <kw1> [kw2...]        Search skills across skills.sh & GitHub with consensus ranking
  download <source...>         Download one or more skills (URL, file list, or triple)
  inspect <path>               Inspect and validate a skill or corpus against agentskills.io spec
  --where                      Print script location and dependency status as JSON
  --version                    Print version
  --help, -h                   Show this help message

SEARCH OPTIONS
  --top <N>                    Limit output to top N results (default: 20)
  --min-match <N>              Minimum keyword match count (default: 1)
  --json                       Emit results as JSON instead of Markdown table

DOWNLOAD OPTIONS
  -o, --output <dir>           Output directory (default: ./skills-collection)
  -c, --category <name>        Force all skills into this category subfolder
  --no-auto-category           Flat output layout (<output>/<owner>--<repo>--<skill>/)
  -f, --force                  Overwrite existing target directories
  --dry-run                    Preview downloads without cloning

EXAMPLES
  node scripts/skill-dl.mjs search "typescript" "mcp" "testing" --top 10
  node scripts/skill-dl.mjs download https://skills.sh/anthropics/skills/skill-creator -o ./corpus
  node scripts/skill-dl.mjs download https://github.com/anthropics/skills/tree/main/skills/mcp-builder -o ./corpus
  node scripts/skill-dl.mjs download urls.txt -o ./corpus --no-auto-category -f
  node scripts/skill-dl.mjs inspect ./skills/build-skill
  node scripts/skill-dl.mjs inspect ./corpus
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

async function doSearch(keywordsArgs) {
  let topN = 20;
  let minMatch = 1;
  let emitJson = false;
  const keywords = [];

  for (let i = 0; i < keywordsArgs.length; i++) {
    const arg = keywordsArgs[i];
    if (arg === '--top' && keywordsArgs[i + 1]) {
      topN = parseInt(keywordsArgs[++i], 10) || 20;
    } else if (arg === '--min-match' && keywordsArgs[i + 1]) {
      minMatch = parseInt(keywordsArgs[++i], 10) || 1;
    } else if (arg === '--json') {
      emitJson = true;
    } else if (!arg.startsWith('-')) {
      keywords.push(arg);
    }
  }

  if (keywords.length === 0) {
    console.error('Error: Please provide at least one keyword for search.');
    process.exit(1);
  }

  const skillMap = new Map();

  for (const kw of keywords) {
    const proc = spawnSync('npx', ['-y', 'skills', 'find', kw], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 30000
    });

    if (proc.status === 0 && proc.stdout) {
      const parsed = parseSkillsFindOutput(proc.stdout);
      for (const item of parsed) {
        const key = `${item.owner}/${item.repo}/${item.skill}`;
        if (!skillMap.has(key)) {
          skillMap.set(key, {
            ...item,
            matchedKeywords: new Set(),
            matchCount: 0
          });
        }
        const record = skillMap.get(key);
        record.matchedKeywords.add(kw);
        record.matchCount = record.matchedKeywords.size;
      }
    }
  }

  let ranked = Array.from(skillMap.values())
    .filter(r => r.matchCount >= minMatch)
    .sort((a, b) => {
      if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount;
      const parseInstalls = (str) => {
        if (!str || str === 'N/A') return 0;
        const num = parseFloat(str.replace(/[^0-9.]/g, ''));
        if (str.toLowerCase().includes('m')) return num * 1000000;
        if (str.toLowerCase().includes('k')) return num * 1000;
        return num || 0;
      };
      return parseInstalls(b.installs) - parseInstalls(a.installs);
    })
    .slice(0, topN);

  if (emitJson) {
    console.log(JSON.stringify(ranked.map(r => ({
      ...r,
      matchedKeywords: Array.from(r.matchedKeywords)
    })), null, 2));
    return;
  }

  console.log(`\n### Skill Discovery Results (${ranked.length} candidates)\n`);
  if (ranked.length === 0) {
    console.log('No skills matched the search criteria.\n');
    return;
  }

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

  // 1. Match GitHub tree URLs: owner/repo/tree/<branch>/skills/<skill> or owner/repo/tree/<branch>/<skill>
  const ghTreeMatch = clean.match(/^([^/]+)\/([^/]+)\/tree\/[^/]+(?:\/skills|\/.agents\/skills|\/.claude\/skills)?\/(.+)$/);
  if (ghTreeMatch) {
    return { owner: ghTreeMatch[1], repo: ghTreeMatch[2], skill: ghTreeMatch[3] };
  }

  // 2. Match GitHub blob URLs (e.g. pointing to SKILL.md)
  const ghBlobMatch = clean.match(/^([^/]+)\/([^/]+)\/blob\/[^/]+(?:\/skills|\/.agents\/skills|\/.claude\/skills)?\/([^/]+)\/SKILL\.md$/);
  if (ghBlobMatch) {
    return { owner: ghBlobMatch[1], repo: ghBlobMatch[2], skill: ghBlobMatch[3] };
  }

  // 3. Match 3-part spec: owner/repo/skill
  const parts = clean.split('/');
  if (parts.length === 3) {
    return {
      owner: parts[0],
      repo: parts[1],
      skill: parts[2]
    };
  } else if (parts.length === 2 && clean.includes('@')) {
    const [ownerRepo, skill] = clean.split('@');
    if (skill) {
      const [owner, repo] = ownerRepo.split('/');
      return { owner, repo, skill };
    }
  } else if (parts.length > 3) {
    if (parts[2] === 'skills' || parts[2] === '.skills' || parts[2] === '.claude') {
      return { owner: parts[0], repo: parts[1], skill: parts.slice(3).join('/') };
    }
    return { owner: parts[0], repo: parts[1], skill: parts[parts.length - 1] };
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

  // 4. Direct <skillName> (immediate subdirectory)
  const p4 = path.join(cloneDir, skillName);
  if (fs.existsSync(p4) && fs.statSync(p4).isDirectory() && fs.existsSync(path.join(p4, 'SKILL.md'))) return p4;

  // 5. Root level if root is the skill
  const rootSkillMd = path.join(cloneDir, 'SKILL.md');
  if (fs.existsSync(rootSkillMd)) return cloneDir;

  // 6. Recursive search
  const candidates = [];
  function search(dir, depth = 0) {
    if (depth > 4) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        if (entry.name === '.git' || entry.name === 'node_modules') continue;
        if (entry.name === skillName && fs.existsSync(path.join(dir, entry.name, 'SKILL.md'))) {
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
  let forcedCategory = null;
  let flatLayout = false;
  const rawSources = [];

  for (let i = 0; i < args.length; i++) {
    if ((args[i] === '-o' || args[i] === '--output') && args[i + 1]) {
      outputDir = args[++i];
    } else if ((args[i] === '-c' || args[i] === '--category') && args[i + 1]) {
      forcedCategory = args[++i];
    } else if (args[i] === '--no-auto-category') {
      flatLayout = true;
    } else if (args[i] === '-f' || args[i] === '--force') {
      force = true;
    } else if (args[i] === '--dry-run') {
      dryRun = true;
    } else if (!args[i].startsWith('-')) {
      rawSources.push(args[i]);
    }
  }

  if (rawSources.length === 0) {
    console.error('Error: At least one skill source, file, or URL is required.');
    process.exit(1);
  }

  // Expand batch files and stdin
  const sources = [];
  for (const src of rawSources) {
    if (src === '-') {
      const input = fs.readFileSync(0, 'utf8');
      sources.push(...input.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#')));
    } else if (fs.existsSync(src) && fs.statSync(src).isFile()) {
      const lines = fs.readFileSync(src, 'utf8').split('\n');
      sources.push(...lines.map(l => l.trim()).filter(l => l && !l.startsWith('#')));
    } else {
      sources.push(src);
    }
  }

  if (sources.length === 0) {
    console.error('Error: No valid URLs or specs found in provided input.');
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
    repoGroups.get(repoKey).push({ ...parsed, originalUrl: src });
  }

  for (const [repoKey, skillItems] of repoGroups.entries()) {
    console.log(`\n[REPO] Cloning https://github.com/${repoKey}.git ...`);
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-dl-'));

    try {
      if (!dryRun) {
        const cloneProc = spawnSync('git', ['clone', '--depth', '1', `https://github.com/${repoKey}.git`, tempDir], {
          stdio: ['ignore', 'ignore', 'pipe']
        });
        if (cloneProc.status !== 0) {
          throw new Error(cloneProc.stderr ? cloneProc.stderr.toString().trim() : 'git clone failed');
        }
      }

      for (const item of skillItems) {
        const skillName = item.skill;
        const [owner, repo] = repoKey.split('/');
        
        let targetSubdir = `${owner}--${repo}--${skillName}`;
        if (forcedCategory) {
          targetSubdir = path.join(forcedCategory, targetSubdir);
        }

        const destFolder = path.join(outputDir, targetSubdir);
        if (fs.existsSync(destFolder) && !force) {
          console.log(`  [SKIP] ${targetSubdir} already exists in output (use -f to overwrite)`);
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

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return { frontmatter: null, bodyLines: content.split('\n') };

  const endIdx = content.indexOf('\n---', 3);
  if (endIdx === -1) return { frontmatter: null, bodyLines: content.split('\n') };

  const rawFm = content.slice(3, endIdx).trim();
  const body = content.slice(endIdx + 4).trim();

  const lines = rawFm.split('\n');
  const fm = {};
  let currentKey = null;
  let currentSubMap = null;

  for (const line of lines) {
    const subMatch = line.match(/^\s+([a-zA-Z0-9._-]+):\s*(.*)$/);
    if (subMatch && currentKey) {
      if (!currentSubMap) currentSubMap = {};
      currentSubMap[subMatch[1].trim()] = subMatch[2].trim().replace(/^["']|["']$/g, '');
      fm[currentKey] = currentSubMap;
      continue;
    }

    const topMatch = line.match(/^([a-zA-Z0-9._-]+):\s*(.*)$/);
    if (topMatch) {
      currentKey = topMatch[1].trim();
      currentSubMap = null;
      const val = topMatch[2].trim().replace(/^["']|["']$/g, '');
      fm[currentKey] = val;
    }
  }

  return { frontmatter: fm, bodyLines: body.split('\n') };
}

function inspectSingleSkill(absPath) {
  const skillMdPath = path.join(absPath, 'SKILL.md');
  if (!fs.existsSync(skillMdPath)) {
    console.error(`Error: SKILL.md not found in ${absPath}`);
    return false;
  }

  const content = fs.readFileSync(skillMdPath, 'utf8');
  const lines = content.split('\n');
  const { frontmatter, bodyLines } = parseFrontmatter(content);

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

  // Specification validation rules (agentskills.io)
  const issues = [];
  const ALLOWED_FIELDS = ['name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'];
  
  if (frontmatter) {
    // 1. name validation
    if (!frontmatter.name) {
      issues.push("Missing required field 'name'");
    } else {
      const name = frontmatter.name;
      if (typeof name !== 'string' || name.length < 1 || name.length > 64) {
        issues.push(`Field 'name' must be between 1 and 64 characters (current: ${name ? name.length : 0})`);
      }
      if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name)) {
        issues.push(`Field 'name' must be lowercase alphanumeric and hyphens only, cannot start or end with hyphen, no consecutive hyphens: '${name}'`);
      }
      const dirName = path.basename(absPath);
      const expectedSkillName = dirName.includes('--') ? dirName.split('--').pop() : dirName;
      if (expectedSkillName !== name && dirName !== name) {
        issues.push(`Field 'name' ('${name}') does not match directory name ('${expectedSkillName}')`);
      }
    }

    // 2. description validation
    if (!frontmatter.description) {
      issues.push("Missing required field 'description'");
    } else {
      const desc = typeof frontmatter.description === 'string' ? frontmatter.description : String(frontmatter.description);
      if (desc.length < 1 || desc.length > 1024) {
        issues.push(`Field 'description' must be between 1 and 1024 characters (current: ${desc.length})`);
      }
      if (/[<>]/.test(desc)) {
        issues.push("Field 'description' contains forbidden angle brackets ('<' or '>')");
      }
    }

    // 3. compatibility validation
    if (frontmatter.compatibility && frontmatter.compatibility.length > 500) {
      issues.push(`Field 'compatibility' exceeds 500 characters (${frontmatter.compatibility.length} chars)`);
    }

    // 4. allowed-tools validation
    if (frontmatter['allowed-tools']) {
      const tools = frontmatter['allowed-tools'];
      if (typeof tools === 'string' && tools.includes(',')) {
        issues.push("Field 'allowed-tools' must be a space-separated string, NOT comma-separated");
      }
    }

    // 5. unknown fields check
    for (const key of Object.keys(frontmatter)) {
      if (!ALLOWED_FIELDS.includes(key)) {
        issues.push(`Non-spec frontmatter field '${key}' (Agent Skills spec allows only: ${ALLOWED_FIELDS.join(', ')})`);
      }
    }
  } else {
    issues.push('Missing YAML frontmatter delimiters (---) at start of file');
  }

  // 6. sizing recommendation check
  if (lines.length > 500) {
    issues.push(`SKILL.md exceeds recommended 500 lines (${lines.length} lines)`);
  }

  if (issues.length > 0) {
    console.log(`\n⚠️  Specification & Quality Notices (${issues.length}):`);
    issues.forEach(i => console.log(`  - ${i}`));
    return false;
  } else {
    console.log(`\n✅ Conforms cleanly to agentskills.io specification guidelines.`);
    return true;
  }
}

function inspectDirectory(targetPath) {
  const absPath = path.resolve(targetPath);
  if (!fs.existsSync(absPath)) {
    console.error(`Error: Path does not exist: ${absPath}`);
    process.exit(1);
  }

  const skillMdPath = path.join(absPath, 'SKILL.md');
  if (fs.existsSync(skillMdPath)) {
    const ok = inspectSingleSkill(absPath);
    console.log('');
    return ok;
  }

  // Corpus mode: search child directories
  const foundSkillDirs = [];
  function findSkills(dir, depth = 0) {
    if (depth > 3) return;
    try {
      for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
        if (!e.isDirectory()) continue;
        if (e.name === '.git' || e.name === 'node_modules') continue;
        const sub = path.join(dir, e.name);
        if (fs.existsSync(path.join(sub, 'SKILL.md'))) {
          foundSkillDirs.push(sub);
        } else {
          findSkills(sub, depth + 1);
        }
      }
    } catch {}
  }
  findSkills(absPath);

  if (foundSkillDirs.length === 0) {
    console.error(`Error: No skills found (no SKILL.md directly or in subdirectories of ${absPath})`);
    process.exit(1);
  }

  console.log(`\n=== Auditing Corpus: ${foundSkillDirs.length} skill(s) found in ${absPath} ===`);
  let passed = 0;
  for (const sDir of foundSkillDirs) {
    if (inspectSingleSkill(sDir)) passed++;
  }
  console.log(`\nCorpus Audit Summary: ${passed}/${foundSkillDirs.length} skills passed agentskills.io compliance.\n`);
  return passed === foundSkillDirs.length;
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
    inspectDirectory(args[1] || '.');
  } else {
    // Treat bare arguments as search or download
    if (args[0].includes('/') || args[0].includes('http') || args[0].endsWith('.txt') || args[0] === '-') {
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
