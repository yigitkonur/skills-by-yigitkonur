#!/usr/bin/env node
import { pathToFileURL } from 'node:url';

const commands = {
  doctor: { options: ['project', 'setup'], required: [], module: 'workflow' },
  init: { options: ['project', 'slug', 'mode', 'max-active', 'host-capacity', 'max-attempts', 'locale', 'github-remote'], required: ['project', 'slug'], module: 'workflow' },
  'plan accept': { options: ['campaign', 'file', 'audit'], required: ['campaign', 'file', 'audit'], module: 'workflow' },
  'finding link': { options: ['campaign', 'file'], required: ['campaign', 'file'], module: 'workflow' },
  'finding decide': { options: ['campaign', 'finding-id', 'scope', 'reason', 'source'], required: ['campaign', 'finding-id', 'scope', 'reason', 'source'], module: 'workflow' },
  'task create': { options: ['campaign', 'request'], required: ['campaign', 'request'], module: 'workflow' },
  'task dispatch': { options: ['campaign', 'task-id'], required: ['campaign', 'task-id'], module: 'workflow' },
  'task bind': { options: ['campaign', 'task-id', 'handle'], required: ['campaign', 'task-id', 'handle'], module: 'workflow' },
  'task close': { options: ['campaign', 'task-id', 'finished'], required: ['campaign', 'task-id', 'finished'], module: 'workflow' },
  'task interrupt': { options: ['campaign', 'task-id', 'reason', 'finished'], required: ['campaign', 'task-id', 'reason'], module: 'workflow' },
  submit: { options: ['campaign', 'task-id', 'file', 'check'], required: ['campaign', 'task-id', 'file'], module: 'workflow' },
  reconcile: { options: ['campaign'], required: ['campaign'], module: 'workflow' },
  status: { options: ['campaign'], required: ['campaign'], module: 'workflow' },
  records: { options: ['campaign', 'record-id', 'kind', 'case-id', 'round-id', 'finding-id', 'ready', 'format'], required: ['campaign'], module: 'workflow' },
  'runtime recover': { options: ['campaign', 'target-id', 'file'], required: ['campaign', 'target-id', 'file'], module: 'workflow' },
  'runtime start': { options: ['campaign', 'file'], required: ['campaign', 'file'], module: 'runtime' },
  'runtime inspect': { options: ['campaign', 'target-id'], required: ['campaign', 'target-id'], module: 'runtime' },
  'runtime stop': { options: ['campaign', 'target-id'], required: ['campaign', 'target-id'], module: 'runtime' },
  'report build': { options: ['campaign'], required: ['campaign'], module: 'report' },
  'report serve': { options: ['campaign', 'port'], required: ['campaign'], module: 'report' },
  'report stop': { options: ['campaign'], required: ['campaign'], module: 'report' },
};

const booleanOptions = new Set(['setup', 'finished', 'check', 'ready', 'help']);
function usageError(code, message, details = []) {
  return Object.assign(new Error(message), { code, exitCode: 2, details });
}

