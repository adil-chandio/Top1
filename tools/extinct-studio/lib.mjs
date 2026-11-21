import fs from 'node:fs';
import path from 'node:path';

export const SCHEMA_VERSION = '1.0';

export const STATES = Object.freeze([
  'idea',
  'researched',
  'shortlisted',
  'owner-selected',
  'claims-locked',
  'scripted',
  'proof-pending',
  'proof-passed',
  'voice-locked',
  'picture-locked',
  'mix-locked',
  'qa-passed',
  'owner-accepted',
  'private-uploaded',
  'published',
]);

export const IDEA_WEIGHTS = Object.freeze({
  audience_clarity: 20,
  visual_proof: 20,
  novelty: 15,
  evidence_strength: 15,
  stakes: 10,
  format_fit: 10,
  rights: 5,
  feasibility: 5,
});

const REQUIRED_PROOF_CHECKS = Object.freeze([
  'native_motion',
  'mechanism_legible',
  'phone_review',
  'source_media_reused',
]);

const REQUIRED_FILES = Object.freeze([
  [1, 'research.json'],
  [2, 'idea-score.json'],
  [3, 'owner-decision.json'],
  [4, 'claims.json'],
  [4, 'rights.json'],
  [5, 'story.json'],
  [6, 'proof-receipt.json'],
  [8, 'voice-lock.json'],
  [9, 'render-manifest.json'],
  [10, 'audio-qa.json'],
  [11, 'video-qa.json'],
  [12, 'owner-signoff.json'],
  [13, 'studio-receipt.json'],
  [14, 'publication-receipt.json'],
]);

const PRIVATE_DRIVE_URL = /https?:\/\/(?:drive\.google\.com|docs\.google\.com)\//i;
const SECRET_VALUE = /(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|ya29\.|AIza[0-9A-Za-z_-]{20,}|gh[pousr]_[0-9A-Za-z_]+|access_token\s*[:=])/i;

function indexOfState(state) {
  return STATES.indexOf(state);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function readJsonFile(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    const suffix = error instanceof SyntaxError ? `invalid JSON: ${error.message}` : error.message;
    throw new Error(`${file}: ${suffix}`);
  }
}

function hasFile(root, name) {
  return fs.existsSync(path.join(root, name));
}

function loadOptional(root, name, report) {
  const file = path.join(root, name);
  if (!fs.existsSync(file)) return null;
  try {
    const value = readJsonFile(file);
    report.documents[name] = value;
    return value;
  } catch (error) {
    report.errors.push(error.message);
    return null;
  }
}

function addError(report, message) {
  report.errors.push(message);
}

function addWarning(report, message) {
  report.warnings.push(message);
}

function requireString(value, label, report) {
  if (typeof value !== 'string' || value.trim() === '') {
    addError(report, `${label} must be a non-empty string`);
    return false;
  }
  return true;
}

function requireBoolean(value, label, report) {
  if (typeof value !== 'boolean') {
    addError(report, `${label} must be boolean`);
    return false;
  }
  return true;
}

function requireNumber(value, label, report, { min = -Infinity, max = Infinity } = {}) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max) {
    addError(report, `${label} must be a finite number between ${min} and ${max}`);
    return false;
  }
  return true;
}

function scanSensitiveValues(value, pointer, report) {
  if (typeof value === 'string') {
    if (PRIVATE_DRIVE_URL.test(value)) {
      addError(report, `${pointer || 'document'} contains a private Drive/Docs URL; store a redacted source ID and access receipt instead`);
    }
    if (SECRET_VALUE.test(value)) {
      addError(report, `${pointer || 'document'} looks like it contains a credential or private key`);
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => scanSensitiveValues(item, `${pointer}[${index}]`, report));
    return;
  }
  if (isObject(value)) {
    Object.entries(value).forEach(([key, item]) => scanSensitiveValues(item, `${pointer}.${key}`, report));
  }
}

