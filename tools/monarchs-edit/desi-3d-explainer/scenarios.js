// Pilot registry shared by the compositor and the render harness.
// Each pilot exports a timeline module (beats, clock, captions, progress
// curves) and a scene module ({ createScene, WORLD }).

import * as p1Timeline from './p1/timeline.js';
import { createScene as p1CreateScene, WORLD as p1World } from './p1/scene.js';
import * as e1Timeline from './e1/timeline.js';
import { createScene as e1CreateScene, WORLD as e1World } from './e1/scene.js';
import * as longTimeline from './long/timeline.js';
import { createScene as longCreateScene, WORLD as longWorld } from './long/scene.js';

// The layout/camera block is intentionally optional. Pilots that omit it
// (p1, e1) render exactly as before: the compositor falls back to its
// hardcoded 9:16 layout. The long pilot (16:9) defines both explicitly.

export const PILOTS = Object.freeze({
  p1: {
    id: 'p1',
    view: {
      tag: 'P1 · 3D EDIT',
      window: '38s · 9:16',
      labels: { left: 'METAL', right: 'LAKRI' },
      labelSub: { left: 'LEFT · LOW-MASS ICE', right: 'RIGHT · LOW-MASS ICE' },
      captionTitle: 'MONARCHs Edit',
      captionLine: 'Desi 3D explainer · everyday science, test-first',
      pixelClock: true,
      stillTimes: [2.5, 7.0, 9.5, 13.5, 23.0, 28.0, 36.0],
    },
    timeline: p1Timeline,
    createScene: p1CreateScene,
    WORLD: p1World,
  },
  e1: {
    id: 'e1',
    view: {
      tag: 'E1 · 3D EDIT',
      window: '38s · 9:16',
      labels: { left: 'METAL', right: 'LAKRI' },
      labelSub: { left: 'LEFT · SAME ROOM TEMP', right: 'RIGHT · SAME ROOM TEMP' },
      captionTitle: 'MONARCHs Edit',
      captionLine: 'Desi 3D explainer · everyday science, test-first',
      pixelClock: true,
      stillTimes: [2.5, 7.0, 9.5, 13.5, 23.0, 28.0, 36.0],
    },
    timeline: e1Timeline,
    createScene: e1CreateScene,
    WORLD: e1World,
  },
  long: {
    id: 'long',
    view: {
      tag: 'LONG · 3D EDIT',
      window: '92s · 16:9',
      labels: { left: 'METAL', right: 'LAKRI' },
      labelSub: { left: 'LEFT · METAL', right: 'RIGHT · LAKRI' },
      captionTitle: 'MONARCHs Edit',
      captionLine: 'Desi 3D explainer · long-form · everyday science, test-first',
      pixelClock: true,
      stillTimes: [2.5, 8, 14, 26, 46, 62, 82, 89],
      // Composed for the 16:9 frame. x and y are px at 1280×720; sizes are
      // CSS px. The compositor uses these instead of the 9:16 defaults.
      layout: {
        headerX: 56, headerY: 44, headerRightPad: 56,
        headerTitleFont: '700 20px Copy', headerSubFont: '500 13px Copy', headerTagFont: '600 16px Copy',
        badgeX: 56, badgeY: 92, badgeFont: '600 13px Copy',
        blocksLeftX: 359, blocksRightX: 922, blocksY: 402, blocksSubY: 428,
        blocksFont: '700 23px Title', blocksSubFont: '500 13px Copy',
        clockY: 524, clockSubY: 548, clockFont: '750 25px Title', clockSubFont: '600 14px Copy',
        timelapseY: 524, timelapseFont: '700 22px Title',
        questionY: 580, questionWrapFrac: 170, questionFont: '700 34px Title', questionLineHeight: 46,
        setupY: 582, setupWrapFrac: 150, setupFont: '620 27px Copy', setupLineHeight: 38,
        timelapseCaptionY: 582, timelapseWrapFrac: 170, timelapseFont: '600 25px Copy', timelapseLineHeight: 34,
        revealY: 568, revealWrapFrac: 150, revealFont: '700 32px Title', revealLineHeight: 44,
        revealDisclaimerY: 640, revealDisclaimerFont: '500 16px Copy',
        outroY: 596, outroSubY: 634, outroTitleFont: '750 33px Title', outroSubFont: '500 17px Copy',
        railLeft: 56, railY: 700,
        disclaimerText: 'Yeh ek illustrative model hai — yeh koi tested result nahi hai.',
      },
      camera: {
        fov: 38,
        from: [1.3, 2.55, 5.6],
        to: [0.28, 2.32, 5.05],
        lookAt: [0, 0.82, 0],
      },
    },
    timeline: longTimeline,
    createScene: longCreateScene,
    WORLD: longWorld,
  },
});

export function getPilot(name) {
  const pilot = PILOTS[name ?? 'p1'];
  if (!pilot) throw new Error(`Unknown pilot '${name}' — use one of: ${Object.keys(PILOTS).join(', ')}`);
  return pilot;
}
