#!/usr/bin/env node
// build-docs.mjs — auto-generate scripts/<name>.md from each script's --help
// output plus a hand-written WHY block.
//
// Why this exists: the run-codex-1 audit (Phase 0 captured at
// /tmp/run-codex-1-audit/MASTER-REPORT.md) found 595 misinformation
// findings across 22 .md docs because they were maintained by hand against
// code that evolved. This tool inverts the relationship: the script source's
// --help output is the canonical documentation, regenerated mechanically.
// Hand-edited content is confined to a <!-- BEGIN WHY --> ... <!-- END WHY -->
// block per file.
//
// CI gate:
//   node build-docs.mjs --check    # exit non-zero if any committed .md
//                                  # differs from regenerated; ensures docs
//                                  # match source.
//
// Operator commands:
//   node build-docs.mjs --update             # rewrite all .md files
//   node build-docs.mjs --update --script audit.py   # one file only
//   node build-docs.mjs --list               # list scripts that have docs
//   node build-docs.mjs --help               # this message

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { dirname, join, basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCRIPTS_DIR = __dirname;

const BEGIN_AUTO = "<!-- AUTO-GENERATED — DO NOT EDIT BETWEEN MARKERS -->";
const BEGIN_HELP = "<!-- BEGIN HELP -->";
const END_HELP = "<!-- END HELP -->";
const BEGIN_WHY = "<!-- BEGIN WHY -->";
const END_WHY = "<!-- END WHY -->";
const END_AUTO = "<!-- END AUTO-GENERATED -->";

const DEFAULT_WHY = (name) => `
## Why this script exists

(WHY block placeholder. Replace this paragraph with a short narrative — the
why, when to use it, and cross-references. Argument tables and exit codes
belong in the --help section above, not here.)

This block is hand-written and preserved across regenerations. The
<!-- BEGIN HELP --> / <!-- END HELP --> block above is regenerated from
\`${name} --help\` by build-docs.mjs.
`.trim();

function parseArgs(argv) {
  const args = { mode: null, script: null, check: false, list: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--check") { args.mode = "check"; args.check = true; }
    else if (a === "--update") { args.mode = "update"; }
    else if (a === "--list") { args.mode = "list"; args.list = true; }
    else if (a === "--script") { args.script = argv[++i]; }
    else if (a === "--help" || a === "-h") {
      console.log("build-docs.mjs --check | --update [--script <name>] | --list");
      process.exit(0);
    } else {
      console.error(`unknown flag: ${a}`);
      process.exit(2);
    }
  }
  if (!args.mode) args.mode = "check";
  return args;
}

const args = parseArgs(process.argv);

function listScripts() {
  return readdirSync(SCRIPTS_DIR)
    .filter(f => /\.(py|sh|mjs)$/.test(f))
    .filter(f => !f.startsWith("_"))            // skip _lib.sh / _lib.py
    .filter(f => !f.startsWith("test-"))       // skip legacy test shims
    .filter(f => !f.includes("__fixtures__"))
    .filter(f => f !== "build-docs.mjs")
    .filter(f => f !== "verify-help-doc-sync.mjs")
    .sort();
}

function helpFor(scriptFile) {
  const path = join(SCRIPTS_DIR, scriptFile);
  const interp = scriptFile.endsWith(".py") ? "python3"
               : scriptFile.endsWith(".mjs") ? "node"
               : "bash";
  const r = spawnSync(interp, [path, "--help"], { encoding: "utf8", timeout: 5000 });
  // Some scripts emit --help to stderr; pick whichever is non-empty.
  return (r.stdout && r.stdout.trim()) || (r.stderr && r.stderr.trim()) || "";
}

function extractWhy(mdContent) {
  if (!mdContent) return null;
  const i = mdContent.indexOf(BEGIN_WHY);
  const j = mdContent.indexOf(END_WHY);
  if (i < 0 || j < 0 || j < i) return null;
  return mdContent.slice(i + BEGIN_WHY.length, j).trim();
}

function generateMd(scriptFile, helpText, whyText) {
  return `${BEGIN_AUTO}
${BEGIN_HELP}
\`\`\`
${helpText}
\`\`\`
${END_HELP}

${BEGIN_WHY}
${whyText || DEFAULT_WHY(scriptFile)}
${END_WHY}
${END_AUTO}
`;
}

function diff(a, b) {
  // Simple diff: line-by-line, return first N differences.
  const al = a.split("\n");
  const bl = b.split("\n");
  const out = [];
  const max = Math.max(al.length, bl.length);
  for (let i = 0; i < max && out.length < 5; i++) {
    if (al[i] !== bl[i]) {
      out.push(`  line ${i + 1}: '-${al[i] ?? ""}' / '+${bl[i] ?? ""}'`);
    }
  }
  return out.join("\n");
}

function process_script(scriptFile, mode) {
  const mdPath = join(SCRIPTS_DIR, scriptFile.replace(/\.(py|sh|mjs)$/, ".md"));
  const existingMd = existsSync(mdPath) ? readFileSync(mdPath, "utf8") : "";
  const whyText = extractWhy(existingMd);
  const help = helpFor(scriptFile);
  if (!help) {
    return { script: scriptFile, status: "skipped", reason: "no --help output" };
  }
  const generated = generateMd(scriptFile, help, whyText);

  if (mode === "update") {
    writeFileSync(mdPath, generated, "utf8");
    return { script: scriptFile, status: "wrote", path: mdPath, bytes: generated.length };
  }
  // mode === "check"
  if (existingMd === generated) {
    return { script: scriptFile, status: "ok", path: mdPath };
  }
  return {
    script: scriptFile,
    status: "drift",
    path: mdPath,
    diff: diff(existingMd, generated),
  };
}

const scripts = args.script ? [args.script] : listScripts();

if (args.mode === "list") {
  for (const s of scripts) console.log(s);
  process.exit(0);
}

let driftCount = 0;
let wroteCount = 0;
let skippedCount = 0;
for (const s of scripts) {
  const r = process_script(s, args.mode);
  if (r.status === "drift") {
    console.log(`DRIFT ${r.script} → ${r.path}`);
    console.log(r.diff);
    driftCount++;
  } else if (r.status === "wrote") {
    console.log(`UPDATE ${r.script}`);
    wroteCount++;
  } else if (r.status === "skipped") {
    console.log(`SKIP ${r.script}: ${r.reason}`);
    skippedCount++;
  }
}

if (args.mode === "check") {
  if (driftCount > 0) {
    console.log(`\n${driftCount} doc(s) drift from --help output. Run: node build-docs.mjs --update`);
    process.exit(1);
  }
  console.log(`\nAll docs in sync (${scripts.length - skippedCount} checked, ${skippedCount} skipped)`);
} else if (args.mode === "update") {
  console.log(`\nWrote ${wroteCount} doc(s); ${skippedCount} skipped`);
}
process.exit(0);
