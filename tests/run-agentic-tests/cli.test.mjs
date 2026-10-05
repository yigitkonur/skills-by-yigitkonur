import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { mkdtemp, symlink, rm } from 'node:fs/promises';

const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
function invoke(...args) {
  const result = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
  return { ...result, data: result.stdout.trim() ? JSON.parse(result.stdout) : null };
}

test('help is machine-readable and available without setup', () => {
  const result = invoke('--help');
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.data.ok, true);
  assert.ok(result.data.commands.some(command => command.name === 'submit'));
  assert.ok(result.data.commands.some(command => command.name === 'runtime stop'));
  assert.match(result.data.completion_rule, /accepted.*not.*pass/i);
});

test('unknown commands produce a structured usage failure', () => {
  const result = invoke('approve-everything');
  assert.equal(result.status, 2);
  assert.equal(result.data.ok, false);
  assert.equal(result.data.error.code, 'UNKNOWN_COMMAND');
  assert.equal(result.data.worker_may_finish, false);
});

test('misspelled flags are rejected before a command can mutate a campaign', () => {
  const result = invoke('submit', '--camapign', '/tmp/none');
  assert.equal(result.status, 2);
  assert.equal(result.data.error.code, 'UNKNOWN_OPTION');
});

test('duplicate flags do not silently select the final value', () => {
  const result = invoke('status', '--campaign', '/first', '--campaign', '/second');
  assert.equal(result.status, 2);
  assert.equal(result.data.error.code, 'DUPLICATE_OPTION');
});

test('missing flag values and required arguments are actionable usage errors', () => {
  const missingValue = invoke('submit', '--campaign');
  assert.equal(missingValue.status, 2);
  assert.equal(missingValue.data.error.code, 'MISSING_OPTION_VALUE');
  const missingRequired = invoke('submit', '--campaign', '/tmp/none');
  assert.equal(missingRequired.status, 2);
  assert.equal(missingRequired.data.error.code, 'MISSING_OPTION');
  assert.ok(missingRequired.data.error.details.some(detail => detail.option === 'task-id'));
});

test('subcommand help exposes its exact accepted flags', () => {
  const result = invoke('task', 'bind', '--help');
  assert.equal(result.status, 0);
  assert.equal(result.data.command, 'task bind');
  assert.ok(result.data.options.includes('handle'));
});

test('interrupt can record confirmed worker termination without releasing live workers', () => {
  const result = invoke('task', 'interrupt', '--help');
  assert.equal(result.status, 0);
  assert.ok(result.data.options.includes('finished'));
  assert.ok(!result.data.required.includes('finished'));
});

test('scope decisions require finding identity, disposition, reason and decision source', () => {
  const result = invoke('finding', 'decide', '--help');
  assert.equal(result.status, 0, result.stdout);
  assert.deepEqual(result.data.required, ['campaign', 'finding-id', 'scope', 'reason', 'source']);
});

test('CLI entry executes when invoked through a symlink to its scripts folder', async () => {
  const tempDir = await mkdtemp(path.join(tmpdir(), 'agentic-tests-cli-symlink-'));
  const symlinkedScripts = path.join(tempDir, 'scripts');
  try {
    await symlink(path.dirname(cli), symlinkedScripts, 'dir');
    const symlinkedCli = path.join(symlinkedScripts, path.basename(cli));
    const result = spawnSync(process.execPath, [symlinkedCli, '--help'], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    const data = result.stdout.trim() ? JSON.parse(result.stdout) : null;
    assert.ok(data, 'expected JSON output from --help through symlink');
    assert.equal(data.ok, true);
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
});

