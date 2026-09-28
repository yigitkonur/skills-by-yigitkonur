import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, mkdir, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readYaml, readRecords, writeRecord, containedPath, withController } from '../../skills/run-agentic-tests/scripts/lib/store.mjs';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
import { run, assessCampaign } from '../../skills/run-agentic-tests/scripts/lib/workflow.mjs';

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
  await promisify(execFile)('git', ['init', '-q', project]);
  await promisify(execFile)('git', ['-C', project, 'remote', 'add', 'origin', 'https://github.com/example/project.git']);
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

async function authorCase(c, slug = 'search', expectationOptions = {}, request = {}) {
  const task = await createTask(c, { role: 'scenario-author', slug, requested_action: `Write the approved ${slug} case`, ...request });
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

async function acceptPlan(c, cases, { dependencies = {}, resources = {}, target = 'G001' } = {}) {
  const planner = await createTask(c, { role: 'planner', target_id: target, requested_action: 'Plan these sourced E2E cases' });
  await startTask(c, planner);
  const plan = await readYaml(path.join(c.campaign, planner.draft_paths[0]));
  Object.assign(plan, { target_id: target, scope: { in_scope: ['Search E2E'], out_of_scope: [] }, cases: cases.map(item => ({ case_id: item.record.case_id, spec_revision: item.record.spec_revision, target_id: target, depends_on: dependencies[item.record.case_id] || [], resources: resources[item.record.case_id] || [] })), coverage: [{ source: 'Approved search requirement', case_ids: cases.map(item => item.record.case_id) }] });
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

async function execution(c, { status = 'COMPLETED', observed = { results: ['cats'] }, gap = false, request = {} } = {}) {
  const task = await createTask(c, { role: 'executor', case_ids: ['T0001'], target_id: 'G001', requested_action: 'Run the real search command', ...request });
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
  draft.created_at = '2099-01-01T00:00:00.000Z';
  assert.equal((await submitDraft(c, task, draft, true)).submission_status, 'VALIDATED');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'execution' })).records.length, 0);
  const accepted = await submitDraft(c, task, draft);
  assert.equal(accepted.submission_status, 'ACCEPTED');
  assert.equal(accepted.test_verdict, 'NOT_DECIDED');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'execution' })).records[0].created_at, task.created_at);
  assert.equal((await submitDraft(c, task, draft)).record_id, accepted.record_id);
  await assert.rejects(submitDraft(c, task, { ...draft, observations: [{ ...draft.observations[0], observed: 'Changed claim' }] }), { code: 'RECORD_CONFLICT' });
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records.length, 0);
});

async function verification(c, executionTask, { verdict = 'PASS', slot } = {}) {
  const task = await createTask(c, { role: 'verifier', case_ids: executionTask.case_ids, target_id: executionTask.target_id, round_id: executionTask.round_id, requested_action: 'Inspect saved artifacts against every expectation', ...(slot ? { verification_slot: slot } : {}) });
  await startTask(c, task);
  const draft = await readYaml(path.join(c.campaign, task.draft_paths[0]));
  const record = (await run('records', { campaign: c.campaign, kind: 'execution', 'round-id': executionTask.round_id })).records.find(item => item.case_id === executionTask.case_ids[0]);
  Object.assign(draft, { execution_record_id: record.record_id, reviews: [{ expectation_id: 'E1', verdict, expected: 'JSON contains cats', observed: { results: ['cats'] }, evidence_ids: record.evidence.map(item => item.id), reason: verdict === 'PASS' ? 'Opened JSON and matched the cats result' : 'Opened JSON and found a wrong result' }], inspected_evidence: record.evidence.map(item => ({ id: item.id, sha256: item.sha256, method: 'read JSON', observation: 'The persisted JSON contains results' })) });
  return { task, draft };
}

test('critical PASS requires two independent artifact reviews and changed evidence invalidates current proof', async t => {
  const c = await prepared(t, { priority: 'P0', review_count: 2 });
  const executed = await execution(c);
  await submitDraft(c, executed.task, executed.draft);
  await finishTask(c, executed.task);
  const first = await verification(c, executed.task);
  await assert.rejects(submitDraft(c, first.task, { ...first.draft, inspected_evidence: [] }), { code: 'UNINSPECTED_EVIDENCE' });
  await submitDraft(c, first.task, first.draft);
  await finishTask(c, first.task);
  let reconciled = await run('reconcile', { campaign: c.campaign });
  assert.equal(reconciled.cases[0].outcome, 'PENDING_VERIFICATION');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records.length, 0);
  const second = await verification(c, executed.task, { slot: 'b' });
  assert.ok(second.task.required_inputs.every(input => !input.includes('verification-a') && !input.includes('verdict')));
  await submitDraft(c, second.task, second.draft);
  await finishTask(c, second.task);
  reconciled = await run('reconcile', { campaign: c.campaign });
  assert.equal(reconciled.cases[0].outcome, 'PASS');
  assert.equal(reconciled.complete, false);
  assert.ok(reconciled.obligations.some(item => item.type === 'CLOSURE_AUDIT_REQUIRED'));
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records.length, 1);
  await writeFile(path.join(c.campaign, executed.artifact), '{"results":["wrong"]}');
  const invalidated = await run('status', { campaign: c.campaign });
  assert.equal(invalidated.cases[0].proof_valid, false);
  assert.ok(invalidated.obligations.some(item => item.type === 'EVIDENCE_CHANGED'));
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records[0].outcome, 'PASS');
});

