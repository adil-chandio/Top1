// Extinct Studio OS — claims classification + rights/licensing manifest.
//
// Straight from the doc's C and I sections:
//   - Every narration line gets a category — "directly-observed", "measured",
//     "published-finding", "derived-calculation", "modelled-reconstruction",
//     "illustrative-animation", "hypothesis", "unknown-limitation".
//     This kills "animation ko real footage" and "model ko proven fact" claims.
//   - Every third-party source is checked separately — paper, data, font, sound,
//     texture, model, code, reference-image, voice — and unknown/unclear
//     license is NOT safe. "Free download" is not a license.
//
// This module is pure. It does not classify or verify a claim on the owner's
// behalf; it validates that each artifact honestly states what it is.

export const CLAIM_CATEGORIES = Object.freeze([
  'directly-observed',
  'measured',
  'published-finding',
  'derived-calculation',
  'modelled-reconstruction',
  'illustrative-animation',
  'hypothesis',
  'unknown-limitation',
]);

// Categories that must carry evidence reference.
export const EVIDENCE_REQUIRED = Object.freeze(['directly-observed', 'measured', 'published-finding']);
// Categories that must NOT be presented as direct observation or fact.
export const NEVER_OBSERVED = Object.freeze(['modelled-reconstruction', 'illustrative-animation']);

export const CLAIMS_CATEGORY_BY_KEY = Object.freeze(Object.fromEntries(
  CLAIM_CATEGORIES.map((c) => [c.toLowerCase(), c]),
));

/** Validate a single claim entry. Returns { ok, errors }. */
export function validateClaim(entry) {
  const errors = [];
  if (!entry || typeof entry !== 'object') return { ok: false, errors: ['claim must be an object'] };
  if (typeof entry.id !== 'string' || !entry.id.trim()) errors.push('claim id must be a non-empty string');
  if (typeof entry.category !== 'string') {
    errors.push('claim category is required');
  } else {
    const category = CLAIMS_CATEGORY_BY_KEY[entry.category.toLowerCase()];
    if (!category) errors.push(`unknown category '${entry.category}' (allowed: ${CLAIM_CATEGORIES.join(', ')})`);
    else if (EVIDENCE_REQUIRED.includes(category)) {
      if (!Array.isArray(entry.evidenceIds) || entry.evidenceIds.length === 0 || entry.evidenceIds.some((e) => typeof e !== 'string' || !e.trim())) {
        errors.push(`category '${category}' requires at least one evidence reference`);
      }
      if (typeof entry.basis !== 'string' || !entry.basis.trim()) {
        errors.push(`category '${category}' requires a basis statement`);
      }
    }
    // Never present a modelled/illustrative thing as a direct observation.
    if (NEVER_OBSERVED.includes(category) && entry.text && /(directly observed|observed|proven fact|real footage)/i.test(entry.text)) {
      errors.push(`category '${category}' cannot be presented as a direct observation or proven fact`);
    }
  }
  if (typeof entry.text !== 'string' || !entry.text.trim()) errors.push('claim text is required');
  return { ok: errors.length === 0, errors };
}

/** Validate a claims register. Returns { ok, errors, entries }. */
export function validateClaims(claims) {
  const errors = [];
  if (!claims || typeof claims !== 'object') return { ok: false, errors: ['claims register must be an object'], entries: [] };
  if (!Array.isArray(claims.entries) || claims.entries.length === 0) {
    return { ok: false, errors: ['claims register must contain at least one entry'], entries: [] };
  }
  const entries = [];
  for (let i = 0; i < claims.entries.length; i++) {
    const entry = claims.entries[i];
    const result = validateClaim(entry);
    if (!result.ok) for (const err of result.errors) errors.push(`entries[${i}]: ${err}`);
    else entries.push(entry);
  }
  return { ok: errors.length === 0, errors, entries };
}

export const RIGHTS_SOURCE_TYPES = Object.freeze([
  'paper', 'data', 'font', 'sound', 'texture', 'model', 'code', 'reference-image', 'voice',
]);

