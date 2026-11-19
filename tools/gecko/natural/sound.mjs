import { picturePlan } from './edit.mjs';
import { contactEvents } from '../motion.js';
import { action as release, inFrame } from '../creature/motion.js';

export function editionCues(cut){
  const {entries}=picturePlan(cut);
  const begin=kind=>entries.find(s=>s.kind===kind).frame/cut.fps;
  const editAt=t=>entries.findLast(s=>s.frame/cut.fps<=t);
  const state=inFrame/cut.fps;
  const cues=[];
  const add=(t,kind,gain,pan,role,more={})=>cues.push({t,kind,gain,pan,role,pitch:190.61,...more});
  // The beat is the actual touchdown, including delayed heel lift before
  // the swing. Offscreen contact is quieter. No sound is emitted by setae.
  for(const {t,foot,side} of contactEvents(cut.duration)){
    const {kind}=editAt(t);
    if(!['grip-anchor','step','climb','through','walk-out','no-yank','hero','hero-eye'].includes(kind))continue;
    const isClose=['step','grip-anchor','no-yank'].includes(kind)&&foot===0;
    const reverse=kind==='through';
    add(t-.011,'pad',isClose?.94:reverse?.35:.48,side*(isClose?.33:reverse?-.38:.48),'dry pad plant',{foot,touchdown:t});
    if(isClose)add(t-.364,'brush',.56,side*.29,'forearm follows airborne paw',{length:.337});
  }
  for(const [kind,lead,gain,pan] of [['step',.23,.62,-.31],['through',.58,.54,.28],['foot',.59,.59,-.22],
    ['lamella',.56,.57,.19],['setae',.56,.73,.29],['vanderwaals',.59,.37,-.22],['creature-release',.83,.28,.32],
    ['replay',.59,.45,.23],['angles',.57,.58,-.22],['walk-out',.60,.54,.26],['hero',.56,.66,-.30]]){
    add(begin(kind)-lead,'air',gain,pan,'editorial perspective change');
  }
  add(state+.243,'brush',.51,.22,'reach before the pad loads',{length:.43});
  add(state+release.plant-.008,'pad',.98,.34,'right forepad sets before body shift',{foot:1,touchdown:state+release.plant});
  add(state+1.02,'brush',.33,.18,'weight rolls against the fixed footprint',{length:.38});
  add(state+2.25,'brush',.37,-.21,'weight moves to other feet',{length:.53});
  add(state+3.065,'brush',.30,.21,'distal roll in extreme close-up',{length:.63});
  add(state+release.free+.10,'brush',.50,.31,'wrist leaves after pad clearance',{length:.57});
  add(begin('replay')+1.15,'brush',.35,.22,'mechanical replay, curling digits',{length:.53});
  add(begin('recap-peel')+.46,'brush',.42,.31,'recap, toe tips peel away',{length:.66});
  for(const [t,pitch,pan,gain,role] of [
    [cut.marks.microContact-.07,207.652,-.29,.34,'illustration accent, contact'],
    [cut.marks.shear-.08,146.832,-.09,.30,'illustration accent, parallel load'],
    [53.59-.053,196,-.21,.33,'recap accent, contact'],[54.22-.06,155.564,.19,.24,'recap accent, loading'],
  ])add(t,'glass',gain,pan,role,{pitch});
  return cues.sort((a,b)=>a.t-b.t);
}