test('a confirmed defect retains its lineage through ticket, isolated fix, new target, independent retest, and closure audit', async t => {
  const c = await prepared(t);
  const failed = await execution(c, { observed: { results: [] } });
  await submitDraft(c, failed.task, failed.draft);
  await finishTask(c, failed.task);
  const review = await verification(c, failed.task, { verdict: 'FAIL' });
  await submitDraft(c, review.task, review.draft);
  await finishTask(c, review.task);
  await run('reconcile', { campaign: c.campaign });
  const finding = (await run('records', { campaign: c.campaign, kind: 'finding' })).records[0];
  assert.equal(finding.class, 'PRODUCT_DEFECT');
  assert.equal(finding.attempts, 1);

  const diagnosis = await createTask(c, { role: 'diagnostician', finding_id: finding.finding_id, requested_action: 'Trace the confirmed wrong search result' });
  await startTask(c, diagnosis);
  const diagnosisDraft = await readYaml(path.join(c.campaign, diagnosis.draft_paths[0]));
  Object.assign(diagnosisDraft, { conclusion: 'confirmed', summary: 'The search filter uses a wrong key', root_cause: 'Query key differs from stored result key', evidence_record_ids: [failed.draft.record_id], artifacts: [] });
  await submitDraft(c, diagnosis, diagnosisDraft);
  await finishTask(c, diagnosis);

  const ticket = await createTask(c, { role: 'ticket-writer', finding_id: finding.finding_id, requested_action: 'Record a deduplicated confirmed issue' });
  await startTask(c, ticket);
  const ticketDraft = await readYaml(path.join(c.campaign, ticket.draft_paths[0]));
  Object.assign(ticketDraft, { issue_url: 'https://github.com/example/project/issues/12', dedup_marker: `agentic-tests:${c.config.campaign_id}:${finding.finding_id}`, body_path: 'findings/issue.md', artifacts: [] });
  await writeFile(path.join(c.campaign, ticketDraft.body_path), 'Confirmed search defect with execution and verifier evidence.');
  await submitDraft(c, ticket, ticketDraft);
  await finishTask(c, ticket);

  const implementer = await createTask(c, { role: 'implementer', finding_id: finding.finding_id, requested_action: 'Fix search in a separate worktree' });
  await startTask(c, implementer);
  const implementation = await readYaml(path.join(c.campaign, implementer.draft_paths[0]));
  const worktree = path.join(c.project, 'repair-worktree');
  await mkdir(worktree);
  const prBody = 'findings/pr.md'; const checks = 'findings/check.log';
  await writeFile(path.join(c.campaign, prBody), 'Fix the query key. Related issue #12. Independent retest pending.');
  await writeFile(path.join(c.campaign, checks), 'Regression check passed');
  Object.assign(implementation, { commit: 'fix-commit', worktree, pr_url: 'https://github.com/example/project/pull/13', pr_body_path: prBody, changed_files: ['app.mjs'], checks: [{ command: 'node --test search.test.mjs', exit_code: 0, artifact_path: checks }], summary: 'Search now uses the correct key', artifacts: [] });
  for (const closing of ['Fixes #12', 'Resolves example/project#12', 'CLOSES: #12', 'Closes https://github.com/example/project/issues/12']) {
    await writeFile(path.join(c.campaign, prBody), closing);
    await assert.rejects(submitDraft(c, implementer, implementation), { code: 'PREMATURE_ISSUE_CLOSURE' });
  }
  await writeFile(path.join(c.campaign, prBody), 'x'.repeat(50001));
  await assert.rejects(submitDraft(c, implementer, implementation), { code: 'PR_BODY_TOO_LONG' });
  await writeFile(path.join(c.campaign, prBody), 'Fix the query key. Related issue #12. Independent retest pending.');
  for (const secretPath of ['.env', 'config/.env.local', 'config\\.env.local']) {
    implementation.changed_files = ['app.mjs', secretPath];
    await assert.rejects(submitDraft(c, implementer, implementation), { code: 'UNSAFE_PATH' });
  }
  implementation.changed_files = ['app.mjs', '.env.example', 'config/.env.example'];
  await submitDraft(c, implementer, implementation);
  await finishTask(c, implementer);
  const integrator = await createTask(c, { role: 'integrator', finding_id: finding.finding_id, requested_action: 'Integrate and assign mandatory retest on G002' });
  await startTask(c, integrator);
  const integration = await readYaml(path.join(c.campaign, integrator.draft_paths[0]));
  Object.assign(integration, { implementation_record_id: implementation.record_id, new_target_id: 'G002', commit: 'revision-G002', affected_case_ids: ['T0001'], retest_obligations: [{ case_id: 'T0001', reason: 'Search query code changed' }], artifacts: [] });
  await submitDraft(c, integrator, integration);
  await finishTask(c, integrator);
  let status = await run('status', { campaign: c.campaign });
  assert.equal(status.latest_target_id, 'G002');
  assert.equal(status.complete, false);
  assert.ok(status.obligations.some(item => item.type === 'RETEST_REQUIRED'));
  assert.ok(status.obligations.some(item => item.type === 'PREPARE_TARGET' && item.target_id === 'G002' && item.commit === 'revision-G002'));
  await environment(c, 'G002');

  const retest = await createTask(c, { role: 'executor', case_ids: ['T0001'], target_id: 'G002', finding_id: finding.finding_id, purpose: 'retest', requested_action: 'Independently rerun search against merged code', prior_context: { previous_failure: 'Search returned an empty result', what_changed: 'Query key fixed in PR 13 and integrated on G002', hypothesis: 'The fixed key returns the cats record', do_not_repeat: ['Do not test the old G001 runtime'], remaining_attempts: 4, issue_url: ticketDraft.issue_url, pr_urls: [implementation.pr_url] } });
  await run('task dispatch', { campaign: c.campaign, 'task-id': retest.task_id });
  await assert.rejects(run('task bind', { campaign: c.campaign, 'task-id': retest.task_id, handle: `host-${implementer.task_id}` }), { code: 'ACTOR_ISOLATION' });
  await run('task bind', { campaign: c.campaign, 'task-id': retest.task_id, handle: `host-${retest.task_id}` });
  const retestDraft = await readYaml(path.join(c.campaign, retest.draft_paths[0]));
  const retestArtifact = `${path.posix.dirname(retest.outputs[0].path)}/evidences/retest.json`;
  await writeFile(path.join(c.campaign, retestArtifact), '{"results":["cats"]}');
  Object.assign(retestDraft, { execution_status: 'COMPLETED', observations: [{ expectation_id: 'E1', observed: { results: ['cats'] }, evidence_ids: ['EV1'], gaps: [] }], evidence: [{ id: 'EV1', path: retestArtifact, type: 'json', expectation_ids: ['E1'] }] });
  await submitDraft(c, retest, retestDraft);
  await finishTask(c, retest);
  const retestReview = await verification(c, retest);
  await submitDraft(c, retestReview.task, retestReview.draft);
  await finishTask(c, retestReview.task);
  status = await run('reconcile', { campaign: c.campaign });
  assert.equal(status.cases[0].outcome, 'PASS');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'finding' })).records[0].state, 'RESOLVED');
  const auditor = await createTask(c, { role: 'plan-auditor', phase: 'closure', requested_action: 'Audit final target proof and all repair/scope obligations' });
  await startTask(c, auditor);
  const audit = await readYaml(path.join(c.campaign, auditor.draft_paths[0]));
  Object.assign(audit, { outcome: 'approved', findings: [], artifacts: [] });
  await submitDraft(c, auditor, audit);
  await finishTask(c, auditor);
  const final = await run('reconcile', { campaign: c.campaign });
  assert.equal(final.complete, true);
  assert.equal(final.outcome, 'PASS');
  assert.deepEqual(final.obligations, []);
  await assert.rejects(run('plan accept', { campaign: c.campaign, file: path.join(c.campaign, c.accepted.planner.outputs[0].path), audit: path.join(c.campaign, c.accepted.auditor.outputs[0].path) }), { code: 'TARGET_DRIFT' });
  assert.equal((await run('status', { campaign: c.campaign })).latest_target_id, 'G002');
});

