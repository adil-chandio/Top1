#pragma once
namespace opening {
const char* surfaceFragment=R"(#version 300 es
precision highp float;
in vec3 P,N;in vec2 U;in float D;flat in vec4 C;
out vec4 outColor;uniform sampler2D quartz,chitin;
uniform vec3 eye;uniform vec4 shot; // focus, warm key, studio, matte eligibility
uniform vec3 sun;
vec3 film(vec3 linear){
 vec3 p=max(linear-.0035,vec3(0.));
 p=p*(p*.93+.35)/(p*(p+1.08)+.268);
 return pow(clamp(p,0.,.992),vec3(.469));
}
void main(){
 vec3 v=normalize(eye-P),n=normalize(N),c=C.rgb;
 float m=C.a, d=abs(shot.x-D)/max(.27,shot.x);
 float key=max(dot(n,sun),0.),up=max(n.y,0.);
 vec3 soft=normalize(vec3(-.67,.48,.58)),rim=normalize(vec3(.49,.63,.56));
 float fill=max(dot(n,soft),0.),edge=max(dot(n,rim),0.),F=1.-max(dot(n,v),0.);
 vec3 keyColor=vec3(1.60,1.15,.746)*shot.y;
 vec3 fillColor=mix(vec3(.216,.292,.323),vec3(.25,.43,.47),shot.z);
 vec3 light=keyColor*(.10+.78*key)+fillColor*(.22+.55*fill+.26*up);
 vec3 p;
 if(m<.5){
  float r=length(P.xz);vec3 roundFloor=normalize(vec3(-.49*P.x/max(.15,r),1.,-.51*P.z/max(.15,r)));
  n=normalize(mix(n,roundFloor,.51*smoothstep(.03,.47,r)*(1.-smoothstep(3.89,4.51,r))));
  key=max(dot(n,sun),0.);light=keyColor*(.10+.78*key)+fillColor*(.22+.55*fill+.26*up);
  vec2 st=P.xz*.378;vec3 tex=texture(quartz,st,d*.38).rgb;
  float softshade=.52+.48*smoothstep(-1.,1.,sin(P.x*1.18-P.z*.94)+.5*sin(P.x*.62+P.z*1.59));
  float soilShade=mix(.61,1.05,smoothstep(.28,4.63,length(P.xz)));
  vec3 a=pow(tex,vec3(2.12))*vec3(1.043,.996,.931);
  if(d<.46 && D<4.3){
   vec2 f=vec2(texture(quartz,st+vec2(.00103,0.)).r-tex.r,texture(quartz,st+vec2(0.,.00103)).r-tex.r);
   vec3 b=normalize(n+vec3(-1.1*f.x,0.,-1.1*f.y));
   float add=max(0.,dot(b,sun));key=mix(key,add,.71);light=keyColor*(.10+.78*key)+fillColor*(.22+.55*fill+.26*up);
  }
  float k=pow(max(dot(n,normalize(sun+v)),0.),24.);
  p=a*(light*soilShade*softshade)+k*keyColor*.025;
 }else if(m<2.5){
  vec2 z=U*vec2(3.2,2.4);vec3 micrograin=texture(chitin,z,min(d,.92)).rgb;
  float h=micrograin.g;float coarse=smoothstep(.11,.29,h);
  if(m<1.5 && D<5.25 && d<.75){
   vec2 a=vec2(texture(chitin,z+vec2(.0021,0.)).g-h,texture(chitin,z+vec2(0.,.0021)).g-h);
   vec3 axis=normalize(dFdx(P));n=normalize(n+(.71*a.x+.014*sin(U.x*134.))*axis+.68*a.y*normalize(cross(n,axis)));
   key=max(dot(n,sun),0.); fill=max(dot(n,soft),0.);edge=max(dot(n,rim),0.);
  }
  float x=max(0.,dot(n,normalize(sun+v))),y=max(0.,dot(n,normalize(soft+v))),z1=max(0.,dot(n,normalize(rim+v)));
  float width=mix(72.,30.,coarse),catchLight=pow(x,width)*key*.84;
  vec3 lam=c*(.66+.48*coarse)+micrograin*micrograin*.021;
  if(m>1.5){lam=vec3(.009,.015,.017);catchLight=pow(x,122.)*.99+pow(y,49.)*.14;}
  p=lam*(light+.054)+(catchLight*.36+pow(x,13.)*key*.064)*keyColor;
  p+=(F*F*edge*.112+pow(z1,28.)*.109+pow(y,29.)*fill*.037)*vec3(.423,.620,.665);
  p+=F*F*F*key*.121*vec3(.859,.43,.193);
 }else if(m<3.5){
  p=c*(light+.088)*(.83+.17*sin(U.x*43.+sin(U.y*24.)))+keyColor*.034*F*key;
 }else if(m<4.5){
  float a=pow(max(dot(n,normalize(sun+v)),0.),26.);
  p=c*light*(.82+.18*sin(U.y*71.+U.x*13.))+keyColor*a*.102;
 }else if(m>8.5){ // Dark frontmost pincer rendered as scene geometry, not overlaid text.
  float str=.88+.12*cos(U.x*9.+U.y*17.);
  p=c*(light*.69+.14)*str+F*F*keyColor*.036;
 }else p=c*(light+.053);
 // Alpha is an internal actor-matte channel. No burn-in of this pass.
 outColor=vec4(film(p),(m>.5 && shot.w>.5)?1.:0.);
}
)";
const char* plateFragment=R"(#version 300 es
precision mediump float;
in vec2 uv;out vec4 color;uniform sampler2D canopy;uniform vec4 shape;
void main(){
 vec2 q=(uv-vec2(.65,.55))*vec2(1.20,1.66);
 vec3 c=texture(canopy,vec2(.47,.52)+(uv-.5)*vec2(.81,.80)+shape.xy).rgb;
 float gray=dot(c,vec3(.2126,.7152,.0722));c=mix(c,vec3(gray),.26);
 c=c*.82*vec3(.86,.91,.858)+vec3(.011,.016,.013);
 vec3 stage=mix(vec3(.021,.033,.039),vec3(.092,.179,.177),exp(-dot(q,q)*4.2));
 color=vec4(mix(c,stage,shape.z),0.);
}
)";
const char* shadowVertex=R"(#version 300 es
layout(location=0) in vec3 p;
layout(location=3) in vec4 a;layout(location=4) in vec4 b;layout(location=5) in vec4 c;layout(location=6) in vec4 d;
uniform mat4 lightMatrix;
void main(){gl_Position=lightMatrix*(mat4(a,b,c,d)*vec4(p,1.));}
)";
const char* shadowFragment=R"(#version 300 es
precision mediump float;
void main(){}
)";
const char* finishFragment=R"(#version 300 es
precision highp float;
in vec2 uv;out vec4 color;
uniform sampler2D base,depth,lightmap;
uniform mat4 lightMatrix;
uniform vec3 eye,rayF,rayX,rayY;
uniform vec4 lens; // width, height, focal distance, blur scale
uniform vec4 state; // shadow, vignette, atmospheric contrast, frame index
float z(float n){return .828/(36.-n*35.977);}
vec4 grab(vec2 pt){return texture(base,pt);}
void main(){
  float depth0=texture(depth,uv).r;float D=z(depth0);
  vec4 c=grab(uv);
  if(depth0<.99996){
   float nearBlur=(D<.23 && c.a>.6)?14.:0.;
   float defocus=min(18.,abs(lens.z-D)*lens.w/max(lens.z,.23)+nearBlur);
   if(defocus>.73){
     vec2 step0=vec2(defocus)/lens.xy;
     vec4 avg=c*.21;
     avg+=grab(uv+step0*vec2(.91,.22))*.168;
     avg+=grab(uv+step0*vec2(.21,1.1))*.143;
     avg+=grab(uv+step0*vec2(-.52,.67))*.143;
     avg+=grab(uv+step0*vec2(-.94,-.32))*.139;
     avg+=grab(uv+step0*vec2(.45,-.87))*.131;
     avg+=grab(uv+step0*vec2(-.35,-.94))*.066;
     c=mix(c,avg,smoothstep(.60,2.4,defocus));
   }
   if(state.x>.5){
     vec2 ndc=uv*2.-1.;vec3 P=eye+D*(rayF+rayX*ndc.x+rayY*ndc.y);
     vec3 p=(lightMatrix*vec4(P,1.)).xyz*.5+.5;
     if(all(greaterThan(p.xy,vec2(.012)))&&all(lessThan(p.xy,vec2(.988)))){
       float s=0.;float bias=.00215;
       s+=step(texture(lightmap,p.xy+vec2(.0021,-.0019)).r+bias,p.z);
       s+=step(texture(lightmap,p.xy+vec2(-.0022,-.0016)).r+bias,p.z);
       s+=step(texture(lightmap,p.xy+vec2(-.0017,.0023)).r+bias,p.z);
       s+=step(texture(lightmap,p.xy+vec2(.0017,.0022)).r+bias,p.z);
       c.rgb*=1.0-s*.25*mix(.42,.27,c.a);
     }
   }
   float a=smoothstep(3.5,16.5,D)*state.z;
   c.rgb=mix(c.rgb,vec3(.240,.262,.230),a*.21);
  }
  vec2 v=(uv-vec2(.51,.53))*vec2(1.22,1.00);
  float fall=1.-state.y*smoothstep(.23,.77,length(v));
  // Low-amplitude print texture; not a substitute for evaluated object motion.
  float dust=fract(sin(dot(gl_FragCoord.xy+state.w,vec2(12.9898,78.233)))*43758.5453)-.5;
  c.rgb=max(vec3(.006),c.rgb*fall+dust*.009);
  color=c;
}
)";
}
