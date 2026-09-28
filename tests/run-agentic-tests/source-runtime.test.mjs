import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, realpath, chmod, symlink, unlink, cp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';

await loadDependencies({ setup: true });
const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
const invoke = (...args) => {
  const result = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
  return { status: result.status, data: result.stdout.trim() ? JSON.parse(result.stdout) : null, stderr: result.stderr };
};
const accepted = result => { assert.equal(result.status, 0, JSON.stringify(result)); return result.data; };
const git = (root, ...args) => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();

async function fixture(t, provider = 'git') {
  const root = await realpath(await mkdtemp(path.join(tmpdir(), 'agentic-source-')));
  const project = path.join(root, 'project');
  await mkdir(project);
  await writeFile(path.join(project, 'app.mjs'), "console.log('application ready');\n");
  await writeFile(path.join(project, '.gitignore'), 'ignored.txt\n');
  if (provider === 'git') {
    git(project, 'init', '-q');
    git(project, 'add', '.');
    git(project, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Initial source');
  }
  const initialized = accepted(invoke('init', '--project', project, '--slug', 'source-proof'));
  const campaign = initialized.campaign_path;
  const draft = {
    target_id: 'G001', runtime_type: 'cli',
    source: { revision: provider === 'git' ? git(project, 'rev-parse', 'HEAD') : 'fixture-v1', worktree: project,
      ...(provider === 'files' ? { provider: { type: provider, root: project, paths: ['app.mjs'] } } : {}),
      fingerprint: 'caller-chosen-unverified-value' },
    command: { argv: [process.execPath, 'app.mjs'], cwd: project },
    readiness: { type: 'process', body_contains: 'application ready', timeout_ms: 2000 },
  };
  const file = path.join(root, 'environment.json');
  const save = () => writeFile(file, JSON.stringify(draft));
  await save();
  t.after(async () => {
    for (const target of ['G001', 'G002']) invoke('runtime', 'stop', '--campaign', campaign, '--target-id', target);
    await rm(root, { recursive: true, force: true });
  });
  const start = () => invoke('runtime', 'start', '--campaign', campaign, '--file', file);
  const inspect = () => accepted(invoke('runtime', 'inspect', '--campaign', campaign, '--target-id', 'G001'));
  return { root, project, campaign, campaign_id: initialized.campaign.campaign_id, draft, file, save, start, inspect };
}

test('runtime computes actual Git source proof and inspection detects an edited tracked file', async t => {
  const f = await fixture(t);
  const started = accepted(f.start());
  assert.match(started.environment.source.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.equal(started.environment.source.attestation.git_head, git(f.project, 'rev-parse', 'HEAD'));
  assert.equal(f.inspect().source_verification.valid, true);
  await writeFile(path.join(f.project, 'app.mjs'), "console.log('changed behavior');\n");
  const inspected = f.inspect();
  assert.equal(inspected.source_verification.valid, false);
  assert.equal(inspected.source_verification.code, 'SOURCE_CHANGED');
});

test('a files provider can attest the project directory while excluding campaign output', async t => {
  const f = await fixture(t, 'files');
  f.draft.source.provider.paths = ['.'];
  await f.save();
  const started = accepted(f.start());
  assert.ok(started.environment.source.attestation.manifest.some(entry => entry.path === 'app.mjs'));
  assert.ok(started.environment.source.attestation.manifest.every(entry => !entry.path.startsWith('agentic-tests/')));
  await writeFile(path.join(f.campaign, 'new-output.txt'), 'a later campaign artifact');
  assert.equal(f.inspect().source_verification.valid, true);
});

test('a runtime cannot become ready after changing its own frozen source during startup', async t => {
  const f = await fixture(t, 'files');
  await writeFile(path.join(f.project, 'app.mjs'), "import fs from 'node:fs'; fs.writeFileSync('app.mjs', 'changed during startup'); console.log('application ready');\n");
  const result = f.start();
  assert.notEqual(result.status, 0);
  assert.equal(result.data.error.code, 'RUNTIME_START_FAILED');
  assert.match(result.data.error.message, /source|configuration/i);
  assert.equal(f.inspect().environment.status, 'FAILED');
});

test('Git source inspection covers untracked files, staged deletion, file modes and symlink targets', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.project, 'untracked.txt'), 'original untracked source');
  await writeFile(path.join(f.project, 'ignored.txt'), 'irrelevant ignored output');
  await symlink('app.mjs', path.join(f.project, 'entry.mjs'));
  git(f.project, 'rm', '-q', '.gitignore');
  // Keep the ignore policy present but staged as deleted: both index and disk are inspected.
  await writeFile(path.join(f.project, '.gitignore'), 'ignored.txt\n');
  const started = accepted(f.start());
  const paths = started.environment.source.attestation.manifest.map(entry => entry.path);
  assert.ok(paths.includes('untracked.txt'));
  assert.ok(paths.includes('entry.mjs'));
  assert.ok(!paths.includes('ignored.txt'));
  assert.ok(paths.every(item => !item.startsWith('agentic-tests/')));
  await writeFile(path.join(f.project, 'ignored.txt'), 'new ignored output');
  assert.equal(f.inspect().source_verification.valid, true);
  await writeFile(path.join(f.project, 'untracked.txt'), 'different untracked source');
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
  await writeFile(path.join(f.project, 'untracked.txt'), 'original untracked source');
  await chmod(path.join(f.project, 'app.mjs'), 0o755);
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
  await chmod(path.join(f.project, 'app.mjs'), 0o644);
  await unlink(path.join(f.project, 'entry.mjs'));
  await symlink('untracked.txt', path.join(f.project, 'entry.mjs'));
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
  await unlink(path.join(f.project, 'entry.mjs'));
  await symlink('app.mjs', path.join(f.project, 'entry.mjs'));
  await unlink(path.join(f.project, 'app.mjs'));
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
});

