import { mkdir, readFile, writeFile, readdir, rm, rename, stat, realpath } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { CliError, validateRecord, validateShape } from './contracts.mjs';
import { loadDependencies, getDependencies, dependencyLocation } from './dependencies.mjs';
import { readYaml, readCampaign, readRecords, writeRecord, withController, containedPath, stableStringify } from './store.mjs';
import { renderHandoff } from './handoffs.mjs';
import { resolveInput, inputLabel } from './inputs.mjs';

const execute = promisify(execFile);
const now = () => new Date().toISOString();
const sha = value => createHash('sha256').update(value).digest('hex');
const digest = value => sha(stableStringify(value));
const fail = (code, message, details = [], exitCode = 3) => { throw new CliError(code, message, exitCode, details); };
const trueFlag = value => value === true || value === 'true';
const required = (options, name) => { if (!options[name]) fail('USAGE', `--${name} is required.`, [], 2); return options[name]; };
const common = (campaign, kind, id) => ({ schema_version: 1, kind, record_id: id, campaign_id: campaign.campaign_id, created_at: now() });
const next = (values, prefix, width) => `${prefix}${String(Math.max(0, ...values.map(value => Number(String(value).match(new RegExp(`^${prefix}(\\d+)`))?.[1]) || 0)) + 1).padStart(width, '0')}`;
const taskPath = id => `tasks/${id}/00-task.record.yaml`;
const active = task => ['DISPATCHED', 'RUNNING', 'INTERRUPTED'].includes(task.state) && !task.worker_finished;
const byKind = (records, kind) => records.filter(item => item.record.kind === kind);
const isCompleteResult = record => !['PARTIAL', 'BLOCKED'].includes(record.result_status);
const completedRecords = (records, kind) => byKind(records, kind).filter(item => isCompleteResult(item.record));

async function snapshot(campaign) {
  const records = await readRecords(campaign);
  const config = records.find(item => item.record.kind === 'campaign')?.record;
  if (!config) fail('INVALID_CAMPAIGN', 'Campaign record is missing.');
  for (const { record } of records) if (record.campaign_id !== config.campaign_id) fail('WRONG_CAMPAIGN', `${record.record_id} belongs to another campaign.`);
  const state = { campaign, config, records, tasks: byKind(records, 'task').map(item => item.record) };
  await refreshFindings(state);
  return state;
}

async function writeText(campaign, relative, contents, { overwrite = false } = {}) {
  const file = containedPath(campaign, relative);
  await mkdir(path.dirname(file), { recursive: true });
  containedPath(campaign, relative);
  if (!overwrite) { await writeFile(file, contents, { flag: 'wx', mode: 0o600 }); return; }
  const temporary = `${file}.${randomUUID()}.tmp`;
  await writeFile(temporary, contents, { flag: 'wx', mode: 0o600 });
  try { await rename(temporary, file); } finally { await rm(temporary, { force: true }); }
}

async function doctor(options) {
  let dependencies = false;
  try { await loadDependencies({ setup: trueFlag(options.setup) }); dependencies = true; } catch (error) { if (trueFlag(options.setup)) throw error; }
  let yq = null;
  try { const result = await execute('yq', ['--version'], { timeout: 3000 }); if (/mikefarah|mike farah/i.test(result.stdout)) yq = result.stdout.trim(); } catch {}
  const nodeReady = Number(process.versions.node.split('.')[0]) >= 22;
  return { ready: nodeReady && dependencies, node: process.versions.node, dependencies, dependency_cache: dependencyLocation(), optional_yq: yq, next_actions: nodeReady && dependencies ? [] : ['Install Node >=22 and run doctor --setup.'] };
}

async function init(options) {
  await loadDependencies();
  const project = await realpath(required(options, 'project'));
  const slug = required(options, 'slug');
  const id = `C-${new Date().toISOString().replace(/[-:.]/g, '')}-${randomUUID().slice(0, 8)}`;
  const config = { schema_version: 1, kind: 'campaign', record_id: id, campaign_id: id, created_at: now(), project, slug, mode: options.mode || 'interactive', max_active: Number(options['max-active'] ?? 20), host_capacity: Number(options['host-capacity'] ?? 0), max_attempts: Number(options['max-attempts'] ?? 5), active_plan_id: null, final_target_id: null, locale: options.locale || 'en', state: 'OPEN' };
  validateRecord(config);
  const directory = path.join(project, 'agentic-tests', `${slug}--${id.slice(2)}`);
  await mkdir(path.dirname(directory), { recursive: true });
  await mkdir(directory, { recursive: false });
  for (const name of ['discovery', 'plans', 'environments', 'tasks', 'cases', 'findings', 'report']) await mkdir(path.join(directory, name));
  await writeRecord(directory, '00-campaign.record.yaml', config);
  await writeText(directory, '.gitignore', '*.runtime.json\n.controller.lock\n*.tmp\n**/logs/\n**/evidences/\nreport/\n');
  await writeText(directory, '02-decisions.md', '# Campaign decisions\n\nRecord material scope decisions with their source.\n');
  return { campaign_path: directory, campaign: config, next_actions: config.host_capacity ? ['CREATE_SCENARIOS_OR_DISCOVERY'] : ['AGENT_ISOLATION_UNAVAILABLE: initialize with the real isolated worker capacity.'] };
}

function findTask(state, id) {
  const task = state.tasks.find(item => item.task_id === id);
  if (!task) fail('TASK_NOT_FOUND', `No task ${id}.`);
  return task;
}

function replacementAncestors(state, task) {
  const ancestors = new Set();
  let cursor = task.replaces_task_id;
  while (cursor && !ancestors.has(cursor)) { ancestors.add(cursor); cursor = state.tasks.find(item => item.task_id === cursor)?.replaces_task_id; }
  return ancestors;
}

function hasCompletedReplacement(state, taskId, visited = new Set()) {
  if (visited.has(taskId)) return false;
  visited.add(taskId);
  return state.tasks.filter(task => task.replaces_task_id === taskId).some(task => {
    const completed = task.state === 'DONE' && task.worker_finished && task.outputs.every(output => state.records.some(item => item.path === output.path && item.record.record_id === output.record_id && item.record.task_id === task.task_id && isCompleteResult(item.record)));
    return completed || hasCompletedReplacement(state, task.task_id, visited);
  });
}

function specFor(state, caseId, revision) {
  const specs = completedRecords(state.records, 'expectations').filter(item => item.record.case_id === caseId && (!revision || item.record.spec_revision === revision));
  return specs.sort((a, b) => b.record.spec_revision.localeCompare(a.record.spec_revision))[0];
}

const planFor = state => state.records.find(item => item.record.record_id === state.config.active_plan_id && item.record.kind === 'plan')?.record;
const environmentFor = (state, targetId) => byKind(state.records, 'environment').find(item => item.record.target_id === targetId);
const effectiveFindings = state => state.findings || byKind(state.records, 'finding');
const findingFor = (state, findingId) => effectiveFindings(state).find(item => item.record.finding_id === lineageRoot(state, findingId));
const targetDigest = environment => digest({ source: environment.source, command: environment.command, readiness: environment.readiness });

async function specHashes(state, caseId, revision) {
  const spec = specFor(state, caseId, revision);
  if (!spec) fail('SPEC_NOT_FOUND', `Missing accepted ${caseId}/${revision} expectations.`);
  const root = path.posix.dirname(spec.path);
  const hashes = [];
  for (const name of ['01-test-case.md', '02-expectations.record.yaml', '03-how-to-run.md']) {
    const relative = `${root}/${name}`;
    hashes.push({ path: relative, sha256: sha(await readFile(containedPath(state.campaign, relative))) });
  }
  return hashes;
}

