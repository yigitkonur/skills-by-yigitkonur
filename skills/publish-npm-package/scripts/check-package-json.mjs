#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const jsonOnly = args.includes("--json-only");
const dirArg = args.find((arg) => !arg.startsWith("--")) || ".";
const packageDir = path.resolve(dirArg);
const packageJsonPath = path.join(packageDir, "package.json");

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    throw new Error(`Cannot read JSON at ${file}: ${error.message}`);
  }
}

function exists(relPath) {
  return fs.existsSync(path.join(packageDir, relPath));
}

function findRepoRoot(start) {
  let current = start;
  while (true) {
    if (fs.existsSync(path.join(current, ".git"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return start;
    current = parent;
  }
}

function detectPackageManager(root, pkg) {
  const lockfiles = [
    ["package-lock.json", "npm", "npm ci"],
    ["npm-shrinkwrap.json", "npm", "npm ci"],
    ["pnpm-lock.yaml", "pnpm", "pnpm install --frozen-lockfile"],
    ["yarn.lock", "yarn", "yarn install --frozen-lockfile"],
    ["bun.lockb", "bun", "bun install --frozen-lockfile"],
  ].filter(([file]) => fs.existsSync(path.join(root, file)));

  const packageManager = typeof pkg.packageManager === "string" ? pkg.packageManager : "";
  const hasYarnBerry = fs.existsSync(path.join(root, ".yarnrc.yml")) || packageManager.startsWith("yarn@");
  const detected = lockfiles.map(([file, manager, install]) => ({
    file,
    manager,
    install: manager === "yarn" && hasYarnBerry ? "yarn install --immutable" : install,
  }));

  if (!detected.length && packageManager) {
    const manager = packageManager.split("@")[0];
    const install =
      manager === "pnpm" ? "pnpm install --frozen-lockfile" :
      manager === "yarn" ? "yarn install --immutable" :
      manager === "bun" ? "bun install --frozen-lockfile" :
      "npm ci";
    detected.push({ file: "packageManager", manager, install });
  }

  return {
    root,
    detected,
    multipleLockfiles: detected.filter((item) => item.file !== "packageManager").length > 1,
  };
}

function collectEntryPaths(value, paths = []) {
  if (!value) return paths;
  if (typeof value === "string") {
    paths.push(value);
    return paths;
  }
  if (typeof value === "object") {
    for (const child of Object.values(value)) collectEntryPaths(child, paths);
  }
  return paths;
}

function add(results, level, message, detail = undefined) {
  results.push({ level, message, ...(detail === undefined ? {} : { detail }) });
}

function main() {
  if (!fs.existsSync(packageJsonPath)) {
    throw new Error(`package.json not found in ${packageDir}`);
  }

  const pkg = readJson(packageJsonPath);
  const repoRoot = findRepoRoot(packageDir);
  const checks = [];
  const entryPaths = [
    pkg.main,
    pkg.module,
    pkg.types,
    pkg.typings,
    ...collectEntryPaths(pkg.exports),
    ...Object.values(pkg.bin || {}),
  ].filter(Boolean).map((entry) => String(entry).replace(/^\.\//, ""));

  add(checks, pkg.name && typeof pkg.name === "string" ? "ok" : "error", "package name present", pkg.name);
  add(checks, /^\d+\.\d+\.\d+/.test(String(pkg.version || "")) ? "ok" : "error", "semver-ish version present", pkg.version);

  const repository = typeof pkg.repository === "string" ? { url: pkg.repository } : pkg.repository;
  add(checks, repository?.url ? "ok" : "warn", "repository.url present", repository?.url);

  if (pkg.name?.startsWith("@")) {
    add(
      checks,
      pkg.publishConfig?.access === "public" ? "ok" : "warn",
      "scoped package has publishConfig.access public",
      pkg.publishConfig?.access,
    );
  }

  add(checks, Array.isArray(pkg.files) ? "ok" : "warn", "files allowlist present", pkg.files);

  const hasTypes = Boolean(pkg.types || pkg.typings || JSON.stringify(pkg.exports || {}).includes('"types"'));
  add(checks, hasTypes ? "ok" : "warn", "type declarations are declared");

  const missingEntries = entryPaths.filter((entry) => !entry.includes("*") && !exists(entry));
  add(checks, missingEntries.length ? "warn" : "ok", "entry paths exist on disk", missingEntries);

  const files = Array.isArray(pkg.files) ? pkg.files.map(String) : [];
  const entryUsesDist = entryPaths.some((entry) => entry.startsWith("dist/") || entry.includes("/dist/"));
  const filesIncludeDist = files.some((item) => item === "dist" || item.startsWith("dist/"));
  const filesIncludeSrc = files.some((item) => item === "src" || item.startsWith("src/"));

  if (entryUsesDist && files.length && !filesIncludeDist) {
    add(checks, "error", "entries point at dist but files omits dist", { entryPaths, files });
  } else if (entryUsesDist && filesIncludeSrc) {
    add(checks, "warn", "files includes src while entries point at dist", { entryPaths, files });
  } else {
    add(checks, "ok", "no obvious src/dist packaging mismatch");
  }

  const packageManager = detectPackageManager(repoRoot, pkg);
  add(
    checks,
    packageManager.multipleLockfiles ? "warn" : "ok",
    "package manager lockfile detection",
    packageManager.detected,
  );

  const summary = {
    packageDir,
    packageJsonPath,
    package: {
      name: pkg.name,
      version: pkg.version,
      private: Boolean(pkg.private),
      repository,
      publishConfig: pkg.publishConfig || null,
    },
    packageManager,
    checks,
    ok: !checks.some((check) => check.level === "error"),
  };

  if (!jsonOnly) {
    console.log(`Package: ${pkg.name || "(missing)"}@${pkg.version || "(missing)"}`);
    console.log(`Directory: ${packageDir}`);
    for (const check of checks) {
      const label = check.level.toUpperCase().padEnd(5);
      const detail = check.detail === undefined ? "" : ` ${JSON.stringify(check.detail)}`;
      console.log(`${label} ${check.message}${detail}`);
    }
    console.log("");
  }

  console.log(JSON.stringify(summary, null, 2));
  process.exit(summary.ok ? 0 : 1);
}

try {
  main();
} catch (error) {
  const failure = { ok: false, error: error.message };
  if (!jsonOnly) console.error(`ERROR ${error.message}`);
  console.log(JSON.stringify(failure, null, 2));
  process.exit(1);
}
