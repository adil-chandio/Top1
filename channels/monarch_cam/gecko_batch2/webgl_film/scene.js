import * as THREE from 'three';
const W=540,H=960, canvas=document.querySelector('#frame');canvas.width=W;canvas.height=H;const ctx=canvas.getContext('2d');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(360,640,false);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.18;
const scene=new THREE.Scene();scene.background=new THREE.Color('#061820');scene.fog=new THREE.Fog('#071b22',8,25);const camera=new THREE.PerspectiveCamera(35,360/640,.1,80);
scene.add(new THREE.HemisphereLight('#b3e6de','#292015',2));
function light(col,intensity,x,y,z){let l=new THREE.DirectionalLight(col,intensity);l.position.set(x,y,z);scene.add(l)}light('#ffdbac',2.5,-3,6,8);light('#80cddd',2,4,0,4);
const skinMat=new THREE.MeshStandardMaterial({color:'#ba7750',roughness:.68});const dark=new THREE.MeshStandardMaterial({color:'#4c2d20',roughness:.8});const padMat=new THREE.MeshStandardMaterial({color:'#d0a47a',roughness:.8});const eyeMat=new THREE.MeshStandardMaterial({color:'#ddad50',roughness:.3,metalness:.1});const pupil=new THREE.MeshStandardMaterial({color:'#0b1514',roughness:.2});
let sphere=new THREE.SphereGeometry(1,24,16);function oval(parent,x,y,z,sx,sy,sz,mat){let o=new THREE.Mesh(sphere,mat);o.position.set(x,y,z);o.scale.set(sx,sy,sz);parent.add(o);return o}
function capsule(parent,a,b,r,mat){const o=oval(parent,0,0,0,r,1,r,mat);link(o,a,b,r);return o}
function link(o,a,b,r){const av=new THREE.Vector3(...a),bv=new THREE.Vector3(...b);o.position.copy(av).add(bv).multiplyScalar(.5);o.scale.set(r,av.distanceTo(bv)*.55,r);o.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),bv.sub(av).normalize())}
const wall=new THREE.Mesh(new THREE.PlaneGeometry(25,25),new THREE.MeshStandardMaterial({color:'#284e4a',roughness:.5,metalness:.12}));wall.position.z=-.14;scene.add(wall);
const animal=new THREE.Group();scene.add(animal);
const body=oval(animal,0,0,.65,.64,1.05,.30,skinMat);const head=oval(animal,0,1.11,.60,.58,.50,.28,skinMat);oval(animal,0,1.43,.56,.46,.23,.23,skinMat);
for(const x of [-.43,.43]){oval(animal,x,1.2,.81,.18,.20,.10,eyeMat);oval(animal,x,1.2,.90,.046,.13,.026,pupil)}
// Distinct tapering tail geometry, skinned for the prototype and visibly not a reference scan.
let tailGroup=new THREE.Group();animal.add(tailGroup);const tail=[];for(let i=0;i<9;i++){const t=i/8;tail.push(oval(tailGroup,0,-.98-t*1.55,.48,(1-t)*.31+.02,.19,.17*(1-t)+.018,skinMat))}
// Stable spots on the back, no source photograph used.
for(let i=0;i<32;i++){let y=-.75+(i%8)*.23,x=(((i*37)%17)/16-.5)*.85;let z=.66+.25*Math.sqrt(Math.max(0,1-(x/.66)**2-(y/1.05)**2));oval(animal,x,y,z,.035+(i%3)*.012,.042,.009,dark)}
let legs=[];
for(let row of [-1,1])for(let side of [-1,1]){
 let hip=[side*.45,row*.60,.50],knee=[side*.85,row*.55,.37],foot=[side*1.14,row*.82,.20];let upper=capsule(animal,hip,knee,.105,skinMat),lower=capsule(animal,knee,foot,.09,skinMat);let grp=new THREE.Group();animal.add(grp);let palm=oval(grp,0,0,0,.15,.12,.055,skinMat);
 for(let j=0;j<5;j++){let ang=(j-2)*.27,dx=side*.23*Math.cos(ang),dy=.23*Math.sin(ang),a=[0,0,0],b=[dx,dy,.0];capsule(grp,a,b,.035,skinMat);oval(grp,dx,dy,.0,.075,.047,.024,padMat)}
 legs.push({row,side,hip,upper,lower,grp})
}
// Scaled, diagrammatic macro stage, not biologically faithful proportions or a physics solve.
const macro=new THREE.Group();scene.add(macro);const substrate=new THREE.Mesh(new THREE.BoxGeometry(5,5,.15),new THREE.MeshStandardMaterial({color:'#316a70',roughness:.48}));substrate.position.z=-.1;macro.add(substrate);const slab=new THREE.Mesh(new THREE.BoxGeometry(4.4,.27,.4),skinMat);slab.position.set(0,1.45,.65);macro.add(slab);let strands=[];
for(let i=0;i<11;i++){let x=-1.95+i*.39;let a=[x,1.32,.65],b=[x+.30,.15,.26];let stem=capsule(macro,a,b,.028,padMat);let branch=[];for(let j=-2;j<=2;j++){let end=[x+.45+j*.075,-.63,.10];let l=capsule(macro,b,end,.014,padMat);let tip=oval(macro,...end,.055,.038,.02,padMat);branch.push({l,tip,end})}strands.push({x,stem,branch})}
function smooth(a,b,t){t=THREE.MathUtils.clamp((t-a)/(b-a),0,1);return t*t*(3-2*t)}
function update(t){let micro=t>=7.2&&t<10.4;macro.visible=micro;animal.visible=!micro;
 if(!micro){let move=t<3.5?smooth(0,3.5,t)*.27:0;animal.position.y=move;
  for(let l of legs){let phase=t<3.5?Math.sin(t*3+(l.side*l.row>0?0:Math.PI)):0;let foot=[l.side*1.14+l.side*.035*phase,l.row*.82+.06*phase,.20+.035*Math.max(0,phase)];let knee=[l.side*.86,l.row*.55+.03*phase,.37];link(l.upper,l.hip,knee,.105);link(l.lower,knee,foot,.09);l.grp.position.set(...foot)}
  for(let i=0;i<tail.length;i++)tail[i].position.x=Math.sin(t*1.5-i*.35)*.03*(i+1);
 }
 if(micro){let shift=.20*smooth(8,9.5,t);slab.position.x=shift;for(let s of strands){let a=[s.x+shift,1.32,.65],b=[s.x+.30+shift*.35,.15,.26];link(s.stem,a,b,.028);for(let br of s.branch)link(br.l,b,br.end,.014)}}
 let pos,target;if(t<3.5){pos=[.5,.4,8.8-0.5*smooth(0,3.5,t)];target=[0,0,.35]}else if(t<7.2){pos=[-2.3,-1.05,3.55];target=[-1.05,-.62,.2]}else if(t<10.4){pos=[1.5,.4,7.1];target=[0,.25,.2]}else {pos=[.4,.5,8.4];target=[0,0,.4]}
 camera.position.set(...pos);camera.lookAt(...target);renderer.render(scene,camera)
}
function wrap(text,max){ctx.font='700 34px Arial';let lines=[],line='';for(const word of text.split(' ')){let n=(line?line+' ':'')+word;if(ctx.measureText(n).width>max&&line){lines.push(line);line=word}else line=n}if(line)lines.push(line);return lines}
window.renderFrame=(t)=>{update(t);ctx.drawImage(renderer.domElement,0,0,W,H);const grad=ctx.createLinearGradient(0,620,0,960);grad.addColorStop(0,'rgba(3,14,19,0)');grad.addColorStop(.25,'rgba(3,14,19,.72)');grad.addColorStop(1,'rgba(3,14,19,.97)');ctx.fillStyle=grad;ctx.fillRect(0,600,W,360);
 ctx.fillStyle='#8de5d2';ctx.font='700 16px Arial';ctx.fillText('MONARCH CAM  /  VISUAL CONCEPT',30,670);
 const text=t<3.5?'How can a gecko climb glass?':t<7.2?'Adhesive pads line its toes.':t<10.4?'Microscopic hairs branch into tiny tips.':'Close contact helps create grip.';
 ctx.fillStyle='#ffffff';let lines=wrap(text,470);lines.forEach((l,i)=>ctx.fillText(l,30,726+i*46));ctx.font='18px Arial';ctx.fillStyle='#aecbc8';ctx.fillText('Illustration • not to scale',30,907);return canvas.toDataURL('image/jpeg',.91).split(',')[1]};