async function ensureFrozen(state, hashes) {
  for (const item of hashes) {
    let actual;
    try { actual = sha(await readFile(containedPath(state.campaign, item.path))); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (actual !== item.sha256) fail('SPEC_CHANGED', `Frozen scenario file changed or disappeared: ${item.path}`);
  }
}

async function validatePlan(state, plan) {
  const ids = plan.cases.map(item => item.case_id);
  if (new Set(ids).size !== ids.length) fail('INVALID_DAG', 'A case may occur only once in a plan.');
  const covered = new Set();
  for (const row of plan.coverage) for (const id of row.case_ids) {
    if (!ids.includes(id)) fail('INVALID_COVERAGE', `Coverage references an unknown case: ${id}`);
    covered.add(id);
  }
  if (ids.some(id => !covered.has(id))) fail('INVALID_COVERAGE', 'Every accepted case needs a source coverage link.');
  const visiting = new Set(); const visited = new Set();
  const visit = id => {
    if (visiting.has(id)) fail('INVALID_DAG', `Prerequisite cycle at ${id}.`);
    if (visited.has(id)) return;
    const item = plan.cases.find(item => item.case_id === id);
    if (!item) fail('INVALID_DAG', `Unknown prerequisite ${id}.`);
    visiting.add(id);
    for (const dependency of item.depends_on) visit(dependency);
    visiting.delete(id); visited.add(id);
  };
  for (const id of ids) visit(id);
  for (const item of plan.cases) {
    const target = environmentFor(state, item.target_id);
    if (!target) fail('TARGET_NOT_FOUND', `Plan references unknown runtime ${item.target_id}.`);
    if (new Set(item.resources.map(resource => resource.name)).size !== item.resources.length) fail('INVALID_RESOURCES', 'Each case resource may be claimed once.');
    const current = await specHashes(state, item.case_id, item.spec_revision);
    if (item.spec_hashes && stableStringify(current) !== stableStringify(item.spec_hashes)) fail('SPEC_CHANGED', `Plan scenario ${item.case_id} changed.`);
    item.spec_hashes = current;
  }
  if (!environmentFor(state, plan.target_id)) fail('TARGET_NOT_FOUND', `Unknown final target ${plan.target_id}.`);
  return plan;
}

async function acceptPlanCommand(options, state) {
  const plan = await readYaml(required(options, 'file'));
  const audit = await readYaml(required(options, 'audit'));
  const accepted = record => state.records.some(item => stableStringify(item.record) === stableStringify(record));
  if (plan.kind !== 'plan' || audit.kind !== 'plan_audit' || !accepted(plan) || !accepted(audit) || !isCompleteResult(plan) || !isCompleteResult(audit)) fail('UNACCEPTED_PLAN', 'Submit complete planner and independent auditor outputs before accepting a plan.');
  await validatePlan(state, plan);
  if (audit.phase !== 'plan' || audit.subject_record_id !== plan.record_id || audit.subject_digest !== digest(plan) || audit.outcome !== 'approved' || audit.findings.length) fail('PLAN_NOT_APPROVED', 'Plan requires an independent approval of this exact frozen revision without unresolved findings.');
  if (audit.actor_id === plan.actor_id || findTask(state, audit.task_id).handle === findTask(state, plan.task_id).handle) fail('ACTOR_ISOLATION', 'The plan auditor must use a separate real context.');
  const integrated = completedRecords(state.records, 'integration').map(item => item.record).sort((a, b) => Number(b.new_target_id.slice(1)) - Number(a.new_target_id.slice(1)))[0];
  if (integrated && plan.target_id !== integrated.new_target_id) fail('TARGET_DRIFT', 'A plan cannot roll final proof back from the latest integrated runtime generation.');
  if (state.config.active_plan_id && state.config.active_plan_id !== plan.record_id && byKind(state.records, 'execution').length) {
    const previous = planFor(state);
    const omitted = previous.cases.filter(item => !plan.cases.some(next => next.case_id === item.case_id));
    if (omitted.length) fail('SCOPE_OBLIGATION', 'A new plan cannot silently drop previously accepted cases.');
  }
  const config = { ...state.config, active_plan_id: plan.record_id, final_target_id: plan.target_id, state: 'OPEN' };
  await writeRecord(state.campaign, '00-campaign.record.yaml', config, { immutable: false });
  return { plan_id: plan.record_id, target_id: plan.target_id, cases: plan.cases.length, subject_digest: digest(plan), next_actions: ['DISPATCH_READY_CASES'] };
}

async function createTask(options, state) {
  const request = await readYaml(required(options, 'request'));
  validateShape('task_request', request);
  const id = request.task_id || next(state.tasks.map(task => task.task_id), 'J', 5);
  if (state.tasks.some(task => task.task_id === id)) fail('TASK_CONFLICT', `Task ${id} already exists.`, [], 4);
  const actor = next(state.tasks.map(task => task.actor_id), 'A', 5);
  const task = { ...common(state.config, 'task', id), task_id: id, actor_id: actor, role: request.role, state: 'PLANNED', case_ids: request.case_ids || [], dependencies: request.dependencies || [], resources: request.resources || [], required_inputs: request.required_inputs || [], outputs: [], draft_paths: [], requested_action: request.requested_action, worker_finished: false };
  for (const key of ['spec_revision', 'round_id', 'target_id', 'prior_context', 'finding_id', 'plan_id', 'phase', 'purpose', 'verification_slot', 'group', 'replaces_task_id', 'intervention']) if (request[key] !== undefined) task[key] = request[key];
  if (task.finding_id) task.finding_id = lineageRoot(state, task.finding_id);
  if (task.replaces_task_id) {
    const previous = findTask(state, task.replaces_task_id);
    if (previous.role !== task.role || previous.finding_id !== task.finding_id || !previous.worker_finished) fail('INVALID_REPLACEMENT', 'Replacement requires the same role/finding and a confirmed finished previous context.');
    if (!request.case_ids) task.case_ids = previous.case_ids;
    else if (stableStringify(request.case_ids) !== stableStringify(previous.case_ids)) fail('INVALID_REPLACEMENT', 'A replacement must retain the assigned cases.');
  }
  for (const dep of task.dependencies) findTask(state, dep);
  for (const input of task.required_inputs) await resolveInput(state.campaign, state.config.project, input);
  if (task.case_ids.length > 1 && !task.group) fail('INVALID_GROUP', 'Grouped variants require declared shared setup, reliable reset, and independent results.');
  const addOutput = (kind, recordId, relative, caseId) => {
    task.outputs.push({ kind, record_id: recordId, path: relative, ...(caseId ? { case_id: caseId } : {}) });
    task.draft_paths.push(`tasks/${id}/draft/${String(task.outputs.length).padStart(2, '0')}-${kind}${caseId ? `-${caseId}` : ''}.draft.yaml`);
  };
  if (task.role === 'scenario-author') {
    if (task.case_ids.length > 1) fail('INVALID_GROUP', 'Author each scenario separately.');
    if (!task.case_ids.length) task.case_ids = [next(state.tasks.flatMap(item => item.case_ids), 'T', 4)];
    const previous = specFor(state, task.case_ids[0]);
    task.spec_revision ||= next([...byKind(state.records, 'expectations').filter(item => item.record.case_id === task.case_ids[0]).map(item => item.record.spec_revision), ...state.tasks.filter(item => item.role === 'scenario-author' && item.case_ids.includes(task.case_ids[0])).map(item => item.spec_revision)], 'S', 3);
    if (previous) task.case_slug = previous.path.split('/')[1].replace(/^T\d+-/, '');
    else task.case_slug = request.slug || state.tasks.find(item => item.role === 'scenario-author' && item.case_ids.includes(task.case_ids[0]))?.case_slug || fail('INVALID_REQUEST', 'New scenarios require a slug.');
    const root = `cases/${task.case_ids[0]}-${task.case_slug}/specs/${task.spec_revision}`;
    addOutput('expectations', `EXP-${task.case_ids[0]}-${task.spec_revision}`, `${root}/02-expectations.record.yaml`, task.case_ids[0]);
  } else if (task.role === 'feature-scout') {
    const feature = next(byKind(state.records, 'feature').map(item => item.record.record_id).concat(state.tasks.flatMap(item => item.outputs.map(output => output.record_id))), 'FT', 4);
    addOutput('feature', feature, `discovery/${feature}-${request.slug || 'features'}.record.yaml`);
  } else if (task.role === 'planner') {
    task.plan_id ||= next(state.tasks.map(item => item.plan_id), 'P', 3);
    addOutput('plan', task.plan_id, `plans/${task.plan_id}/10-plan.record.yaml`);
  } else if (task.role === 'plan-auditor') {
    task.plan_id ||= state.config.active_plan_id;
    if (!task.plan_id) fail('INVALID_REQUEST', 'Plan auditors require plan_id.');
    task.phase ||= 'plan';
    const subject = state.records.find(item => item.record.kind === 'plan' && item.record.record_id === task.plan_id);
    if (!subject) fail('PLAN_NOT_FOUND', 'Submit the plan before assigning its audit.');
    task.required_inputs = [...new Set([...task.required_inputs, subject.path])];
    const reviewedBefore = state.tasks.some(item => item.role === 'plan-auditor' && item.plan_id === task.plan_id && item.phase === task.phase);
    addOutput('plan_audit', `AUDIT-${task.plan_id}-${task.phase}-${id}`, `plans/${task.plan_id}/${task.phase === 'plan' ? `20-audit${reviewedBefore ? `-${id}` : ''}` : `30-closure-${id}`}.record.yaml`);
  } else if (task.role === 'environment-operator') {
    task.target_id ||= next([...state.tasks.map(item => item.target_id), ...byKind(state.records, 'environment').map(item => item.record.target_id)], 'G', 3);
    addOutput('environment', `ENV-${task.target_id}`, `environments/${task.target_id}/00-environment.record.yaml`);
  } else if (task.role === 'executor' || task.role === 'verifier') {
    const plan = planFor(state);
    if (!plan || !task.case_ids.length) fail('PLAN_REQUIRED', 'Execution and verification require an accepted plan and assigned cases.');
    const entries = task.case_ids.map(caseId => plan.cases.find(item => item.case_id === caseId) || fail('UNKNOWN_CASE', `Case ${caseId} is outside the accepted plan.`));
    task.spec_revision ||= entries[0].spec_revision;
    if (entries.some(item => item.spec_revision !== task.spec_revision)) fail('INVALID_GROUP', 'Grouped cases need the same spec revision.');
    task.target_id ||= state.config.final_target_id;
    const environment = environmentFor(state, task.target_id);
    if (!environment) fail('TARGET_NOT_FOUND', `Unknown runtime ${task.target_id}.`);
    task.plan_id = plan.record_id;
    task.purpose ||= 'initial';
    if (task.role === 'executor') {
      const related = effectiveFindings(state).map(item => item.record).filter(item => item.scope === 'in_scope' && item.state !== 'RESOLVED' && (item.class === 'SIDE_FINDING' ? item.confirmation_case_ids || [] : item.case_ids).some(id => task.case_ids.includes(id)));
      if (task.finding_id && !findingFor(state, task.finding_id)) fail('FINDING_NOT_FOUND', `Unknown finding ${task.finding_id}.`);
      task.finding_id ||= related[0]?.finding_id;
      const reservation = caseReservationProblems(state, task);
      if (reservation.length) fail(reservation[0].code, 'This case/spec/target already has reserved work or evidence awaiting independent review.', reservation, 4);
      task.intervention = interventionFor(state, task);
      task.attempt_id = attemptIdentity(task.intervention);
      validateIntervention(state, task);
      if (task.finding_id) {
        const finding = findingFor(state, task.finding_id).record;
        task.resources.push({ name: `finding:${task.finding_id}`, mode: 'write' });
        if (finding.attempts >= state.config.max_attempts && !finding.attempt_ids.includes(task.attempt_id)) fail('ATTEMPT_LIMIT', 'The unresolved finding exhausted its execution allowance; new specs, rounds, and final sweeps cannot reset it.');
        if (!task.prior_context && finding.class !== 'SIDE_FINDING') fail('RETRY_CONTEXT_REQUIRED', 'Retry requires the previous failure, change, new hypothesis, do-not-repeat guidance, and remaining attempts.');
        if (task.prior_context && task.prior_context.remaining_attempts !== state.config.max_attempts - finding.attempts) fail('RETRY_CONTEXT_REQUIRED', 'Remaining attempts must match the durable finding history.');
        const previous = state.tasks.filter(item => item.role === 'executor' && lineageRoot(state, item.finding_id) === task.finding_id).at(-1);
        if (task.prior_context && previous?.prior_context?.what_changed === task.prior_context.what_changed && previous?.prior_context?.hypothesis === task.prior_context.hypothesis) fail('BLIND_RETRY', 'Do not repeat an unchanged retry hypothesis and change description.');
        if (task.prior_context && finding.issue_url) task.prior_context.issue_url = finding.issue_url;
        if (task.prior_context && finding.pr_urls?.length) task.prior_context.pr_urls = finding.pr_urls;
      }
    }
    if (task.role === 'executor') task.round_id ||= next(byKind(state.records, 'round_context').filter(item => task.case_ids.includes(item.record.case_id)).map(item => item.record.round_id), 'R', 3);
    if (!task.round_id) fail('INVALID_REQUEST', 'Verifiers require an assigned round_id.');
    if (task.role === 'verifier') task.required_inputs = [];
    for (const entry of entries) {
      await ensureFrozen(state, entry.spec_hashes);
      if (entry.depends_on.some(id => task.case_ids.includes(id))) fail('INVALID_GROUP', 'Grouped variants cannot depend on each other.');
      const spec = specFor(state, entry.case_id, task.spec_revision);
      const caseRoot = spec.path.split('/').slice(0, 2).join('/');
      const root = `${caseRoot}/rounds/${task.round_id}`;
      task.required_inputs.push(...entry.spec_hashes.map(item => item.path), environment.path, `${root}/00-context.record.yaml`);
      if (task.role === 'verifier') task.resources = [];
      for (const claim of task.role === 'executor' ? entry.resources : []) {
        const previous = task.resources.find(item => item.name === claim.name);
        if (!previous) task.resources.push(claim);
        else if (claim.mode === 'write') previous.mode = 'write';
      }
      if (task.role === 'executor') {
        addOutput('execution', `EXEC-${entry.case_id}-${task.round_id}`, `${root}/10-execution.record.yaml`, entry.case_id);
      } else {
        const execution = byKind(state.records, 'execution').find(item => item.record.case_id === entry.case_id && item.record.round_id === task.round_id);
        if (!execution || execution.record.target_id !== task.target_id || execution.record.spec_revision !== task.spec_revision) fail('EXECUTION_NOT_FOUND', 'Verify the exact accepted execution assigned to this target/spec/round.');
        task.verification_slot ||= state.tasks.some(other => other.role === 'verifier' && other.case_ids.includes(entry.case_id) && other.round_id === task.round_id && !['INTERRUPTED', 'CANCELLED'].includes(other.state)) ? 'b' : 'a';
        if (task.verification_slot === 'b' && !spec.record.expectations.some(item => item.review_count === 2)) fail('EXCESS_REVIEW', 'This case declares one review, not two.');
        task.required_inputs.push(execution.path, ...execution.record.evidence.map(item => item.path));
        const stem = task.verification_slot === 'a' ? '20-verification-a' : '21-verification-b';
        const replacement = state.records.some(item => item.path === `${root}/${stem}.record.yaml`);
        addOutput('verification', `VERIFY-${entry.case_id}-${task.round_id}-${task.verification_slot}${replacement ? `-${id}` : ''}`, `${root}/${stem}${replacement ? `-${id}` : ''}.record.yaml`, entry.case_id);
      }
    }
    task.required_inputs = [...new Set(task.required_inputs)];
  } else if (['diagnostician', 'ticket-writer', 'implementer', 'integrator'].includes(task.role)) {
    const finding = findingFor(state, task.finding_id);
    if (!finding) fail('FINDING_NOT_FOUND', 'This role requires an existing finding_id.');
    if (finding.record.scope !== 'in_scope') fail('SCOPE_OBLIGATION', 'Confirm the finding in scope before diagnosis, tickets, or fixes.');
    const root = path.posix.dirname(finding.path);
    task.case_ids = finding.record.case_ids.slice(0, 4);
    task.required_inputs = [...new Set([...task.required_inputs, finding.path, ...finding.record.source_record_ids.map(id => state.records.find(item => item.record.record_id === id)?.path).filter(Boolean)])];
    task.resources.push({ name: `finding:${task.finding_id}`, mode: 'write' });
    const diagnosis = completedRecords(state.records, 'diagnosis').filter(item => lineageRoot(state, item.record.finding_id) === task.finding_id && item.record.conclusion === 'confirmed').at(-1);
    if (task.role === 'diagnostician') {
      const existing = state.tasks.some(item => item.role === 'diagnostician' && lineageRoot(state, item.finding_id) === task.finding_id);
      addOutput('diagnosis', `DIAG-${task.finding_id}-${id}`, `${root}/${existing ? `diagnoses/${id}/` : ''}10-diagnosis.record.yaml`);
    } else {
      if (finding.record.class !== 'PRODUCT_DEFECT' || !finding.record.authorized || !diagnosis) fail('UNCONFIRMED_DEFECT', 'Tickets and code delivery require an in-scope product defect with a confirmed diagnosis.');
      task.required_inputs.push(diagnosis.path);
      if (task.role === 'ticket-writer') {
        if (finding.record.issue_url) fail('TICKET_EXISTS', `Finding already has issue ${finding.record.issue_url}.`, [], 4);
        addOutput('ticket', `TICKET-${task.finding_id}`, `${root}/20-ticket.record.yaml`);
      } else if (task.role === 'implementer') {
        if (finding.record.attempts >= state.config.max_attempts) fail('ATTEMPT_LIMIT', 'Do not begin another fix when no independent retest attempts remain.');
        if (!finding.record.issue_url) fail('TICKET_REQUIRED', 'A confirmed implementation-bound defect needs its deduplicated ticket.');
        const attempt = Math.max(0, ...completedRecords(state.records, 'implementation').filter(item => lineageRoot(state, item.record.finding_id) === task.finding_id).map(item => item.record.attempt)) + 1;
        if (attempt >= state.config.max_attempts) fail('ATTEMPT_LIMIT', 'No corrective implementation allowance remains.');
        addOutput('implementation', `IMPL-${task.finding_id}-A${String(attempt).padStart(3, '0')}`, `${root}/fixes/A${String(attempt).padStart(3, '0')}/10-implementation.record.yaml`);
      } else {
        const implementation = completedRecords(state.records, 'implementation').filter(item => lineageRoot(state, item.record.finding_id) === task.finding_id).at(-1);
        if (!implementation) fail('IMPLEMENTATION_REQUIRED', 'Integration needs an accepted implementation result.');
        task.target_id ||= next([...state.tasks.map(item => item.target_id), ...byKind(state.records, 'environment').map(item => item.record.target_id), ...completedRecords(state.records, 'integration').map(item => item.record.new_target_id)], 'G', 3);
        task.resources.push({ name: 'campaign:integration', mode: 'write' });
        task.required_inputs.push(implementation.path);
        addOutput('integration', `INTEGRATION-${task.finding_id}-A${String(implementation.record.attempt).padStart(3, '0')}`, `${path.posix.dirname(implementation.path)}/20-integration.record.yaml`);
      }
    }
  } else fail('UNSUPPORTED_ROLE', `${task.role} task allocation is not available.`);
  for (const output of task.outputs) {
    const previous = state.records.find(item => item.path === output.path);
    if (previous && !isCompleteResult(previous.record) && replacementAncestors(state, task).has(previous.record.task_id)) {
      output.path = output.path.replace(/\.record\.yaml$/, `-${id}.record.yaml`);
      output.record_id += `-${id}`;
    }
    if (state.tasks.some(existing => existing.outputs.some(other => other.path === output.path) && !(existing.worker_finished && ['INTERRUPTED', 'CANCELLED'].includes(existing.state)))) fail('OUTPUT_CONFLICT', `${output.path} is already assigned.`, [], 4);
  }
  validateRecord(task);
  const drafts = task.outputs.map(output => ({ ...common(state.config, output.kind, output.record_id), task_id: id, actor_id: actor, ...(output.case_id ? { case_id: output.case_id } : {}), ...(task.spec_revision ? { spec_revision: task.spec_revision } : {}), ...(task.target_id ? { [output.kind === 'integration' ? 'new_target_id' : 'target_id']: task.target_id } : {}), ...(task.round_id ? { round_id: task.round_id } : {}) }));
  if (task.role === 'environment-operator') {
    const integration = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === task.target_id)?.record;
    if (integration) drafts[0].source = { revision: integration.commit };
  }
  if (task.role === 'plan-auditor') {
    const subject = state.records.find(item => item.record.record_id === task.plan_id).record;
    Object.assign(drafts[0], { phase: task.phase, subject_record_id: subject.record_id, subject_digest: task.phase === 'closure' ? (await assessState(state)).closure_subject_digest : digest(subject) });
  }
  if (task.finding_id && ['diagnostician', 'ticket-writer', 'implementer', 'integrator'].includes(task.role)) {
    drafts[0].finding_id = task.finding_id;
    if (task.role === 'implementer') drafts[0].attempt = Number(task.outputs[0].record_id.match(/-A(\d+)(?:-J\d+)?$/)[1]);
    if (task.role === 'integrator') drafts[0].implementation_record_id = completedRecords(state.records, 'implementation').filter(item => lineageRoot(state, item.record.finding_id) === task.finding_id).at(-1).record.record_id;
  }
  if (task.role === 'scenario-author') {
    const root = path.posix.dirname(task.outputs[0].path);
    drafts[0].author_actor_id = actor;
    drafts[0].expectations = [];
    if (task.finding_id) {
      const finding = findingFor(state, task.finding_id);
      if (!finding || finding.record.class !== 'SIDE_FINDING' || finding.record.scope !== 'in_scope') fail('SCOPE_OBLIGATION', 'Confirmation scenarios require an explicitly in-scope side finding.');
      drafts[0].confirms_finding_id = task.finding_id;
      task.required_inputs.push(finding.path);
    }
    if (request.scenario_source) {
      const source = request.scenario_source;
      const authored = await readYaml(source.expectations_path);
      if (!Array.isArray(authored.expectations)) fail('INVALID_SCENARIO', 'Existing expectations source needs an expectations array.');
      drafts[0].expectations = authored.expectations;
      await writeText(state.campaign, `${root}/01-test-case.md`, await readFile(source.test_case_path, 'utf8'));
      await writeText(state.campaign, `${root}/03-how-to-run.md`, await readFile(source.how_to_run_path, 'utf8'));
    } else {
      await writeText(state.campaign, `${root}/01-test-case.md`, '# TODO: Write a sourced Given/When/Then scenario with expectation IDs.\n');
      await writeText(state.campaign, `${root}/03-how-to-run.md`, '# TODO: Write real E2E steps and evidence capture instructions.\n');
    }
  }
  await writeRecord(state.campaign, taskPath(id), task);
  if (task.role === 'executor') for (const output of task.outputs) {
    const entry = planFor(state).cases.find(item => item.case_id === output.case_id);
    const root = path.posix.dirname(output.path);
    const context = { ...common(state.config, 'round_context', `ROUND-${output.case_id}-${task.round_id}`), case_id: output.case_id, spec_revision: task.spec_revision, round_id: task.round_id, target_id: task.target_id, execution_task_id: task.task_id, expectations_record_id: specFor(state, output.case_id, task.spec_revision).record.record_id, plan_id: task.plan_id, purpose: task.purpose, attempt_id: task.attempt_id, intervention: task.intervention, finding_ids: task.finding_id ? [task.finding_id] : [], target_source_digest: targetDigest(environmentFor(state, task.target_id).record), spec_hashes: entry.spec_hashes };
    await writeRecord(state.campaign, `${root}/00-context.record.yaml`, context);
    await mkdir(containedPath(state.campaign, `${root}/evidences`), { recursive: true });
  }
  for (let i = 0; i < drafts.length; i++) await writeText(state.campaign, task.draft_paths[i], getDependencies().YAML.stringify(drafts[i]));
  await writeText(state.campaign, `tasks/${id}/10-handoff.md`, renderHandoff(task, { campaign: state.campaign, project: state.config.project }));
  return { task, task_id: id, actor_id: actor, handoff_path: `tasks/${id}/10-handoff.md`, draft_paths: task.draft_paths, outputs: task.outputs };
}

