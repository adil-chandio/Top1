// Geographic cartography, tectonic cutaways, habitats and fish rig.
#pragma once
#include "sets.hpp"

namespace feature {

inline void world(Studio& s,int v){
    auto& g=s.g;auto& earth=s.earth;
    const bool old=v>=1&&v<=5;const float u=s.q, t=s.t;
    float lat=0,lon=0,range=14.90f,roll=.016f,aimlon=0,aimlat=0;
    if(v==0){lat=lerp(17.f,-4.8f,u);lon=lerp(-14.8f,-34.6f,u);aimlon=lerp(-20.f,-38.26f,u);aimlat=lerp(1.f,-6.7f,u);range=lerp(15.1f,9.35f,u);}
    else if(old){lat=lerp(3.7f,-3.45f,u)+(v==1?6.f:0.f);lon=lerp(-10.3f,3.22f,u)+(v==2?6.f:0.f);range=lerp(v==4?13.9f:15.8f,v==4?13.4f:14.3f,u);
        aimlon=lerp(-6.f,.6f,u);aimlat=lerp(.4f,-3.f,u);roll=lerp(.026f,-.038f,u);}
    else{lat=lerp(17.4f,10.3f,u);lon=lerp(-21.f,-16.3f,u);aimlon=-15.7f;aimlat=1.5f;range=lerp(15.78f,14.68f,u);
        if(v>=7){lat=lerp(9.9f,8.35f,u);lon=lerp(-16.3f,-13.5f,u);range=lerp(14.67f,14.31f,u);}
        if(v==8){lat=lerp(8.35f,4.7f,u);lon=lerp(-13.5f,-9.1f,u);range=lerp(14.31f,13.7f,u);}}
    const V p=geo(lat,lon)*range,aim=geo(aimlat,aimlon)*(v==0?R-.1f:1.92f);
    const Camera cam(p,aim,40.2f,g.w/float(g.h),roll);g.cam=cam;
    const auto& field=old?earth.ancient:earth.modern;
    const float alpha=(v==4?s.at(K_RANGE,.94f):v==5?(1-ramp(.74f,.97f,u))*.84f:0.f);
    const V centre=unit(earth.pin(true,0)+earth.pin(true,1));
    #pragma omp parallel for schedule(static)
    for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
        const float X=(x+.5f)/g.w,Y=(y+.5f)/g.h;V d=cam.ray(X,Y),c=earth.sphere(field,p,d,t,X,old);
        if(alpha>.0001f){
            float b=dot(p,d),dd=R*R-dot(p,p)+b*b;
            if(dd>0){const V n=(p+d*(-b-sqrtf(dd)))/R;float radius=1-dot(n,centre);
                // Generous feather: not surveyed boundaries or a path.
                float w0=expf(-radius*156.f);const float land=field.at(n).m;
                c=c+V{.112f,.198f,.091f}*(w0*land*alpha*(.88f+.12f*sinf(t*.92f)));}
        }
        c=c*(1.f-.25f*clamp(sq((X-.54f)*1.62f)+sq((Y-.5f)*1.28f)));int k=(y*g.w+x)*3;
        g.rgb[k]=earth.byte(c.x);g.rgb[k+1]=earth.byte(c.y);g.rgb[k+2]=earth.byte(c.z);
    }
    s.mark(0,earth.pin(old,0));s.mark(1,earth.pin(old,1));
    const V L=unit(earth.pin(old,0)),B=unit(earth.pin(old,1));
    for(int i=0;i<10;i++){float f=i/9.f; s.mark(i+2,unit(lerp(L,B,f))*(R+.048f+(old?.11f:.33f)*sinf(PI*f)));}
}