test('declared ignored configuration is hashed without exposing values and cannot change silently', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.project, 'ignored.txt'), 'private configuration value');
  f.draft.source.provider = { type: 'git', root: f.project, config_files: ['ignored.txt'] };
  await f.save();
  const started = accepted(f.start());
  assert.equal(started.environment.source.attestation.config_manifest[0].path, 'ignored.txt');
  assert.ok(!JSON.stringify(started).includes('private configuration value'));
  await writeFile(path.join(f.project, 'ignored.txt'), 'changed private configuration');
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
  await unlink(path.join(f.project, 'ignored.txt'));
  assert.equal(f.inspect().source_verification.code, 'SOURCE_MISSING');
});

test('legacy records remain readable but cannot become current proof through inspection', async t => {
  const f = await fixture(t, 'files');
  const started = accepted(f.start());
  const legacy = { ...started.environment, source: { revision: 'old-text-only-revision', worktree: f.project } };
  const record = path.join(f.campaign, started.record_path);
  const historical = JSON.stringify(legacy);
  await writeFile(record, historical);
  assert.equal(f.inspect().source_verification.code, 'SOURCE_ATTESTATION_REQUIRED');
  assert.equal(await readFile(record, 'utf8'), historical);
});

test('fresh runtimes reject arbitrary non-Git labels and incorrect checked-out commits', async t => {
  const files = await fixture(t, 'files');
  delete files.draft.source.provider;
  await files.save();
  assert.equal(files.start().data.error.code, 'SOURCE_ATTESTATION_REQUIRED');
  const repository = await fixture(t);
  repository.draft.source.revision = 'invented-revision';
  await repository.save();
  assert.equal(repository.start().data.error.code, 'SOURCE_REVISION_MISMATCH');
});

test('another campaign does not change source while ordinary code under agentic-tests stays attested', async t => {
  const f = await fixture(t);
  await mkdir(path.join(f.project, 'agentic-tests', 'product'), { recursive: true });
  await writeFile(path.join(f.project, 'agentic-tests', 'product', 'feature.mjs'), 'original product code');
  accepted(f.start());
  const other = accepted(invoke('init', '--project', f.project, '--slug', 'independent-campaign')).campaign_path;
  await writeFile(path.join(other, 'worker-output.txt'), 'independent evidence');
  assert.equal(f.inspect().source_verification.valid, true);
  await writeFile(path.join(f.project, 'agentic-tests', 'product', 'feature.mjs'), 'changed product code');
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
});

async function activeWorker(f, overrides = {}) {
  const record = { schema_version: 1, kind: 'task', record_id: 'J00001', campaign_id: f.campaign_id,
    created_at: '2026-09-28T00:00:00.000Z', task_id: 'J00001', actor_id: 'A00001', role: 'executor', state: 'RUNNING',
    target_id: 'G001', worker_finished: false, handle: 'active-fixture-context', case_ids: [], dependencies: [], resources: [],
    required_inputs: [], outputs: [{ kind: 'execution', record_id: 'EXEC-T0001', path: 'cases/T0001-fixture/rounds/R001/01-execution.record.yaml' }],
    draft_paths: ['tasks/J00001/draft/execution.yaml'], requested_action: 'Exercise the frozen fixture runtime.', ...overrides };
  await mkdir(path.join(f.campaign, 'tasks', record.task_id), { recursive: true });
  await writeFile(path.join(f.campaign, 'tasks', record.task_id, '00-task.record.yaml'), JSON.stringify(record));
  return record;
}

