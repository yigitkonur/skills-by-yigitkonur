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
  assert.equal(spawnSync('git', ['remote', 'add', 'origin', 'git@github.com:example/project.git'], { cwd: project }).status, 0);
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
  return { planner: task, auditor };
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
  const verifier = await reviewCase(c, retry, 'FAIL', [{ class: 'PRODUCT_DEFECT', summary: 'Now confirmed by actual saved evidence', lineage_id: 'F0001', expectation_ids: ['E1'] }]);
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
  const diagnosis = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Diagnose all six affected cases' })).task;
  assert.deepEqual(diagnosis.related_case_ids, ids); assert.equal(diagnosis.case_ids.length, 4);
  const handoff = await readFile(path.join(c.campaign, `tasks/${diagnosis.task_id}/10-handoff.md`), 'utf8'); assert.ok(handoff.includes(ids.join(', ')));
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

test('corrective handoffs receive the latest failure history and stale dispatch requires a refreshed task', async t => {
  const c = await setup(t), id = await author(c, 'history'); await runtime(c); await plan(c, [id]);
  const first = await executeCase(c, [id]); await reviewCase(c, first);
  const old = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Find the root cause' })).task;
  assert.ok(old.prior_context); assert.ok(old.history_basis.record_ids.includes(first.outputs[0].record_id));
  const next = await executeCase(c, [id], { request: { prior_context: retryContext(1) } }); await reviewCase(c, next);
  const stale = call('task dispatch', { campaign: c.campaign, 'task-id': old.task_id }, 4); assert.equal(stale.error.code, 'STALE_RETRY_CONTEXT'); assert.ok(stale.error.details.some(x => x.record_ids?.includes(next.outputs[0].record_id)));
  call('task interrupt', { campaign: c.campaign, 'task-id': old.task_id, reason: 'Superseded history', finished: true });
  const current = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Diagnose using fresh failed execution' })).task;
  assert.ok(current.required_inputs.includes(next.outputs[0].path)); assert.ok(current.prior_context.previous_failure.includes(next.outputs[0].record_id)); assert.equal(current.prior_context.remaining_attempts, 3); c.start(current);
  const bad = await c.create({ role: 'verifier', case_ids: [id], target_id: 'G001', round_id: next.round_id, verification_slot: 'a', requested_action: 'Review with forbidden peer context', required_inputs: [current.outputs[0].path] }, 3); assert.equal(bad.error.code, 'BLIND_INPUT');
});

test('ready tasks rank by priority and downstream work consistently across every query surface', async t => {
  const c = await setup(t), leaf = await author(c, 'leaf', 'P3'), urgent = await author(c, 'urgent', 'P0'), root = await author(c, 'root', 'P3'), child = await author(c, 'child', 'P3'); await runtime(c); await plan(c, [leaf, urgent, root, child], 'G001', { [child]: [root] });
  const tasks = []; for (const id of [leaf, urgent, root, child]) tasks.push((await c.create({ role: 'executor', case_ids: [id], requested_action: 'Run when ready' })).task);
  const status = call('status', { campaign: c.campaign }); assert.deepEqual(status.ready, [tasks[1].task_id, tasks[2].task_id, tasks[0].task_id]); assert.equal(status.ready_details[0].priority, 'P0'); assert.equal(status.ready_details[1].unblocks, 1);
  assert.deepEqual(c.records({ ready: true }).map(x => x.task_id), status.ready);
  assert.deepEqual(call('reconcile', { campaign: c.campaign }).ready, status.ready);
  const notebook = getDependencies().YAML.parse(await readFile(path.join(c.campaign, '01-notebook.view.yaml'), 'utf8')); assert.deepEqual(notebook.ready_details, status.ready_details);
});

