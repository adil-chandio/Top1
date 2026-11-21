// Extinct Studio OS — automated QA skeleton (honest reporting).
//
// The doc's Q — Quality assurance list: frame count, FPS, black frames,
// duplicate frames, freeze frames, dropped frames, color range, audio/video
// duration, clipping, caption overflow, safe area, OCR readability, scene-
// change continuity, visual diff against approved boards, phone-size playback.
//
// The skeleton is honest by construction: it never claims a check passed.
// Every check comes back 'unavailable' with a reason when the probe cannot
// run in the environment. Real probe results are injected by the caller via
// `probeOverrides`; the skeleton never invents them.

export const VIDEO_QA_ITEMS = Object.freeze([
  { id: 'frame-count', label: 'Frame count' },
  { id: 'fps', label: 'FPS' },
  { id: 'black-frames', label: 'Black frames' },
  { id: 'duplicate-frames', label: 'Duplicate frames' },
  { id: 'freeze-frames', label: 'Freeze frames' },
  { id: 'dropped-frames', label: 'Dropped frames' },
  { id: 'color-range', label: 'Color range' },
  { id: 'duration-audio-video', label: 'Audio/video durations' },
  { id: 'clipping', label: 'Audio clipping' },
  { id: 'caption-overflow', label: 'Caption overflow' },
  { id: 'safe-area', label: 'Safe area' },
  { id: 'ocr-readability', label: 'OCR readability' },
  { id: 'scene-change-continuity', label: 'Scene-change continuity' },
  { id: 'visual-diff', label: 'Visual diff vs approved boards' },
  { id: 'phone-size-playback', label: 'Phone-size playback' },
]);

export const AUDIO_QA_ITEMS = Object.freeze([
  { id: 'lufs', label: 'LUFS' },
  { id: 'true-peak', label: 'True peak' },
  { id: 'aac-re-encode', label: 'AAC re-encode check' },
  { id: 'mono-compatibility', label: 'Mono compatibility' },
  { id: 'phone-speaker-review', label: 'Phone speaker review' },
]);

/**
 * Build the honest QA report.
 * @param {object} input
 * @param {string} [input.projectId]
 * @param {string} [input.generatedAt]
 * @param {object} [input.probeOverrides] - { checkId: { status, reason?, observed? } }
 * @returns the honest report
 */
export function runSkeleton({ projectId, generatedAt, probeOverrides } = {}) {
  const stamp = generatedAt ?? new Date().toISOString();
  const probe = probeOverrides ?? {};

  const run = (items) => items.map((item) => {
    const override = probe[item.id];
    if (override && ['ok', 'fail', 'pending'].includes(override.status)) {
      return {
        id: item.id,
        label: item.label,
        status: override.status,
        reason: override.reason ?? null,
        observed: override.observed ?? null,
      };
    }
    return {
      id: item.id,
      label: item.label,
      status: 'unavailable',
      reason: 'no probe available in this environment (no media file / no decoder)',
      observed: null,
    };
  });

  const video = run(VIDEO_QA_ITEMS);
  const audio = run(AUDIO_QA_ITEMS);

  const all = [...video, ...audio];
  const tally = {
    total: all.length,
    ok: all.filter((c) => c.status === 'ok').length,
    fail: all.filter((c) => c.status === 'fail').length,
    unavailable: all.filter((c) => c.status === 'unavailable').length,
    pending: all.filter((c) => c.status === 'pending').length,
  };

  return {
    projectId: projectId ?? null,
    generatedAt: stamp,
    video,
    audio,
    overall: tally,
    qaPasses: video.every((c) => c.status === 'ok') && audio.every((c) => c.status === 'ok'),
    honestyNote: 'No render, media decode or audio probe has run. Every check is reported as unavailable until a real probe returns ' +
      'ok/fail for it. This skeleton is not a QA pass.',
  };
}

/** Summarize a report into the receipt shape the state machine's qa-passed gate needs. */
export function toGateReceipt(report) {
  const all = [...report.video, ...report.audio];
  return {
    videoOk: report.video.every((c) => c.status === 'ok'),
    audioOk: report.audio.every((c) => c.status === 'ok'),
    unchecked: all.filter((c) => c.status !== 'ok').map((c) => c.id),
  };
}

// Quick re-export of the item lists (useful for callers that only want the check names).
export const ALL_QA_ITEMS = Object.freeze([...VIDEO_QA_ITEMS, ...AUDIO_QA_ITEMS]);

export default { runSkeleton, toGateReceipt, VIDEO_QA_ITEMS, AUDIO_QA_ITEMS, ALL_QA_ITEMS };
