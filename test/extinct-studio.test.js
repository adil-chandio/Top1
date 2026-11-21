import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import {
  checkTransition,
  scoreIdea,
  scoreIdeas,
  selfCheck,
  validateAnalyticsDocument,
  validateProjectDirectory,
} from '../tools/extinct-studio/lib.mjs';

function tempProject(project = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'extinct-studio-'));
  fs.writeFileSync(path.join(directory, 'project.json'), JSON.stringify({
    schema_version: '1.0',
    project_id: 'NEW-001',
    channel: 'extinct',
    working_title: 'A new topic awaiting selection',
    format: 'both',
    language: 'english',
    status: 'idea',
    active_slate: true,
    historical_reference_only: false,
    ...project,
  }, null, 2));
  return directory;
}

function put(directory, name, value) {
  fs.writeFileSync(path.join(directory, name), JSON.stringify(value, null, 2));
}

test('the OS self-check keeps the state machine and idea weights internally consistent', () => {
  const result = selfCheck();
  assert.equal(result.ok, true);
  assert.equal(result.idea_weights.visual_proof, 20);
  assert.equal(result.states.at(-1), 'published');
});

test('idea scoring is a readiness gate, not a viral forecast', () => {
  const result = scoreIdea({
    id: 'idea-001',
    promise: 'Show one surprising extinct-animal mechanism with evidence',
    audience_clarity: 5,
    visual_proof: 5,
    novelty: 4,
    evidence_strength: 5,
    stakes: 4,
    format_fit: 5,
    rights: 5,
    feasibility: 4,
  });
  assert.equal(result.score, 94);
  assert.equal(result.eligible_for_owner_review, true);
  assert.match(result.note, /not a viral probability/);

  const blocked = scoreIdeas({ ideas: [{
    id: 'idea-002',
    promise: 'A claim',
    audience_clarity: 5,
    visual_proof: 5,
    novelty: 5,
    evidence_strength: 1,
    stakes: 5,
    format_fit: 5,
    rights: 2,
    feasibility: 5,
  }] });
  assert.equal(blocked[0].eligible_for_owner_review, false);
  assert.match(blocked[0].blocking_reasons.join(' '), /evidence|rights|vague/);
});

test('redacted Studio observations keep format and calendar age separate', () => {
  const result = validateAnalyticsDocument({
    schema_version: '1.0',
    project_id: 'NEW-001',
    platform: 'youtube',
    format: 'short',
    observed_on: '2026-11-21',
    age_days: 7,
    redacted: true,
    source: 'studio-export-redacted',
    metrics: { views: 1200, impressions: 30000, ctr: 0.04, average_percentage_viewed: 91.2 },
  });
  assert.equal(result.ok, true);

  const unsafe = validateAnalyticsDocument({
    schema_version: '1.0',
    project_id: 'NEW-001',
    platform: 'youtube',
    format: 'long',
    observed_on: '2026-11-21',
    age_days: 7,
    redacted: false,
    source: 'studio-export-redacted',
    metrics: { views: -1 },
  });
  assert.equal(unsafe.ok, false);
  assert.match(unsafe.errors.join(' '), /redacted|non-negative/);
});

test('an idea project validates without pretending that later gates passed', () => {
  const directory = tempProject();
  const result = validateProjectDirectory(directory);
  assert.equal(result.ok, true);
  assert.equal(result.state, 'idea');
  assert.equal(fs.existsSync(path.join(directory, 'release-status.json')), false);
});

test('release status cannot quietly schedule or publish a project', () => {
  const directory = tempProject();
  put(directory, 'release-status.json', {
    schema_version: '1.0',
    status: 'idea',
    writes_files: false,
    upload: 'not_started',
    schedule: 'owner_manual',
    publication: 'not_started',
  });
  const result = validateProjectDirectory(directory);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(' '), /schedule/);
});

test('historical material cannot be active slate material', () => {
  const directory = tempProject({ historical_reference_only: true, active_slate: true });
  const result = validateProjectDirectory(directory);
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /historical_reference_only/);
});

test('transition checks are sequential, read-only, and never publish', () => {
  const directory = tempProject();
  const next = checkTransition(directory, 'researched');
  assert.equal(next.ok, false);
  assert.match(next.errors.join('\n'), /research\.json/);
  assert.equal(next.writes_files, false);
  assert.equal(fs.readFileSync(path.join(directory, 'project.json'), 'utf8').includes('researched'), false);

  const publish = checkTransition(directory, 'published');
  assert.equal(publish.ok, false);
  assert.match(publish.errors.join('\n'), /owner-manual/);
  assert.equal(publish.publication_side_effect, false);
});

test('private Drive links and credentials are rejected from manifests', () => {
  const directory = tempProject();
  put(directory, 'research.json', {
    sources: [{
      id: 'source-1',
      kind: 'paper',
      url: 'https://drive.google.com/file/d/private/view',
      accessed_on: '2026-11-21',
      notes: 'not for a public manifest',
    }],
  });
  const result = validateProjectDirectory(directory, { stateOverride: 'researched' });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /private Drive\/Docs URL/);
});

test('proof gate rejects reused footage and a broken frame clock', () => {
  const directory = tempProject({ status: 'proof-passed' });
  put(directory, 'research.json', { sources: [{ id: 'paper-1', kind: 'paper', url: 'https://example.org/paper', accessed_on: '2026-11-21', notes: 'primary source' }] });
  put(directory, 'idea-score.json', { idea_id: 'idea-001', score: 85, eligible_for_owner_review: true, blocking_reasons: [] });
  put(directory, 'owner-decision.json', { decision: 'selected', owner: 'owner', decided_at: '2026-11-21', idea_id: 'idea-001' });
  put(directory, 'claims.json', { claims: [{ id: 'claim-1', text: 'A sourced claim', type: 'published', supporting_source_ids: ['paper-1'], status: 'verified', on_screen: true }] });
  put(directory, 'rights.json', { assets: [{ id: 'asset-1', kind: 'font', source: 'pinned repository', license: 'OFL-1.1', status: 'verified', used_in_output: true }] });
  put(directory, 'story.json', { hook_variants: [{ id: 'hook-a', text: 'A' }, { id: 'hook-b', text: 'B' }], chosen_hook_id: 'hook-a', beats: ['hook', 'proof', 'payoff'], caption_policy: { max_lines: 2 } });
  put(directory, 'proof-receipt.json', {
    status: 'pass',
    duration_s: 8,
    fps: 30,
    frames: 239,
    checks: { native_motion: true, mechanism_legible: true, phone_review: true, source_media_reused: true },
    human_review: { status: 'pass' },
  });
  const result = validateProjectDirectory(directory);
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /frames must equal|source media/);
});
