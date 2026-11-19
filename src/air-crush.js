// Editorial cues live with the film, shared by the shot guide, renderer and mix.
const shot = (frame, tag, jumpTo, shotNote) => ({ at: frame / 24, tag, jumpTo, shotNote });

export const AIR_CRUSH = {
  id: 'air-crush',
  number: '04',
  asset: 'air-crush-cinema-edition',
  width: 1080,
  height: 1920,
  title: 'Who Crushed the Can?',
  category: 'TOP1 LAB / CINEMA EDITION',
  duration: 29,
  posterAt: 26.66,
  color: '#ffba72',
  voiceLabel: 'Urdu VO',
  sample: '/samples/air-crush-blueprint.md',
  studio: '/monarch-studio/',
  description: 'An aluminium can buckles without being squeezed. Follow the steam through an aluminium cutaway, then watch the first fold in slow motion. Urdu narration with kinetic Roman Urdu captions.',
  preset: {
    topic: 'Paani mein ulti can ko hawa ka pressure kaise kuchal deta hai?',
    style: 'explainer',
    language: 'roman-urdu',
    duration: '25',
    visualDirection: 'Cold open on an inverted orange can buckling inward. Rewind to the intact can with water vapor pushing out most of the air. Use an axial cutaway for the submerged opening, vapor condensing into droplets and falling inside pressure. Use a restrained inward vector cue for steady outside pressure, then replay the metallic buckle in slow motion. Keep the screen clear of labels except a brief cutaway ID and animated Roman Urdu dialogue captions. Label tracers and pressure graphics as illustrative. Treat it as an explanation, not a home procedure. Fact-check with UW–Madison Wonders of Physics.',
  },
  shots: [
    shot(0, 'THE SNAP', .45, 'Cold open: metal buckles'),
    shot(39, 'BEFORE THE SNAP', 2.5, 'The intact can'),
    shot(106, 'CUTAWAY · HOT WATER', 5.4, 'The water starts to boil'),
    shot(156, 'VAPOR DISPLACES AIR', 7.5, 'Macro: air exits the opening'),
    shot(213, 'COLD WATER', 10.4, 'Inverted can meets cold water'),
    shot(276, 'CUTAWAY · THE SEAL', 12.3, 'The open mouth is underwater'),
    shot(326, 'CUTAWAY · CONDENSATION', 15.75, 'Vapor turns to droplets'),
    shot(400, 'PRESSURE COMPARISON', 18.8, 'Inside pressure drops'),
    shot(460, 'OUTSIDE AIR', 21, 'Pressure pushes inward'),
    shot(551, 'SLOW-MOTION REPLAY', 23.85, 'Watch the first fold spread'),
    shot(602, 'THE PAYOFF', 27, 'Crushed by air, not by water'),
  ],
};

export const AIR_TIMING = Object.freeze({ dip: 10.25, condense: 13.75, pressureStart: 15.3, pressureEnd: 19.08, hookSnap: 1 / 4, snap: 554 / 24 });

export const AIR_CRUSH_CAPTIONS = [
  [0, 2.18, 'Is can ko kisi ne', 'dabaya nahi.'],
  [2.20, 3.73, 'Phir ye pichak', 'kaise gaya?'],
  [3.85, 5.91, 'Can ke andar', 'paani garam hua.'],
  [5.98, 6.96, 'Bhaap uthi…'],
  [6.99, 8.86, '…aur zyada tar hawa', 'bahar nikal gayi.'],
  [8.96, 11.34, 'Phir iska munh', 'thande paani mein dooba.'],
  [11.40, 13.48, 'Hawa ke wapas aane', 'ka raasta band.'],
  [13.68, 15.32, 'Andar ki bhaap', 'thandi hote hi…'],
  [15.34, 16.49, 'boondein ban gayi.'],
  [16.69, 18.82, 'Andar ka pressure', 'tezi se gir gaya.'],
  [19.29, 20.83, 'Lekin bahar ki hawa…'],
  [20.86, 22.81, '…utne hi zor se', 'dhakka de rahi thi.'],
  [24.60, 26.63, 'Paani ne bas', 'raasta band kiya.'],
  [26.91, 28.85, 'Can ko hawa ne kuchla.'],
];
