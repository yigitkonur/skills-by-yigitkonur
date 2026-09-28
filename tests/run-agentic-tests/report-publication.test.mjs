import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
import { run as workflow } from '../../skills/run-agentic-tests/scripts/lib/workflow.mjs';
import { run as runtime } from '../../skills/run-agentic-tests/scripts/lib/runtime.mjs';
import { run as report } from '../../skills/run-agentic-tests/scripts/lib/report.mjs';

const { YAML } = await loadDependencies({ setup: true });
const sha = value => createHash('sha256').update(value).digest('hex');

// Use the supported command boundaries to freeze records and evidence. These
// fixtures model independent role records; they do not claim independent agents.
async function campaignFixture(t, {
  observed = { message: 'Order confirmed' }, reason = 'The saved response confirms the order.',
  outcome = 'PASS', closure = true, artifactName = 'response.json', artifactId = 'EV1', reviewObserved = observed,
  supplementalCaptures = [],
} = {}) {
  const root = await mkdtemp(path.join(tmpdir(), 'agentic-publication-'));
  const project = path.join(root, 'project');
  await mkdir(project);
  const app = path.join(project, 'app.mjs');
  await writeFile(app, `console.log(${JSON.stringify(JSON.stringify(observed))});\n`);
  const { campaign_path: campaign } = await workflow('init', { project, slug: 'publication', 'host-capacity': '4' });
  t.after(async () => {
    await report('report stop', { campaign }).catch(() => {});
    await runtime('runtime stop', { campaign, 'target-id': 'G001' }).catch(() => {});
    await rm(root, { recursive: true, force: true });
  });
  const command = (name, options = {}) => workflow(name, { campaign, ...options });
  let serial = 0;
  async function task(request) {
    const file = path.join(root, `request-${++serial}.yaml`);
    await writeFile(file, YAML.stringify(request));
    const assigned = (await command('task create', { request: file })).task;
    await command('task dispatch', { 'task-id': assigned.task_id });
    await command('task bind', { 'task-id': assigned.task_id, handle: `publication-fixture-${assigned.task_id}` });
    return assigned;
  }
  async function publish(assigned, body) {
    const file = path.join(campaign, assigned.draft_paths[0]);
    const draft = { ...YAML.parse(await readFile(file, 'utf8')), ...body };
    await writeFile(file, YAML.stringify(draft));
    const receipt = await command('submit', { 'task-id': assigned.task_id, file });
    assert.equal(receipt.submission_status, 'ACCEPTED');
    await command('task close', { 'task-id': assigned.task_id, finished: true });
    return YAML.parse(await readFile(path.join(campaign, assigned.outputs[0].path), 'utf8'));
  }
  const author = await task({ role: 'scenario-author', slug: 'checkout', requested_action: 'Write the approved checkout scenario.' });
  const specRoot = path.dirname(path.join(campaign, author.outputs[0].path));
  await writeFile(path.join(specRoot, '01-test-case.md'), 'Feature: Checkout\nScenario: Successful checkout\nGiven checkout is ready\nWhen the customer orders\nThen [E1] the response confirms the order.\n');
  await writeFile(path.join(specRoot, '03-how-to-run.md'), 'Run app.mjs and preserve its exact JSON output as response evidence.');
  const expectation = { id: 'E1', statement: 'The checkout response confirms the order.',
    source: { type: 'approved_scenario', reference: 'Approved checkout contract' }, priority: 'P2', review_count: 1,
    observable: { description: 'The response message is Order confirmed.' },
    evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Exact checkout response' }] };
  await publish(author, { expectations: [expectation] });
  const operator = await task({ role: 'environment-operator', requested_action: 'Probe the fixture CLI.' });
  const environment = path.join(root, 'environment.yaml');
  await writeFile(environment, YAML.stringify({ target_id: operator.target_id, task_id: operator.task_id, actor_id: operator.actor_id,
    runtime_type: 'cli', source: { revision: `sha256:${sha(await readFile(app))}`, worktree: project,
      provider: { type: 'files', root: project, paths: ['app.mjs'] } },
    command: { argv: [process.execPath, app], cwd: project },
    readiness: { type: 'process', body_contains: 'message', timeout_ms: 3000 } }));
  await runtime('runtime start', { campaign, file: environment });
  await command('task close', { 'task-id': operator.task_id, finished: true });
  const planner = await task({ role: 'planner', target_id: 'G001', requested_action: 'Plan the checkout case.' });
  const plan = await publish(planner, { scope: { in_scope: ['checkout'], out_of_scope: [] },
    cases: [{ case_id: 'T0001', spec_revision: 'S001', target_id: 'G001', depends_on: [], resources: [] }],
    coverage: [{ source: 'Approved checkout contract', case_ids: ['T0001'] }] });
  const auditor = await task({ role: 'plan-auditor', plan_id: plan.record_id, requested_action: 'Audit the plan.' });
  await publish(auditor, { outcome: 'approved', findings: [], artifacts: [] });
  await command('plan accept', { file: path.join(campaign, planner.outputs[0].path), audit: path.join(campaign, auditor.outputs[0].path) });
  const executor = await task({ role: 'executor', case_ids: ['T0001'], requested_action: 'Run checkout and save the response.' });
  const body = execFileSync(process.execPath, [app]);
  const artifactPath = `${path.posix.dirname(executor.outputs[0].path)}/evidences/${artifactName}`;
  await writeFile(path.join(campaign, artifactPath), body);
  const evidence = [{ id: artifactId, path: artifactPath, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER1'], source: 'fixture CLI stdout', tool: 'Node.js' }];
  for (const [index, capture] of supplementalCaptures.entries()) {
    const relative = `${path.posix.dirname(executor.outputs[0].path)}/evidences/${capture.name}`;
    await writeFile(path.join(campaign, relative), capture.body);
    evidence.push({ id: `EV${index + 2}`, path: relative, type: 'log', expectation_ids: ['E1'], source: 'fixture auxiliary capture' });
  }
  const evidenceIds = evidence.map(item => item.id);
  const execution = await publish(executor, { execution_status: 'COMPLETED',
    observations: [{ expectation_id: 'E1', observed: JSON.parse(body), evidence_ids: evidenceIds, gaps: [] }], evidence });
  const verifier = await task({ role: 'verifier', case_ids: ['T0001'], round_id: executor.round_id, requested_action: 'Inspect saved response without rerunning.' });
  await publish(verifier, { execution_record_id: execution.record_id,
    reviews: [{ expectation_id: 'E1', verdict: outcome, expected: expectation.statement, observed: reviewObserved, evidence_ids: evidenceIds, reason }],
    inspected_evidence: execution.evidence.map(item => ({ id: item.id, sha256: item.sha256, method: 'Read exact saved capture', observation: 'The capture was inspected.' })) });
  await command('reconcile');
  if (closure && outcome === 'PASS') {
    const closer = await task({ role: 'plan-auditor', plan_id: plan.record_id, phase: 'closure', requested_action: 'Audit final proof and unresolved work.' });
    await publish(closer, { outcome: 'approved', findings: [], artifacts: [] });
    await command('reconcile');
  }
  return { root, project, campaign, command, task, publish, expectation, app, execution, body, artifactPath };
}

async function build(f) {
  const result = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, result.report_path), 'utf8');
  const model = JSON.parse(html.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  return { result, html, model };
}

async function canonicalBytes(campaign) {
  const names = (await readdir(campaign, { recursive: true })).filter(name => name.endsWith('.record.yaml')).sort();
  return Promise.all(names.map(async name => [name, await readFile(path.join(campaign, name), 'utf8')]));
}

test('harmless credential prose stays public without changing canonical PASS', async t => {
  const reason = 'No token is required. The checkout response confirms the order.';
  const f = await campaignFixture(t, { reason, observed: { message: 'Order confirmed', note: 'No token is required' } });
  const status = await f.command('status');
  assert.equal(status.outcome, 'PASS');
  assert.equal(status.cases[0].proof_valid, true);
  const { result, html, model } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  assert.equal(model.cases[0].outcome, 'PASS');
  assert.deepEqual(result.publication, { status: 'READY', issues: [] });
  assert.deepEqual(model.publication, result.publication);
  assert.equal(model.cases[0].rounds[0].reviews[0].reason, reason);
  assert.match(html, /No token is required/);
  const href = model.cases[0].rounds[0].artifacts[0].href;
  assert.deepEqual(await readFile(path.join(f.campaign, 'report', href)), f.body);
});

test('credential fields are omitted independently of canonical proof and sealed records stay unchanged', async t => {
  const values = ['fixture-structured-12345', 'fixture-header-23456', 'fixture-password-34567',
    'fixture-assignment-45678', 'ghp_fixturetokenabcdefghijklmnopqrstuvwxyz', 'fixture-url-56789', 'fixture-key-67890'];
  const f = await campaignFixture(t, {
    reviewObserved: { message: 'Order confirmed', api_key: values[0], headers: [{ name: 'Authorization', value: `Bearer ${values[1]}` }] },
    reason: `The response confirms the order. password: ${values[2]}\naccess_token = ${values[3]}\n${values[4]}\nhttps://example.test/?token=${values[5]}\n-----BEGIN PRIVATE KEY-----\n${values[6]}\n-----END PRIVATE KEY-----`,
  });
  const before = await canonicalBytes(f.campaign);
  const status = await f.command('status');
  assert.equal(status.outcome, 'PASS');
  const { result, html, model } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  assert.equal(model.cases[0].outcome, 'PASS');
  assert.deepEqual(result.summary.gaps, []);
  assert.equal(result.publication.status, 'PARTIAL');
  assert.ok(result.publication.issues.some(issue => issue.type === 'SENSITIVE_DATA_OMITTED'));
  assert.deepEqual(model.publication, result.publication);
  assert.match(html, /Publication/);
  for (const value of values) assert.equal(html.includes(value), false, 'Fixture credential entered the public report.');
  assert.doesNotMatch(html, /sanitize source|redact before submission|fresh evidence review/i);
  assert.deepEqual(await canonicalBytes(f.campaign), before);
  assert.deepEqual(await readFile(path.join(f.campaign, f.artifactPath)), f.body);
  assert.equal((await f.command('status')).outcome, 'PASS');
});

test('withholding every current artifact blocks publication while verified tests still PASS', async t => {
  const value = 'fixture-evidence-private-12345';
  const f = await campaignFixture(t, { observed: { message: 'Order confirmed', access_token: value } });
  const before = await canonicalBytes(f.campaign);
  const status = await f.command('status');
  assert.equal(status.outcome, 'PASS');
  const { result, html, model } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  assert.equal(model.cases[0].outcome, 'PASS');
  assert.equal(model.cases[0].rounds[0].outcome, 'PASS');
  assert.deepEqual(result.summary.gaps, []);
  assert.equal(result.publication.status, 'BLOCKED');
  assert.ok(result.publication.issues.some(issue => issue.type === 'SENSITIVE_ARTIFACT_WITHHELD' && issue.artifact_id === 'EV1'));
  assert.equal(model.cases[0].rounds[0].artifacts[0].href, undefined);
  assert.equal(html.includes(value), false);
  assert.match(html, /canonical proof/);
  assert.doesNotMatch(html, /sanitize source|redact before submission|fresh evidence review/i);
  assert.deepEqual(await canonicalBytes(f.campaign), before);
  assert.deepEqual(await readFile(path.join(f.campaign, f.artifactPath)), f.body);
  assert.deepEqual(await readdir(path.join(f.campaign, 'report/artifacts')), []);
  const served = await report('report serve', { campaign: f.campaign, port: '0' });
  assert.equal((await fetch(served.url)).status, 200);
  assert.equal((await fetch(`${served.url}artifacts/${sha(f.body)}.json`)).status, 404);
  assert.equal((await fetch(`${served.url}${f.artifactPath}`)).status, 404);
});

test('changed or missing sensitive originals invalidate proof before publication screening', async t => {
  for (const failure of ['changed', 'missing']) await t.test(failure, async t => {
    const f = await campaignFixture(t, { observed: { message: 'Order confirmed', access_token: 'fixture-original-private-12345' } });
    const before = await canonicalBytes(f.campaign);
    if (failure === 'changed') await writeFile(path.join(f.campaign, f.artifactPath), '{"access_token":"fixture-replaced-private-23456"}');
    else await rm(path.join(f.campaign, f.artifactPath));
    const status = await f.command('status');
    assert.equal(status.outcome, 'INCOMPLETE');
    assert.equal(status.cases[0].proof_valid, false);
    const { result, model } = await build(f);
    assert.equal(result.summary.overall, status.outcome);
    assert.equal(result.summary.counts.PASS, 0);
    assert.equal(model.cases[0].outcome, 'INVALID_EVIDENCE');
    assert.equal(model.cases[0].rounds[0].recorded_outcome, 'PASS', 'The original sealed result remains historical, not current proof.');
    assert.equal(result.publication.status, 'BLOCKED');
    assert.ok(result.publication.issues.some(issue => issue.type === 'ORIGINAL_ARTIFACT_INVALID'));
    assert.ok(!result.publication.issues.some(issue => issue.type === 'SENSITIVE_ARTIFACT_WITHHELD'), 'An invalid original must not be described as merely withheld.');
    assert.equal(model.cases[0].rounds[0].artifacts[0].href, undefined);
    assert.deepEqual(await canonicalBytes(f.campaign), before);
  });
});

test('some withheld captures leave safe artifact links available and publication PARTIAL', async t => {
  const secret = 'fixture-log-private-12345';
  const f = await campaignFixture(t, { supplementalCaptures: [
    { name: 'debug.log', body: `Authorization: Bearer ${secret}\n` },
    { name: 'public.log', body: 'Order confirmed. No password is required.\n' },
  ] });
  const { result, model } = await build(f);
  assert.equal(result.summary.overall, 'PASS');
  assert.equal(result.publication.status, 'PARTIAL');
  const artifacts = model.cases[0].rounds[0].artifacts;
  assert.ok(artifacts.find(item => item.id === 'EV1').href);
  assert.equal(artifacts.find(item => item.id === 'EV2').href, undefined);
  assert.ok(artifacts.find(item => item.id === 'EV3').href);
  assert.ok(result.publication.issues.some(issue => issue.type === 'SENSITIVE_ARTIFACT_WITHHELD' && issue.artifact_id === 'EV2'));
  const stale = `artifacts/${'a'.repeat(64)}.txt`;
  await writeFile(path.join(f.campaign, 'report', stale), 'Unlisted older public file');
  const served = await report('report serve', { campaign: f.campaign, port: '0' });
  for (const artifact of artifacts.filter(item => item.href)) {
    const response = await fetch(served.url + artifact.href);
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
    assert.equal((await response.text()).includes(secret), false);
  }
  assert.equal((await fetch(served.url + stale)).status, 404, 'Only this build\'s allowlist can be served.');
});

test('hidden and credential-named valid originals are withheld without changing proof', async t => {
  for (const artifactName of ['.capture.json', 'credentials.json']) await t.test(artifactName, async t => {
    const f = await campaignFixture(t, { artifactName });
    assert.equal((await f.command('status')).outcome, 'PASS');
    const { result, model } = await build(f);
    assert.equal(result.summary.overall, 'PASS');
    assert.equal(model.cases[0].outcome, 'PASS');
    assert.equal(result.publication.status, 'BLOCKED');
    assert.ok(result.publication.issues.some(issue => issue.type === 'SENSITIVE_ARTIFACT_WITHHELD'));
  });
});

test('an output-copy failure blocks publication without invalidating the verified original', async t => {
  const f = await campaignFixture(t);
  await mkdir(path.join(f.campaign, 'report/artifacts', `${sha(f.body)}.json`), { recursive: true });
  const { result, model } = await build(f);
  assert.equal(result.summary.overall, 'PASS');
  assert.equal(model.cases[0].outcome, 'PASS');
  assert.deepEqual(result.summary.gaps, []);
  assert.equal(result.publication.status, 'BLOCKED');
  assert.ok(result.publication.issues.some(issue => issue.type === 'ARTIFACT_PUBLICATION_FAILED'));
  assert.deepEqual(await readFile(path.join(f.campaign, f.artifactPath)), f.body);
});

test('publishable passing case cards cannot replace the canonical closure result', async t => {
  const f = await campaignFixture(t, { closure: false });
  const status = await f.command('status');
  assert.equal(status.outcome, 'INCOMPLETE');
  assert.equal(status.cases[0].outcome, 'PASS');
  const { result, model } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  assert.equal(result.summary.counts.PASS, 1);
  assert.equal(model.cases[0].outcome, 'PASS');
  assert.equal(result.publication.status, 'READY');
  assert.ok(result.summary.gaps.some(gap => /CLOSURE_AUDIT_REQUIRED/.test(gap)));
});

test('a verified failure remains FAIL when the evidence publication is blocked', async t => {
  const f = await campaignFixture(t, { outcome: 'FAIL', observed: { message: 'Order rejected', password: 'fixture-failed-response-12345' }, reason: 'The saved response rejected the order.' });
  const status = await f.command('status');
  assert.equal(status.outcome, 'FAIL');
  const { result, model } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  assert.equal(model.cases[0].outcome, 'FAIL');
  assert.equal(result.publication.status, 'BLOCKED');
  assert.equal(model.cases[0].findings[0].class, 'PRODUCT_DEFECT');
});

test('publication issue metadata is screened before it enters public JSON or HTML', async t => {
  const artifactId = 'ghp_fixtureidentifierabcdefghijklmnopqrstuvwxyz';
  const f = await campaignFixture(t, { artifactId, observed: { message: 'Order confirmed', token: 'fixture-sensitive-response-12345' } });
  const { result, html, model } = await build(f);
  assert.equal(result.summary.overall, 'PASS');
  assert.equal(result.publication.status, 'BLOCKED');
  assert.equal(html.includes(artifactId), false);
  assert.equal(JSON.stringify(result.publication).includes(artifactId), false);
  assert.deepEqual(model.publication, result.publication);
});

test('case reports share the canonical effective root after explicit association and immutable linking', async t => {
  const f = await campaignFixture(t, { outcome: 'FAIL', observed: { message: 'Order rejected' }, reason: 'The response rejected the approved order.' });
  const caseIds = ['T0001'];
  async function addFailure(lineageId) {
    const author = await f.task({ role: 'scenario-author', slug: `checkout-${caseIds.length + 1}`, requested_action: 'Write another approved checkout variant.' });
    const caseId = author.case_ids[0];
    caseIds.push(caseId);
    const directory = path.dirname(path.join(f.campaign, author.outputs[0].path));
    await writeFile(path.join(directory, '01-test-case.md'), 'Given checkout is ready\nWhen ordering\nThen [E1] the response confirms the order.\n');
    await writeFile(path.join(directory, '03-how-to-run.md'), 'Run app.mjs and save its exact JSON output.');
    await f.publish(author, { expectations: [f.expectation] });
    const planner = await f.task({ role: 'planner', target_id: 'G001', requested_action: 'Include the newly approved checkout variant.' });
    const plan = await f.publish(planner, { scope: { in_scope: ['checkout'], out_of_scope: [] },
      cases: caseIds.map(case_id => ({ case_id, spec_revision: 'S001', target_id: 'G001', depends_on: [], resources: [] })),
      coverage: [{ source: 'Approved checkout contract', case_ids: caseIds }] });
    const auditor = await f.task({ role: 'plan-auditor', plan_id: plan.record_id, requested_action: 'Audit the expanded variant coverage.' });
    await f.publish(auditor, { outcome: 'approved', findings: [], artifacts: [] });
    await f.command('plan accept', { file: path.join(f.campaign, planner.outputs[0].path), audit: path.join(f.campaign, auditor.outputs[0].path) });
    const executor = await f.task({ role: 'executor', case_ids: [caseId], requested_action: 'Capture the actual checkout failure.' });
    const body = execFileSync(process.execPath, [f.app]);
    const artifact = `${path.posix.dirname(executor.outputs[0].path)}/evidences/response.json`;
    await writeFile(path.join(f.campaign, artifact), body);
    const execution = await f.publish(executor, { execution_status: 'COMPLETED',
      observations: [{ expectation_id: 'E1', observed: JSON.parse(body), evidence_ids: ['EV1'], gaps: [] }],
      evidence: [{ id: 'EV1', path: artifact, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER1'] }] });
    const verifier = await f.task({ role: 'verifier', case_ids: [caseId], round_id: executor.round_id, requested_action: 'Independently compare the saved response with the approved order.' });
    await f.publish(verifier, { execution_record_id: execution.record_id,
      reviews: [{ expectation_id: 'E1', verdict: 'FAIL', expected: f.expectation.statement, observed: JSON.parse(body), evidence_ids: ['EV1'], reason: 'The response rejected the approved order.' }],
      inspected_evidence: [{ id: 'EV1', sha256: execution.evidence[0].sha256, method: 'Read saved JSON', observation: 'Order rejected.' }],
      ...(lineageId ? { findings: [{ class: 'PRODUCT_DEFECT', summary: 'The same checkout handler rejects every variant.', lineage_id: lineageId, expectation_ids: ['E1'] }] } : {}) });
    await f.command('reconcile');
    return execution;
  }
  await addFailure('F0001');
  const separate = await addFailure();
  const linkRequest = path.join(f.root, 'link.json');
  await writeFile(linkRequest, JSON.stringify({ from_finding_id: 'F0002', into_finding_id: 'F0001',
    evidence_record_ids: [f.execution.record_id, separate.record_id], reason: 'Both independently reviewed failures identify the same checkout handler.' }));
  await f.command('finding link', { file: linkRequest });
  const before = await canonicalBytes(f.campaign);
  const status = await f.command('status');
  assert.equal(status.findings.length, 1);
  assert.deepEqual(status.findings[0].related_finding_ids, ['F0001', 'F0002']);
  assert.equal(status.findings[0].attempts, 1);
  assert.deepEqual(status.findings[0].case_ids, caseIds);
  const { result, model, html } = await build(f);
  assert.equal(result.summary.overall, status.outcome);
  for (const item of model.cases) assert.deepEqual(item.findings, status.findings, `${item.case_id} must use the controller's effective lineage.`);
  assert.match(html, /Related finding IDs: F0001, F0002/);
  assert.deepEqual(await canonicalBytes(f.campaign), before);
});
