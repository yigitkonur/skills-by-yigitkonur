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

async function snapshot(campaign) {
  const records = await readRecords(campaign);
  const config = records.find(item => item.record.kind === 'campaign')?.record;
  if (!config) fail('INVALID_CAMPAIGN', 'Campaign record is missing.');
  for (const { record } of records) if (record.campaign_id !== config.campaign_id) fail('WRONG_CAMPAIGN', `${record.record_id} belongs to another campaign.`);
  return { campaign, config, records, tasks: byKind(records, 'task').map(item => item.record) };
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
  const config = { schema_version: 1, kind: 'campaign', record_id: id, campaign_id: id, created_at: now(), project, slug, mode: options.mode || 'interactive', max_active: Number(options['max-active'] ?? 20), host_capacity: Number(options['host-capacity'] ?? 0), max_attempts: Number(options['max-attempts'] ?? 5), active_plan_id: null, final_target_id: null, locale: 'en', state: 'OPEN' };
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

function specFor(state, caseId, revision) {
  const specs = byKind(state.records, 'expectations').filter(item => item.record.case_id === caseId && (!revision || item.record.spec_revision === revision));
  return specs.sort((a, b) => b.record.spec_revision.localeCompare(a.record.spec_revision))[0];
}

const planFor = state => state.records.find(item => item.record.record_id === state.config.active_plan_id && item.record.kind === 'plan')?.record;
const environmentFor = (state, targetId) => byKind(state.records, 'environment').find(item => item.record.target_id === targetId);
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
  if (plan.kind !== 'plan' || audit.kind !== 'plan_audit' || !accepted(plan) || !accepted(audit)) fail('UNACCEPTED_PLAN', 'Submit the planner and independent auditor outputs before accepting a plan.');
  await validatePlan(state, plan);
  if (audit.phase !== 'plan' || audit.subject_record_id !== plan.record_id || audit.subject_digest !== digest(plan) || audit.outcome !== 'approved' || audit.findings.length) fail('PLAN_NOT_APPROVED', 'Plan requires an independent approval of this exact frozen revision without unresolved findings.');
  if (audit.actor_id === plan.actor_id || findTask(state, audit.task_id).handle === findTask(state, plan.task_id).handle) fail('ACTOR_ISOLATION', 'The plan auditor must use a separate real context.');
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
  for (const key of ['spec_revision', 'round_id', 'target_id', 'prior_context', 'finding_id', 'plan_id', 'phase', 'purpose', 'verification_slot', 'group']) if (request[key] !== undefined) task[key] = request[key];
  for (const dep of task.dependencies) findTask(state, dep);
  for (const input of task.required_inputs) containedPath(state.campaign, input);
  if (task.case_ids.length > 1 && !task.group) fail('INVALID_GROUP', 'Grouped variants require declared shared setup, reliable reset, and independent results.');
  const addOutput = (kind, recordId, relative, caseId) => {
    task.outputs.push({ kind, record_id: recordId, path: relative, ...(caseId ? { case_id: caseId } : {}) });
    task.draft_paths.push(`tasks/${id}/draft/${String(task.outputs.length).padStart(2, '0')}-${kind}${caseId ? `-${caseId}` : ''}.draft.yaml`);
  };
  if (task.role === 'scenario-author') {
    if (task.case_ids.length > 1) fail('INVALID_GROUP', 'Author each scenario separately.');
    if (!task.case_ids.length) task.case_ids = [next(state.tasks.flatMap(item => item.case_ids), 'T', 4)];
    const previous = specFor(state, task.case_ids[0]);
    task.spec_revision ||= next(byKind(state.records, 'expectations').filter(item => item.record.case_id === task.case_ids[0]).map(item => item.record.spec_revision), 'S', 3);
    if (previous) task.case_slug = previous.path.split('/')[1].replace(/^T\d+-/, '');
    else task.case_slug = request.slug || fail('INVALID_REQUEST', 'New scenarios require a slug.');
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
    addOutput('plan_audit', `AUDIT-${task.plan_id}-${task.phase}-${id}`, `plans/${task.plan_id}/${task.phase === 'plan' ? '20-audit' : `30-closure-${id}`}.record.yaml`);
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
    if (task.role === 'executor') task.round_id ||= next(byKind(state.records, 'round_context').filter(item => task.case_ids.includes(item.record.case_id)).map(item => item.record.round_id), 'R', 3);
    if (!task.round_id) fail('INVALID_REQUEST', 'Verifiers require an assigned round_id.');
    task.required_inputs = [];
    for (const entry of entries) {
      await ensureFrozen(state, entry.spec_hashes);
      if (entry.depends_on.some(id => task.case_ids.includes(id))) fail('INVALID_GROUP', 'Grouped variants cannot depend on each other.');
      const spec = specFor(state, entry.case_id, task.spec_revision);
      const caseRoot = spec.path.split('/').slice(0, 2).join('/');
      const root = `${caseRoot}/rounds/${task.round_id}`;
      task.required_inputs.push(...entry.spec_hashes.map(item => item.path), environment.path);
      for (const claim of entry.resources) {
        const previous = task.resources.find(item => item.name === claim.name);
        if (!previous) task.resources.push(claim);
        else if (claim.mode === 'write') previous.mode = 'write';
      }
      if (task.role === 'executor') {
        addOutput('execution', `EXEC-${entry.case_id}-${task.round_id}`, `${root}/10-execution.record.yaml`, entry.case_id);
      } else {
        const execution = byKind(state.records, 'execution').find(item => item.record.case_id === entry.case_id && item.record.round_id === task.round_id);
        if (!execution || execution.record.target_id !== task.target_id || execution.record.spec_revision !== task.spec_revision) fail('EXECUTION_NOT_FOUND', 'Verify the exact accepted execution assigned to this target/spec/round.');
        task.verification_slot ||= state.tasks.some(other => other.role === 'verifier' && other.case_ids.includes(entry.case_id) && other.round_id === task.round_id) ? 'b' : 'a';
        if (task.verification_slot === 'b' && !spec.record.expectations.some(item => item.review_count === 2)) fail('EXCESS_REVIEW', 'This case declares one review, not two.');
        task.required_inputs.push(execution.path, ...execution.record.evidence.map(item => item.path));
        addOutput('verification', `VERIFY-${entry.case_id}-${task.round_id}-${task.verification_slot}`, `${root}/${task.verification_slot === 'a' ? '20-verification-a' : '21-verification-b'}.record.yaml`, entry.case_id);
      }
    }
    task.required_inputs = [...new Set(task.required_inputs)];
  } else fail('UNSUPPORTED_ROLE', `${task.role} task allocation is not available.`);
  for (const output of task.outputs) {
    if (state.tasks.some(existing => existing.outputs.some(other => other.path === output.path))) fail('OUTPUT_CONFLICT', `${output.path} is already assigned.`, [], 4);
  }
  validateRecord(task);
  const drafts = task.outputs.map(output => ({ ...common(state.config, output.kind, output.record_id), task_id: id, actor_id: actor, ...(output.case_id ? { case_id: output.case_id } : {}), ...(task.spec_revision ? { spec_revision: task.spec_revision } : {}), ...(task.target_id ? { target_id: task.target_id } : {}), ...(task.round_id ? { round_id: task.round_id } : {}) }));
  if (task.role === 'plan-auditor') {
    const subject = state.records.find(item => item.record.record_id === task.plan_id).record;
    Object.assign(drafts[0], { phase: task.phase, subject_record_id: subject.record_id, subject_digest: digest(subject) });
  }
  if (task.role === 'scenario-author') {
    const root = path.posix.dirname(task.outputs[0].path);
    drafts[0].author_actor_id = actor;
    drafts[0].expectations = [];
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
    const context = { ...common(state.config, 'round_context', `ROUND-${output.case_id}-${task.round_id}`), case_id: output.case_id, spec_revision: task.spec_revision, round_id: task.round_id, target_id: task.target_id, execution_task_id: task.task_id, expectations_record_id: specFor(state, output.case_id, task.spec_revision).record.record_id, plan_id: task.plan_id, purpose: task.purpose, finding_ids: task.finding_id ? [task.finding_id] : [], target_source_digest: targetDigest(environmentFor(state, task.target_id).record), spec_hashes: entry.spec_hashes };
    await writeRecord(state.campaign, `${root}/00-context.record.yaml`, context);
    await mkdir(containedPath(state.campaign, `${root}/evidences`), { recursive: true });
  }
  for (let i = 0; i < drafts.length; i++) await writeText(state.campaign, task.draft_paths[i], getDependencies().YAML.stringify(drafts[i]));
  await writeText(state.campaign, `tasks/${id}/10-handoff.md`, renderHandoff(task));
  return { task, task_id: id, actor_id: actor, handoff_path: `tasks/${id}/10-handoff.md`, draft_paths: task.draft_paths, outputs: task.outputs };
}