inline void block(Raster& g,float minx,float maxx,float offset,float y0,float base,float depth,float slopeL,float slopeR,int variant){
    // Cross-section fixed in material coordinates. Each layer is clipped by
    // inclined boundaries; a downthrown block carries its own layers with it.
    const float dz=depth*.5f;
    auto pos=[&](float u,float h,float z){float L=minx+slopeL*h,R=maxx+slopeR*h;
        const float x=offset+lerp(L,R,u);float wav=.024f*sinf(u*8.f+z*.53f)+.018f*sinf(u*23.f+z*1.7f);
        return V{x,y0+h+wav,z};};
    const V palette[]={{154,108,72},{147,136,98},{176,143,100},{101,116,112},{174,139,85},{110,104,83},{186,156,110},{106,113,101}};
    for(int i=0;i<26;i++){
        float h0=lerp(-base,0.f,i/26.f),h1=lerp(-base,0.f,(i+1)/26.f);
        for(int j=0;j<27;j++){
            float u=j/27.f,v=(j+1)/27.f;
            const V p=palette[((i*9)/5+variant)%8]; V c=p*(.73f+.30f*hash(i*17+7,j*9+variant));
            g.face(pos(u,h0,-dz),pos(v,h0,-dz),pos(v,h1,-dz),pos(u,h1,-dz),light({0,0,-1},c));
            g.face(pos(u,h0,dz),pos(v,h0,dz),pos(v,h1,dz),pos(u,h1,dz),light({0,0,1},c));
        }
        for(int j=0;j<21;j++){
            float z=depth*(j/21.f-.5f),z1=z+depth/21;
            V c=palette[((i*9)/5+variant)%8]*(.65f+.34f*hash(j+61,i+variant));
            g.face(pos(0,h0,z),pos(0,h0,z1),pos(0,h1,z1),pos(0,h1,z),light(unit({-1,slopeL,0}),c));
            g.face(pos(1,h0,z),pos(1,h0,z1),pos(1,h1,z1),pos(1,h1,z),light(unit({1,-slopeR,0}),c));
        }
    }
    g.lattice(39,29,[&](float u,float v){
        V p=pos(u,0,(v-.5f)*depth);
        p.y+=.037f*sinf(u*37.f+v*18.f)+.046f*fnoise(u*14.f+variant,v*11.f+4.f);
        V c=lerp(variant==2?V{55,78,65}:V{105,119,83},variant==2?V{132,159,130}:V{170,164,108},
                 .27f+.73f*fnoise(39*u+variant,34*v+3.f));
        return Node{p,c*(.89f+.16f*clamp(p.y+1.3f))};
    });
}

inline void fault(Studio& s,int v){
    auto& g=s.g;const float t=s.t;
    const V a=v==3?V{-1.26f,4.37f,-11.4f}:V{-2.17f,4.17f,-8.5f},b=v==3?V{.78f,4.91f,-11.5f}:V{1.28f,5.21f,-8.75f};
    g.begin(s.camera(a,b,{.15f,-.25f,.12f},v==3?36.f:43.2f),2,t);
    s.stage(.37f);
    const float d=v==0?0.f:v==1?s.at(K_RIFT_DOWN,4.05f):v==2?1.f:.31f*s.at(K_RIFT_EARLY,2.48f)+1.72f*s.at(K_RIFT_LATE,2.31f);
    const float offset=d*(v==3?.96f:.41f);const float sink=.65f*d;
    block(g,-3.34f,-1.12f,-offset,.57f,1.9f,2.6f,0,-.59f,0);
    block(g,1.04f,3.37f,offset,.48f,1.82f,2.58f,.58f,0,0);
    block(g,-1.11f,1.04f,0,.53f-sink,1.80f-sink*.39f,2.6f,-.59f,.58f,0);
    if(v==0||v==1){
        const float light0=.26f+.67f*(v==1?s.at(K_RIFT_DOWN,1.25f):s.at(K_FAULT_LIGHT,.8f));
        for(int i=0;i<2;i++){
            float sign=i?1:-1,x=(i?1.04f:-1.12f)+sign*offset,y=i?.48f:.57f;
            g.line({x,y,-1.34f},{x+(i?-.75f:.77f),y-1.30f,-1.34f},GOLD,light0,2.7f);
            g.line({x,y,-1.33f},{x,y,1.30f},MINT,light0*.61f,1.9f);
        }
    }
    if(v==2||v==3){float fill=v==2?s.at(K_RIFT_FILL,3.82f):s.at(K_RIFT_LATE,1.98f);
        const float height=lerp(.54f-sink,.265f,fill);
        if(fill>.002f){
            if(v==2){
                for(int i=0;i<8;i++){
                    float q0=clamp(fill*8.f-i);if(q0<.005f)continue;
                    V P={-1.25f-.03f*i,-.10f+i*.047f,-1.315f};
                    V c=lerp({166,127,81},{201,161,109},hash(i,991));
                    g.face(P,P+V{2.57f,0,0},P+V{2.57f,.048f*q0,0},P+V{0,.048f*q0,0},c);
                }
            }
            float W=v==2?1.51f:offset+1.095f;
            if(v==3){
                // The sea occupies the available basin, not a sheet floating
                // above a void. Layer the section dark toward the ocean floor.
                const float Z=-1.298f;
                for(int j=0;j<15;j++){
                    float b=j/15.f,h=(j+1)/15.f;
                    float y=lerp(-.94f-d*.25f,height,b),Y=lerp(-.94f-d*.25f,height,h);
                    const float w=W+(.30f*(1-b));
                    const V c=lerp({20,47,53},{72,138,143},b*b);
                    g.face({-w,y,Z},{w,y,Z},{w,Y,Z},{-w,Y,Z},c,.96f*fill);
                }
            }
            s.water(0,0,W,1.288f,height,v==2?2:0,.97f);
            if(v==2)s.specks(160,91,{.05f,.76f,-.03f},{1.11f,.68f,1.43f},GOLD,.27f);
        }
    }
    s.specks(895+v,44,{.45f,1.13f,.21f},{4.26f,.85f,2.37f},WHITE,.10f+.20f*d);
    s.mark(0,{-1.14f-offset,.61f,-1.22f});s.mark(1,{1.06f+offset,.57f,-1.25f});
}

