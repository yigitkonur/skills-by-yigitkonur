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
  await submitDraft(c, implementer, implementation);
  await finishTask(c, implementer);
  await environment(c, 'G002');

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
