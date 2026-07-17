#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const SSH_OPTIONS = [
  '-o', 'BatchMode=yes',
  '-o', 'ConnectTimeout=10',
  '-o', 'ServerAliveInterval=15',
  '-o', 'ServerAliveCountMax=4',
];

const HELP = `Usage: run-martool-cli-audit.mjs [options]

Run martool's generated-command and platform-command black-box audits and
write raw evidence plus one combined JSON report.

Options:
  --target <source|coolify>       Audit target (default: source)
  --repo <path>                   Martool checkout for source mode (default: cwd)
  --ssh-host <host>               SSH host or alias for Coolify mode
  --coolify-project <name>        Coolify project label (default: martool)
  --service <name>                Compose service label (default: martool)
  --container <id-or-name>        Override Coolify label discovery
  --matrix <all|generated|platform>
                                  Matrix selection (default: all)
  --command <exact-name>          Diagnostic scope; never full release proof
  --report-dir <path>             Evidence directory (default: timestamped cwd)
  --no-build                      Reuse source dist/cli/main.js without building
  -h, --help                      Show this help

Examples:
  node scripts/run-martool-cli-audit.mjs --target source --repo /src/martool
  node scripts/run-martool-cli-audit.mjs --target coolify --ssh-host hetzner
  node scripts/run-martool-cli-audit.mjs --target coolify --ssh-host hetzner \
    --command "keywords research"
`;

const DISCOVER_REMOTE = String.raw`set -eu
project=$1
service=$2
override=$3
[ "$override" = "-" ] && override=

if [ -n "$override" ]; then
  cid=$(docker inspect --type container --format '{{.Id}}' "$override" 2>/dev/null) || {
    echo "container override not found: $override" >&2
    exit 21
  }
else
  ids=$(docker ps -q --no-trunc \
    --filter "label=coolify.projectName=$project" \
    --filter "label=com.docker.compose.service=$service")
  set -- $ids
  if [ "$#" -eq 0 ]; then
    echo "no running container matched project=$project service=$service" >&2
    exit 21
  fi
  if [ "$#" -ne 1 ]; then
    echo "multiple running containers matched project=$project service=$service" >&2
    exit 22
  fi
  cid=$1
fi

docker inspect --type container --format \
  '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.Image}}|{{.State.Running}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
  "$cid"
`;

const RUN_REMOTE = String.raw`set -eu
cid=$1
action=$2
filter=$3
[ "$filter" = "-" ] && filter=

case "$action" in
  preflight)
    docker exec "$cid" sh -c \
      'test -f dist/cli/main.js && test -f scripts/audit-martool-generated-flags.mjs && test -f scripts/audit-martool-platform-flags.mjs'
    ;;
  version)
    docker exec "$cid" node dist/cli/main.js version --json
    ;;
  usage)
    docker exec "$cid" node dist/cli/main.js usage --json
    ;;
  generated)
    if [ -n "$filter" ]; then
      docker exec -e "MARTOOL_FLAG_AUDIT_COMMAND=$filter" "$cid" \
        node scripts/audit-martool-generated-flags.mjs
    else
      docker exec "$cid" node scripts/audit-martool-generated-flags.mjs
    fi
    ;;
  platform)
    if [ -n "$filter" ]; then
      docker exec \
        -e "MARTOOL_PLATFORM_AUDIT_COMMAND=$filter" \
        -e MARTOOL_PLATFORM_AUDIT_ALLOW_PARTIAL=1 \
        "$cid" node scripts/audit-martool-platform-flags.mjs
    else
      docker exec "$cid" node scripts/audit-martool-platform-flags.mjs
    fi
    ;;
  *)
    echo "unknown remote action: $action" >&2
    exit 23
    ;;
esac
`;

class CliError extends Error {
  constructor(message, exitCode = 2, details = undefined) {
    super(message);
    this.name = 'CliError';
    this.exitCode = exitCode;
    this.details = details;
  }
}

function valueAfter(argv, index, option) {
  const value = argv[index + 1];
  if (value === undefined || value.startsWith('--')) {
    throw new CliError(`${option} requires a value.`);
  }
  return value;
}

function safeToken(value, label, pattern) {
  if (!pattern.test(value)) throw new CliError(`${label} contains unsupported characters.`);
  return value;
}

export function encodeRemoteValue(value) {
  return value === null || value === '' ? '-' : value;
}