test('delivery binds the tested project GitHub remote and remote drift leaves unrelated work available', async t => {
  const c = await setup(t); assert.deepEqual(c.config.github_repository, { remote: 'origin', repository: 'example/project' });
  const id = await author(c, 'delivery'); await runtime(c); await plan(c, [id]); const failed = await executeCase(c, [id]); await reviewCase(c, failed);
  const diagnosis = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Diagnose missing filter' })).task; c.start(diagnosis);
  const d = await c.draft(diagnosis); Object.assign(d, { conclusion: 'confirmed', summary: 'Shared filter is wrong', root_cause: 'Missing search filter', evidence_record_ids: [failed.outputs[0].record_id], artifacts: [] }); await c.submit(diagnosis, d); c.close(diagnosis);
  const { task: ticket, handoff_path } = await c.create({ role: 'ticket-writer', finding_id: 'F0001', requested_action: 'Create one project issue' }); c.start(ticket);
  const handoff = await readFile(path.join(c.campaign, handoff_path), 'utf8'); assert.ok(handoff.includes("--repo 'example/project'"));
  const body_path = ticket.companion_paths.body; await writeFile(path.join(c.campaign, body_path), 'Confirmed missing filter; independent failure evidence.');
  const draft = await c.draft(ticket); Object.assign(draft, { issue_url: 'https://github.com/other/repo/issues/1', body_path, dedup_marker: `agentic-tests:${c.config.campaign_id}:F0001`, artifacts: [] });
  assert.equal((await c.submit(ticket, draft, 3)).error.code, 'GITHUB_REPOSITORY_MISMATCH'); draft.issue_url = 'https://github.com/example/project/issues/1'; await c.submit(ticket, draft); c.close(ticket);
  assert.equal(spawnSync('git', ['remote', 'set-url', 'origin', 'https://github.com/other/repo.git'], { cwd: c.project }).status, 0);
  assert.equal((await c.create({ role: 'implementer', finding_id: 'F0001', requested_action: 'Fix the filter' }, 4)).error.code, 'GITHUB_REMOTE_DRIFT');
  const independent = (await c.create({ role: 'feature-scout', requested_action: 'Discover an unrelated local feature' })).task; c.start(independent);
});

test('runtime recovery allocates a fresh immutable source-compatible target and requires its accepted plan and fresh proof', async t => {
  const c = await setup(t), id = await author(c, 'recovery');
  const revision = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: c.project, encoding: 'utf8' }).stdout.trim();
  const failed = call('runtime start', { campaign: c.campaign, file: await c.json({ target_id: 'G001', runtime_type: 'cli', source: { revision, worktree: c.project }, command: { argv: [process.execPath, 'app.mjs'], cwd: c.project }, readiness: { type: 'process', body_contains: 'unavailable-marker', timeout_ms: 300 } }) }, 5); assert.equal(failed.error.code, 'RUNTIME_START_FAILED');
  await plan(c, [id]); const old = c.records({ kind: 'environment' })[0];
  const recovery = call('runtime recover', { campaign: c.campaign, 'target-id': 'G001', file: await c.json({ reason: 'Readiness marker corrected after recorded failure', requested_action: 'Start the same source with the correct marker' }) });
  assert.equal(recovery.successor_target_id, 'G002'); assert.equal(recovery.task.role, 'environment-operator'); assert.equal(recovery.recovery.expected_revision, revision);
  assert.deepEqual(c.records({ 'record-id': old.record_id })[0], old);
  const duplicate = call('runtime recover', { campaign: c.campaign, 'target-id': 'G001', file: await c.json({ reason: 'Duplicate recovery' }) }, 4); assert.equal(duplicate.error.code, 'RECOVERY_EXISTS');
  c.start(recovery.task); const draft = await c.draft(recovery.task); draft.readiness.body_contains = 'ready';
  call('runtime start', { campaign: c.campaign, file: await c.json(draft) }); c.close(recovery.task);
  const status = call('status', { campaign: c.campaign }); assert.equal(status.latest_target_id, 'G002'); assert.ok(status.obligations.some(x => x.type === 'TARGET_PLAN_REQUIRED')); assert.equal(status.complete, false);
  await plan(c, [id], 'G002'); const execution = await executeCase(c, [id]); assert.equal(execution.target_id, 'G002'); await reviewCase(c, execution, 'PASS');
  const final = call('status', { campaign: c.campaign }); assert.equal(final.cases[0].outcome, 'PASS'); assert.equal(final.cases[0].proof_valid, true); assert.ok(final.obligations.some(x => x.type === 'CLOSURE_AUDIT_REQUIRED'));
});

