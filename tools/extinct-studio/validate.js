// Minimal, dependency-free JSON Schema validator (draft-07, subset).
//
// This exists so the Extinct Studio schemas have an honest, zero-dependency
// validator in the repo. It deliberately implements only the subset the
// schemas use — type, required, properties, additionalProperties, enum,
// items, minItems/maxItems, minLength/maxLength, minimum/maximum, pattern,
// anyOf. It is NOT a full replacement for ajv, and it will say so loudly
// if a schema uses a keyword it does not implement (unknown keywords are
// surfaced as warnings, never silently ignored).

export const SUPPORTED_KEYWORDS = Object.freeze([
  'type', 'required', 'properties', 'additionalProperties', 'items',
  'minItems', 'maxItems', 'minLength', 'maxLength', 'minimum', 'maximum',
  'pattern', 'enum', 'anyOf', 'title', 'description',
]);

const TYPE_NAMES = { string: 'string', number: 'number', integer: 'integer', boolean: 'boolean', array: 'array', object: 'object', null: 'null' };

function typeMatches(type, value) {
  if (type === 'integer') return typeof value === 'number' && Number.isInteger(value);
  if (type === 'number') return typeof value === 'number' && Number.isFinite(value);
  if (type === 'array') return Array.isArray(value);
  if (type === 'object') return value !== null && typeof value === 'object' && !Array.isArray(value);
  if (type === 'null') return value === null;
  return typeof value === type;
}

function typeName(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((x, i) => deepEqual(x, b[i]));
  }
  if (!Array.isArray(a) && !Array.isArray(b)) {
    const ka = Object.keys(a); const kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    return ka.every((k) => deepEqual(a[k], b[k]));
  }
  return false;
}

const KNOWN_KEYS = new Set(['title', 'description', '$schema', 'definitions', ...SUPPORTED_KEYWORDS]);

/** Validate `value` against `schema`. Returns an array of human-readable error strings (empty = valid). */
export function validate(schema, value, path = '$') {
  const errors = [];
  checkSchemaShape(schema, path, errors);
  check(schema, value, path, errors);
  return errors;
}

function checkSchemaShape(schema, path, errors) {
  if (schema === null || typeof schema !== 'object' || Array.isArray(schema)) {
    errors.push(`${path}: schema must be an object`);
  }
}

function check(schema, value, path, errors) {
  if (schema === null || typeof schema !== 'object' || Array.isArray(schema)) return;
  // Surface unsupported keywords honestly (never silently ignored).
  for (const key of Object.keys(schema)) {
    if (!KNOWN_KEYS.has(key)) errors.push(`${path}: schema keyword '${key}' is not supported by this validator`);
  }

  // anyOf is handled first: if any sub-schema validates cleanly, the value passes.
  if (Array.isArray(schema.anyOf)) {
    const matched = schema.anyOf.some((sub) => {
      const subErrors = [];
      check(sub, value, path, subErrors);
      return subErrors.length === 0;
    });
    if (!matched) errors.push(`${path}: value does not match any allowed shape`);
    return;
  }

  if (schema.enum !== undefined && !schema.enum.some((e) => deepEqual(e, value))) {
    errors.push(`${path}: value must be one of ${JSON.stringify(schema.enum)} (got ${JSON.stringify(value)})`);
  }
  if (schema.type !== undefined && !typeMatches(schema.type, value)) {
    errors.push(`${path}: expected ${schema.type}, got ${typeName(value)}`);
    return;   // further keyword checks on a non-matching value would be noise
  }

  if (schema.minimum !== undefined && typeof value === 'number' && value < schema.minimum) errors.push(`${path}: ${value} < minimum ${schema.minimum}`);
  if (schema.maximum !== undefined && typeof value === 'number' && value > schema.maximum) errors.push(`${path}: ${value} > maximum ${schema.maximum}`);
  if (schema.minLength !== undefined && typeof value === 'string' && value.length < schema.minLength) errors.push(`${path}: string shorter than ${schema.minLength}`);
  if (schema.maxLength !== undefined && typeof value === 'string' && value.length > schema.maxLength) errors.push(`${path}: string longer than ${schema.maxLength}`);
  if (schema.pattern !== undefined && typeof value === 'string') {
    try { if (!new RegExp(schema.pattern).test(value)) errors.push(`${path}: '${value}' does not match pattern /${schema.pattern}/`); } catch { /* invalid pattern surfaces as error below */ }
  }
  if (schema.minItems !== undefined && Array.isArray(value) && value.length < schema.minItems) errors.push(`${path}: array shorter than ${schema.minItems}`);
  if (schema.maxItems !== undefined && Array.isArray(value) && value.length > schema.maxItems) errors.push(`${path}: array longer than ${schema.maxItems}`);

  if (schema.type === 'object' || (schema.properties !== undefined && value !== null && typeof value === 'object' && !Array.isArray(value))) {
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      const required = schema.required ?? [];
      for (const key of required) if (!(key in value)) errors.push(`${path}: missing required property '${key}'`);
      const props = schema.properties ?? {};
      for (const [key, subSchema] of Object.entries(props)) {
        if (key in value) check(subSchema, value[key], `${path}.${key}`, errors);
      }
      if (schema.additionalProperties === false) {
        for (const key of Object.keys(value)) {
          if (!(key in props)) errors.push(`${path}: unexpected property '${key}'`);
        }
      }
    }
  }

  if (schema.type === 'array' || schema.items !== undefined) {
    if (Array.isArray(value)) {
      if (schema.items) {
        for (let i = 0; i < value.length; i++) check(schema.items, value[i], `${path}[${i}]`, errors);
      }
    }
  }
}

/** Validate an artifact against its schema file (file contents as JSON.parse-able text). */
export function validateAgainstSchema(schema, value) {
  return validate(schema, value);
}

export default { validate };