function eligibility(task, state) {
  const reasons = [];
  for (const id of task.dependencies) if (findTask(state, id).state !== 'DONE') reasons.push(`DEPENDENCY:${id}`);
  for (const input of task.required_inputs) if (!existsSync(containedPath(state.campaign, input))) reasons.push(`MISSING_INPUT:${input}`);
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
    const reasons = eligibility(task, state);
    if (reasons.length) fail('TASK_BLOCKED', `Task ${task.task_id} is not eligible.`, reasons, 4);
    if (['executor', 'verifier'].includes(task.role)) {
      for (const id of task.case_ids) await ensureFrozen(state, planFor(state).cases.find(item => item.case_id === id).spec_hashes);
      const environment = environmentFor(state, task.target_id);
      if (!environment || environment.record.status !== 'READY') fail('TARGET_NOT_READY', 'Assigned runtime is not ready.');
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
    if (!['PLANNED', 'READY', 'BLOCKED', 'DISPATCHED', 'RUNNING', 'INTERRUPTED'].includes(task.state)) fail('INVALID_TRANSITION', 'Cannot interrupt a completed task.', [], 4);
    task.interrupt_reason = required(options, 'reason');
    task.worker_finished = trueFlag(options.finished) || !active(task);
    task.state = 'INTERRUPTED';
  }
  await writeRecord(state.campaign, taskPath(task.task_id), task, { immutable: false });
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

async function validateExecution(state, task, record, output) {
  const spec = specFor(state, record.case_id, record.spec_revision)?.record;
  if (!spec) fail('SPEC_NOT_FOUND', 'Execution requires accepted expectations.');
  if (spec.author_actor_id === record.actor_id || findTask(state, spec.task_id).handle === task.handle) fail('ACTOR_ISOLATION', 'The author cannot execute their own scenario.');
  const context = byKind(state.records, 'round_context').find(item => item.record.case_id === record.case_id && item.record.round_id === record.round_id)?.record;
  if (!context || context.execution_task_id !== task.task_id) fail('WRONG_ASSIGNMENT', 'Execution has no assigned round context.');
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
      if (!observation.gaps.some(gap => gap.requirement_id === requirement.id) && !attached.some(item => item.type === requirement.type && (!item.requirement_ids || item.requirement_ids.includes(requirement.id)))) fail('EVIDENCE_COVERAGE', `Expectation ${expected.id}/${requirement.id} needs captured evidence or an explicit gap.`);
    }
    if (record.execution_status === 'COMPLETED' && observation.gaps.length) fail('INVALID_EXECUTION_STATUS', 'A completed execution cannot omit required evidence; use PARTIAL.');
    if (record.execution_status === 'NOT_RUN' && !observation.gaps.length) fail('INVALID_EXECUTION_STATUS', 'A not-run execution must mark expectation evidence as unavailable.');
  }
  return record;
}

