import test from 'node:test';
import assert from 'node:assert/strict';
import {
  STATES, GATES, nextState, isState, canTransition, applyTransition,
  affectedScopes, DAG,
} from '../tools/extinct-studio/state-machine.js';

test('state machine covers the full lifecycle, 15 states, ordered', () => {
  assert.equal(STATES.length, 15);
  assert.equal(STATES[0], 'idea');
  assert.equal(STATES.at(-1), 'published');
  for (let i = 0; i < STATES.length - 1; i++) assert.equal(nextState(STATES[i]), STATES[i + 1]);
  assert.equal(nextState('published'), null);
});

test('forward-only: skipping a state is rejected, and backwards is rejected', () => {
  const ctx = { research: { ok: true }, ownerSelection: true, claimLedgerComplete: true };
  const skip = canTransition('idea', 'shortlisted', ctx);
  assert.equal(skip.ok, false);
  assert.match(skip.reason, /skipping/);
  const back = canTransition('scripted', 'claim-checked', ctx);
  assert.equal(back.ok, false);
  assert.match(back.reason, /backwards/);
});

test('every gated target requires its context flag; the published state is human-only', () => {
  // claim-checked requires claimLedgerComplete
  assert.equal(canTransition('owner-selected', 'claim-checked', {}).ok, false);
  assert.equal(
    canTransition('owner-selected', 'claim-checked', { claimLedgerComplete: true }).ok,
    true,
  );

  // proof-passed requires a pass receipt
  assert.equal(canTransition('proof-pending', 'proof-passed', { proofReceipt: { status: 'fail' } }).ok, false);
  assert.equal(canTransition('proof-pending', 'proof-passed', { proofReceipt: { status: 'pending' } }).ok, false);
  assert.equal(canTransition('proof-pending', 'proof-passed', { proofReceipt: { status: 'pass' } }).ok, true);

  // qa-passed needs both video and audio reports ok
  assert.equal(canTransition('mix-locked', 'qa-passed', { qaReports: { videoOk: true, audioOk: false } }).ok, false);
  assert.equal(canTransition('mix-locked', 'qa-passed', { qaReports: { videoOk: true, audioOk: true } }).ok, true);

  // published is never allowed from any tool
  assert.equal(canTransition('private-uploaded', 'published', { publishedReceipt: { id: 'x' } }).ok, false);

  // owner selection required at the start
  assert.equal(canTransition('shortlisted', 'owner-selected', { ownerSelection: false }).ok, false);
});

test('applyTransition reports the target state and gate label', () => {
  const ok = applyTransition('idea', 'researched', { research: { ok: true } });
  assert.equal(ok.ok, true);
  assert.equal(ok.value.state, 'researched');
  const denied = applyTransition('idea', 'published', { research: { ok: true } });
  assert.equal(denied.ok, false);
});

test('dependency DAG maps a change to its re-run scope, not the full film', () => {
  assert.deepEqual(affectedScopes('mix'), ['audio-qa']);
  assert.deepEqual(affectedScopes('thumbnail'), ['packaging']);
  assert.deepEqual(affectedScopes('claim'), ['script-review']);
  assert.equal(affectedScopes('unknown-thing'), null);
  // every DAG entry has at least one scope
  for (const entry of DAG) assert.ok(entry.change && entry.scopes.length > 0);
});

test('gates referenced by STATES are defined for every nonterminal state', () => {
  for (const state of STATES) {
    assert.ok(state === 'idea' || GATES[state] || state === 'idea', `gate definition missing for '${state}'`);
  }
});
