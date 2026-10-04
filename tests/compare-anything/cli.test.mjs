import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { mkdtemp, symlink, rm } from 'node:fs/promises';

const scriptsDir = fileURLToPath(new URL('../../skills/compare-anything/scripts', import.meta.url));
const wave2Script = path.join(scriptsDir, 'validate-wave2-research.mjs');
const wave3Script = path.join(scriptsDir, 'validate-wave3-verification.mjs');

test('validate-wave2-research prints usage and exits non-zero when invoked without required arguments', () => {
  const result = spawnSync(process.execPath, [wave2Script], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stdout, /Usage:/);
});

test('validate-wave3-verification prints usage and exits non-zero when invoked without required arguments', () => {
  const result = spawnSync(process.execPath, [wave3Script], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stdout, /Usage:/);
});

test('validate-wave2-research executes when invoked through a symlink to its scripts folder', async () => {
  const tempDir = await mkdtemp(path.join(tmpdir(), 'compare-anything-symlink-'));
  const symlinkedScripts = path.join(tempDir, 'scripts');
  try {
    await symlink(scriptsDir, symlinkedScripts, 'dir');
    const symlinkedScript = path.join(symlinkedScripts, 'validate-wave2-research.mjs');
    const result = spawnSync(process.execPath, [symlinkedScript], { encoding: 'utf8' });
    assert.equal(result.status, 1, `Expected exit code 1, got ${result.status} (stdout: "${result.stdout}", stderr: "${result.stderr}")`);
    assert.match(result.stdout, /Usage:/, 'Expected script to execute and print usage output through symlink');
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
});

test('validate-wave3-verification executes when invoked through a symlink to its scripts folder', async () => {
  const tempDir = await mkdtemp(path.join(tmpdir(), 'compare-anything-symlink-'));
  const symlinkedScripts = path.join(tempDir, 'scripts');
  try {
    await symlink(scriptsDir, symlinkedScripts, 'dir');
    const symlinkedScript = path.join(symlinkedScripts, 'validate-wave3-verification.mjs');
    const result = spawnSync(process.execPath, [symlinkedScript], { encoding: 'utf8' });
    assert.equal(result.status, 1, `Expected exit code 1, got ${result.status} (stdout: "${result.stdout}", stderr: "${result.stderr}")`);
    assert.match(result.stdout, /Usage:/, 'Expected script to execute and print usage output through symlink');
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
});
