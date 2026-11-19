import { AIR_CRUSH } from './air-crush.js';
import { REFLECTOR } from './reflector.js';

export const DEMOS = [
  AIR_CRUSH,
  {
    id: 'phone-storage',
    number: '01',
    title: 'The Phone Storage Trap',
    category: '3D EXPLAINER',
    duration: 11,
    posterAt: 6.37,
    color: '#b8dbf5',
    description: 'A macro pass over machined metal cuts to an abstract visualization of files filling a phone’s storage.',
    preset: {
      topic: 'Why phone storage fills up and what to check before deleting files',
      style: 'explainer',
      language: 'roman-urdu',
      duration: '25',
      visualDirection: 'Open with a macro dolly across a titanium phone. Match cut to its screen as stylized file blocks fall and settle, then isolate a large file for review. Use 9:16, a cool studio key, coral warning accents, and clearly label the file animation as a visualization.',
    },
    shots: [
      { at: 0, tag: '01 / MACRO', jumpTo: .7, shotNote: 'Titanium lens macro', lines: ['Phone full?'], caption: 'Your storage has a limit.' },
      { at: 3.3, tag: '02 / THE BUILD', jumpTo: 4.5, shotNote: 'Files drop and settle', lines: ['Files add up.'], caption: 'Videos and downloads take up space.' },
      { at: 7.1, tag: '03 / THE TAKEAWAY', jumpTo: 8.5, shotNote: 'Large file isolated', lines: ['Check Storage.'], caption: 'Review large files before deleting.' },
    ],
  },
  {
    id: 'halo-desk-lamp',
    number: '02',
    title: 'Halo Desk Lamp',
    category: '3D PRODUCT PROMO',
    duration: 10,
    posterAt: 8.45,
    color: '#ffc18b',
    description: 'A machined switch engages. A copper light pivots into place, revealing a pool of amber light on a walnut desk.',
    preset: {
      topic: 'Reveal Halo, a fictional ring-shaped desk lamp for a small workspace',
      style: 'promo',
      language: 'english',
      duration: '15',
      visualDirection: 'Open with a shallow-focus dolly across a machined switch on a dark walnut desk. Cut wide as the fictional copper ring lamp warms up and the hinged head settles. Finish with an amber practical-light hero orbit. Do not invent specifications.',
    },
    shots: [
      { at: 0, tag: '01 / SWITCH', jumpTo: .9, shotNote: 'Machined switch detail', lines: ['Small desk.'], caption: 'A light for the space you have.' },
      { at: 2.8, tag: '02 / THE REVEAL', jumpTo: 4.4, shotNote: 'Amber light spills onto walnut', lines: ['Big glow.'], caption: 'A warm pool of light where you work.' },
      { at: 6.8, tag: '03 / THE HERO SHOT', jumpTo: 8.4, shotNote: 'Low-angle copper ring', lines: ['Meet Halo.'], caption: 'A fictional desk lamp concept.' },
    ],
  },
  {
    id: 'last-signal',
    number: '03',
    title: 'The Last Signal',
    category: '3D MINI STORY',
    duration: 12,
    posterAt: 6.3,
    color: '#a9e8ff',
    description: 'A solar-winged probe skims a cratered moon and sends an amber pulse. A light answers from the surface.',
    preset: {
      topic: 'A lone satellite sends a final signal and a sleeping moon answers',
      style: 'story',
      language: 'english',
      duration: '25',
      visualDirection: 'Track a foil-wrapped satellite in an elliptical orbit above a cratered moon. Cut from a tight tracking shot to a wider signal visualization. Show the amber response at the surface, using hard sunlight against the lunar terminator. Keep it explicitly fictional.',
    },
    shots: [
      { at: 0, tag: '01 / THE SETUP', jumpTo: 1, shotNote: 'Satellite tracking pass', lines: ['A quiet moon.'], caption: 'One tiny satellite stayed in orbit.' },
      { at: 4, tag: '02 / THE SIGNAL', jumpTo: 6.1, shotNote: 'Cratered moon and signal pulse', lines: ['One last ping.'], caption: 'It sent a signal into the dark.' },
      { at: 8, tag: '03 / THE PAYOFF', jumpTo: 9, shotNote: 'Surface beacon lights up', lines: ['It answered.'], caption: 'A light blinked back from the surface.' },
    ],
  },
];

export function findDemo(id) {
  return DEMOS.find((film) => film.id === id) ?? (id === REFLECTOR.id ? REFLECTOR : undefined);
}

export function demoAssetName(id, extension) {
  return `${findDemo(id)?.asset ?? `${id}-cinema-cut`}.${extension}`;
}
