import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { loadDependencies, getDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
await loadDependencies({ setup: true });
function call(command, args = {}, expected = 0) {
  const argv = command.split(' ').concat(Object.entries(args).flatMap(([k, v]) => [`--${k}`, String(v)]));
  const r = spawnSync(process.execPath, [cli, ...argv], { encoding: 'utf8' });
  assert.equal(r.status, expected, `${command}: ${r.stdout}\n${r.stderr}`);
  return JSON.parse(r.stdout);
}
async function setup(t) {
  const project = await mkdtemp(path.join(tmpdir(), 'controller space-'));
  t.after(() => rm(project, { recursive: true, force: true }));
  await writeFile(path.join(project, 'app.mjs'), 'console.log("ready")\n');
  await writeFile(path.join(project, '.gitignore'), 'agentic-tests/\n');
  for (const args of [['init', '-q'], ['config', 'user.name', 'Fixture'], ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'], ['commit', '-qm', 'fixture']]) assert.equal(spawnSync('git', args, { cwd: project }).status, 0);
  const init = call('init', { project, slug: 'public', 'host-capacity': 8 });
  let seq = 0;
  const c = { project, campaign: init.campaign_path, config: init.campaign };
  c.json = async obj => { const f = path.join(c.campaign, `request-${++seq}.json`); await writeFile(f, JSON.stringify(obj)); return f; };
  c.create = async (request, expected = 0) => call('task create', { campaign: c.campaign, request: await c.json(request) }, expected);
  c.start = task => { call('task dispatch', { campaign: c.campaign, 'task-id': task.task_id }); call('task bind', { campaign: c.campaign, 'task-id': task.task_id, handle: `host-${task.task_id}` }); };
  c.draft = async (task, i = 0) => getDependencies().YAML.parse(await readFile(path.join(c.campaign, task.draft_paths[i]), 'utf8'));
  c.submit = async (task, draft, expected = 0) => call('submit', { campaign: c.campaign, 'task-id': task.task_id, file: await c.json(draft) }, expected);
  c.close = task => call('task close', { campaign: c.campaign, 'task-id': task.task_id, finished: true });
  c.records = options => call('records', { campaign: c.campaign, ...options }).records;
  return c;
}

test('typed project inputs are resolved read-only with concrete bounded handoffs and symlink containment', async t => {
  const c = await setup(t);
  await mkdir(path.join(c.project, 'src'));
  await writeFile(path.join(c.project, 'src', 'product.mjs'), 'export const product = true;\n');
  const { task, handoff_path } = await c.create({ role: 'feature-scout', requested_action: 'Discover product features', required_inputs: [{ base: 'project', path: '.' }, { base: 'project', path: 'src/product.mjs' }] });
  c.start(task);
  const handoff = await readFile(path.join(c.campaign, handoff_path), 'utf8');
  for (const value of [cli, c.project, c.campaign, 'src/product.mjs', 'references/roles/feature-scout.md', 'submit', '--check', '--task-id', task.task_id, 'worker_may_finish', 'Write scope']) assert.ok(handoff.includes(value), value);
  await symlink(tmpdir(), path.join(c.project, 'escape'));
  const rejected = await c.create({ role: 'feature-scout', requested_action: 'Read outside source', required_inputs: [{ base: 'project', path: 'escape' }] }, 3);
  assert.equal(rejected.error.code, 'UNSAFE_INPUT');
  const bad = await c.create({ role: 'feature-scout', requested_action: 'Read traversal', required_inputs: [{ base: 'project', path: '../other' }] }, 3);
  assert.equal(bad.error.code, 'UNSAFE_INPUT');
});

test('validation failures name bad fields and allowed values without echoing supplied secrets', async t => {
  const c = await setup(t);
  const invalid = await c.create({ role: 'bad-role-SECRET_VALUE', requested_action: 'Inspect features', api_secret: 'SECRET_VALUE' }, 3);
  assert.equal(invalid.error.code, 'INVALID_RECORD');
  assert.ok(invalid.error.issues.some(i => i.field === '/role' && i.rule === 'enum' && i.allowed.includes('feature-scout')));
  assert.ok(invalid.error.issues.some(i => i.property === 'api_secret' && i.remedy));
  assert.ok(invalid.next_actions.length);
  assert.ok(!JSON.stringify(invalid).includes('SECRET_VALUE'));
});

async function author(c, slug, priority = 'P1') {
  const { task } = await c.create({ role: 'scenario-author', slug, requested_action: `Write ${slug}` });
  c.start(task);
  const root = path.dirname(path.join(c.campaign, task.outputs[0].path));
  await writeFile(path.join(root, '01-test-case.md'), 'Given ready product\nWhen run\nThen [E1] returns cats\n');
  await writeFile(path.join(root, '03-how-to-run.md'), 'Run node app.mjs and save the full stdout JSON output.');
  const draft = await c.draft(task);
  draft.expectations = [{ id: 'E1', statement: 'Returns cats', source: { type: 'user_request', reference: 'Approved cats requirement' }, priority, review_count: priority === 'P0' ? 2 : 1, observable: { description: 'Contains cats' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Full output JSON' }] }];
  await c.submit(task, draft); c.close(task); return task.case_ids[0];
}
async function runtime(c, target = 'G001') {
  const revision = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: c.project, encoding: 'utf8' }).stdout.trim();
  const draft = { target_id: target, runtime_type: 'cli', source: { revision, worktree: c.project }, command: { argv: [process.execPath, 'app.mjs'], cwd: c.project }, readiness: { type: 'process', body_contains: 'ready', timeout_ms: 3000 } };
  return call('runtime start', { campaign: c.campaign, file: await c.json(draft) }).environment;
}
async function plan(c, cases, target = 'G001', dependencies = {}) {
  const { task } = await c.create({ role: 'planner', target_id: target, requested_action: 'Plan accepted scope' }); c.start(task);
  const p = await c.draft(task);
  Object.assign(p, { target_id: target, scope: { in_scope: ['Cats'], out_of_scope: [] }, cases: cases.map(case_id => ({ case_id, spec_revision: 'S001', target_id: target, depends_on: dependencies[case_id] || [], resources: [] })), coverage: [{ source: 'Approved requirement', case_ids: cases }] });
  await c.submit(task, p); c.close(task);
  const { task: auditor } = await c.create({ role: 'plan-auditor', plan_id: task.plan_id, requested_action: 'Audit plan' }); c.start(auditor);
  const a = await c.draft(auditor); Object.assign(a, { outcome: 'approved', findings: [], artifacts: [] }); await c.submit(auditor, a); c.close(auditor);
  call('plan accept', { campaign: c.campaign, file: path.join(c.campaign, task.outputs[0].path), audit: path.join(c.campaign, auditor.outputs[0].path) });
}
async function executeCase(c, cases, { gap = false, notRun = false, request = {} } = {}) {
  const { task } = await c.create({ role: 'executor', case_ids: cases, requested_action: 'Run actual case', ...request }); c.start(task);
  for (let i = 0; i < task.outputs.length; i++) {
    const d = await c.draft(task, i), evidencePath = `${path.posix.dirname(task.outputs[i].path)}/evidences/output.json`;
    if (!gap) await writeFile(path.join(c.campaign, evidencePath), '{"results":[]}');
    Object.assign(d, { execution_status: notRun ? 'NOT_RUN' : gap ? 'PARTIAL' : 'COMPLETED', observations: [{ expectation_id: 'E1', observed: 'No cats', evidence_ids: gap ? [] : ['EV1'], gaps: gap ? [{ requirement_id: 'ER1', reason: 'Capture unavailable' }] : [] }], evidence: gap ? [] : [{ id: 'EV1', path: evidencePath, type: 'json', expectation_ids: ['E1'] }], ...(notRun ? { blocker: { reason_code: 'NOT_EXECUTED', detail: 'Unavailable fixture' } } : {}) });
    await c.submit(task, d);
  }
  c.close(task); return task;
}
async function reviewCase(c, executed, outcome = 'FAIL', findings = [], expected = 0, slot = 'a') {
  const { task } = await c.create({ role: 'verifier', case_ids: executed.case_ids, target_id: executed.target_id, round_id: executed.round_id, verification_slot: slot, requested_action: 'Review saved evidence', ...(executed.group ? { group: executed.group } : {}) }); c.start(task);
  for (let i = 0; i < task.outputs.length; i++) {
    const d = await c.draft(task, i), e = c.records({ 'record-id': executed.outputs[i].record_id })[0];
    Object.assign(d, { execution_record_id: e.record_id, reviews: [{ expectation_id: 'E1', verdict: outcome, expected: 'Returns cats', observed: 'No cats', evidence_ids: e.evidence.map(x => x.id), reason: 'Observed saved stdout' }], inspected_evidence: e.evidence.map(x => ({ id: x.id, sha256: x.sha256, method: 'Read JSON', observation: 'Missing cats' })), findings });
    const result = await c.submit(task, d, expected); if (expected) return result;
  }
  c.close(task); call('reconcile', { campaign: c.campaign }); return task;
}
const retryContext = n => ({ previous_failure: 'The latest round was inconclusive', what_changed: `Configured capture approach ${n}`, hypothesis: `Capture approach ${n} records actual output`, do_not_repeat: ['Do not infer missing evidence'], remaining_attempts: 5 - n });

test('current independently reviewed FAIL promotes a gap lineage and withdrawal revokes product authorization', async t => {
  const c = await setup(t), id = await author(c, 'cats'); await runtime(c); await plan(c, [id]);
  const first = await executeCase(c, [id], { gap: true }); await reviewCase(c, first, 'INCONCLUSIVE', [{ class: 'PRODUCT_DEFECT', summary: 'Unsupported product label' }]);
  let finding = c.records({ kind: 'finding' })[0]; assert.equal(finding.class, 'EVIDENCE_GAP');
  const original = c.records({ kind: 'execution' })[0];
  const retry = await executeCase(c, [id], { request: { finding_id: finding.finding_id, prior_context: retryContext(1) } });
  const verifier = await reviewCase(c, retry);
  finding = c.records({ kind: 'finding' })[0];
  assert.equal(finding.finding_id, 'F0001'); assert.equal(finding.class, 'PRODUCT_DEFECT'); assert.equal(finding.attempts, 2); assert.equal(finding.authorized, true);
  assert.deepEqual(c.records({ 'record-id': original.record_id })[0], original);
  assert.deepEqual(finding.classification_history.map(x => x.class), ['EVIDENCE_GAP', 'PRODUCT_DEFECT']);
  call('task interrupt', { campaign: c.campaign, 'task-id': verifier.task_id, reason: 'Review contaminated', finished: true });
  finding = c.records({ kind: 'finding' })[0]; assert.equal(finding.authorized, false); assert.equal(finding.class, 'PRODUCT_DEFECT');
  const invalid = await c.create({ role: 'ticket-writer', finding_id: finding.finding_id, requested_action: 'Create ticket' }, 3); assert.equal(invalid.error.code, 'UNCONFIRMED_DEFECT');
});

test('explicit reviewer lineage joins cases and a supported immutable link joins existing roots', async t => {
  const c = await setup(t), ids = [];
  for (const slug of ['cats-a', 'cats-b', 'cats-c', 'cats-d', 'cats-e', 'cats-f']) ids.push(await author(c, slug)); await runtime(c); await plan(c, ids);
  const a = await executeCase(c, [ids[0]]); await reviewCase(c, a);
  const b = await executeCase(c, ids.slice(1, 5), { request: { group: { shared_setup: 'Same baseline fixture', reset: 'Fresh independent CLI invocation per case', independent: true } } }); await reviewCase(c, b, 'FAIL', [{ class: 'PRODUCT_DEFECT', summary: 'Same actual root', lineage_id: 'F0001', expectation_ids: ['E1'] }]);
  let findings = c.records({ kind: 'finding' }); assert.equal(findings.length, 1); assert.deepEqual(findings[0].case_ids, ids.slice(0, 5));
  const d = await executeCase(c, [ids[5]]); await reviewCase(c, d);
  findings = c.records({ kind: 'finding' }); assert.equal(findings.length, 2);
  const before = c.records({ kind: 'verdict' });
  const request = { from_finding_id: 'F0002', into_finding_id: 'F0001', evidence_record_ids: [a.outputs[0].record_id, d.outputs[0].record_id], reason: 'Independent failures identify the same missing shared search filter' };
  const linked = call('finding link', { campaign: c.campaign, file: await c.json(request) }); assert.equal(linked.effective_finding_id, 'F0001');
  const history = call('records', { campaign: c.campaign, 'finding-id': 'F0002' }); assert.equal(history.effective_finding_id, 'F0001'); assert.ok(history.records.some(r => r.kind === 'finding_link'));
  findings = c.records({ kind: 'finding' }); assert.equal(findings.length, 1); assert.deepEqual(findings[0].case_ids, ids); assert.equal(findings[0].attempts, 1, 'six cases exercise one initial baseline intervention; variants cannot exhaust the five-correction budget');
  assert.deepEqual(c.records({ kind: 'verdict' }), before);
  const cycle = call('finding link', { campaign: c.campaign, file: await c.json({ ...request, from_finding_id: 'F0001', into_finding_id: 'F0002' }) }, 3); assert.equal(cycle.error.code, 'LINEAGE_CYCLE');
});

test('case reservations block duplicate and overlapping groups through interrupted live workers and pending review', async t => {
  const c = await setup(t), ids = [await author(c, 'reserved-a'), await author(c, 'reserved-b')]; await runtime(c); await plan(c, ids);
  const first = (await c.create({ role: 'executor', case_ids: [ids[0]], requested_action: 'First reservation' })).task;
  const duplicate = await c.create({ role: 'executor', case_ids: [ids[0]], requested_action: 'Duplicate reservation' }, 4); assert.equal(duplicate.error.code, 'CASE_RESERVED');
  const overlap = await c.create({ role: 'executor', case_ids: ids, group: { shared_setup: 'Read-only fixture', reset: 'Independent invocation', independent: true }, requested_action: 'Overlapping group' }, 4); assert.equal(overlap.error.code, 'CASE_RESERVED');
  c.start(first); call('task interrupt', { campaign: c.campaign, 'task-id': first.task_id, reason: 'Host unknown' });
  assert.equal((await c.create({ role: 'executor', case_ids: [ids[0]], requested_action: 'Still reserved' }, 4)).error.code, 'CASE_RESERVED');
  call('task interrupt', { campaign: c.campaign, 'task-id': first.task_id, reason: 'Host stopped', finished: true });
  const executed = await executeCase(c, [ids[0]]);
  const awaiting = await c.create({ role: 'executor', case_ids: [ids[0]], requested_action: 'Awaiting review' }, 4); assert.equal(awaiting.error.code, 'VERIFICATION_REQUIRED');
  await reviewCase(c, executed);
  const repeated = await c.create({ role: 'executor', case_ids: [ids[0]], intervention: { kind: 'BASELINE', ref: 'initial-assessment' }, prior_context: retryContext(1), requested_action: 'Same baseline again' }, 3); assert.equal(repeated.error.code, 'REPEAT_INTERVENTION');
});
