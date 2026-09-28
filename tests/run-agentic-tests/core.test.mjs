import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, mkdir, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { readYaml, readRecords, writeRecord, containedPath, withController } from '../../skills/run-agentic-tests/scripts/lib/store.mjs';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
import { run } from '../../skills/run-agentic-tests/scripts/lib/workflow.mjs';

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
    'true: first\n"true": second\n',
    '? [a, b]\n: value\n',
  ]) {
    await writeFile(file, yaml);
    await assert.rejects(readYaml(file), { code: 'INVALID_YAML' });
  }
});

async function campaign(t, options = {}) {
  const project = await temporary(t);
  const result = await run('init', { project, slug: 'real-check', 'host-capacity': '3', ...options });
  return { project, campaign: result.campaign_path, config: result.campaign };
}

async function createTask(c, request) {
  const file = path.join(c.project, `request-${Math.random().toString(36).slice(2)}.yaml`);
  await writeFile(file, JSON.stringify(request));
  return (await run('task create', { campaign: c.campaign, request: file })).task;
}

async function startTask(c, task, handle = `host-${task.task_id}`) {
  await run('task dispatch', { campaign: c.campaign, 'task-id': task.task_id });
  await run('task bind', { campaign: c.campaign, 'task-id': task.task_id, handle });
}

async function submitDraft(c, task, draft, check = false) {
  const file = path.join(c.campaign, task.draft_paths[0]);
  await writeFile(file, JSON.stringify(draft));
  return run('submit', { campaign: c.campaign, 'task-id': task.task_id, file, check });
}

async function finishTask(c, task) {
  return run('task close', { campaign: c.campaign, 'task-id': task.task_id, finished: true });
}

