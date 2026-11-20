#pragma once
namespace ant {
const char *geoVS=R"(#version 300 es
precision highp float;
layout(location=0) in vec3 aP;layout(location=1) in vec3 aN; layout(location=2) in vec2 aUV;
layout(location=3) in vec4 m0;layout(location=4) in vec4 m1;layout(location=5) in vec4 m2;layout(location=6) in vec4 m3;layout(location=7) in vec4 col;
uniform mat4 uVP;uniform mat4 uView;uniform mat4 uLight;
out vec3 P,N,Lp;out vec2 UV;out float D;flat out vec4 C;
void main(){mat4 m=mat4(m0,m1,m2,m3);vec4 p=m*vec4(aP,1.);P=p.xyz;
 N=normalize(aN.x*m0.xyz/max(1e-7,dot(m0.xyz,m0.xyz))+aN.y*m1.xyz/max(1e-7,dot(m1.xyz,m1.xyz))+aN.z*m2.xyz/max(1e-7,dot(m2.xyz,m2.xyz)));
 Lp=(uLight*p).xyz*.5+.5;D=-(uView*p).z;UV=aUV;C=col;gl_Position=uVP*p;}
)";
const char *shadowVS=R"(#version 300 es
layout(location=0) in vec3 aP;layout(location=3) in vec4 m0;layout(location=4) in vec4 m1;layout(location=5) in vec4 m2;layout(location=6) in vec4 m3;
uniform mat4 uVP;
void main(){gl_Position=uVP*mat4(m0,m1,m2,m3)*vec4(aP,1.);}
)";
const char *shadowFS=R"(#version 300 es
precision mediump float;
void main(){}
)";
const char *geoFS=R"(#version 300 es
precision highp float;
in vec3 P,N,Lp;in vec2 UV;in float D;flat in vec4 C;
out vec4 outColor;
uniform sampler2D uSand;uniform sampler2D uShadow;
uniform vec3 uEye,uSun,uAnt,uLarva;
uniform vec4 uLook; // warm key, sky, diagram, ambient level
float hash(vec2 p){p=fract(p*vec2(123.31,311.17));p+=dot(p,p+19.18);return fract(p.x*p.y);}
float sdh(float k){return step(Lp.z-k,texture(uShadow,Lp.xy).r);}
vec3 film(vec3 a){a=max(a-.004,0.); return clamp((a*(2.1*a+.13))/(a*(2.1*a+.66)+.19),0.,1.);}
void main(){
 float k=C.a; vec3 n=normalize(N),b=C.rgb, V=normalize(uEye-P), l=uSun;
 float dyn=hash(floor(UV*180.)); float rough=.34;float occ=1.;
 if(k<.5){
   vec2 q=P.xz*.34;
   vec3 tex=texture(uSand,q).rgb;
   float cold=clamp((2.4-length(P.xz))*.12,0.,.28);
   float v=sin(P.x*3.1+cos(P.z*2.2))*sin(P.z*3.9)*.065+sin(P.x*.8+P.z*1.2)*.08+.93;
   // Use top-down albedo and gently directional grain relief. Avoid screen-space crawl.
   tex=mix(tex,vec3(.687,.568,.424),.18);
   b=pow(tex,vec3(2.06))*vec3(1.,.91,.81)*v;
   vec2 r=vec2(.0019,0.);float g=dot(tex,vec3(.3,.6,.1));
   vec2 bGrad=vec2(texture(uSand,q+r).g-g,texture(uSand,q+r.yx).g-g);
   n=normalize(n+vec3(-bGrad.x*.31,0.,-bGrad.y*.31));
   float oa=length((P.xz-uAnt.xz)*vec2(.90,1.58));
   float ol=length((P.xz-uLarva.xz)*vec2(1.4,1.15));
   occ=(1.-.29*(1.-smoothstep(.12,1.30,oa))*exp(-max(0.,uAnt.y-P.y-.50)*1.4))*(1.-.47*(1.-smoothstep(.10,.89,ol)))*(1.-cold);
   rough=.81;
 }else if(k<1.5){float streak=sin(UV.x*231.+sin(UV.y*73.)*1.5)*.038;
  b*=.83+.24*dyn+streak;rough=.22+(.165*dyn);occ=.92+.08*sin(UV.y*3.14);
 }else if(k<2.5){b*=.88+.16*dyn;rough=.19;}
 else if(k<3.5){b*=.83+.25*dyn;rough=.54;}
 else if(k<4.5){rough=.70;}
 else if(k<5.5){rough=.45;}
 else{rough=.69;}
 float lam=max(dot(n,l),0.),h=max(dot(n,normalize(l+V)),0.);
 float shadow=1.;
 if(k<5.7 && Lp.x>.002&&Lp.x<.998&&Lp.y>.002&&Lp.y<.998&&Lp.z<1.){
   float bias=.00064+.00105*(1.-lam);
   vec2 d=vec2(.00153,0.);
   shadow=sdh(bias);
   if(D<5.6 && k<.5) shadow=.25*(shadow+step(Lp.z-bias,texture(uShadow,Lp.xy+d).r)+step(Lp.z-bias,texture(uShadow,Lp.xy-d).r)+step(Lp.z-bias,texture(uShadow,Lp.xy+d.yx).r));
   shadow=mix(.26,1.,shadow);
 }
 float rim=pow(1.-max(dot(V,n),0.),2.7);
 float front=max(0.,dot(n,normalize(vec3(-.44,.64,.66))));
 float back=max(0.,dot(n,normalize(vec3(.62,.36,-.65))));
 float spec=pow(h,mix(128.,5.,rough))*mix(.45,.032,rough)*lam;
 float bounce=max(0.,-n.y)*.12;
 vec3 ground=vec3(.54,.62,.69)*(uLook.y*(.47+.32*max(n.y,0.)))+vec3(.43,.24,.10)*bounce+front*vec3(.35,.48,.60)*.86;
 vec3 light=vec3(1.25,1.04,.79)*uLook.x*lam*shadow;
 vec3 tint=vec3(1.,.79,.50);
 vec3 c=b*(light+ground)*occ+spec*tint*(.55+.45*shadow)*uLook.x;
 if(k>.5&&k<3.5){c+=vec3(.38,.53,.62)*pow(max(dot(n,normalize(V+vec3(-.4,.65,.63))),0.),32.)*.148;
  c+=(vec3(.35,.16,.071)*rim*back*.57+vec3(.16,.23,.30)*rim*front*.37)*(1.-.5*uLook.z);
 }
 if(k>5.5){c+=b*.64;}
 if(uLook.z>.5&&k<.5)c=mix(c,vec3(.010,.022,.026),.89);
 float fog=1.-exp(-max(0.,D-9.)*.025);
 c=mix(c,vec3(.056,.047,.024),fog*(1.-uLook.z)*.68);
 outColor=vec4(pow(film(c*uLook.w),vec3(.87)),min(D/35.,.98));
}
)";
const char *fullVS=R"(#version 300 es
precision highp float;
out vec2 uv;
void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));uv=p;gl_Position=vec4(p*2.-1.,0.,1.);}
)";
const char *skyFS=R"(#version 300 es
precision mediump float;
in vec2 uv;out vec4 color;uniform sampler2D uMatte;uniform vec4 uSky;
void main(){vec2 q=(uv-.5)*.85+.5+uSky.xy;vec3 c=texture(uMatte,q).rgb;
 c=c*.79;if(uSky.z>.5){float b=exp(-dot((uv-vec2(.59,.50))*vec2(1.,1.55),(uv-vec2(.59,.50))*vec2(1.,1.55))*3.1);c=mix(vec3(.023,.042,.044),vec3(.102,.181,.182),b);}
 color=vec4(c,1.);}
)";
const char *postFS=R"(#version 300 es
precision mediump float;
in vec2 uv;out vec4 color;uniform sampler2D uPicture,uOverlay;
uniform vec2 uPix;uniform vec4 uLens;uniform float uFade;
void main(){vec4 tex=texture(uPicture,uv);float d=tex.a*35.;float blur=clamp(abs(d-uLens.x)/max(uLens.x,.65),0.,1.);
 float a=blur*blur*uLens.y;vec3 col=tex.rgb;
 if(a>.45){vec2 r=uPix*a;vec4 p1=texture(uPicture,uv+r*vec2(.93,.17)),p2=texture(uPicture,uv+r*vec2(-.61,.74)),p3=texture(uPicture,uv+r*vec2(-.72,-.54)),p4=texture(uPicture,uv+r*vec2(.27,-.85));
  col=(tex.rgb*1.4+p1.rgb+p2.rgb+p3.rgb+p4.rgb)/5.4;
 }
 vec2 p=(uv-.5)*vec2(1.14,.9);col*=1.-.34*dot(p,p);
 col=mix(col,vec3(.012,.021,.018),uLens.z);
 vec4 o=texture(uOverlay,uv);col=mix(col,o.rgb,o.a*uFade);
 color=vec4(clamp(col*uLens.w,0.,1.),1.);
}
)";
}
