import { mkdir, readFile, writeFile, rename, rm } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { readCampaign, readRecords, containedPath, withController } from './store.mjs';
import { CliError } from './contracts.mjs';
import { startOwned, inspectOwned, stopOwned } from './process-host.mjs';
import { assessCampaign } from './workflow.mjs';

const templatePath = new URL('../../assets/report-template.html', import.meta.url);
const escape = value => String(value ?? '').replace(/[&<>"']/g, character =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
const json = value => JSON.stringify(value).replace(/[<>&\u2028\u2029]/g,
  character => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
const hash = value => createHash('sha256').update(value).digest('hex');
const display = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
const list = items => items.length ? `<ul>${items.map(item => `<li>${escape(item)}</li>`).join('')}</ul>` : '<p>None.</p>';
function publicData(value) {
  if (Array.isArray(value)) return value.map(publicData);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, publicData(item)]));
  if (typeof value !== 'string') return value;
  return value.replace(/https?:\/\/[^\s<>"']+/g, candidate => {
    try {
      const url = new URL(candidate);
      if (url.username || url.password || [...url.searchParams.keys()].some(key => /token|secret|password|api.?key|authorization|credential|session/i.test(key))) return '[credential URL omitted]';
    } catch { /* Non-URL prose is escaped when rendered. */ }
    return candidate;
  });
}