inline void strata(Studio& s,int v){
    auto& g=s.g;
    g.begin(s.camera({-1.95f,3.28f,-8.34f},{1.44f,3.91f,-7.55f},{.06f,-.23f,.10f},40),0,s.t);
    s.stage(.51f);
    for(int i=0;i<2;i++){
        float x=i?1.76f:-1.81f;const float y=i?-.33f:.11f,z=i?.37f:.0f;
        s.slab(i?s.earth.koum:s.earth.brazil,{x,y,z},{1.48f,.95f,1.37f},18+i,.06f,0,.15f);
        if(v>=1){
            V cols=i?MINT:GOLD;
            for(int j=0;j<4;j++){
                const float h=y-.26f-j*.139f;
                if(v==2 && (j==1 || (i==0&&j==3))) {
                    V C={x+.45f,h,z-1.43f};g.dust(C,.067f,cols,.72f);g.line(C,C+V{.51f,0,0},cols,.71f,1.9f);
                }
            }
        }
        s.mark(i,{x,y-.21f,z-.5f});
    }
    s.specks(381+v,33,{.32f,.97f,.17f},{3.26f,.79f,1.79f},MINT,.07f);
}

inline void haven(Studio& s,int v){
    auto& g=s.g;g.begin(s.camera({-1.50f,4.64f,-8.25f},{1.64f,5.22f,-7.9f},{.12f,.0f,.25f},40),0,s.t);s.stage(.44f);
    const int hits[]={K_HABITAT_FIRST,K_HABITAT_NEXT,K_HABITAT_LAST};
    const int key[]={K_MORE_SITES,K_BETTER_DATES,K_BETTER_FOSSILS};
    for(int i=0;i<3;i++){
        float on=v==0?s.at(hits[i],1.06f):v==1?.84f:s.at(key[i],.8f);
        const V p={(i-1)*2.48f,.0f,(i==1?.40f:0.f)};
        const auto& G=i%2?s.earth.koum:s.earth.brazil;
        s.slab(G,p,{1.08f,.54f,.90f},76+i,.085f,0,.35f-.23f*on);
        if(v==0||v==1){
            // Each pool is confined to its own model; there are no arrows or migration track.
            if(on>.003f){
                g.lattice(76,34,[&](float u,float w){float A=u*2*PI, U=w*on;float R=.86f*U*(.85f+.12f*cosf(3*A))+U*.07f*sinf(6*A);
                    float x=R*cosf(A),z=R*.58f*sinf(A),y=.14f+.008f*sinf(11*x+18*z-s.t*2.2f);
                    float gl=.54f+.19f*sinf(11*x+18*z+s.t*2.1f)+.29f*cosf(13*z-10*x+s.t*1.1f);
                    return Node{p+V{x,y,z},lerp({37,92,89},{132,183,151},clamp(gl))};
                });
                for(int j=0;j<5;j++){
                    float a=j*1.42f+.17f, rad=on*(.78f+.10f*sinf(j*2.f));V c=p+V{rad*cosf(a),.35f,rad*.64f*sinf(a)};
                    g.dust(c,.015f,MINT,on*.51f);
                }
            }
        }else if(on>.008f){
            if(i==0){for(int j=0;j<3;j++){
                auto P=p+V{-.51f+.54f*j,.15f+on*.27f,.07f+.29f*sinf(j)};
                pebble(g,P,{.19f,.12f,.22f},GOLD*(.83f+.10f*j),418+j,9,16,.19f);}}
            else if(i==1){for(int j=0;j<6;j++){
                float y=.17f+j*.081f*on; V m=p+V{.0f,y,.1f};pebble(g,m,{.25f,.056f,.26f},j%2?MINT*.8f:GOLD*.72f,j+992,5,19,.036f);}}
            else{for(int j=0;j<5;j++){
                float d=j/4.f;V m=p+V{-.54f+1.17f*d,.11f+on*.21f,.11f+sinf(d*PI)*.13f};pebble(g,m,{.092f,.059f,.19f*(1-.64f*d)},WHITE*.75f,547+j,7,13,.085f,d*.53f);}}
        }
        s.mark(i,p+V{0,0,-.11f});
    }
    s.specks(833,35,{0,.89f,-.23f},{4.1f,.73f,2.33f},MINT,.17f);
}