test('actual source changes block dispatch, submission, and current proof while legacy attestations stay explicit blockers', async t => {
  const c = await setup(t), id = await author(c, 'source-boundary'); await runtime(c); await plan(c, [id]);
  const task = (await c.create({ role: 'executor', case_ids: [id], requested_action: 'Execute attested source' })).task;
  const app = path.join(c.project, 'app.mjs'), original = await readFile(app, 'utf8'); await writeFile(app, 'console.log("changed")\n');
  const blocked = call('task dispatch', { campaign: c.campaign, 'task-id': task.task_id }, 3); assert.equal(blocked.error.code, 'SOURCE_CHANGED');
  await writeFile(app, original); c.start(task);
  const d = await c.draft(task), artifact = `${path.posix.dirname(task.outputs[0].path)}/evidences/output.json`; await writeFile(path.join(c.campaign, artifact), '{"results":["cats"]}'); Object.assign(d, { execution_status: 'COMPLETED', observations: [{ expectation_id: 'E1', observed: 'Cats', evidence_ids: ['EV1'], gaps: [] }], evidence: [{ id: 'EV1', path: artifact, type: 'json', expectation_ids: ['E1'] }] });
  await writeFile(app, 'console.log("changed")\n'); assert.equal((await c.submit(task, d, 3)).error.code, 'SOURCE_CHANGED');
  await writeFile(app, original); await c.submit(task, d); c.close(task); await reviewCase(c, task, 'PASS');
  await writeFile(app, 'console.log("changed")\n'); const changed = call('status', { campaign: c.campaign }); assert.equal(changed.cases[0].proof_valid, false); assert.ok(changed.obligations.some(x => x.type === 'SOURCE_CHANGED'));
  await writeFile(app, original);
  const env = c.records({ kind: 'environment' })[0]; delete env.source.attestation;
  await writeFile(path.join(c.campaign, 'environments/G001/00-environment.record.yaml'), getDependencies().YAML.stringify(env));
  const legacy = call('status', { campaign: c.campaign }); assert.equal(legacy.complete, false); assert.ok(legacy.obligations.some(x => x.type === 'SOURCE_ATTESTATION_REQUIRED')); assert.equal(c.records({ kind: 'execution' }).length, 1);
});

test('five corrections share an explicit budget and one final sweep reuses the selected passing intervention', async t => {
  const c = await setup(t), id = await author(c, 'fifth-correction'); await runtime(c); await plan(c, [id]);
  for (let n = 1; n <= 5; n++) {
    const task = await executeCase(c, [id], { request: n === 1 ? {} : { prior_context: { what_changed: `Corrective approach ${n}`, hypothesis: `Evidence for approach ${n}`, do_not_repeat: ['Previous failing corrections'] } } });
    if (n > 1) assert.equal(task.intervention.ref, `task:${task.task_id}`, 'implicit correction IDs are controller allocations, never prose equivalence');
    await reviewCase(c, task, n === 5 ? 'PASS' : 'FAIL');
    assert.equal(c.records({ kind: 'finding' })[0].attempts, n);
  }
  const sweep = await executeCase(c, [id], { request: { purpose: 'final' } }); await reviewCase(c, sweep, 'PASS');
  const finding = c.records({ kind: 'finding' })[0]; assert.equal(finding.attempts, 5); assert.equal(finding.state, 'RESOLVED'); assert.equal(sweep.prior_context.remaining_attempts, 0);
  const bypass = await c.create({ role: 'executor', case_ids: [id], purpose: 'final', requested_action: 'Repeat final again' }, 3); assert.equal(bypass.error.code, 'ATTEMPT_LIMIT');
});

