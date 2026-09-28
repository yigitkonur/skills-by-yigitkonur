import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, mkdir, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { readYaml, readRecords, writeRecord, containedPath, withController } from '../../skills/run-agentic-tests/scripts/lib/store.mjs';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';

const temporary = async t => {
  const dir = await mkdtemp(path.join(tmpdir(), 'agentic-core-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  return dir;
};

test('strict YAML preserves scalar types and rejects ambiguous or executable document features', async t => {
  await loadDependencies({ setup: true });
  const dir = await temporary(t);
  const file = path.join(dir, 'input.yaml');
  await writeFile(file, 'answer: 42\nword: "yes"\n');
  assert.deepEqual(await readYaml(file), { answer: 42, word: 'yes' });
  for (const yaml of [
    'a: 1\na: 2\n',
    'a: 1\n---\nb: 2\n',
    'a: &anchor 1\nb: *anchor\n',
    'a: !!str 42\n',
    'a: { <<: { x: 1 } }\n',
    'a: !custom hello\n',
  ]) {
    await writeFile(file, yaml);
    await assert.rejects(readYaml(file), { code: 'INVALID_YAML' });
  }
});

test('accepted records are schema checked, immutable, idempotent, and contained', async t => {
  const dir = await temporary(t);
  const record = {
    schema_version: 1, kind: 'environment', record_id: 'ENV-G001', campaign_id: 'C001',
    created_at: '2026-09-28T00:00:00.000Z', target_id: 'G001', runtime_type: 'cli',
    source: { revision: 'abc123' }, command: { argv: ['node', 'app.mjs'], cwd: dir },
    readiness: { type: 'process', body_contains: 'ready', timeout_ms: 1000 }, status: 'READY',
    process: { pid: 12345, start_token: 'start-identity', argv: ['node', 'app.mjs'], cwd: dir },
    logs: { stdout: 'environments/G001/logs/stdout.log', stderr: 'environments/G001/logs/stderr.log' },
  };
  await withController(dir, () => writeRecord(dir, 'environments/G001/00-environment.record.yaml', record));
  await writeRecord(dir, 'environments/G001/00-environment.record.yaml', record);
  await assert.rejects(writeRecord(dir, 'environments/G001/00-environment.record.yaml', { ...record, status: 'STOPPED' }), { code: 'RECORD_CONFLICT' });
  await assert.rejects(writeRecord(dir, 'bad.record.yaml', { ...record, forged_status: 'PASS' }), { code: 'INVALID_RECORD' });
  assert.throws(() => containedPath(dir, '../outside.record.yaml'), { code: 'UNSAFE_PATH' });
  await writeFile(path.join(dir, 'ignored.draft.yaml'), 'broken: [');
  const records = await readRecords(dir);
  assert.equal(records.length, 1);
  assert.deepEqual(records[0].record, record);
  await withController(dir, async () => {
    await assert.rejects(withController(dir, async () => {}), { code: 'CONTROLLER_BUSY' });
  });
});