async function authorCase(c, slug = 'search', expectationOptions = {}) {
  const task = await createTask(c, { role: 'scenario-author', slug, requested_action: `Write the approved ${slug} case` });
  await startTask(c, task);
  const root = path.dirname(path.join(c.campaign, task.outputs[0].path));
  await writeFile(path.join(root, '01-test-case.md'), '# Approved search\nGiven the CLI is ready\nWhen searching cats\nThen [E1] JSON contains cats.\n');
  await writeFile(path.join(root, '03-how-to-run.md'), 'Run node app.mjs search cats and save JSON stdout.');
  const draft = await readYaml(path.join(c.campaign, task.draft_paths[0]));
  draft.expectations = [{ id: 'E1', statement: 'JSON contains cats', source: { type: 'user_request', reference: 'Approved search requirement' }, priority: 'P1', review_count: 1, observable: { description: 'stdout includes requested term' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Save stdout JSON' }], ...expectationOptions }];
  await submitDraft(c, task, draft);
  await finishTask(c, task);
  return { task, record: draft };
}

async function environment(c, target = 'G001') {
  const record = { schema_version: 1, kind: 'environment', record_id: `ENV-${target}`, campaign_id: c.config.campaign_id, created_at: '2026-09-28T00:00:00.000Z', target_id: target, runtime_type: 'cli', source: { revision: `revision-${target}` }, command: { argv: ['node', 'app.mjs'], cwd: c.project }, readiness: { type: 'process', body_contains: 'ready' }, status: 'READY', logs: { stdout: `environments/${target}/logs/stdout.log`, stderr: `environments/${target}/logs/stderr.log` } };
  await writeRecord(c.campaign, `environments/${target}/00-environment.record.yaml`, record);
  return record;
}

async function acceptPlan(c, cases, { dependencies = {}, resources = {} } = {}) {
  const planner = await createTask(c, { role: 'planner', target_id: 'G001', requested_action: 'Plan these sourced E2E cases' });
  await startTask(c, planner);
  const plan = await readYaml(path.join(c.campaign, planner.draft_paths[0]));
  Object.assign(plan, { target_id: 'G001', scope: { in_scope: ['Search E2E'], out_of_scope: [] }, cases: cases.map(item => ({ case_id: item.record.case_id, spec_revision: item.record.spec_revision, target_id: 'G001', depends_on: dependencies[item.record.case_id] || [], resources: resources[item.record.case_id] || [] })), coverage: [{ source: 'Approved search requirement', case_ids: cases.map(item => item.record.case_id) }] });
  await submitDraft(c, planner, plan);
  await finishTask(c, planner);
  const auditor = await createTask(c, { role: 'plan-auditor', plan_id: planner.plan_id, requested_action: 'Audit the frozen DAG and coverage' });
  await startTask(c, auditor);
  const audit = await readYaml(path.join(c.campaign, auditor.draft_paths[0]));
  Object.assign(audit, { outcome: 'approved', findings: [], artifacts: [] });
  await submitDraft(c, auditor, audit);
  await finishTask(c, auditor);
  await run('plan accept', { campaign: c.campaign, file: path.join(c.campaign, planner.outputs[0].path), audit: path.join(c.campaign, auditor.outputs[0].path) });
  return { planner, auditor, plan: await readYaml(path.join(c.campaign, planner.outputs[0].path)) };
}

test('audited plans reject cyclic prerequisites and freeze scenario files before execution', async t => {
  const c = await campaign(t);
  const authored = await authorCase(c);
  await environment(c);
  const planner = await createTask(c, { role: 'planner', target_id: 'G001', requested_action: 'Plan the case' });
  await startTask(c, planner);
  const bad = await readYaml(path.join(c.campaign, planner.draft_paths[0]));
  Object.assign(bad, { scope: { in_scope: ['Search'], out_of_scope: [] }, cases: [{ case_id: 'T0001', spec_revision: 'S001', target_id: 'G001', depends_on: ['T0001'], resources: [] }], coverage: [{ source: 'User requirement', case_ids: ['T0001'] }] });
  await assert.rejects(submitDraft(c, planner, bad), { code: 'INVALID_DAG' });
  await run('task interrupt', { campaign: c.campaign, 'task-id': planner.task_id, reason: 'invalid draft abandoned', finished: true });
  const accepted = await acceptPlan(c, [authored]);
  assert.equal(accepted.plan.cases[0].spec_hashes.length, 3);
  const executor = await createTask(c, { role: 'executor', case_ids: ['T0001'], target_id: 'G001', requested_action: 'Execute the actual search CLI' });
  assert.equal(executor.outputs[0].path, 'cases/T0001-search/rounds/R001/10-execution.record.yaml');
  const scenario = path.join(c.campaign, path.dirname(authored.task.outputs[0].path), '01-test-case.md');
  await writeFile(scenario, 'Given a changed contract\nWhen run\nThen [E1] something different.');
  await assert.rejects(run('task dispatch', { campaign: c.campaign, 'task-id': executor.task_id }), { code: 'SPEC_CHANGED' });
});

async function prepared(t, expectationOptions = {}, options = {}) {
  const c = await campaign(t, options);
  const authored = await authorCase(c, 'search', expectationOptions);
  await environment(c);
  const accepted = await acceptPlan(c, [authored]);
  return { ...c, authored, accepted };
}

async function execution(c, { status = 'COMPLETED', observed = { results: ['cats'] }, gap = false } = {}) {
  const task = await createTask(c, { role: 'executor', case_ids: ['T0001'], target_id: 'G001', requested_action: 'Run the real search command' });
  await startTask(c, task);
  const draft = await readYaml(path.join(c.campaign, task.draft_paths[0]));
  const artifact = `${path.posix.dirname(task.outputs[0].path)}/evidences/search.json`;
  if (!gap) await writeFile(path.join(c.campaign, artifact), JSON.stringify(observed));
  Object.assign(draft, { execution_status: status, observations: [{ expectation_id: 'E1', observed, evidence_ids: gap ? [] : ['EV1'], gaps: gap ? [{ requirement_id: 'ER1', reason: 'Credential unavailable; command did not run' }] : [] }], evidence: gap ? [] : [{ id: 'EV1', path: artifact, type: 'json', expectation_ids: ['E1'] }] });
  return { task, draft, artifact };
}

test('honest partial reports are accepted while missing coverage, claimed missing files, wrong targets, and conflicting resubmits are rejected', async t => {
  const c = await prepared(t);
  const { task, draft, artifact } = await execution(c);
  await assert.rejects(submitDraft(c, task, { ...draft, observations: [] }), { code: 'INVALID_RECORD' });
  await assert.rejects(submitDraft(c, task, { ...draft, observations: [{ ...draft.observations[0], expectation_id: 'E999' }] }), { code: 'EXPECTATION_COVERAGE' });
  await assert.rejects(submitDraft(c, task, { ...draft, target_id: 'G002' }), { code: 'WRONG_ASSIGNMENT' });
  await rm(path.join(c.campaign, artifact));
  await assert.rejects(submitDraft(c, task, draft, true), { code: 'MISSING_ARTIFACT' });
  Object.assign(draft, { execution_status: 'PARTIAL', evidence: [], observations: [{ expectation_id: 'E1', observed: 'The command ran but JSON capture failed', evidence_ids: [], gaps: [{ requirement_id: 'ER1', reason: 'Output capture was unavailable' }] }] });
  assert.equal((await submitDraft(c, task, draft, true)).submission_status, 'VALIDATED');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'execution' })).records.length, 0);
  const accepted = await submitDraft(c, task, draft);
  assert.equal(accepted.submission_status, 'ACCEPTED');
  assert.equal(accepted.test_verdict, 'NOT_DECIDED');
  assert.equal((await submitDraft(c, task, draft)).record_id, accepted.record_id);
  await assert.rejects(submitDraft(c, task, { ...draft, observations: [{ ...draft.observations[0], observed: 'Changed claim' }] }), { code: 'RECORD_CONFLICT' });
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records.length, 0);
});