test('DAG prerequisites block only dependent cases while resource claims and interrupted reservations enforce capacity', async t => {
  const c = await campaign(t, { 'host-capacity': '2' });
  const registration = await authorCase(c, 'registration');
  const login = await authorCase(c, 'login');
  const search = await authorCase(c, 'search');
  await environment(c);
  await acceptPlan(c, [registration, login, search], { dependencies: { T0002: ['T0001'] }, resources: { T0001: [{ name: 'auth-account', mode: 'write' }], T0003: [{ name: 'search-index', mode: 'read' }] } });
  const first = await createTask(c, { role: 'executor', case_ids: ['T0001'], requested_action: 'Register an account' });
  const dependent = await createTask(c, { role: 'executor', case_ids: ['T0002'], requested_action: 'Login to the registered account' });
  const independent = await createTask(c, { role: 'executor', case_ids: ['T0003'], requested_action: 'Search public content' });
  await assert.rejects(run('task dispatch', { campaign: c.campaign, 'task-id': dependent.task_id }), error => error.code === 'TASK_BLOCKED' && error.details.includes('CASE_PREREQUISITE:T0001'));
  await startTask(c, first);
  const shared = await createTask(c, { role: 'feature-scout', requested_action: 'Read account metadata', resources: [{ name: 'auth-account', mode: 'read' }] });
  await assert.rejects(run('task dispatch', { campaign: c.campaign, 'task-id': shared.task_id }), error => error.code === 'TASK_BLOCKED' && error.details.some(item => item.startsWith('RESOURCE:auth-account')));
  await startTask(c, independent);
  await run('task interrupt', { campaign: c.campaign, 'task-id': first.task_id, reason: 'Host interrupted; worker termination not yet confirmed' });
  assert.equal((await run('status', { campaign: c.campaign })).counts.active, 2);
  await assert.rejects(run('task dispatch', { campaign: c.campaign, 'task-id': shared.task_id }), error => error.code === 'TASK_BLOCKED' && error.details.includes('CAPACITY'));
  await run('task interrupt', { campaign: c.campaign, 'task-id': first.task_id, reason: 'Host confirms worker stopped', finished: true });
  await run('task dispatch', { campaign: c.campaign, 'task-id': shared.task_id });
  assert.equal((await run('status', { campaign: c.campaign })).complete, false);
});