async function eligibility(task, state) {
  const reasons = [];
  for (const id of task.dependencies) if (findTask(state, id).state !== 'DONE') reasons.push(`DEPENDENCY:${id}`);
  for (const input of task.required_inputs) {
    try { if (!existsSync(await resolveInput(state.campaign, state.config.project, input))) reasons.push(`MISSING_INPUT:${inputLabel(input)}`); }
    catch (error) { reasons.push(`${error.code || 'MISSING_INPUT'}:${inputLabel(input)}`); }
  }
  if (task.role === 'executor') {
    reasons.push(...caseReservationProblems(state, task).map(item => `${item.code}:${item.task_id || item.record_id}`));
    const environment = environmentFor(state, task.target_id)?.record;
    if (!environment || environment.status !== 'READY') reasons.push('TARGET_NOT_READY');
    const integration = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === task.target_id)?.record;
    if (integration && environment?.source.revision !== integration.commit) reasons.push('TARGET_DRIFT');
    for (const id of task.case_ids) {
      const context = byKind(state.records, 'round_context').find(item => item.record.case_id === id && item.record.round_id === task.round_id)?.record;
      if (!context) reasons.push('MISSING_PROVENANCE');
      else {
        if (environment && context.target_source_digest !== targetDigest(environment)) reasons.push('TARGET_DRIFT');
        try { await ensureFrozen(state, context.spec_hashes); } catch (error) { if (error.code === 'SPEC_CHANGED') reasons.push('SPEC_CHANGED'); else throw error; }
      }
    }
  }
  if (task.role === 'executor') for (const id of task.case_ids) {
    const entry = planFor(state)?.cases.find(item => item.case_id === id);
    for (const dependency of entry?.depends_on || []) {
      const context = byKind(state.records, 'round_context').map(item => item.record).filter(item => item.case_id === dependency && item.target_id === task.target_id).sort((a, b) => Number(b.round_id.slice(1)) - Number(a.round_id.slice(1)))[0];
      const verdict = context && latestVerdict(state, item => item.case_id === dependency && item.round_id === context.round_id);
      const execution = verdict && byKind(state.records, 'execution').find(item => item.record.record_id === verdict.execution_record_id)?.record;
      if (!execution || verdict.outcome !== 'PASS' || (await sealedProofProblems(state, execution, verdict)).length) reasons.push(`CASE_PREREQUISITE:${dependency}`);
    }
  }
  if (task.role === 'executor' && task.finding_id) {
    const finding = findingFor(state, task.finding_id)?.record;
    if (!finding) reasons.push('FINDING_NOT_FOUND');
    else {
      if (finding.attempt_mapping_problems.length) reasons.push('ATTEMPT_MAPPING_REQUIRED');
      if (finding.attempts >= state.config.max_attempts && !finding.attempt_ids.includes(task.attempt_id)) reasons.push('ATTEMPT_LIMIT');
      if (task.prior_context && task.prior_context.remaining_attempts !== state.config.max_attempts - finding.attempts) reasons.push('RETRY_CONTEXT_STALE');
      for (const { record: execution } of byKind(state.records, 'execution')) {
        const assigned = state.tasks.find(item => item.task_id === execution.task_id);
        if (assigned?.finding_id === task.finding_id && !latestVerdict(state, item => item.execution_record_id === execution.record_id)) reasons.push(`VERIFICATION_REQUIRED:${execution.record_id}`);
      }
    }
  }
  if (!state.config.host_capacity) reasons.push('AGENT_ISOLATION_UNAVAILABLE');
  if (state.tasks.filter(active).length >= Math.min(20, state.config.max_active, state.config.host_capacity)) reasons.push('CAPACITY');
  for (const other of state.tasks.filter(active)) for (const own of task.resources) for (const claimed of other.resources) {
    if (own.name === claimed.name && (own.mode === 'write' || claimed.mode === 'write')) reasons.push(`RESOURCE:${own.name}:${other.task_id}`);
  }
  return [...new Set(reasons)];
}

async function transition(command, options, state) {
  const task = { ...findTask(state, required(options, 'task-id')) };
  if (command === 'task dispatch') {
    if (!['PLANNED', 'READY', 'BLOCKED'].includes(task.state)) fail('INVALID_TRANSITION', `Cannot dispatch ${task.state} task.`, [], 4);
    const reasons = await eligibility(task, state);
    if (reasons.some(reason => reason.startsWith('CASE_RESERVED:') || reason.startsWith('VERIFICATION_REQUIRED:'))) fail(reasons.some(reason => reason.startsWith('CASE_RESERVED:')) ? 'CASE_RESERVED' : 'VERIFICATION_REQUIRED', 'Reserved case work or pending verification must finish before another execution.', reasons, 4);
    for (const code of ['TARGET_NOT_READY', 'TARGET_DRIFT', 'SPEC_CHANGED']) if (reasons.includes(code)) fail(code, `Task ${task.task_id} no longer has its assigned ready target and frozen source.`, reasons);
    if (reasons.length) fail('TASK_BLOCKED', `Task ${task.task_id} is not eligible.`, reasons, 4);
    if (task.role === 'executor') {
      for (const id of task.case_ids) await ensureFrozen(state, planFor(state).cases.find(item => item.case_id === id).spec_hashes);
      const environment = environmentFor(state, task.target_id);
      if (!environment || environment.record.status !== 'READY') fail('TARGET_NOT_READY', 'Assigned runtime is not ready.');
      const integration = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === task.target_id)?.record;
      if (integration && environment.record.source.revision !== integration.commit) fail('TARGET_DRIFT', 'Assigned runtime source differs from its integrated commit.');
    }
    task.state = 'DISPATCHED';
  } else if (command === 'task bind') {
    if (task.state !== 'DISPATCHED') fail('INVALID_TRANSITION', 'Bind only a dispatched task.', [], 4);
    const handle = required(options, 'handle');
    if (state.tasks.some(other => other.handle === handle)) fail('ACTOR_ISOLATION', 'A real host context cannot be reused for another task.', [], 4);
    task.handle = handle;
    task.state = 'RUNNING';
  } else if (command === 'task close') {
    if (!trueFlag(options.finished)) fail('WORKER_NOT_FINISHED', 'Confirm actual host worker termination with --finished true.', [], 4);
    if (task.state !== 'RUNNING' && task.state !== 'DONE') fail('INVALID_TRANSITION', 'Close only a running task with accepted outputs.', [], 4);
    const missing = task.outputs.filter(output => !state.records.some(item => item.path === output.path && item.record.record_id === output.record_id && item.record.actor_id === task.actor_id && item.record.task_id === task.task_id));
    if (missing.length) fail('OUTPUTS_MISSING', 'All assigned outputs must be accepted before closing.', missing.map(output => output.path), 4);
    task.worker_finished = true;
    task.state = 'DONE';
  } else {
    if (!['PLANNED', 'READY', 'BLOCKED', 'DISPATCHED', 'RUNNING', 'INTERRUPTED'].includes(task.state) && !(task.state === 'DONE' && task.role === 'verifier')) fail('INVALID_TRANSITION', 'Cannot interrupt a completed task other than withdrawing a verifier.', [], 4);
    task.interrupt_reason = required(options, 'reason');
    task.worker_finished = trueFlag(options.finished) || !active(task);
    task.state = 'INTERRUPTED';
  }
  await writeRecord(state.campaign, taskPath(task.task_id), task, { immutable: false });
  if (task.role === 'verifier' && task.state === 'INTERRUPTED') await synchronizeDerived(await snapshot(state.campaign));
  return { task, reservation_active: active(task) };
}