test('tested-project remote discovery ignores repository and injected configuration overrides from the host', async t => {
  const c = await setup(t), installation = await setup(t);
  assert.equal(spawnSync('git', ['remote', 'set-url', 'origin', 'https://github.com/installation/skills.git'], { cwd: installation.project }).status, 0);
  const keys = ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_VALUE_0']; const saved = Object.fromEntries(keys.map(k => [k, process.env[k]]));
  try {
    Object.assign(process.env, { GIT_DIR: path.join(installation.project, '.git'), GIT_WORK_TREE: installation.project, GIT_CONFIG_COUNT: '1', GIT_CONFIG_KEY_0: 'remote.origin.url', GIT_CONFIG_VALUE_0: 'https://github.com/injected/wrong.git' });
    const bound = call('init', { project: c.project, slug: 'sanitized-identity', 'host-capacity': 2 }); assert.deepEqual(bound.campaign.github_repository, { remote: 'origin', repository: 'example/project' });
  } finally { for (const key of keys) if (saved[key] === undefined) delete process.env[key]; else process.env[key] = saved[key]; }
});

test('a latest PASS removes repair authorization even though an older immutable FAIL remains', async t => {
  const c = await setup(t), id = await author(c, 'authorization'); await runtime(c); await plan(c, [id]);
  const failed = await executeCase(c, [id]); await reviewCase(c, failed);
  const diagnosis = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Explain failure' })).task; c.start(diagnosis); const d = await c.draft(diagnosis); Object.assign(d, { conclusion: 'confirmed', summary: 'Fixture capture failed', root_cause: 'Wrong capture approach', evidence_record_ids: [failed.outputs[0].record_id], artifacts: [] }); await c.submit(diagnosis, d); c.close(diagnosis);
  const fresh = await executeCase(c, [id], { request: { prior_context: { what_changed: 'Corrected capture', hypothesis: 'Actual output includes cats', do_not_repeat: ['Wrong capture'] } } }); await reviewCase(c, fresh, 'PASS');
  const finding = c.records({ kind: 'finding' })[0]; assert.equal(finding.state, 'RESOLVED'); assert.equal(finding.authorized, false);
  assert.equal((await c.create({ role: 'ticket-writer', finding_id: 'F0001', requested_action: 'Open a stale defect ticket' }, 3)).error.code, 'UNCONFIRMED_DEFECT');
  assert.ok(c.records({ kind: 'verdict' }).some(x => x.outcome === 'FAIL'));
});

test('blind verifier packets reject corrective narrative fields before writing any handoff', async t => {
  const c = await setup(t), id = await author(c, 'blind-context'); await runtime(c); await plan(c, [id]); const executed = await executeCase(c, [id]);
  for (const extra of [{ prior_context: { previous_failure: 'Peer verdict FAIL', what_changed: 'PR fixed the defect', hypothesis: 'Prior reviewer expects PASS', do_not_repeat: ['Do not disagree'], remaining_attempts: 4 } }, { finding_id: 'F0001' }, { intervention: { kind: 'EXECUTION_APPROACH', ref: 'repair narrative' } }]) {
    const rejected = await c.create({ role: 'verifier', case_ids: [id], target_id: 'G001', round_id: executed.round_id, requested_action: 'Blindly inspect saved evidence', ...extra }, 3); assert.equal(rejected.error.code, 'BLIND_INPUT');
  }
});