test('saved artifacts can be reviewed after runtime shutdown and a withdrawn verifier is replaceable without rerunning execution', async t => {
  const c = await campaign(t);
  const authored = await authorCase(c);
  const target = await environment(c);
  await acceptPlan(c, [authored], { resources: { T0001: [{ name: 'shared-account', mode: 'write' }] } });
  const executed = await execution(c);
  await submitDraft(c, executed.task, executed.draft);
  await finishTask(c, executed.task);
  await writeRecord(c.campaign, 'environments/G001/00-environment.record.yaml', { ...target, status: 'STOPPED' }, { immutable: false });
  const other = await createTask(c, { role: 'feature-scout', requested_action: 'Inspect a different live session', resources: [{ name: 'shared-account', mode: 'write' }] });
  await startTask(c, other);
  const leaked = await verification(c, executed.task, { verdict: 'FAIL' });
  assert.deepEqual(leaked.task.resources, []);
  await submitDraft(c, leaked.task, leaked.draft);
  await run('task interrupt', { campaign: c.campaign, 'task-id': leaked.task.task_id, reason: 'Review context received peer conclusions; withdraw it', finished: true });
  const replacement = await verification(c, executed.task);
  assert.notEqual(replacement.draft.record_id, leaked.draft.record_id);
  await assert.rejects(submitDraft(c, leaked.task, leaked.draft), { code: 'TASK_NOT_RUNNING' });
  await submitDraft(c, replacement.task, replacement.draft);
  await finishTask(c, replacement.task);
  await run('reconcile', { campaign: c.campaign });
  const verdicts = (await run('records', { campaign: c.campaign, kind: 'verdict' })).records;
  assert.equal(verdicts[0].outcome, 'PASS');
  assert.deepEqual(verdicts[0].verification_record_ids, [replacement.draft.record_id]);
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verification' })).records.length, 2);
  assert.equal((await run('records', { campaign: c.campaign, kind: 'execution' })).records.length, 1);
  await run('task interrupt', { campaign: c.campaign, 'task-id': replacement.task.task_id, reason: 'Later host audit found peer leakage; withdraw sealed review', finished: true });
  const reviewRecovery = await run('status', { campaign: c.campaign });
  assert.ok(reviewRecovery.obligations.some(item => item.type === 'VERIFICATION_REQUIRED'));
  assert.ok(!reviewRecovery.obligations.some(item => item.type === 'FRESH_EXECUTION_REQUIRED'), 'Review withdrawal alone must not request an application rerun.');
  const finalReviewer = await verification(c, executed.task);
  await submitDraft(c, finalReviewer.task, finalReviewer.draft); await finishTask(c, finalReviewer.task);
  await run('reconcile', { campaign: c.campaign });
  const revised = (await run('records', { campaign: c.campaign, kind: 'verdict' })).records;
  assert.equal(revised.length, 2);
  assert.ok(revised.some(item => item.verification_record_ids.includes(finalReviewer.draft.record_id)));
  assert.equal((await run('status', { campaign: c.campaign })).cases[0].outcome, 'PASS');
});

test('one unresolved lineage has five actual execution attempts; unavailable credentials and invalid drafts do not spend them', async t => {
  const c = await prepared(t);
  let finding;
  let queued;
  for (let attempt = 1; attempt <= 5; attempt++) {
    const request = attempt === 1 ? {} : { finding_id: finding.finding_id, prior_context: { previous_failure: 'Search returned no matching result', what_changed: `Corrective hypothesis ${attempt} applied`, hypothesis: `Trace evidence ${attempt} suggests this correction`, do_not_repeat: ['Do not repeat the prior unchanged correction'], remaining_attempts: 6 - attempt } };
    if (attempt === 2) {
      const blocked = await execution(c, { status: 'NOT_RUN', gap: true, request: { ...request, prior_context: { ...request.prior_context, what_changed: 'New test client configured; credentials missing' } } });
      blocked.draft.blocker = { reason_code: 'MISSING_CREDENTIAL', detail: 'The dedicated test account is unavailable' };
      await submitDraft(c, blocked.task, blocked.draft);
      await finishTask(c, blocked.task);
      const report = await verification(c, blocked.task, { verdict: 'NOT_ASSESSED' });
      await submitDraft(c, report.task, report.draft);
      await finishTask(c, report.task);
      await run('reconcile', { campaign: c.campaign });
      assert.equal((await run('records', { campaign: c.campaign, kind: 'finding' })).records[0].attempts, 1);
    }

    const executed = await execution(c, { observed: { results: [] }, request });
    if (attempt === 5) await assert.rejects(createTask(c, { role: 'executor', case_ids: ['T0001'], target_id: 'G001', requested_action: 'Queued alternate corrective attempt', ...request, prior_context: { ...request.prior_context, what_changed: 'Alternate fifth correction prepared' } }), { code: 'CASE_RESERVED' });
    if (attempt === 2) {
      await assert.rejects(submitDraft(c, executed.task, { ...executed.draft, observations: [] }), { code: 'INVALID_RECORD' });
      assert.equal((await run('records', { campaign: c.campaign, kind: 'finding' })).records[0].attempts, 1);
    }
    await submitDraft(c, executed.task, executed.draft);
    await finishTask(c, executed.task);
    const verified = await verification(c, executed.task, { verdict: 'FAIL' });
    await submitDraft(c, verified.task, verified.draft);
    await finishTask(c, verified.task);
    await run('reconcile', { campaign: c.campaign });
    const findings = (await run('records', { campaign: c.campaign, kind: 'finding' })).records;
    assert.equal(findings.length, 1);
    finding = findings[0];
    assert.equal(finding.attempts, attempt);
  }
  await assert.rejects(createTask(c, { role: 'executor', case_ids: ['T0001'], purpose: 'final', requested_action: 'Try one more final sweep' }), { code: 'ATTEMPT_LIMIT' });
  await assert.rejects(createTask(c, { role: 'executor', case_ids: ['T0001'], requested_action: 'Attempt sixth correction', prior_context: { previous_failure: 'Still fails', what_changed: 'Sixth correction', hypothesis: 'New sixth idea', do_not_repeat: ['Previous failures'], remaining_attempts: 0 } }), { code: 'ATTEMPT_LIMIT' });
  const final = await run('status', { campaign: c.campaign });
  assert.equal(final.complete, false);
  assert.ok(final.obligations.some(item => item.type === 'ATTEMPT_LIMIT' && item.finding_id === finding.finding_id));
});