async function validateSubmission(state, task, draft) {
  validateRecord(draft);
  const output = task.outputs.find(item => item.kind === draft.kind && item.record_id === draft.record_id && item.case_id === draft.case_id);
  if (!output) fail('WRONG_ASSIGNMENT', 'Result does not match an assigned output.');
  if (draft.campaign_id !== state.config.campaign_id || draft.task_id !== task.task_id || draft.actor_id !== task.actor_id) fail('WRONG_ASSIGNMENT', 'Result campaign, task, and actor must match the assignment.');
  for (const field of ['spec_revision', 'round_id', 'target_id']) if (task[field] !== undefined && draft[field] !== task[field]) fail('WRONG_ASSIGNMENT', `Result ${field} differs from its assignment.`);
  if (!task.handle || !['RUNNING', 'DONE'].includes(task.state)) fail('TASK_NOT_RUNNING', 'Bind a real dispatched worker context before submitting.');
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
    if (/TODO/i.test(scenario + how) || !['Given', 'When', 'Then'].every(word => new RegExp(`\\b${word}\\b`, 'i').test(scenario)) || !ids.every(id => scenario.includes(id)) || how.trim().length < 20) fail('INVALID_SCENARIO', 'Scenario needs sourced Given/When/Then, all expectation IDs, and concrete E2E steps.');
  } else if (draft.kind === 'plan') {
    await validatePlan(state, draft);
  } else if (draft.kind === 'plan_audit') {
    const subject = state.records.find(item => item.record.kind === 'plan' && item.record.record_id === draft.subject_record_id)?.record;
    if (!subject || subject.record_id !== task.plan_id || draft.phase !== task.phase || draft.subject_digest !== digest(subject)) fail('WRONG_AUDIT_SUBJECT', 'Audit must reference the assigned plan and exact digest.');
    if (subject.actor_id === draft.actor_id || findTask(state, subject.task_id).handle === task.handle) fail('ACTOR_ISOLATION', 'Plan author and auditor must use independent contexts.');
  } else if (draft.kind === 'execution') {
    await validateExecution(state, task, draft, output);
  }
  return { record: draft, output };
}

