// Pilot registry shared by the compositor and the render harness.
// Each pilot exports a timeline module (beats, clock, captions, progress
// curves) and a scene module ({ createScene, WORLD }).

import * as p1Timeline from './p1/timeline.js';
import { createScene as p1CreateScene, WORLD as p1World } from './p1/scene.js';
import * as e1Timeline from './e1/timeline.js';
import { createScene as e1CreateScene, WORLD as e1World } from './e1/scene.js';

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
    },
    timeline: e1Timeline,
    createScene: e1CreateScene,
    WORLD: e1World,
  },
});

export function getPilot(name) {
  const pilot = PILOTS[name ?? 'p1'];
  if (!pilot) throw new Error(`Unknown pilot '${name}' — use one of: ${Object.keys(PILOTS).join(', ')}`);
  return pilot;
}
