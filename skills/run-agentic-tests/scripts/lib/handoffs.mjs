import path from 'node:path';
import { fileURLToPath } from 'node:url';
const packageRoot = fileURLToPath(new URL('../../', import.meta.url));
export const shellQuote = value => "'" + String(value).replaceAll("'", "'\"'\"'") + "'";
export function renderHandoff(task, { campaign = '', project = '' } = {}) {
  const cli = path.join(packageRoot, 'scripts/agentic-tests.mjs');
  const command = name => `node ${shellQuote(cli)} ${name} --campaign ${shellQuote(campaign)}`;
  const absolute = relative => path.join(campaign, relative);
  const lines = [
    `# ${task.task_id}: ${task.role}`, '',
    `Actor: ${task.actor_id}. Use a fresh, real isolated host context; never reuse another task's handle.`,
    'Do not spawn workers. Read only your bounded inputs. Save evidence; submit a structured result. Accepted is not PASS.', '',
    `CLI: ${cli}`, `Campaign: ${campaign}`, `Project: ${project}`, '',
    '## Read first', `- ${path.join(packageRoot, 'references/roles', task.role + '.md')}`, `- ${path.join(packageRoot, 'references/records-and-states.md')}`, `- ${path.join(packageRoot, 'references/cli-and-yq.md')}`, `- ${absolute(`tasks/${task.task_id}/00-task.record.yaml`)}`, '',
    '## Assignment', task.requested_action, '',
    `Cases: ${task.case_ids.join(', ') || '(campaign-level)'}`,
    `Target: ${task.target_id || '(not assigned)'}. Spec: ${task.spec_revision || '(not assigned)'}. Round: ${task.round_id || '(not assigned)'}.`, '',
    '## Required inputs', ...task.required_inputs.map(input => `- ${typeof input === 'string' ? absolute(input) : path.join(project, input.path)} (read only)`), '',
    '## Assigned outputs', ...task.outputs.map((output, i) => `- Draft: ${absolute(task.draft_paths[i])} → ${absolute(output.path)} (${output.record_id})`), '',
  ];
  lines.push('## Write scope', ...task.draft_paths.map(p => `- ${absolute(p)}`), ...task.outputs.filter(o => o.kind === 'execution').map(o => `- ${absolute(path.join(path.dirname(o.path), 'evidences'))}`), ...task.outputs.filter(o => o.kind === 'expectations').flatMap(o => ['01-test-case.md', '03-how-to-run.md'].map(p => `- ${absolute(path.join(path.dirname(o.path), p))}`)), 'The controller alone publishes canonical record files.', '', '## Resources', ...task.resources.map(r => `- ${r.name}: ${r.mode}`));
  if (task.group) lines.push('', '## Grouped execution', `Shared setup: ${task.group.shared_setup}`, `Reset between cases: ${task.group.reset}`, 'Submit each assigned output separately; each case keeps independent evidence and verdict.');
  lines.push('', '## Exact completion commands', ...task.draft_paths.flatMap(p => task.role === 'environment-operator' ? [`${command('runtime start')} --file ${shellQuote(absolute(p))}`] : [`${command('submit')} --task-id ${shellQuote(task.task_id)} --file ${shellQuote(absolute(p))} --check`, `${command('submit')} --task-id ${shellQuote(task.task_id)} --file ${shellQuote(absolute(p))}`]));
  if (task.role === 'executor') lines.push('Run the actual E2E scenario. Cover every expectation with saved evidence or an explicit gap. Never submit a final PASS.');
  if (task.role === 'verifier') lines.push('Open saved artifacts and compare each expectation. Do not rerun the test. Do not read other verification records or verdicts; this review is blind. Missing evidence needs a fresh executor.');
  if (task.role === 'scenario-author') lines.push('Write Given/When/Then with expectation IDs into 01-test-case.md and concrete steps into 03-how-to-run.md beside the assigned expectations output. Expected behavior needs an explicit source.');
  if (task.prior_context) {
    const prior = task.prior_context;
    lines.push('', '## Retry context', `Previous failure: ${prior.previous_failure}`, `What changed: ${prior.what_changed}`, `New hypothesis/evidence: ${prior.hypothesis}`, `Do not repeat: ${prior.do_not_repeat.join('; ')}`, `Remaining execution attempts: ${prior.remaining_attempts}`, `Issue: ${prior.issue_url || '(local only)'}`, `PRs: ${(prior.pr_urls || []).join(', ') || '(none)'}`);
  }
  if (task.role === 'environment-operator') {
    lines.push('', 'Run runtime start with the assigned environment draft. Preserve its record_id, task_id, actor_id, and target_id. Runtime publication writes the canonical environment result. Return its path and READY or FAILED status to the controller; the controller closes the task after confirmed worker termination.');
  } else {
    lines.push('', 'Run submit --check first if useful, then submit. Finish the assigned work after receipt.worker_may_finish is true; the controller records confirmed worker termination separately. Accepted means a valid report, not a passing test.');
  }
  const unavailable = task.role === 'environment-operator'
    ? 'Report unavailable work using the runtime command result and its saved diagnostics.'
    : 'Report unavailable work honestly: execution uses PARTIAL or NOT_RUN; verification uses INCONCLUSIVE or NOT_ASSESSED; other structured roles may use result_status: BLOCKED with blocker, summary, and artifacts.';
  lines.push('', `${unavailable} If a valid report is impossible, retain the draft and artifacts, report the concrete blocker to the controller, and let it interrupt the task and confirm host termination. Never invent missing URLs, commits, evidence, or outcomes.`, '');
  return lines.join('\n');
}
