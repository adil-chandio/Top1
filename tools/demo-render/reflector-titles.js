import { REFLECTOR_CAPTIONS } from '../../src/reflector.js';
import { kineticPhrases } from './air-crush-titles.js';
import { smooth } from './motion.js';

export function reflectorTitles(ctx, width, height) {
  const scale = width / 720;
  const accents = new Set(['light','battery','reflector','chamak','aaine','tirchhi','kone','teen','nabbe','takraayi','doosri','teesri','ulta','headlight','wapas']);
  const captions = kineticPhrases(ctx, width, height, REFLECTOR_CAPTIONS, accents,
    (t) => t >= 14 && t < 19.5 ? '#b9e9f7' : '#ffba9c',
    (t) => t >= 280/24 && t < 333/24 ? .726 : .825);
  return (t, cut) => {
    captions(t);
    const note = cut.index === 6 ? 'AAM AAINA  /  RAY DIAGRAM'
      : cut.index === 10 ? '90°  /  ENLARGED CORNER'
      : cut.index === 11 ? 'KIRAN KA RAASTA  /  SLOW VIEW' : null;
    if (note) {
      ctx.save();
      ctx.globalAlpha = .86*smooth(cut.age/.30)*smooth(cut.remaining/.37);
      ctx.font = `680 ${15.5*scale}px Copy`;
      ctx.fillStyle = '#dae3e9';
      ctx.textAlign = 'left';
      ctx.fillText(note,43*scale,height*.081);
      ctx.restore();
    }
  };
}
