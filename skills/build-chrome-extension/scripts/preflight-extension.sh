#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="${1:-dist}"

node - "$EXT_DIR" <<'NODE'
const fs = require("fs");
const path = require("path");

const root = path.resolve(process.argv[2] || "dist");
const manifestPath = path.join(root, "manifest.json");
const failures = [];
const reviews = [];

function fail(message) {
  failures.push(message);
}

function review(message) {
  reviews.push(message);
}

function isHostPattern(pattern) {
  if (typeof pattern !== "string") return false;
  return pattern === "<all_urls>" || /^((\*|https?|file|ftp):\/\/|\*:\/\/\/)/.test(pattern) || pattern.includes("://");
}

function readJson(file, label) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    fail(`${label} is invalid JSON: ${error.message}`);
    return null;
  }
}

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const absolute = path.join(dir, entry.name);
    const relative = path.relative(root, absolute);
    if (entry.isDirectory()) walk(absolute, out);
    else out.push(relative);
  }
  return out;
}

function pngSize(file) {
  const buffer = fs.readFileSync(file);
  if (buffer.length < 24) return null;
  if (buffer.readUInt32BE(0) !== 0x89504e47 || buffer.toString("ascii", 12, 16) !== "IHDR") return null;
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

function checkIcon(rel, expected, label) {
  if (!rel || typeof rel !== "string") return;
  const file = path.join(root, rel.replace(/^\//, ""));
  if (!fs.existsSync(file)) {
    fail(`${label} missing: ${rel}`);
    return;
  }
  if (path.extname(file).toLowerCase() === ".png") {
    const size = pngSize(file);
    if (!size) {
      fail(`${label} is not a valid PNG: ${rel}`);
    } else if (expected && (size.width !== expected || size.height !== expected)) {
      fail(`${label} expected ${expected}x${expected}, found ${size.width}x${size.height}: ${rel}`);
    }
  }
}

if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
  fail(`extension directory not found: ${root}`);
}
if (!fs.existsSync(manifestPath)) {
  fail(`manifest.json not found in ${root}`);
}

const manifest = failures.length ? null : readJson(manifestPath, "manifest.json");

if (manifest) {
  const versionRegex = /^(0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])(\.(0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])){0,3}$/;
  if (typeof manifest.version !== "string" || manifest.version.trim() === "") {
    fail("version is required in manifest.json");
  } else if (!versionRegex.test(manifest.version)) {
    fail(`version "${manifest.version}" is invalid: Chrome requires 1-4 dot-separated integers (0-65535) with no leading zeros`);
  }

  if (typeof manifest.icons === "object" && manifest.icons !== null) {
    for (const [size, rel] of Object.entries(manifest.icons)) checkIcon(rel, Number(size), `icons.${size}`);
  }

  if (typeof manifest.action?.default_icon === "string") {
    checkIcon(manifest.action.default_icon, null, "action.default_icon");
  } else if (typeof manifest.action?.default_icon === "object" && manifest.action?.default_icon !== null) {
    for (const [size, rel] of Object.entries(manifest.action.default_icon)) {
      if (typeof rel === "string") checkIcon(rel, Number(size), `action.default_icon.${size}`);
    }
  }

  const broadPermissions = new Set(["tabs", "history", "bookmarks", "cookies", "webRequest"]);
  for (const perm of manifest.permissions || []) {
    if (isHostPattern(perm)) {
      fail(`permissions includes host match pattern "${perm}"; in MV3, host permissions must be declared in host_permissions, not permissions`);
    } else if (broadPermissions.has(perm)) review(`permission needs review justification: ${perm}`);
  }
  for (const host of manifest.host_permissions || []) {
    if (host === "<all_urls>" || /^(\*|https?):\/\/\*(\/.*)?$/.test(host) || /^\*:\/\//.test(host)) {
      review(`broad host permission needs review justification: ${host}`);
    }
  }

  if (manifest.content_security_policy !== undefined) {
    if (typeof manifest.content_security_policy === "string") {
      fail("CSP must be an object in MV3, not a string");
    } else if (typeof manifest.content_security_policy === "object" && manifest.content_security_policy !== null) {
      const extPagesCsp = manifest.content_security_policy.extension_pages || "";
      if (typeof extPagesCsp === "string") {
        if (/(?<!wasm-)unsafe-eval/.test(extPagesCsp)) {
          fail("CSP extension_pages contains unsafe-eval");
        }
        if (/script-src[^;]*(https?:|\/\/)/i.test(extPagesCsp)) {
          fail("CSP extension_pages script-src allows remote scripts");
        }
        if (/'?unsafe-inline'?/i.test(extPagesCsp)) {
          fail("CSP extension_pages contains unsafe-inline (forbidden in MV3)");
        }
      }
    }
  }
}

const locales = path.join(root, "_locales");
if (fs.existsSync(locales)) {
  if (!manifest?.default_locale || typeof manifest.default_locale !== "string" || manifest.default_locale.trim() === "") {
    fail("default_locale is required in manifest.json when _locales directory exists");
  }
  for (const entry of fs.readdirSync(locales, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const messages = path.join(locales, entry.name, "messages.json");
    if (!fs.existsSync(messages)) fail(`_locales/${entry.name}/messages.json missing`);
    else readJson(messages, `_locales/${entry.name}/messages.json`);
  }
}

const junkPatterns = [
  { re: /(^|\/)\.DS_Store$/, label: ".DS_Store" },
  { re: /(^|\/)__MACOSX(\/|$)/, label: "__MACOSX" },
  { re: /(^|\/)(test|tests|__tests__)(\/|$)/i, label: "test files" },
  { re: /\.(test|spec)\.(js|jsx|ts|tsx)$/i, label: "test files" },
  { re: /(^|\/)(node_modules|\.git|\.github)(\/|$)/, label: "non-package directory" },
];

for (const rel of walk(root)) {
  if (/\.map$/i.test(rel)) {
    if (process.env.ALLOW_SOURCE_MAPS === "1") {
      review(`package input contains source map (explicitly allowed by ALLOW_SOURCE_MAPS): ${rel}`);
    } else {
      review(`package input contains source map (strip before upload unless intentionally shipped): ${rel}`);
    }
    continue;
  }
  for (const pattern of junkPatterns) {
    if (pattern.re.test(rel)) {
      fail(`package input contains ${pattern.label}: ${rel}`);
      break;
    }
  }
}

for (const message of reviews) console.log(`REVIEW ${message}`);
if (failures.length > 0) {
  for (const message of failures) console.error(`FAIL ${message}`);
  process.exit(1);
}

console.log(`PASS extension package preflight: ${path.relative(process.cwd(), root) || root}`);
NODE