function validateProject(project, report) {
  if (!isObject(project)) {
    addError(report, 'project.json must contain an object');
    return;
  }
  requireString(project.schema_version, 'project.schema_version', report);
  if (project.schema_version !== SCHEMA_VERSION) addError(report, `project.schema_version must be ${SCHEMA_VERSION}`);
  requireString(project.project_id, 'project.project_id', report);
  requireString(project.channel, 'project.channel', report);
  requireString(project.working_title, 'project.working_title', report);
  if (!['short', 'long', 'both'].includes(project.format)) addError(report, 'project.format must be short, long, or both');
  if (!['english', 'urdu', 'roman-urdu', 'mixed'].includes(project.language)) addError(report, 'project.language is not supported');
  if (!STATES.includes(project.status)) addError(report, `project.status must be one of: ${STATES.join(', ')}`);
  requireBoolean(project.active_slate, 'project.active_slate', report);
  requireBoolean(project.historical_reference_only, 'project.historical_reference_only', report);
  if (project.active_slate === true && project.historical_reference_only === true) {
    addError(report, 'historical_reference_only projects cannot be active_slate projects');
  }
  if (project.channel !== 'extinct') addWarning(report, 'project.channel is not "extinct"; confirm this is intentional before using the Extinct Studio OS');
}

function validateResearch(research, report) {
  if (!isObject(research)) {
    addError(report, 'research.json must contain an object');
    return;
  }
  if (!Array.isArray(research.sources) || research.sources.length === 0) {
    addError(report, 'research.sources must contain at least one source');
    return;
  }
  const ids = new Set();
  research.sources.forEach((source, index) => {
    const label = `research.sources[${index}]`;
    if (!isObject(source)) {
      addError(report, `${label} must be an object`);
      return;
    }
    requireString(source.id, `${label}.id`, report);
    if (ids.has(source.id)) addError(report, `${label}.id is duplicated: ${source.id}`);
    ids.add(source.id);
    requireString(source.kind, `${label}.kind`, report);
    if (source.url !== undefined) requireString(source.url, `${label}.url`, report);
    if (source.accessed_on !== undefined) requireString(source.accessed_on, `${label}.accessed_on`, report);
    if (source.notes !== undefined) requireString(source.notes, `${label}.notes`, report);
  });
  report.sourceIds = ids;
}

function validateIdeaScore(score, report) {
  if (!isObject(score)) {
    addError(report, 'idea-score.json must contain an object');
    return;
  }
  requireString(score.idea_id, 'idea-score.idea_id', report);
  requireNumber(score.score, 'idea-score.score', report, { min: 0, max: 100 });
  if (typeof score.eligible_for_owner_review !== 'boolean') addError(report, 'idea-score.eligible_for_owner_review must be boolean');
  if (score.score >= 80 && score.eligible_for_owner_review !== true) addError(report, 'an idea scoring 80 or higher must be eligible_for_owner_review');
  if (score.score < 80 && score.eligible_for_owner_review === true) addError(report, 'an idea below 80 cannot be eligible_for_owner_review');
  if (!Array.isArray(score.blocking_reasons)) addError(report, 'idea-score.blocking_reasons must be an array');
}

function validateOwnerDecision(decision, report) {
  if (!isObject(decision)) {
    addError(report, 'owner-decision.json must contain an object');
    return;
  }
  if (decision.decision !== 'selected') addError(report, 'owner-decision.decision must be selected before production');
  requireString(decision.owner, 'owner-decision.owner', report);
  requireString(decision.decided_at, 'owner-decision.decided_at', report);
  requireString(decision.idea_id, 'owner-decision.idea_id', report);
}

