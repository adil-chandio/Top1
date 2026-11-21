// Extinct Studio OS — formal project state machine + dependency DAG.
//
// The doc's V — Version and status requires a formal state machine, and the
// doc's W — Workflow DAG requires a dependency graph so a blind
// `run-all.sh` never rebuilds the whole film on every little change.
//
// Two hard rules, straight from the doc:
//   1. No tool sets the `published` status. Publication is a human act.
//   2. The dependency DAG is the unit of re-run scope, not the full film.
//
// Transitions are forward-only and require the receipt-gate for the target
// state (ctx carries the receipts/flags referenced by the gate).

export const STATES = Object.freeze([
  'idea', 'researched', 'shortlisted', 'owner-selected', 'claim-checked',
  'scripted', 'proof-pending', 'proof-passed', 'voice-locked', 'picture-locked',
  'mix-locked', 'qa-passed', 'owner-accepted', 'private-uploaded', 'published',
]);

export const nextState = (state) => {
  const i = STATES.indexOf(state);
  if (i < 0 || i === STATES.length - 1) return null;
  return STATES[i + 1];
};

// Gates: which context flag/receipt the target state requires.
export const GATES = Object.freeze({
  'researched': { key: 'research', label: 'research.json recorded' },
  'shortlisted': { key: 'research', label: 'research.json recorded and gap honesty checked' },
  'owner-selected': { key: 'ownerSelection', label: 'owner selection recorded' },
  'claim-checked': { key: 'claimLedgerComplete', label: 'claims ledger complete + every line classified' },
  'scripted': { key: 'story', label: 'story.json valid' },
  'proof-pending': { key: 'proofPossible', label: 'an 8-12s proof is possible' },
  'proof-passed': { key: 'proofReceipt', label: 'a pass proof-receipt exists', isReceipt: true },
  'voice-locked': { key: 'voiceLock', label: 'voice-lock.json valid', isReceipt: true },
  'picture-locked': { key: 'renderManifest', label: 'render-manifest.json valid', isReceipt: true },
  'mix-locked': { key: 'mix', label: 'audio mix lock recorded' },
  'qa-passed': { key: 'qaReports', label: 'video-qa + audio-qa both ok', isReceipt: true },
  'owner-accepted': { key: 'ownerAccept', label: 'owner sign-off — human action' },
  'private-uploaded': { key: 'privateUploadReceipt', label: 'private upload receipt recorded' },
  'published': { key: 'publishedReceipt', label: 'owner-only publication — never set by a tool' },
});

export const stateIndex = (state) => STATES.indexOf(state);

export function isState(state) {
  return STATES.includes(state);
}

/**
 * Check whether a transition is allowed.
 * ctx flags: research, ownerSelection, claimLedgerComplete, story,
 * proofPossible, proofReceipt:{pass}, voiceLock, renderManifest, mix,
 * qaReports:{videoOk,audioOk}, ownerAccept, privateUploadReceipt, publishedReceipt.
 */
export function canTransition(from, to, ctx = {}) {
  if (!isState(from)) return { ok: false, reason: `unknown state '${from}'` };
  if (!isState(to)) return { ok: false, reason: `unknown state '${to}'` };
  if (!STATES.includes(to)) return { ok: false, reason: `unknown state '${to}'` };

  const expected = nextState(from);
  if (expected === null) {
    if (to === from) return { ok: false, reason: 'terminal state — no transitions out' };
    return { ok: false, reason: `'${from}' is terminal (no next state)` };
  }
  if (to !== expected) {
    const fromIdx = stateIndex(from);
    const toIdx = stateIndex(to);
    if (toIdx > fromIdx) {
      const skipped = STATES.slice(fromIdx + 1, toIdx);
      return { ok: false, reason: `skipping states is not allowed — missing: ${skipped.join(', ')}` };
    }
    return { ok: false, reason: `going backwards is not allowed — use an explicit reject/return path` };
  }

  if (to === 'published') {
    return { ok: false, reason: 'no tool sets the published status — publication is an owner act' };
  }

  const gate = GATES[to];
  if (!gate) return { ok: false, reason: `state '${to}' has no gate definition` };

  if (ctx == null || typeof ctx !== 'object') return { ok: false, reason: 'missing context object' };

  // Evaluate the gate. `isReceipt` gates need artifact receipts, not flags.
  if (gate.isReceipt) {
    const receipt = ctx[gate.key];
    if (!receipt || typeof receipt !== 'object') return { ok: false, reason: `missing ${gate.label}` };
    if (gate.key === 'proofReceipt') {
      if (receipt.status !== 'pass') return { ok: false, reason: `proof-receipt must be status 'pass' (got '${receipt.status}')` };
    }
    if (gate.key === 'qaReports') {
      if (!(receipt.videoOk && receipt.audioOk)) return { ok: false, reason: 'video-qa and audio-qa must both be ok for qa-passed' };
    }
  } else if (gate.key === 'research') {
    if (!ctx.research || !ctx.research.ok) return { ok: false, reason: 'research.json must be present and valid' };
  } else if (gate.key === 'ownerSelection') {
    if (!ctx.ownerSelection) return { ok: false, reason: 'owner selection must be recorded' };
  } else if (gate.key === 'claimLedgerComplete') {
    if (!ctx.claimLedgerComplete) return { ok: false, reason: 'claims ledger must be complete and every line classified' };
  } else if (gate.key === 'story') {
    if (!ctx.story || !ctx.story.ok) return { ok: false, reason: 'story.json must be present and valid' };
  } else if (gate.key === 'proofPossible') {
    if (!ctx.proofPossible) return { ok: false, reason: 'an 8-12s proof must be possible before proof-pending' };
  } else if (gate.key === 'mix') {
    if (!ctx.mix || !ctx.mix.ok) return { ok: false, reason: 'mix lock must be recorded' };
  } else if (gate.key === 'ownerAccept') {
    if (!ctx.ownerAccept) return { ok: false, reason: 'owner sign-off — human action, not a tool' };
  } else if (gate.key === 'privateUploadReceipt') {
    if (!ctx.privateUploadReceipt?.receiptId) return { ok: false, reason: 'private upload receipt must be recorded' };
  }
  return { ok: true, reason: `ok → ${to}` };
}

/** Attempt a transition. Non-throwing: returns { ok, value | reason }. */
export function applyTransition(from, to, ctx = {}) {
  const check = canTransition(from, to, ctx);
  if (!check.ok) return { ok: false, reason: check.reason };
  return { ok: true, value: { state: to, gate: GATES[to]?.label ?? null }, reason: check.reason };
}

// Dependency DAG (doc's W): a change must re-run the affected scope only.
export const DAG = Object.freeze([
  { change: 'claim', scopes: ['script-review'] },
  { change: 'script', scopes: ['voice-caption-timing'] },
  { change: 'voice', scopes: ['captions-mix'] },
  { change: 'shot-plan', scopes: ['render-shots'] },
  { change: 'asset', scopes: ['shaders-frames'] },
  { change: 'mix', scopes: ['audio-qa'] },
  { change: 'thumbnail', scopes: ['packaging'] },
]);

/** Return the affected re-run scopes for a change, or null if unknown. */
export function affectedScopes(change) {
  const entry = DAG.find((d) => d.change === change);
  return entry ? [...entry.scopes] : null;
}

// The idea → published lifecycle for a production candidate.
// Rerun scope for any upstream change uses the DAG above, not the full film.
export const LIFECYCLE = STATES;