function parse(argv) {
  if (argv.length === 0 || (argv.length === 1 && ['--help', '-h'].includes(argv[0]))) return { help: true };
  const words = [];
  let index = 0;
  while (index < argv.length && !argv[index].startsWith('-')) words.push(argv[index++]);
  const command = words.join(' ');
  const definition = commands[command];
  if (!definition) throw usageError('UNKNOWN_COMMAND', `Unknown command: ${command || '(empty)'}. Run --help.`);
  const options = {};
  while (index < argv.length) {
    const token = argv[index++];
    if (token === '-h') {
      if (options.help !== undefined) throw usageError('DUPLICATE_OPTION', 'Option --help was repeated.');
      options.help = true;
      continue;
    }
    if (!token.startsWith('--')) throw usageError('UNEXPECTED_ARGUMENT', `Unexpected positional argument after ${command}.`);
    const separator = token.indexOf('=');
    const key = token.slice(2, separator < 0 ? undefined : separator);
    const supplied = separator < 0 ? undefined : token.slice(separator + 1);
    if (key !== 'help' && !definition.options.includes(key)) {
      throw usageError('UNKNOWN_OPTION', `Unknown option --${key} for ${command}.`, [{ valid_options: definition.options }]);
    }
    if (Object.hasOwn(options, key)) throw usageError('DUPLICATE_OPTION', `Option --${key} was repeated.`);
    if (booleanOptions.has(key)) {
      const value = supplied ?? (['true', 'false'].includes(argv[index]) ? argv[index++] : 'true');
      if (!['true', 'false'].includes(value)) throw usageError('INVALID_OPTION_VALUE', `--${key} requires true or false.`);
      options[key] = value === 'true';
    } else {
      const value = supplied ?? (argv[index] && !argv[index].startsWith('--') ? argv[index++] : undefined);
      if (value === undefined || value === '') throw usageError('MISSING_OPTION_VALUE', `--${key} needs a value.`);
      options[key] = value;
    }
  }
  if (!options.help) {
    const missing = definition.required.filter(key => !Object.hasOwn(options, key));
    if (missing.length) throw usageError('MISSING_OPTION', `Missing required options for ${command}.`, missing.map(option => ({ option, remedy: `Supply --${option}.` })));
  }
  if (options.format && !['json', 'yaml-stream'].includes(options.format)) throw usageError('INVALID_OPTION_VALUE', '--format must be json or yaml-stream.');
  return { command, definition, options, help: options.help };
}

function help(command) {
  const rule = 'An accepted submission is not a test pass. Independent evidence verification determines verdicts.';
  if (command) return { command, options: commands[command].options, required: commands[command].required, completion_rule: rule };
  return {
    description: 'Filesystem records and handoffs for independent agentic E2E testing.',
    commands: Object.entries(commands).map(([name, definition]) => ({ name, options: definition.options, required: definition.required })),
    completion_rule: rule,
    exit_codes: { 0: 'command accepted, including negative test reports', 2: 'usage', 3: 'validation', 4: 'conflict', 5: 'dependency or access', 6: 'I/O or internal failure' },
  };
}

export async function main(argv = process.argv.slice(2)) {
  let command;
  try {
    const parsed = parse(argv);
    command = parsed.command;
    if (parsed.help) {
      process.stdout.write(`${JSON.stringify({ ok: true, schema_version: 1, ...help(command) })}\n`);
      return 0;
    }
    if (Number(process.versions.node.split('.')[0]) < 22) {
      throw Object.assign(new Error('Node.js 22 or newer is required.'), { code: 'NODE_VERSION_UNSUPPORTED', exitCode: 5 });
    }
    const implementation = await import(new URL(`./lib/${parsed.definition.module}.mjs`, import.meta.url));
    const result = await implementation.run(command, parsed.options);
    if (command === 'records' && parsed.options.format === 'yaml-stream') {
      if (typeof result.yaml_stream !== 'string') throw new Error('Record export did not return a YAML stream.');
      process.stdout.write(result.yaml_stream);
    } else {
      process.stdout.write(`${JSON.stringify({ ...result, ok: true, schema_version: 1, command })}\n`);
    }
    return 0;
  } catch (error) {
    const exitCode = Number.isInteger(error.exitCode) && error.exitCode >= 2 && error.exitCode <= 6 ? error.exitCode : 6;
    process.stdout.write(`${JSON.stringify({
      ok: false,
      schema_version: 1,
      command: command ?? null,
      worker_may_finish: false,
      error: { code: error.code ?? 'INTERNAL_ERROR', message: error.message, details: error.details ?? [], issues: error.issues ?? [] },
      next_actions: error.next_actions ?? ['Correct the reported problem and retry; preserve drafts and accepted history.'],
    })}\n`);
    return exitCode;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = await main();
}
