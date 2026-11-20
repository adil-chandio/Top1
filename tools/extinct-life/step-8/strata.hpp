#pragma once
#include "terrain.hpp"
namespace cinema {
inline void sediment_block(CutSet& s,V C,float L,float U,float thick,float depth,float slopeL,float slopeR,int kind,float relief=1.f){
    auto& g=s.g;const V sun=unit({-.69f,.58f,-.54f});
    auto P=[&](float x,float z,float h){
        float grainX=lerp(L+slopeL*h,U+slopeR*h,x);
        return C+V{grainX,h+relief*(.037f*sinf(grainX*3.2f+z*.8f)+.021f*sinf(grainX*12.4f-z*4.3f)+.033f*(fnoise(grainX*9.f,z*7.2f)-.5f)),z};
    };
    g.lattice(64,36,[&](float u,float v){
        float z=lerp(-depth,depth,v);V p=P(u,z,0);
        const float x=p.x-C.x, coarse=fnoise(x*3.9f,z*3.3f),fine=fnoise(x*23.2f,z*17.9f+kind);
        float type=fnoise(x*1.45f+kind*7.f,z*1.41f+2.f);
        V dye=lerp({105,105,86},{196,157,103},ramp(.31f,.71f,type));
        V n=unit({-.119f*cosf(x*3.2f+z*.8f)-.261f*cosf(x*12.4f-z*4.3f),1,.091f*cosf(x*12.4f-z*4.3f)});
        return Node{p,light(n,dye,.92f+.24f*(.78f*coarse+.22f*fine))};
    });
    const V layers[]={{149,99,65},{192,144,98},{126,104,76},{89,106,113},{134,138,130},{183,142,91},{104,82,70},{131,113,96}};
    auto C0=[&](V p,V n,float h){
        float am=h/thick;float bias=(p.x-C.x)*.84f+(p.z-C.z)*.39f;
        float jitter=.17f*sinf(bias*3.f)+.11f*sinf(bias*11.f);
        int i=int(am*32.0f+jitter+33.4f);
        float a=ramp(.03f,.77f,fnoise((p.x-C.x)*17.0f+p.z*2.07f,(p.y-C.y)*38.f));
        float dark=.74f+.23f*a+.13f*sinf(am*235.f+bias)+.044f*sinf(am*420.f+8.f*bias);
        return layers[(std::max(0,i)+kind)%8]*dark*(V{.37f,.40f,.44f}+V{.70f,.56f,.42f}*clamp(dot(sun,n)));
    };
    for(int side=0;side<4;side++){
        const V n=side==0?V{0,0,-1}:side==1?unit({1,-slopeR,0}):side==2?V{0,0,1}:unit({-1,slopeL,0});
        g.lattice(side%2?37:64,66,[&](float a,float v){
            const auto Z=side==0?-depth:side==2?depth:lerp(-depth,depth,a);
            const auto X=side==1?1.f:side==3?0.f:a;const float h=-v*thick;
            V p=P(X,Z,h);return Node{p,C0(p,n,h)};
        });
    }
}
inline void gap_water(CutSet& s,float w,float z,float y,float fill,int mode){
    auto& g=s.g;const V sun=unit({-.47f,.62f,-.58f});
    g.lattice(mode==2?128:100,mode==2?83:68,[&](float u,float v){
        const float x=(2*u-1)*w,pz=(2*v-1)*z;
        const float warp=.93f*sinf(pz*1.5f+x*.49f+s.t*1.22f);
        const float a=sinf(x*3.27f+pz*7.7f-s.t*2.20f+warp),b=cosf(x*8.1f-pz*6.2f+s.t*1.50f+warp*.41f);
        const float edge=1-sq(2*u-1),height=(.0051f*a+.0033f*b)*edge;
        V pt={x,y+height,pz};V n=unit({.024f*a+.022f*b,1,.047f*a-.026f*b}),v0=unit(g.cam.p-pt);
        const float face=1-clamp(dot(n,v0));float F=.028f+.82f*face*face*face*face;
        float k=clamp(dot(reflect(v0*(-1),n),sun));k=k*k;k=k*k;k=k*k;
        float crest=ramp(.87f,1.18f,.68f*a+.43f*b);
        V c=lerp(mode==1?V{.058f,.101f,.094f}:V{.018f,.070f,.091f},V{.23f,.37f,.43f},F);
        c+=V{.81f,.72f,.55f}*(k*k*k*k*.26f)+V{.137f,.151f,.116f}*((1-ramp(.006f,.145f,fabsf(x)-w+.16f))*crest*fill*.30f);
        uint8_t out[3];camera_response.put(out,c);
        return Node{pt,{float(out[0]),float(out[1]),float(out[2])}};
    });
}
inline void rift_stage(CutSet& s){
    const int k=s.shot;const bool final=k==60;auto& g=s.g;
    float release=k==47?0:k==49?s.at(K_RIFT_DOWN,2.63f):k==50?1:s.at(K_RIFT_EARLY,2.40f);
    float fill=k==50?s.at(K_RIFT_FILL,3.78f):final?s.at(K_RIFT_LATE,2.26f):0;
    float spread=final?(.56f*release+1.46f*fill):.48f*release,sink=final?.55f*release+.65f*fill:.59f*release;
    V eye= final?spline({-1.86f,3.53f,-8.15f},{-1.01f,4.10f,-7.75f},{-.26f,4.42f,-8.05f},{1.04f,5.55f,-8.34f},s.q):
       k==49?spline({-1.24f,2.54f,-6.78f},{-1.92f,2.74f,-6.85f},{-.86f,3.23f,-7.24f},{.22f,3.91f,-7.32f},s.q):
       k==50?lerp(V{.58f,3.82f,-7.35f},V{1.51f,4.70f,-6.48f},s.q):lerp(V{-1.43f,3.35f,-6.81f},V{.79f,3.37f,-6.38f},s.q);
    s.view(eye,{.02f,-.236f,.26f},final?43.4f:41.6f,2);s.stage(.59f);
    const float h=.48f,z=1.48f,base=-1.91f;
    const float left=-3.51f-spread,right=3.51f+spread;
    g.face({left,-1.54f,-z},{right,-1.54f,-z},{right,base,-z},{left,base,-z},{58,53,43});
    g.face({left,-1.54f,-z},{right,-1.54f,-z},{right,-1.54f,z},{left,-1.54f,z},{57,60,51});
    sediment_block(s,{-spread,h,0},-3.45f,-1.065f,2.03f,z,0,-.47f,1);
    sediment_block(s,{spread,h,0},1.065f,3.45f,2.03f,z,.47f,0,1);
    sediment_block(s,{0,h-sink,0},-1.065f,1.065f,2.03f-sink,z-.003f,-.47f,.47f,1,final?.28f:1.f);
    const float edge1=1.065f+spread;
    if(k==47||k==49||final){
        const float a=k==47?s.at(K_FAULT_LIGHT,.46f):k==49?s.at(K_RIFT_DOWN,.37f):release*(1-fill);
        for(float dir:{-1.f,1.f}){
            g.line({dir*edge1,.484f,-z-.015f},{dir*(edge1-.827f),-1.26f,-z-.015f},HONEY,.85f*a,2.36f);
            g.line({dir*edge1,.481f,-z-.008f},{dir*edge1,.48f,z},PAPER,.43f*a,1.28f);
        }
    }
    if(fill>.0001f){
        const float bottom=h-sink,top=bottom+(final?(.29f-bottom):.36f)*fill;
        const float edge=edge1+.47f*(top-h)-.019f;
        if(!final){
            for(int i=0;i<11;i++){
                float E=clamp(fill*11.5f-i);if(E<.005f)continue;
                const float y=bottom+.0241f*i-.013f,w=edge1+.47f*(y-h);
                for(int n=0;n<32;n++){
                    float x=lerp(-w,w,n/32.f),X=lerp(-w,w,(n+1)/32.f);
                    V c=lerp({118,90,63},{190,147,91},.18f+.68f*hash(n+i*5,221));
                    g.face({x,y,-z-.023f},{X,y,-z-.023f},{X,y+.026f*E,-z-.023f},{x,y+.026f*E,-z-.023f},c);
                }
            }
        }else{
            g.lattice(46,21,[&](float u,float v){
                float y=lerp(bottom,top,v),w=edge1+.47f*(y-h);
                float band=clamp(v+(1-v)*.037f*cosf(u*31.5f-v*24.f));
                return Node{{lerp(-w,w,u),y,-z-.019f},lerp({16,39,54},{72,125,129},band*band)};
            });
        }
        if(edge>.08f)gap_water(s,edge,z,top,fill,final?0:1);
    }
    const int a=final?K_RIFT_EARLY:K_RIFT_DOWN;
    if(k==49||final){
        for(int i=0;i<48;i++){
            float t=(s.f-a)/24.f-hash(i,199)*.86f;if(t<0||t>2.18f)continue;
            float sign=i%2?-1.f:1.f,rad=.012f+.051f*sq(hash(i,224));
            const float y=std::max(h-sink+.01f,.51f+(.33f+1.05f*hash(i,438))*t-2.05f*t*t);
            V p={sign*(edge1-.14f-.47f*smoother(t/1.5f)),y,lerp(-z,z,hash(i,716))};
            pebble(g,p,{rad*1.63f,rad*.66f,rad*1.08f},lerp({132,109,72},{203,161,104},hash(i,251)),i+102,4,7,.23f,t*3.3f);
        }
    }
    s.mark(0,{-edge1,h,-z});s.mark(1,{edge1,h,-z});s.mark(2,{0,h-sink,-z});
}

inline void rock_answer(CutSet& s){
    const float f=s.at(K_ROCKS_ANSWER,2.72f),out=.02f+1.17f*f;
    s.view(spline({.76f,7.15f,-5.36f},{.38f,6.77f,-6.05f},{-.57f,6.04f,-6.38f},{-.96f,5.63f,-6.62f},s.q),{.0f,-.37f,.12f},40.f,0);
    s.stage(.55f);gap_water(s,12.04f,6.88f,-.62f,1.f,2);
    for(int i=0;i<2;i++){
        const float k=i?-1:1;const float x=k*out;
        sediment_block(s,{x,-.21f,.21f},i?-4.61f:.012f,i?-.012f:4.61f,1.18f,1.85f,i?.05f:0,i?0:-.06f,i?3:1);
        const V P={x+k*1.77f,.018f,.11f};const auto& b=i?s.earth.koum:s.earth.brazil;
        material(s,b);s.slab(b,P,{1.13f,.34f,1.16f},142+i,.08f,0,.018f);
        s.contour(b,P,.55f,i?JADE:HONEY,s.at(K_ROCKS_ANSWER,1.02f)*.55f,1.13f/1.77f,1.16f/1.78f,.037f);
        s.mark(i,P+V{.05f,.033f,.28f});
    }
}
// Two independent sections sit beside the age reading. Their separate beds
// remain visible while the time ranges appear; no cross-bed horizon is drawn.
inline void age_stage(CutSet& s){
    const bool broad=s.shot==45;
    const V eye=spline({-.45f,2.85f,-8.90f},{-.13f,3.65f,-8.95f},{.56f,3.91f,-8.80f},{.89f,3.54f,-8.64f},s.q);
    s.view(eye,{-3.56f,-.16f,.26f},43.5f,0,.023f-.016f*s.q);
    s.stage(.33f);
    for(int i=0;i<2;i++){
        const float d=i?.72f:.80f;
        const V p={i?-.94f:.91f,i?.09f:.33f,i?-.13f:.13f};
        sediment_block(s,p,-d,d,1.30f+.27f*i,.65f+i*.12f,0,0,i?5:0,broad?.48f:.72f);
        const auto& grid=i?s.earth.koum:s.rim;
        s.slab(grid,p+V{0,.075f,.04f},{d*.88f,.22f,.53f},176+i,.057f,0,.019f);
    }
}
inline void habitats(CutSet& s){
    auto& g=s.g;
    s.view(spline({-1.38f,5.34f,-6.31f},{-.74f,4.61f,-6.09f},{.51f,5.32f,-5.63f},{1.02f,5.97f,-5.13f},s.q),{.02f,.0f,.12f},44.9f,0);
    s.stage(.42f);
    const int in[]={K_HABITAT_FIRST,K_HABITAT_NEXT,K_HABITAT_LAST};
    for(int i=0;i<3;i++){
        const float a=s.at(in[i],1.04f),z=i==1?.58f:i==2?-.32f:.10f;
        const V P={(1-i)*2.08f,.058f+.05f*i,z};const auto& b=i==1?s.ripples:i==2?s.weather:s.earth.koum;
        material(s,b);s.slab(b,P,{1.01f,.52f,1.23f},352+i,.085f,.78f,.027f);
        if(a>.002f){
            g.lattice(71,38,[&](float u,float w){
                float phi=u*2*PI,r=sqrtf(w)*a;
                const float x=r*cosf(phi)*(.72f+.093f*cosf(phi*3.f+i)),zz=r*sinf(phi)*(.61f+.043f*sinf(phi*7.f+i));
                float phase=x*10.8f+zz*5.4f+s.t*2.13f+i*.9f,wave=cosf(phase+.75f*cosf(zz*9.f)),chip=sinf(zz*23.f-x*17.f+s.t*4.4f);
                V pt=P+V{x,.122f+.0043f*wave+.0021f*chip,zz};
                const float F0=1-clamp(dot(unit(g.cam.p-pt),unit({.069f*wave,1.f,.046f*chip})));
                V c=lerp(i==2?V{.048f,.115f,.106f}:V{.035f,.136f,.141f},V{.173f,.256f,.24f},.14f+.44f*sq(F0)+.08f*chip);
                c+=V{.14f,.114f,.064f}*ramp(.57f,1.f,sq(w))*.24f;
                uint8_t pix[3];camera_response.put(pix,c);return Node{pt,{float(pix[0]),float(pix[1]),float(pix[2])}};
            });
        }
        for(int j=0;j<7;j++){
            const float phase=(j+.09f*i)*2.398f,F=.86f+.105f*hash(i,j+711);
            V p=P+V{cosf(phase)*F,.047f,sinf(phase)*F};
            float height=.083f+.105f*hash(j,i+85),bend=.027f*sinf(s.t*1.51f+j+i);
            for(int v=-1;v<=1;v++){
                g.line(p,p+V{v*.08f,bend+height,v*.034f-.019f},{116,126,79},.72f,1.08f);
            }
        }
        s.mark(i,P+V{0,.144f,-.65f});
    }
}

}
