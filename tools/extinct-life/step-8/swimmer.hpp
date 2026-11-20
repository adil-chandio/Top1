#pragma once
#include "look.hpp"
namespace cinema {
inline void swimmer(CutSet& s){
    auto& g=s.g;const float t=s.sec();
    const float c=smoother(t/8.5f),face=smoother(t/4.81f);
    const V eye=spline({-4.27f,1.01f,-4.67f},{-3.82f,2.18f,-6.19f},{-.12f,.68f,-7.05f},{1.82f,1.64f,-6.77f},c);
    s.view(eye,{.16f,.14f,.45f},36.7f,1,-.016f);
    const float turn=.31f-.50f*face;
    const V forward={cosf(turn),0,sinf(turn)},right={-forward.z,0,forward.x};
    const V C={lerp(1.44f,-1.36f,c),.18f+.14f*sinf(t*.98f),.95f-.49f*c};
    const float pool=3.45f*t+.24f*sinf(t*1.74f);
    auto W=[&](V v){return C+forward*v.x+V{0,v.y,0}+right*v.z;};
    auto spine=[&](float x){
        float caudal=sq(clamp((x+.90f)/3.20f));
        return V{x,.048f*sinf(pool*.51f)+.067f*caudal*sinf(pool-x*1.24f),(.042f+.28f*caudal)*sinf(pool-x*1.38f)};
    };
    auto surface=[&](float u,float v){
        float x=lerp(-2.05f,1.94f,u),a=2*PI*v;
        float body=std::max(0.f,sinf(PI*clamp(u)));
        float radius=.016f+.533f*sqrtf(body)*(.98f+.35f*(1-u))*(1-.72f*ramp(.67f,1.f,u));
        float head=ramp(0.f,.11f,u)*(1-ramp(.19f,.37f,u));radius+=head*.050f;
        float cheek=head*.04f*sq(sinf(a));
        return W(spine(x)+V{0,radius*cosf(a)-.032f*head,(.724f*radius+cheek)*sinf(a)});
    };
    const V key=unit({-.30f,.88f,-.46f});
    const V ink{38,62,60},silica{106,123,109},belly{162,168,127};
    g.lattice(154,100,[&](float u,float v){
        V P=surface(u,v),N=unit(cross(surface(u+.0017f,v)-surface(u-.0017f,v),surface(u,v+.0033f)-surface(u,v-.0033f)));
        float x=lerp(-2.05f,1.94f,u);if(dot(N,P-W(spine(x)))<0)N=N*(-1);
        float az=2*PI*v,angle=az*14.f+u*3.f;
        float streak=cosf(u*260.f+1.19f*cosf(angle*2.f)),sc=.50f+.29f*streak+.21f*cosf(angle*2.f-.77f*streak);
        float grain=.71f+.29f*ramp(.07f,.78f,sc);
        float dorsal=ramp(-.45f,.93f,-cosf(az)),bar=.80f+.20f*fnoise(u*21.f,v*18.f+3.19f);
        float light0=clamp(dot(N,key)),rim=clamp(dot(N,unit({.18f,.27f,.93f}))),shine=clamp(dot(reflect(unit(P-g.cam.p),N),key));shine*=shine;shine*=shine;float sheen=shine*shine;
        V base=lerp(ink,lerp(silica,belly,.66f*dorsal),.26f+.65f*dorsal+.08f*sc);
        float caust=(.84f+.17f*powf(.50f+.50f*cosf(P.x*17.f+P.y*15.4f+P.z*21.2f+3.3f*s.t),5.f));
        V color=base*grain*bar*caust*(.52f+.70f*light0)+V{43,105,101}*(.57f*rim+.50f*sheen)+V{49,63,48}*(sheen*sheen*.49f);
        return Node{P,color};
    });
    auto sail=[&](V a,V b,V w,float fin,float fphase){
        V normal=unit(cross(b-a,w));
        const float sun=.57f+.43f*fabsf(dot(normal,key));
        g.lattice(33,20,[&](float u,float v){
            const float h=powf(std::max(0.f,sinf(PI*u)),.81f),q0=2*v-1;
            V p=lerp(a,b,u)+w*(q0*h)+V{0,.061f*h*sinf(q0*2.f+u*4.f),fin*h*sinf(pool+fphase-u*2.3f)};
            V col=lerp(V{46,76,75},V{133,151,115},.41f+.13f*cosf(v*61.f+u*1.42f)+.38f*u)*sun;
            return Node{W(p),col};
        });
    };
    for(float side:{-1.f,1.f}){
        float phase=pool*.72f+side*.98f;auto bend=sinf(phase);
        sail(spine(-.90f)+V{0,-.20f,side*.324f},spine(-.04f)+V{.16f,-.52f+.105f*bend,side*(.66f+.18f*bend)},{.34f,.104f,.091f*side},.092f,phase);
        sail(spine(.54f)+V{0,-.30f,side*.244f},spine(1.09f)+V{.06f,-.67f+.073f*bend,side*.54f},{.28f,.052f,.079f*side},.087f,phase+.54f);
        const V p=spine(-1.64f)+V{0,.19f,side*.323f};
        pebble(g,W(p),{.115f,.098f,.091f},{96,102,71},17,7,15,.015f);
        pebble(g,W(p+V{-.021f,.013f,side*.067f}),{.074f,.068f,.039f},{130,129,81},19,9,14,.009f);
        pebble(g,W(p+V{-.038f,.008f,side*.094f}),{.048f,.051f,.026f},{13,27,31},21,7,10,.008f);
        g.dust(W(p+V{-.05f,.034f,.112f*side}),.016f,PAPER,.91f);
        for(int i=0;i<20;i++){
            auto L=[&](float v){return W(spine(-1.02f)+V{.153f*sinf(v*PI),.35f-.585f*v,side*(.326f+.161f*sinf(v*PI))});};
            g.line(L(i*.05f),L((i+1)*.05f),{27,56,57},.75f,1.35f);
        }
    }
    sail(spine(-.49f)+V{0,.51f,0},spine(.15f)+V{0,1.04f,.042f},{.44f,.05f,.02f},.051f,.44f);
    sail(spine(.70f)+V{0,.272f,.02f},spine(1.35f)+V{0,.713f,.026f},{.30f,.038f,0},.087f,1.17f);
    sail(spine(.91f)+V{0,-.24f,0},spine(1.42f)+V{0,-.59f,0},{.28f,.048f,0},.082f,1.64f);
    const V tail=spine(1.71f),last=spine(2.63f);
    sail(tail,last+V{.29f,.71f,.03f},{.420f,.118f,0},.117f,.81f);
    sail(tail,last+V{.28f,-.61f,.011f},{.44f,.12f,.02f},.120f,.65f);
    sail(tail+V{.08f,.01f,.0f},last+V{.53f,.031f,.02f},{.21f,.151f,0},.096f,1.17f);
    s.specks(478,110,{.23f,-.11f,.58f},{6.1f,2.73f,5.4f},{104,154,143},.29f);
    s.mark(0,W(spine(-1.65f)+V{0,.19f,-.49f}));
}
}
