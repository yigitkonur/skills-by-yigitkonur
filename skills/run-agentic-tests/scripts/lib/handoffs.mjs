export function renderHandoff(task) {
  const lines = [
    `# ${task.task_id}: ${task.role}`, '',
    `Actor: ${task.actor_id}. Use a fresh, real isolated host context; never reuse another task's handle.`,
    'Do not spawn workers. Read only your bounded inputs. Save evidence; submit a structured result. Accepted is not PASS.', '',
    '## Assignment', task.requested_action, '',
    `Cases: ${task.case_ids.join(', ') || '(campaign-level)'}`,
    `Target: ${task.target_id || '(not assigned)'}. Spec: ${task.spec_revision || '(not assigned)'}. Round: ${task.round_id || '(not assigned)'}.`, '',
    '## Required inputs', ...task.required_inputs.map(input => `- ${input}`), '',
    '## Assigned outputs', ...task.outputs.map((output, i) => `- Draft: ${task.draft_paths[i]} → ${output.path} (${output.record_id})`), '',
  ];
  if (task.role === 'executor') lines.push('Run the actual E2E scenario. Cover every expectation with saved evidence or an explicit gap. Never submit a final PASS.');
  if (task.role === 'verifier') lines.push('Open saved artifacts and compare each expectation. Do not rerun the test. Do not read other verification records or verdicts; this review is blind. Missing evidence needs a fresh executor.');
  if (task.role === 'scenario-author') lines.push('Write Given/When/Then with expectation IDs into 01-test-case.md and concrete steps into 03-how-to-run.md beside the assigned expectations output. Expected behavior needs an explicit source.');
  if (task.prior_context) {
    const prior = task.prior_context;
    lines.push('', '## Retry context', `Previous failure: ${prior.previous_failure}`, `What changed: ${prior.what_changed}`, `New hypothesis/evidence: ${prior.hypothesis}`, `Do not repeat: ${prior.do_not_repeat.join('; ')}`, `Remaining execution attempts: ${prior.remaining_attempts}`, `Issue: ${prior.issue_url || '(local only)'}`, `PRs: ${(prior.pr_urls || []).join(', ') || '(none)'}`);
  }
  lines.push('', 'Run submit --check first if useful, then submit. Stop only after receipt.worker_may_finish is true. The controller records actual worker termination separately.', '');
  return lines.join('\n');
}
