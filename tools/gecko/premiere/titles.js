import { between, clamp, smooth } from '../motion.js';
const W=1080,H=1920;
const milky='#f5f3e7', warm='#ffe0ab', mint='#b8efd7', muted='#b4cccb';
const normalized=(s)=>s.toLowerCase().replace(/[^a-z]/gu,'');
const accents=new Set(['wall','step','controlled','tokay','setae','tips','contact','suction','waals','adhere','direction','base','curl','detach','hyperextension','microscopic','yank','loading','movement','grip','gripping','possible']);
// Important word reveals are locked to the selected v2 performance.
const keyTiming={wall:2.03,controlled:9.42,tokay:11.04,setae:15.04,tips:17.09,suction:21.41,waals:24.75,direction:27.71,base:30.11,curl:36.05,detach:40.11,hyperextension:43.17,microscopic:47.18,yank:50.92,loading:54.98,gripping:58.54};
export function premiereTitles(ctx,cut,chapterCopy={}) {
  const shade=ctx.createLinearGradient(0,H*.65,0,H*.97);
  shade.addColorStop(0,'#040a1000');shade.addColorStop(.65,'#030c11b9');shade.addColorStop(1,'#020811c7');
  const header=ctx.createLinearGradient(0,0,0,H*.229);header.addColorStop(0,'#070c11bd');header.addColorStop(.47,'#070c1168');header.addColorStop(1,'#070c1100');
  const rule=(x,y,w,alpha)=>{ctx.fillStyle=`rgba(171,218,200,${alpha})`;ctx.fillRect(x,y,w,2.5);};
  function typeset(copy){
    const lines=copy.slice(2),rows=lines.length, longest=Math.max(...lines.map(l=>l.length));
    const px=longest>27?60:longest>23?65:72;
    ctx.font=`760 ${px}px Copy`;
    const max=Math.max(...lines.map(l=>ctx.measureText(l).width));
    const scale=Math.min(1,914/max), space=ctx.measureText(' ').width*scale;
    const parts=lines.flatMap((line,j)=>{
      const words=line.split(/\s+/u),sizes=words.map(w=>ctx.measureText(w).width*scale);
      let x=(W-sizes.reduce((a,b)=>a+b,space*(words.length-1)))*.5;
      return words.map((text,k)=>{const n={text,name:normalized(text),x:x+sizes[k]*.5,j,k};x+=sizes[k]+space;return n;});
    });
    return {rows,px,scale,parts,focus:parts.findLast(p=>accents.has(p.name))};
  }
  const cues=cut.captions.map(copy=>({copy,...typeset(copy)}));
  return function paint(t,s,physics){
    const cue=cues.find(({copy})=>t>=copy[0]&&t<copy[1]);
    if(cue){
      const {copy,px,parts,focus,rows,scale}=cue, [a,b]=copy;
      const inAlpha=smooth((t-a+.025)/.13), outAlpha=smooth((b-t)/.093);
      ctx.save();ctx.globalAlpha=.92;ctx.fillStyle=shade;ctx.fillRect(0,H*.65,W,H*.35);ctx.restore();
      const ink=t>10.53&&t<48.96?mint:warm;
      ctx.save();ctx.font=`760 ${px}px Copy`;ctx.textAlign='center';ctx.textBaseline='alphabetic';
      ctx.lineJoin='round';ctx.lineWidth=2.1;ctx.strokeStyle='#0513178c';
      for(const p of parts) {
        const age=t-a-Math.min(.085,.010*(p.k+parts.length*p.j));
        const r=smooth((age+.03)/.13), keyed=p===focus;
        const at=clamp(keyTiming[p.name]??a+(b-a)*.42,a+.16,b-.16);
        const k=keyed?between(t,at-.080,at+.126):0;
        const y=H*.843+(p.j-rows+1)*79+(1-r)*10-k*2.8;
        ctx.save();ctx.translate(p.x,y);ctx.scale(scale*(1+.019*k),1+.028*k);
        ctx.globalAlpha=r*outAlpha*inAlpha;
        ctx.strokeText(p.text,0,0);
        ctx.fillStyle=k>.51?ink:milky;ctx.shadowColor='#020702d9';ctx.shadowBlur=15;ctx.shadowOffsetY=3.5;
        ctx.fillText(p.text,0,0);ctx.restore();
      }
      ctx.restore();
    }
    const head=(kicker,title,m,alpha)=>{
      ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle=header;ctx.fillRect(0,0,W,H*.24);
      rule(70,126,72,.80);ctx.textAlign='left';ctx.font=`680 22px Display`;ctx.fillStyle=m;
      ctx.fillText(kicker,70,169);ctx.font='690 46px Display';ctx.fillStyle=milky;ctx.fillText(title,68,224);ctx.restore();
    };
    if(t<2.31){
      const o=between(t,.038,.29)*(1-between(t,2.04,2.311));
      head('MONARCH STUDIO  /  WILDLIFE', 'A grip without glue',warm,o);
    } else if (s.kind==='step'){
      const a=between(t,2.39,2.66)*(1-between(t,4.53,4.95));
      ctx.save();ctx.globalAlpha=a;ctx.fillStyle=header;ctx.fillRect(0,0,W,H*.268);
      ctx.font='700 25px Display';ctx.fillStyle=warm;ctx.fillText('FROM GRIP TO RELEASE',70,164);
      ctx.font='730 63px Display';ctx.fillStyle=milky;ctx.fillText('How does it let go?',67,237);
      rule(71,271,188+40*between(t,2.79,3.6),.72);ctx.restore();
    }
    const chapters={
      through:['01  /  THE GRIP','Through the glass'],foot:['TOKAY GECKO  /  UNDERSIDE','Adhesive toe pads'],
      lamella:['SCALE CHANGE  /  ENLARGED','Lamellae'],setae:['MICRO VIEW  /  ILLUSTRATION','Setae'],
      'contact-ground':['01  /  INTERFACE','Close contact'],vanderwaals:['MICRO VIEW  /  ILLUSTRATION','No suction seal'],
      'vd-detail':['SCALE DETAIL  /  ENLARGED','Terminal tips'],shear:['02  /  THE LOAD','Toward the toe base'],
      'shear-locked':['LOAD PATH  /  DIRECTION','Parallel to the surface'],
      'peel-wide':['03  /  THE RELEASE','Distal tip lifts first'],replay:['SLOW VIEW  /  TOE SCALE','Digital hyperextension'],
      angles:['MICRO VIEW  /  SETAL SCALE','Not the toe joint'],
      'angle-detail':['MICRO VIEW  /  ILLUSTRATION','Shaft and tip'],
    };
    const mark=chapterCopy[s.kind]??chapters[s.kind];
    if(mark)head(mark[0],mark[1],mint,.91*between(s.age,.045,.38)*smooth(s.remaining/.24));
    // Track annotations to the rendered toe. These are landmarks, not
    // quantitative force sensors; keep the graphic out of caption territory.
    const guide=(name,anchor,sign,alpha)=>{
      if(!anchor||anchor[0]<.07||anchor[0]>.94||anchor[1]>.68||alpha<=0)return;
      const [x,y]=[anchor[0]*W,anchor[1]*H];
      const X=clamp(x+sign*160,142,W-142),Y=y-111;
      ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle='#a7e0cb';ctx.fillStyle=mint;ctx.lineWidth=1.86;
      ctx.beginPath();ctx.arc(x,y,6.8,0,Math.PI*2);ctx.stroke();
      ctx.beginPath();ctx.moveTo(x+sign*7,y-9);ctx.lineTo(x+sign*43,Y);ctx.lineTo(X,Y);ctx.stroke();
      ctx.font='690 23px Display';ctx.textAlign=sign<0?'left':'right';ctx.shadowColor='#031d14';ctx.shadowBlur=5;
      ctx.fillText(name,X,Y-11);ctx.restore();
    };
    if(s.kind==='shear-locked')guide('TOE BASE',physics.pixels?.base,-1,.88*between(s.age,.07,.35)*smooth(s.remaining/.26));
    if(s.kind==='peel-wide'||s.kind==='peel-side')guide('DISTAL TIP',physics.pixels?.tip,-1,.84*between(t,34.83,35.33)*(1-between(t,37.35,38.14)));
    if(s.kind.startsWith('recap-')){
      const pair={'recap-contact':['01','CONTACT'],'recap-shear':['02','DIRECTION'],'recap-peel':['03','RELEASE']}[s.kind];
      const a=between(s.age,.012,.22)*smooth(s.remaining/.26);
      ctx.save();ctx.globalAlpha=a;ctx.fillStyle=header;ctx.fillRect(0,0,W,H*.229);
      ctx.fillStyle=mint;ctx.font='680 26px Display';ctx.fillText(pair[0],72,177);
      rule(132,168,38,.7);ctx.font='730 40px Display';ctx.fillStyle=milky;ctx.fillText(pair[1],190,178);ctx.restore();
    }
  };
}