const UNSAFE_LICENSE_PATTERNS = [
  /unknown/i,
  /unclear/i,
  /not[- ]licensed/i,
  /all[- ]rights[- ]reserved/i,
  /free download/i,
  /no[- ]license/i,
  /do not use/i,
  /no[- ]license[- ]specified/i,
];

const GENERIC_LICENSE_MARKERS = [
  'cc-by', 'cc by', 'cc-by-sa', 'cc0', 'public domain', 'apache', 'mit', 'isc', 'bsd', 'mpl', 'lgpl', 'gpl', 'wtfpl',
];

/**
 * Validate a rights entry. Returns { ok, errors }.
 *
 * Rules:
 *  - sourceType required and must be in the known list.
 *  - license must clearly describe what the license IS. Unknown/unclear and
 *    "free download" alone are not safe.
 *  - commercialAllowed must be consistent with the license.
 */
export function validateRightsEntry(entry) {
  const errors = [];
  if (!entry || typeof entry !== 'object') return { ok: false, errors: ['rights entry must be an object'] };
  if (typeof entry.sourceType !== 'string' || !RIGHTS_SOURCE_TYPES.includes(entry.sourceType)) {
    errors.push(`sourceType must be one of: ${RIGHTS_SOURCE_TYPES.join(', ')}`);
  }
  if (typeof entry.license !== 'string' || !entry.license.trim()) {
    errors.push('license is required');
  } else {
    const text = entry.license.trim();
    const isGeneric = GENERIC_LICENSE_MARKERS.some((marker) => text.toLowerCase().includes(marker));
    const isUnsafe = UNSAFE_LICENSE_PATTERNS.some((re) => re.test(text));
    if (isUnsafe) {
      errors.push(`license '${text}' is not safe to use (unknown/unclear/all-rights-reserved/free-download alone)`);
    } else if (!isGeneric) {
      // Known-safe generic license not recognized — surface it rather than auto-approving.
      errors.push(`license '${text}' is not in the known-safe list; do not use without explicit owner confirmation`);
    }
  }
  if (typeof entry.commercialAllowed !== 'boolean') {
    errors.push('commercialAllowed must be a boolean');
  } else if (entry.commercialAllowed === true && typeof entry.license === 'string') {
    const text = entry.license.toLowerCase();
    if (UNSAFE_LICENSE_PATTERNS.some((re) => re.test(text))) {
      errors.push('commercialAllowed cannot be true while the license forbids it');
    }
  }
  if (typeof entry.url !== 'string' || !entry.url.trim()) errors.push('url is required for provenance');
  if (typeof entry.accessDate !== 'string' || !/^\d{4}-\d{2}-\d{2}/.test(entry.accessDate ?? '')) errors.push('accessDate is required (ISO format)');
  return { ok: errors.length === 0, errors };
}

/** Validate a rights manifest. Returns { ok, errors, entries }. */
export function validateRights(manifest) {
  const errors = [];
  if (!manifest || typeof manifest !== 'object') return { ok: false, errors: ['rights manifest must be an object'], entries: [] };
  if (!Array.isArray(manifest.entries) || manifest.entries.length === 0) {
    return { ok: false, errors: ['rights manifest must contain at least one entry'], entries: [] };
  }
  const seen = new Set();
  const entries = [];
  for (let i = 0; i < manifest.entries.length; i++) {
    const entry = manifest.entries[i];
    const result = validateRightsEntry(entry);
    if (!result.ok) for (const err of result.errors) errors.push(`entries[${i}]: ${err}`);
    else if (entry.id != null) {
      if (seen.has(entry.id)) errors.push(`entries[${i}]: duplicate id '${entry.id}'`);
      seen.add(entry.id);
      entries.push(entry);
    }
  }
  return { ok: errors.length === 0, errors, entries };
}

// Convenience: assert the full claim-check for a story artifact.
export function narrativeAllowed(claims, text) {
  const result = validateClaims(claims);
  if (!result.ok) return { ok: false, reasons: result.errors, safe: [] };
  const claimLine = claims.entries.find((c) => c.id === text);
  if (!claimLine) return { ok: false, reasons: [`no claim matches id '${text}'`], safe: [] };
  const category = claimLine.category;
  return { ok: true, category, safe: [category] };
}