function validateClaims(claims, sourceIds, report, targetIndex) {
  if (!isObject(claims)) {
    addError(report, 'claims.json must contain an object');
    return;
  }
  if (!Array.isArray(claims.claims) || claims.claims.length === 0) {
    addError(report, 'claims.claims must contain at least one claim');
    return;
  }
  const ids = new Set();
  claims.claims.forEach((claim, index) => {
    const label = `claims.claims[${index}]`;
    if (!isObject(claim)) {
      addError(report, `${label} must be an object`);
      return;
    }
    requireString(claim.id, `${label}.id`, report);
    if (ids.has(claim.id)) addError(report, `${label}.id is duplicated: ${claim.id}`);
    ids.add(claim.id);
    requireString(claim.text, `${label}.text`, report);
    if (!['observed', 'measured', 'published', 'derived', 'modelled', 'illustrative', 'hypothesis', 'limitation'].includes(claim.type)) {
      addError(report, `${label}.type is not a supported claim type`);
    }
    if (!Array.isArray(claim.supporting_source_ids)) addError(report, `${label}.supporting_source_ids must be an array`);
    else claim.supporting_source_ids.forEach((sourceId) => {
      if (!sourceIds?.has(sourceId)) addError(report, `${label} refers to missing source ${sourceId}`);
    });
    if (!['draft', 'verified', 'rejected'].includes(claim.status)) addError(report, `${label}.status must be draft, verified, or rejected`);
    if (typeof claim.on_screen !== 'boolean') addError(report, `${label}.on_screen must be boolean`);
    if (targetIndex >= indexOfState('claims-locked') && claim.on_screen === true && claim.status !== 'verified') {
      addError(report, `${label} is on-screen but is not verified`);
    }
    if (claim.type === 'illustrative' && claim.status === 'verified' && !claim.limitation) {
      addError(report, `${label} is illustrative and needs an explicit limitation`);
    }
  });
}

function validateRights(rights, report, targetIndex) {
  if (!isObject(rights)) {
    addError(report, 'rights.json must contain an object');
    return;
  }
  if (!Array.isArray(rights.assets)) {
    addError(report, 'rights.assets must be an array');
    return;
  }
  const ids = new Set();
  rights.assets.forEach((asset, index) => {
    const label = `rights.assets[${index}]`;
    if (!isObject(asset)) {
      addError(report, `${label} must be an object`);
      return;
    }
    requireString(asset.id, `${label}.id`, report);
    if (ids.has(asset.id)) addError(report, `${label}.id is duplicated: ${asset.id}`);
    ids.add(asset.id);
    requireString(asset.kind, `${label}.kind`, report);
    requireString(asset.source, `${label}.source`, report);
    requireString(asset.license, `${label}.license`, report);
    if (!['verified', 'pending', 'rejected'].includes(asset.status)) addError(report, `${label}.status must be verified, pending, or rejected`);
    if (typeof asset.used_in_output !== 'boolean') addError(report, `${label}.used_in_output must be boolean`);
    if (targetIndex >= indexOfState('claims-locked') && asset.used_in_output === true && asset.status !== 'verified') {
      addError(report, `${label} is used in output but its rights status is not verified`);
    }
    if (targetIndex >= indexOfState('claims-locked') && asset.license.toLowerCase() === 'unknown') {
      addError(report, `${label} has an unknown license`);
    }
  });
}

function validateStory(story, report) {
  if (!isObject(story)) {
    addError(report, 'story.json must contain an object');
    return;
  }
  if (!Array.isArray(story.hook_variants) || story.hook_variants.length < 2) {
    addError(report, 'story.hook_variants must contain at least two alternatives before script lock');
  }
  requireString(story.chosen_hook_id, 'story.chosen_hook_id', report);
  if (!Array.isArray(story.beats) || story.beats.length < 3) addError(report, 'story.beats must contain at least three beats');
  if (!isObject(story.caption_policy)) addError(report, 'story.caption_policy must be an object');
}

function validateProof(proof, report, targetIndex) {
  if (!isObject(proof)) {
    addError(report, 'proof-receipt.json must contain an object');
    return;
  }
  if (!['pending', 'pass', 'fail'].includes(proof.status)) addError(report, 'proof-receipt.status must be pending, pass, or fail');
  if (targetIndex >= indexOfState('proof-passed') && proof.status !== 'pass') addError(report, 'proof-passed requires proof-receipt.status=pass');
  requireNumber(proof.duration_s, 'proof-receipt.duration_s', report, { min: 8, max: 12 });
  requireNumber(proof.fps, 'proof-receipt.fps', report, { min: 1, max: 240 });
  requireNumber(proof.frames, 'proof-receipt.frames', report, { min: 1 });
  if (Number.isFinite(proof.duration_s) && Number.isFinite(proof.fps) && Number.isFinite(proof.frames)) {
    const expected = Math.round(proof.duration_s * proof.fps);
    if (proof.frames !== expected) addError(report, `proof-receipt.frames must equal rounded duration × fps (${expected})`);
  }
  if (!isObject(proof.checks)) addError(report, 'proof-receipt.checks must be an object');
  else REQUIRED_PROOF_CHECKS.forEach((key) => {
    if (typeof proof.checks[key] !== 'boolean') addError(report, `proof-receipt.checks.${key} must be boolean`);
    if (key === 'source_media_reused' && proof.checks[key] === true) addError(report, 'proof may not reuse third-party source media as production footage');
    if (targetIndex >= indexOfState('proof-passed') && proof.checks[key] !== (key === 'source_media_reused' ? false : true)) {
      addError(report, `proof-receipt.checks.${key} has not passed`);
    }
  });
  if (!isObject(proof.human_review) || proof.human_review.status !== 'pass') addError(report, 'proof-receipt.human_review.status must be pass');
}