test('accepted patch revisions do not consume the independent execution budget before any retest runs', async t => {
  const c = await setup(t), id = await author(c, 'patch-budget'); await runtime(c); await plan(c, [id]); const failed = await executeCase(c, [id]); await reviewCase(c, failed);
  const diagnosis = (await c.create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Diagnose search' })).task; c.start(diagnosis); const diagnosisDraft = await c.draft(diagnosis); assert.equal(diagnosis.artifact_directory, `tasks/${diagnosis.task_id}/artifacts`); Object.assign(diagnosisDraft, { conclusion: 'confirmed', summary: 'Wrong search filter', root_cause: 'Wrong comparison key', evidence_record_ids: [failed.outputs[0].record_id], artifacts: [] }); await c.submit(diagnosis, diagnosisDraft); c.close(diagnosis);
  const ticket = (await c.create({ role: 'ticket-writer', finding_id: 'F0001', requested_action: 'Record one ticket' })).task; c.start(ticket); const issue = await c.draft(ticket); await writeFile(path.join(c.campaign, issue.body_path), 'Confirmed search failure with independent evidence.'); Object.assign(issue, { issue_url: 'https://github.com/example/project/issues/1', dedup_marker: `agentic-tests:${c.config.campaign_id}:F0001`, artifacts: [] }); await c.submit(ticket, issue); c.close(ticket);
  for (let n = 1; n <= 5; n++) {
    const task = (await c.create({ role: 'implementer', finding_id: 'F0001', requested_action: `Record patch revision ${n} before integration` })).task; c.start(task);
    const d = await c.draft(task), body = d.pr_body_path, check = d.checks[0].artifact_path, worktree = d.worktree;
    assert.equal(worktree, task.worktree_path); assert.equal(path.isAbsolute(worktree), true); assert.ok(!worktree.startsWith(c.project + path.sep)); assert.equal(d.pr_body_path, task.companion_paths.pr_body); assert.equal(check, task.companion_paths.check);
    assert.ok((await readFile(path.join(c.campaign, `tasks/${task.task_id}/10-handoff.md`), 'utf8')).includes(worktree));
    await mkdir(worktree, { recursive: true }); t.after(() => rm(worktree, { recursive: true, force: true })); await writeFile(path.join(c.campaign, body), 'Search correction. Related issue #1. Retest pending.'); await writeFile(path.join(c.campaign, check), 'Fixture developer check passed.');
    Object.assign(d, { commit: `fixture-patch-${n}`, worktree, pr_url: `https://github.com/example/project/pull/${n + 1}`, pr_body_path: body, changed_files: ['app.mjs'], checks: [{ command: 'fixture-check', exit_code: 0, artifact_path: check }], summary: `Unexercised patch revision ${n}`, artifacts: [] });
    if (n === 1) {
      assert.equal((await c.submit(task, { ...d, worktree: c.project }, 3)).error.code, 'WRONG_ASSIGNMENT');
      assert.equal((await c.submit(task, { ...d, pr_body_path: issue.body_path }, 3)).error.code, 'WRONG_ASSIGNMENT');
      assert.equal((await c.submit(task, { ...d, checks: [{ ...d.checks[0], artifact_path: issue.body_path }] }, 3)).error.code, 'WRONG_ASSIGNMENT');
    }
    await c.submit(task, d); c.close(task);
    assert.equal(c.records({ kind: 'finding' })[0].attempts, 1);
  }
  assert.equal(c.records({ kind: 'implementation' }).length, 5);
});

test('legacy ambiguous corrections and excess history remain visible without blocking unrelated discovery', async t => {
  const c = await setup(t), id = await author(c, 'legacy-history'); await runtime(c); await plan(c, [id]); const initial = await executeCase(c, [id]); await reviewCase(c, initial);
  const retry = await executeCase(c, [id], { request: { prior_context: { what_changed: 'Legacy correction', hypothesis: 'Capture the output', do_not_repeat: ['Initial approach'] } } }); await reviewCase(c, retry);
  const taskFile = path.join(c.campaign, `tasks/${retry.task_id}/00-task.record.yaml`), task = getDependencies().YAML.parse(await readFile(taskFile, 'utf8')); delete task.attempt_id; delete task.intervention; await writeFile(taskFile, getDependencies().YAML.stringify(task));
  const contextFile = path.join(c.campaign, path.dirname(retry.outputs[0].path), '00-context.record.yaml'), context = getDependencies().YAML.parse(await readFile(contextFile, 'utf8')); delete context.attempt_id; delete context.intervention; await writeFile(contextFile, getDependencies().YAML.stringify(context));
  const findingFile = path.join(c.campaign, 'findings/F0001-t0001/00-finding.record.yaml'), finding = getDependencies().YAML.parse(await readFile(findingFile, 'utf8'));
  for (let n = 0; n < 5; n++) finding.attempt_rounds.push({ case_id: id, round_id: `R90${n}`, execution_record_id: `LEGACY-EXEC-${n}` }); await writeFile(findingFile, getDependencies().YAML.stringify(finding));
  const history = await readFile(findingFile, 'utf8'), before = c.records({ kind: 'execution' });
  const status = call('status', { campaign: c.campaign }); assert.ok(status.obligations.some(x => x.type === 'ATTEMPT_MAPPING_REQUIRED')); assert.ok(status.obligations.some(x => x.type === 'ATTEMPT_LIMIT')); assert.equal(status.findings[0].attempts, 7); assert.equal(status.findings[0].state, 'EXHAUSTED');
  const rejected = await c.create({ role: 'executor', case_ids: [id], requested_action: 'Unproven sixth retry', prior_context: { what_changed: 'New correction', hypothesis: 'Unproven mapping', do_not_repeat: ['Do not erase history'] } }, 4); assert.equal(rejected.error.code, 'VERIFICATION_REQUIRED');
  const scout = (await c.create({ role: 'feature-scout', requested_action: 'Discover an independent feature' })).task; c.start(scout); assert.deepEqual(c.records({ kind: 'execution' }), before); assert.equal(await readFile(findingFile, 'utf8'), history);
});

test('replayed legacy duplicate executor reservations are surfaced and remain intact until explicitly interrupted', async t => {
  const c = await setup(t), id = await author(c, 'legacy-reservations'); await runtime(c); await plan(c, [id]); const first = (await c.create({ role: 'executor', case_ids: [id], requested_action: 'Existing original reservation' })).task;
  const duplicate = structuredClone(first); Object.assign(duplicate, { task_id: 'J90001', record_id: 'J90001', actor_id: 'A90001', requested_action: 'Historical duplicate reservation' }); await mkdir(path.join(c.campaign, 'tasks/J90001')); const file = path.join(c.campaign, 'tasks/J90001/00-task.record.yaml'); await writeFile(file, getDependencies().YAML.stringify(duplicate)); const original = await readFile(file, 'utf8');
  const status = call('status', { campaign: c.campaign }); assert.ok(status.blocked.filter(x => [first.task_id, duplicate.task_id].includes(x.task_id)).every(x => x.reasons.some(r => r.startsWith('CASE_RESERVED:'))));
  assert.equal(call('task dispatch', { campaign: c.campaign, 'task-id': first.task_id }, 4).error.code, 'CASE_RESERVED'); assert.equal(await readFile(file, 'utf8'), original);
  call('task interrupt', { campaign: c.campaign, 'task-id': duplicate.task_id, reason: 'Controller confirmed unused duplicate context', finished: true }); c.start(first);
});


test('role packets allocate companion artifacts and route plan auditors to bounded current proof', async t => {
  const c = await setup(t);
  const planner = (await c.create({ role: 'planner', requested_action: 'Plan the approved case set' })).task;
  assert.equal(planner.companion_paths?.scope, 'plans/P001/00-scope.md');
  assert.ok((await readFile(path.join(c.campaign, planner.companion_paths.scope), 'utf8')).includes('Scope'));
  assert.ok((await readFile(path.join(c.campaign, `tasks/${planner.task_id}/10-handoff.md`), 'utf8')).includes(path.join(c.campaign, planner.companion_paths.scope)));
  const scout = (await c.create({ role: 'feature-scout', requested_action: 'Inspect unrelated feature' })).task;
  assert.equal(scout.artifact_directory, `tasks/${scout.task_id}/artifacts`);
  c.start(scout); const scoutDraft = await c.draft(scout), unrelated = 'discovery/unassigned.txt'; await writeFile(path.join(c.campaign, unrelated), 'Unassigned artifact');
  Object.assign(scoutDraft, { features: [{ id: 'unrelated', title: 'Unrelated feature', source: { type: 'user_request', reference: 'Separate approved source' }, subfeatures: [] }], unknowns: [], artifacts: [{ path: unrelated, type: 'text' }] });
  assert.equal((await c.submit(scout, scoutDraft, 3)).error.code, 'WRONG_ASSIGNMENT');
  const note = `${scout.artifact_directory}/notes.md`; await writeFile(path.join(c.campaign, note), 'Unavailable external tool'); scoutDraft.artifacts = [{ path: note, type: 'text' }]; await c.submit(scout, scoutDraft); c.close(scout);
  const id = await author(c, 'audit-inputs'); await runtime(c); const accepted = await plan(c, [id]);
  const spec = c.records({ kind: 'expectations' })[0];
  const specPath = `cases/${id}-audit-inputs/specs/${spec.spec_revision}`;
  for (const input of [`${specPath}/01-test-case.md`, `${specPath}/02-expectations.record.yaml`, `${specPath}/03-how-to-run.md`, 'environments/G001/00-environment.record.yaml']) assert.ok(accepted.auditor.required_inputs.includes(input), input);
  const executed = await executeCase(c, [id]); const reviewed = await reviewCase(c, executed);
  const auditor = (await c.create({ role: 'plan-auditor', phase: 'closure', requested_action: 'Audit current proof' })).task;
  for (const input of [executed.outputs[0].path, reviewed.outputs[0].path, `${path.dirname(executed.outputs[0].path)}/00-context.record.yaml`, `${path.dirname(executed.outputs[0].path)}/30-verdict--FAIL.record.yaml`, 'findings/F0001-t0001/00-finding.record.yaml']) assert.ok(auditor.required_inputs.includes(input), input);
  assert.ok(!auditor.required_inputs.includes(scout.outputs[0].path)); assert.ok(!auditor.required_inputs.includes(note));
});

test('linking roots preserves distinct local correction labels while grouped members share one intervention', async t => {
  const c = await setup(t), ids = [await author(c, 'label-a'), await author(c, 'label-b')]; await runtime(c); await plan(c, ids);
  for (const id of ids) { const first = await executeCase(c, [id]); await reviewCase(c, first); }
  const corrections = [];
  for (let index = 0; index < ids.length; index++) {
    const corrected = await executeCase(c, [ids[index]], { request: { intervention: { kind: 'EXECUTION_APPROACH', ref: 'retry-1' }, prior_context: { what_changed: ['Use a fresh session', 'Use corrected seed data'][index], hypothesis: ['Session expired', 'Seed omitted the record'][index], do_not_repeat: ['Original failing approach'] } } });
    await reviewCase(c, corrected); corrections.push(corrected);
  }
  call('finding link', { campaign: c.campaign, file: await c.json({ from_finding_id: 'F0002', into_finding_id: 'F0001', evidence_record_ids: corrections.map(task => task.outputs[0].record_id), reason: 'Current independent failures establish the same shared root after distinct corrections' }) });
  assert.equal(c.records({ kind: 'finding' })[0].attempts, 3, 'one baseline and two distinct corrections remain after linking');
  assert.notEqual(corrections[0].attempt_id, corrections[1].attempt_id);
  const shared = await executeCase(c, ids, { request: { group: { shared_setup: 'One corrected shared fixture', reset: 'Fresh process for each case', independent: true }, intervention: { kind: 'EXECUTION_APPROACH', ref: 'linked-correction' }, prior_context: { what_changed: 'One new shared fixture for both variants', hypothesis: 'The shared fixture captures each result', do_not_repeat: ['Previous separate corrections'] } } });
  await reviewCase(c, shared); assert.equal(c.records({ kind: 'finding' })[0].attempts, 4);
});

test('a changed capture after an integrated inconclusive retest gets a fresh intervention', async t => {
  const c = await setup(t), id = await author(c, 'integrated-capture'); await runtime(c); await plan(c, [id]);
  const failed = await executeCase(c, [id]); await reviewCase(c, failed);
  const deliver = async (role, fields) => {
    const { task } = await c.create({ role, finding_id: 'F0001', requested_action: `Record synthetic ${role} boundary` }); c.start(task);
    const draft = await c.draft(task); Object.assign(draft, await fields(task, draft)); await c.submit(task, draft); c.close(task); return draft;
  };
  await deliver('diagnostician', () => ({ conclusion: 'confirmed', summary: 'Fixture filter failed', root_cause: 'Filter key mismatch', evidence_record_ids: [failed.outputs[0].record_id], artifacts: [] }));
  await deliver('ticket-writer', async (_task, draft) => { await writeFile(path.join(c.campaign, draft.body_path), 'Confirmed fixture mismatch.'); return { issue_url: 'https://github.com/example/project/issues/1', dedup_marker: `agentic-tests:${c.config.campaign_id}:F0001`, artifacts: [] }; });
  const commit = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: c.project, encoding: 'utf8' }).stdout.trim();
  const patch = await deliver('implementer', async (task, draft) => {
    await mkdir(task.worktree_path, { recursive: true }); t.after(() => rm(task.worktree_path, { recursive: true, force: true }));
    await writeFile(path.join(c.campaign, draft.pr_body_path), 'Related issue #1. Retest pending.'); await writeFile(path.join(c.campaign, draft.checks[0].artifact_path), 'Synthetic developer boundary passed.');
    return { commit, pr_url: 'https://github.com/example/project/pull/2', changed_files: ['app.mjs'], checks: [{ ...draft.checks[0], command: 'fixture check', exit_code: 0 }], summary: 'Synthetic delivery boundary for controller retry state', artifacts: [] };
  });
  const integration = await deliver('integrator', () => ({ implementation_record_id: patch.record_id, new_target_id: 'G002', commit, affected_case_ids: [id], retest_obligations: [{ case_id: id, reason: 'Independently retest recorded correction' }], artifacts: [] }));
  await runtime(c, 'G002'); await plan(c, [id], 'G002');
  const initial = await executeCase(c, [id], { gap: true, request: { purpose: 'retest', prior_context: retryContext(1) } }); await reviewCase(c, initial, 'INCONCLUSIVE');
  assert.deepEqual(initial.intervention, { kind: 'INTEGRATION', ref: integration.record_id }); assert.equal(c.records({ kind: 'finding' })[0].attempts, 2);
  const changed = await executeCase(c, [id], { request: { purpose: 'retest', prior_context: { what_changed: 'Capture stdout using the correct descriptor', hypothesis: 'The original redirection lost JSON', do_not_repeat: ['Wrong descriptor'] } } });
  assert.equal(changed.intervention.kind, 'EXECUTION_APPROACH'); assert.notEqual(changed.attempt_id, initial.attempt_id); await reviewCase(c, changed, 'PASS'); assert.equal(c.records({ kind: 'finding' })[0].attempts, 3);
  const final = await executeCase(c, [id], { request: { purpose: 'final' } }); assert.equal(final.attempt_id, changed.attempt_id); await reviewCase(c, final, 'PASS'); assert.equal(c.records({ kind: 'finding' })[0].attempts, 3);
});