test('side findings preserve the original PASS and require a durable scope decision without becoming confirmed defects', async t => {
  const c = await prepared(t);
  const executed = await execution(c);
  executed.draft.findings = [{ class: 'SIDE_FINDING', summary: 'Unrelated settings link might be broken' }];
  await submitDraft(c, executed.task, executed.draft);
  await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task);
  await submitDraft(c, reviewed.task, reviewed.draft);
  await finishTask(c, reviewed.task);
  let assessed = await run('reconcile', { campaign: c.campaign });
  assert.equal(assessed.cases[0].outcome, 'PASS');
  const finding = (await run('records', { campaign: c.campaign, kind: 'finding' })).records[0];
  assert.equal(finding.class, 'SIDE_FINDING');
  assert.equal(finding.scope, 'pending');
  assert.ok(assessed.obligations.some(item => item.type === 'SCOPE_DECISION_REQUIRED'));
  await run('finding decide', { campaign: c.campaign, 'finding-id': finding.finding_id, scope: 'in_scope', reason: 'Related settings flow merits confirmation', source: 'User approved independent confirmation' });
  assessed = await run('status', { campaign: c.campaign });
  assert.ok(assessed.obligations.some(item => item.type === 'CONFIRMATION_REQUIRED'));
  await assert.rejects(createTask(c, { role: 'implementer', finding_id: finding.finding_id, requested_action: 'Fix speculative side report' }), { code: 'UNCONFIRMED_DEFECT' });
  await run('finding decide', { campaign: c.campaign, 'finding-id': finding.finding_id, scope: 'out_of_scope', reason: 'User explicitly defers this unrelated settings flow', source: 'User decision in scope review' });
  const decisions = (await run('records', { campaign: c.campaign, kind: 'scope_decision' })).records;
  assert.equal(decisions.length, 2);
  assert.equal((await run('status', { campaign: c.campaign })).cases[0].outcome, 'PASS');
});

test('scenario recovery preserves allocated revisions and accepts Todo domains while requiring exact expectation markers', async t => {
  const c = await campaign(t, { locale: 'tr' });
  assert.equal(c.config.locale, 'tr');
  const abandoned = await createTask(c, { role: 'scenario-author', slug: 'todo-list', requested_action: 'Author a Todo app scenario' });
  await run('task interrupt', { campaign: c.campaign, 'task-id': abandoned.task_id, reason: 'Author context interrupted before submitting', finished: true });
  const fresh = await createTask(c, { role: 'scenario-author', case_ids: abandoned.case_ids, requested_action: 'Resume the approved Todo scenario in a new context' });
  assert.equal(fresh.spec_revision, 'S002');
  await startTask(c, fresh);
  const root = path.dirname(path.join(c.campaign, fresh.outputs[0].path));
  await writeFile(path.join(root, '01-test-case.md'), '# Todo list\nGiven a Todo item\nWhen it is completed\nThen [E10] the Todo item is checked.');
  await writeFile(path.join(root, '03-how-to-run.md'), 'Launch the Todo app and complete an existing Todo item.');
  const draft = await readYaml(path.join(c.campaign, fresh.draft_paths[0]));
  draft.expectations = [{ id: 'E1', statement: 'The Todo item is checked', source: { type: 'user_request', reference: 'Approved Todo contract' }, priority: 'P1', review_count: 1, observable: { description: 'Completed Todo item is checked' }, evidence_requirements: [{ id: 'ER1', type: 'screenshot', capture: 'Capture the completed Todo item' }] }];
  await assert.rejects(submitDraft(c, fresh, draft), { code: 'INVALID_SCENARIO' });
  await writeFile(path.join(root, '01-test-case.md'), '# Todo list\nGiven a Todo item\nWhen it is completed\nThen [E1] the Todo item is checked.');
  assert.equal((await submitDraft(c, fresh, draft)).submission_status, 'ACCEPTED');
});