function validateVoice(voice, report) {
  if (!isObject(voice)) {
    addError(report, 'voice-lock.json must contain an object');
    return;
  }
  requireString(voice.voice_id, 'voice-lock.voice_id', report);
  requireString(voice.narration_sha256, 'voice-lock.narration_sha256', report);
  if (voice.consent_status !== 'verified') addError(report, 'voice-lock.consent_status must be verified');
  if (voice.caption_source !== 'locked-narration') addError(report, 'voice-lock.caption_source must be locked-narration');
}

function validateRenderManifest(manifest, report) {
  if (!isObject(manifest)) {
    addError(report, 'render-manifest.json must contain an object');
    return;
  }
  requireString(manifest.renderer, 'render-manifest.renderer', report);
  requireString(manifest.renderer_sha256, 'render-manifest.renderer_sha256', report);
  requireString(manifest.shot_plan_sha256, 'render-manifest.shot_plan_sha256', report);
  if (manifest.source_media_reused !== false) addError(report, 'render-manifest.source_media_reused must be false');
  requireNumber(manifest.fps, 'render-manifest.fps', report, { min: 1, max: 240 });
  if (!Array.isArray(manifest.resolution) || manifest.resolution.length !== 2 || !manifest.resolution.every((n) => Number.isInteger(n) && n > 0)) {
    addError(report, 'render-manifest.resolution must be [width, height]');
  }
}

function validateAudio(audio, report) {
  if (!isObject(audio)) {
    addError(report, 'audio-qa.json must contain an object');
    return;
  }
  if (audio.status !== 'pass') addError(report, 'audio-qa.status must be pass');
  requireNumber(audio.lufs_i, 'audio-qa.lufs_i', report, { min: -60, max: 0 });
  requireNumber(audio.true_peak_dbtp, 'audio-qa.true_peak_dbtp', report, { min: -60, max: 0 });
  if (audio.clipping !== false) addError(report, 'audio-qa.clipping must be false');
  if (audio.dialogue_masking !== false) addError(report, 'audio-qa.dialogue_masking must be false');
  if (audio.phone_review !== true) addError(report, 'audio-qa.phone_review must be true');
}

function validateVideo(video, report) {
  if (!isObject(video)) {
    addError(report, 'video-qa.json must contain an object');
    return;
  }
  if (video.status !== 'pass') addError(report, 'video-qa.status must be pass');
  if (video.decoded !== true) addError(report, 'video-qa.decoded must be true');
  requireNumber(video.frames, 'video-qa.frames', report, { min: 1 });
  requireNumber(video.fps, 'video-qa.fps', report, { min: 1, max: 240 });
  requireString(video.sha256, 'video-qa.sha256', report);
  if (video.captions_ok !== true) addError(report, 'video-qa.captions_ok must be true');
  if (video.visual_review !== 'pass') addError(report, 'video-qa.visual_review must be pass');
  if (video.audio_review !== 'pass') addError(report, 'video-qa.audio_review must be pass');
}

function validateOwnerSignoff(signoff, report) {
  if (!isObject(signoff)) {
    addError(report, 'owner-signoff.json must contain an object');
    return;
  }
  if (signoff.status !== 'accepted') addError(report, 'owner-signoff.status must be accepted');
  requireString(signoff.owner, 'owner-signoff.owner', report);
  requireString(signoff.accepted_at, 'owner-signoff.accepted_at', report);
  if (!Array.isArray(signoff.scope) || signoff.scope.length === 0) addError(report, 'owner-signoff.scope must list what was accepted');
}

