export { loadDependencies } from './dependencies.mjs';
import { readFileSync } from 'node:fs';
import { getDependencies } from './dependencies.mjs';

const schema = JSON.parse(readFileSync(new URL('../../schemas/records.schema.json', import.meta.url), 'utf8'));
const runtimeSchema = JSON.parse(readFileSync(new URL('../../schemas/runtime.schema.json', import.meta.url), 'utf8'));
Object.assign(schema.definitions, runtimeSchema.definitions);
const validators = new Map();

export class CliError extends Error {
  constructor(code, message, exitCode = 3, details = []) {
    super(message);
    this.name = 'CliError';
    this.code = code;
    this.exitCode = exitCode;
    this.details = details;
  }
}

export function validateRecord(record) {
  return validateShape(record?.kind, record);
}

export function validateShape(kind, record) {
  if (!schema.definitions[kind]) throw new CliError('INVALID_RECORD', `Unknown record kind ${kind}.`);
  if (!validators.has(kind)) validators.set(kind, new (getDependencies().Ajv)({ allErrors: true, strict: true }).compile(schema.definitions[kind]));
  const validate = validators.get(kind);
  if (!validate(record)) {
    const meaningful = validate.errors.filter(error => !error.schemaPath.includes('/oneOf/') || error.keyword === 'additionalProperties');
    const errors = meaningful.length ? meaningful : validate.errors;
    const issues = errors.map(error => ({
      field: error.instancePath || '/', rule: error.keyword,
      ...(error.params.additionalProperty ? { property: error.params.additionalProperty } : {}),
      ...(error.params.missingProperty ? { property: error.params.missingProperty } : {}),
      ...(error.params.allowedValues ? { allowed: error.params.allowedValues } : {}),
      ...(error.params.allowedValue !== undefined ? { expected: error.params.allowedValue } : {}),
      ...(error.params.type ? { expected: error.params.type } : {}),
      remedy: error.keyword === 'additionalProperties' ? `Remove the unsupported property ${error.params.additionalProperty}.` : error.keyword === 'required' ? `Supply ${error.params.missingProperty}.` : error.keyword === 'enum' ? 'Choose one of the allowed values.' : `Correct this field to satisfy ${error.keyword}.`,
    }));
    const error = new CliError('INVALID_RECORD', `Invalid ${kind} record.`, 3, errors.map(error => `${error.instancePath || '/'} ${error.message}${error.params.additionalProperty ? `: ${error.params.additionalProperty}` : ''}`));
    error.issues = issues;
    error.next_actions = ['Correct the listed fields in the draft and retry the same command.'];
    throw error;
  }
  return record;
}