test('active and interrupted executors lease their runtime until the worker has actually finished', async t => {
  const f = await fixture(t, 'files');
  accepted(f.start());
  await activeWorker(f);
  const stop = () => invoke('runtime', 'stop', '--campaign', f.campaign, '--target-id', 'G001');
  assert.equal(stop().data.error?.code, 'RUNTIME_IN_USE');
  await activeWorker(f, { state: 'INTERRUPTED' });
  assert.equal(stop().data.error?.code, 'RUNTIME_IN_USE');
  await activeWorker(f, { state: 'INTERRUPTED', worker_finished: true });
  assert.equal(accepted(stop()).environment.status, 'STOPPED');
});

test('a live source lease allows an isolated successor while preventing startup on shared mutable source', async t => {
  const f = await fixture(t, 'files');
  const old = accepted(f.start()).environment;
  await activeWorker(f);
  f.draft.target_id = 'G002';
  await f.save();
  assert.equal(f.start().data.error?.code, 'SOURCE_IN_USE');
  const isolated = path.join(f.root, 'isolated');
  await mkdir(isolated);
  await cp(path.join(f.project, 'app.mjs'), path.join(isolated, 'app.mjs'));
  f.draft.source.provider.root = isolated;
  f.draft.source.worktree = isolated;
  f.draft.command.cwd = isolated;
  await f.save();
  const successor = accepted(f.start()).environment;
  assert.equal(successor.source.attestation.source_digest, old.source.attestation.source_digest);
  assert.equal(f.inspect().environment.status, 'READY');
  await activeWorker(f, { worker_finished: true });
});

test('offline verifiers hold no runtime lease after execution has finished', async t => {
  const f = await fixture(t, 'files');
  accepted(f.start());
  await activeWorker(f, { role: 'verifier' });
  assert.equal(accepted(invoke('runtime', 'stop', '--campaign', f.campaign, '--target-id', 'G001')).environment.status, 'STOPPED');
});

async function integrated(f, commit = f.draft.source.revision) {
  const record = { schema_version: 1, kind: 'integration', record_id: 'INTEGRATION-F0001', campaign_id: f.campaign_id,
    created_at: '2026-09-28T00:00:00.000Z', task_id: 'J00099', actor_id: 'A00099', finding_id: 'F0001',
    implementation_record_id: 'IMPLEMENTATION-F0001', new_target_id: 'G001', commit, affected_case_ids: ['T0001'],
    retest_obligations: [{ case_id: 'T0001', reason: 'Retest the recorded local integration.' }], artifacts: [] };
  await mkdir(path.join(f.campaign, 'findings'), { recursive: true });
  await writeFile(path.join(f.campaign, 'findings', '20-integration.record.yaml'), JSON.stringify(record));
}

test('integrated runtime startup rejects dirty source despite matching the recorded Git HEAD', async t => {
  const f = await fixture(t);
  await integrated(f);
  await writeFile(path.join(f.project, 'app.mjs'), "console.log('application ready'); // an unintegrated source edit\n");
  assert.equal(f.start().data.error?.code, 'TARGET_DRIFT');
  await writeFile(path.join(f.project, 'app.mjs'), "console.log('application ready');\n");
  assert.equal(accepted(f.start()).environment.status, 'READY');
});

test('a fresh target can repair declared ignored configuration while retaining the same product code identity', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.project, 'ignored.txt'), 'incorrect startup configuration');
  f.draft.source.provider = { type: 'git', root: f.project, config_files: ['ignored.txt'] };
  await f.save();
  const first = accepted(f.start()).environment.source;
  await writeFile(path.join(f.project, 'ignored.txt'), 'correct startup configuration');
  assert.equal(f.inspect().source_verification.code, 'SOURCE_CHANGED');
  f.draft.target_id = 'G002';
  await f.save();
  const successor = accepted(f.start()).environment.source;
  assert.equal(first.attestation.source_digest, successor.attestation.source_digest);
  assert.notEqual(first.attestation.configuration_digest, successor.attestation.configuration_digest);
  assert.notEqual(first.fingerprint, successor.fingerprint);
});

test('managed process ownership is bound to the frozen target source identity', async t => {
  const f = await fixture(t, 'files');
  await writeFile(path.join(f.project, 'app.mjs'), "console.log('application ready');setInterval(()=>{},1000);\n");
  f.draft.runtime_type = 'mcp_stdio';
  await f.save();
  const started = accepted(f.start());
  const recordPath = path.join(f.campaign, started.record_path);
  const historical = await readFile(recordPath, 'utf8');
  await writeFile(recordPath, JSON.stringify({ ...started.environment,
    source: { ...started.environment.source, fingerprint: `sha256:${'a'.repeat(64)}` } }));
  try {
    assert.equal(f.inspect().ownership, 'MISMATCH');
    assert.equal(invoke('runtime', 'stop', '--campaign', f.campaign, '--target-id', 'G001').data.error?.code, 'PROCESS_OWNERSHIP_MISMATCH');
    assert.equal(process.kill(started.environment.process.pid, 0), true);
  } finally { await writeFile(recordPath, historical); }
});
