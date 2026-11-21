// Extinct Studio OS — idea scorecard (pre-production quality gate).
//
// The doc's #5 scores 100 points across eight dimensions with explicit
// weights. An idea only becomes a production candidate when the score is
// strong AND every gate is green; an idea that is only an interesting
// fact is rejected outright.
//
// This module is pure (no I/O) and carries its own gates — the scorecard
// artifact is produced with `evaluateIdea`, then validated against the
// idea-scorecard.json schema.

export const WEIGHTS = Object.freeze({
  viewerPromiseClarity: 20,
  visibleProofPotential: 20,
  novelty: 15,
  evidenceStrength: 15,
  emotionalStakesValue: 10,
  shortLongFormatFit: 10,
  rightsCertainty: 5,
  productionFeasibility: 5,
});

export const WEIGHT_SUM = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
export const STRONG_SCORE = 75; // documented heuristic for "strong" — owner may tighten it

// Rejection — the doc's words: "agar idea sirf 'interesting fact' hai lekin
// visually prove nahi hota to reject hoga." No visual proof possible = rejected.
export const REJECT_SCORE = 0;

/** Validate the eight scores. Returns { ok, missing, invalid }. */
export function scoreIdea(scores) {
  const missing = [];
  const invalid = [];
  const breakdown = {};
  for (const [key, weight] of Object.entries(WEIGHTS)) {
    const raw = scores?.[key];
    if (raw === undefined || raw === null) { missing.push(key); continue; }
    if (typeof raw !== 'number' || Number.isNaN(raw) || !Number.isFinite(raw)) { invalid.push({ key, value: raw, reason: 'must be a finite number' }); continue; }
    if (raw < 0) { invalid.push({ key, value: raw, reason: 'cannot be negative' }); continue; }
    if (raw > weight) { invalid.push({ key, value: raw, reason: `cannot exceed weight ${weight}` }); continue; }
    breakdown[key] = raw;
  }
  // total must be >= sum of weights
  return {
    ok: missing.length === 0 && invalid.length === 0,
    missing,
    invalid,
    breakdown,
    total: Object.values(breakdown).reduce((a, b) => a + b, 0),
  };
}

/**
 * Evaluate an idea.
 * gates: { claimLedgerComplete, titlePromiseClear, proofPossible, ownerSelection }
 * → { total, rejected, rejectReason, decision, gateResults, reasons }
 */
export function evaluateIdea(scores, gates = {}) {
  const scored = scoreIdea(scores);
  if (!scored.ok) {
    return {
      total: scored.total,
      rejected: false,
      rejectReason: null,
      decision: 'not-yet',
      invalid: true,
      missing: scored.missing,
      invalidScores: scored.invalid,
      gateResults: {},
      reasons: ['incomplete or invalid scores'],
    };
  }
  // Reject — only an interesting fact, not provable visually.
  if (scored.breakdown.visibleProofPotential === REJECT_SCORE) {
    return {
      total: scored.total,
      rejected: true,
      rejectReason: 'idea is only an interesting fact — no visual proof is possible',
      decision: 'rejected',
      gateResults: {},
      reasons: ['visible proof potential is 0'],
    };
  }

  const gateResults = Object.freeze({
    claimLedgerComplete: Boolean(gates.claimLedgerComplete),
    titlePromiseClear: Boolean(gates.titlePromiseClear),
    proofPossible: Boolean(gates.proofPossible),
    ownerSelection: Boolean(gates.ownerSelection),
  });

  const failedGates = [];
  for (const [gate, ok] of Object.entries(gateResults)) {
    if (!ok) failedGates.push(gate);
  }

  const strongScore = scored.total >= STRONG_SCORE;
  const productionCandidate = strongScore && failedGates.length === 0 && gateResults.ownerSelection;

  const reasons = [];
  if (!strongScore) reasons.push(`score ${scored.total} is below strong threshold ${STRONG_SCORE}`);
  if (failedGates.length) reasons.push(`gates not green: ${failedGates.join(', ')}`);

  return {
    total: scored.total,
    rejected: false,
    rejectReason: null,
    decision: productionCandidate ? 'production-candidate' : 'not-yet',
    gateResults,
    strongScore,
    failedGates,
    reasons,
  };
}

// Build the idea-scorecard artifact (validatable against the schema).
export function buildScorecard({ projectId, pilotId, scores, gates, decision, notes, rejectReason, createdAt }) {
  const scored = scoreIdea(scores);
  if (!scored.ok) throw new Error(`invalid scores: ${scored.missing.join(', ') || 'none missing but invalid'}`);
  const evalResult = evaluateIdea(scores, gates);
  if (decision !== undefined) {
    if (decision !== evalResult.decision) {
      throw new Error(`declared decision '${decision}' contradicts computed decision '${evalResult.decision}'`);
    }
  }
  return {
    createdAt: createdAt ?? new Date().toISOString(),
    ...(projectId ? { projectId } : {}),
    ...(pilotId ? { pilotId } : {}),
    scores: scored.breakdown,
    total: scored.total,
    gates: {
      claimLedgerComplete: Boolean(gates?.claimLedgerComplete),
      titlePromiseClear: Boolean(gates?.titlePromiseClear),
      proofPossible: Boolean(gates?.proofPossible),
      ownerSelection: Boolean(gates?.ownerSelection),
    },
    decision: evalResult.decision,
    ...(evalResult.rejectReason ? { rejectReason: evalResult.rejectReason } : {}),
    ...(notes ? { notes } : {}),
  };
}