test('doctor setup repairs only its incomplete external lock cache and leaves neighboring files intact', async t => {
  const cacheRoot = await temporary(t);
  const module = new URL('../../skills/run-agentic-tests/scripts/lib/dependencies.mjs', import.meta.url).href;
  await writeFile(path.join(cacheRoot, 'keep.txt'), 'unrelated cache data');
  const script = `import {dependencyLocation,loadDependencies} from ${JSON.stringify(module)}; import {mkdir,writeFile} from 'node:fs/promises'; import path from 'node:path'; const cache=dependencyLocation(); await mkdir(cache,{recursive:true}); await writeFile(path.join(cache,'incomplete.txt'),'interrupted install'); const loaded=await loadDependencies({setup:true}); console.log(loaded.YAML.parse('answer: 42').answer);`;
  const result = await promisify(execFile)(process.execPath, ['--input-type=module', '-e', script], { env: { ...process.env, AGENTIC_TESTS_CACHE: cacheRoot }, timeout: 30000 });
  assert.equal(result.stdout.trim(), '42');
  assert.equal(await readFile(path.join(cacheRoot, 'keep.txt'), 'utf8'), 'unrelated cache data');
});

test('a blocked ticket result is accepted without inventing GitHub data and a fresh replacement preserves the failed report', async t => {
  const c = await prepared(t);
  const executed = await execution(c, { observed: { results: [] } });
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task, { verdict: 'FAIL' });
  await submitDraft(c, reviewed.task, reviewed.draft); await finishTask(c, reviewed.task);
  await run('reconcile', { campaign: c.campaign });
  const finding = (await run('records', { campaign: c.campaign, kind: 'finding' })).records[0];
  const diagnostician = await createTask(c, { role: 'diagnostician', finding_id: finding.finding_id, requested_action: 'Confirm wrong query parameter' });
  await startTask(c, diagnostician);
  const diagnosis = await readYaml(path.join(c.campaign, diagnostician.draft_paths[0]));
  Object.assign(diagnosis, { conclusion: 'confirmed', root_cause: 'Wrong query key', summary: 'Wrong key removes valid matches', evidence_record_ids: [executed.draft.record_id], artifacts: [] });
  await submitDraft(c, diagnostician, diagnosis); await finishTask(c, diagnostician);
  const blocked = await createTask(c, { role: 'ticket-writer', finding_id: finding.finding_id, requested_action: 'Create the deduplicated issue' });
  await startTask(c, blocked);
  const draft = await readYaml(path.join(c.campaign, blocked.draft_paths[0]));
  Object.assign(draft, { result_status: 'BLOCKED', summary: 'GitHub access is unavailable', blocker: { reason_code: 'GITHUB_UNAVAILABLE', detail: 'Host has no GitHub authentication' }, artifacts: [] });
  assert.equal((await submitDraft(c, blocked, draft)).worker_may_finish, true);
  await finishTask(c, blocked);
  assert.ok((await run('status', { campaign: c.campaign })).obligations.some(item => item.type === 'ROLE_BLOCKED' && item.task_id === blocked.task_id));
  assert.equal((await run('records', { campaign: c.campaign, kind: 'finding' })).records[0].issue_url, undefined);
  const replacement = await createTask(c, { role: 'ticket-writer', finding_id: finding.finding_id, replaces_task_id: blocked.task_id, requested_action: 'Resume issue creation after GitHub access was restored' });
  await startTask(c, replacement);
  const completed = await readYaml(path.join(c.campaign, replacement.draft_paths[0]));
  await writeFile(path.join(c.campaign, 'findings/resumed-issue.md'), 'Confirmed issue with reproduction and accepted evidence.');
  Object.assign(completed, { issue_url: 'https://github.com/example/project/issues/14', dedup_marker: `agentic-tests:${c.config.campaign_id}:${finding.finding_id}`, body_path: 'findings/resumed-issue.md', artifacts: [] });
  await submitDraft(c, replacement, completed); await finishTask(c, replacement);
  assert.equal((await run('records', { campaign: c.campaign, kind: 'ticket' })).records.length, 2);
  assert.ok(!(await run('status', { campaign: c.campaign })).obligations.some(item => item.type === 'ROLE_BLOCKED'));
});

test('missing actor provenance is an explicit proof gap and supplied report records cannot cross campaigns', async t => {
  const c = await prepared(t);
  const executed = await execution(c);
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task);
  await submitDraft(c, reviewed.task, reviewed.draft); await finishTask(c, reviewed.task);
  await run('reconcile', { campaign: c.campaign });
  const records = await readRecords(c.campaign);
  const foreign = structuredClone(records);
  foreign.find(item => item.record.kind === 'verification').record.campaign_id = 'Foreign';
  await assert.rejects(assessCampaign(c.campaign, foreign), { code: 'WRONG_CAMPAIGN' });
  await rm(path.join(c.campaign, `tasks/${reviewed.task.task_id}/00-task.record.yaml`));
  const incomplete = await run('status', { campaign: c.campaign });
  assert.equal(incomplete.cases[0].proof_valid, false);
  assert.ok(incomplete.obligations.some(item => item.type === 'MISSING_PROVENANCE'));
});

