#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="${1:-dist}"

node - "$EXT_DIR" <<'NODE'
const fs = require("fs");
const path = require("path");

const root = path.resolve(process.argv[2] || "dist");
const manifestPath = path.join(root, "manifest.json");
const failures = [];
const warnings = [];

function fail(message) {
  failures.push(message);
}

function warn(message) {
  warnings.push(message);
}

function hasGlob(rel) {
  return /[*?[\]{}]/.test(rel);
}

function exists(rel, label, options = {}) {
  if (!rel || typeof rel !== "string") return;
  const normalized = rel.replace(/^\//, "");
  if (/\bsrc\/.+\.(ts|tsx|jsx?)$/i.test(normalized) || /\.(ts|tsx)$/i.test(normalized)) {
    fail(`${label} points at source path: ${rel}`);
  }
  if (options.allowGlob && hasGlob(normalized)) return;
  if (!fs.existsSync(path.join(root, normalized))) {
    fail(`${label} missing: ${rel}`);
  }
}

function checkPathList(values, label, options = {}) {
  if (!Array.isArray(values)) return;
  for (const value of values) exists(value, label, options);
}

if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
  fail(`extension directory not found: ${root}`);
} else if (!fs.existsSync(manifestPath)) {
  fail(`manifest.json not found in ${root}`);
}

let manifest = {};
if (failures.length === 0) {
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch (error) {
    fail(`manifest.json is invalid JSON: ${error.message}`);
  }
}

if (failures.length === 0) {
  if (manifest.manifest_version !== 3) fail("manifest_version must be 3");
  if (typeof manifest.name !== "string" || manifest.name.trim() === "") fail("name is required");
  if (typeof manifest.version !== "string" || manifest.version.trim() === "") fail("version is required");

  if (manifest.background?.scripts) fail("background.scripts is MV2-only; use background.service_worker");
  exists(manifest.background?.service_worker, "background.service_worker");

  exists(manifest.action?.default_popup, "action.default_popup");
  exists(manifest.options_page, "options_page");
  exists(manifest.options_ui?.page, "options_ui.page");
  exists(manifest.side_panel?.default_path, "side_panel.default_path");
  exists(manifest.devtools_page, "devtools_page");

  for (const [size, rel] of Object.entries(manifest.icons || {})) exists(rel, `icons.${size}`);
  for (const [size, rel] of Object.entries(manifest.action?.default_icon || {})) {
    if (typeof rel === "string") exists(rel, `action.default_icon.${size}`);
  }

  for (const [i, script] of (manifest.content_scripts || []).entries()) {
    checkPathList(script.js, `content_scripts[${i}].js`);
    checkPathList(script.css, `content_scripts[${i}].css`);
  }

  const dnr = manifest.declarative_net_request?.rule_resources || [];
  for (const [i, rule] of dnr.entries()) exists(rule.path, `declarative_net_request.rule_resources[${i}].path`);

  const webResources = manifest.web_accessible_resources || [];
  for (const [i, entry] of webResources.entries()) {
    checkPathList(entry.resources, `web_accessible_resources[${i}].resources`, { allowGlob: true });
  }

  const csp = JSON.stringify(manifest.content_security_policy || {});
  if (/\bunsafe-eval\b/.test(csp)) fail("content_security_policy contains unsafe-eval");
  if (/script-src[^;]*(https?:|\/\/)/i.test(csp)) fail("content_security_policy script-src allows remote scripts");

  const manifestText = JSON.stringify(manifest);
  if (/\beval\s*\(|new Function\s*\(/.test(manifestText)) fail("manifest contains inline eval/new Function red flag");
  if (/https?:\/\/[^"']+\.(js|mjs)(["'])/i.test(manifestText)) fail("manifest references a remote script file");

  if (manifest.permissions?.includes("<all_urls>")) warn("permissions includes <all_urls>; justify or narrow it");
  if ((manifest.host_permissions || []).includes("<all_urls>")) warn("host_permissions includes <all_urls>; justify or narrow it");
}

for (const message of warnings) console.log(`WARN ${message}`);
if (failures.length > 0) {
  for (const message of failures) console.error(`FAIL ${message}`);
  process.exit(1);
}

console.log(`PASS MV3 manifest checks: ${path.relative(process.cwd(), manifestPath) || manifestPath}`);
NODE