function containsCredential(body) {
  const text = body.toString('utf8');
  return /-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{20,}|\bsk-[A-Za-z0-9_-]{24,}/.test(text) ||
    /(?:^|[\s"'{,])(?:[\w-]*(?:token|password|secret)|api[_-]?key|authorization)\s*["']?\s*[:=]\s*["']?(?!\[REDACTED\]|<REDACTED>|null\b)[A-Za-z0-9/+_=.-]{8,}/im.test(text) ||
    /https?:\/\/[^\s/]+:[^\s/]+@/i.test(text);
}
function link(url, label = url) {
  try {
    const parsed = new URL(url);
    if (!['https:', 'http:'].includes(parsed.protocol) || parsed.username || parsed.password) throw new Error();
    return `<a href="${escape(parsed.href)}" rel="noopener noreferrer">${escape(label)}</a>`;
  } catch { return escape(label); }
}

function renderRound(round) {
  const evidence = new Map(round.artifacts.map(artifact => [artifact.id, artifact]));
  const rows = round.expectations.map(expectation => {
    const observed = round.observations.find(item => item.expectation_id === expectation.id);
    const reviews = round.reviews.filter(item => item.expectation_id === expectation.id);
    const links = (observed?.evidence_ids || []).map(id => {
      const artifact = evidence.get(id);
      return artifact?.href ? `<a href="${escape(artifact.href)}">${escape(id)} (${escape(artifact.type)})</a>` : escape(`${id} — unavailable`);
    });
    return `<tr><th>${escape(expectation.id)}<p>${escape(expectation.statement)}</p><small>${link(expectation.source.reference)}</small></th>` +
      `<td><pre>${escape(display(observed?.observed ?? 'Not observed'))}</pre>${list((observed?.gaps || []).map(gap => `${gap.requirement_id}: ${gap.reason}`))}</td>` +
      `<td>${reviews.map(review => `<p><strong>${escape(review.verdict)}</strong> — ${escape(review.actor_id)}</p><pre>${escape(display(review.observed))}</pre><p>${escape(review.reason)}</p>`).join('') || 'Awaiting independent verification'}</td>` +
      `<td>${links.join('<br>') || 'No evidence'}</td></tr>`;
  }).join('');
  const previews = round.artifacts.filter(artifact => artifact.image && artifact.href).map(artifact =>
    `<figure><a href="${escape(artifact.href)}"><img src="${escape(artifact.href)}" alt="Evidence ${escape(artifact.id)}" loading="lazy"></a><figcaption>${escape(artifact.id)}</figcaption></figure>`).join('');
  return `<details ${round.current ? 'open' : ''} class="${round.current ? 'current' : 'history'}"><summary>${round.current ? 'Current' : 'Historical'} ${escape(round.round_id)} · ${escape(round.target_id)} · ${escape(round.outcome)}${round.recorded_outcome && round.recorded_outcome !== round.outcome ? ` (sealed ${escape(round.recorded_outcome)})` : ''}</summary>` +
    `<p>Execution ${escape(round.execution_record_id)} · ${escape(round.execution_status)} · source ${escape(round.source || 'not recorded')}</p>` +
    `<p>Verifier records: ${escape(round.verification_record_ids.join(', ') || 'none')}</p>${list(round.gaps)}` +
    `<table><thead><tr><th>Expected and source</th><th>Actual observation and gaps</th><th>Independent review</th><th>Evidence</th></tr></thead><tbody>${rows}</tbody></table>${previews}</details>`;
}

function renderCase(item) {
  return `<article data-case="${escape(item.case_id)}" data-outcome="${escape(item.outcome)}"><h2>${escape(item.case_id)} · ${escape(item.outcome)}</h2>` +
    `<p>Spec ${escape(item.spec_revision || 'unplanned')} · ${item.accepted ? 'Accepted coverage' : 'Outside accepted coverage'}</p>${list(item.gaps)}` +
    item.rounds.map(renderRound).join('') +
    `<h3>Findings and delivery trail</h3>${item.findings.length ? item.findings.map(finding => `<p><strong>${escape(finding.finding_id)}</strong> ${escape(finding.class)} · ${escape(finding.state)} · ${escape(finding.scope)} · ${escape(finding.attempts)} attempts</p><p>${escape(finding.summary)}</p><p>${[finding.issue_url, ...(finding.pr_urls || [])].filter(Boolean).map(url => link(url)).join(' · ')}</p>`).join('') : '<p>None recorded.</p>'}</article>`;
}

async function build(campaign) {
  const campaignRecord = await readCampaign(campaign);
  const records = await readRecords(campaign);
  const assessment = await assessCampaign(campaign, records);
  const assessedCases = new Map(assessment.cases.map(item => [item.case_id, item]));
  const all = records.map(item => item.record);
  const byId = new Map(all.map(record => [record.record_id, record]));
  const gaps = assessment.obligations.map(item => [item.type, item.case_id, item.round_id, item.target_id,
    item.finding_id, item.task_id, item.message].filter(Boolean).join(': '));
  const plan = byId.get(campaignRecord.active_plan_id);
  if (!plan) gaps.push('No accepted plan; coverage is not established.');
  if (!campaignRecord.final_target_id) gaps.push('No final target selected.');
  await mkdir(containedPath(campaign, 'report'), { recursive: true });
  await mkdir(containedPath(campaign, 'report/artifacts'), { recursive: true });
  const files = new Map();
  const accepted = new Map((plan?.cases || []).map(item => [item.case_id, item]));
  const caseIds = [...new Set([...accepted.keys(), ...all.filter(record => record.case_id).map(record => record.case_id)])].sort();
  const cases = [];
  for (const case_id of caseIds) {
    const assignment = accepted.get(case_id);
    const caseGaps = [];
    const rounds = [];
    const executions = records.filter(({ record }) => record.kind === 'execution' && record.case_id === case_id)
      .sort((a, b) => a.record.round_id.localeCompare(b.record.round_id, 'en', { numeric: true }) || a.record.created_at.localeCompare(b.record.created_at));
    for (const { record: execution, path: executionPath } of executions) {
      const verdict = all.find(record => record.kind === 'verdict' && record.execution_record_id === execution.record_id);
      const spec = all.find(record => record.kind === 'expectations' && record.case_id === case_id && record.spec_revision === execution.spec_revision);
      const verifications = verdict ? verdict.verification_record_ids.map(id => byId.get(id)).filter(Boolean) :
        all.filter(record => record.kind === 'verification' && record.execution_record_id === execution.record_id);
      const roundGaps = [];
      let invalidEvidence = false;
      const invalid = message => { invalidEvidence = true; roundGaps.push(message); };
      const matches = record => ['campaign_id', 'case_id', 'spec_revision', 'round_id', 'target_id'].every(key => record?.[key] === execution[key]);
      if (verdict && !matches(verdict)) invalid('Sealed verdict target/source provenance does not match its execution.');
      if (verdict && verifications.length !== verdict.verification_record_ids.length) invalid('A sealed verifier record is missing.');
      for (const verification of verifications) {
        if (verification.kind !== 'verification' || !matches(verification) || verification.execution_record_id !== execution.record_id) invalid('Verifier target/source provenance does not match the execution.');
        if (verification.actor_id === execution.actor_id || verification.actor_id === spec?.author_actor_id) invalid('Independent verifier identity is invalid.');
      }
      if (spec?.author_actor_id === execution.actor_id) invalid('Scenario author and executor are not independent.');
      for (const observation of [...execution.observations, ...verifications.flatMap(record => record.reviews || [])]) {
        for (const evidence_id of observation.evidence_ids) {
          if (!execution.evidence.some(item => item.id === evidence_id && item.expectation_ids.includes(observation.expectation_id))) invalid(`${evidence_id}: Missing evidence reference for ${observation.expectation_id}.`);
        }
      }
      const artifacts = [];
      for (const artifact of execution.evidence) {
        try {
          if (!artifact.path.startsWith(`${path.posix.dirname(executionPath)}/evidences/`)) throw new Error('Evidence is outside its assigned round.');
          if (artifact.path.split('/').some(component => component.startsWith('.')) || /^(?:credentials?|secrets?)(?:\.|$)/i.test(path.basename(artifact.path))) throw new Error('Credential or hidden evidence files cannot be published.');
          const body = await readFile(containedPath(campaign, artifact.path));
          if (containsCredential(body)) throw new Error('Possible plaintext credentials in evidence; redact before submission.');
          const digest = hash(body);
          if (artifact.sha256 !== digest || (artifact.size !== undefined && artifact.size !== body.length)) throw new Error('Evidence hash or size changed after submission.');
          if (verdict && !verdict.evidence_hashes.some(item => item.path === artifact.path && item.sha256 === digest)) throw new Error('Evidence hash does not match the sealed verdict.');
          for (const verification of verifications) {
            const inspected = verification.inspected_evidence.find(item => item.id === artifact.id);
            if (verification.reviews.some(review => review.evidence_ids.includes(artifact.id)) && inspected?.sha256 !== digest) throw new Error('Evidence hash does not match the verifier inspection.');
          }
          const extension = path.extname(artifact.path).slice(1).toLowerCase();
          const image = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(extension);
          const safeExtension = image || ['json', 'log', 'txt', 'csv'].includes(extension) ? extension : 'txt';
          const content_type = image ? `image/${extension === 'jpg' ? 'jpeg' : extension}` :
            (extension === 'json' ? 'application/json; charset=utf-8' : 'text/plain; charset=utf-8');
          const href = `artifacts/${digest}.${safeExtension}`;
          await writeFile(containedPath(campaign, `report/${href}`), body, { mode: 0o600 });
          files.set(href, { path: href, sha256: digest, content_type, download: !image });
          artifacts.push({ id: artifact.id, type: artifact.type, source: artifact.source, href, image });
        } catch (error) { invalidEvidence = true; roundGaps.push(`${artifact.id}: ${error.code === 'ENOENT' ? 'Missing evidence file.' : error.message}`); artifacts.push({ id: artifact.id, type: artifact.type }); }
      }
      if (!verdict) roundGaps.push('Independent verdict is pending.');
      if (!spec) roundGaps.push('Expectation specification is missing.');
      const environment = all.find(record => record.kind === 'environment' && record.target_id === execution.target_id);
      rounds.push({ round_id: execution.round_id, target_id: execution.target_id, spec_revision: execution.spec_revision,
        execution_record_id: execution.record_id, execution_status: execution.execution_status,
        verification_record_ids: verifications.map(record => record.record_id), expectations: spec?.expectations || [],
        observations: execution.observations, reviews: verifications.flatMap(record => record.reviews.map(review => ({ ...review, actor_id: record.actor_id }))),
        source: environment?.source.revision, artifacts, gaps: roundGaps, outcome: invalidEvidence ? 'INVALID_EVIDENCE' : verdict?.outcome || (execution.execution_status === 'NOT_RUN' ? 'NOT_RUN' : 'NOT_ASSESSED') });
    }
    const assessed = assessedCases.get(case_id);
    const current = rounds.find(round => round.execution_record_id === assessed?.execution_record_id);
    if (current) {
      current.current = true;
      current.recorded_outcome = current.outcome;
      current.gaps.push(...(assessed.blockers || []).map(item => [item.type, item.message].filter(Boolean).join(': ')));
      if (current.outcome !== 'INVALID_EVIDENCE') {
        if ((assessed.blockers || []).some(item => /EVIDENCE_CHANGED|MISSING_ARTIFACT|UNSAFE_ARTIFACT|UNSAFE_PATH|RECORDS_CHANGED|TARGET_DRIFT|SPEC_CHANGED|MISSING_PROVENANCE/.test(item.type))) current.outcome = 'INVALID_EVIDENCE';
        else if (!assessed.proof_valid && assessed.outcome === 'PASS') current.outcome = 'INCONCLUSIVE';
        else current.outcome = assessed.outcome === 'PENDING_VERIFICATION' ? 'NOT_ASSESSED' : assessed.outcome;
      }
    }
    if (assignment && !current) caseGaps.push('No execution and independent proof on the final target.');
    const outcome = current?.outcome || 'NOT_RUN';
    const findings = all.filter(record => record.kind === 'finding' && record.case_ids.includes(case_id));
    cases.push({ case_id, spec_revision: assignment?.spec_revision, accepted: Boolean(assignment), outcome, rounds, findings, gaps: caseGaps });
  }
  const counts = { PASS: 0, FAIL: 0, INCONCLUSIVE: 0, NOT_RUN: 0, NOT_ASSESSED: 0, INVALID_EVIDENCE: 0 };
  for (const item of cases.filter(item => item.accepted)) counts[item.outcome]++;
  for (const item of cases.filter(item => item.accepted)) {
    gaps.push(...item.gaps.map(gap => `${item.case_id}: ${gap}`));
    gaps.push(...item.rounds.filter(round => round.current).flatMap(round => round.gaps.map(gap => `${item.case_id} ${round.round_id}: ${gap}`)));
  }
  if (assessment.obligations.some(item => item.type === 'CLOSURE_AUDIT_REQUIRED')) gaps.push('Independent closure audit is pending for the current proof digest.');
  if (!accepted.size) gaps.push('No accepted cases have final-target proof.');
  const overall = counts.FAIL ? 'FAIL' : (assessment.complete && accepted.size && counts.PASS === accepted.size && !gaps.length ? 'PASS' : 'INCOMPLETE');
  const summary = publicData({ overall, total: accepted.size, counts, gaps });
  const model = publicData({ campaign: campaignRecord.slug, final_target_id: campaignRecord.final_target_id, summary, cases });
  const html = (await readFile(templatePath, 'utf8'))
    .replace('{{TITLE}}', escape(campaignRecord.slug))
    .replace('{{SUMMARY}}', `<strong class="status">${escape(summary.overall)}</strong><p>${summary.total} accepted cases</p>`)
    .replace('{{GAPS}}', list(summary.gaps))
    .replace('{{CASES}}', (model.cases.map(renderCase).join('') || '<p>No case observations are available.</p>') +
      `<section><h2>Out-of-scope coverage</h2>${list(publicData((plan?.scope.out_of_scope || []).map(item => `${item.item}: ${item.reason}`)))}</section>`)
    .replace('{{DATA}}', json(model));
  const temporary = containedPath(campaign, `report/index.${randomUUID()}.tmp`);
  await writeFile(temporary, html, { mode: 0o600 });
  await rename(temporary, containedPath(campaign, 'report/index.html'));
  await writeFile(containedPath(campaign, '.report-bundle.runtime.json'), JSON.stringify({ files: [{
    path: 'index.html', sha256: createHash('sha256').update(html).digest('hex'), content_type: 'text/html; charset=utf-8',
  }, ...files.values()] }), { mode: 0o600 });
  return { report_path: 'report/index.html', summary };
}

export async function run(command, options = {}) {
  if (typeof options.campaign !== 'string') throw new CliError('INVALID_REPORT', '--campaign is required.');
  const campaign = path.resolve(options.campaign);
  if (command === 'report build') return withController(campaign, () => build(campaign));
  if (command === 'report serve' || command === 'report stop') {
    await readCampaign(campaign);
    const manifestPath = containedPath(campaign, '.report-server.runtime.json');
    let existing;
    try { existing = JSON.parse(await readFile(manifestPath, 'utf8')); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (existing && (existing.mode !== 'report' || existing.root !== containedPath(campaign, 'report') || existing.manifest_path !== manifestPath)) {
      throw new CliError('PROCESS_OWNERSHIP_MISMATCH', 'This handle does not belong to the campaign report server.', 4);
    }
    if (command === 'report stop') {
      if (!existing) return { alive: false, ownership: 'EXITED' };
      const state = await stopOwned(existing, manifestPath);
      if (state.ownership === 'MISMATCH') throw new CliError('PROCESS_OWNERSHIP_MISMATCH', 'Report server ownership changed; no process was signalled.', 4);
      return state;
    }
    const port = options.port === undefined ? 0 : Number(options.port);
    if (!Number.isInteger(port) || port < 0 || port > 65535) throw new CliError('INVALID_REPORT', '--port must be 0..65535.', 2);
    if (existing) {
      const state = await inspectOwned(existing, manifestPath);
      if (state.ownership === 'OWNED') return { url: existing.url, process: { pid: existing.pid, start_token: existing.start_token }, ...state };
      if (state.ownership === 'MISMATCH') throw new CliError('PROCESS_OWNERSHIP_MISMATCH', 'Report server ownership changed; its handle was preserved.', 4);
      await rm(manifestPath);
    }
    const bundlePath = containedPath(campaign, '.report-bundle.runtime.json');
    try { await readFile(bundlePath); }
    catch { throw new CliError('REPORT_NOT_BUILT', 'Run report build before report serve.', 3); }
    const handle = await startOwned(manifestPath, {
      mode: 'report', root: containedPath(campaign, 'report'), bundle_path: bundlePath, port,
      stdout: containedPath(campaign, '.report-stdout.log'), stderr: containedPath(campaign, '.report-stderr.log'),
    });
    return { url: handle.url, process: { pid: handle.pid, start_token: handle.start_token }, alive: true, ownership: 'OWNED' };
  }
  throw new CliError('UNKNOWN_COMMAND', `Unsupported report command: ${command}`, 2);
}