async function submit(options, state) {
  const task = findTask(state, required(options, 'task-id'));
  const draft = await readYaml(required(options, 'file'));
  const { record, output } = await validateSubmission(state, task, draft);
  const existing = state.records.find(item => item.path === output.path);
  if (existing && stableStringify(existing.record) !== stableStringify(record)) fail('RECORD_CONFLICT', 'A different result was already accepted for this assignment.', [], 4);
  if (!trueFlag(options.check)) await writeRecord(state.campaign, output.path, record);
  const accepted = task.outputs.every(item => item.path === output.path || state.records.some(record => record.path === item.path));
  return { submission_status: trueFlag(options.check) ? 'VALIDATED' : 'ACCEPTED', worker_may_finish: !trueFlag(options.check) && accepted, test_verdict: 'NOT_DECIDED', record_id: record.record_id, next_actions: trueFlag(options.check) ? ['SUBMIT'] : accepted ? ['CLOSE_TASK_AFTER_HOST_FINISH'] : ['SUBMIT_REMAINING_OUTPUTS'] };
}

async function status(state) {
  const ready = state.tasks.filter(task => ['PLANNED', 'READY', 'BLOCKED'].includes(task.state) && !eligibility(task, state).length).map(task => task.task_id);
  const blocked = state.tasks.filter(task => ['PLANNED', 'READY', 'BLOCKED'].includes(task.state)).map(task => ({ task_id: task.task_id, reasons: eligibility(task, state) })).filter(task => task.reasons.length);
  return { complete: false, outcome: 'INCOMPLETE', latest_target_id: state.config.final_target_id, counts: { tasks: state.tasks.length, active: state.tasks.filter(active).length, ready: ready.length, blocked: blocked.length }, ready, running: state.tasks.filter(active).map(task => task.task_id), blocked, obligations: state.config.active_plan_id ? [] : [{ type: 'PLAN_REQUIRED' }] };
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
    if (command === 'status') return status(state);
    if (command === 'records') {
      let records = state.records.map(item => item.record);
      for (const field of ['kind', 'record-id', 'case-id', 'round-id']) if (options[field]) records = records.filter(record => record[field.replaceAll('-', '_')] === options[field]);
      if (trueFlag(options.ready)) { const ready = (await status(state)).ready; records = records.filter(record => record.kind === 'task' && ready.includes(record.task_id)); }
      if (options.format && !['json', 'yaml-stream'].includes(options.format)) fail('USAGE', '--format must be json or yaml-stream.', [], 2);
      return options.format === 'yaml-stream' ? { yaml_stream: records.map(record => `---\n${getDependencies().YAML.stringify(record)}`).join('') } : { records };
    }
    fail('USAGE', `Unknown core command ${command}.`, [], 2);
  };
  return ['status', 'records'].includes(command) || (command === 'submit' && trueFlag(options.check)) ? perform() : withController(campaign, perform);
}