function exactCoverage(items, expected, label) {
  const ids = items.map(item => item.expectation_id);
  if (ids.length !== expected.length || new Set(ids).size !== ids.length || ids.some(id => !expected.some(item => item.id === id))) fail('EXPECTATION_COVERAGE', `${label} must cover every expectation exactly once.`);
}

async function hashArtifact(state, relative) {
  const file = containedPath(state.campaign, relative);
  if (relative.split('/').some(name => name === '.env' || name.startsWith('.env.') || name === '.git')) fail('UNSAFE_ARTIFACT', 'Secret/configuration files cannot be evidence artifacts.');
  try {
    const metadata = await stat(file);
    if (!metadata.isFile()) fail('MISSING_ARTIFACT', `Evidence is not a regular file: ${relative}`);
    const contents = await readFile(file);
    return { sha256: sha(contents), size: contents.length };
  } catch (error) {
    if (error.code === 'ENOENT') fail('MISSING_ARTIFACT', `Claimed evidence does not exist: ${relative}`);
    throw error;
  }
}

function coversRequirement(evidence, expected, requirement) {
  return evidence.type === requirement.type && evidence.expectation_ids.includes(expected.id) && (evidence.requirement_ids ? evidence.requirement_ids.includes(requirement.id) : expected.evidence_requirements.filter(item => item.type === evidence.type).length === 1);
}

async function validateExecution(state, task, record, output) {
  const spec = specFor(state, record.case_id, record.spec_revision)?.record;
  if (!spec) fail('SPEC_NOT_FOUND', 'Execution requires accepted expectations.');
  if (spec.author_actor_id === record.actor_id || findTask(state, spec.task_id).handle === task.handle) fail('ACTOR_ISOLATION', 'The author cannot execute their own scenario.');
  const context = byKind(state.records, 'round_context').find(item => item.record.case_id === record.case_id && item.record.round_id === record.round_id)?.record;
  if (!context || context.execution_task_id !== task.task_id) fail('WRONG_ASSIGNMENT', 'Execution has no assigned round context.');
  if (task.finding_id && record.execution_status !== 'NOT_RUN' && !state.records.some(item => item.record.record_id === record.record_id)) {
    const finding = findingFor(state, task.finding_id)?.record;
    if (!finding || (finding.attempts >= state.config.max_attempts && !finding.attempt_ids.includes(task.attempt_id))) fail('ATTEMPT_LIMIT', 'This finding has no remaining actual execution allowance; preserve this draft and artifacts for the controller.');
  }
  await ensureFrozen(state, context.spec_hashes);
  const environment = environmentFor(state, record.target_id)?.record;
  if (!environment || targetDigest(environment) !== context.target_source_digest) fail('TARGET_DRIFT', 'Runtime provenance changed during this execution.');
  exactCoverage(record.observations, spec.expectations, 'Execution observations');
  if (record.execution_status === 'NOT_RUN' && !record.blocker) fail('NOT_RUN_REASON', 'NOT_RUN needs an explicit blocker and reason.');
  if (new Set(record.evidence.map(item => item.id)).size !== record.evidence.length || new Set(record.evidence.map(item => item.path)).size !== record.evidence.length) fail('INVALID_EVIDENCE', 'Evidence IDs and paths must be unique.');
  const evidenceRoot = `${path.posix.dirname(output.path)}/evidences/`;
  for (const evidence of record.evidence) {
    if (!evidence.path.startsWith(evidenceRoot)) fail('UNSAFE_ARTIFACT', 'Save executor evidence only under its assigned round evidences directory.');
    if (new Set(evidence.expectation_ids).size !== evidence.expectation_ids.length || evidence.expectation_ids.some(id => !spec.expectations.some(item => item.id === id))) fail('EXPECTATION_COVERAGE', 'Evidence references an unknown or duplicate expectation.');
    const expectations = spec.expectations.filter(item => evidence.expectation_ids.includes(item.id));
    if (evidence.requirement_ids) {
      if (new Set(evidence.requirement_ids).size !== evidence.requirement_ids.length || evidence.requirement_ids.some(id => !expectations.some(item => item.evidence_requirements.some(requirement => requirement.id === id && requirement.type === evidence.type)))) fail('INVALID_EVIDENCE', 'Evidence requirement IDs must name assigned requirements of the declared evidence type.');
    } else if (expectations.some(item => item.evidence_requirements.filter(requirement => requirement.type === evidence.type).length > 1)) fail('AMBIGUOUS_EVIDENCE_REQUIREMENT', 'Multiple captures use this type; provide explicit requirement_ids rather than implicitly covering them all.');
    const computed = await hashArtifact(state, evidence.path);
    if (evidence.sha256 && evidence.sha256 !== computed.sha256) fail('EVIDENCE_CHANGED', `Evidence hash differs: ${evidence.path}`);
    if (evidence.size !== undefined && evidence.size !== computed.size) fail('EVIDENCE_CHANGED', `Evidence size differs: ${evidence.path}`);
    Object.assign(evidence, computed);
  }
  for (const expected of spec.expectations) {
    const observation = record.observations.find(item => item.expectation_id === expected.id);
    if (new Set(observation.evidence_ids).size !== observation.evidence_ids.length || new Set(observation.gaps.map(item => item.requirement_id)).size !== observation.gaps.length) fail('INVALID_EVIDENCE', 'Evidence and gap references must be unique.');
    const attached = observation.evidence_ids.map(id => record.evidence.find(item => item.id === id && item.expectation_ids.includes(expected.id)) || fail('INVALID_EVIDENCE', `Observation references unassigned evidence ${id}.`));
    if (observation.gaps.some(gap => !expected.evidence_requirements.some(requirement => requirement.id === gap.requirement_id))) fail('INVALID_EVIDENCE', 'Gap references an unknown evidence requirement.');
    for (const requirement of expected.evidence_requirements) {
      if (!observation.gaps.some(gap => gap.requirement_id === requirement.id) && !attached.some(item => coversRequirement(item, expected, requirement))) fail('EVIDENCE_COVERAGE', `Expectation ${expected.id}/${requirement.id} needs captured evidence or an explicit gap.`);
    }
    if (record.execution_status === 'COMPLETED' && observation.gaps.length) fail('INVALID_EXECUTION_STATUS', 'A completed execution cannot omit required evidence; use PARTIAL.');
    if (record.execution_status === 'NOT_RUN' && !observation.gaps.length) fail('INVALID_EXECUTION_STATUS', 'A not-run execution must mark expectation evidence as unavailable.');
  }
  return record;
}

function roundRecords(state, execution) {
  const spec = specFor(state, execution.case_id, execution.spec_revision)?.record;
  const reviews = byKind(state.records, 'verification').map(item => item.record).filter(item => item.execution_record_id === execution.record_id && !['INTERRUPTED', 'CANCELLED'].includes(state.tasks.find(task => task.task_id === item.task_id)?.state)).sort((a, b) => a.record_id.localeCompare(b.record_id));
  const context = byKind(state.records, 'round_context').find(item => item.record.case_id === execution.case_id && item.record.round_id === execution.round_id)?.record;
  return { spec, execution, reviews, context };
}

const roundDigest = round => digest({ expectations: round.spec, execution: round.execution, verifications: round.reviews, context: round.context });
const latestVerdict = (state, predicate) => byKind(state.records, 'verdict').map(item => item.record).filter(predicate).sort((a, b) => b.created_at.localeCompare(a.created_at) || b.record_id.localeCompare(a.record_id))[0];

async function sealedProofProblems(state, execution, verdict) {
  const round = roundRecords(state, execution);
  const problems = await proofProblems(state, round);
  if (!verdict || verdict.inputs_digest !== roundDigest(round)) problems.push({ type: 'RECORDS_CHANGED', message: 'Sealed verdict inputs no longer match current accepted records.' });
  if (!round.spec || round.reviews.length < Math.max(...round.spec.expectations.map(item => item.review_count))) problems.push({ type: 'VERIFICATION_REQUIRED', message: 'Current independent review quorum is incomplete.' });
  if (verdict?.outcome === 'PASS' && (execution.execution_status !== 'COMPLETED' || execution.observations.some(item => item.gaps.length) || round.spec?.expectations.some(expected => round.reviews.some(review => review.reviews.find(item => item.expectation_id === expected.id)?.verdict !== 'PASS')))) problems.push({ type: 'INCOMPLETE_PROOF', message: 'Passing verdict disagrees with current execution or independent reviews.' });
  if (verdict?.outcome === 'PASS' && round.spec?.expectations.some(expected => expected.evidence_requirements.some(requirement => round.reviews.some(review => !review.reviews.find(item => item.expectation_id === expected.id)?.evidence_ids.some(id => execution.evidence.some(evidence => evidence.id === id && coversRequirement(evidence, expected, requirement))))))) problems.push({ type: 'EVIDENCE_COVERAGE', message: 'Current passing reviews do not explicitly cover every required capture.' });
  return problems;
}

async function proofProblems(state, round) {
  const problems = [];
  try { await ensureFrozen(state, round.context?.spec_hashes || []); } catch (error) { problems.push({ type: error.code || 'SPEC_CHANGED', message: error.message }); }
  if (!round.context || !round.spec) problems.push({ type: 'MISSING_PROVENANCE', message: 'Round context or expectations are missing.' });
  const proofWorkers = [[round.spec, 'scenario-author'], [round.execution, 'executor'], ...round.reviews.map(record => [record, 'verifier'])];
  const handles = [];
  for (const [record, role] of proofWorkers) {
    const task = state.tasks.find(item => item.task_id === record?.task_id);
    if (!task || !task.handle || task.role !== role || task.actor_id !== record?.actor_id || !task.outputs.some(output => output.record_id === record?.record_id && output.kind === record?.kind)) problems.push({ type: 'MISSING_PROVENANCE', message: `No matching bound ${role} assignment for ${record?.record_id || 'missing record'}.` });
    else handles.push(task.handle);
  }
  if (new Set(handles).size !== handles.length) problems.push({ type: 'ACTOR_ISOLATION', message: 'Author, executor, and reviewers must have distinct real context handles.' });
  const target = environmentFor(state, round.execution.target_id)?.record;
  if (!target || targetDigest(target) !== round.context?.target_source_digest) problems.push({ type: 'TARGET_DRIFT', message: 'Runtime provenance differs from the assigned generation.' });
  const integration = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === round.execution.target_id)?.record;
  if (integration && target?.source.revision !== integration.commit) problems.push({ type: 'TARGET_DRIFT', message: 'Runtime source does not identify the integrated commit.' });
  for (const evidence of round.execution.evidence) {
    try {
      const current = await hashArtifact(state, evidence.path);
      if (current.sha256 !== evidence.sha256 || current.size !== evidence.size) problems.push({ type: 'EVIDENCE_CHANGED', message: `Accepted artifact changed: ${evidence.path}`, path: evidence.path });
    } catch (error) { problems.push({ type: error.code || 'MISSING_ARTIFACT', message: error.message, path: evidence.path }); }
  }
  return problems;
}