test('a fresh plan auditor can review an already audited immutable plan without overwriting the previous report', async t => {
  const c = await prepared(t);
  const auditor = await createTask(c, { role: 'plan-auditor', plan_id: c.accepted.planner.plan_id, requested_action: 'Recheck the previous audit in a fresh context' });
  assert.notEqual(auditor.outputs[0].path, c.accepted.auditor.outputs[0].path);
  await startTask(c, auditor);
  const draft = await readYaml(path.join(c.campaign, auditor.draft_paths[0]));
  Object.assign(draft, { outcome: 'approved', findings: [], artifacts: [] });
  await submitDraft(c, auditor, draft); await finishTask(c, auditor);
  assert.equal((await run('records', { campaign: c.campaign, kind: 'plan_audit' })).records.length, 2);
});

test('environment handoffs use runtime publication and give an honest termination path for unavailable work', async t => {
  const c = await campaign(t);
  const task = await createTask(c, { role: 'environment-operator', requested_action: 'Start the owned CLI target and prove readiness' });
  const handoff = await readFile(path.join(c.campaign, `tasks/${task.task_id}/10-handoff.md`), 'utf8');
  assert.match(handoff, /runtime start/);
  assert.match(handoff, /confirmed worker termination/);
  assert.match(handoff, /retain.*draft.*artifacts/i);
  assert.doesNotMatch(handoff, /Stop only after receipt\.worker_may_finish/);
  assert.doesNotMatch(handoff, /result_status: BLOCKED/);
});

test('blind verifier disagreement is inconclusive and honest evidence gaps cannot receive PASS', async t => {
  const c = await prepared(t, { critical: true, review_count: 2 });
  const executed = await execution(c);
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const first = await verification(c, executed.task);
  await submitDraft(c, first.task, first.draft); await finishTask(c, first.task);
  const second = await verification(c, executed.task, { verdict: 'FAIL' });
  await submitDraft(c, second.task, second.draft); await finishTask(c, second.task);
  const status = await run('reconcile', { campaign: c.campaign });
  assert.equal(status.cases[0].outcome, 'INCONCLUSIVE');
  assert.equal((await run('records', { campaign: c.campaign, kind: 'finding' })).records[0].class, 'VERIFIER_DISAGREEMENT');
  const gapCampaign = await prepared(t);
  const gap = await execution(gapCampaign, { status: 'PARTIAL', gap: true });
  await submitDraft(gapCampaign, gap.task, gap.draft); await finishTask(gapCampaign, gap.task);
  const unfounded = await verification(gapCampaign, gap.task);
  await assert.rejects(submitDraft(gapCampaign, unfounded.task, unfounded.draft), { code: 'UNINSPECTED_EVIDENCE' });
});

test('a historical assigned target result remains accepted but cannot prove a newer plan target, and views rebuild from records', async t => {
  const c = await prepared(t);
  const old = await execution(c);
  await environment(c, 'G002');
  await acceptPlan(c, [c.authored], { target: 'G002' });
  assert.equal((await submitDraft(c, old.task, old.draft)).submission_status, 'ACCEPTED');
  await finishTask(c, old.task);
  const reviewed = await verification(c, old.task);
  await submitDraft(c, reviewed.task, reviewed.draft); await finishTask(c, reviewed.task);
  const historical = await run('reconcile', { campaign: c.campaign });
  assert.equal((await run('records', { campaign: c.campaign, kind: 'verdict' })).records[0].outcome, 'PASS');
  assert.equal(historical.cases[0].target_id, 'G002');
  assert.equal(historical.cases[0].outcome, 'NOT_RUN');
  assert.equal(historical.complete, false);
  await rm(path.join(c.campaign, '01-notebook.view.yaml'));
  await writeFile(path.join(c.campaign, 'cases/T0001-search/00-current--PASS.view.yaml'), 'outcome: PASS\n');
  await run('reconcile', { campaign: c.campaign });
  assert.equal((await readYaml(path.join(c.campaign, '01-notebook.view.yaml'))).cases[0].outcome, 'NOT_RUN');
  await assert.rejects(readFile(path.join(c.campaign, 'cases/T0001-search/00-current--PASS.view.yaml')), { code: 'ENOENT' });
});

test('a scoped side finding becomes a product defect only after a separate sourced scenario and independent failed review', async t => {
  const c = await prepared(t);
  const original = await execution(c);
  original.draft.findings = [{ class: 'SIDE_FINDING', summary: 'A second search mode may drop matching items' }];
  await submitDraft(c, original.task, original.draft); await finishTask(c, original.task);
  const originalReview = await verification(c, original.task);
  await submitDraft(c, originalReview.task, originalReview.draft); await finishTask(c, originalReview.task);
  await run('reconcile', { campaign: c.campaign });
  const side = (await run('records', { campaign: c.campaign, kind: 'finding' })).records[0];
  await run('finding decide', { campaign: c.campaign, 'finding-id': side.finding_id, scope: 'in_scope', reason: 'Confirm the related alternate search mode', source: 'User-authorized search scope' });
  const confirmation = await authorCase(c, 'alternate-search', {}, { finding_id: side.finding_id });
  assert.equal(confirmation.record.confirms_finding_id, side.finding_id);
  await acceptPlan(c, [c.authored, confirmation]);
  const executed = await execution(c, { observed: { results: [] }, request: { case_ids: confirmation.task.case_ids } });
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task, { verdict: 'FAIL' });
  await submitDraft(c, reviewed.task, reviewed.draft); await finishTask(c, reviewed.task);
  const assessed = await run('reconcile', { campaign: c.campaign });
  const confirmed = (await run('records', { campaign: c.campaign, kind: 'finding' })).records[0];
  assert.equal(confirmed.finding_id, side.finding_id);
  assert.equal(confirmed.class, 'PRODUCT_DEFECT');
  assert.deepEqual(confirmed.case_ids, ['T0001', 'T0002']);
  assert.equal(confirmed.attempts, 1);
  assert.equal(assessed.cases.find(item => item.case_id === 'T0001').outcome, 'PASS');
});