export function parseArgs(argv, cwd = process.cwd()) {
  const timestamp = new Date().toISOString().replaceAll(':', '-').replaceAll('.', '-');
  const options = {
    target: 'source',
    repo: cwd,
    sshHost: null,
    coolifyProject: 'martool',
    service: 'martool',
    container: null,
    matrix: 'all',
    command: null,
    reportDir: resolve(cwd, `martool-cli-audit-${timestamp}`),
    build: true,
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const option = argv[index];
    if (option === '--help' || option === '-h') options.help = true;
    else if (option === '--no-build') options.build = false;
    else if (option === '--target') options.target = valueAfter(argv, index++, option);
    else if (option === '--repo') options.repo = valueAfter(argv, index++, option);
    else if (option === '--ssh-host') options.sshHost = valueAfter(argv, index++, option);
    else if (option === '--coolify-project') options.coolifyProject = valueAfter(argv, index++, option);
    else if (option === '--service') options.service = valueAfter(argv, index++, option);
    else if (option === '--container') options.container = valueAfter(argv, index++, option);
    else if (option === '--matrix') options.matrix = valueAfter(argv, index++, option);
    else if (option === '--command') options.command = valueAfter(argv, index++, option);
    else if (option === '--report-dir') options.reportDir = valueAfter(argv, index++, option);
    else throw new CliError(`Unknown option: ${option}`);
  }

  if (!['source', 'coolify'].includes(options.target)) {
    throw new CliError('--target must be source or coolify.');
  }
  if (!['all', 'generated', 'platform'].includes(options.matrix)) {
    throw new CliError('--matrix must be all, generated, or platform.');
  }
  if (options.command !== null && options.command.trim().length === 0) {
    throw new CliError('--command cannot be empty.');
  }
  if (options.target === 'coolify' && options.sshHost === null) {
    throw new CliError('--ssh-host is required for --target coolify.');
  }
  if (options.target === 'coolify' && options.build === false) {
    throw new CliError('--no-build applies only to --target source.');
  }

  if (options.sshHost !== null) {
    options.sshHost = safeToken(options.sshHost, 'SSH host', /^[A-Za-z0-9_.:@-]+$/u);
  }
  options.coolifyProject = safeToken(options.coolifyProject, 'Coolify project', /^[A-Za-z0-9_.-]+$/u);
  options.service = safeToken(options.service, 'service', /^[A-Za-z0-9_.-]+$/u);
  if (options.container !== null) {
    options.container = safeToken(options.container, 'container', /^[A-Za-z0-9_.-]+$/u);
  }
  if (options.command !== null) {
    options.command = safeToken(options.command, 'command filter', /^[A-Za-z0-9_. -]+$/u);
  }
  options.repo = resolve(cwd, options.repo);
  options.reportDir = resolve(cwd, options.reportDir);
  return options;
}

function progress(message) {
  process.stderr.write(`[test-martool-cli] ${message}\n`);
}

function runProcess(command, args, options = {}) {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: options.env ?? process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      if (options.stdoutToStderr === true) process.stderr.write(chunk);
      else stdout += chunk;
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
      if (options.forwardStderr !== false) process.stderr.write(chunk);
    });
    child.on('error', rejectPromise);
    child.on('close', (code, signal) => resolvePromise({ code, signal, stdout, stderr }));
    if (options.input !== undefined) child.stdin.end(options.input);
    else child.stdin.end();
  });
}