async function validateVerification(state, task, record) {
  const execution = byKind(state.records, 'execution').map(item => item.record).find(item => item.record_id === record.execution_record_id);
  if (!execution || ['case_id', 'spec_revision', 'round_id', 'target_id'].some(key => execution[key] !== record[key])) fail('WRONG_EXECUTION', 'Review must reference the assigned execution, target, spec, and round.');
  const round = roundRecords(state, execution);
  const excludedActors = [execution.actor_id, round.spec.author_actor_id];
  const excludedHandles = [findTask(state, execution.task_id).handle, findTask(state, round.spec.task_id).handle];
  if (excludedActors.includes(record.actor_id) || excludedHandles.includes(task.handle)) fail('ACTOR_ISOLATION', 'Verifier must be independent of the author and executor.');
  exactCoverage(record.reviews, round.spec.expectations, 'Verification reviews');
  if (new Set(record.inspected_evidence.map(item => item.id)).size !== record.inspected_evidence.length) fail('INVALID_EVIDENCE', 'Inspect each evidence item once.');
  const problems = await proofProblems(state, round);
  for (const inspected of record.inspected_evidence) {
    const evidence = execution.evidence.find(item => item.id === inspected.id);
    if (!evidence || evidence.sha256 !== inspected.sha256) fail('UNINSPECTED_EVIDENCE', 'Inspection must cite the accepted artifact ID and exact hash.');
  }
  for (const review of record.reviews) {
    const expected = round.spec.expectations.find(item => item.id === review.expectation_id);
    if (review.expected !== expected.statement) fail('EXPECTATION_CHANGED', 'Copy the frozen expectation statement without redefining it.');
    if (new Set(review.evidence_ids).size !== review.evidence_ids.length) fail('INVALID_EVIDENCE', 'Review evidence IDs must be unique.');
    const attached = review.evidence_ids.map(id => execution.evidence.find(item => item.id === id && item.expectation_ids.includes(expected.id)) || fail('INVALID_EVIDENCE', `Review cites unknown evidence ${id}.`));
    if (attached.some(evidence => !record.inspected_evidence.some(item => item.id === evidence.id && item.sha256 === evidence.sha256))) fail('UNINSPECTED_EVIDENCE', 'Every cited artifact needs an explicit inspection with its hash, method, and observation.');
    if (['PASS', 'FAIL'].includes(review.verdict) && !attached.length) fail('UNINSPECTED_EVIDENCE', 'PASS or FAIL needs inspected supporting artifacts; otherwise report INCONCLUSIVE or NOT_ASSESSED.');
    if (review.verdict === 'PASS') {
      const observed = execution.observations.find(item => item.expectation_id === expected.id);
      if (problems.length || execution.execution_status !== 'COMPLETED' || observed.gaps.length) fail('INCOMPLETE_PROOF', 'A stale, partial, not-run, or evidence-gap execution cannot pass.', problems);
      for (const requirement of expected.evidence_requirements) if (!attached.some(item => coversRequirement(item, expected, requirement))) fail('EVIDENCE_COVERAGE', 'A passing review must inspect every required capture.');
    }
    if (review.verdict === 'FAIL' && problems.length) fail('INCOMPLETE_PROOF', 'Changed or missing artifacts cannot establish a product failure; report INCONCLUSIVE.', problems);
  }
  const roots = new Set();
  for (const proposed of record.findings || []) if (proposed.lineage_id && proposed.class !== 'SIDE_FINDING') {
    const root = findingFor(state, proposed.lineage_id);
    if (!root || root.record.scope !== 'in_scope' || !root.record.authorized || !record.reviews.some(item => item.verdict === 'FAIL')) fail('UNSUPPORTED_LINEAGE', 'Explicit lineage requires an in-scope root and independently inspected failure evidence for both cases.');
    roots.add(root.record.finding_id);
  }
  const existingRoots = effectiveFindings(state).filter(item => item.record.scope === 'in_scope' && item.record.case_ids.includes(record.case_id)).map(item => item.record.finding_id);
  if (roots.size > 1 || (roots.size && existingRoots.some(id => !roots.has(id)))) fail('LINEAGE_CONFLICT', 'Conflicting roots require finding link with evidence after conflicting work has stopped.');
  return record;
}

