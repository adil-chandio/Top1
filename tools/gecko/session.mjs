import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const BASE=new URL('./edit.json',import.meta.url);
export const VO_SHA256='8eedfd172a8ab5ea6fa683f8691872a0b24e67a9d713b785dd056b62ce331fb4';
const ss=(s)=>{
  const m=s.match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/u);
  assert.ok(m,`Invalid caption time: ${s}`);
  return +m[1]*3600 + +m[2]*60 + +m[3] + +m[4]/1000;
};
export function readGeckoSrt(raw){
  return raw.replace(/\r/g,'').trim().split(/\n\s*\n/u).map((block,i)=>{
    const [n,range,...lines]=block.split('\n');assert.equal(+n,i+1);
    const [a,b]=range.split(' --> ');
    return [ss(a),ss(b),...lines];
  });
}

export function validateGeckoEdit(cut, picture=false){
  assert.equal(cut.voiceDuration,60.8);
  assert.equal(cut.fps,24);assert.equal(cut.frames,cut.duration*cut.fps);
  assert.equal(cut.shots[0].frame,0);
  assert.ok(cut.shots.every((s,i)=>Number.isInteger(s.frame)&&s.frame<cut.frames&&(!i||s.frame>cut.shots[i-1].frame)));
  assert.equal(new Set(cut.shots.map(s=>s.kind)).size,cut.shots.length);
  assert.ok(cut.marks.microContact<cut.marks.shear&&cut.marks.shear<cut.marks.curlStart&&cut.marks.curlStart<cut.marks.digitRelease&&cut.marks.digitRelease<cut.marks.footClear);
  if(picture){
    assert.ok(cut.captions?.length>=32,'Picture needs the aligned session captions (SRT)');
    for(const [i,[from,to,...copy]] of cut.captions.entries()){
      assert.ok(from>=0&&from<to&&to<=cut.voiceDuration&&(!i||from>=cut.captions[i-1][1]),`Caption timing error at ${i+1}`);
      assert.ok(copy.length<=2&&copy.length>0&&copy.every(s=>s.trim()&&s.length<33),`Caption layout error at ${i+1}`);
    }
  }
  return cut;
}

// The picture/physics edit is reproducible without committing customer audio
// or dialogue to the public repo. Caption strings come from a local SRT.
export async function loadGeckoEdit({picture=false,from=process.env.GECKO_TIMELINE}={}) {
  const cut=JSON.parse(await readFile(from??BASE,'utf8'));
  if(picture&&!cut.captions){
    const srt=process.env.GECKO_CAPTIONS??'deliverables/How-Does-a-Gecko-Let-Go.en.srt';
    cut.captions=readGeckoSrt(await readFile(srt,'utf8'));
  }
  return validateGeckoEdit(cut,picture);
}