function validateStudioReceipt(receipt, report) {
  if (!isObject(receipt)) {
    addError(report, 'studio-receipt.json must contain an object');
    return;
  }
  if (receipt.visibility !== 'private') addError(report, 'studio-receipt.visibility must be private');
  requireString(receipt.upload_sha256, 'studio-receipt.upload_sha256', report);
  requireString(receipt.uploaded_at, 'studio-receipt.uploaded_at', report);
  requireString(receipt.uploaded_by, 'studio-receipt.uploaded_by', report);
  if (receipt.scheduled !== false) addError(report, 'studio-receipt.scheduled must be false until an owner explicitly changes it');
}

function validatePublicationReceipt(receipt, report) {
  if (!isObject(receipt)) {
    addError(report, 'publication-receipt.json must contain an object');
    return;
  }
  if (receipt.method !== 'owner_manual') addError(report, 'publication-receipt.method must be owner_manual');
  requireString(receipt.owner, 'publication-receipt.owner', report);
  requireString(receipt.published_at, 'publication-receipt.published_at', report);
}

function validateReleaseStatus(release, report, projectStatus, stateOverride) {
  if (!isObject(release)) {
    addError(report, 'release-status.json must contain an object');
    return;
  }
  requireString(release.schema_version, 'release-status.schema_version', report);
  if (release.schema_version !== SCHEMA_VERSION) addError(report, `release-status.schema_version must be ${SCHEMA_VERSION}`);
  if (!STATES.includes(release.status)) addError(report, `release-status.status must be one of: ${STATES.join(', ')}`);
  if (!stateOverride && release.status !== projectStatus) addError(report, 'release-status.status and project.status must match');
  if (release.writes_files !== false) addError(report, 'release-status.writes_files must be false');
  if (!['not_started', 'private_only', 'owner_manual'].includes(release.upload)) addError(report, 'release-status.upload is invalid');
  if (!['not_started', 'owner_manual'].includes(release.schedule)) addError(report, 'release-status.schedule is invalid');
  if (!['not_started', 'owner_manual'].includes(release.publication)) addError(report, 'release-status.publication is invalid');
  if (release.status !== 'published' && release.publication !== 'not_started') addError(report, 'publication must remain not_started before published');
  if (!['private-uploaded', 'published'].includes(release.status) && release.schedule !== 'not_started') addError(report, 'schedule must remain not_started before private handoff');
  if (release.status !== 'private-uploaded' && release.upload === 'private_only') addError(report, 'private_only upload requires private-uploaded state');
}

function validateStageDocuments(root, targetIndex, report) {
  for (const [minimumIndex, name] of REQUIRED_FILES) {
    if (targetIndex >= minimumIndex && !hasFile(root, name)) addError(report, `${name} is required for state ${STATES[targetIndex]}`);
  }

  const research = report.documents['research.json'];
  const sourceIds = new Set(research?.sources?.map((source) => source.id).filter(Boolean) ?? []);
  if (targetIndex >= indexOfState('researched') && research) validateResearch(research, report);
  if (targetIndex >= indexOfState('shortlisted')) validateIdeaScore(report.documents['idea-score.json'], report);
  if (targetIndex >= indexOfState('owner-selected')) validateOwnerDecision(report.documents['owner-decision.json'], report);
  if (targetIndex >= indexOfState('claims-locked')) {
    validateClaims(report.documents['claims.json'], sourceIds, report, targetIndex);
    validateRights(report.documents['rights.json'], report, targetIndex);
  }
  if (targetIndex >= indexOfState('scripted')) validateStory(report.documents['story.json'], report);
  if (targetIndex >= indexOfState('proof-pending')) validateProof(report.documents['proof-receipt.json'], report, targetIndex);
  if (targetIndex >= indexOfState('voice-locked')) validateVoice(report.documents['voice-lock.json'], report);
  if (targetIndex >= indexOfState('picture-locked')) validateRenderManifest(report.documents['render-manifest.json'], report);
  if (targetIndex >= indexOfState('mix-locked')) validateAudio(report.documents['audio-qa.json'], report);
  if (targetIndex >= indexOfState('qa-passed')) validateVideo(report.documents['video-qa.json'], report);
  if (targetIndex >= indexOfState('owner-accepted')) validateOwnerSignoff(report.documents['owner-signoff.json'], report);
  if (targetIndex >= indexOfState('private-uploaded')) validateStudioReceipt(report.documents['studio-receipt.json'], report);
  if (targetIndex >= indexOfState('published')) validatePublicationReceipt(report.documents['publication-receipt.json'], report);
}