async function validateRoleResult(state, task, record) {
  for (const artifact of record.artifacts || []) {
    const computed = await hashArtifact(state, artifact.path);
    if (artifact.sha256 && artifact.sha256 !== computed.sha256) fail('EVIDENCE_CHANGED', `Role artifact changed: ${artifact.path}`);
    artifact.sha256 = computed.sha256;
  }
  if (record.finding_id && record.finding_id !== task.finding_id) fail('WRONG_ASSIGNMENT', 'Result belongs to a different finding.');
  if (!isCompleteResult(record)) return;
  if (record.kind === 'diagnosis') {
    if (record.conclusion === 'confirmed' && !record.root_cause) fail('UNCONFIRMED_DEFECT', 'A confirmed diagnosis needs a concrete root cause.');
    if (record.evidence_record_ids.some(id => !state.records.some(item => item.record.record_id === id))) fail('MISSING_PROVENANCE', 'Diagnosis references a missing evidence record.');
  } else if (record.kind === 'ticket') {
    if (record.dedup_marker !== `agentic-tests:${state.config.campaign_id}:${record.finding_id}`) fail('INVALID_DEDUP_MARKER', 'Ticket marker must include the campaign and stable finding ID.');
    await hashArtifact(state, record.body_path);
  } else if (record.kind === 'implementation') {
    const assignedAttempt = Number(task.outputs[0].record_id.match(/-A(\d+)(?:-J\d+)?$/)[1]);
    if (record.attempt !== assignedAttempt) fail('WRONG_ASSIGNMENT', 'Implementation attempt differs from the assigned attempt.');
    const frozenRoots = byKind(state.records, 'environment').map(item => item.record.source.worktree || item.record.command.cwd);
    const worktree = await realpath(record.worktree);
    if (frozenRoots.includes(worktree)) fail('FROZEN_SOURCE', 'Implement in a separate worktree from every running target.');
    if (record.changed_files.some(file => path.isAbsolute(file) || file.split(/[\\/]/).some(part => part === '..' || (part !== '.env.example' && /^\.env(?:\.|$)/.test(part))))) fail('UNSAFE_PATH', 'Changed files must be safe source-relative paths without secrets; .env.example placeholders are allowed.');
    const body = await readFile(containedPath(state.campaign, record.pr_body_path), 'utf8');
    if (Array.from(body).length > 50000) fail('PR_BODY_TOO_LONG', 'PR body exceeds 50,000 Unicode characters.');
    if (/\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+(?:#[0-9]+|[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+#[0-9]+|https:\/\/github\.com\/\S+\/issues\/\d+)/i.test(body)) fail('PREMATURE_ISSUE_CLOSURE', 'Use related-issue references until independent retest confirms resolution.');
    for (const check of record.checks) {
      await hashArtifact(state, check.artifact_path);
      if (check.exit_code !== 0) fail('FAILED_DEVELOPER_CHECK', 'An implementation ready for integration must pass its declared developer checks.');
    }
  } else if (record.kind === 'integration') {
    const implementation = completedRecords(state.records, 'implementation').map(item => item.record).find(item => item.record_id === record.implementation_record_id && item.finding_id === record.finding_id);
    if (!implementation || !task.required_inputs.some(input => state.records.some(item => item.path === input && item.record.record_id === implementation.record_id))) fail('WRONG_ASSIGNMENT', 'Integrate the assigned accepted implementation.');
    const target = environmentFor(state, record.new_target_id)?.record;
    if (target && target.source.revision !== record.commit) fail('TARGET_DRIFT', 'An existing integrated target must identify the declared integrated commit.');
    const already = state.records.some(item => item.record.record_id === record.record_id);
    if (!already && Number(record.new_target_id.slice(1)) <= Number(state.config.final_target_id.slice(1))) fail('TARGET_DRIFT', 'Integration must allocate a new runtime generation.');
    const known = planFor(state).cases.map(item => item.case_id);
    if (record.affected_case_ids.some(id => !known.includes(id)) || findingFor(state, record.finding_id).record.case_ids.some(id => !record.affected_case_ids.includes(id))) fail('RETEST_COVERAGE', 'Affected cases must include every case linked to this finding and belong to the accepted plan.');
    if (record.affected_case_ids.some(id => !record.retest_obligations.some(item => item.case_id === id)) || record.retest_obligations.some(item => !known.includes(item.case_id))) fail('RETEST_COVERAGE', 'Every affected case requires an explicit independent retest obligation.');
  }
}

async function validateSubmission(state, task, draft) {
  validateRecord(draft);
  const output = task.outputs.find(item => item.kind === draft.kind && item.record_id === draft.record_id && item.case_id === draft.case_id);
  if (!output) fail('WRONG_ASSIGNMENT', 'Result does not match an assigned output.');
  if (draft.campaign_id !== state.config.campaign_id || draft.task_id !== task.task_id || draft.actor_id !== task.actor_id) fail('WRONG_ASSIGNMENT', 'Result campaign, task, and actor must match the assignment.');
  for (const field of ['spec_revision', 'round_id', 'target_id']) if (task[field] !== undefined && draft[field === 'target_id' && draft.kind === 'integration' ? 'new_target_id' : field] !== task[field]) fail('WRONG_ASSIGNMENT', `Result ${field} differs from its assignment.`);
  if (!task.handle || !['RUNNING', 'DONE'].includes(task.state)) fail('TASK_NOT_RUNNING', 'Bind a real dispatched worker context before submitting.');
  if (!isCompleteResult(draft)) { await validateRoleResult(state, task, draft); return { record: draft, output }; }
  if (draft.kind === 'expectations') {
    if (draft.author_actor_id !== task.actor_id) fail('ACTOR_ISOLATION', 'The scenario author must be the assigned actor.');
    const ids = draft.expectations.map(item => item.id);
    if (new Set(ids).size !== ids.length) fail('INVALID_EXPECTATIONS', 'Expectation IDs must be unique.');
    for (const item of draft.expectations) {
      if ((item.priority === 'P0' || item.critical || item.subjective) && item.review_count !== 2) fail('QUORUM_REQUIRED', 'Critical and subjective expectations require two independent reviews.');
      if (new Set(item.evidence_requirements.map(requirement => requirement.id)).size !== item.evidence_requirements.length) fail('INVALID_EXPECTATIONS', 'Evidence requirement IDs must be unique within an expectation.');
    }
    const root = path.posix.dirname(output.path);
    const scenario = await readFile(containedPath(state.campaign, `${root}/01-test-case.md`), 'utf8');
    const how = await readFile(containedPath(state.campaign, `${root}/03-how-to-run.md`), 'utf8');
    if (scenario.trim() === '# TODO: Write a sourced Given/When/Then scenario with expectation IDs.' || how.trim() === '# TODO: Write real E2E steps and evidence capture instructions.' || !['Given', 'When', 'Then'].every(word => new RegExp(`\\b${word}\\b`, 'i').test(scenario)) || !ids.every(id => scenario.includes(`[${id}]`)) || how.trim().length < 20) fail('INVALID_SCENARIO', 'Scenario needs sourced Given/When/Then, every [expectation ID], and concrete E2E steps.');
  } else if (draft.kind === 'plan') {
    await validatePlan(state, draft);
  } else if (draft.kind === 'plan_audit') {
    const subject = state.records.find(item => item.record.kind === 'plan' && item.record.record_id === draft.subject_record_id)?.record;
    const assessment = task.phase === 'closure' ? await assessState(state) : null;
    const expectedDigest = assessment?.closure_subject_digest || (subject && digest(subject));
    if (!subject || subject.record_id !== task.plan_id || draft.phase !== task.phase || draft.subject_digest !== expectedDigest) fail('WRONG_AUDIT_SUBJECT', 'Audit must reference the assigned plan/current proof and exact digest.');
    if (subject.actor_id === draft.actor_id || findTask(state, subject.task_id).handle === task.handle) fail('ACTOR_ISOLATION', 'Plan author and auditor must use independent contexts.');
    if (task.phase === 'closure' && draft.outcome === 'approved') {
      const remaining = assessment.obligations.filter(item => item.type !== 'CLOSURE_AUDIT_REQUIRED' && item.task_id !== task.task_id);
      if (remaining.length || assessment.cases.some(item => item.outcome !== 'PASS' || !item.proof_valid)) fail('CLOSURE_BLOCKED', 'Closure approval cannot ignore unfinished tasks, scope decisions, repairs, retests, or current proof.', remaining);
    }
  } else if (draft.kind === 'execution') {
    await validateExecution(state, task, draft, output);
  } else if (draft.kind === 'verification') {
    await validateVerification(state, task, draft);
  }
  await validateRoleResult(state, task, draft);
  return { record: draft, output };
}

async function submit(options, state) {
  const task = findTask(state, required(options, 'task-id'));
  const draft = await readYaml(required(options, 'file'));
  draft.created_at = state.records.find(item => item.record.record_id === draft.record_id)?.record.created_at || task.created_at;
  const { record, output } = await validateSubmission(state, task, draft);
  const existing = state.records.find(item => item.path === output.path);
  if (existing && stableStringify(existing.record) !== stableStringify(record)) fail('RECORD_CONFLICT', 'A different result was already accepted for this assignment.', [], 4);
  if (!trueFlag(options.check)) {
    await writeRecord(state.campaign, output.path, record);
    await synchronizeDerived(await snapshot(state.campaign));
  }
  const accepted = task.outputs.every(item => item.path === output.path || state.records.some(record => record.path === item.path));
  return { submission_status: trueFlag(options.check) ? 'VALIDATED' : 'ACCEPTED', worker_may_finish: !trueFlag(options.check) && accepted, test_verdict: 'NOT_DECIDED', record_id: record.record_id, next_actions: trueFlag(options.check) ? ['SUBMIT'] : accepted ? ['CLOSE_TASK_AFTER_HOST_FINISH'] : ['SUBMIT_REMAINING_OUTPUTS'] };
}

async function assessState(state) {
  const plan = planFor(state);
  const cases = [];
  const obligations = [];
  if (!plan) obligations.push({ type: 'PLAN_REQUIRED' });
  const integratedTarget = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === state.config.final_target_id)?.record;
  const runtime = environmentFor(state, state.config.final_target_id)?.record;
  if (integratedTarget && (!runtime || runtime.status !== 'READY' || runtime.source.revision !== integratedTarget.commit)) obligations.push({ type: 'PREPARE_TARGET', target_id: integratedTarget.new_target_id, commit: integratedTarget.commit });
  for (const entry of plan?.cases || []) {
    const target = state.config.final_target_id;
    const contexts = byKind(state.records, 'round_context').map(item => item.record).filter(item => item.case_id === entry.case_id && item.spec_revision === entry.spec_revision && item.target_id === target).sort((a, b) => b.round_id.localeCompare(a.round_id));
    const context = contexts[0];
    const current = { case_id: entry.case_id, spec_revision: entry.spec_revision, target_id: target, round_id: context?.round_id || null, outcome: 'NOT_RUN', proof_valid: false, blockers: [] };
    const execution = context && byKind(state.records, 'execution').map(item => item.record).find(item => item.case_id === entry.case_id && item.round_id === context.round_id);
    if (!execution) current.blockers.push({ type: completedRecords(state.records, 'integration').length ? 'RETEST_REQUIRED' : 'EXECUTION_REQUIRED', case_id: entry.case_id, target_id: target });
    else {
      current.execution_record_id = execution.record_id;
      const round = roundRecords(state, execution);
      const verdict = latestVerdict(state, item => item.execution_record_id === execution.record_id);
      const problems = verdict ? await sealedProofProblems(state, execution, verdict) : await proofProblems(state, round);
      if (!verdict) {
        current.outcome = 'PENDING_VERIFICATION';
        current.blockers.push({ type: 'VERIFICATION_REQUIRED', case_id: entry.case_id, round_id: execution.round_id, required_reviews: round.spec ? Math.max(...round.spec.expectations.map(item => item.review_count)) : null, accepted_reviews: round.reviews.length });
      } else {
        current.verdict_record_id = verdict.record_id;
        current.outcome = verdict.outcome;
        if (problems.length) current.outcome = 'INCONCLUSIVE';
        current.proof_valid = !problems.length;
        const reviewOnlyRecovery = problems.some(item => item.type === 'VERIFICATION_REQUIRED') && problems.every(item => ['VERIFICATION_REQUIRED', 'RECORDS_CHANGED'].includes(item.type));
        if (current.outcome !== 'PASS' && !reviewOnlyRecovery) current.blockers.push({ type: current.outcome === 'FAIL' ? 'FIX_REQUIRED' : 'FRESH_EXECUTION_REQUIRED', case_id: entry.case_id, round_id: execution.round_id });
      }
      current.blockers.push(...problems.map(item => ({ ...item, case_id: entry.case_id, round_id: execution.round_id })));
    }
    const environment = environmentFor(state, target)?.record;
    if (!environment || environment.status !== 'READY') {
      current.proof_valid = false;
      current.blockers.push({ type: 'TARGET_NOT_READY', case_id: entry.case_id, target_id: target });
    }
    obligations.push(...current.blockers);
    cases.push(current);
  }
  for (const { record: finding } of effectiveFindings(state)) {
    if (finding.scope === 'pending') obligations.push({ type: 'SCOPE_DECISION_REQUIRED', finding_id: finding.finding_id });
    else if (finding.scope === 'in_scope' && finding.class === 'SIDE_FINDING' && finding.state !== 'RESOLVED') obligations.push({ type: 'CONFIRMATION_REQUIRED', finding_id: finding.finding_id, case_ids: finding.confirmation_case_ids || [] });
    else if (finding.scope === 'in_scope' && !['RESOLVED', 'OUT_OF_SCOPE'].includes(finding.state)) obligations.push({ type: finding.attempts >= state.config.max_attempts ? 'ATTEMPT_LIMIT' : 'FINDING_OPEN', finding_id: finding.finding_id, remaining_attempts: Math.max(0, state.config.max_attempts - finding.attempts) });
  }
  for (const task of state.tasks) if (task.state !== 'DONE' && !(task.worker_finished && ['INTERRUPTED', 'CANCELLED'].includes(task.state))) obligations.push({ type: active(task) ? 'WORKER_ACTIVE' : 'TASK_PENDING', task_id: task.task_id, role: task.role });
  for (const { record } of state.records.filter(item => !isCompleteResult(item.record))) {
    if (!hasCompletedReplacement(state, record.task_id)) obligations.push({ type: 'ROLE_BLOCKED', task_id: record.task_id, record_id: record.record_id, reason_code: record.blocker.reason_code, detail: record.blocker.detail });
  }
  const proof = { plan_id: plan?.record_id || null, final_target_id: state.config.final_target_id, cases, findings: effectiveFindings(state).map(item => item.record), integrations: completedRecords(state.records, 'integration').map(item => item.record.record_id).sort() };
  const closureDigest = digest(proof);
  const closure = byKind(state.records, 'plan_audit').map(item => item.record).find(item => item.phase === 'closure' && item.subject_record_id === plan?.record_id && item.subject_digest === closureDigest && item.outcome === 'approved' && !item.findings.length);
  if (plan && !closure) obligations.push({ type: 'CLOSURE_AUDIT_REQUIRED', subject_record_id: plan.record_id, subject_digest: closureDigest });
  const ready = []; const blocked = [];
  for (const task of state.tasks.filter(task => ['PLANNED', 'READY', 'BLOCKED'].includes(task.state))) {
    const reasons = await eligibility(task, state);
    if (reasons.length) blocked.push({ task_id: task.task_id, reasons });
    else ready.push(task.task_id);
  }
  const complete = Boolean(plan && cases.length && cases.every(item => item.outcome === 'PASS' && item.proof_valid) && !obligations.length);
  return { complete, outcome: complete ? 'PASS' : cases.some(item => item.outcome === 'FAIL') ? 'FAIL' : 'INCOMPLETE', latest_target_id: state.config.final_target_id, findings: effectiveFindings(state).map(item => item.record), counts: { cases: cases.length, pass: cases.filter(item => item.outcome === 'PASS' && item.proof_valid).length, tasks: state.tasks.length, active: state.tasks.filter(active).length, ready: ready.length, blocked: blocked.length, obligations: obligations.length }, cases, ready, running: state.tasks.filter(active).map(task => task.task_id), blocked, obligations, closure_subject_record_id: plan?.record_id || null, closure_subject_digest: closureDigest, closure_audit_record_id: closure?.record_id || null };
}

export async function assessCampaign(campaign, records) {
  await loadDependencies();
  if (!records) return assessState(await snapshot(campaign));
  const config = records.find(item => item.record.kind === 'campaign')?.record;
  if (!config) fail('INVALID_CAMPAIGN', 'Campaign record is missing.');
  const actual = await readCampaign(campaign);
  if (actual.campaign_id !== config.campaign_id) fail('WRONG_CAMPAIGN', 'Report snapshot belongs to another campaign.');
  const ids = new Set();
  for (const { record, path: relative } of records) {
    validateRecord(record);
    containedPath(campaign, relative);
    if (record.campaign_id !== config.campaign_id) fail('WRONG_CAMPAIGN', `${record.record_id} belongs to another campaign.`);
    if (ids.has(record.record_id)) fail('DUPLICATE_RECORD', `Duplicate record ${record.record_id}.`);
    ids.add(record.record_id);
  }
  const state = { campaign, records, config, tasks: byKind(records, 'task').map(item => item.record) };
  await refreshFindings(state);
  return assessState(state);
}

function lineageRoot(state, findingId) {
  if (!findingId) return findingId;
  const seen = new Set(); let id = findingId;
  while (id) {
    if (seen.has(id)) fail('LINEAGE_CYCLE', 'Finding relationships contain a cycle.');
    seen.add(id);
    const raw = byKind(state.records, 'finding').find(item => item.record.finding_id === id)?.record;
    const links = byKind(state.records, 'finding_link').filter(item => item.record.from_finding_id === id);
    const targets = [...new Set(links.map(item => item.record.into_finding_id))];
    if (targets.length > 1) fail('LINEAGE_CONFLICT', 'A finding has conflicting effective roots.');
    const parent = targets[0] || (raw?.lineage_id !== id ? raw?.lineage_id : null);
    if (!parent) return id;
    if (!byKind(state.records, 'finding').some(item => item.record.finding_id === parent)) fail('FINDING_NOT_FOUND', 'Finding relationship references a missing root.');
    id = parent;
  }
  return id;
}

const attemptIdentity = intervention => `ATT-${digest(intervention).slice(0, 16)}`;
function interventionFor(state, task) {
  if (task.purpose === 'final' && !task.intervention && !task.prior_context) {
    const previous = state.tasks.filter(item => item.role === 'executor' && item.target_id === task.target_id && item.case_ids.some(id => task.case_ids.includes(id)) && item.attempt_id).at(-1);
    if (previous) { if (previous.prior_context) task.prior_context = structuredClone(previous.prior_context); return previous.intervention; }
  }
  if (task.intervention) return task.intervention;
  const integration = completedRecords(state.records, 'integration').find(item => item.record.new_target_id === task.target_id)?.record;
  if (integration) return { kind: 'INTEGRATION', ref: integration.record_id };
  if (task.prior_context) return { kind: 'EXECUTION_APPROACH', ref: digest({ what_changed: task.prior_context.what_changed, hypothesis: task.prior_context.hypothesis }) };
  return { kind: 'BASELINE', ref: 'initial-assessment' };
}

function caseReservationProblems(state, task) {
  if (task.role !== 'executor') return [];
  const problems = [];
  for (const other of state.tasks) {
    if (other.task_id === task.task_id || other.role !== 'executor' || other.target_id !== task.target_id || other.spec_revision !== task.spec_revision || !other.case_ids.some(id => task.case_ids.includes(id))) continue;
    if (active(other) || ['PLANNED', 'READY', 'BLOCKED'].includes(other.state)) problems.push({ code: 'CASE_RESERVED', task_id: other.task_id, case_ids: other.case_ids.filter(id => task.case_ids.includes(id)) });
    else for (const { record: execution } of byKind(state.records, 'execution').filter(item => item.record.task_id === other.task_id && task.case_ids.includes(item.record.case_id))) {
      const verdict = latestVerdict(state, item => item.execution_record_id === execution.record_id);
      if (!verdict || verdict.inputs_digest !== roundDigest(roundRecords(state, execution))) problems.push({ code: 'VERIFICATION_REQUIRED', record_id: execution.record_id });
    }
  }
  return problems;
}

function validateIntervention(state, task) {
  const intervention = task.intervention;
  if (intervention.kind === 'BASELINE' && intervention.ref !== 'initial-assessment') fail('INVALID_INTERVENTION', 'All initial baseline cases share ref initial-assessment.');
  if (intervention.kind === 'INTEGRATION' && !completedRecords(state.records, 'integration').some(item => item.record.record_id === intervention.ref && item.record.new_target_id === task.target_id)) fail('INVALID_INTERVENTION', 'Integration basis must identify the accepted integration for this target.');
  if (intervention.kind === 'EXECUTION_APPROACH' && !task.prior_context) fail('RETRY_CONTEXT_REQUIRED', 'A changed execution approach requires concrete what_changed, hypothesis and do_not_repeat.');
  for (const other of state.tasks.filter(item => item.role === 'executor' && item.task_id !== task.task_id)) {
    const runs = byKind(state.records, 'execution').filter(item => item.record.task_id === other.task_id && item.record.execution_status !== 'NOT_RUN' && task.case_ids.includes(item.record.case_id));
    if (!runs.length) continue;
    const sameAttempt = (other.attempt_id || attemptIdentity(interventionFor(state, other))) === task.attempt_id;
    const repeatedApproach = task.prior_context && other.prior_context && task.prior_context.what_changed === other.prior_context.what_changed && task.prior_context.hypothesis === other.prior_context.hypothesis;
    if (!sameAttempt && !repeatedApproach) continue;
    const finalAllowed = task.purpose === 'final' && other.purpose !== 'final' && runs.every(item => latestVerdict(state, verdict => verdict.execution_record_id === item.record.record_id)?.outcome === 'PASS');
    const recoveredTarget = sameAttempt && task.target_id !== other.target_id && effectiveTarget(state, other.target_id) === task.target_id;
    if (!finalAllowed && !recoveredTarget) {
      const finding = task.finding_id && findingFor(state, task.finding_id)?.record;
      fail(finding?.attempts >= state.config.max_attempts ? 'ATTEMPT_LIMIT' : 'REPEAT_INTERVENTION', 'This case already exercised the intervention. Use a genuinely changed correction; final sweeps cannot repeat failed work.');
    }
  }
}

function effectiveTarget(state, target) {
  const seen = new Set(); let current = target;
  while (current) {
    if (seen.has(current)) fail('RECOVERY_CYCLE', 'Runtime recovery chain contains a cycle.');
    seen.add(current);
    const links = byKind(state.records, 'runtime_recovery').filter(item => item.record.predecessor_target_id === current);
    if (!links.length) return current;
    if (links.length > 1) fail('RECOVERY_CONFLICT', 'Runtime generation has conflicting successors.');
    current = links[0].record.successor_target_id;
  }
  return current;
}

async function refreshFindings(state) {
  state.findings = [];
  const roots = [...new Set(byKind(state.records, 'finding').map(item => lineageRoot(state, item.record.finding_id)))];
  for (const id of roots) {
    const entry = byKind(state.records, 'finding').find(item => item.record.finding_id === id);
    const members = byKind(state.records, 'finding').filter(item => lineageRoot(state, item.record.finding_id) === id);
    const record = structuredClone(entry.record);
    record.lineage_id = id;
    record.related_finding_ids = members.map(item => item.record.finding_id);
    record.case_ids = [...new Set(members.flatMap(item => item.record.case_ids))].sort();
    record.source_record_ids = [...new Set(members.flatMap(item => item.record.source_record_ids))];
    record.priority = members.map(item => item.record.priority).sort()[0];
    const history = byKind(state.records, 'finding_classification').map(item => item.record).filter(item => lineageRoot(state, item.finding_id) === id).sort((a, b) => a.created_at.localeCompare(b.created_at) || a.record_id.localeCompare(b.record_id));
    record.classification_history = history;
    if (history.some(item => item.class === 'PRODUCT_DEFECT') || members.some(item => item.record.class === 'PRODUCT_DEFECT')) record.class = 'PRODUCT_DEFECT';
    const executions = byKind(state.records, 'execution').map(item => item.record).filter(execution => record.source_record_ids.includes(execution.record_id) || lineageRoot(state, state.tasks.find(task => task.task_id === execution.task_id)?.finding_id) === id);
    record.attempt_rounds = []; record.attempt_mapping_problems = [];
    for (const execution of executions.filter(item => item.execution_status !== 'NOT_RUN')) {
      const task = state.tasks.find(item => item.task_id === execution.task_id);
      const intervention = interventionFor(state, task || {});
      const attemptId = task?.attempt_id || attemptIdentity(intervention);
      if (!task?.attempt_id && task?.finding_id && !task.prior_context && intervention.kind === 'BASELINE' && task.purpose !== 'initial') record.attempt_mapping_problems.push(execution.record_id);
      record.attempt_rounds.push({ case_id: execution.case_id, round_id: execution.round_id, execution_record_id: execution.record_id, attempt_id: record.attempt_mapping_problems.includes(execution.record_id) ? `LEGACY-${execution.record_id}` : attemptId });
    }
    // Retain unresolvable historical entries rather than silently forgetting spent corrections.
    for (const round of members.flatMap(item => item.record.attempt_rounds)) if (!record.attempt_rounds.some(item => item.execution_record_id === round.execution_record_id)) { record.attempt_rounds.push({ ...round, attempt_id: round.attempt_id || `LEGACY-${round.execution_record_id}` }); record.attempt_mapping_problems.push(round.execution_record_id); }
    record.attempt_ids = [...new Set(record.attempt_rounds.map(item => item.attempt_id))];
    record.attempts = record.attempt_ids.length;
    const related = kind => completedRecords(state.records, kind).map(item => item.record).filter(item => lineageRoot(state, item.finding_id) === id);
    record.related_issue_urls = [...new Set([...members.map(item => item.record.issue_url), ...related('ticket').map(item => item.issue_url)].filter(Boolean))];
    if (record.related_issue_urls.length) record.issue_url ||= record.related_issue_urls[0];
    record.pr_urls = [...new Set([...members.flatMap(item => item.record.pr_urls || []), ...related('implementation').map(item => item.pr_url)])];
    record.authorized = false;
    for (const execution of executions) {
      const verdict = latestVerdict(state, item => item.execution_record_id === execution.record_id);
      if (verdict?.outcome === 'FAIL' && execution.target_id === state.config.final_target_id && !(await sealedProofProblems(state, execution, verdict)).length) record.authorized = true;
    }
    if (!['RESOLVED', 'OUT_OF_SCOPE'].includes(record.state) && record.attempts >= state.config.max_attempts) record.state = 'EXHAUSTED';
    state.findings.push({ path: entry.path, record });
  }
}

export async function resolveFindings(campaign, records) {
  await loadDependencies();
  const state = records ? { campaign, records, config: records.find(item => item.record.kind === 'campaign')?.record, tasks: byKind(records, 'task').map(item => item.record) } : await snapshot(campaign);
  if (!state.config) fail('INVALID_CAMPAIGN', 'Campaign record is missing.');
  if (records) await refreshFindings(state);
  return { findings: effectiveFindings(state).map(item => item.record), relationships: byKind(state.records, 'finding_link').map(item => item.record) };
}

async function recordFinding(state, round, outcome, problems) {
  if (outcome === 'PASS') return null;
  const execution = round.execution;
  const contextFinding = round.context.finding_ids[0];
  let existing = contextFinding ? findingFor(state, contextFinding) : effectiveFindings(state).find(item => item.record.scope === 'in_scope' && item.record.class !== 'SIDE_FINDING' && item.record.state !== 'RESOLVED' && item.record.case_ids.includes(execution.case_id));
  const disagree = round.spec.expectations.some(expected => new Set(round.reviews.map(item => item.reviews.find(review => review.expectation_id === expected.id).verdict)).size > 1);
  const proposed = round.reviews.flatMap(item => item.findings || []).find(item => item.class !== 'SIDE_FINDING');
  let classification = problems.length ? 'EVIDENCE_CONFLICT' : execution.execution_status === 'NOT_RUN' ? 'ENVIRONMENT_BLOCKER' : disagree ? 'VERIFIER_DISAGREEMENT' : outcome === 'FAIL' ? 'PRODUCT_DEFECT' : 'EVIDENCE_GAP';
  if (proposed && proposed.class !== 'PRODUCT_DEFECT' && !problems.length && !disagree && outcome !== 'NOT_RUN' && outcome !== 'FAIL') classification = proposed.class;
  const requestedRoots = [...new Set(round.reviews.flatMap(item => item.findings || []).filter(item => item.class !== 'SIDE_FINDING' && item.lineage_id).map(item => lineageRoot(state, item.lineage_id)))];
  if (requestedRoots.length > 1 || (existing && requestedRoots.length && requestedRoots[0] !== existing.record.finding_id)) fail('LINEAGE_CONFLICT', 'Conflicting finding roots require a supported finding link after conflicting work is quiescent.');
  if (requestedRoots.length && classification === 'PRODUCT_DEFECT') existing = findingFor(state, requestedRoots[0]);
  const id = existing?.record.finding_id || next(byKind(state.records, 'finding').map(item => item.record.finding_id), 'F', 4);
  const sources = [execution.record_id, ...round.reviews.map(item => item.record_id)];
  if (!existing) {
    const attempts = execution.execution_status === 'NOT_RUN' ? 0 : 1;
    const finding = { ...common(state.config, 'finding', id), finding_id: id, class: classification, priority: round.spec.expectations.map(item => item.priority).sort()[0], case_ids: [execution.case_id], source_record_ids: sources, scope: 'in_scope', state: attempts >= state.config.max_attempts ? 'EXHAUSTED' : 'OPEN', lineage_id: id, attempts, attempt_rounds: attempts ? [{ case_id: execution.case_id, round_id: execution.round_id, execution_record_id: execution.record_id }] : [], summary: proposed?.summary || `${execution.case_id}/${execution.round_id}: ${classification.toLowerCase().replaceAll('_', ' ')}` };
    if (problems.length) finding.reason_code = problems.some(item => item.type === 'MISSING_ARTIFACT') ? 'MISSING_ARTIFACT' : 'EVIDENCE_CHANGED';
    else if (execution.blocker) finding.reason_code = execution.blocker.reason_code;
    existing = { record: finding, path: `findings/${id}-${execution.case_id.toLowerCase()}/00-finding.record.yaml` };
    await writeRecord(state.campaign, existing.path, finding); state.records.push(existing);
  } else {
    const raw = byKind(state.records, 'finding').find(item => item.record.finding_id === id);
    raw.record = { ...raw.record, case_ids: [...new Set([...existing.record.case_ids, execution.case_id])], source_record_ids: [...new Set([...existing.record.source_record_ids, ...sources])], class: existing.record.class === 'PRODUCT_DEFECT' ? 'PRODUCT_DEFECT' : classification };
    await writeRecord(state.campaign, raw.path, raw.record, { immutable: false });
  }
  const historyId = `CLASS-${id}-${execution.record_id}-${digest(sources).slice(0, 8)}`;
  if (!state.records.some(item => item.record.record_id === historyId)) {
    const record = { ...common(state.config, 'finding_classification', historyId), finding_id: id, class: classification, execution_record_id: execution.record_id, evidence_record_ids: sources };
    const relative = `${path.posix.dirname(existing.path)}/classifications/${historyId}.record.yaml`;
    await writeRecord(state.campaign, relative, record); state.records.push({ record, path: relative });
  }
  await refreshFindings(state);
  return id;
}

async function recordSideFindings(state, round) {
  const ids = [];
  for (const source of [round.execution, ...round.reviews]) for (const proposed of source.findings || []) {
    if (proposed.class !== 'SIDE_FINDING') continue;
    const previous = byKind(state.records, 'finding').find(item => item.record.summary === proposed.summary && item.record.case_ids.includes(round.execution.case_id));
    if (previous) { ids.push(previous.record.finding_id); continue; }
    const id = next(byKind(state.records, 'finding').map(item => item.record.finding_id), 'F', 4);
    const finding = { ...common(state.config, 'finding', id), finding_id: id, class: 'SIDE_FINDING', priority: proposed.priority || 'P2', case_ids: [round.execution.case_id], source_record_ids: [source.record_id], scope: 'pending', state: 'OPEN', lineage_id: id, attempts: 0, attempt_rounds: [], summary: proposed.summary, confirmation_case_ids: [] };
    const relative = `findings/${id}-${round.execution.case_id.toLowerCase()}/00-finding.record.yaml`;
    await writeRecord(state.campaign, relative, finding);
    state.records.push({ record: finding, path: relative });
    ids.push(id);
  }
  return [...new Set(ids)];
}

async function linkFinding(options, state) {
  const request = await readYaml(required(options, 'file')); validateShape('finding_link_request', request);
  const from = findingFor(state, request.from_finding_id), into = findingFor(state, request.into_finding_id);
  if (!from || !into) fail('FINDING_NOT_FOUND', 'Link only findings owned by this campaign.');
  if (from.record.finding_id === into.record.finding_id) fail('LINEAGE_CYCLE', 'Findings already share a root; a reverse or self link would create a cycle.');
  if (from.record.scope !== 'in_scope' || into.record.scope !== 'in_scope') fail('SCOPE_OBLIGATION', 'Both linked roots must be in scope.');
  const ids = [from.record.finding_id, into.record.finding_id];
  const busy = state.tasks.filter(task => ids.includes(lineageRoot(state, task.finding_id)) && !task.worker_finished && !['DONE', 'CANCELLED'].includes(task.state));
  if (busy.length) fail('LINEAGE_BUSY', 'Finish or interrupt conflicting root work and confirm host termination before linking.', busy.map(item => item.task_id), 4);
  const evidence = request.evidence_record_ids.map(id => state.records.find(item => item.record.record_id === id) || fail('MISSING_PROVENANCE', 'Link evidence must name accepted records in this campaign.'));
  for (const root of [from.record, into.record]) {
    let supported = false;
    for (const item of evidence) {
      const execution = item.record.kind === 'execution' ? item.record : byKind(state.records, 'execution').find(e => e.record.record_id === item.record.execution_record_id)?.record;
      const verdict = execution && latestVerdict(state, v => v.execution_record_id === execution.record_id);
      if (execution && root.case_ids.includes(execution.case_id) && verdict?.outcome === 'FAIL' && !(await sealedProofProblems(state, execution, verdict)).length) supported = true;
    }
    if (!supported) fail('UNSUPPORTED_LINEAGE', 'Link evidence must support a current independently reviewed failure on each root.');
  }
  const record = { ...common(state.config, 'finding_link', `LINK-${from.record.finding_id}-${into.record.finding_id}`), ...request, from_finding_id: from.record.finding_id, into_finding_id: into.record.finding_id };
  await writeRecord(state.campaign, `findings/relationships/${record.record_id}.record.yaml`, record);
  await synchronizeDerived(await snapshot(state.campaign));
  return { relationship: record, effective_finding_id: into.record.finding_id, next_actions: ['RECONCILE'] };
}

async function decideFinding(options, state) {
  const finding = findingFor(state, required(options, 'finding-id'));
  if (!finding) fail('FINDING_NOT_FOUND', 'Scope decisions need a known finding.');
  const scope = required(options, 'scope');
  if (!['in_scope', 'out_of_scope'].includes(scope)) fail('USAGE', '--scope must be in_scope or out_of_scope.', [], 2);
  const reason = required(options, 'reason'); const source = required(options, 'source');
  const previous = byKind(state.records, 'scope_decision').filter(item => item.record.finding_id === finding.record.finding_id).at(-1);
  if (previous && previous.record.scope === scope && previous.record.reason === reason && previous.record.source === source) return { decision: previous.record, finding_id: finding.record.finding_id };
  const suffix = next(byKind(state.records, 'scope_decision').filter(item => item.record.finding_id === finding.record.finding_id).map(item => item.record.record_id.split('-').at(-1)), 'D', 3);
  const decision = { ...common(state.config, 'scope_decision', `DECISION-${finding.record.finding_id}-${suffix}`), finding_id: finding.record.finding_id, scope, reason, source };
  await writeRecord(state.campaign, `${path.posix.dirname(finding.path)}/decisions/${suffix}.record.yaml`, decision);
  await synchronizeDerived(await snapshot(state.campaign));
  return { decision, finding_id: finding.record.finding_id, next_actions: scope === 'in_scope' && finding.record.class === 'SIDE_FINDING' ? ['AUTHOR_INDEPENDENT_CONFIRMATION_SCENARIO'] : ['RECONCILE'] };
}

async function synchronizeDerived(state) {
  const integrations = completedRecords(state.records, 'integration').map(item => item.record);
  const latest = integrations.sort((a, b) => Number(b.new_target_id.slice(1)) - Number(a.new_target_id.slice(1)))[0];
  if (latest && Number(latest.new_target_id.slice(1)) > Number((state.config.final_target_id || 'G000').slice(1))) {
    state.config = { ...state.config, final_target_id: latest.new_target_id, state: 'OPEN' };
    await writeRecord(state.campaign, '00-campaign.record.yaml', state.config, { immutable: false });
  }
  await refreshFindings(state);
  for (const entry of effectiveFindings(state)) {
    const finding = structuredClone(entry.record);
    finding.state = 'OPEN';
    const decision = byKind(state.records, 'scope_decision').filter(item => lineageRoot(state, item.record.finding_id) === finding.finding_id).at(-1)?.record;
    if (decision) { finding.scope = decision.scope; finding.scope_decision = { decision: decision.scope, reason: decision.reason, source: decision.source }; }
    const confirmations = byKind(state.records, 'expectations').filter(item => item.record.confirms_finding_id === finding.finding_id).map(item => item.record.case_id);
    if (confirmations.length) { finding.confirmation_case_ids = [...new Set(confirmations)]; finding.case_ids = [...new Set([...finding.case_ids, ...confirmations])]; }
    for (const { record: execution } of byKind(state.records, 'execution')) {
      const task = findTask(state, execution.task_id);
      if (lineageRoot(state, task.finding_id) === finding.finding_id && execution.execution_status !== 'NOT_RUN' && !finding.attempt_rounds.some(item => item.execution_record_id === execution.record_id)) finding.attempt_rounds.push({ case_id: execution.case_id, round_id: execution.round_id, execution_record_id: execution.record_id });
    }
    finding.attempts = finding.attempt_ids.length;
    const diagnoses = completedRecords(state.records, 'diagnosis').filter(item => lineageRoot(state, item.record.finding_id) === finding.finding_id && item.record.conclusion === 'confirmed');
    const ticket = completedRecords(state.records, 'ticket').find(item => lineageRoot(state, item.record.finding_id) === finding.finding_id)?.record;
    const implementations = completedRecords(state.records, 'implementation').map(item => item.record).filter(item => lineageRoot(state, item.finding_id) === finding.finding_id);
    const integrated = integrations.some(item => lineageRoot(state, item.finding_id) === finding.finding_id);
    if (diagnoses.length) finding.state = 'DIAGNOSED';
    if (ticket) { finding.issue_url = ticket.issue_url; finding.state = 'TICKETED'; }
    if (implementations.length) { finding.pr_urls = [...new Set(implementations.map(item => item.pr_url))]; finding.state = 'IMPLEMENTED'; }
    if (integrated) finding.state = 'RETEST_PENDING';
    const relevantCases = finding.class === 'SIDE_FINDING' ? finding.confirmation_case_ids || [] : finding.case_ids;
    const passing = await Promise.all(relevantCases.map(async caseId => {
      const revision = planFor(state)?.cases.find(item => item.case_id === caseId)?.spec_revision;
      const latest = byKind(state.records, 'round_context').map(item => item.record).filter(item => item.case_id === caseId && item.spec_revision === revision && item.target_id === state.config.final_target_id).sort((a, b) => Number(b.round_id.slice(1)) - Number(a.round_id.slice(1)))[0];
      const verdict = latest && latestVerdict(state, item => item.case_id === caseId && item.round_id === latest.round_id && item.target_id === state.config.final_target_id);
      if (!verdict || verdict.outcome !== 'PASS') return false;
      const execution = byKind(state.records, 'execution').find(item => item.record.record_id === verdict.execution_record_id)?.record;
      return execution && !(await sealedProofProblems(state, execution, verdict)).length;
    }));
    if (finding.scope === 'out_of_scope') finding.state = 'OUT_OF_SCOPE';
    else if (finding.scope === 'in_scope' && relevantCases.length && passing.every(Boolean)) finding.state = 'RESOLVED';
    else if (finding.scope === 'in_scope' && finding.attempts >= state.config.max_attempts) finding.state = 'EXHAUSTED';
    await writeRecord(state.campaign, entry.path, finding, { immutable: false });
    entry.record = finding;
    const raw = byKind(state.records, 'finding').find(item => item.record.finding_id === finding.finding_id);
    raw.record = finding;
  }
  await refreshFindings(state);
}

async function reconcile(state) {
  for (const { record: execution, path: executionPath } of byKind(state.records, 'execution')) {
    const round = roundRecords(state, execution);
    const prior = latestVerdict(state, item => item.execution_record_id === execution.record_id);
    if (prior && prior.inputs_digest === roundDigest(round)) continue;
    if (prior && !prior.verification_record_ids.some(id => {
      const review = byKind(state.records, 'verification').find(item => item.record.record_id === id)?.record;
      return review && ['INTERRUPTED', 'CANCELLED'].includes(state.tasks.find(task => task.task_id === review.task_id)?.state);
    })) continue;
    if (!round.spec || round.reviews.length < Math.max(...round.spec.expectations.map(item => item.review_count))) continue;
    const problems = await proofProblems(state, round);
    const expectationVerdicts = round.spec.expectations.map(expected => {
      const reviews = round.reviews.map(item => item.reviews.find(review => review.expectation_id === expected.id));
      let outcome = 'INCONCLUSIVE';
      let reason = 'Independent reviewers disagree or cannot establish the expectation.';
      if (problems.length) reason = 'Artifacts or provenance changed after acceptance.';
      else if (execution.execution_status === 'NOT_RUN') { outcome = 'NOT_RUN'; reason = 'Execution explicitly did not run.'; }
      else if (new Set(reviews.map(item => item.verdict)).size === 1) {
        if (reviews[0].verdict === 'FAIL') { outcome = 'FAIL'; reason = 'Independent evidence review established a failure.'; }
        else if (reviews[0].verdict === 'PASS' && execution.execution_status === 'COMPLETED' && !execution.observations.find(item => item.expectation_id === expected.id).gaps.length) { outcome = 'PASS'; reason = 'Declared independent review quorum passed against saved evidence.'; }
      }
      return { expectation_id: expected.id, outcome, reason };
    });
    const outcome = expectationVerdicts.some(item => item.outcome === 'FAIL') ? 'FAIL' : expectationVerdicts.every(item => item.outcome === 'PASS') ? 'PASS' : execution.execution_status === 'NOT_RUN' ? 'NOT_RUN' : 'INCONCLUSIVE';
    const sideFindings = await recordSideFindings(state, round);
    const finding = await recordFinding(state, round, outcome, problems);
    const revision = prior ? `V${String(byKind(state.records, 'verdict').filter(item => item.record.execution_record_id === execution.record_id).length + 1).padStart(3, '0')}` : null;
    const verdict = { ...common(state.config, 'verdict', `VERDICT-${execution.case_id}-${execution.round_id}${revision ? `-${revision}` : ''}`), case_id: execution.case_id, spec_revision: execution.spec_revision, round_id: execution.round_id, target_id: execution.target_id, outcome, verification_record_ids: round.reviews.map(item => item.record_id), execution_record_id: execution.record_id, finding_ids: [...new Set([...(finding ? [finding] : []), ...sideFindings])], evidence_hashes: execution.evidence.map(item => ({ path: item.path, sha256: item.sha256 })), inputs_digest: roundDigest(round), expectation_verdicts: expectationVerdicts, ...(prior ? { supersedes_record_id: prior.record_id } : {}) };
    const relative = `${path.posix.dirname(executionPath)}/30-verdict--${outcome}${revision ? `--${revision}` : ''}.record.yaml`;
    await writeRecord(state.campaign, relative, verdict);
  }
  const fresh = await snapshot(state.campaign);
  await synchronizeDerived(fresh);
  await refreshFindings(fresh);
  const assessed = await assessState(fresh);
  for (const item of assessed.cases) {
    const spec = specFor(fresh, item.case_id, item.spec_revision);
    const root = spec.path.split('/').slice(0, 2).join('/');
    for (const file of await readdir(containedPath(state.campaign, root))) if (/^00-current--[A-Z_]+\.view\.yaml$/.test(file)) await rm(containedPath(state.campaign, `${root}/${file}`));
    await writeText(state.campaign, `${root}/00-current--${item.outcome}.view.yaml`, getDependencies().YAML.stringify(item), { overwrite: true });
  }
  await writeText(state.campaign, '01-notebook.view.yaml', getDependencies().YAML.stringify({ schema_version: 1, campaign_id: state.config.campaign_id, generated_at: now(), ...assessed }, { aliasDuplicateObjects: false }), { overwrite: true });
  return { ...assessed, next_actions: assessed.obligations };
}

export async function run(command, options = {}) {
  if (command === 'doctor') return doctor(options);
  if (command === 'init') return init(options);
  await loadDependencies();
  const campaign = path.resolve(required(options, 'campaign'));
  const perform = async () => {
    const state = await snapshot(campaign);
    if (command === 'task create') return createTask(options, state);
    if (['task dispatch', 'task bind', 'task close', 'task interrupt'].includes(command)) return transition(command, options, state);
    if (command === 'submit') return submit(options, state);
    if (command === 'plan accept') return acceptPlanCommand(options, state);
    if (command === 'finding link') return linkFinding(options, state);
    if (command === 'finding decide') return decideFinding(options, state);
    if (command === 'status') return assessState(state);
    if (command === 'reconcile') return reconcile(state);
    if (command === 'records') {
      let records = state.records.filter(item => item.record.kind !== 'finding').map(item => item.record).concat(effectiveFindings(state).map(item => item.record));
      let effectiveId;
      if (options['finding-id']) {
        const root = findingFor(state, options['finding-id']);
        if (!root) fail('FINDING_NOT_FOUND', 'No matching finding in this campaign.');
        effectiveId = root.record.finding_id;
        const sources = new Set(root.record.source_record_ids);
        records = records.filter(record => record.kind === 'finding' ? record.finding_id === effectiveId : lineageRoot(state, record.finding_id) === effectiveId || record.kind === 'finding_link' && lineageRoot(state, record.into_finding_id) === effectiveId || sources.has(record.record_id) || record.case_id && root.record.case_ids.includes(record.case_id));
      }
      for (const field of ['kind', 'record-id', 'case-id', 'round-id']) if (options[field]) records = records.filter(record => record[field.replaceAll('-', '_')] === options[field]);
      if (trueFlag(options.ready)) { const ready = (await assessState(state)).ready; records = records.filter(record => record.kind === 'task' && ready.includes(record.task_id)); }
      if (options.format && !['json', 'yaml-stream'].includes(options.format)) fail('USAGE', '--format must be json or yaml-stream.', [], 2);
      return options.format === 'yaml-stream' ? { yaml_stream: records.map(record => `---\n${getDependencies().YAML.stringify(record)}`).join('') } : { records, ...(effectiveId ? { effective_finding_id: effectiveId } : {}) };
    }
    fail('USAGE', `Unknown core command ${command}.`, [], 2);
  };
  return ['status', 'records'].includes(command) || (command === 'submit' && trueFlag(options.check)) ? perform() : withController(campaign, perform);
}