async function runRequired(command, args, options, label) {
  let result;
  try {
    result = await runProcess(command, args, options);
  } catch (error) {
    throw new CliError(`${label} could not start: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (result.code !== 0) {
    throw new CliError(`${label} failed with exit ${String(result.code)}.`, 2, {
      signal: result.signal,
      stderr: result.stderr.trim() || null,
    });
  }
  return result;
}

function parseJson(source, label) {
  try {
    return JSON.parse(source.trim());
  } catch (error) {
    throw new CliError(`${label} did not emit valid JSON: ${error instanceof Error ? error.message : String(error)}`, 1);
  }
}

async function writeAtomic(path, contents) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary, contents, { flag: 'wx' });
    await rename(temporary, path);
  } finally {
    await rm(temporary, { force: true });
  }
}

function sha256(contents) {
  return createHash('sha256').update(contents).digest('hex');
}

function countList(value) {
  return Array.isArray(value) ? value.length : null;
}

export function validateGeneratedReport(report) {
  const failures = [];
  if (report?.schema_version !== '1') failures.push('schema_version must be 1');
  if (report?.audit !== 'martool-generated-flags') failures.push('unexpected audit name');
  if (report?.totals?.fail !== 0) failures.push(`failed variants: ${String(report?.totals?.fail)}`);
  if (report?.totals?.baseline_fail !== 0) failures.push(`failed baselines: ${String(report?.totals?.baseline_fail)}`);
  if (report?.coverage?.complete !== true) failures.push('coverage is incomplete');
  if (countList(report?.coverage?.missing_cases) !== 0) failures.push('coverage has missing cases');
  if (countList(report?.coverage?.unexpected_cases) !== 0) failures.push('coverage has unexpected cases');
  if (countList(report?.coverage?.duplicate_plan_ids) !== 0) failures.push('coverage has duplicate plan IDs');
  if (countList(report?.coverage?.duplicate_completed_ids) !== 0) failures.push('coverage has duplicate completed IDs');
  return failures;
}

export function validatePlatformReport(report, { diagnostic = false } = {}) {
  const failures = [];
  if (report?.schema_version !== '1') failures.push('schema_version must be 1');
  if (report?.audit !== 'martool-platform-flags') failures.push('unexpected audit name');
  if (report?.totals?.fail !== 0) failures.push(`failed variants: ${String(report?.totals?.fail)}`);
  if (!(Number(report?.totals?.attempted) > 0)) failures.push('no platform cases were attempted');
  if (report?.safety?.provider_calls !== 0) failures.push(`provider calls: ${String(report?.safety?.provider_calls)}`);
  if (report?.safety?.paid_provider_calls !== 0) failures.push(`paid provider calls: ${String(report?.safety?.paid_provider_calls)}`);
  if (countList(report?.manifest?.duplicate_commands) !== 0) failures.push('manifest has duplicate commands');
  if (countList(report?.manifest?.duplicate_flags) !== 0) failures.push('manifest has duplicate flags');
  if (countList(report?.coverage?.unexpected_cases) !== 0) failures.push('coverage has unexpected cases');
  if (countList(report?.coverage?.duplicate_plan_ids) !== 0) failures.push('coverage has duplicate plan IDs');
  if (!diagnostic) {
    if (countList(report?.coverage?.missing_cases) !== 0) failures.push('coverage has missing cases');
    if (countList(report?.coverage?.uncovered_flags) !== 0) failures.push('coverage has uncovered flags');
    if (countList(report?.coverage?.uncovered_positionals) !== 0) failures.push('coverage has uncovered positionals');
    if (report?.totals?.reachable_commands !== report?.totals?.total_commands) {
      failures.push('not every platform command was reachable');
    }
  }
  return failures;
}

export function parseContainerLine(source) {
  const line = source.trim();
  const fields = line.split('|');
  if (fields.length !== 6 || fields.some((field) => field.length === 0)) {
    throw new CliError('Coolify discovery returned an invalid container record.');
  }
  const [id, rawName, imageRef, imageId, running, health] = fields;
  if (running !== 'true') throw new CliError(`Container ${rawName} is not running.`);
  if (health !== 'healthy') throw new CliError(`Container ${rawName} is not healthy (health=${health}).`);
  return { id, name: rawName.replace(/^\//u, ''), image_ref: imageRef, image_id: imageId, health };
}

async function runSsh(host, remoteArgs, script, label) {
  return runRequired(
    'ssh',
    [...SSH_OPTIONS, '--', host, 'sh', '-s', '--', ...remoteArgs],
    { input: script },
    label,
  );
}

async function discoverContainer(options, override = options.container ?? '') {
  const result = await runSsh(
    options.sshHost,
    [options.coolifyProject, options.service, encodeRemoteValue(override)],
    DISCOVER_REMOTE,
    'Coolify container discovery',
  );
  return parseContainerLine(result.stdout);
}

async function runRemoteAction(options, containerId, action) {
  return runRequired(
    'ssh',
    [...SSH_OPTIONS, '--', options.sshHost, 'sh', '-s', '--', containerId, action, encodeRemoteValue(options.command)],
    { input: RUN_REMOTE },
    `remote ${action}`,
  );
}

async function readSourceTarget(options) {
  const packagePath = join(options.repo, 'package.json');
  let packageJson;
  try {
    packageJson = JSON.parse(await readFile(packagePath, 'utf8'));
  } catch (error) {
    throw new CliError(`Could not read ${packagePath}: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (packageJson.name !== 'martool') throw new CliError(`${options.repo} is not a martool checkout.`);

  if (options.build) {
    progress('building the source checkout');
    await runRequired('pnpm', ['build'], { cwd: options.repo, stdoutToStderr: true }, 'pnpm build');
  }

  for (const relativePath of [
    'dist/cli/main.js',
    'scripts/audit-martool-generated-flags.mjs',
    'scripts/audit-martool-platform-flags.mjs',
  ]) {
    try {
      await readFile(join(options.repo, relativePath));
    } catch {
      throw new CliError(`Required martool file is missing: ${relativePath}`);
    }
  }

  const git = await runProcess('git', ['-C', options.repo, 'rev-parse', 'HEAD'], { forwardStderr: false }).catch(() => null);
  return {
    kind: 'source',
    repo: options.repo,
    binary: join(options.repo, 'dist/cli/main.js'),
    git_commit: git?.code === 0 ? git.stdout.trim() : null,
  };
}

async function readTarget(options) {
  if (options.target === 'source') {
    const target = await readSourceTarget(options);
    const version = await runRequired('node', [target.binary, 'version', '--json'], { cwd: options.repo }, 'martool version');
    const usage = await runRequired('node', [target.binary, 'usage', '--json'], { cwd: options.repo }, 'martool usage');
    return { target, version: parseJson(version.stdout, 'martool version'), usage: parseJson(usage.stdout, 'martool usage') };
  }

  const container = await discoverContainer(options);
  progress(`pinned ${container.name} (${container.image_id})`);
  await runRemoteAction(options, container.id, 'preflight');
  const version = await runRemoteAction(options, container.id, 'version');
  const usage = await runRemoteAction(options, container.id, 'usage');
  return {
    target: {
      kind: 'coolify',
      ssh_host: options.sshHost,
      coolify_project: options.coolifyProject,
      service: options.service,
      container,
    },
    version: parseJson(version.stdout, 'remote martool version'),
    usage: parseJson(usage.stdout, 'remote martool usage'),
  };
}

function manifestNames(usage, key) {
  const entries = usage?.[key];
  if (!Array.isArray(entries)) throw new CliError(`martool usage is missing ${key}.`);
  const names = entries.map((entry) => entry?.name).filter((name) => typeof name === 'string');
  if (names.length !== entries.length) throw new CliError(`martool usage has invalid ${key} entries.`);
  return names;
}

function chooseMatrices(options, usage) {
  const requested = options.matrix === 'all' ? ['generated', 'platform'] : [options.matrix];
  if (options.command === null) return requested;
  const available = {
    generated: new Set(manifestNames(usage, 'commands')),
    platform: new Set(manifestNames(usage, 'platform_commands')),
  };
  const selected = requested.filter((matrix) => available[matrix].has(options.command));
  if (selected.length === 0) {
    throw new CliError(`Command filter did not match the selected manifest: ${options.command}`);
  }
  return selected;
}

async function executeAudit(options, context, matrix, reportDir) {
  progress(`running ${matrix} matrix${options.command === null ? '' : ` for ${options.command}`}`);
  let result;
  if (options.target === 'coolify') {
    result = await runProcess(
      'ssh',
      [...SSH_OPTIONS, '--', options.sshHost, 'sh', '-s', '--', context.target.container.id, matrix, encodeRemoteValue(options.command)],
      { input: RUN_REMOTE },
    ).catch((error) => ({ code: null, signal: null, stdout: '', stderr: String(error) }));
  } else {
    const script = matrix === 'generated'
      ? 'scripts/audit-martool-generated-flags.mjs'
      : 'scripts/audit-martool-platform-flags.mjs';
    const env = { ...process.env, MARTOOL_BIN: context.target.binary };
    if (options.command !== null && matrix === 'generated') env.MARTOOL_FLAG_AUDIT_COMMAND = options.command;
    if (options.command !== null && matrix === 'platform') {
      env.MARTOOL_PLATFORM_AUDIT_COMMAND = options.command;
      env.MARTOOL_PLATFORM_AUDIT_ALLOW_PARTIAL = '1';
    }
    result = await runProcess('node', [script], { cwd: options.repo, env })
      .catch((error) => ({ code: null, signal: null, stdout: '', stderr: String(error) }));
  }

  const rawName = `${matrix}-flags.json`;
  const rawPath = join(reportDir, rawName);
  const failures = [];
  let report = null;
  if (result.stdout.trim().length === 0) failures.push('audit emitted no JSON report');
  else {
    try {
      report = JSON.parse(result.stdout.trim());
      await writeAtomic(rawPath, `${JSON.stringify(report)}\n`);
    } catch (error) {
      failures.push(`invalid JSON report: ${error instanceof Error ? error.message : String(error)}`);
      await writeAtomic(join(reportDir, `${matrix}-stdout.txt`), result.stdout);
    }
  }
  if (result.code !== 0) failures.push(`audit process exited ${String(result.code)}`);
  if (report !== null) {
    failures.push(...(matrix === 'generated'
      ? validateGeneratedReport(report)
      : validatePlatformReport(report, { diagnostic: options.command !== null })));
  }

  const contents = report === null ? null : `${JSON.stringify(report)}\n`;
  const coverage = report?.coverage;
  return {
    status: failures.length === 0 ? 'pass' : 'fail',
    exit_code: result.code,
    report_file: report === null ? null : rawName,
    sha256: contents === null ? null : sha256(contents),
    totals: report?.totals ?? null,
    coverage: coverage === undefined ? null : {
      complete: matrix === 'generated' ? coverage.complete === true : countList(coverage.missing_cases) === 0,
      planned: coverage.planned_cases ?? report?.totals?.eligible_variants ?? null,
      attempted: coverage.attempted_cases ?? report?.totals?.completed_variants ?? null,
      missing: countList(coverage.missing_cases),
      unexpected: countList(coverage.unexpected_cases),
      uncovered_flags: countList(coverage.uncovered_flags),
      uncovered_positionals: countList(coverage.uncovered_positionals),
    },
    safety: matrix === 'platform' ? report?.safety ?? null : {
      provider_mode: 'sandbox, dry-run, read-only test environment',
    },
    failures,
    stderr_tail: failures.length === 0 ? null : result.stderr.trim().split('\n').slice(-20),
  };
}

function publicVersion(version) {
  const row = version?.result?.data?.[0];
  return row !== undefined ? {
    version: row.version ?? null,
    git_commit: row.git_commit ?? null,
    engine_version: row.engine_version ?? null,
    node_version: row.node_version ?? null,
    schema_version: row.schema_version ?? null,
  } : version;
}

async function execute(options) {
  const startedAt = new Date();
  await mkdir(options.reportDir, { recursive: true });
  const context = await readTarget(options);
  const generatedNames = manifestNames(context.usage, 'commands');
  const platformNames = manifestNames(context.usage, 'platform_commands');
  const matrices = chooseMatrices(options, context.usage);
  const checks = {};
  for (const matrix of matrices) checks[matrix] = await executeAudit(options, context, matrix, options.reportDir);

  if (options.target === 'coolify') {
    const after = await discoverContainer(options, context.target.container.id);
    if (after.id !== context.target.container.id || after.image_id !== context.target.container.image_id) {
      throw new CliError('The Coolify container changed during the audit.', 1, { before: context.target.container, after });
    }
    context.target.container_after = after;
  }

  const allPassed = Object.values(checks).every((check) => check.status === 'pass');
  const releaseProof = allPassed && options.command === null && options.matrix === 'all';
  const completedAt = new Date();
  return {
    schema_version: '1',
    audit: 'martool-cli-combined',
    run_id: randomUUID(),
    started_at: startedAt.toISOString(),
    completed_at: completedAt.toISOString(),
    duration_ms: completedAt.getTime() - startedAt.getTime(),
    target: context.target,
    selection: { matrix: options.matrix, command: options.command, executed_matrices: matrices },
    version: publicVersion(context.version),
    manifest: {
      generated_commands: generatedNames.length,
      platform_commands: platformNames.length,
      unique_commands: new Set([...generatedNames, ...platformNames]).size,
    },
    checks,
    safety: {
      local_docker_used: false,
      paid_provider_calls_allowed: false,
      remote_environment_dumped: false,
    },
    verdict: allPassed ? (releaseProof ? 'verified' : 'diagnostic-pass') : 'failed',
    artifacts: { report_dir: options.reportDir, combined_report: 'combined.json' },
  };
}

async function emit(report, exitCode) {
  if (report.artifacts?.report_dir !== undefined) {
    await writeAtomic(join(report.artifacts.report_dir, 'combined.json'), `${JSON.stringify(report, null, 2)}\n`);
  }
  process.stdout.write(`${JSON.stringify(report)}\n`);
  process.exitCode = exitCode;
}

async function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
    if (options.help) {
      process.stdout.write(HELP);
      return;
    }
    const report = await execute(options);
    await emit(report, report.verdict === 'failed' ? 1 : 0);
  } catch (error) {
    const known = error instanceof CliError;
    const message = error instanceof Error ? error.message : String(error);
    const report = {
      schema_version: '1',
      audit: 'martool-cli-combined',
      ok: false,
      fatal_error: { code: known ? 'AUDIT_SETUP_FAILED' : 'UNEXPECTED_FAILURE', message, details: known ? error.details : undefined },
      verdict: 'failed',
      artifacts: options === undefined ? null : { report_dir: options.reportDir, combined_report: 'combined.json' },
    };
    await emit(report, known ? error.exitCode : 1);
  }
}

const invokedPath = process.argv[1] === undefined ? null : pathToFileURL(resolve(process.argv[1])).href;
if (invokedPath === import.meta.url) await main();

export { HELP };
