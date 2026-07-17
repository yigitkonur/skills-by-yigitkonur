import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import * as runner from './run-martool-cli-audit.mjs';
import {
  parseArgs,
  parseContainerLine,
  validateGeneratedReport,
  validatePlatformReport,
} from './run-martool-cli-audit.mjs';

const skillRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function generatedReport(overrides = {}) {
  return {
    schema_version: '1',
    audit: 'martool-generated-flags',
    totals: { fail: 0, baseline_fail: 0 },
    coverage: {
      complete: true,
      missing_cases: [],
      unexpected_cases: [],
      duplicate_plan_ids: [],
      duplicate_completed_ids: [],
    },
    ...overrides,
  };
}

function platformReport(overrides = {}) {
  return {
    schema_version: '1',
    audit: 'martool-platform-flags',
    manifest: { duplicate_commands: [], duplicate_flags: [] },
    totals: { attempted: 4, fail: 0, reachable_commands: 2, total_commands: 2 },
    safety: { provider_calls: 0, paid_provider_calls: 0 },
    coverage: {
      missing_cases: [],
      unexpected_cases: [],
      duplicate_plan_ids: [],
      uncovered_flags: [],
      uncovered_positionals: [],
    },
    ...overrides,
  };
}

test('parseArgs uses safe source defaults', () => {
  const options = parseArgs([], '/tmp/martool');
  assert.equal(options.target, 'source');
  assert.equal(options.repo, '/tmp/martool');
  assert.equal(options.matrix, 'all');
  assert.equal(options.build, true);
});

test('parseArgs accepts the Coolify interface', () => {
  const options = parseArgs([
    '--target', 'coolify',
    '--ssh-host', 'ops@hetzner',
    '--coolify-project', 'martool',
    '--service', 'martool',
    '--command', 'keywords research',
  ], '/tmp');
  assert.equal(options.sshHost, 'ops@hetzner');
  assert.equal(options.command, 'keywords research');
});

test('parseArgs rejects shell metacharacters in remote identifiers', () => {
  assert.throws(
    () => parseArgs(['--target', 'coolify', '--ssh-host', 'hetzner;touch-pwned'], '/tmp'),
    /unsupported characters/u,
  );
});

test('parseArgs rejects shell metacharacters in a remote command filter', () => {
  assert.throws(
    () => parseArgs([
      '--target', 'coolify',
      '--ssh-host', 'hetzner',
      '--command', 'version; touch-pwned',
    ], '/tmp'),
    /unsupported characters/u,
  );
});

test('remote transport preserves empty positional values with a sentinel', () => {
  assert.equal(typeof runner.encodeRemoteValue, 'function');
  assert.equal(runner.encodeRemoteValue(null), '-');
  assert.equal(runner.encodeRemoteValue(''), '-');
  assert.equal(runner.encodeRemoteValue('version'), 'version');
});

test('remote transport keeps long-running SSH sessions alive', () => {
  assert.deepEqual(runner.SSH_OPTIONS, [
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=10',
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=4',
  ]);
});

test('parseContainerLine accepts one healthy pinned container', () => {
  assert.deepEqual(
    parseContainerLine('abc123|/martool-1|martool:sha|sha256:image|true|healthy\n'),
    {
      id: 'abc123',
      name: 'martool-1',
      image_ref: 'martool:sha',
      image_id: 'sha256:image',
      health: 'healthy',
    },
  );
});

test('parseContainerLine rejects an unhealthy container', () => {
  assert.throws(
    () => parseContainerLine('abc123|/martool-1|martool:sha|sha256:image|true|unhealthy\n'),
    /not healthy/u,
  );
});

test('generated report requires exact complete coverage', () => {
  assert.deepEqual(validateGeneratedReport(generatedReport()), []);
  const failures = validateGeneratedReport(generatedReport({
    coverage: {
      complete: false,
      missing_cases: ['case-1'],
      unexpected_cases: [],
      duplicate_plan_ids: [],
      duplicate_completed_ids: [],
    },
  }));
  assert.match(failures.join('\n'), /coverage is incomplete/u);
  assert.match(failures.join('\n'), /missing cases/u);
});

test('platform report requires zero provider calls', () => {
  assert.deepEqual(validatePlatformReport(platformReport()), []);
  const failures = validatePlatformReport(platformReport({
    safety: { provider_calls: 1, paid_provider_calls: 0 },
  }));
  assert.deepEqual(failures, ['provider calls: 1']);
});

test('diagnostic platform report allows declared partial coverage', () => {
  const report = platformReport({
    totals: { attempted: 2, fail: 0, reachable_commands: 1, total_commands: 35 },
    coverage: {
      missing_cases: ['outside-scope'],
      unexpected_cases: [],
      duplicate_plan_ids: [],
      uncovered_flags: ['outside-scope --flag'],
      uncovered_positionals: [],
    },
  });
  assert.deepEqual(validatePlatformReport(report, { diagnostic: true }), []);
  assert.match(validatePlatformReport(report).join('\n'), /missing cases/u);
});

test('Codex installation examples use the current plugin add command', async () => {
  for (const relativePath of ['README.md', 'references/installation.md']) {
    const contents = await readFile(resolve(skillRoot, relativePath), 'utf8');
    assert.match(contents, /codex plugin add test-martool-cli@yigitkonur/u);
    assert.doesNotMatch(contents, /codex plugin install/u);
  }
});
