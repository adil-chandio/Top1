#pragma once
namespace cinema {
const char* meshV=R"(#version 300 es
precision highp float;
layout(location=0) in vec3 a;layout(location=1) in vec3 n;layout(location=2) in vec2 uv;
layout(location=3) in vec4 m0;layout(location=4) in vec4 m1;layout(location=5) in vec4 m2;layout(location=6) in vec4 m3;layout(location=7) in vec4 color;
uniform mat4 uVP;uniform mat4 uView;
out vec3 P,N;out vec2 U;out float D;flat out vec4 C;
void main(){vec4 p=mat4(m0,m1,m2,m3)*vec4(a,1.); P=p.xyz;U=uv;
 N=normalize(n.x*m0.xyz/max(1e-7,dot(m0.xyz,m0.xyz))+n.y*m1.xyz/max(1e-7,dot(m1.xyz,m1.xyz))+n.z*m2.xyz/max(1e-7,dot(m2.xyz,m2.xyz)));
 C=color;D=-(uView*p).z;gl_Position=uVP*p;}
)";
const char* meshF=R"(#version 300 es
precision mediump float;
in highp vec3 P;in highp vec3 N;in vec2 U;in highp float D;flat in vec4 C;
out vec4 o;
uniform sampler2D sand,cuticle;
uniform highp vec3 uEye;
uniform vec4 optics; // focus, defocus, scene palette, studio flag
vec3 tonemap(vec3 x){x=max(x-.009,0.);return sqrt(clamp(x*x+.46*x,0.,1.)/max(x*x+1.07*x+.38,.001));}
void main(){
 vec3 n=normalize(N),v=normalize(uEye-P),c=C.rgb;
 float mat=C.a, grade=optics.z;
 vec3 back=normalize(vec3(-.45,.67,-.78)),sky=normalize(vec3(-.39,.73,.47)),rim=normalize(vec3(.52,.48,.66));
 float f=clamp(abs(D-optics.x)*optics.y/max(optics.x,.64),0.,3.1);
 float front=max(0.,dot(n,sky)), key=max(0.,dot(n,back));float y=max(0.,n.y);
 vec3 keyC=mix(vec3(1.49,1.06,.68),vec3(1.04,1.02,.93),grade);
 vec3 fillC=mix(vec3(.28,.40,.51),vec3(.33,.48,.59),grade);
 vec3 light=keyC*(key*.81+.083)+fillC*(.33+.51*front+.13*y);
 vec3 p;
 if(mat<.5||mat>7.5){
  vec2 st=mat<.5 ? P.xz*.45 : vec2(P.x,P.z)*.29;
  vec3 a=texture(sand,st,f*2.55).rgb;
  // Far texture tends towards the measured mean, not an unsharp proxy image.
  float valley=smoothstep(.26,5.05,length(P.xz));
  float swirl=.91+.08*sin(P.x*1.81+P.z*.89)+.035*cos(P.z*4.13-P.x*2.17);
  vec3 tint=mix(vec3(1.08,1.00,.83),vec3(.84,1.02,1.06),grade);
  a=mix(a,vec3(.65,.59,.48),f*.17);
  p=a*a*tint*light*(.63+valley*.41)*swirl;
  if(mat>7.5)p*=vec3(.76,.85,.84);
  p+=vec3(.061,.046,.029)*pow(max(0.,dot(n,normalize(back+v))),12.);
 } else if(mat<2.5){
  vec2 q=U*vec2(2.8,1.9);vec3 a=texture(cuticle,q,min(f,.9)).rgb;
  float r=a.g;float pitted=smoothstep(.105,.32,r);float az=sin(U.x*144.+sin(U.y*53.)*3.2);
  if(mat<1.5 && f<.62){
   vec2 g=vec2(texture(cuticle,q+vec2(.002,0.)).g-r,texture(cuticle,q+vec2(0.,.002)).g-r);
   highp vec3 T=normalize(dFdx(P)),B=normalize(cross(n,T));n=normalize(n+(.72*g.x+.021*az)*T+g.y*.72*B);
   key=max(0.,dot(n,back));front=max(0.,dot(n,sky));
  }
  // Micrograin changes both albedo and the reflected highlight. Keep the cuticle
  // dark without a flat black fill and keep broad glints away from the tips.
  float rough=mix(.17,.36,pitted),F=1.-max(0.,dot(n,v));
  float h=max(0.,dot(n,normalize(back+v))), s=max(0.,dot(n,normalize(sky+v)));
  float lob=pow(h,mix(84.,34.,rough))*key;float area=pow(s,23.)*front;
  if(mat>1.5&&mat<2.5){lob=pow(h,93.)*1.28;area=pow(s,62.)*1.03;c=vec3(.014,.021,.022);}
  vec3 rich=c*(.59+.59*pitted+.038*az)+a*a*.039;
  p=rich*(light*1.04+vec3(.038,.053,.073))+(lob*.43+area*.096)*mix(keyC,fillC,.27);
  p+=(keyC*.14*key+fillC*.10*max(dot(n,rim),0.))*F*F;
 }else if(mat<3.5){
  p=c*(light+vec3(.11,.065,.035))*(.83+.17*cos(U.x*17.))+keyC*(key*key*.028)*(.27+.73*y);
 }else if(mat<4.5){
  float tw=pow(max(0.,dot(n,normalize(back+v))),31.);
  p=c*light*(.83+.12*sin(U.y*43.+P.x*211.))+keyC*tw*.17;
 }else{
  float x=max(0.,dot(n,normalize(sky+v)));p=c*(.4+key*.80+front*.43)*vec3(.91,1.01,1.09)+pow(x,23.)*vec3(.08,.096,.11);
  if(mat>5.6){
   float r=smoothstep(.34,.82,.5+.5*sin(U.x*109.+.28*sin(U.y*24.)));
   p=p*(.80+.25*r)+c*(mat>6.6?.38:.18);
  }
 }
 o=vec4(tonemap(p),1.);
}
)";
const char* fillV=R"(#version 300 es
out vec2 uv;
void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));uv=p;gl_Position=vec4(p*2.-1.,0.,1.);}
)";
const char* fillF=R"(#version 300 es
precision mediump float;
in vec2 uv;out vec4 color;
uniform sampler2D forest;uniform vec4 look; // pan x/y, studio mode, grade
void main(){
 float v=pow(clamp(length((uv-.5)*vec2(.66,.87)),0.,1.),1.8);
 vec3 forestColor=texture(forest,vec2(.5)+(uv-.5)*.79+look.xy).rgb;
 forestColor=forestColor*vec3(.77,.82,.81);vec2 q=(uv-vec2(.59,.53))*vec2(1.3,1.7);
 vec3 stage=mix(vec3(.017,.029,.031),vec3(.090,.154,.153),exp(-dot(q,q)*2.8));
 color=vec4(mix(forestColor,stage,look.z)*(1.-v*.71),1.);
}
)";
const char* shadeV=R"(#version 300 es
layout(location=0) in vec3 a;out vec3 P;
uniform mat4 uVP;
void main(){P=a;gl_Position=uVP*vec4(a,1.);}
)";
const char* shadeF=R"(#version 300 es
precision mediump float;
in vec3 P;out vec4 outP;uniform vec4 uShade[3]; // x z radius alpha
void main(){float a=0.;for(int i=0;i<3;i++){
 vec4 f=uShade[i];vec2 d=(P.xz-f.xy)/max(f.z,.05);a+=exp2(-dot(d,d)*3.43)*f.w;}
 outP=vec4(.040,.034,.023,clamp(a,0.,.57));}
)";
}
