import { AIR_CRUSH_CAPTIONS } from '../../src/air-crush.js';
import { clamp, smooth } from './motion.js';

const keyedWords = new Set(['can', 'pichak', 'garam', 'bhaap', 'bahar', 'thande', 'band', 'boondein', 'pressure', 'dhakka', 'hawa', 'kuchla']);
const openEase = (n) => 1 - (1 - clamp(n)) ** 3;
const clean = (word) => word.toLowerCase().replace(/[^a-z]/g, '');

// Small editorial phrases rather than an animated wall of title cards. The
// layout is settled first, so the active word never pushes neighbours around.
export function kineticPhrases(ctx, W, H, cues, keywords, accent, baseline = () => .825) {
  const sx = W / 720;
  const shade = ctx.createLinearGradient(0, H * .64, 0, H * .982);
  shade.addColorStop(0, '#040a1000');
  shade.addColorStop(.62, '#040a1048');
  shade.addColorStop(1, '#040a10a8');
  const white = '#f5f8f7';
  let cached;

  function prepare(cue) {
    const lines = cue.slice(2);
    const long = Math.max(...lines.map((line) => line.length));
    const size = (long > 25 ? 39 : long > 21 ? 43 : 48) * sx;
    ctx.font = `760 ${size}px Copy`;
    const lineWidth = Math.max(...lines.map((line) => ctx.measureText(line).width));
    const squeeze = Math.min(1, (W - 100 * sx) / lineWidth);
    const words = lines.map((line, row) => {
      const items = line.split(/\s+/u);
      const space = ctx.measureText(' ').width * squeeze;
      const lengths = items.map((v) => ctx.measureText(v).width * squeeze);
      const width = lengths.reduce((x, v) => x + v, space * (items.length - 1));
      let x = (W - width) / 2;
      return items.map((v, i) => {
        const item = { word: v, accent: keywords.has(clean(v)), row, x: x + lengths[i] / 2, width: lengths[i] };
        x += lengths[i] + space;
        return item;
      });
    }).flat();
    // One emphasis per cue, not three competing karaoke highlights.
    const marked = words.findLast((item) => item.accent);
    return { cue, size, words, marked, squeeze, rows: lines.length };
  }

  function caption(t, cue) {
    if (!cached || cached.cue !== cue) cached = prepare(cue);
    const { size, words, marked, squeeze, rows } = cached;
    const [start, end] = cue;
    const exit = smooth((end - t) / .112);
    const emphasisAt = start + Math.min(.65, (end - start) * .31);
    const lineHeight = 55 * sx;
    const y = H * baseline(t) - (rows - 1) * lineHeight;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.font = `760 ${size}px Copy`;
    ctx.strokeStyle = '#07101780';
    ctx.lineWidth = 1.18 * sx;
    ctx.lineJoin = 'round';
    const ink = accent(t);
    for (let j = 0; j < words.length; j++) {
      const item = words[j];
      const rise = openEase((t - start + .032 - Math.min(.14, j * .019 + item.row * .022)) / .18);
      if (rise <= 0) continue;
      const accent = item === marked ? smooth((t - emphasisAt) / .152) : 0;
      ctx.save();
      ctx.translate(item.x, y + item.row * lineHeight + (1 - rise) * 11 * sx - accent * 1.9 * sx);
      ctx.scale(squeeze * (1 + .031 * accent), 1 + .048 * accent);
      ctx.globalAlpha = rise * exit;
      ctx.strokeText(item.word, 0, 0);
      ctx.fillStyle = accent > .55 ? ink : white;
      ctx.shadowColor = '#05090da8'; ctx.shadowBlur = 9 * sx; ctx.shadowOffsetY = 2.5 * sx;
      ctx.fillText(item.word, 0, 0);
      ctx.restore();
    }
    ctx.restore();
  }

  return function draw(t) {
    const cue = cues.find(([start, end]) => t >= start && t < end);
    if (cue) {
      ctx.fillStyle = shade;
      ctx.fillRect(0, H * .64, W, H * .36);
      caption(t, cue);
    }
  };
}

export function airCrushTitles(ctx, W, H) {
  const sx = W / 720;
  const phrases = kineticPhrases(ctx, W, H, AIR_CRUSH_CAPTIONS, keyedWords, (t) => t < 9 || t > 24 ? '#ffcbab' : '#aeeaf8');
  return (t, cut) => {
    phrases(t);
    // A small, transient diagram note only on the first interior view.
    if (cut.index === 2) {
      const visibility = smooth(cut.age / .29) * smooth(cut.remaining / .29);
      ctx.save();
      ctx.globalAlpha = visibility * .83;
      ctx.font = `680 ${15 * sx}px Copy`;
      ctx.fillStyle = '#d6dfe0';
      ctx.fillText('CUTAWAY · VISUALIZATION', 41 * sx, 98 * sx);
      ctx.restore();
    }
  };
}
