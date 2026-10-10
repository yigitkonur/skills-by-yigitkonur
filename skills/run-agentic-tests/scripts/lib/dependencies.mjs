import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { existsSync, readFileSync, lstatSync } from 'node:fs';
import { mkdir, copyFile, rename, rm } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const root = fileURLToPath(new URL('../../', import.meta.url));
let modules;
const failure = (message, details = []) => Object.assign(new Error(message), { code: 'DEPENDENCIES_MISSING', exitCode: 5, details });

export function dependencyLocation() {
  const hash = createHash('sha256').update(readFileSync(path.join(root, 'package-lock.json'))).digest('hex');
  return path.join(process.env.AGENTIC_TESTS_CACHE || path.join(homedir(), '.cache', 'run-agentic-tests'), hash);
}

export function getDependencies() {
  const cache = dependencyLocation();
  if (modules?.cache === cache) return modules;
  modules = undefined;
  if (!existsSync(path.join(cache, 'node_modules', 'yaml', 'package.json'))) {
    throw failure('Run doctor --setup to install locked dependencies in the external cache.', [cache]);
  }
  try {
    const require = createRequire(path.join(cache, 'package.json'));
    if (require('yaml/package.json').version !== '2.9.1' || require('ajv/package.json').version !== '8.20.0') {
      throw failure('Dependency cache versions differ from the lock; remove this cache and run doctor --setup.', [cache]);
    }
    modules = { YAML: require('yaml'), Ajv: require('ajv').default, cache };
    return modules;
  } catch (error) {
    if (error.code === 'DEPENDENCIES_MISSING') throw error;
    throw failure('Dependency cache is incomplete; run doctor --setup.', [cache]);
  }
}

