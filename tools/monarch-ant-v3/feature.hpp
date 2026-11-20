#pragma once
#include "stage.hpp"
namespace feature {
using namespace opening;

inline V hinge(const Motion&a,int side){return point(a.h,{.518f,-.062f,.153f*side});}
// Eyelines, framing offsets, focal marks and set stations for the feature edit.
// The same illustration rig drives both the photograph and any tracked graphic.
inline Optic lens(int id,int mode,float t,float q,const Motion&a){
 if(id<=10)return opening::camera(id,t,q,a);
 Optic k;V p=a.p,tip=(a.tips[0]+a.tips[1])*.5f, head=point(a.h,{.25f,.006f,0});
 auto mark=[&](V eye,V aim,float fov,float aperture,float key=1.f){k.eye=eye;k.aim=aim;k.fov=fov;k.focusAt=aim;k.aperture=aperture;k.key=key;};
 switch(id){
 case 50: // Continue the pilot's overhead, then look over its near rim.
  mark({-.73f,10.88f-.70f*ease(q),2.f},{-.13f,-.34f,.04f},47,2.7f,1.021f);k.up={0,0,-1};k.fixed=false;break;
 case 51:
  mark({-6.35f+.65f*ease(q),1.93f-.32f*ease(q),2.65f},{-.48f,-.90f,.17f},44,4.8f,1.05f);k.fixed=false;break;
 case 52:
  mark({1.44f,-.89f,-1.75f},{.19f,-1.76f,.055f},33,8.f,.89f);break;
 case 53:
  mark({.67f,-1.03f,1.11f},{.24f,-1.77f,.06f},39,7.3f,1.11f);break;
 case 54:
  mark({1.09f,-.76f,.94f},{.355f,-1.51f,.068f},47,6.3f,1.09f);break;
 case 55:
  mark({2.65f,.43f,-2.06f},{1.89f,-.71f,.10f},45,4.4f,1.03f);break;
 case 56:
  mark({.05f,-.19f,3.65f},{1.52f,-.94f,.52f},42,4.3f,1.02f);break;
 case 57:
  mark({-2.23f,4.89f,-5.85f},{-.38f,-1.12f,.02f},47,3.1f,.97f);break;
 case 58:
  mark({4.48f,2.17f,-2.31f},{2.57f,-.36f,.11f},41,5.55f,1.07f);k.focusAt=head;break;
 case 59:
  mark({3.45f,.54f,-2.97f},{3.31f,-.30f,.17f},42,5.3f,1.14f);k.focusAt=tip;break;
 case 60:
  mark({.16f,1.03f,2.29f},{.32f,-.015f,.025f},37,5.9f,1.10f);k.studio=1;break;
 case 61: // Shared focus and position on either side of the exposed hinge match.
  mark({.28f,1.79f,1.87f},{.276f,-.025f,.027f},37,2.8f,1.16f);k.studio=1;break;
 case 62:
  mark({.47f,1.16f,2.10f},{.55f,-.026f,.088f},31,3.7f,1.19f);k.studio=1;break;
 case 63:
  mark({.32f,2.29f,-1.16f},{.32f,-.035f,.012f},36,3.2f,1.17f);k.studio=1;break;
 case 64:
  mark({.28f,1.47f,1.93f},{.285f,-.006f,.048f},37,3.4f,1.07f);k.studio=1;break;
 case 65:
  mark({.26f,1.42f,-2.13f},{.312f,-.028f,.078f},37,4.15f,.98f);k.studio=1;break;
 case 66:
  mark({.22f,2.67f,1.42f},{.30f,-.036f,.045f},36,3.45f,1.08f);k.studio=1;break;
 case 67:
  mark({.79f,1.88f,2.34f},{.21f,-.08f,.065f},36,3.8f,1.09f);k.studio=1;break;
 case 68:
  mark({3.10f,.91f,-3.14f},{2.81f,-.34f,.16f},38,3.8f,1.15f);k.focusAt=head;break;
 case 69:
  mark({3.37f,1.43f,-3.26f},{2.77f,.03f,.14f},36,3.6f,1.16f);
  {float move=ramp(3.505f,3.704f,t);k.aim.y+=.63f*move;k.eye.y+=.17f*move;k.aim.x-=.11f*move;k.fixed=move==0.f;}
  k.focusAt=mix(head,tip,.26f+.68f*ramp(3.18f,3.42f,t));break;
 case 70:
  mark({4.18f,.82f,1.31f},{3.44f,-.30f,.08f},43,8.1f,1.11f);break;
 case 71:{
  V g=mix(V{1.36f,.65f,.09f},a.p,.61f);mark(g+V{.33f,1.62f,-4.60f},g,38,4.3f,1.12f);k.fixed=false;break;}
 case 72:
  mark({.33f,5.59f,-9.29f},{-.58f,.30f,-.02f},43,4.0f,1.16f);break;
 case 73:{ // Same sightline as the prologue; the trajectory is not the same.
  k=opening::camera(6,t,q,a);
  float end=ramp(3.66f,3.95f,t);k.aim.y+=.49f*end;k.aim.z+=.21f*end;
  return k;}
 case 74:
  mark({-.02f,2.84f,7.32f},{1.43f,-.84f,1.20f},41,3.6f,.96f);k.focusAt=a.p;break;
 case 75:
  mark({-1.40f,9.85f,2.87f},{-.19f,-.56f,.01f},48,3.2f,.94f);k.up={0,0,-1};break;
 case 76:
  mark({-.05f,5.67f,7.57f},{-.10f,-.24f,.07f},40,2.7f,1.04f);k.studio=1;break;
 case 77:
  mark({.05f,4.37f,6.31f},{-.05f,-.29f,.052f},35,2.7f,1.08f);k.studio=1;break;
 case 78:
  mark({-6.41f,1.22f,-3.72f},{-5.04f,.48f,-.43f},37,5.9f,1.05f);k.focusAt=a.p;break;
 case 79:
  mark({2.77f,.77f,2.94f},{2.39f,-.31f,.19f},39,5.45f,1.105f);k.focusAt=tip;break;
 case 80:
  mark({-.73f,10.10f+.78f*ease(q),2.f},{-.13f,-.34f,.04f},47,2.7f,1.02f);k.up={0,0,-1};k.fixed=false;break;
 case 81:{ // Final contact and a little breathing room ahead of both tips.
  mark({3.11f,.93f,3.32f},{2.94f,-.29f,.14f},43,5.65f,1.14f);
  k.focusAt=mix(head,tip,.75f);break;}
 case 82:{ // A running body stays inside frame: read legs, not streaks of sand.
  mark(p+V{.39f,1.88f,3.66f},p+V{.12f,-.28f,.06f},42,4.7f,1.04f);
  k.fixed=false;k.focusAt=p;break;}
 case 83:{ // Raking the line of the joined tips, not the glenoid.
  mark({1.57f,1.64f,1.53f},{.94f,-.02f,.04f},35,6.2f,1.10f);k.studio=1;k.focusAt=tip;break;}
 default:{
   // Ancillary coverage: use the blocking from the V2 set; reframe/relight
   // on this native stage. No plate from the V2 video is sampled.
   const int v2=id-100;
   auto old=cinema::lens(v2,t,q,a,mode);
   if(old.fixed)old=cinema::lens(v2,0,0,a,mode);
   k.eye=old.eye+V{.132f*cosf(id*1.1f),.073f,.132f*sinf(id*1.1f)};
   k.aim=old.aim+V{.065f,.022f,0}; k.fov=old.lens*.974f;k.up=old.up;k.studio=old.stage?1.f:0.f;
   k.aperture=old.stop*4.3f;k.key=1.01f+.069f*cosf(id*.861f);k.fixed=old.fixed;
   k.focusAt=(mode==0||mode==1||mode==4||mode==9||mode==11||mode==13)?a.p:k.aim;
   break;}
 }
 if(!k.studio)k.eye.y=std::max(k.eye.y,ground(k.eye.x,k.eye.z)+.125f);
 return k;
}
inline Motion pose(int mode,int camera,float t){
 if(camera==56&&mode==1)return openingPose(mode,2,t);
 if(mode==12||(mode==16&&camera==67)){
  Motion a=openingPose(mode,camera,t);a.jaw=cinema::restrainedJawAngle;matrices(a);
  if(mode==12&&camera==67)for(int j=0;j<6;j++){
   float phase=tau*(t*.88f+.5f*((j/2+j%2)%2));
   a.toes[j]+=V{.17f*cosf(phase),.14f*fmaxf(0.f,sinf(phase)),0};
  }
  return a;
 }
 if(camera==73&&t<=impact)return openingPose(mode,6,t);
 return openingPose(mode,camera,t);
}
}
