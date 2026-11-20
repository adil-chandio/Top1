#pragma once
#include "../monarch-ant-v2/world.hpp"
namespace opening {
using namespace ant;
using cinema::World;
constexpr float hNear=.023f,hFar=36.f;
inline constexpr V warmKey={-.46f,.77f,-.44f};
const V stoneAt={1.40f,ground(1.40f,.621f)+.031f,.621f};
struct Optic{
 V eye,aim,up={0,1,0},focusAt;
 float fov=36,aperture=5.0f,key=1,studio=0;
 bool fixed=true;
};
inline V rollingGrain(float u){
 float f=.12f*u+.88f*u*u;
 float x=1.362f-.808f*f,z=.823f-.51f*f+.032f*sinf(u*12.7f);
 float y=ground(x,z)+.033f+.042f*powf(std::max(0.f,sinf(u*18.f)),2);
 return {x,y,z};
}
inline Motion openingPose(int mode,int id,float t){
 Motion a=cinema::pose(mode,t);
 if(id==2){
  // The same gait continues while the ground fails. Translate each unlocked
  // stance with the slide, then re-evaluate tarsal constraints on the slope.
  float x=1.557f+.135f*ramp(.625f,1.055f,t)-.606f*ramp(.983f,1.888f,t);
  x+=.012f*sinf(t*25.f)*pulse(.87f,1.36f,1.89f,t);
  float dx=x-a.p.x;float before=ground(a.p.x,a.p.z);a.p.x=x;
  a.p.y+=ground(a.p.x,a.p.z)-before;
  for(auto& toe:a.toes){float old=ground(toe.x,toe.z);toe.x+=dx;toe.y+=ground(toe.x,toe.z)-old;}
  matrices(a);if(a.clear<.075f)solveContact(a,.075f);
 }
 if(id==5||id==6){
  // A small anticipatory head lift rolls across the axis change. The hero
  // shot holds the planted legs as both tips are aimed down onto the sand.
  if(t<impact){float headRoom=.225f*ramp(2.24f,2.674f,t)*(1-ramp(2.844f,3.42f,t));
   if(headRoom>.00002f)solveContact(a,a.clear+headRoom);
  }
 }
 return a;
}
inline Optic camera(int id,float t,float q,const Motion&a){
 Optic k;V p=a.p,tip=(a.tips[0]+a.tips[1])*.5f;float y0=ground(1.72f,.51f);
 switch(id){
 case 0: // Turn the tarsus into a foreground reveal, not a whole ant silhouette.
  k.eye={1.45f,y0+.292f,2.374f}; k.aim={1.510f,y0+.041f,.555f}; k.fov=40;k.aperture=7.4f;
  k.focusAt={1.49f,y0+.026f,.742f}; break;
 case 1:
  k.eye={.67f,ground(.67f,1.38f)+.25f,1.38f};k.aim={1.57f,ground(1.57f,.56f)+.028f,.56f};k.fov=38;k.key=.91f;k.aperture=7.1f;
  k.focusAt=k.aim;break;
 case 2:
  k.eye={.60f,-.035f,2.968f};k.aim={1.40f,-.97f,.46f};k.fov=40;k.key=1.f;k.aperture=5.7f;k.focusAt=stoneAt;break;
 case 3:{ // An unbroken descending optical move with the witness grain.
  V g=rollingGrain(q);k.fixed=false;k.eye=g+V{.304f,.195f,.344f};
  k.aim=g+V{-.075f,-.014f,-.06f};k.fov=45;k.key=.81f;k.aperture=12.7f;k.focusAt=g;break;
 }
 case 4:
  k.eye={1.226f,-1.18f,1.54f};k.aim={.285f,-1.766f,.014f};k.fov=35;k.key=.85f;k.aperture=5.75f;
  k.focusAt={.375f,-1.766f,.05f};break;
 case 5:
  k.eye={3.30f,.54f,-2.36f};k.aim={2.795f,-.20f,.24f};k.fov=38;k.key=1.f;k.aperture=4.9f;
  k.focusAt=point(a.h,{.26f,.016f,.012f});break;
 case 6:{ // Keep floor, working tips, tarsi and the first movement in one exposure.
  float lift=ramp(3.57f,3.962f,t);
  k.eye={2.08f,.98f+.13f*lift,4.85f+.19f*lift};
  k.aim={2.059f-.32f*lift,.18f+.68f*lift,.236f}; k.fov=40;k.key=1.13f;k.aperture=4.7f;
  k.fixed=lift==0;
  // This is an optical focus mark, not a change to the fixed camera or frame speed.
  V body=point(a.h,{.24f,.016f,.011f});
  k.focusAt=mix(body,tip,ramp(2.77f,3.385f,t)*(1-ramp(3.445f,3.70f,t))*.92f);
  break;}
 case 7:
  k.eye={-1.11f,5.49f,9.42f}; k.aim={-.53f,.17f,.008f};k.fov=41;k.key=1.12f;k.aperture=4.0f;
  k.focusAt={-2.40f,.24f,.10f};break;
 case 8:
  k.eye={.377f,1.58f,2.62f};k.aim={.312f,.038f,.046f};k.fov=36;k.studio=1;k.aperture=4.2f;
  k.focusAt=point(a.h,{.48f,-.05f,0});break;
 case 9:
  k.eye={-6.33f,1.037f,-3.48f};k.aim={-5.03f,.40f,-.43f};k.fov=36;k.key=.98f;k.aperture=5.9f;
  k.focusAt=p;break;
 case 10:
  k.fixed=false;k.eye={-.73f,9.50f+1.38f*ease(q),2.f};k.aim={-.13f,-.34f,.04f};k.up={0,0,-1};k.fov=47;k.key=1.02f;k.aperture=2.8f;
  k.focusAt=k.aim;break;
 }
 if(!k.studio)k.eye.y=std::max(k.eye.y,ground(k.eye.x,k.eye.z)+.125f);
 return k;
}
inline float focusDistance(const Optic&k){return std::max(.12f,dot(k.focusAt-k.eye,norm(k.aim-k.eye)));}

class Stage:public World{
public:
 Mesh rock=sweep(6,8,5);
 Stage(){
  rock.bind();list.push_back(&rock);
  // Dark reddish-brown cuticle with separate semitranslucent-looking warm joints.
  shell=rgb(0x513124); body=rgb(0x452c22); gaster=rgb(0x33261d);
  limb=rgb(0x714631); joint=rgb(0x402a22);mand=rgb(0x76472a);
 }
 void dressed(const Optic&k,const M&vp,int shot,bool lean=false){
  reset();if(k.studio)return;
  soil.add({},rgb(0xcfad79),0);quartz(vp);
  // A fixed reference above the sliding layer. Its silhouette is kept steady in
  // the locked traction shot, against which the ant slips.
  rock.add(mul(loc(stoneAt),mul(ry(.92f),mul(rz(.24f),size({.141f,.082f,.106f})))),rgb(0x5d5845),4);
  Rng r{83117};
  for(int i=0;i<(lean?690:1850);i++){
   float x=r.r(-5.3f,5.3f),z=r.r(-5.3f,5.3f),rr=hypotf(x,z),w=r.r(.007f,.029f);
   if(rr>6.7f||!inView({x,ground(x,z),z},vp,.12f))continue;
   if(i%17==0)w*=2.24f;
   if(shot>=7&&i%3&&!lean)continue;
   V c=rgb(i%17==0?0x85755a:((i%7==0)?0xe8cf9e:((i%5==0)?0x99764f:0xcaa771)));
   float h=ground(x,z);grain.add(mul(loc({x,h+w*.094f,z}),mul(ry(r.r(0,tau)),size({w*1.27f,w*.58f,w}))),c,4);
  }
  for(int i=0;i<46;i++){
   float angle=r.r(0,tau),d=r.r(4.75f,11.2f),x=d*cosf(angle),z=d*sinf(angle),t=r.r(.11f,.53f),o=r.r(-.75f,.65f);
   if(!inView({x,ground(x,z)+.17f,z},vp,.8f))continue;
   V p={x,ground(x,z)+.018f,z};
   for(int j=1;j<6;j++){
    float a=j*.2f;V q={x+t*a*cosf(o),ground(x+t*a*cosf(o),z+t*a*sinf(o))+.019f+.058f*sinf(pi*a*.87f),z+t*a*sinf(o)};
    bar(p,q,.020f*(1-a*.72f),rgb(i%6?0x4d4836:0x5a6448),3,true);p=q;
   }
  }
 }
 void slipping(float t,int n,float weight,const M&vp){
  Rng r{882995};
  for(int i=0;i<n;i++){
   float x=r.r(.42f,3.5f),z=r.r(-.72f,1.77f),df=r.r(.24f,1.16f),seed=r.f();
   float k=fmod(t*(.37f+.22f*df)+seed,1.f),p=k*k;
   x-=p*df*weight;z-=p*z*.20f*df*weight;
   float wave=powf(std::abs(sinf(k*(pi*(2+(i%5))))),3)*.023f;
   float s=r.r(.0085f,.025f)*(1.02f-.31f*p);float y=ground(x,z)+.008f+wave;
   if(inView({x,y,z},vp,.14f))grain.add(mul(loc({x,y,z}),mul(rz(k*2.3f+seed*9),size({s*1.32f,s*.59f,s}))),rgb(i%9==0?0xe9d5a2:0xc3a16d),4);
  }
 }
 void actionSet(int m,int shot,float t,float q,const Motion&a,const M&vp,bool longForm=false){
  if(m<=16){
    actors(m,t,a,vp,longForm);
    if(shot==0||shot==2)slipping(t*.91f+.7f,172,1.07f,vp);
    return;
  }
  reset();shadowCasts.clear();
  if(m==23){slipping(t*.35f+.38f,32,.66f,vp);return;}
  if(m==21){slipping(t*1.51f+.16f,420,1.21f,vp);return;}
  if(m==22){
   V g=rollingGrain(q);slipping(q*1.06f+.36f,180,1.08f,vp);
   rock.add(mul(loc(g),mul(ry(q*-4.89f),mul(rz(q*-8.7f),size({.053f,.041f,.029f})))),rgb(0xb69564),4);
  }
 }
 // Cut under an out-of-focus, camera-near 3D jaw surface. Only the 14-frame
 // optical insert crosses the lens; the set changes once under that occlusion.
 bool crossPincer(const Optic&k,int f){
  if(f<227||f>240)return false;
  reset();V dir=norm(k.aim-k.eye),right=norm(cross(dir,k.up)),up=cross(right,dir);
  float t=(f-233.5f)/6.5f, mid=1.f-ramp(.14f,.64f,fabsf(t)),d=.096f+.061f*t*t-.019f*mid;
  V X=up*.88f+right*.19f-dir*.055f,Y=right*(2.24f+.35f*mid)-up*.235f,Z=dir*.43f;
  const float u=.423f;V g={.630f*u,.375f*u+.097f*u*u,.270f*sinf(u*pi*.80f)-.177f*u*u};
  V center=k.eye+dir*d+right*(.392f*t)+up*(.037f*t);
  V root=center-X*g.x-Y*g.y-Z*g.z;
  hook.add(basis(X,Y,Z,root),rgb(0x2d1b12),9);
  return true;
 }
};
}
