import { loadGeckoEdit } from '../session.mjs';
import { inFrame, outFrame } from '../creature/motion.js';

export const title='How Does a Gecko Let Go? — Creature Edition';
export const premiere=new URL('../premiere/edit.json',import.meta.url);
const created=new Set(['eye','grip-anchor','step','climb','through','foot','replay','walk-out','no-yank','recap-peel','hero','hero-eye']);
export async function naturalEdit(options={}){
  const base=await loadGeckoEdit({from:premiere,...options});
  const changes={...base,id:'gecko-creature-edition',title};
  changes.shots=[...base.shots.filter(({frame})=>frame<inFrame||frame>=outFrame),
    {frame:inFrame,kind:'creature-release',note:'Continuous original Tokay reach, brace, load transfer and distal-first peel'},
    {frame:outFrame,kind:'settled',note:'Same released hold carried into the explanation before the alternate angle'},
  ].sort((a,b)=>a.frame-b.frame);
  return changes;
}

export function picturePlan(cut){
  const route={new:'trace',proof:'proof',retained:'science'};
  const type=({kind})=>created.has(kind)?route.new:kind==='creature-release'?route.proof:kind==='settled'?'settle':route.retained;
  const entries=cut.shots.map((s,i)=>({...s,end:cut.shots[i+1]?.frame??cut.frames,source:type(s)}));
  // Runs are joined only at the original timeline frames. The printed recap,
  // arrow and scale labels in scientific plates are retained with their cuts.
  const spans=[];
  for(const e of entries){
    if(spans.at(-1)?.source===e.source){spans.at(-1).end=e.end;continue;}
    spans.push({first:e.frame,end:e.end,source:e.source});
  }
  return {entries,spans};
}