export async function loadDependencies(options = {}) {
  if (Number(process.versions.node.split('.')[0]) < 22) throw failure('Node.js 22 or newer is required.');
  try { return getDependencies(); } catch (error) { if (!options?.setup) throw error; }
  const cache = dependencyLocation();
  await mkdir(path.dirname(cache), { recursive: true });
  const staging = `${cache}.${process.pid}.${Date.now()}.tmp`;
  await mkdir(staging, { recursive: false });
  try {
    for (const file of ['package.json', 'package-lock.json']) await copyFile(path.join(root, file), path.join(staging, file));
    await execute('npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], { cwd: staging, timeout: 120000, maxBuffer: 1024 * 1024 });
    try { await rename(staging, cache); } catch (error) {
      if (!['EEXIST', 'ENOTEMPTY'].includes(error.code)) throw error;
      try { return getDependencies(); } catch (invalid) { if (invalid.code !== 'DEPENDENCIES_MISSING') throw invalid; }
      if (lstatSync(cache).isSymbolicLink() || !lstatSync(cache).isDirectory()) throw failure('Refusing to replace a dependency-cache symlink or non-directory.', [cache]);
      const quarantined = `${cache}.${process.pid}.${Date.now()}.incomplete`;
      await rename(cache, quarantined);
      try {
        await rename(staging, cache);
        getDependencies();
      } catch (installError) {
        if (!existsSync(cache)) await rename(quarantined, cache);
        throw installError;
      } finally { if (existsSync(cache)) await rm(quarantined, { recursive: true, force: true }); }
    }
    return getDependencies();
  } catch (error) {
    if (error.code === 'DEPENDENCIES_MISSING') throw error;
    throw failure('Installing locked dependencies failed. Check npm/network access, then retry doctor --setup.', [error.code || 'NPM_FAILED']);
  } finally { await rm(staging, { recursive: true, force: true }); }
}

export async function checkRunnerEgoBrowser() {
  const skillPaths = [
    path.join(homedir(), '.agents', 'skills', 'ego-browser', 'SKILL.md'),
    path.join(root, '..', 'ego-browser', 'SKILL.md'),
    path.join(root, 'skills', 'ego-browser', 'SKILL.md'),
  ];
  const skillAvailable = skillPaths.some(p => existsSync(p));

  try {
    const { stdout, stderr } = await execute('ego-browser', ['--version'], { timeout: 3000 });
    const output = `${stdout}\n${stderr}`;
    const versionMatch = output.match(/ego-browser\s+([\d.]+)/i);
    return {
      available: true,
      cli_available: true,
      skill_available: skillAvailable,
      version: versionMatch ? versionMatch[1] : output.trim().split('\n')[0],
      remote_host: output.includes('tugce') ? 'tugce' : null,
    };
  } catch (error) {
    return {
      available: false,
      cli_available: false,
      skill_available: skillAvailable,
      error: error.code || 'NOT_FOUND',
    };
  }
}

export async function checkRunnerMaestro() {
  const skillPaths = [
    path.join(root, '..', 'test-by-maestro', 'SKILL.md'),
    path.join(root, 'skills', 'test-by-maestro', 'SKILL.md'),
    path.join(homedir(), '.agents', 'skills', 'test-by-maestro', 'SKILL.md'),
  ];
  const skillAvailable = skillPaths.some(p => existsSync(p));

  let javaAvailable = false;
  let javaVersion = null;
  try {
    const { stdout, stderr } = await execute('java', ['-version'], { timeout: 3000 });
    const output = `${stdout}\n${stderr}`;
    const match = output.match(/version\s+"([\d._]+)"/i);
    if (match && !output.includes('Unable to locate a Java Runtime')) {
      javaAvailable = true;
      javaVersion = match[1];
    }
  } catch {}

  try {
    const { stdout, stderr } = await execute('maestro', ['--version'], { timeout: 5000 });
    const output = `${stdout}\n${stderr}`;
    if (output.includes('Unable to locate a Java Runtime')) {
      return {
        available: false,
        cli_available: true,
        skill_available: skillAvailable,
        supported: false,
        java: { available: false, version: null },
        error: 'JAVA_RUNTIME_MISSING',
      };
    }
    const version = stdout.trim();
    const versionSupported = /^2\.(1[01]|\d+)\./.test(version);
    return {
      available: javaAvailable && versionSupported,
      cli_available: true,
      skill_available: skillAvailable,
      version,
      supported: versionSupported,
      java: { available: javaAvailable, version: javaVersion },
      platform: process.platform,
      ios_simulator_supported: process.platform === 'darwin',
    };
  } catch (error) {
    return {
      available: false,
      cli_available: false,
      skill_available: skillAvailable,
      supported: false,
      java: { available: javaAvailable, version: javaVersion },
      error: error.code || 'NOT_FOUND',
    };
  }
}

export async function checkRunnerMcpc() {
  const skillPaths = [
    path.join(root, '..', 'test-by-mcpc-cli', 'SKILL.md'),
    path.join(root, 'skills', 'test-by-mcpc-cli', 'SKILL.md'),
    path.join(homedir(), '.agents', 'skills', 'test-by-mcpc-cli', 'SKILL.md'),
  ];
  const skillAvailable = skillPaths.some(p => existsSync(p));

  try {
    const { stdout } = await execute('mcpc', ['--version'], { timeout: 3000 });
    const version = stdout.trim();
    const versionSupported = /^0\.7\./.test(version);
    return {
      available: versionSupported,
      cli_available: true,
      skill_available: skillAvailable,
      version,
      supported: versionSupported,
      session_first: true,
      skills_extension: true,
    };
  } catch (error) {
    return {
      available: false,
      cli_available: false,
      skill_available: skillAvailable,
      supported: false,
      error: error.code || 'NOT_FOUND',
    };
  }
}

export async function inspectAllRunners() {
  const [egoBrowser, maestro, mcpc] = await Promise.all([
    checkRunnerEgoBrowser(),
    checkRunnerMaestro(),
    checkRunnerMcpc(),
  ]);
  return {
    ego_browser: egoBrowser,
    maestro,
    mcpc,
  };
}