test('a scenario author receives fixed paths and can bootstrap approved Gherkin into an accepted immutable specification', async t => {
  const c = await campaign(t);
  const source = path.join(c.project, 'existing');
  await mkdir(source);
  await writeFile(path.join(source, 'scenario.md'), '# Search\nGiven an available CLI\nWhen a search runs\nThen [E1] it returns the requested item.\n');
  await writeFile(path.join(source, 'run.md'), 'Run node app.mjs search cats; capture stdout as JSON.\n');
  const expectations = [{ id: 'E1', statement: 'Returns the requested item', source: { type: 'user_request', reference: 'User-provided search scenario' }, priority: 'P1', review_count: 1, observable: { description: 'JSON result contains cats' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Save stdout JSON' }] }];
  await writeFile(path.join(source, 'expectations.yaml'), JSON.stringify({ expectations }));
  const author = await createTask(c, { role: 'scenario-author', slug: 'search', requested_action: 'Bootstrap approved existing search scenario', scenario_source: { test_case_path: path.join(source, 'scenario.md'), how_to_run_path: path.join(source, 'run.md'), expectations_path: path.join(source, 'expectations.yaml') } });
  assert.deepEqual(author.case_ids, ['T0001']);
  assert.equal(author.outputs[0].path, 'cases/T0001-search/specs/S001/02-expectations.record.yaml');
  await startTask(c, author);
  const draft = await readYaml(path.join(c.campaign, author.draft_paths[0]));
  assert.deepEqual(draft.expectations, expectations);
  const receipt = await submitDraft(c, author, draft);
  assert.equal(receipt.submission_status, 'ACCEPTED');
  assert.equal(receipt.worker_may_finish, true);
  const closed = await run('task close', { campaign: c.campaign, 'task-id': author.task_id, finished: true });
  assert.equal(closed.task.state, 'DONE');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'expectations' })).records.length, 1);
  const status = await run('status', { campaign: c.campaign });
  assert.equal(status.complete, false);
  assert.ok(status.obligations.some(item => item.type === 'PLAN_REQUIRED'));
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
