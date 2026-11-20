#pragma once
#include "../monarch-ant/scene.hpp"
namespace cinema {
using namespace ant;
struct Lens { V eye,aim,up={0,1,0}; float lens=33,stop=1.0f,grade=0,focus=0; bool fixed=true,stage=false; };
// All shot motion is solved in scene space. Locked macro cameras also allow a
// depth-retaining set plate to be cached; animals and moving sand are not cached.
inline Lens lens(int id,float t,float q,const Motion&a,int mode){
 Lens l;V p=a.p;
 float n=sinf(t*.44f)*.13f;
 switch(id){
 case 0: l.aim={1.72f,-1.19f,.43f};l.eye={.37f,-.45f,2.30f};l.lens=33;l.stop=1.7f;break; // skating tarsi
 case 1: l.aim={-.45f,-.78f,.08f};l.eye={.08f,3.67f,8.68f};l.lens=42;l.stop=.73f;break; // landscape depth
 case 2: l.aim={1.44f,-.42f,.23f};l.eye={.25f,.80f,4.99f};l.lens=39;l.stop=1.3f;break; // approaches from one side, no tracking zoom
 case 3: { // hero: hold the contact frame long enough to see it, let the ant move out of frame
  l.aim={1.86f,.56f,.24f};l.eye=l.aim+V{.16f+n,1.22f,4.84f};l.lens=39;l.stop=1.3f;
  break;
 }
 case 4: l.aim={-.41f,.10f,-.01f};l.eye={-1.12f,5.02f,9.72f};l.lens=42;l.stop=.8f;break; // single opener clearance
 case 5: l.aim={.27f,-1.89f,-.01f};l.eye={1.16f,-.50f,1.91f};l.lens=30;l.stop=1.65f;l.grade=.15f;break; // larva in warm reflection
 case 6: l.aim={-.20f,-.65f,-.18f};l.eye={-.45f,10.1f,2.37f};l.up={0,0,-1};l.lens=47;l.stop=.45f;break; // diagonal plan view
 case 7: l.aim={-.76f,-.61f,.10f};l.eye={-6.85f,2.00f,3.14f};l.lens=40;l.grade=.30f;l.stop=1.28f;break;
 case 8: l.aim={.41f,-1.87f,-.13f};l.eye={1.72f,-.55f,-1.61f};l.lens=32;l.stop=1.9f;l.grade=.15f;break; // opposite antlion
 case 9: l.aim={1.96f,-.88f,-.20f};l.eye={1.04f,.38f,-2.77f};l.lens=36;l.stop=1.37f;break; // loose sand sheet
 case 10:l.aim={.57f,-.045f,.06f};l.eye={1.76f+n,1.15f,1.90f};l.lens=37;l.stop=1.0f;l.stage=true;break; // jaw manipulation
 case 11:l.aim={.70f,.028f,.04f};l.eye={1.19f,3.26f,1.67f};l.lens=35;l.stop=.65f;l.stage=true;break;
 case 12:l.aim={.53f,-.02f,.07f};l.eye={1.26f,2.0f,2.43f};l.lens=33;l.stage=true;l.stop=.70f;l.grade=.35f;break; // anatomy envelope
 case 13:l.aim={.62f,.04f,.03f};l.eye={.10f,2.84f,-1.37f};l.lens=35;l.stage=true;l.stop=.8f;l.grade=.4f;break;
 case 14:l.aim={.61f,-.042f,.10f};l.eye={1.47f,1.27f,-2.07f};l.lens=37;l.stage=true;l.stop=.8f;l.grade=.2f;break; // unsupported snap
 case 15:l.aim={2.91f,-.24f,.25f};l.eye={3.77f,1.86f,-2.86f};l.lens=36;l.stop=1.25f;l.grade=.34f;break; // open jaws + raised foreleg from rear side
 case 16:{ // proof reprise (opposite optical axis, not the opening plate)
  l.fixed=false;float fs=ramp(3.43f,3.89f,t);
  l.aim=mix(V{3.46f,-.02f,.21f},p+V{.47f,-.045f,.09f},fs*.94f);
  l.eye=l.aim+V{.72f+.24f*fs,1.20f+.42f*fs,-3.19f-1.02f*fs};l.lens=36;l.stop=1.7f;l.grade=.27f;break;
 }
 case 17:l.aim={-.21f,1.18f,.02f};l.eye={.94f,4.95f,-9.37f};l.lens=43;l.grade=.39f;l.stop=.65f;break; // different side of rim
 case 18:l.aim={1.27f,.03f,1.0f};l.eye={-.24f,2.06f,6.54f};l.lens=38;l.grade=.32f;l.stop=1.07f;break; // failed wall path
 case 19:l.aim={1.52f,-.50f,1.25f};l.eye={.21f,4.95f,-4.79f};l.lens=39;l.grade=.46f;l.stop=.72f;break;
 case 20:l.aim={0,-.20f,-.08f};l.eye={.13f,5.95f,7.09f};l.lens=41;l.stage=true;l.stop=.5f;l.grade=.46f;break; // controlled groups
 case 21:l.aim={.36f,-.17f,.04f};l.eye={1.73f,3.62f,5.45f};l.lens=34;l.stage=true;l.stop=.98f;l.grade=.53f;break; // paired, tighter
 case 22:l.aim={-4.96f,.41f,-.34f};l.eye={-5.09f,1.15f,4.20f};l.lens=34;l.grade=.22f;l.stop=1.8f;break; // on open sand, real feet
 case 23:l.aim={2.04f,-.069f,.22f};l.eye={.51f,3.30f,3.52f};l.lens=42;l.stop=.91f;break;
 case 24:l.aim={.13f,-1.98f,-.09f};l.eye={-.76f,-.76f,-1.52f};l.lens=36;l.grade=.30f;l.stop=1.55f;break;
 case 25:{ l.fixed=false;l.aim={-.25f,-.21f,.18f};l.eye={3.33f-.81f*q,3.40f-.31f*q,7.03f+.35f*q};l.lens=49;l.grade=.21f;l.stop=1.18f;break;} // final drift towards bowl, no static hold
 case 26:l.aim={3.68f,.05f,.32f};l.eye={3.35f,.61f,1.58f};l.lens=42;l.grade=.11f;l.stop=1.64f;break; // strike insert at grain scale
 case 27:l.aim={.65f,-.037f,0};l.eye={.12f,1.30f,2.17f};l.lens=35;l.stage=true;l.grade=.5f;l.stop=.85f;break;
 case 28:l.aim={1.85f,-.48f,.62f};l.eye={3.67f,1.85f,3.36f};l.lens=40;l.grade=.2f;l.stop=1.06f;break;
 case 29:l.aim={3.22f,-.26f,.16f};l.eye={2.30f,1.17f,3.10f};l.lens=42;l.grade=.12f;l.stop=1.24f;break;
 case 30:l.aim={-.45f,.02f,.25f};l.eye={-5.51f,7.46f,3.41f};l.lens=49;l.grade=.3f;l.stop=.74f;break; // watch fall or ordinary run
 case 31:l.aim={-1.89f,.02f,.1f};l.eye={-4.44f,3.81f,6.16f};l.lens=46;l.grade=.34f;l.stop=1.01f;break; // air over rim in coda
 case 32:l.aim={.22f,-1.70f,-.07f};l.eye={2.12f,.19f,.9f};l.lens=34;l.grade=.16f;l.stop=1.47f;break;
 case 33:l.aim={4.13f,.45f,.37f};l.eye={5.51f,1.46f,4.01f};l.lens=37;l.grade=.27f;l.stop=1.24f;break;
 case 34:l.aim={-.26f,-.12f,.15f};l.eye={-.44f,1.12f,6.24f};l.lens=33;l.stage=true;l.stop=.55f;l.grade=.46f;break;
 case 35:l.aim={-1.6f,-.55f,.17f};l.eye={-5.27f,2.63f,-6.07f};l.lens=44;l.grade=.50f;l.stop=.8f;break;
 case 36:l.aim={2.85f,-.25f,.19f};l.eye={3.54f,2.01f,.46f};l.up={.13f,0,-1};l.lens=44;l.stop=.95f;l.grade=.30f;break; // jaw/contact and legs from near top
 case 37:l.aim={2.91f,-.24f,.23f};l.eye={2.64f,1.08f,-3.57f};l.lens=37;l.stop=1.24f;l.grade=.38f;break;
 case 38:l.aim={-5.23f,.32f,-.23f};l.eye={-6.89f,1.78f,-3.52f};l.lens=38;l.stop=1.28f;l.grade=.38f;break;
 case 39:l.aim={3.61f,-.018f,.27f};l.eye={4.73f,1.52f,2.09f};l.lens=38;l.stop=1.33f;l.grade=.39f;break;
 case 40:l.aim={4.78f,.36f,.39f};l.eye={4.32f,1.55f,-3.57f};l.lens=36;l.stop=1.29f;l.grade=.41f;break;
 default:l.eye={2.0f,4.0f,8.0f};l.aim=p;
 }
 if(mode==7){
  // The three key detail angles show different parts of the mechanism.
  switch(id){
  case 11:l.aim={.50f,-.007f,.022f};l.eye={.83f,1.86f,-.43f};l.lens=35;break;
  case 12:l.aim={.56f,-.010f,.028f};l.eye={1.05f+.23f*sinf(t*1.1f),1.44f,1.73f};l.lens=37;break;
  case 13:l.aim={.56f,-.017f,.042f};l.eye={.34f,2.36f,-.66f+.11f*sinf(t)};l.lens=34;break;
  case 27:l.aim={.47f,-.010f,.055f};l.eye={.42f,.92f,1.70f};l.lens=35;break;
  }
  l.grade=.63f;l.stop=.52f;
 }
 if(!l.stage)l.eye.y=std::max(l.eye.y,ground(l.eye.x,l.eye.z)+.17f);
 if(l.focus<=0)l.focus=len(l.eye-l.aim);
 return l;
}
}
