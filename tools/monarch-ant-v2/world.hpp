#pragma once
#include "lens.hpp"
namespace cinema {
constexpr float wallClock=4.4728f;
constexpr float restrainedJawAngle=-.119f; // model tips meet, relative to hinge-zero reference
inline Motion failedJump(float t){
 if(t<=impact)return planted(std::max(0.f,t));
 static const Motion initial=planted(impact);Motion a=initial;
 constexpr float settled=5.37f;V end={.73f,0,1.77f};
 V w={1.76f,ground(1.76f,2.70f)+.63f,2.70f};
 float u=sat((t-impact)/(wallClock-impact)),v=sat((t-wallClock)/(settled-wallClock));
 if(t<wallClock)a.p=mix(initial.p,w,u)+V{0,1.43f*sinf(pi*u),0};
 else{
   a.p=mix(w,end,1-(1-v)*(1-v));a.p.y=ground(a.p.x,a.p.z)+mix(.63f,.448f,ramp(0,1,v))+.027f*sinf(v*pi);
 }
 a.fly=t<wallClock;a.yaw=initial.yaw+1.42f*ramp(.05f,1,u)+.70f*ramp(.14f,.93f,v);
 a.pitch=mix(initial.pitch,.072f,ramp(0,1,u))+.19f*sinf(pi*u)-.23f*pulse(0,.34f,.96f,v);
 a.roll=.46f*sinf(pi*u)+.34f*ramp(.58f,1,u)*(1-ramp(.04f,.89f,v));
 a.jaw=mix(initial.jaw,.32f,ramp(.39f,1,u))+.10f*ramp(.1f,.84f,v);a.head=mix(initial.head,.029f,ramp(0,.53f,u));
 matrices(a);
 // The impact on the sidewall is not permission to bury the rigid head mesh.
 // Aim both jaws above the slope until the closest tip meets it at the wall.
 float clearance=mix(.0015f,.086f,ramp(0,.29f,u));
 if(t<wallClock){clearance=mix(clearance,.009f,ramp(.71f,1,u));if(u>.88f)solveContact(a,clearance);}
 else clearance=mix(.009f,.072f,ramp(.06f,.68f,v));
 if(a.clear<clearance||t==wallClock)solveContact(a,clearance);
 if(a.clear<0){a.p.y+=clearance-a.clear;matrices(a);}
 a.support=0;
 for(int i=0;i<6;i++){
  int k=i/2,s=i%2?1:-1;float x[]={.52f,.014f,-.65f},z[]={.54f,.65f,.50f};
  V toe=point(a.torso,{x[k]-.18f*sinf(pi*u),-.38f,s*z[k]});
  if(a.fly)toe=mix(initial.toes[i]+(a.p-initial.p),toe,ramp(0,.32f,u));
  else toe.x+=.060f*sinf(v*9.9f+i*2.1f)*sinf(pi*v);
  float y=ground(toe.x,toe.z)+.012f;
  if(t>wallClock-.047f&&t<wallClock+.13f&&k==0)toe.y=y+.08f*(1-ramp(.965f,1,u));
  else if(!a.fly)toe.y=y+std::max(0.f,.047f*sinf(v*8.8f+i))*sinf(pi*v);
  else toe.y=std::max(toe.y,y);
  a.toes[i]=toe;a.support+=toe.y<y+.013f;
 }
 return a;
}
inline Motion pose(int set,float t){
 if(set==0)return action(t);
 if(set==4)return failedJump(t);
 if(set==1)return planted(std::min(t,3.24f));
 if(set==9)return action(land+std::clamp(t,.0f,1.95f));
 if(set==11)return climb(t);
 if(set==13){
  Motion a=failedJump(5.37f);float p=ramp(.25f,3.20f,t);
  a.p=mix(a.p,V{.64f,-1.7f,.35f},p);a.p.y=ground(a.p.x,a.p.z)+mix(.42f,-.34f,ramp(1.62f,3.32f,t));
  a.yaw=2.1f+.19f*sinf(t*2.3f);a.pitch=-.074f+.14f*sinf(4*t);a.head=-.17f+.05f*sinf(3.2f*t);a.jaw=mix(.41f,.18f,p);matrices(a);
  a.support=0;
  for(int i=0;i<6;i++){int k=i/2,s=i%2?1:-1;float x[]={.51f,.02f,-.64f};float d=.065f*sinf(t*12+i*2.1f);
   V q=point(a.torso,{x[k]+d,-.42f,s*(.52f+(k==1?.10f:0.f))});
   q.y=ground(q.x,q.z)+mix(.012f,-.17f,ramp(2.32f,3.32f,t))+fmaxf(0,d*.39f);a.toes[i]=q;a.support+=d<.025f;
  }
  return a;
 }
 if(set==5||set==6||set==7||set==12||set==16){
   Motion a=study(t,set!=5&&set!=12);
   if(set==5){a.jaw=mix(.49f,.158f,ramp(.35f,2.09f,t))+.018f*sinf(5.3f*t);matrices(a);}
   if(set==12){a.jaw=.029f;matrices(a);}
   if(set==16){a.jaw=1.36f-.018f*sinf(t*2);a.pitch=-.028f;matrices(a);}
   return a;
 }
 return planted(1.23f);
}
// Continuous head and gaster silhouettes for the macro lens. No intersecting
// abdomen balls or exposed spherical hinge caps in the worker model.
inline Mesh chitinLoft(int shape){
 Mesh m;int L=shape==1?28:32,K=23;
 for(int i=0;i<=L;i++){
  float u=float(i)/L,x=-cosf(u*pi),r=std::max(.00045f,sinf(u*pi));
  for(int j=0;j<=K;j++){
   float v=float(j)/K,a=tau*v,cs=cosf(a),sn=sinf(a),y,z;
   if(shape==1){
    r=std::max(.00045f,sinf(u*pi));float w=powf(r,.55f)*(.94f-.11f*x+.12f*expf(-powf((x+.33f)*2.9f,2)));
    y=powf(r,.71f)*copysignf(powf(fabsf(cs),.82f),cs)*(.92f-.16f*x);
    z=w*copysignf(powf(fabsf(sn),.83f),sn);
    y+=.020f*sinf(u*pi)*sn*sn;
   }else{
    float d=.026f*(expf(-powf((u-.395f)*135,2))+expf(-powf((u-.565f)*144,2))+expf(-powf((u-.733f)*159,2)));
    float w=r*(1.f-.12f*x)-d;y=w*cs;z=w*sn;
   }
   m.v.push_back({{x,y,z},{},{u,v}});
  }
 }
 for(int i=0;i<L;i++)for(int j=0;j<K;j++){
   unsigned a=i*(K+1)+j,b=a+K+1;m.idx.insert(m.idx.end(),{a,a+1,b,b,a+1,b+1});
 }
 normals(m);for(int i=0;i<=L;i++){auto &a=m.v[i*(K+1)].n,&b=m.v[i*(K+1)+K].n;a=b=norm(a+b);}return m;
}
inline Mesh mandiblesLarva(){
 Mesh m;constexpr int N=23,K=9;
 auto axis=[](float u){return V{.630f*u,.375f*u+.097f*u*u,.270f*sinf(u*pi*.80f)-.177f*u*u};};
 for(int i=0;i<=N;i++){
  float u=float(i)/N,w=.054f*powf(std::max(.001f,1-u),.68f),f=std::max(.04f,sinf(pi*(.12f+.88f*u)));
  V p=axis(u),d=norm(axis(u+.005f)-axis(u-.005f)),h=norm(cross(d,{0,0,1})),l=norm(cross(h,d));
  for(int j=0;j<=K;j++){
   float z=tau*j/K; m.v.push_back({p+(h*(cosf(z)*.87f)+l*(sinf(z)*(.81f+.19f*f)))*w,{},{u,float(j)/K}});
  }
 }
 for(int i=0;i<N;i++)for(int j=0;j<K;j++){
  unsigned a=i*(K+1)+j,b=a+K+1;m.idx.insert(m.idx.end(),{a,b,a+1,b,b+1,a+1});
 }
 normals(m);
 // Align all normals consistently to the outward side of the hooked tube.
 if(dot(m.v[(K+1)*8+1].n,m.v[(K+1)*8+1].p-axis(8.f/N))<0)
  for(auto&v:m.v)v.n=v.n*-1.f;
 return m;
}
// Sawn-shell surface for the diagram. Each continuous rim tapers into an
// anterior lever; the solid interior is exposed without transparent panels.
inline Mesh capsuleHalf(){
 Mesh m;constexpr int L=25,K=14;
 for(int i=0;i<=L;i++){
  float u=float(i)/L,x=-cosf(u*pi),r=std::max(.025f,powf(sinf(u*pi),.58f));
  for(int j=0;j<=K;j++){
   float v=float(j)/K,b=mix(-1.37f,.33f,v);
   float y=.85f*sinf(b)*r+(u-.54f)*.24f*v;
   float z=(.92f-.13f*x)*r*cosf(b);
   m.v.push_back({{x,y,z},{},{u,v}});
  }
 }
 for(int i=0;i<L;i++)for(int j=0;j<K;j++){
  unsigned a=i*(K+1)+j,b=a+K+1;m.idx.insert(m.idx.end(),{a,b,a+1,b,b+1,a+1});
 }
 normals(m);if(m.v[12*(K+1)+10].n.z<0)for(auto&v:m.v)v.n=v.n*-1.f;
 return m;
}
class World:public Set {
public:
 Mesh cop=chitinLoft(1),abd=chitinLoft(2),hook=mandiblesLarva(),capsule=capsuleHalf();
 float detail=1;
 World(){
  shell=rgb(0x4f352a);body=rgb(0x493229);gaster=rgb(0x382b23);limb=rgb(0x795238);
  joint=rgb(0x4a3028);mand=rgb(0x6d4427);edge=rgb(0xbb9061);eye=rgb(0x171d1c);
  for(auto* m:{&cop,&abd,&hook,&capsule}){m->bind();list.push_back(m);}
  // Avoid tessellating a sub-pixel bristle, or a grain, as a round high-polygon prop.
  thread=sweep(2,3,4);thread.bind();rod=sweep(5,7,4);rod.bind();grain=sweep(2,4,5);grain.bind();
  ball=sweep(10,11,0);ball.bind();
 }
 std::vector<V> shadowCasts;
 void reset(){for(auto m:list)m->live.clear();}
 void quartz(const M&vp){
  for(auto&g:earth){const float *m=vp.a;float x=g.mat.a[12],y=g.mat.a[13],z=g.mat.a[14];
   float tx=m[0]*x+m[4]*y+m[8]*z+m[12],ty=m[1]*x+m[5]*y+m[9]*z+m[13],w=m[3]*x+m[7]*y+m[11]*z+m[15];
   if(w>0 && fabsf(tx)<w+.16f && fabsf(ty)<w+.16f)grain.live.push_back(g);
  }
 }
 void scrub(){
  Rng r{69290};
  for(int i=0;i<38;i++){
   float a=r.r(0,tau),d=r.r(4.9f,9.24f),x=d*cosf(a),z=d*sinf(a),b=r.r(0,tau),h=ground(x,z),l=r.r(.18f,.83f);
   V p={x,h+.012f,z};
   for(int k=1;k<=6;k++){
    float u=k/6.f;V q={x+l*u*cosf(b),h+.092f*sinf(pi*u*.64f),z+l*u*sinf(b)};
    q.y=std::max(q.y,ground(q.x,q.z)+.016f);bar(p,q,.0135f*(1-.67f*u),rgb(i%4?0x655943:0x5d6c42),3,true);p=q;
   }
  }
  // Poorly focused grasses beyond the trap edge, held well out of the action.
  for(int i=0;i<5;i++){
   float x=r.r(-8.2f,-1.2f),z=r.r(-6.6f,-4.65f),h=ground(x,z),a=r.r(-.25f,.31f),b=r.r(.27f,.63f);V p{x,h,z};
   for(int j=1;j<6;j++){
    float u=j*.2f;V q{x+a*u*u,h+u*b,z+.08f*u};bar(p,q,.018f*(1-u*.89f),rgb(0x5b6b48),3,true);p=q;
   }
  }
 }
 void pads(int mode){
  int n=mode==14?3:2;float spacing=mode==14?2.67f:2.68f;
  for(int i=0;i<n;i++){
   float x=(i-(n-1)*.5f)*spacing;
   taper.add(tr({}, {x,-.612f,0},{1.24f,.179f,1.13f}),rgb(0x7d6f57),8);
   taper.add(tr({}, {x,-.757f,0},{1.27f,.088f,1.16f}),rgb(0x596364),5);
   taper.add(tr({}, {x,-.842f,0},{1.25f,.028f,1.14f}),rgb(0x354545),5);
  }
 }
 void staticScene(int mode,const Lens& l,const M &vp){
  reset();
  if(l.stage){if(mode>=14&&mode<=15)pads(mode);}
  else{soil.add({},rgb(0xd1bd95),0);quartz(vp);scrub();}
 }
 void worker(const Motion&a,float t,bool inset=false){
  M h=a.h,b=a.torso;antPosition=a.p;
  const bool macro=detail>.63f;
  if(!inset){
   cop.add(tr(b,{.172f,.014f,0},{.296f,.162f,.157f}),body,1);
   taper.add(tr(b,{-.142f,-.018f,0},{.325f,.132f,.140f}),rgb(0x4d342a),1);
   taper.add(tr(b,{-.404f,-.055f,0},{.140f,.094f,.107f}),shell,1);
   taper.add(tr(b,{-.631f,-.047f,0},{.175f,.060f,.060f}),joint,1);
   cop.add(tr(b,{-.656f,-.002f,0},{.087f,.122f,.073f}),shell,1);
   M g=mul(b,mul(loc({-.978f,-.018f,0}),rz(-.162f+.042f*sinf(t*3.6f))));
   abd.add(tr(g,{-.059f,.006f,0},{.509f,.247f,.238f}),gaster,1);
   setae(g,{-.056f,.010f,0},{.490f,.242f,.230f},macro?81:26,714,.050f,.0019f);
   setae(b,{.066f,.010f,0},{.394f,.152f,.151f},macro?53:20,119,.040f,.0021f);
  }
  cop.add(tr(h,{.232f,.039f,0},{.337f,.203f,.258f}),shell,1);
  for(int s:{-1,1}){
    M eyes=mul(h,ry(s*.19f));
    ballAt(eyes,{.381f,.089f,s*.162f},{.073f,.052f,.041f},eye,2);
    setae(h,{.179f,.045f,s*.004f},{.312f,.191f,.235f},macro?41:16,283+(s+1)*13,.048f,.0020f);
    M j=mandible(h,s,a.jaw);jaw.add(j,mand,1);
    for(int k=0;k<5;k++){
     float u=.65f+.071f*k;
     V p=point(j,{u,-.056f,-.76f*powf(u,1.7f)-.17f}),q=point(j,{u+.043f,-.140f,-.76f*powf(u,1.7f)-.53f+.048f*k});
     bar(p,q,.0153f-.0018f*k,mand,1);
    }
    V root={.438f,.107f,s*.125f},bend={.838f,.192f+.049f*sinf(t*4.0f+s),s*(.435f+.055f*cosf(t*4.2f+s))};
    V dst={1.405f+.08f*cosf(t*3.7f+s),.067f+.080f*sinf(t*3.0f+s),s*(.687f+.123f*sinf(t*3.6f+s))};
    if(a.head<-.35f){bend.y-=.04f;dst.y=-.065f;}
    branch(h,root,bend,.0165f,limb);V last=bend;
    for(int i=1;i<=11;i++){float u=i/11.f;V q=mix(bend,dst,u)+V{.095f*sinf(pi*u),.051f*sinf(pi*u),s*.03f*sinf(pi*u)};branch(h,last,q,.0129f*(1-.63f*u),i%5?limb:edge,1,true);last=q;}
    for(int i=0;i<6;i++){float u=i/6.f;V p={.451f+.063f*u,-.041f-.050f*u,s*(.126f+.084f*u)};branch(h,p,p+V{.037f,-.029f,s*.024f},.0035f,edge,3,true);}
  }
  if(inset)return;
  for(int i=0;i<6;i++){
   int r=i/2,s=i%2?1:-1;float x[]={.21f,-.063f,-.301f},L[]={.367f,.389f,.419f};
   V hip=point(b,{x[r],-.107f,s*.130f}),cx=point(b,{x[r]-.047f,-.161f,s*.219f});
   V toe=a.toes[i],ankle=mix(toe,cx,.161f)+V{0,.058f,0}; V d0=ankle-cx,d=norm(d0);float D=std::max(.004f,len(d0)),l=L[r],l2=.46f+.025f*r;
   float along=std::clamp((D*D+l*l-l2*l2)/(2*D),.087f,l*.96f);V out=point(b,{-.13f,.53f,s*1.10f})-a.p;
   V knee=cx+d*along+norm(out-d*dot(out,d))*sqrtf(l*l-along*along);
   bar(hip,cx,.047f,joint);bar(cx,knee,.044f+r*.004f,limb);bar(knee,ankle,.026f+r*.0015f,rgb(0x8a5c3f));
   V ji=norm(knee-cx);bar(knee-ji*.033f,knee+norm(ankle-knee)*.040f,.028f,limb);
   V prev=ankle;
   for(int k=1;k<=4;k++){float u=k*.25f;V p=mix(ankle,toe,u)+V{0,.014f*sinf(pi*u),0};bar(prev,p,.0185f*(1-.59f*u),limb);prev=p;}
   V f=norm(V{toe.x-ankle.x,0,toe.z-ankle.z});
   for(int k:{-1,1})bar(toe,toe+f*.044f+V{-f.z*k*.012f,-.003f,f.x*k*.012f},.0062f,joint,1,true);
   for(int k=0;k<(macro?8:3);k++){V p=mix(knee,ankle,(k+.51f)/(macro?9.f:4.f));bar(p,p+V{-.020f,.023f,s*.024f},.0021f,edge,3,true);}
  }
  shadowCasts.push_back(a.p);
 }
 void antlion(float t,float attack){
  float f=0;for(float t0:{.38f,1.41f,2.56f,6.05f,8.24f,10.5f,12.3f})f+=pulse(t0,t0+.14f,t0+.45f,t)*.73f;
  f*=attack;V p={.028f,ground(.03f,0)+.119f+.171f*f,-.040f};larvaPosition=p;
  M m=mul(loc(p),mul(ry(.128f+sinf(.7f*t)*.09f),rz(.06f+f*.49f)));
  V car=rgb(0x7c6950),lobes=rgb(0x796849),tooth=rgb(0x542e1b);
  abd.add(tr(m,{-.425f,-.16f,0},{.52f,.22f,.335f}),lobes,3);
  cop.add(tr(m,{.094f,.026f,0},{.254f,.112f,.236f}),car,3);
  for(int s:{-1,1}){
    auto j=mul(m,mul(loc({.233f,.015f,s*.151f}),mul(ry(-s*(.071f*sinf(t*1.13f+s)+.139f*f)),size({1,1,float(s)}))));
    hook.add(j,tooth,1);
    for(float u:{.36f,.56f,.73f,.88f}){
     V q={.630f*u,.375f*u+.097f*u*u,.270f*sinf(u*pi*.80f)-.177f*u*u};
     branch(j,q,q+V{.035f,.016f,-.090f*(1-.55f*u)},.024f*(1-.56f*u),tooth,1);
    }
    for(int i=0;i<3;i++)ballAt(m,{.146f-.030f*i,.101f-.010f*i,s*(.181f+.009f*i)},{.013f,.013f,.014f},eye,2);
  }
  setae(m,{-.327f,-.034f,0},{.464f,.197f,.331f},detail>.63f?126:54,715,.075f,.0029f);
  setae(m,{.104f,.019f,0},{.232f,.108f,.226f},detail>.63f?65:27,718,.044f,.0022f);
 }
 bool inView(V p,const M&vp,float r){
  const float*m=vp.a;float w=m[3]*p.x+m[7]*p.y+m[11]*p.z+m[15];
  float x=m[0]*p.x+m[4]*p.y+m[8]*p.z+m[12],y=m[1]*p.x+m[5]*p.y+m[9]*p.z+m[13];
  return w+r>0 && fabsf(x)<w+r&&fabsf(y)<w+r*1.55f;
 }
 void mechanism(const Motion&a,float t){
  const M h=a.h;const float load=ramp(.32f,2.935f,t)*(1-ramp(2.955f,3.218f,t));
  const float rel=ramp(2.945f,3.233f,t);const V amber=rgb(0x91583b),gold=rgb(0xbda170),lobe=rgb(0x985b4c);
  taper.add(tr(h,{.233f,-.107f,.001f},{.338f,.061f,.227f}),rgb(0x574335),1);
  for(int i:{-1,1}){
   M wall=mul(h,mul(loc({.219f,-.012f,0}),mul(ry(i*(.006f+.092f*load)),size({.351f,.157f,i*(.257f-.032f*load)}))));
   capsule.add(wall,amber,1);
   V last{};
   for(int k=1;k<19;k++){
    float u=k/19.f,x=-cosf(u*pi),r=std::max(.025f,powf(sinf(u*pi),.58f));
    V q={x,.85f*sinf(.33f)*r+(u-.54f)*.24f,(.92f-.13f*x)*r*cosf(.33f)};
    if(k>1)branch(wall,last,q,.0086f-.0018f*fabsf(x),gold,5,true);
    last=q;
   }
   V attach={.504f+.037f*rel,-.031f,i*(.119f+.036f*load)},rear={-.071f,.021f,i*.093f};
   V middle=mix(rear,attach,.47f)+V{-.058f,.015f,-i*.017f};
   auto jac=mandible(h,i,a.jaw);jaw.add(jac,mand,1);
   ballAt(h,{.511f,-.049f,i*.150f},{.056f,.073f,.064f},joint,1);
   V lever=point(jac,{.185f,-.23f,-.062f});
   for(int q=0;q<9;q++){
    float f=q/8.f,ang=f*tau,sy=sinf(ang),cz=cosf(ang);
    V x=rear+V{.021f*sy,.050f*sy,.043f*cz},y=middle+V{-.029f*cz,.049f*sy,.064f*cz};
    V out=mix(attach,y,.27f);out.y+=sy*.019f;out.z+=cz*.024f;
    V m0=mix(x,y,.37f)+V{0,.008f*sy,.006f*cz};
    V m1=mix(y,out,.57f)+V{0,.006f*sy,0};
    float r=.0232f-.0022f*(q%3);V color=mix(lobe,rgb(0xbd836f),float(q%4)/5.f);
    branch(h,x,m0,r*.70f,color,6);branch(h,m0,y,r,color,6);branch(h,y,m1,r*.93f,color,6);branch(h,m1,out,r*.64f,color,6);
    if(q%2==0)branch(h,out,attach,.0068f,gold,7,true);
   }
   // The amber capsule presses one lug; the tensioned gold attachment pulls
   // the inset crank arm. Both act on the same revolute jaw joint.
   V shoulder={.400f+.072f*rel,-.016f,i*(.200f-.012f*rel+.017f*load)};
   V pad={.509f+.027f*rel,-.049f,i*(.184f-.009f*rel)};
   branch(h,shoulder,pad,.028f,amber,1);
   V v0=point(h,attach);bar(v0,mix(v0,lever,.5f)+V{0,.013f*load,0},.017f,gold,7);
   bar(mix(v0,lever,.5f)+V{0,.013f*load,0},lever,.015f,gold,7);
   ballAt({},lever,{.029f,.025f,.024f},gold,7);
  }
 }
 void collar(const Motion&u){
   // Schematic hold, not a claim about the size or chemistry of laboratory material.
   taper.add(tr(u.h,{.708f,-.083f,0},{.085f,.040f,.142f}),rgb(0x7b6850),3);
 }
 // At a true distal restraint the tips nearly meet. The small bond sits at
 // their contact, not wedged between the inner part of the shafts.
 void tipBond(const Motion&u){
   V l=u.tips[0],r=u.tips[1],m=(l+r)*.5f;
   ballAt({},m,{.029f,.018f,.021f},rgb(0xb6a887),7);
 }
 void actors(int m,float t,const Motion &a,const M&vp,bool feature=false){
  reset();shadowCasts.clear();
  if(m>=14&&m<=15){
   int n=m==14?3:2;float spacing=2.67f;
   for(int i=0;i<n;i++){
     float offset=(i-(n-1)*.5f)*spacing;
     Motion u=study(t*.91f+i*.33f,false);
     bool bound=i==n-1;
     u.jaw=bound?(feature?restrainedJawAngle:.038f):mix(.49f,1.32f,.5f+.5f*sinf(t*1.7f+i*.41f));
     if(m==15&&!bound)for(float cue:{2.38f,4.43f,7.54f,9.f})u.jaw=mix(u.jaw,feature?restrainedJawAngle:.046f,pulse(cue-.14f,cue,cue+.34f,t));
     u.yaw=pi*.57f+.13f*sinf(t*1.10f+i);u.p={0,0,0};matrices(u);
     for(int j=0;j<6;j++){
       int k=j/2,s=j%2?1:-1;float rest[]={.53f,.035f,-.70f};
       float delta=.15f*sinf(t*4.21f+(k+j%2)*pi);u.toes[j]=point(u.torso,{rest[k]+delta,-.47f+std::max(0.f,delta*.42f),s*(k==1?.65f:.51f)});
     }
     std::vector<size_t> idx;for(auto q:list)idx.push_back(q->live.size());
     worker(u,t+i*.21f);if(bound){if(feature)tipBond(u);else collar(u);}M shift=mul(loc({offset,-.086f,.04f}),size({.79f,.79f,.79f}));
     size_t j=0;for(auto q:list){for(size_t i0=idx[j];i0<q->live.size();i0++)q->live[i0].mat=mul(shift,q->live[i0].mat);j++;}
   }
   return;
  }
  if(m==5||m==6||m==7||m==12||m==16){
   if(m==7)mechanism(a,t);
   else worker(a,t,m!=12&&!(feature&&m==16));
   if(m==12){if(feature)tipBond(a);else collar(a);}
   if(m==5){ // fragment carried by slowly closing jaws, unmistakably neither a recoil nor literal bait
      V midpoint=(a.tips[0]+a.tips[1])*.5f;
      float grip=ramp(.58f,1.82f,t);V p=mix(V{1.57f,-.17f,.161f},midpoint,grip);
      grain.add(tr(mul(loc(p),ry(a.yaw-.74f+grip*.62f)),{-.084f,-.017f,0},{.163f,.064f,.176f}),rgb(0xa98c59),4);
   }
   return;
  }
  if((m==0||m==1||m==4||m==9||m==11||m==13)&&inView(a.p,vp,3.22f)){worker(a,t);}
  if((m==0||m==3||m==4||m==8||m==10||m==11||m==13)&&inView({.22f,-1.77f,0},vp,2.1f))antlion(t,(m==8||m==10)?.27f:1.f);
  if(m==2||m==9||m==10||m==13){ // movement for environment transitions, no still image holds
    Rng r{6690};
    for(int i=0;i<(detail>.63f?86:43);i++){
      float x=r.r(-3.8f,4.6f),z=r.r(-1.6f,2.3f),d=r.r(.08f,.79f),s=r.r(.008f,.026f),p=fmod(t*.41f+r.f(),1.f);
      x-=copysignf(p*d,x);z-=copysignf(p*d*.34f,z);
      float y=ground(x,z)+.0085f+powf(sinf(p*pi),2)*r.r(.009f,.052f);
      grain.add(tr({}, {x,y,z},{s*1.31f,s*.53f,s}),rgb(i%4?0xb89258:0xddc094),4);
    }
  }
  if(m==1||m==3||m==4||m==0||m==11){silt(t,m);if(detail<=.63f)grain.live.resize(grain.live.size()/2);}
  if(m==0||m==3||m==4){
     for(float q:{.38f,1.41f,2.56f,6.05f,8.24f,10.5f,12.3f}){
      int n=m==3?128:68;
      grains({.39f,ground(.39f,.06f)+.29f,.10f},t-q,n,81922+int(q*100),.93f,.0169f,.12f);
     }
     if(m!=3){
      static const Motion f=planted(impact);V src=(f.tips[0]+f.tips[1])*.5f;src.y+=.026f;
      grains(src,t-impact,163,981726,.94f,.018f,2.82f);
      if(m==4)grains({1.69f,ground(1.69f,2.75f)+.061f,2.75f},t-wallClock,96,51187,.57f,.014f,-1.44f);
      else grains({-5.08f,ground(-5.08f,-.51f)+.052f,-.51f},t-land,73,91672,.28f,.0175f,.61f);
     }
  }
 }
};
}
