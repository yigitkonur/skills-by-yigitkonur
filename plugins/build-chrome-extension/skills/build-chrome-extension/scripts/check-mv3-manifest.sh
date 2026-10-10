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

function isHostPattern(pattern) {
  if (typeof pattern !== "string") return false;
  return pattern === "<all_urls>" || /^((\*|https?|file|ftp):\/\/|\*:\/\/\/)/.test(pattern) || pattern.includes("://");
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
  const versionRegex = /^(0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])(\.(0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])){0,3}$/;
  if (typeof manifest.version !== "string" || manifest.version.trim() === "") {
    fail("version is required");
  } else if (!versionRegex.test(manifest.version)) {
    fail(`version "${manifest.version}" is invalid: Chrome requires 1-4 dot-separated integers (0-65535) with no leading zeros`);
  }

  // MV2 legacy key checks
  if (manifest.background?.scripts) fail("background.scripts is MV2-only; use background.service_worker");
  if (manifest.background?.page) fail("background.page is MV2-only; use background.service_worker");
  if (manifest.browser_action) fail("browser_action is MV2-only; use action");
  if (manifest.page_action) fail("page_action is MV2-only; use action");

  exists(manifest.background?.service_worker, "background.service_worker");

  exists(manifest.action?.default_popup, "action.default_popup");
  exists(manifest.options_page, "options_page");
  exists(manifest.options_ui?.page, "options_ui.page");
  exists(manifest.side_panel?.default_path, "side_panel.default_path");
  exists(manifest.devtools_page, "devtools_page");

  if (typeof manifest.icons === "object" && manifest.icons !== null) {
    for (const [size, rel] of Object.entries(manifest.icons)) exists(rel, `icons.${size}`);
  }

  if (typeof manifest.action?.default_icon === "string") {
    exists(manifest.action.default_icon, "action.default_icon");
  } else if (typeof manifest.action?.default_icon === "object" && manifest.action?.default_icon !== null) {
    for (const [size, rel] of Object.entries(manifest.action.default_icon)) {
      if (typeof rel === "string") exists(rel, `action.default_icon.${size}`);
    }
  }

  for (const [i, script] of (manifest.content_scripts || []).entries()) {
    if (!Array.isArray(script.matches) || script.matches.length === 0) {
      fail(`content_scripts[${i}].matches must be a non-empty array of match patterns`);
    }
    checkPathList(script.js, `content_scripts[${i}].js`);
    checkPathList(script.css, `content_scripts[${i}].css`);
  }

  const dnr = manifest.declarative_net_request?.rule_resources || [];
  for (const [i, rule] of dnr.entries()) exists(rule.path, `declarative_net_request.rule_resources[${i}].path`);

  const webResources = manifest.web_accessible_resources;
  if (webResources !== undefined) {
    if (!Array.isArray(webResources)) {
      fail("web_accessible_resources must be an array");
    } else {
      for (const [i, entry] of webResources.entries()) {
        if (typeof entry === "string") {
          fail(`web_accessible_resources[${i}] is an MV2 string; MV3 requires an object with resources and matches/extension_ids`);
        } else if (typeof entry === "object" && entry !== null) {
          if (!Array.isArray(entry.resources) || entry.resources.length === 0) {
            fail(`web_accessible_resources[${i}].resources must be a non-empty array`);
          } else {
            checkPathList(entry.resources, `web_accessible_resources[${i}].resources`, { allowGlob: true });
          }
          if (!Array.isArray(entry.matches) && !Array.isArray(entry.extension_ids)) {
            fail(`web_accessible_resources[${i}] requires matches or extension_ids array`);
          }
        }
      }
    }
  }

  // Check CSP: in MV3, CSP must be an object with extension_pages (and optional sandbox).
  if (manifest.content_security_policy !== undefined) {
    if (typeof manifest.content_security_policy === "string") {
      fail("content_security_policy must be an object in MV3, not a string");
    } else if (typeof manifest.content_security_policy === "object" && manifest.content_security_policy !== null) {
      const extPagesCsp = manifest.content_security_policy.extension_pages || "";
      if (typeof extPagesCsp === "string") {
        if (/(?<!wasm-)unsafe-eval/.test(extPagesCsp)) {
          fail("content_security_policy.extension_pages contains unsafe-eval (only wasm-unsafe-eval is permitted)");
        }
        if (/script-src[^;]*(https?:|\/\/)/i.test(extPagesCsp)) {
          fail("content_security_policy.extension_pages script-src allows remote scripts");
        }
        if (/'?unsafe-inline'?/i.test(extPagesCsp)) {
          fail("content_security_policy.extension_pages contains unsafe-inline (forbidden in MV3)");
        }
      }
    }
  }

  const manifestText = JSON.stringify(manifest);
  if (/https?:\/\/[^"']+\.(js|mjs)(["'])/i.test(manifestText)) fail("manifest references a remote script file");

  // Locale check
  const localesDir = path.join(root, "_locales");
  if (fs.existsSync(localesDir) && fs.statSync(localesDir).isDirectory()) {
    if (typeof manifest.default_locale !== "string" || manifest.default_locale.trim() === "") {
      fail("default_locale is required in manifest.json when _locales directory exists");
    }
  }

  for (const perm of manifest.permissions || []) {
    if (isHostPattern(perm)) {
      fail(`permissions includes host match pattern "${perm}"; in MV3, host permissions must be declared in host_permissions, not permissions`);
    }
  }
  if ((manifest.host_permissions || []).includes("<all_urls>")) warn("host_permissions includes <all_urls>; justify or narrow it");
}

for (const message of warnings) console.log(`WARN ${message}`);
if (failures.length > 0) {
  for (const message of failures) console.error(`FAIL ${message}`);
  process.exit(1);
}

console.log(`PASS MV3 manifest checks: ${path.relative(process.cwd(), manifestPath) || manifestPath}`);
NODE
