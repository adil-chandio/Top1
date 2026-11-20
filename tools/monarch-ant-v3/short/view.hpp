#pragma once
#include "../feature.hpp"
#include <string_view>

// Isolated portrait lenses for the promo. All poses, contact marks, particles,
// species shapes and lab conditions still come from the V3 feature rig.
namespace portrait {
using namespace opening;
inline bool close(std::string_view s){
 return s=="v2_cold"||s=="v2_loop"||s=="v2_tarsi"||s=="v2_predator"||s=="v2_air"||s=="v2_contact"||
        s=="strike_open"||s=="before_the_bite"||s=="antlion_flick"||s=="slide"||s=="slipping_grain"||
        s=="aimed_jaws"||s=="air_snap"||s=="sand_snap"||s=="held_shut";
}
inline Optic view(std::string_view s,Optic k,float t,float q,const Motion&a){
 const V tip=(a.tips[0]+a.tips[1])*.5f, head=point(a.h,{.255f,.009f,.034f}),p=a.p;
 const V grounded={2.615f,ground(2.615f,.229f)+.584f,.229f};
 auto place=[&](V target,V offset,V focus,float fov,float stop,float key,bool fixed){
  k.aim=target;k.eye=target+offset;k.focusAt=focus;k.fov=fov;k.aperture=stop;k.key=key;k.fixed=fixed;
 };
 float roll=0.f;
 if(s=="v2_cold"||s=="v2_loop"){
  // The hook reads as a whole-body launch, rather than a crop of the tips.
  const float lift=ramp(3.42f,3.73f,t);
  V c=V{2.904f,-.224f,.223f}+(p-grounded)*(.85f*lift);
  c.y+=.165f*lift;
  place(c,{.71f,1.44f,3.87f},mix(head,tip,.48f-.26f*lift),60.5f,4.2f,1.28f,lift==0);
  roll=.531f;
 }else if(s=="v2_tarsi"){
  V toe=mix(a.toes[1],a.toes[3],.62f);
  place({1.487f,-1.074f,.621f},{.37f,.69f,1.93f},toe,47.f,5.0f,1.12f,true);
  roll=.29f;
 }else if(s=="v2_predator"){
  place({.477f,-1.61f,.072f},{.75f,1.01f,1.12f},{.42f,-1.70f,.048f},53.f,6.75f,1.15f,true);
  roll=.433f;
 }else if(s=="v2_air"){
  const float push=ease(q);
  place({.931f,.184f,.038f},{.62f,1.48f-.105f*push,-3.17f+.16f*push},mix(head,tip,.52f),47.f,4.3f,1.20f,false);
  roll=.331f;
 }else if(s=="v2_contact"){
  const float move=ramp(3.427f,3.754f,t), rais=ramp(3.427f,3.56f,t);
  V c=V{3.303f,-.108f,.209f}+(p-grounded)*(.91f*move);
  c.y+=.112f*rais;
  place(c,{1.015f,1.29f,-4.33f},mix(head,tip,.60f-.47f*move),53.5f,4.8f,1.25f,rais==0);
  roll=.33f;
 }else if(s=="v2_rise"){
  V c=mix(V{.77f,1.15f,.04f},p,.70f)+(tip-p)*.14f;
  c.y-=.13f;
  place(c,{-.49f,1.19f,-4.79f},p,51.f,4.5f,1.24f,false);
  roll=-.29f;
 }else if(s=="v2_apex"){
  V c=mix(V{-.86f,.45f,.02f},p,.46f);c.y-=.28f;
  place(c,{1.51f,6.40f,-6.65f},p,54.f,3.2f,1.17f,false);
  roll=.34f;
 }else if(s=="v2_lab"){
  const float u=ease(q);
  place({.028f,-.18f,.025f},{.18f-.55f*u,7.45f-.38f*u,3.2f+.30f*u},
        {.04f,-.09f,.035f},44.f,3.1f,1.15f,false);
  roll=1.22f+.11f*u;
 }else if(s=="strike_open"||s=="before_the_bite"){
  // Identical optic through the loop seam. A little lag lets the ant break up
  // out of the sand fan instead of pinning it motionless in the viewfinder.
  const float rise=ramp(3.45f,3.77f,t);
  V c=V{3.461f,-.241f,.242f}+(p-grounded)*(.84f*rise);
  c.y+=.14f*rise;
  place(c,{.88f,1.039f,3.39f},mix(head,tip,.60f-.27f*rise),51.f,4.8f,1.24f,rise==0.f);
  roll=.284f;
 }else if(s=="slide"){
  // Fixed perspective: the stone stays put while the feet shear back downhill.
  place({1.582f,-.740f,.325f},{.88f,1.55f,3.91f},mix(p,a.toes[3],.42f),54.f,4.4f,1.10f,true);
  roll=.401f;
 }else if(s=="slipping_grain"){
  k.fov=51.f;k.key=.98f;roll=-.14f;
 }else if(s=="funnel"||s=="same_pit"){
  const bool ending=s=="same_pit";
  const float move=ease(q);
  place({.05f,-.73f,.12f},{-2.39f+.48f*move,15.05f+(ending?1.39f:-1.04f)*move,7.27f-.83f*move},
        {.22f,-1.39f,.09f},61.f,2.6f,1.05f,false);
  k.up={0,0,-1};roll=ending?.18f:.05f;
 }else if(s=="antlion_flick"){
  place({.538f,-1.598f,.055f},{.966f,1.16f,1.18f},{.477f,-1.712f,.04f},49.f,6.0f,1.13f,true);
  roll=.19f;
 }else if(s=="aimed_jaws"){
  place({3.139f,-.025f,.172f},{.65f,1.32f,-2.89f},head,46.f,4.3f,1.09f,true);
  roll=.21f;
 }else if(s=="air_snap"){
  place({.883f,.188f,.027f},{.64f,1.11f,-3.34f},mix(head,tip,.49f),47.f,4.7f,1.16f,true);
  roll=.225f;
 }else if(s=="sand_snap"||s=="second_launch"){
  // Same sidedness and roll as the AIR plate. No tiles or cut hide the actual
  // contact. Whole head and part of planted stance remain readable in portrait.
  const float rise=ramp(3.464f,3.84f,t), lag=ramp(3.42f,3.59f,t);
  V c=V{3.368f,-.139f,.232f}+(p-grounded)*(.96f*rise);
  c.y+=.127f*lag;
  place(c,{.85f,1.23f,-4.11f},mix(head,tip,.54f-.36f*rise),54.f,4.7f,1.19f,lag==0.f);
  roll=.225f;
 }else if(s=="over_the_rim"){
  // Track gently across the lip; slightly behind the body at takeoff, ahead
  // of it at touchdown. The position change stays visible against the rim.
  V c=mix(V{-.88f,.75f,.018f},p,.75f)+(tip-p)*.23f;
  c.x-=.23f;c.y-=.67f;
  place(c,{-3.12f,5.14f,-6.26f},p,56.f,3.3f,1.13f,false);
  roll=-.23f;
 }else if(s=="short_of_rim"){
  // On the failure keep the landing zone and moving body in the same shot.
  V c=mix(V{1.52f,-.33f,1.75f},p,.22f);
  place(c,{.685f,3.03f,4.92f},p,51.f,4.6f,1.02f,false);
  roll=.163f;
 }else if(s=="lab_pair"){
  // Rotate the pair down the tall canvas instead of cropping away a cohort.
  place({.026f,-.21f,.034f},{.05f,7.44f,3.20f},{.04f,-.10f,.04f},43.f,3.2f,1.10f,true);
  roll=1.21f;
 }else if(s=="held_shut"){
  const float push=ease(q);
  place(mix(head,tip,.64f)+V{0,.143f,0},{1.42f-.26f*push,1.54f-.21f*push,-1.96f+.33f*push},tip,46.f,6.2f,1.22f,false);
  roll=.426f;
 }
 if(!k.studio)k.eye.y=std::max(k.eye.y,ground(k.eye.x,k.eye.z)+.125f);
 if(roll!=0.f){V dir=norm(k.aim-k.eye),right=norm(cross(dir,k.up));k.up=cross(right,dir)*cosf(roll)+right*sinf(roll);}
 return k;
}
}
