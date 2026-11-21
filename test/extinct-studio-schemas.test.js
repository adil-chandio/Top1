import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { validate } from '../tools/extinct-studio/validate.js';

const here = dirname(fileURLToPath(import.meta.url));
const SCHEMAS_DIR = join(here, '..', 'tools', 'extinct-studio', 'schemas');
const FIXTURES_DIR = join(here, 'fixtures', 'extinct-studio');

const fixtureNames = readdirSync(FIXTURES_DIR).filter((f) => f.endsWith('.json')).sort();

test('every schema file is valid JSON', () => {
  for (const file of readdirSync(SCHEMAS_DIR).filter((f) => f.endsWith('.schema.json'))) {
    assert.doesNotThrow(() => JSON.parse(readFileSync(join(SCHEMAS_DIR, file), 'utf8')), `schema '${file}' should parse`);
  }
});

test('every fixture has a schema and validates clean', () => {
  assert.equal(fixtureNames.length, 14, 'expected the 14 sample fixtures');
  for (const fixtureName of fixtureNames) {
    const schemaFile = join(SCHEMAS_DIR, `${fixtureName}.schema.json`);
    assert.ok(existsSync(schemaFile), `missing schema for fixture '${fixtureName}'`);
    const schema = JSON.parse(readFileSync(schemaFile, 'utf8'));
    const fixture = JSON.parse(readFileSync(join(FIXTURES_DIR, fixtureName), 'utf8'));
    const errors = validate(schema, fixture);
    assert.deepEqual(errors, [], `fixture '${fixtureName}' should validate against its schema — got ${JSON.stringify(errors)}`);
  }
});

test('schemas catch real errors', () => {
  const schema = JSON.parse(readFileSync(join(SCHEMAS_DIR, 'idea-scorecard.json.schema.json'), 'utf8'));
  const errors = validate(schema, { createdAt: '2026-11-21T10:00:00.000Z' });
  assert.ok(errors.length > 0);

  const validFixture = JSON.parse(readFileSync(join(FIXTURES_DIR, 'idea-scorecard.json'), 'utf8'));
  const outOfRange = validate(schema, { ...validFixture, total: 999 });
  assert.ok(outOfRange.some((e) => /total/.test(e)));
});

test('validator reports unsupported keywords rather than silently ignoring them', () => {
  const errors = validate({ type: 'object', dependencies: ['x'] }, {});
  assert.ok(errors.some((e) => /not supported/i.test(e)));
});

test('validator rejects wrong-type values', () => {
  const errors = validate({ type: 'string', minLength: 1 }, 42);
  assert.ok(errors.some((e) => /expected string/.test(e)));
});
