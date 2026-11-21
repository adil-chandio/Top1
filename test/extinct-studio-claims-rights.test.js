import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CLAIM_CATEGORIES, validateClaim, validateClaims,
  validateRightsEntry, validateRights,
} from '../tools/extinct-studio/claims-rights.js';

test('claim categories are the doc\'s 8 and require agreed evidence for direct claims', () => {
  assert.equal(CLAIM_CATEGORIES.length, 8);

  const noEvidence = validateClaim({ id: 'c1', category: 'measured', text: 'x' });
  assert.equal(noEvidence.ok, false);
  assert.ok(noEvidence.errors.some((e) => /evidence/i.test(e)));

  const noBasis = validateClaim({ id: 'c2', category: 'directly-observed', text: 'x', evidenceIds: ['src-1'] });
  assert.equal(noBasis.ok, false);
  assert.ok(noBasis.errors.some((e) => /basis/i.test(e)));

  const ok = validateClaim({ id: 'c3', category: 'published-finding', text: 'x', basis: 'paper', evidenceIds: ['src-1'] });
  assert.equal(ok.ok, true);
});

test('illustrative / modelled content cannot be presented as a direct observation', () => {
  const illustrativeBad = validateClaim({
    id: 'c4', category: 'illustrative-animation',
    text: 'Animation shows the process directly observed',
    evidenceIds: [],
  });
  assert.equal(illustrativeBad.ok, false);

  const modelledOk = validateClaim({ id: 'c5', category: 'modelled-reconstruction', text: 'A modeled estimate of the sequence' });
  assert.equal(modelledOk.ok, true);
});

test('validateClaims returns entries separately from errors', () => {
  const result = validateClaims({
    entries: [
      { id: 'ok-1', category: 'hypothesis', text: 'a' },
      { id: 'bad-1', category: 'measured', text: 'x' },
    ],
  });
  assert.equal(result.ok, false);
  assert.equal(result.entries.length, 1);
  assert.equal(result.entries[0].id, 'ok-1');
});

test('rights entries: free-download alone is rejected, known licenses accepted', () => {
  const freeDownload = validateRightsEntry({
    id: 'r1', sourceType: 'paper', url: 'https://example.org', license: 'free download', commercialAllowed: true, accessDate: '2026-11-21',
  });
  assert.equal(freeDownload.ok, false);

  const ccBy = validateRightsEntry({
    id: 'r2', sourceType: 'paper', url: 'https://example.org', license: 'CC BY 4.0', commercialAllowed: true, accessDate: '2026-11-21',
  });
  assert.equal(ccBy.ok, true);

  const commercialWithUnsafe = validateRightsEntry({
    id: 'r3', sourceType: 'sound', url: 'https://example.org', license: 'All rights reserved', commercialAllowed: true, accessDate: '2026-11-21',
  });
  assert.equal(commercialWithUnsafe.ok, false);
});

test('rights manifest rejects duplicate ids', () => {
  const result = validateRights({
    entries: [
      { id: 'dup', sourceType: 'font', url: 'https://example.org', license: 'MIT', commercialAllowed: true, accessDate: '2026-11-21' },
      { id: 'dup', sourceType: 'font', url: 'https://example.org', license: 'MIT', commercialAllowed: true, accessDate: '2026-11-21' },
    ],
  });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /duplicate/i.test(e)));
});
