import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import os from "os";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const checkScript = path.join(repoRoot, "skills/build-chrome-extension/scripts/check-mv3-manifest.sh");
const preflightScript = path.join(repoRoot, "skills/build-chrome-extension/scripts/preflight-extension.sh");

if (!fs.existsSync(checkScript)) {
  console.error(`Missing script: ${checkScript}`);
  process.exit(1);
}
if (!fs.existsSync(preflightScript)) {
  console.error(`Missing script: ${preflightScript}`);
  process.exit(1);
}

const testDir = fs.mkdtempSync(path.join(os.tmpdir(), "manifest-scripts-test-"));

function createTestExt(manifestContent, files = {}) {
  const dir = fs.mkdtempSync(path.join(testDir, "case-"));
  fs.writeFileSync(path.join(dir, "manifest.json"), JSON.stringify(manifestContent, null, 2));
  for (const [rel, content] of Object.entries(files)) {
    const full = path.join(dir, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content);
  }
  return dir;
}

const baseManifest = {
  manifest_version: 3,
  name: "Test Extension",
  version: "1.0.0",
  background: { service_worker: "sw.js" }
};

const baseFiles = {
  "sw.js": "// service worker"
};

const testCases = [
  // --- Valid Cases (exit 0) ---
  {
    name: "Valid manifest (standard 1.0.0)",
    manifest: { ...baseManifest, version: "1.0.0", permissions: ["storage"] },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
  },
  {
    name: "Valid manifest (short 0.1)",
    manifest: { ...baseManifest, version: "0.1", permissions: ["storage"] },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
  },
  {
    name: "Valid manifest (2-component boundary 65535.65535)",
    manifest: { ...baseManifest, version: "65535.65535", permissions: ["storage"] },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
  },
  {
    name: "Valid manifest (4-component boundary 1.0.0.65535)",
    manifest: { ...baseManifest, version: "1.0.0.65535", permissions: ["storage"] },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
  },
  {
    name: "Valid manifest with host_permissions (<all_urls>)",
    manifest: { ...baseManifest, host_permissions: ["<all_urls>"] },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
    checkOutputContains: "WARN host_permissions includes <all_urls>",
    preflightOutputContains: "REVIEW broad host permission needs review justification: <all_urls>",
  },
  {
    name: "Valid manifest with compliant CSP (wasm-unsafe-eval)",
    manifest: {
      ...baseManifest,
      content_security_policy: {
        extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';"
      }
    },
    expectedCheck: "PASS",
    expectedPreflight: "PASS",
  },

  // --- Version Validation Failures (exit 1) ---
  {
    name: "Version with leading zero (1.01)",
    manifest: { ...baseManifest, version: "1.01" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "no leading zeros",
  },
  {
    name: "Version with leading zero (01.0.0)",
    manifest: { ...baseManifest, version: "01.0.0" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "no leading zeros",
  },
  {
    name: "Version with leading zero (00)",
    manifest: { ...baseManifest, version: "00" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "no leading zeros",
  },
  {
    name: "Version exceeding 65535 (1.0.0.99999)",
    manifest: { ...baseManifest, version: "1.0.0.99999" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "0-65535",
  },
  {
    name: "Version exceeding 65535 (1.0.0.65536)",
    manifest: { ...baseManifest, version: "1.0.0.65536" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "0-65535",
  },
  {
    name: "Version with 5 components (1.0.0.0.1)",
    manifest: { ...baseManifest, version: "1.0.0.0.1" },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "1-4 dot-separated integers",
  },

  // --- Permissions vs Host Permissions Failures (exit 1) ---
  {
    name: "Permissions has <all_urls>",
    manifest: { ...baseManifest, permissions: ["storage", "<all_urls>"] },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "permissions includes host match pattern \"<all_urls>\"",
  },
  {
    name: "Permissions has host match pattern (*://*/*)",
    manifest: { ...baseManifest, permissions: ["storage", "*://*/*"] },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "permissions includes host match pattern \"*://*/*\"",
  },
  {
    name: "Permissions has host match pattern (https://*.example.com/*)",
    manifest: { ...baseManifest, permissions: ["https://*.example.com/*"] },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "permissions includes host match pattern \"https://*.example.com/*\"",
  },

  // --- CSP unsafe-inline Failures (exit 1) ---
  {
    name: "CSP has quoted 'unsafe-inline' in extension_pages",
    manifest: {
      ...baseManifest,
      content_security_policy: {
        extension_pages: "script-src 'self' 'unsafe-inline'; object-src 'self';"
      }
    },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "unsafe-inline",
  },
  {
    name: "CSP has unquoted unsafe-inline in extension_pages",
    manifest: {
      ...baseManifest,
      content_security_policy: {
        extension_pages: "script-src 'self' unsafe-inline; object-src 'self';"
      }
    },
    expectedCheck: "FAIL",
    expectedPreflight: "FAIL",
    outputContains: "unsafe-inline",
  }
];

console.log("================================================================================");
console.log("  Manifest Scripts Validation Test Suite (R3)");
console.log(`  check script:     ${path.relative(repoRoot, checkScript)}`);
console.log(`  preflight script: ${path.relative(repoRoot, preflightScript)}`);
console.log("================================================================================\n");

let passedCount = 0;
let failedCount = 0;

for (const tc of testCases) {
  const extDir = createTestExt(tc.manifest, baseFiles);

  // 1. Run check-mv3-manifest.sh
  let checkStatus = "PASS";
  let checkOut = "";
  try {
    checkOut = execSync(`bash "${checkScript}" "${extDir}"`, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"]
    });
  } catch (err) {
    checkStatus = "FAIL";
    checkOut = (err.stdout || "") + (err.stderr || "");
  }

  // 2. Run preflight-extension.sh
  let preflightStatus = "PASS";
  let preflightOut = "";
  try {
    preflightOut = execSync(`bash "${preflightScript}" "${extDir}"`, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"]
    });
  } catch (err) {
    preflightStatus = "FAIL";
    preflightOut = (err.stdout || "") + (err.stderr || "");
  }

  const checkMatch = checkStatus === tc.expectedCheck;
  const preflightMatch = preflightStatus === tc.expectedPreflight;

  let patternMatch = true;
  let patternErr = "";

  if (tc.outputContains) {
    if (!checkOut.includes(tc.outputContains)) {
      patternMatch = false;
      patternErr += ` check missing expected substring [${tc.outputContains}];`;
    }
    if (!preflightOut.includes(tc.outputContains)) {
      patternMatch = false;
      patternErr += ` preflight missing expected substring [${tc.outputContains}];`;
    }
  }

  if (tc.checkOutputContains && !checkOut.includes(tc.checkOutputContains)) {
    patternMatch = false;
    patternErr += ` check missing [${tc.checkOutputContains}];`;
  }

  if (tc.preflightOutputContains && !preflightOut.includes(tc.preflightOutputContains)) {
    patternMatch = false;
    patternErr += ` preflight missing [${tc.preflightOutputContains}];`;
  }

  if (checkMatch && preflightMatch && patternMatch) {
    passedCount++;
    console.log(`  [PASS] ${tc.name} -> check=${checkStatus}, preflight=${preflightStatus}`);
  } else {
    failedCount++;
    console.error(`  [FAIL] ${tc.name}:`);
    if (!checkMatch) console.error(`    check status mismatch: expected ${tc.expectedCheck}, got ${checkStatus}`);
    if (!preflightMatch) console.error(`    preflight status mismatch: expected ${tc.expectedPreflight}, got ${preflightStatus}`);
    if (!patternMatch) console.error(`    output content mismatch:${patternErr}`);
    console.error(`    check output:     ${checkOut.trim()}`);
    console.error(`    preflight output: ${preflightOut.trim()}`);
  }
}

// Clean up temp dir
try {
  fs.rmSync(testDir, { recursive: true, force: true });
} catch {
  // ignore cleanup error
}

console.log("\n================================================================================");
console.log(`  Results: ${passedCount} passed, ${failedCount} failed out of ${testCases.length} test cases`);
console.log("================================================================================");

if (failedCount > 0) {
  process.exit(1);
} else {
  console.log("  100% PASS RATE ACHIEVED\n");
  process.exit(0);
}