export function validateProjectDirectory(directory, { stateOverride = null } = {}) {
  const root = path.resolve(directory);
  const report = {
    ok: false,
    root,
    errors: [],
    warnings: [],
    documents: {},
    state: null,
    sourceIds: new Set(),
  };
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    addError(report, `project directory does not exist: ${root}`);
    return finalizeReport(report);
  }
  const project = loadOptional(root, 'project.json', report);
  if (!project) addError(report, 'project.json is required');
  validateProject(project, report);
  const currentState = project?.status;
  const targetState = stateOverride ?? currentState;
  if (!STATES.includes(targetState)) addError(report, `unknown project state: ${targetState}`);
  report.state = targetState;
  if (project && hasFile(root, 'release-status.json')) {
    const release = loadOptional(root, 'release-status.json', report);
    if (release) validateReleaseStatus(release, report, project.status, stateOverride);
  }
  for (const name of ['research.json', 'idea-score.json', 'owner-decision.json', 'claims.json', 'rights.json', 'story.json', 'proof-receipt.json', 'voice-lock.json', 'render-manifest.json', 'audio-qa.json', 'video-qa.json', 'owner-signoff.json', 'studio-receipt.json', 'publication-receipt.json']) {
    if (hasFile(root, name) && !report.documents[name]) loadOptional(root, name, report);
  }
  Object.entries(report.documents).forEach(([name, document]) => scanSensitiveValues(document, name, report));
  if (STATES.includes(targetState)) validateStageDocuments(root, indexOfState(targetState), report);
  return finalizeReport(report);
}

function finalizeReport(report) {
  report.ok = report.errors.length === 0;
  report.error_count = report.errors.length;
  report.warning_count = report.warnings.length;
  delete report.sourceIds;
  return report;
}

export function scoreIdea(idea) {
  if (!isObject(idea)) throw new Error('idea must be an object');
  requireString(idea.id, 'idea.id', { errors: [] });
  requireString(idea.promise, 'idea.promise', { errors: [] });
  const blockingReasons = [];
  let score = 0;
  for (const [dimension, weight] of Object.entries(IDEA_WEIGHTS)) {
    const rating = idea[dimension];
    if (!Number.isInteger(rating) || rating < 0 || rating > 5) throw new Error(`idea.${dimension} must be an integer from 0 to 5`);
    score += (rating / 5) * weight;
  }
  if (typeof idea.id !== 'string' || idea.id.trim() === '') blockingReasons.push('missing idea id');
  if (typeof idea.promise !== 'string' || idea.promise.trim().length < 12) blockingReasons.push('viewer promise is too vague or short');
  if (idea.evidence_strength < 3) blockingReasons.push('evidence strength is below the minimum');
  if (idea.visual_proof < 3) blockingReasons.push('visual proof is below the minimum');
  if (idea.rights < 4) blockingReasons.push('rights certainty is not high enough');
  score = Math.round(score * 10) / 10;
  const eligible = score >= 80 && blockingReasons.length === 0;
  return {
    id: idea.id,
    promise: idea.promise,
    score,
    eligible_for_owner_review: eligible,
    decision: eligible ? 'owner-review' : 'revise-or-kill',
    blocking_reasons: blockingReasons,
    note: 'This is an editorial readiness score, not a viral probability or view forecast.',
  };
}

export function scoreIdeas(payload) {
  if (!isObject(payload) || !Array.isArray(payload.ideas)) throw new Error('ideas file must contain an ideas array');
  return payload.ideas.map(scoreIdea).sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
}