inline void fish(Studio& s,int v){
    auto& g=s.g;const float t=s.t,q=s.q;
    if(v){
        g.begin(s.camera({-.94f,4.54f,-7.7f},{.94f,4.23f,-7.63f},{.19f,-.05f,.1f},41),0,t);s.stage(.48f);
        for(int i=0;i<2;i++){
            const V C={i?1.76f:-1.93f,.14f-.08f*i,.08f+.33f*i};
            s.slab(i?s.pressure:s.ripples,C,{1.51f,.67f,1.14f},144+i,.17f,.87f,.24f);
            const V pigment=i?V{164,180,143}:V{175,142,101};
            // Fragment groupings, not invented identifiable specimen photographs.
            for(int j=0;j<12;j++){
                float u=j/11.f,x=-1.14f+2.19f*u,z=.23f*sinf(u*4.59f);
                float height=.085f+s.ripples.height(x,z)*.56f;V p=C+V{x,height,z};
                float f0=hash(j,460+i);pebble(g,p,{.074f+.04f*f0,.035f,.092f},pigment,i*331+j,5,11,.23f);
                if((j+i)%3!=1){V p0=p+V{-.11f,.02f,.28f*(1-u)};g.line(p,p0,pigment,.97f,2.1f);g.line(p,p0+V{.04f,0,-.40f*(1-u)},pigment,.89f,2.1f);}
            }
            s.mark(i,C);
        }
        s.specks(338,43,{.0f,.76f,.30f},{4.12f,.87f,2.11f},MINT,.138f);return;
    }
    g.begin(s.camera({-.40f,1.08f,-8.83f},{.31f,.75f,-7.52f},{-.10f,.0f,.1f},40.2f,-.018f),1,t);
    auto spine=[&](float x){return V{x+.67f-.53f*q,.087f*sinf(t*1.3f)+.13f*sinf(t*1.58f-x*.81f)*clamp((x+.98f)/3.6f),.221f*sq(clamp((x+.96f)/3.51f))*sinf(t*3.5f-x*1.64f)};};
    auto body=[&](float u,float v){
        const float x=lerp(-2.48f,2.16f,u),A=2*PI*v;
        float profile=.06f+.67f*powf(sinf(PI*clamp(u)),.71f)*(1.30f-.82f*u);
        float head=.37f*ramp(0,.063f,u)*(1-ramp(.20f,.47f,u));profile=std::max(head,profile);
        float Y=profile*(.91f+.09f*cosf(A))*cosf(A),Z=profile*.64f*sinf(A);
        return spine(x)+V{0,Y,Z};
    };
    g.lattice(142,96,[&](float u,float v){
        V P=body(u,v), n=unit(cross(body(u+.0001f,v)-body(u-.0001f,v),body(u,v+.0001f)-body(u,v-.0001f)));
        if(dot(n,P-spine(lerp(-2.48f,2.16f,u)))<0) n=n*(-1);
        float a=cosf(2*PI*v),seq0=u*78.f+.34f*sinf(v*58.f*PI),seq1=v*61.f+u*23.f;
        float scale=.83f+.105f*cosf(6.283f*seq0)+.095f*sinf(6.283f*seq1);
        V col=lerp({97,120,94},{210,196,132},clamp(.40f-.40f*a+.15f*sinf(v*7.f*PI)));
        V rgb=light(n,col,.92f*scale)+(V{73,118,112}*(.24f+.40f*clamp(-dot(n,g.cam.f))));
        return Node{P,rgb};
    });
    const auto fin=[&](V root,V edge,float width,float tip,float seed){
        const V d=edge-root,normal=unit(cross(d,{.01f,0,1}));
        g.lattice(34,21,[&](float u,float v){
            const float s0=(v-.5f)*2.f,F=powf(sinf(u*PI),.74f),rib=.19f*cosf(v*62.f+.32f*sinf(69.f*u));
            V p=root+d*u+V{(F*width+sinf(u*1.42f)*tip)*s0,.059f*F*sinf(PI*v),F*.12f*cosf(t*2.1f+seed+v*1.9f)};
            V c=light(normal,lerp({59,89,72},{205,188,131},clamp(.46f+rib+.34f*u)),.68f+.41f*sinf(PI*v));
            return Node{p,c+V{20,32,30}*(.58f+.42f*u)};
        });
    };
    for(float dir:{-1.f,1.f}){
        fin(spine(-1.02f)+V{0,-.13f,dir*.399f},spine(-.13f)+V{0,-.78f,dir*(.62f+.14f*sinf(t*3.f+dir))},.29f,.082f,dir);
        fin(spine(.56f)+V{0,-.38f,dir*.239f},spine(1.13f)+V{0,-.66f,dir*(.45f+.08f*sinf(t*3.7f+dir))},.235f,.041f,dir);
    }
    fin(spine(-.63f)+V{0,.38f,0},spine(-.11f)+V{0,1.03f,.072f},.53f,.029f,.19f);
    fin(spine(.85f)+V{0,.255f,0},spine(1.27f)+V{0,.76f,.063f},.31f,.040f,.85f);
    fin(spine(1.15f)+V{0,-.223f,.052f},spine(1.56f)+V{0,-.67f,.083f},.27f,.029f,.5f);
    // Distinct upper, lower and smaller trailing central lobe.
    fin(spine(1.965f)+V{0,.035f,0},spine(2.94f)+V{0,.76f,.062f},.555f,.115f,.44f);
    fin(spine(1.965f)+V{0,-.035f,0},spine(2.90f)+V{0,-.69f,-.047f},.547f,.112f,.51f);
    fin(spine(2.05f),spine(3.23f)+V{0,.008f,.057f},.192f,.039f,.64f);
    pebble(g,spine(2.05f),{.25f,.145f,.097f},{103,132,98},221,12,20,.013f);
    for(float side:{-1.f,1.f}){
        const V p=spine(-2.075f)+V{0,.205f,side*.295f};
        pebble(g,p,{.114f,.096f,.063f},{164,145,77},812,10,21,.029f);
        pebble(g,p+V{-.007f,.0f,side*.051f},{.064f,.059f,.028f},{17,31,30},844,9,17,.017f);
        g.dust(p+V{-.021f,.027f,side*.076f},.016f,WHITE,.83f);
        const V gill=spine(-1.42f)+V{0,.33f,side*.251f};
        for(int j=1;j<=7;j++){float a=j/7.f,b=(j-1)/7.f;
            auto P=[&](float a){return gill+V{.117f*sinf(a*PI),-.51f*a,side*.22f*sinf(a*PI)};};
            g.line(P(b),P(a),{53,79,64},.7f,1.f);}
        V a0=spine(-2.41f)+V{0,-.084f,side*.124f};
        for(int j=1;j<=12;j++){
            float u=j/12.f;V p1=spine(-2.41f+.59f*u)+V{0,-.085f-.047f*sinf(u*PI),side*(.125f+.26f*u)};
            g.line(a0,p1,{34,57,43},.83f,1.45f);a0=p1;
        }
    }
    s.specks(313,149,{0,.1f,.63f},{6.9f,3.19f,3.05f},{143,203,192},.33f);
}
}
