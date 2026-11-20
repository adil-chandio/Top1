#pragma once
#include "gpu.hpp"
namespace ant {
constexpr float radius=4.33f, impact=3.42f, land=5.48f;
inline float ground(float x,float z){
 float r=hypotf(x,z*1.035f), a=atan2f(z,x), rr=r+.045f*sinf(5*a)+.028f*sinf(9*a+1.3f);
 float pit=-2.16f+.513f*rr;
 // Continuous floor, lip and outer sand field; geometry is illustrative, not a measured pit.
 float h=mix(pit,.035f+.079f*exp(-powf((r-4.40f)*2.65f,2)),ramp(4.02f,4.58f,r));
 h+=.034f*sinf(x*2.15f+z*.79f)*cosf(z*2.36f-x*.59f)+.012f*sinf(r*13.0f+sinf(4*a)*2.0f)*ramp(.10f,.65f,r);
 h+=ramp(5.4,11,r)*(.23f*sinf(x*.85f+z*.34f)+.14f*cosf(z*1.15f-x*.27f));
 return h;
}
inline void normals(Mesh& m){for(auto& p:m.v)p.n={}; for(size_t i=0;i<m.idx.size();i+=3){auto a=m.idx[i],b=m.idx[i+1],c=m.idx[i+2];V n=cross(m.v[b].p-m.v[a].p,m.v[c].p-m.v[a].p);m.v[a].n+=n;m.v[b].n+=n;m.v[c].n+=n;}for(auto&v:m.v){v.n=norm(v.n);}}
inline Mesh sweep(int l,int k,int shape){
 Mesh m;
 for(int i=0;i<=l;i++){
   float u=float(i)/l,x=-cosf(u*pi),rr=std::max(.0005f,sinf(u*pi));
   for(int j=0;j<=k;j++){
     float t=float(j)/k,a=t*tau,c=cosf(a),s=sinf(a),r=rr;
     float y=r*c,z=r*s;
     if(shape==1){ // Sculpted elongate Ponerine head: flatten ventral plane, retain shoulders.
      r=powf(r,.56f);y=r*copysignf(powf(fabsf(c),.80f),c)*(1.0f-.115f*x);z=r*copysignf(powf(fabsf(s),.80f),s)*(1.0f-.20f*x);
      y+=.055f*cosf(tau*u)*z*z;
     }else if(shape==2){ // Petiole & tergite shape
      r*=1.f-.15f*x;y=r*c;z=r*s;
     }else if(shape==3){ // Tapered curved rectangular mandible (tip matches contact solver).
      x=u;float w=std::max(.025f,powf(1-u,.47f))*(.82f+.16f*sinf(u*pi));
      y=c*w*.68f-.15f*u;z=s*w-.76f*powf(u,1.7f);
     }else if(shape==4){ // rounded joint sleeve taper
      y*=.86f-.24f*x;z*=.86f-.24f*x;
     }else if(shape==5){ // faceted grains
      float v=.85f+.16f*sinf(4*a+1.8f*x)+.12f*cosf(6*x+a);y*=v;z*=v;
     }
     m.v.push_back({{x,y,z},{},{u,t}});
   }
 }
 for(int i=0;i<l;i++)for(int j=0;j<k;j++){unsigned a=i*(k+1)+j,b=a+k+1; m.idx.insert(m.idx.end(),{a,a+1,b,b,a+1,b+1});}
 normals(m); // Cross product above is oriented outward for the chosen polar parameterization.
 // Seal the normal seam: shared UV seam is not a ridge.
 for(int i=0;i<=l;i++){auto& a=m.v[i*(k+1)].n;auto&b=m.v[i*(k+1)+k].n;a=b=norm(a+b);}
 return m;
}
inline Mesh pitMesh(){
 Mesh m;const int R=84,A=120;
 for(int j=0;j<=R;j++){float s=j/(float)R,r=.001f+14*powf(s,1.35f);for(int i=0;i<=A;i++){
  float a=i*tau/A,x=r*cosf(a),z=r*sinf(a),d=.013f,y=ground(x,z);
  V n=norm({(ground(x-d,z)-ground(x+d,z))/(2*d),1,(ground(x,z-d)-ground(x,z+d))/(2*d)});
  m.v.push_back({{x,y,z},n,{x,z}});
 }}
 for(int j=0;j<R;j++)for(int i=0;i<A;i++){unsigned a=j*(A+1)+i,b=a+A+1;m.idx.insert(m.idx.end(),{a,a+1,b,b,a+1,b+1});}
 m.shadow=false;return m;
}
inline M rodmat(V a,V b,float r,float flat=1){V delta=b-a,X=norm(delta),Y=norm(cross(fabsf(X.y)>.98f?V{0,0,1}:V{0,1,0},X)),Z=cross(X,Y);return basis(X*(len(delta)*.535f),Y*r,Z*(r*flat),(a+b)*.5f);}
struct Motion{
 V p;float yaw=0,pitch=.30f,roll=0,head=-.1f,jaw=1.22f;int support=0;
 V toes[6];M torso,h;V tips[2];float clear=0;bool fly=false;
};
inline M mandible(const M& h,int s,float open){return mul(h,mul(loc({.518f,-.062f,float(s)*.153f}),mul(ry(s*open),size({.730f,.074f,.079f*float(s)}))));}
inline V jtip(const M& h,int s,float open){return point(mandible(h,s,open),{1,-.15f,-.76f});}
inline void matrices(Motion& a){
 a.torso=mul(loc(a.p),mul(ry(a.yaw),mul(rz(a.pitch),rx(a.roll))));
 a.h=mul(a.torso,mul(loc({.44f,.023f,0}),rz(a.head)));
 a.tips[0]=jtip(a.h,-1,a.jaw);a.tips[1]=jtip(a.h,1,a.jaw);
 a.clear=std::min(a.tips[0].y-ground(a.tips[0].x,a.tips[0].z),a.tips[1].y-ground(a.tips[1].x,a.tips[1].z));
}
inline float runx(float t){return 1.35f+1.265f*ramp(.04f,2.29f,t)-.60f*pulse(.57f,1.37f,2.27f,t);}
inline void solveContact(Motion&a,float gap){float lo=-1.30f,hi=.92f;for(int k=0;k<23;k++){a.head=(lo+hi)*.5f;matrices(a);if(a.clear<gap)lo=a.head;else hi=a.head;}matrices(a);}
inline Motion planted(float t){
 Motion a;float x=runx(t),z=.245f+.04f*sinf(t*1.20f);a.p={x,ground(x,z)+.475f+.115f*ramp(2.32f,3.30f,t)+.027f*sinf(10*t)*(1-ramp(1.95f,2.4f,t)),z};a.yaw=.012f+.08f*sinf(t*.77f);a.pitch=.297f+.038f*sinf(6*t)*(1-ramp(2.0f,2.4f,t));
 a.head=-.04f+.06f*sinf(t*5.3f);a.jaw=mix(1.39f,.032f,ramp(3.245f,impact,t));matrices(a);
 // The ant can hold a stance while the head aims. The clearance reaches a single
 // contact at the end of the jaw sweep, independent of the foot rig.
 if(t>2.17f)solveContact(a,mix(.24f,.0015f,ramp(2.19f,impact,t)));
 else if(a.clear<.075f)solveContact(a,.075f);
 for(int i=0;i<6;i++){
  int leg=i/2,s=i%2?1:-1;float side=float(s);
  float tstep=std::min(t,2.20f),per=.66f+(leg==2?.05f:0.f),q=tstep/per+(leg+i%2)%2*.50f+leg*.048f;
  float cycle=floor(q),phase=q-cycle,st=(cycle-(leg+i%2)%2*.50f-leg*.048f)*per;
  float lift=0,fx=runx(st+.24f),swing=ramp(.60f,1,phase);
  if(phase>.60f){fx=mix(fx,runx(st+per+.24f),swing);lift=.128f*sinf(pi*sat((phase-.60f)/.40f));}
  else fx-=.125f*pulse(.90f,1.62f,2.25f,t)*(phase/.60f);
  float dx[]={.59f,.055f,-.75f},dz[]={.567f,.71f,.58f};
  V pt={fx+dx[leg],0,z+side*dz[leg]+side*.026f*sinf(t*6+i)};
  if(t>2.20f){float lock=ramp(2.20f,2.54f,t);pt.x=mix(pt.x,2.615f+dx[leg],lock);pt.z=mix(pt.z,.278f+side*dz[leg],lock);lift*=1-lock;}
  if(i==1)lift+=.118f*ramp(2.66f,3.10f,t);
  pt.y=ground(pt.x,pt.z)+.012f+lift;
  a.toes[i]=pt;a.support+=lift<.012f;
 }
 return a;
}
inline Motion action(float t,bool failed=false){
 if(t<=impact)return planted(std::max(0.f,t));
 Motion a=planted(impact);float endT=failed?5.3f:land,u=sat((t-impact)/(endT-impact));
 V p0=a.p;V end=failed?V{.73f,0,1.77f}:V{-5.08f,0,-.51f};end.y=ground(end.x,end.z)+.45f;
 if(failed){V wall={1.76f,0,2.70f};wall.y=ground(wall.x,wall.z)+.36f;
   if(u<.56f){float b=u/.56f;a.p=mix(p0,wall,b)+V{0,1.12f*sinf(pi*b),0};}
   else {float b=(u-.56f)/.44f;a.p=mix(wall,end,1.f-(1.f-b)*(1.f-b));a.p.y+=.09f*sinf(pi*b);}
 }else{
   a.p=mix(p0,end,u)+V{0,2.49f*4*u*(1-u),0};
 }
 a.fly=u<(failed?.56f:1.f);
 a.yaw+= (failed?1.89f:3.05f)*ramp(.10f,.98f,u);a.pitch=mix(.297f,-.22f,sinf(pi*u))+.16f*sinf(tau*u);a.head=mix(a.head,.005f,ramp(0,.44f,u));a.roll=(failed?.65f:.50f)*sinf(pi*u);
 if(failed){float bu=pulse(.50f,.562f,.784f,u);a.pitch-=.43f*bu;a.roll+=.36f*bu;}
 if(u>=1 && !failed){a.p.x-=.72f*ramp(land,land+2,t);a.p.y=ground(a.p.x,a.p.z)+.448f+.018f*sinf((t-land)*12);}
 a.jaw=mix(.032f,.44f,ramp(.67f,1.0f,u));matrices(a);a.support=0;
 for(int i=0;i<6;i++){
   int leg=i/2,s=i%2?1:-1;float d[]={.50f,.05f,-.68f};float ss[]={.55f,.71f,.59f};
   V ideal=point(a.torso,{d[leg]-.19f*sinf(pi*u),mix(-.435f,-.24f,sinf(pi*u)),float(s)*ss[leg]});
   V initial=planted(impact).toes[i]+(a.p-p0);V toe=mix(initial,ideal,ramp(0,.24f,u));
   float floor=ground(toe.x,toe.z)+.012f;
   if(!a.fly){
    float stride=.085f*sinf((t-endT)*10+(leg+s)*pi*.48f)*ramp(endT,endT+.34f,t);
    toe.x+=stride; floor=ground(toe.x,toe.z)+.012f;toe.y=floor+std::max(0.f,stride)*.42f;
   }else toe.y=std::max(toe.y,floor);
   a.toes[i]=toe;a.support+=toe.y<=floor+.013f;
 }
 return a;
}
inline Motion study(float t,bool snap){
 Motion a;a.p={0,0,0};a.jaw=snap?mix(1.25f,.057f,ramp(2.95f,3.20f,fmod(t,7.4f))):mix(.26f,.64f,.5f+.5f*sinf(t*1.8f));
 a.yaw=.18f+.12f*sinf(t*.26f);a.pitch=.052f;a.head=.02f*sinf(t*.71f);
 matrices(a);
 for(int i=0;i<6;i++){int l=i/2,s=i%2?1:-1;float a0[]={.67f,.03f,-.73f};V pp=point(a.torso,{a0[l],-.47f,s*(l==1?.69f:.56f)});a.toes[i]=pp;}
 return a;
}
inline Motion climb(float t){
 Motion a;float z=.37f+.16f*sinf(t*.44f),x=1.42f+4.04f*ramp(0,5.25f,t);a.p={x,ground(x,z)+.450f+.023f*sinf(t*22),z};
 a.jaw=.36f+.076f*sinf(t*1.9f);a.pitch=mix(.31f,.018f,ramp(3.7f,4.8f,t));a.yaw=.078f;a.head=.025f*sinf(t*5);matrices(a);
 for(int i=0;i<6;i++){
   int leg=i/2,s=i%2?1:-1;float phase=fmod(t/.43f+(leg+i%2)%2*.50f,1.f);
   float dx[]={.60f,.01f,-.65f};float lx=x+dx[leg]+mix(.20f,-.21f,phase)+.39f*ramp(.68f,1.f,phase), lz=z+float(s)*(.57f+.10f*(leg==1));
   float lift=.14f*sinf(pi*sat((phase-.68f)/.32f));a.toes[i]={lx,ground(lx,lz)+.012f+lift,lz};a.support+=lift<.012f;
 }
 return a;
}
struct Camerawork{V eye,target,up={0,1,0};float fov=36,focus=0,blur=3.1f,diagram=0,key=1.1f,sky=.60f,exposure=1.0f,dark=0;};
inline Camerawork camera(int c,float t,float q,const Motion &a){
 Camerawork k;V p=a.p,h=point(a.h,{.38f,.04f,0});
 float drift=.18f*sinf(t*.18f-.40f)+.075f*sinf(t*.75f);
 switch(c){
 case 0:{ // continuous contact profile; gradual retreat only after visible lift
   float follow=ramp(impact+.46f,impact+1.47f,t);float lag=pulse(impact,impact+.24f,impact+.79f,t); k.target=p+V{.33f+lag*.48f,-.065f-lag*.13f,0};
   k.eye=k.target+V{.27f+drift,1.10f+1.21f*follow,3.55f+2.0f*follow};k.fov=36;k.blur=2.5f;
   break;}
 case 1:k.target={-.48f,-.15f,.03f};k.eye={.1f+1.40f*drift,5.45f+q*.45f,9.40f};k.fov=44;k.blur=1.5f;break;
 case 2:k.target={-.22f,-1.48f,.10f};k.eye={-.73f+1.05f*drift,10.15f,-.19f};k.up={0,0,-1};k.fov=41;k.blur=.7f;break;
 case 3:k.target={1.25f+.47f*p.x,ground(1.77f,.42f)+.13f,.36f};k.eye=k.target+V{-.82f+.65f*drift,.78f,2.59f};k.fov=36;k.blur=4.5f;break;
 case 4:k.target={.24f,ground(.24f,0)+.37f,.035f};k.eye=k.target+V{1.24f+drift,1.35f,2.03f};k.fov=32;k.focus=len(k.target-k.eye);k.blur=5.3f;break;
 case 5:k.target=h+V{.10f,.014f,0};k.eye=k.target+V{1.67f+.56f*drift,1.10f,1.87f};k.fov=36;k.blur=5;break;
 case 6:k.target={.30f,-.35f,.0f};k.eye=k.target+V{-1.62f+drift,2.90f,5.78f};k.fov=36;k.blur=2.0f;break;
 case 7:k.target={.48f,-.006f,0};k.eye=k.target+V{.94f+drift,2.94f,2.77f};k.fov=32;k.diagram=1;k.key=.72f;k.sky=.93f;k.blur=1.35f;break;
 case 8:k.target={.65f,-.03f,.06f};k.eye=k.target+V{.17f+drift,3.9f,1.65f};k.fov=32;k.diagram=1;k.key=.64f;k.sky=.93f;k.blur=1.0f;break;
 case 9:k.target={-.53f,-.42f,0};k.eye=k.target+V{-.36f+drift,4.98f,8.91f};k.fov=39;k.dark=.50f;k.blur=3.7f;break;
 case 10:k.target=p+V{.15f,-.13f,0};k.eye=k.target+V{1.01f+.76f*drift,1.77f,3.0f};k.fov=37;k.blur=3.25f;break;
 case 11:k.target={2.46f,ground(2.46f,.60f)+.109f,.60f};k.eye=k.target+V{-1.17f+drift,.60f,1.84f};k.fov=35;k.blur=5.3f;break;
 case 12:k.target=p+V{.22f,-.16f,0};k.eye=k.target+V{-.83f+drift,1.35f,-3.69f};k.fov=37;k.blur=3.2f;break;
 case 13:k.target={-4.59f,.27f,-.10f};k.eye=k.target+V{-.53f+drift,.91f,3.65f};k.fov=32;k.blur=5.f;break;
 case 14:k.target={-.10f,-.59f,0};k.eye={-5.44f+.4f*drift,7.24f,6.90f};k.fov=44;k.dark=.12f;k.blur=2;break;
 case 15:k.target={1.53f,-.30f,1.13f};k.eye={.10f+.55f*drift,3.93f,-6.14f};k.fov=36;k.blur=1.85f;break;
 case 16:k.target={0,-.82f,.08f};k.eye={-1.5f+.85f*drift,2.35f,7.27f};k.fov=38;k.blur=2.80f;break;
 case 17:k.target=p+V{.30f,-.034f,.03f};k.eye=k.target+V{-.45f+drift,3.51f,2.74f};k.fov=35;k.blur=2.10f;break;
 case 18:k.target={.26f,ground(.26f,0)+.22f,.02f};k.eye=k.target+V{.91f+drift,1.13f,-2.49f};k.fov=31;k.blur=4.2f;break;
 case 19:k.target={.52f,-.05f,.02f};k.eye=k.target+V{.76f+drift,1.85f,3.62f};k.fov=33;k.diagram=1;k.key=.69f;k.sky=.93f;k.blur=1.4f;break;
 default:k.target=p;k.eye=p+V{.40f,1.4f,3.6f};
 }
 if(!k.diagram)k.eye.y=std::max(k.eye.y,ground(k.eye.x,k.eye.z)+.23f);
 if(k.focus<=0)k.focus=len(k.target-k.eye);
 return k;
}
struct Set {
 Mesh soil=pitMesh(),ball=sweep(18,18,0),head=sweep(29,26,1),taper=sweep(15,12,2),rod=sweep(10,8,4),thread=sweep(5,5,4),jaw=sweep(19,14,3),grain=sweep(3,5,5);
 std::vector<Mesh*> list={&soil,&ball,&head,&taper,&rod,&thread,&jaw,&grain};
 std::vector<Instance> earth; V antPosition,larvaPosition={.19f,-2.01f,.02f};
 V shell=rgb(0x51382d),body=rgb(0x49352c),gaster=rgb(0x362b24),limb=rgb(0x865338),joint=rgb(0x4c3426),edge=rgb(0xc19362),eye=rgb(0x161b1a),mand=rgb(0x604027);
 Set(){for(auto m:list)m->bind();grain.shadow=false;thread.shadow=false;
   Rng r{0x76d5bc18u};for(int i=0;i<1250;i++){
    float x=r.r(-6.2f,6.2f),z=r.r(-6.2f,6.2f);if(hypotf(x,z)>7.f)continue;
    float d=r.r(.013f,.027f)*(i%77==0?1.75f:1.f),h=ground(x,z);
    int c[]={0xc69b6a,0xf0c78f,0xdeb27c,0xa97d54,0xcaa66e,0xe9cc9e,0xc5a27d,0x62523c};
    M m=mul(loc({x,h-d*.12f,z}),mul(ry(r.r(0,tau)),mul(rz(r.r(-.65f,.65f)),size({d*r.r(1.0f,1.7f),d*r.r(.42f,.92f),d*r.r(.7f,1.28f)}))));
    V co=rgb(c[(i%97==0)?7:i%7]);earth.push_back({m,{co.x,co.y,co.z,4.f}});
   }
 }
 void ballAt(M m,V p,V s,V c,float mat=1){ball.add(tr(m,p,s),c,mat);}
 void bar(V p,V q,float r,V co,float mat=1,bool thin=false){(thin?thread:rod).add(rodmat(p,q,r),co,mat);}
 void branch(M m,V a,V b,float r,V co,float mat=1,bool thin=false){bar(point(m,a),point(m,b),r,co,mat,thin);}
 void setae(M parent,V at,V scale,int count,int seed,float length,float thickness){
   Rng r{uint32_t(seed)};for(int k=0;k<count;k++){
      float y=r.r(-.45f,.99f),a=r.r(0,tau),rr=sqrtf(1-y*y);V d={rr*cosf(a),y,rr*sinf(a)},p=at+V{d.x*scale.x,d.y*scale.y,d.z*scale.z}*.983f;
      V q=p+(d+V{-.36f,.17f,0})*r.r(length*.35f,length);branch(parent,p,q,thickness*r.r(.58f,1.2f),k%7==0?edge:rgb(0x422b21),3,true);
   }
 }
 void ant(const Motion&a,float t,bool inset=false,bool cutaway=false){
   antPosition=a.p;M b=a.torso,h=a.h;
   if(!inset){
    head.add(tr(b,{.221f,.020f,0},{.263f,.191f,.183f}),shell,1);
    taper.add(tr(b,{-.13f,.001f,0},{.33f,.146f,.154f}),body,1);
    taper.add(tr(b,{-.369f,-.046f,0},{.186f,.127f,.122f}),shell,1);
    ballAt(b,{-.560f,-.057f,0},{.135f,.074f,.089f},joint);
    head.add(tr(b,{-.646f,.015f,0},{.106f,.132f,.087f}),body,1);
    M g=mul(b,mul(loc({-.96f,-.007f,0}),rz(-.16f+.045f*sinf(t*3))));
    taper.add(tr(g,{-.086f,.014f,0},{.477f,.258f,.266f}),gaster,1);
    taper.add(tr(g,{.086f,.013f,0},{.274f,.260f,.267f}),rgb(0x463125),1);
    taper.add(tr(g,{-.255f,.012f,0},{.259f,.227f,.225f}),rgb(0x34261f),1);
    setae(g,{-.086f,.014f,0},{.461f,.249f,.249f},81,10,.043f,.0024f);
    setae(b,{.091f,.007f,0},{.398f,.174f,.176f},45,11,.034f,.0022f);
   }
   if(!cutaway)head.add(tr(h,{.230f,.039f,0},{.338f,.216f,.267f}),shell,1);
   else {
    // Open-view *illustration*: two elastic elements, not a CT reconstruction.
    // The seen elements are the capsule walls and two elongated muscle–attachment units.
    head.add(tr(h,{.205f,-.126f,0},{.350f,.072f,.267f}),rgb(0x543b28),1);
    for(int s:{-1,1}){
     float load=ramp(.26f,2.88f,t)*(1-ramp(2.96f,3.23f,t));
     M a0=mul(h,ry(s*(.045f+.04f*load)));
     head.add(tr(a0,{.18f,-.012f,s*.215f},{.332f,.119f,.071f-.012f*load}),rgb(0x61a8a7),5);
     taper.add(tr(mul(a0,rz(-.09f)),{.106f,.005f,s*.102f},{.275f+.045f*load,.095f,.094f}),rgb(0xc16d49),5);
     branch(h,{.21f,.027f,s*.098f},{.544f,-.020f,s*.150f},.026f,rgb(0xe1bf7a),6);
     for(int j=0;j<9;j++){
      float x=-.056f+.043f*j;branch(h,{x,.080f,s*.081f},{x+.045f,.021f,s*.156f},.0065f,rgb(0xeaa981),5,true);
     }
    }
   }
   for(int s:{-1,1}){
    if(!cutaway){
     ballAt(h,{.353f,.092f,s*.219f},{.066f,.058f,.047f},eye,2);
     ballAt(h,{.477f,.038f,s*.155f},{.064f,.067f,.061f},joint,1);
    }
    M j=mandible(h,s,a.jaw);jaw.add(j,mand,1);
    for(int i=0;i<3;i++){
      float u=.70f+.107f*i,z=-.76f*powf(u,1.7f)-.19f;
      V p=point(j,{u,-.06f,z}),q=point(j,{u+.031f,-.12f,z-.45f+.067f*i});
      bar(p,q,.019f-.0032f*i,mand,1);
    }
    // Elbowed 12-segment antenna, rooted above and separate from the mandible.
    if(!cutaway){
     V root={.433f,.111f,s*.119f},bend={.855f,.218f+.049f*sinf(t*4.4f+s),s*(.395f+.067f*cosf(t*4.f+s))};
     V dst={1.37f+.11f*cosf(t*2.9f+s),.091f+.084f*sinf(t*3.2f+s),s*(.570f+.15f*sinf(t*3+s))};
     if(a.head<-.38f){bend.y-=.042f;dst.y=-.049f;}
     branch(h,root,bend,.017f,limb);V last=bend;
     for(int i=1;i<=10;i++){float v=i/10.f;V q=mix(bend,dst,v)+V{.098f*sinf(pi*v),.048f*sinf(pi*v),s*.027f*sinf(pi*v)};branch(h,last,q,.0135f*(1-.63f*v),edge,1,true);last=q;}
    }
   }
   if(!cutaway)setae(h,{.23f,.039f,0},{.329f,.215f,.253f},85,212,.036f,.0022f);
   if(inset)return;
   for(int i=0;i<6;i++){
    int leg=i/2,s=i%2?1:-1;float X[]={.22f,-.063f,-.306f};
    V hip=point(b,{X[leg],-.10f,s*.132f});
    V coxa=point(b,{X[leg]-.028f,-.152f,s*.230f});
    V toe=a.toes[i],ankle=mix(toe,coxa,.185f)+V{0,.050f,0},diff=ankle-coxa,d=norm(diff);
    float D=std::max(.001f,len(diff)),L1=.355f+leg*.038f,L2=.463f+leg*.020f;
    float ll=std::clamp((D*D+L1*L1-L2*L2)/(2*D),.09f,L1*.94f);
    V out=point(b,{0,.68f,s*1.25f})-a.p, bend=norm(out-d*dot(out,d));V knee=coxa+d*ll+bend*sqrtf(std::max(0.f,L1*L1-ll*ll));
    bar(hip,coxa,.062f,joint);bar(coxa,knee,.056f+leg*.003f,limb);ballAt({},knee,{.043f,.040f,.041f},joint);
    bar(knee,ankle,.031f+leg*.002f,rgb(0x955334));
    V prev=ankle;for(int j=1;j<=4;j++){float u=j/4.f;V p=mix(ankle,toe,u)+V{0,.012f*sinf(pi*u),0};bar(prev,p,.023f*(1-.62f*u),limb);prev=p;}
    V fwd=norm(V{toe.x-ankle.x,0,toe.z-ankle.z});
    for(int k:{-1,1})bar(toe,toe+fwd*.048f+V{-fwd.z*k*.013f,-.005f,fwd.x*k*.013f},.007f,joint,1,true);
    for(int j=0;j<7;j++){V p=mix(knee,ankle,(j+.38f)/8.f);V q=p+V{-.022f,.023f,s*.028f};bar(p,q,.0028f,edge,3,true);}
   }
 }
 void larva(float t,float attack=1){
   float f=0;for(float t0:{.38f,1.41f,2.56f,6.05f,8.24f,10.5f})f+=pulse(t0,t0+.14f,t0+.42f,t)*.73f;
   f*=attack;V p={.028f,ground(.03f,0)+.124f+.17f*f,-.040f};larvaPosition=p;
   M m=mul(loc(p),mul(ry(.128f+sinf(.7f*t)*.07f),rz(.06f+f*.46f)));
   V car=rgb(0x786343),lobes=rgb(0x746145),tooth=rgb(0x58301e);
   taper.add(tr(m,{-.420f,-.168f,0},{.544f,.235f,.330f}),lobes,3);
   for(int i=0;i<6;i++)head.add(tr(m,{-.748f+i*.108f,-.160f,0},{.133f,.225f+.009f*i,.266f+.029f*sinf(pi*i/7)}),i%2?lobes:car,3);
   head.add(tr(m,{.097f,.028f,0},{.250f,.113f,.238f}),car,3);
   for(int s:{-1,1}){
    V pr={.237f,.014f,s*.156f};float o=.237f+.035f*sinf(1.1f*t+s)+f*.09f;
    for(int i=1;i<=14;i++){
      float u=i/14.f;V q={.237f+.63f*u,.014f+.375f*u+.097f*u*u,s*(.156f+o*sinf(u*pi*.80f)-.177f*u*u)};
      branch(m,pr,q,.053f*(1-.84f*u),tooth,1);pr=q;
      if(i==5||i==8||i==11){V toothEnd=q+V{.041f,.023f,-s*.074f};branch(m,q,toothEnd,.022f*(1-.30f*u),tooth,1);}
    }
    for(int i=0;i<3;i++)ballAt(m,{.147f-.031f*i,.103f-.010f*i,s*(.181f+.01f*i)},{.019f,.015f,.015f},eye,2);
   }
   setae(m,{-.33f,-.030f,0},{.468f,.208f,.335f},122,715,.060f,.0032f);
   setae(m,{.106f,.023f,0},{.235f,.101f,.228f},77,718,.041f,.0025f);
 }
 void grains(V src,float t,int count,int seed,float ver,float size,float aim){
   if(t<0||t>1.4f)return;
   Rng r{uint32_t(seed)};
   for(int i=0;i<count;i++){
    float tt=t-r.r(0,.13f);float s=r.r(.04f,1.38f),v=r.r(.37f,2.64f)*ver,angle=aim+r.r(-.91f,.91f);
    V co=rgb(i%5?0xcaa16e:0xffe0ae);
    float x=src.x+cosf(angle)*tt*s,z=src.z+sinf(angle)*tt*s,y=src.y+tt*v-1.98f*tt*tt;
    float rr=size*r.r(.32f,1.61f);float h=ground(x,z);
    if(tt>=0&&tt<1.31f&&y>h-rr*.4f){rr*=1-ramp(1.04f,1.4f,tt)*.65f;
     grain.add(mul(loc({x,y,z}),mul(rz(tt*3+angle),::ant::size({rr*1.45f,rr*.77f,rr}))),co,4);
    }
   }
 }
 void silt(float t,int mode){
   Rng r{81262};
   for(int i=0;i<202;i++){
    float j=r.r(0,1),x=r.r(1.12f,4.28f),z=r.r(-.55f,1.11f),dr=r.r(.15f,.55f),s=r.r(.008f,.021f),phase=fmod(t*.61f+j,1);
    x-=phase*dr;float f=sinf(phase*pi);float y=ground(x,z)+.011f+f*f*r.r(.01f,.058f);
    if(mode==3)s*=.76f;
    grain.add(tr({}, {x,y,z},{s,s*.48f,s*.80f}),rgb(i%9==0?0xf3c894:0xbb8e5e),4);
   }
 }
 void litter(){
   Rng r{3546};for(int t=0;t<22;t++){
    float a=r.r(0,tau),d=r.r(4.55f,8.1f),x=d*cosf(a),z=d*sinf(a),h=ground(x,z),l=r.r(.24f,1.14f),o=r.r(0,tau);V prev={x,h+.024f,z};
    for(int i=1;i<7;i++){float f=i/6.f;V q={x+cosf(o)*f*l,h+.018f+.028f*sinf(pi*f),z+sinf(o)*f*l};q.y=std::max(q.y,ground(q.x,q.z)+.012f);bar(prev,q,.017f*(1-.65f*f),rgb(t%2?0x8a5633:0x665335),3,true);prev=q;}
   }
 }
 void set(int mode,float t,const M& vp,float lod){
   for(auto m:list)m->live.clear();
   larvaPosition={.032f,-1.98f,.01f};
   if(mode==5||mode==6||mode==7||mode==12){
     Motion a=study(t,mode!=5);if(mode==12){a.jaw=.034f;matrices(a);}ant(a,t,mode==6||mode==7,mode==7);return;
   }
   soil.add({},rgb(0xcfad79),0);
   // Skip the tiny geometric relief grains beyond the camera frustum. Surface
   // detail remains in the sand material, including in full-bowl views.
   for(size_t i=0;i<earth.size();i++){
     if(lod>.5f && i%7==1)continue;
     auto& g=earth[i];const float *m=vp.a;float x=g.mat.a[12],y=g.mat.a[13],z=g.mat.a[14];
     float tx=m[0]*x+m[4]*y+m[8]*z+m[12],ty=m[1]*x+m[5]*y+m[9]*z+m[13],w=m[3]*x+m[7]*y+m[11]*z+m[15];
     if(w>-.07f && fabsf(tx)<w+.20f && fabsf(ty)<w+.20f)grain.live.push_back(g);
   }
   litter();
   Motion a=action(t,mode==4);
   if(mode==0||mode==4){ant(a,t);larva(t);
     for(float q:{.38f,1.41f,2.56f})grains({.45f,ground(.45f,.05f)+.29f,.05f},t-q,134,129911+int(q*10),.62f,.018f,-.01f);
     Motion f=planted(impact);V src=(f.tips[0]+f.tips[1])*.5f;src.y+=.043f;
     grains(src,t-impact,214,9821711,.88f,.022f,2.97f);
     if(mode==4)grains({1.72f,ground(1.72f,2.73f)+.065f,2.73f},t-(impact+(5.3f-impact)*.56f),134,51187,.47f,.018f,-1.87f);
     if(mode==0)grains({-5.08f,ground(-5.08f,-.51f)+.055f,-.51f},t-land,65,91672,.31f,.016f,.21f);
     if(t<3.25f)silt(t,mode);
   }else if(mode==1){ant(planted(std::min(t,3.21f)),t);larva(t);silt(t,mode);
   }else if(mode==3){antPosition={20,0,20};larva(t);
     for(float q:{.38f,1.41f,2.56f,6.05f,8.24f,10.5f})grains({.49f,ground(.49f,.06f)+.23f,.06f},t-q,153,81922+int(q*100),.77f,.018f,-.02f);
     silt(t,mode);
   }else if(mode==8){antPosition={20,0,20};larva(t,.18f);silt(t,mode);
   }else if(mode==9){ant(action(land+0.13f+std::min(t,1.6f)),t);larva(t,.12f);
   }else if(mode==2){antPosition={20,0,20};silt(t,mode);
   }else if(mode==11){ant(climb(t),t);larva(t,.08f);silt(t,mode);
   }else if(mode==10){ // a clean slope view for labels; partial stillness, animated grains
     antPosition={20,0,20};larva(t,.08f);if(t<8)silt(t*.5f,mode);
   }
 }
};
}