export function checkTransition(directory, targetState) {
  const current = validateProjectDirectory(directory);
  const result = {
    ok: false,
    from: current.documents['project.json']?.status ?? null,
    to: targetState,
    errors: [...current.errors],
    warnings: [...current.warnings],
    writes_files: false,
    publication_side_effect: false,
  };
  if (!STATES.includes(targetState)) {
    result.errors.push(`unknown target state: ${targetState}`);
    return result;
  }
  if (targetState === 'published') {
    result.errors.push('published is owner-manual only; this tool never transitions or publishes a project');
    return result;
  }
  const fromIndex = indexOfState(result.from);
  const toIndex = indexOfState(targetState);
  if (fromIndex < 0) result.errors.push(`current state is invalid: ${result.from}`);
  else if (toIndex !== fromIndex + 1) result.errors.push(`only the next sequential state is allowed (${STATES[fromIndex + 1] ?? 'none'})`);
  const targetReport = validateProjectDirectory(directory, { stateOverride: targetState });
  result.errors.push(...targetReport.errors);
  result.warnings.push(...targetReport.warnings);
  result.ok = result.errors.length === 0;
  return result;
}

export function validateAnalyticsDocument(document) {
  const report = { ok: false, errors: [], warnings: [] };
  if (!isObject(document)) {
    report.errors.push('analytics document must contain an object');
    return report;
  }
  requireString(document.schema_version, 'analytics.schema_version', report);
  if (document.schema_version !== SCHEMA_VERSION) report.errors.push(`analytics.schema_version must be ${SCHEMA_VERSION}`);
  requireString(document.project_id, 'analytics.project_id', report);
  if (document.platform !== 'youtube') report.errors.push('analytics.platform must be youtube');
  if (!['short', 'long'].includes(document.format)) report.errors.push('analytics.format must be short or long');
  requireString(document.observed_on, 'analytics.observed_on', report);
  if (!Number.isInteger(document.age_days) || document.age_days < 0) report.errors.push('analytics.age_days must be a non-negative integer');
  if (document.redacted !== true) report.errors.push('analytics.redacted must be true; raw viewer-level data is not accepted');
  if (document.source !== 'studio-export-redacted') report.errors.push('analytics.source must be studio-export-redacted');
  if (!isObject(document.metrics)) report.errors.push('analytics.metrics must be an object');
  else {
    const integerMetrics = ['views', 'impressions', 'shares', 'comments', 'subscribers_gained'];
    integerMetrics.forEach((key) => {
      if (document.metrics[key] !== undefined && (!Number.isInteger(document.metrics[key]) || document.metrics[key] < 0)) {
        report.errors.push(`analytics.metrics.${key} must be a non-negative integer`);
      }
    });
    if (document.metrics.ctr !== undefined) requireNumber(document.metrics.ctr, 'analytics.metrics.ctr', report, { min: 0, max: 1 });
    if (document.metrics.average_percentage_viewed !== undefined) requireNumber(document.metrics.average_percentage_viewed, 'analytics.metrics.average_percentage_viewed', report, { min: 0, max: 100 });
    if (document.metrics.average_view_duration_s !== undefined) requireNumber(document.metrics.average_view_duration_s, 'analytics.metrics.average_view_duration_s', report, { min: 0 });
    if (document.metrics.viewed_vs_swiped_away !== undefined && !isObject(document.metrics.viewed_vs_swiped_away)) {
      report.errors.push('analytics.metrics.viewed_vs_swiped_away must be an object when supplied');
    }
  }
  scanSensitiveValues(document, 'analytics', report);
  report.ok = report.errors.length === 0;
  report.error_count = report.errors.length;
  report.warning_count = report.warnings.length;
  return report;
}

export function selfCheck() {
  const errors = [];
  if (new Set(STATES).size !== STATES.length) errors.push('state list contains duplicates');
  const weightTotal = Object.values(IDEA_WEIGHTS).reduce((sum, weight) => sum + weight, 0);
  if (weightTotal !== 100) errors.push(`idea weights total ${weightTotal}, expected 100`);
  if (!REQUIRED_PROOF_CHECKS.includes('source_media_reused')) errors.push('proof policy must include source_media_reused');
  return { ok: errors.length === 0, errors, states: STATES, idea_weights: IDEA_WEIGHTS, schema_version: SCHEMA_VERSION };
}