test('replacement chains retain blocked ancestors until a complete finished descendant resolves the assignment', async t => {
  const c = await campaign(t);
  let previous;
  for (let index = 1; index <= 4; index++) {
    const task = await createTask(c, { role: 'feature-scout', requested_action: `Discover approved surfaces, context ${index}`, ...(previous ? { replaces_task_id: previous.task_id } : {}) });
    await startTask(c, task);
    const draft = await readYaml(path.join(c.campaign, task.draft_paths[0]));
    if (index <= 2) Object.assign(draft, { result_status: 'BLOCKED', blocker: { reason_code: 'TOOL_UNAVAILABLE', detail: 'Discovery tool unavailable in this context' }, summary: 'Unable to inspect the requested surface', artifacts: [] });
    else Object.assign(draft, { features: [{ id: 'search', title: 'Search surface', source: { type: 'user_request', reference: 'User approved search discovery' }, subfeatures: [] }], unknowns: [], artifacts: [] });
    await submitDraft(c, task, draft);
    if (index === 3) {
      await run('task interrupt', { campaign: c.campaign, 'task-id': task.task_id, reason: 'Context terminated before a valid finish', finished: true });
      assert.equal((await run('status', { campaign: c.campaign })).obligations.filter(item => item.type === 'ROLE_BLOCKED').length, 2);
    } else await finishTask(c, task);
    previous = task;
  }
  assert.equal((await run('status', { campaign: c.campaign })).obligations.filter(item => item.type === 'ROLE_BLOCKED').length, 0);
});

test('one artifact cannot implicitly satisfy two different captures of the same evidence type', async t => {
  const c = await prepared(t, { evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Capture API response JSON' }, { id: 'ER2', type: 'json', capture: 'Capture the independently persisted row JSON' }] });
  const executed = await execution(c);
  await assert.rejects(submitDraft(c, executed.task, executed.draft), { code: 'AMBIGUOUS_EVIDENCE_REQUIREMENT' });
  executed.draft.evidence[0].requirement_ids = ['MISSING'];
  await assert.rejects(submitDraft(c, executed.task, executed.draft), { code: 'INVALID_EVIDENCE' });
  executed.draft.evidence[0].requirement_ids = ['ER1'];
  await assert.rejects(submitDraft(c, executed.task, executed.draft), { code: 'EVIDENCE_COVERAGE' });
  const secondPath = `${path.posix.dirname(executed.artifact)}/persisted.json`;
  await writeFile(path.join(c.campaign, secondPath), '{"persisted":["cats"]}');
  executed.draft.evidence.push({ id: 'EV2', path: secondPath, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER2'] });
  executed.draft.observations[0].evidence_ids.push('EV2');
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task);
  await submitDraft(c, reviewed.task, reviewed.draft); await finishTask(c, reviewed.task);
  assert.equal((await run('reconcile', { campaign: c.campaign })).cases[0].outcome, 'PASS');
});

test('executor bounded inputs preserve supplied history and both execution roles receive the allocated round context', async t => {
  const c = await prepared(t);
  const executed = await execution(c, { request: { required_inputs: ['02-decisions.md'] } });
  assert.ok(executed.task.required_inputs.includes('02-decisions.md'));
  const context = `${path.posix.dirname(executed.task.outputs[0].path)}/00-context.record.yaml`;
  assert.ok(executed.task.required_inputs.includes(context));
  assert.match(await readFile(path.join(c.campaign, `tasks/${executed.task.task_id}/10-handoff.md`), 'utf8'), /02-decisions\.md/);
  await submitDraft(c, executed.task, executed.draft); await finishTask(c, executed.task);
  const reviewed = await verification(c, executed.task);
  assert.ok(reviewed.task.required_inputs.includes(context));
  assert.ok(!reviewed.task.required_inputs.includes('02-decisions.md'));
});

test('ready queries and dispatch agree when the assigned runtime stops', async t => {
  const c = await prepared(t);
  const task = await createTask(c, { role: 'executor', case_ids: ['T0001'], requested_action: 'Execute search after readiness' });
  const target = (await run('records', { campaign: c.campaign, kind: 'environment' })).records[0];
  await writeRecord(c.campaign, 'environments/G001/00-environment.record.yaml', { ...target, status: 'STOPPED' }, { immutable: false });
  const status = await run('status', { campaign: c.campaign });
  assert.ok(!status.ready.includes(task.task_id));
  assert.ok(status.blocked.some(item => item.task_id === task.task_id && item.reasons.includes('TARGET_NOT_READY')));
  assert.ok(!(await run('records', { campaign: c.campaign, ready: true })).records.some(item => item.task_id === task.task_id));
  await assert.rejects(run('task dispatch', { campaign: c.campaign, 'task-id': task.task_id }), { code: 'TARGET_NOT_READY' });
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
