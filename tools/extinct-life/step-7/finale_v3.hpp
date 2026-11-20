// Dating and the last answer. All geometry is illustrative, tied to the
// original narration frames; only the atlas constitutes sourced geography.
#pragma once
#include "sets_v3.hpp"

namespace evidence {
inline void age_columns(CutSet& s){
    auto& g=s.g;const int k=s.shot;const float u=s.q;
    const float lift=k==41?s.here(.15f,2.65f):1;
    const float appear=k==44?s.here(.48f,1.92f):0;
    V p=k==41?lerp(V{-.28f,3.16f,-7.24f},V{.06f,2.59f,-6.53f},u):
         k==44?lerp(V{-.43f,2.26f,-6.28f},V{.32f,2.55f,-6.34f},u):V{.08f,2.55f,-6.7f};
    if(k==58)p={-.22f,3.31f,-6.24f};
    s.view(p,{.02f,-.52f,.21f},40.5f,0);s.stage(.29f);
    for(int i=0;i<2;i++){
        const float x=i?-1.72f:1.72f,z=0.f;
        const float top=.49f-(k==44?.17f:.12f)*i*lift,depth=1.27f+1.24f*lift;
        V c{x,top,z};V pick{i?-.09f:.09f,-.52f-.30f*i,-.795f};
        block(g,x-1.17f,x+1.17f,0,top,depth,1.53f,0,0,3+i*3);
        const bool core=k==44&&i;
        s.slab(core?s.dried:i?s.earth.koum:s.rim,c+V{0,.045f,0},{1.17f,.20f,.77f},31+i,.047f,0,.01f);
        s.mark(i,c+V{0,.065f,-.57f});s.mark(2+i,c+pick);
        if(core){
            float y=c.y+pick.y,z=pick.z;
            g.face({x-1.14f,y-.068f,z},{x+1.13f,y-.068f,z},{x+1.13f,y+.069f,z},{x-1.14f,y+.069f,z},JADE,.68f*appear);
        }
        const V col=i?JADE:HONEY;
        const float a=i?.23f+.62f*appear:.29f+.37f*appear;
        for(int j=0;j<32;j++){
            float dx=(j/31.f-.5f)*2.22f;
            V C=c+pick+V{dx,.029f*sinf(j*.56f),-.108f};
            if(core)g.dust(C,.015f+.008f*hash(j,11+i),col,a);
        }
        if(k==44&&i){
            const V P=c+pick+V{-.11f,.04f,-.13f};
            for(int j=0;j<10;j++){
                float a0=(.11f+.2f*hash(j,741))*appear,b=hash(j,742)*2*PI;
                V Q=P+V{cosf(b)*a0,sinf(b)*a0,0};
                g.dust(Q,.013f+.013f*hash(j,377),JADE,.74f*appear);
            }
        }
    }
}

inline void pollen_detail(CutSet& s){
    auto& g=s.g;const float u=s.q,t=s.t;const V c{-.51f,.025f,.1f};
    s.view(lerp(V{.05f,1.71f,-4.13f},V{1.01f,1.54f,-3.90f},u),{.38f,.10f,.05f},38.f,2);
    const V axes{1.28f,.80f,.94f};
    const auto P=[&](float a,float z){
        const float y=sinf(z),r=cosf(z),fold=(1-.139f*expf(-sq((y-.075f)*12.f)))*(1+.015f*sinf(a*13.f+3*z));
        return c+V{r*cosf(a),y,r*sinf(a)}*axes*fold;
    };
    g.lattice(112,72,[&](float u0,float v){
        float a=u0*2*PI-u*.73f,z=(v-.5f)*PI;V p=P(a,z),n=unit(p-c);
        const float seam=expf(-sq((sinf(z)-.075f)*21.f)),bead=.91f+.08f*cosf(118*a+.8f*cosf(z*56.f));
        V col=light(n,lerp(V{224,174,88},V{98,66,40},seam*.84f),bead)+V{54,22,6}*.38f;
        return Node{p,col};
    });
    for(int i=0;i<230;i++){
        float az=2*PI*hash(i,187)-u*.92f,y=hash(i,329)*2-1,r=sqrtf(1-y*y);
        V n={r*cosf(az),y,r*sinf(az)},p=P(az,asinf(y))-n*.009f;
        const float w=.008f+.035f*sq(hash(i,220));
        pebble(g,p,{w*1.22f,w*.91f,w},lerp({169,119,59},{227,192,123},hash(i,685)),475+i,6,9,.11f);
    }
    for(int i=0;i<27;i++){
        const float b=i*.671f+.072f*t;
        s.g.dust({c.x+1.24f*cosf(b),-.7f+.062f*i,.78f*sinf(b)},.013f+.018f*hash(i,14),HONEY,.26f);
    }
    s.mark(0,c+V{.42f,.35f,-.88f});
}

inline void fracture(CutSet& s){
    auto& g=s.g;const int k=s.shot;const bool end=k==60;
    const float drop=k==47?0:k==49?s.at(K_RIFT_DOWN,2.55f):k==50?1.f:.39f*s.at(K_RIFT_EARLY,2.10f)+1.63f*s.at(K_RIFT_LATE,2.35f);
    const float out=drop*(end?.91f:.38f),sink=drop*(end?.63f:.54f);
    V a,b,aim{.02f,-.24f,.14f};
    if(end&&s.f>=K_RIFT_LATE){a={-1.09f,5.8f,-9.94f};b={.47f,6.86f,-9.41f};aim={.07f,-.13f,.29f};}
    else if(k==49&&s.f>=K_RIFT_DOWN){a={-1.64f,3.05f,-6.86f};b={-.98f,3.89f,-6.93f};}
    else if(end){a={-.78f,4.32f,-7.76f};b={1.47f,3.81f,-7.89f};}
    else {a={-1.42f,3.14f,-6.94f};b={.82f,3.79f,-6.58f};}
    const float camq=end&&s.f>=K_RIFT_LATE?s.at(K_RIFT_LATE,3.4f):s.q;
    s.view(lerp(a,b,camq),aim,end?41.f:42.f,2);s.stage(.24f);
    const float depth=2.67f,front=-depth*.5f;
    // A dark common basement ensures no detached floating slabs. The basin
    // floor is continuous with the two sides, below the section cut.
    const float edge=3.45f+out;
    g.face({-edge,-1.60f,front},{edge,-1.60f,front},{edge,-1.91f,front},{-edge,-1.91f,front},{57,53,46});
    g.face({-edge,-1.60f,.5f*depth},{edge,-1.60f,.5f*depth},{edge,-1.60f,front},{-edge,-1.60f,front},{54,62,53});
    block(g,-3.45f,-1.13f,-out,.54f,2.14f,depth,0,-.52f,0);
    block(g,1.16f,3.42f,out,.54f,2.14f,depth,.51f,0,0);
    block(g,-1.11f,1.14f,0,.54f-sink,std::max(.48f,2.14f-sink),depth,-.54f,.51f,0);
    if(k!=50){
        float a0=k==47?s.at(K_FAULT_LIGHT,.39f):end?s.at(K_RIFT_EARLY,.46f)*(1-s.at(K_RIFT_LATE,2.16f)):s.at(K_RIFT_DOWN,.3f);
        for(float side:{-1.f,1.f}){
            const float x=side*(1.143f+out),y=.557f;
            g.line({x,y,front-.019f},{x-side*.78f,y-1.54f,front-.019f},HONEY,a0*.88f,2.8f);
            g.line({x,y,front-.007f},{x,y,.49f*depth},PAPER,a0*.61f,1.28f);
        }
    }
    float fill=k==50?s.at(K_RIFT_FILL,3.51f):end?s.at(K_RIFT_LATE,2.20f):0;
    if(fill>.0001f){
        const float bottom=.54f-sink;
        const float surface=end?lerp(bottom+.002f,.254f,fill):lerp(bottom+.002f,bottom+.331f,fill);
        const float baseWater=bottom+.004f;
        const float z=front-.026f;
        auto edges=[&](float y){return 1.145f+out+.513f*(y-.54f);};
        if(end){
            for(int j=0;j<16;j++){
                const float y=lerp(-1.61f,bottom,j/16.f),h=lerp(-1.61f,bottom,(j+1)/16.f),w=edges(y),r=edges(h);
                const V c=lerp({87,66,48},{145,115,78},.43f+.37f*cosf(j*1.08f));
                g.face({-w,y,z+.004f},{w,y,z+.004f},{r,h,z+.004f},{-r,h,z+.004f},c);
            }
            float r=edges(surface);
            g.line({-r,surface+.004f,z-.007f},{r,surface+.004f,z-.007f},JADE,.78f,2.08f);
        }
        if(!end){
            for(int j=0;j<9;j++){
                const float m=clamp(fill*10.75f-j);if(m<.002f)continue;
                const float y=bottom+.022f*j-.008f,w=edges(y)-.02f;
                const float zo=front-.012f;
                g.face({-w,y,zo},{w,y,zo},{w,y+.024f*m,zo},{-w,y+.024f*m,zo},lerp({121,87,52},{187,146,92},hash(j,578)));
            }
        }
        if(end&&surface>baseWater){
            for(int j=0;j<24;j++){
                const float v=j/24.f,u=(j+1)/24.f,y=lerp(baseWater,surface,v),h=lerp(baseWater,surface,u);
                const float w=std::max(.14f,edges(y)),r=std::max(.14f,edges(h));
                const V c=lerp({20,47,56},{56,113,116},v*v)*(.95f+.05f*sinf(j*.72f));
                g.face({-w,y,z},{w,y,z},{r,h,z},{-r,h,z},c,.93f); // bottom-up volume at the cut plane
            }
        }
        const float w=edges(surface);
        if(w>.1f)s.water(0,0,w,depth*.5f,surface,end?0:2,.993f);
        if(end){
            for(int i=0;i<3;i++){
                float t0=fill*.92f+.12f*i;
                for(int j=0;j<30;j++){
                    auto P=[&](float u){float xx=(2*u-1)*w;
                        return V{xx,surface+.006f,lerp(-1.3f,1.3f,t0)+.06f*cosf(u*19.f+i-t0*2.7f)};};
                    g.line(P(j/30.f),P((j+1)/30.f),PAPER,.21f*fill,1.f);
                }
            }
        }
    }
    const int kick=end?K_RIFT_EARLY:K_RIFT_DOWN;
    if(end||k==49){
        for(int i=0;i<52;i++){
            const float T=(s.f-kick)/24.f-hash(i,57)*1.04f;
            if(T<.0f||T>1.81f)continue;
            const float side=i%2?-.99f:1.f,off=hash(i,993)-.5f;
            V c={side*(1.09f+out*.72f+.13f*T)+off*.31f,std::max(-1.58f,.52f+1.20f*T*hash(i,83)-1.09f*T*T),front+2.47f*hash(i,1194)};
            float r=.024f+.072f*sq(hash(i,822));
            pebble(g,c,{r,r*.61f,r*.76f},lerp({132,120,80},{209,177,110},hash(i,903)),i+48,5,9,.23f,T*2.17f);
        }
    }
    s.mark(0,{-1.15f-out,.59f,front});s.mark(1,{1.16f+out,.59f,front});
    s.mark(2,{.0f,.515f-sink,front-.010f});s.mark(3,{0,fill>0?lerp(.54f-sink,.254f,fill):.54f,front});
    s.specks(609,21,{.48f,.51f,.32f},{3.2f,.84f,2.16f},HONEY,.075f);
}

inline void pools(CutSet& s){
    auto& g=s.g;
    s.view(lerp(V{-1.32f,5.15f,-6.25f},V{.63f,5.43f,-5.82f},s.q),{.02f,.035f,.12f},43.f,0);s.stage(.33f);
    const int hit[]={K_HABITAT_FIRST,K_HABITAT_NEXT,K_HABITAT_LAST};
    for(int i=0;i<3;i++){
        float a=s.at(hit[i],.86f),z=(i==1?.68f:i==2?-.36f:.086f);
        V p={(1-i)*2.09f,.01f+.09f*i,z};
        s.slab(i==1?s.ripples:s.earth.koum,p,{.99f,.54f,1.22f},197+i,.089f,1.f,.31f-.31f*a);
        if(a>.001f){
            const V col=lerp({48,113,115},{81,150,147},a);
            g.lattice(68,33,[&](float u,float w){float b=u*2*PI,k=sqrtf(w)*a;
                float off=.77f+.085f*sinf(3*b+i)+.065f*cosf(5*b);
                float x=k*off*cosf(b),z=k*off*.78f*sinf(b);
                return Node{p+V{x,.128f+.004f*cosf(x*18.f+z*28.f+s.t*3.),z},col*(.85f+.08f*sinf(x*29.f+z*27.f-s.t*4.f)+.12f*cosf(z*17.f-x*20.f+s.t))};
            });
            for(int j=0;j<6;j++){
                float a0=j*1.2f+i*.91f;
                V q=p+V{.75f*cosf(a0),.17f,.85f*sinf(a0)};
                g.dust(q,.016f,JADE,a*.59f);
            }
        }
        s.mark(i,p+V{0,.13f,-.65f});
    }
}

inline void fish_pass(CutSet& s){
    auto& g=s.g;const float u=s.q,t=s.t,sec=s.sec();
    V eye,look;float lens;
    if(sec<1.46f){eye=lerp(V{-4.02f,.77f,-4.10f},V{-3.89f,.50f,-3.68f},s.here(0,1.45f));look={.48f,.03f,0};lens=38.f;}
    else if(sec<4.62f){eye=lerp(V{-3.11f,1.51f,-5.60f},V{-2.02f,1.18f,-5.78f},s.here(1.46f,4.62f));look={.01f,.13f,.10f};lens=42.1f;}
    else if(sec<7.87f){eye=lerp(V{.37f,.66f,-7.60f},V{1.04f,.70f,-7.56f},s.here(4.62f,7.87f));look={.07f,.135f,.19f};lens=41.f;}
    else{eye=lerp(V{-1.77f,3.49f,-5.84f},V{-.85f,4.11f,-6.3f},s.here(7.87f,9.70f));look={.12f,.025f,.13f};lens=39.1f;}
    s.view(eye,look,lens,1,-.019f);
    const float angle=-.48f*(1-s.here(0,4.62f))+.18f*s.here(7.87f,9.65f);
    const float ca=cosf(angle),sa=sinf(angle),speed=.62f*sinf(PI*u);
    const V shift={lerp(1.11f,-.62f,s.here(0,9.6f)),.16f*sinf(t*.68f),.30f-.30f*speed};
    auto rot=[&](V x){return V{x.x*ca+x.z*sa,x.y,-x.x*sa+x.z*ca};};
    auto W=[&](V x){return shift+rot(x);};
    auto spine=[&](float x){return V{x,.105f*sinf(t*1.21f)+.081f*sinf(t*2.05f-x*.96f),.27f*sq(clamp((x+.70f)/3.45f))*sinf(t*3.97f-x*1.62f)};};
    auto body=[&](float u0,float v){
        const float x=lerp(-2.36f,2.03f,u0),A=2*PI*v;
        float core=.057f+.70f*powf(sinf(PI*clamp(u0)),.701f)*(1.30f-.87f*u0);
        float head=.355f*ramp(.0f,.050f,u0)*(1-ramp(.19f,.48f,u0));
        return W(spine(x)+V{0,std::max(head,core)*cosf(A),std::max(head,core)*.68f*sinf(A)});
    };
    const V key=unit({-.20f,.82f,-.52f});
    g.lattice(134,86,[&](float a,float b){
        V P=body(a,b),n=unit(cross(body(a+.0001f,b)-body(a-.0001f,b),body(a,b+.0001f)-body(a,b-.0001f)));
        if(dot(n,P-W(spine(lerp(-2.36f,2.03f,a))))<0)n=n*(-1);
        const float h=clamp(dot(n,key)),bat=clamp(dot(n,unit({.48f,.37f,.84f}))),sp=clamp(dot(reflect(unit(P-g.cam.p),n),key));
        const float rib=.84f+.060f*cosf(482.f*a+3.f*cosf(282*b))+.055f*cosf(351.f*b+21.f*a);
        const float curl=.81f+.19f*sinf(P.x*25.f+P.y*19.f+P.z*28.f+t*3.16f);
        V c=lerp({68,116,117},{160,156,111},clamp(.45f+.57f*cosf(2*PI*b))) * (rib*(.50f+.72f*h)*curl);
        c+=V{74,145,145}*(.37f*bat+.55f*sp*sp*sp*sp*sp*sp);
        return Node{P,c};
    });
    const auto fin=[&](V root,V edge,float width,float tip,float seed){
        const V dir=edge-root,normal=rot(unit(cross(dir,{.01f,0,1})));const float l=clamp(dot(normal,key));
        g.lattice(42,23,[&](float a,float b){
            const float x=2*b-1,h=powf(std::max(0.f,sinf(a*PI)),.72f);
            V p=root+dir*a+V{x*(width*h+sinf(a*1.39f)*tip),.070f*h*sinf(PI*b),h*.145f*cosf(t*2.70f+seed+2*b)};
            const float rib=.48f+.23f*cosf(b*64.f+cosf(a*32.f)*.37f)+.29f*a;
            const V c=lerp({59,103,109},{171,181,139},clamp(rib))*(.65f+.35f*l+.18f*a);
            return Node{W(p),c};
        });
    };
    for(float side:{-1.f,1.f}){
        fin(spine(-1.03f)+V{0,-.13f,side*.40f},spine(-.14f)+V{.01f,-.76f,side*(.67f+.15f*sinf(t*3.f+side))},.28f,.095f,side);
        fin(spine(.50f)+V{0,-.38f,side*.26f},spine(1.16f)+V{0,-.69f,side*(.49f+.13f*sinf(t*3.7f+side))},.254f,.051f,side);
        const V eye=spine(-1.98f)+V{0,.197f,side*.272f};
        pebble(g,W(eye),{.112f,.092f,.083f},{176,161,109},47,12,20,.021f);
        pebble(g,W(eye+V{-.017f,.0f,side*.065f}),{.066f,.061f,.028f},{19,30,35},49,8,19,.021f);
        g.dust(W(eye+V{-.043f,.034f,side*.082f}),.022f,PAPER,.88f);
        for(int j=1;j<=11;j++){
            const auto P=[&](float q){return W(spine(-1.43f)+V{.147f*sinf(PI*q),.32f-.56f*q,side*(.27f+.187f*sinf(q*PI))});};
            g.line(P((j-1)/11.f),P(j/11.f),{39,71,73},.74f,1.85f);
        }
    }
    fin(spine(-.58f)+V{0,.39f,0},spine(.01f)+V{0,1.12f,.047f},.489f,.020f,.23f);
    fin(spine(.79f)+V{0,.248f,0},spine(1.25f)+V{0,.76f,.039f},.316f,.034f,.76f);
    fin(spine(1.18f)+V{0,-.22f,.045f},spine(1.51f)+V{0,-.65f,.080f},.287f,.036f,.43f);
    // Three lobes are kept visible even on the closer pass.
    fin(spine(1.83f),spine(2.91f)+V{0,.76f,.042f},.545f,.109f,.44f);
    fin(spine(1.83f),spine(2.85f)+V{0,-.67f,-.053f},.542f,.110f,.32f);
    fin(spine(1.91f),spine(3.21f)+V{0,.018f,.044f},.181f,.037f,.46f);
    s.specks(368,171,{.12f,.24f,.83f},{6.4f,2.7f,3.77f},{125,210,193},.30f);
    s.mark(0,W(spine(-1.98f)+V{0,.22f,-.32f}));
}

inline void fossil_match(CutSet& s){
    auto& g=s.g;
    const bool portrait=g.w<g.h;
    V eye=lerp(V{-.85f,4.11f,-6.30f},V{-.31f,5.72f,-4.61f},s.here(8.50f,9.72f));
    s.view(portrait?eye*1.19f:eye,{.04f,.025f,.13f},portrait?51.f:39.1f,2);
    s.stage(.32f);const V C{.0f,.035f,.07f};
    s.slab(s.ripples,C,{3.18f,.54f,1.73f},251,.09f,0,.10f);
    const V col{204,178,128};
    // An anonymous, incomplete skeleton illustration echoing the swim axis.
    // No photographed or exact Mawsonia specimen is asserted here.
    for(int i=0;i<31;i++){
        float u=i/30.f,x=lerp(-2.39f,1.27f,u),z=.099f+.051f*sinf(u*PI*3.4f);
        if(i>8&&i<11)continue;
        const V P=C+V{-x,.098f,z};
        const float r=.048f+.021f*hash(i,901);
        pebble(g,P,{r,r*.50f,r*1.31f},col*(.71f+.29f*hash(i,873)),i+281,7,13,.22f);
        if(i>7&&i%4!=0){
            for(int sign:{-1,1}){
                V d={-.12f,.002f,sign*(.19f+.39f*sinf(PI*u))};
                g.line(P,P+d,col,.77f,1.92f);
                g.line(P+d,P+d+V{-.15f,.0f,d.z*.33f},col,.72f,1.68f);
            }
        }
    }
    for(int i=0;i<6;i++){
        V P=C+V{-1.38f-.10f*i,.101f,.07f+.060f*cosf(i*.9f)};
        pebble(g,P,{.20f-.012f*i,.033f,.31f-.019f*i},col*(.89f-.033f*i),296+i,8,18,.16f,.16f*i);
    }
    s.mark(0,C+V{-1.37f,.13f,.06f});
}

inline void independent_clues(CutSet& s){
    std::swap(s.g,s.half);
    s.view(lerp(V{-.68f,4.66f,-4.68f},V{-.36f,5.12f,-4.48f},s.q),{.035f,.25f,.1f},44.f,2);
    s.stage(.25f);
    s.slab(s.earth.brazil,{.0f,.12f,.1f},{1.55f,.63f,1.30f},56,.07f);
    s.contour(s.earth.brazil,{.0f,.12f,.1f},.55f,HONEY,.74f,1.55f/1.77f,1.30f/1.78f,.044f);
    std::swap(s.g,s.half);s.save_half();std::swap(s.g,s.half);
    fossil_match(s);std::swap(s.g,s.half);s.pair_out();
}

inline void fossil(CutSet& s,bool demo=false){
    auto& g=s.g;const float q=s.q;
    s.view(lerp(V{-.15f,4.97f,-2.83f},V{.88f,5.67f,-1.27f},q),{.025f,.025f,.17f},43.f,2);s.stage(.28f);
    for(int i=0;i<2;i++){
        V C={i?-1.67f:1.67f,.08f,(i-1)*.16f};
        const auto& stratum=i?s.dried:s.ripples;
        s.slab(stratum,C,{1.42f,.56f,1.25f},311+i, .11f,.91f,.28f);
        // Fragment assemblage, not a fabricated specimen or surveyed basin pin.
        float a=demo?1.f:s.at(K_OTHER_BASINS,.58f);
        for(int j=0;j<18;j++){
            const float u=j/17.f,x=-.98f+1.96f*u,z=.19f+.25f*sinf(PI*u)*(i?1.f:-1.f);
            const float y=.083f+.035f*hash(j,i+172);
            const float r=.035f+.050f*hash(j,i+80);
            V p=C+V{x,y,z};
            if(((j+i*2)%9==1||j==0)&&!demo)continue;
            const V c=lerp(i?V{133,152,133}:V{166,139,101},PAPER,clamp(.19f+.44f*a));
            pebble(g,p,{r,r*.31f,r*1.42f},c,181+i*12+j,8,13,.21f);
            if(j<14&&(j+i)%4!=0){
                const float h=.12f+.18f*sinf(u*PI);
                for(int l=0;l<6;l++){
                    V a0=p+V{.03f*l/6.f,.021f,h*l/6.f},b=p+V{.03f*(l+1)/6.f,.02f,h*(l+1)/6.f};
                    g.line(a0,b,c,.89f,1.9f);
                }
            }
        }
        s.mark(i,C+V{0,.095f,.25f});
    }
}

inline void answer(CutSet& s){
    auto& g=s.g;const float t=s.at(K_ROCKS_ANSWER,2.5f);
    s.view(lerp(V{.07f,5.32f,-5.26f},V{-1.01f,5.40f,-5.08f},s.q),{.03f,-.05f,.27f},46.f,0);s.stage(.31f);
    const float out=.06f+.97f*t;
    // Each retreating terrain block owns its track slab in local coordinates.
    // Coastlines never morph; the gap is explicitly an explanatory diagram.
    s.water(0,0,6.7f,3.92f,-.53f,0,.998f);
    for(int i=0;i<2;i++){
        const float sign=i?-1.f:1.f;const V P={sign*(1.38f+out),.075f,.06f};
        const float left=i?-5.50f:.017f,right=i?-.017f:5.50f;
        const V basecol=i?V{78,111,99}:V{155,124,80};
        auto vertex=[&](float u,float z){
            float x=lerp(left,right,u)+sign*out+.091f*cosf(z*4.2f+i)*sq(i?u:1-u);
            V p={x,-.18f+.093f*fnoise(1.44f*x-2*i,2.3f*z),z};
            return p;
        };
        g.lattice(56,47,[&](float u,float v){
            float z=lerp(-1.66f,2.37f,v);V p=vertex(u,z);const float ret=fnoise((p.x-sign*out)*11.f,9.f*p.z);
            const float rise=.46f+.42f*fnoise((p.x-sign*out)*2.9f,p.z*3.2f)*(.76f+.31f*ret);
            return Node{p,basecol*(rise*1.26f)};
        });
        for(int side=0;side<4;side++)for(int n=0;n<32;n++){
            auto E=[&](float u){return vertex(side==0?u:side==1?1.f:side==2?1-u:0.f,lerp(-1.66f,2.37f,side==0?0.f:side==1?u:side==2?1.f:1-u));};
            V a=E(n/32.f),b=E((n+1)/32.f);
            for(int j=0;j<8;j++){
                auto C=[&](V p,float t0){p.y=lerp(p.y,-1.16f,t0);return p;};
                float u=j/8.f,v=(j+1)/8.f;
                const V c=basecol*(.43f+.12f*cosf(j*2.1f+side)+.09f*hash(n,j+31));
                g.face(C(a,u),C(b,u),C(b,v),C(a,v),c);
            }
        }
        const auto& b=i?s.earth.koum:s.earth.brazil;
        s.slab(b,P,{1.20f,.33f,1.12f},56+i,.07f,0,.015f);
        s.contour(b,P,.54f,i?JADE:HONEY,.87f*s.at(K_ROCKS_ANSWER,.42f),1.20f/1.77f,1.12f/1.78f,.042f);
        s.mark(i,P+V{-.07f,.078f,.23f});
        s.mark(2+i,P+V{0,-.20f,-1.65f});
    }
}
}
