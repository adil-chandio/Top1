import test from 'node:test';
import assert from 'node:assert/strict';
import {
  WEIGHTS, WEIGHT_SUM, STRONG_SCORE, REJECT_SCORE,
  scoreIdea, evaluateIdea, buildScorecard,
} from '../tools/extinct-studio/scorecard.js';

const fullScores = {
  viewerPromiseClarity: 18,
  visibleProofPotential: 18,
  novelty: 13,
  evidenceStrength: 12,
  emotionalStakesValue: 9,
  shortLongFormatFit: 9,
  rightsCertainty: 4,
  productionFeasibility: 4,
};

test('weights sum to 100 (the doc\'s 100-point math)', () => {
  assert.equal(WEIGHT_SUM, 100);
  for (const [, w] of Object.entries(WEIGHTS)) assert.ok(w > 0);
});

test('scoreIdea sums the breakdown and flags missing/invalid categories', () => {
  const scored = scoreIdea(fullScores);
  assert.equal(scored.ok, true);
  assert.equal(scored.total, 87);

  const missing = scoreIdea({ viewerPromiseClarity: 18 });
  assert.equal(missing.ok, false);
  assert.ok(missing.missing.length >= 6);

  const invalid = scoreIdea({ ...fullScores, novelty: 99 });
  assert.equal(invalid.ok, false);
  assert.ok(invalid.invalid.some((i) => i.key === 'novelty'));
});

test('an idea with zero visual proof is rejected, not scored', () => {
  const evaluated = evaluateIdea({ ...fullScores, visibleProofPotential: REJECT_SCORE }, {
    claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: true,
  });
  assert.equal(evaluated.decision, 'rejected');
  assert.equal(evaluated.rejected, true);
  assert.match(evaluated.rejectReason, /interesting fact/);
});

test('a strong score + all gates green → production-candidate', () => {
  const evaluated = evaluateIdea(fullScores, {
    claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: true,
  });
  assert.equal(evaluated.decision, 'production-candidate');
  assert.equal(evaluated.strongScore, true);
  assert.equal(evaluated.total, 87);
});

test('weak score or failed gate → not-yet, even with a strong-looking total', () => {
  const weak = evaluateIdea({ ...fullScores, viewerPromiseClarity: 0, visibleProofPotential: 18 }, {
    claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: true,
  });
  assert.equal(weak.decision, 'not-yet');

  const missing = evaluateIdea(fullScores, {
    claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: false,
  });
  assert.equal(missing.decision, 'not-yet');
  assert.ok(missing.failedGates.includes('ownerSelection'));
});

test('buildScorecard produces a valid artifact and refuses a contradictory decision', () => {
  const artifact = buildScorecard({
    projectId: 'demo-project',
    scores: fullScores,
    gates: { claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: true },
    createdAt: '2026-11-21T10:00:00.000Z',
  });
  assert.equal(artifact.decision, 'production-candidate');
  assert.equal(artifact.total, 87);
  assert.equal(artifact.gates.ownerSelection, true);

  assert.throws(
    () => buildScorecard({
      scores: fullScores,
      gates: { claimLedgerComplete: true, titlePromiseClear: true, proofPossible: true, ownerSelection: false },
      decision: 'production-candidate',
      createdAt: '2026-11-21T10:00:00.000Z',
    }),
    /contradicts/,
  );
});
