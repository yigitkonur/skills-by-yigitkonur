import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { existsSync, readFileSync } from 'node:fs';
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
  if (modules) return modules;
  const cache = dependencyLocation();
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
    }
    return getDependencies();
  } catch (error) {
    if (error.code === 'DEPENDENCIES_MISSING') throw error;
    throw failure('Installing locked dependencies failed. Check npm/network access, then retry doctor --setup.', [error.code || 'NPM_FAILED']);
  } finally { await rm(staging, { recursive: true, force: true }); }
}
