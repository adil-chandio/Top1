#pragma once
#include "look.hpp"
namespace cinema {
// The microscope stage is a diagram made of separate grains and small
// contacts, not a reconstruction of any particular thin section.
inline void microscope(CutSet& s){
    auto& g=s.g;const int k=s.shot;const bool cement=k==30,sousa=k==36;
    const float u=s.q;
    const float reveal=cement?s.at(K_CEMENT,.68f):sousa?s.at(K_SOUSA_FIBRES,.74f):s.at(K_MAT,.76f);
    const float tilt=s.here(0.f,cement?11.65f:sousa?5.93f:8.5f);
    V p=cement?spline({-.75f,1.42f,-5.33f},{-.41f,1.09f,-4.72f},{.19f,1.48f,-4.28f},{.51f,1.67f,-3.97f},u):
        spline({-.72f,1.36f,-4.81f},{-.51f,1.52f,-4.63f},{.07f,1.83f,-4.36f},{.35f,2.08f,-4.13f},u);
    s.view(p,{.04f,-.04f,.24f},39.0f,cement?2:1,.017f*(1-2*tilt));
    const V light0=unit(cement?V{-.62f,.57f,-.73f}:V{.48f,.64f,-.66f});
    auto P=[](int i,int j){
        float delta=(j%2?.186f:-.04f);
        return V{(i-4.5f)*.532f+delta+.088f*(hash(i,j+310)-.5f),-.19f+.051f*(hash(i,j+445)-.5f),
             -.50f+j*.535f+.118f*(hash(i,j+801)-.5f)};
    };
    for(int j=4;j>=0;j--)for(int i=0;i<10;i++){
        const V C=P(i,j);const float e=hash(i,j+311),seed=i*.631f+j*.872f;
        V size={.258f+.085f*e,.176f+.107f*hash(i,j+902),.264f+.065f*hash(i,j+431)};
        const V col=lerp({.129f,.181f,.162f},sousa?V{.468f,.292f,.127f}:V{.437f,.324f,.183f},ramp(.23f,.80f,e));
        auto surface=[&](float az,float el){
            V d={cosf(el)*cosf(az),sinf(el),cosf(el)*sinf(az)};
            float R0=.992f+.087f*sinf(az*5.f+el*3.f+seed)+.081f*cosf(az*7.0f-el*4.7f-seed)+.068f*sinf(el*8.2f+1.19f*cosf(az*2.1f)+seed);
            // Bent crystal faces and broken edges rather than identical spheres.
            const float max_axis=std::max({fabsf(d.x)*.97f,fabsf(d.y)*.87f,fabsf(d.z)});
            R0=std::min(R0,(.759f+.037f*e)/std::max(.51f,max_axis));
            return C+d*size*R0;
        };
        g.lattice(22,15,[&](float u0,float v){
            const float a=(u0*2*PI)+seed,z=(v-.5f)*PI;
            V x=surface(a,z),N=unit(cross(surface(a+.002f,z)-surface(a-.002f,z),surface(a,z+.002f)-surface(a,z-.002f)));
            if(dot(x-C,N)<0)N=N*(-1);
            const float b=fnoise(x.x*51.90f+x.y*21.7f,x.z*53.6f+x.y*37.0f);
            const float band=.68f+.35f*b+.105f*sinf(x.y*225.f+x.x*98.f+7.f*b);
            const float D=clamp(dot(N,light0)),edge=1-clamp(dot(N,unit(g.cam.p-x)));
            V c=col*band*(.167f+.94f*D)*(.69f+.31f*clamp(.54f+N.y));
            c+=V{.28f,.33f,.29f}*.21f*edge*edge*(.45f+.55f*D);
            const float sp=clamp(dot(reflect(unit(x-g.cam.p),N),light0));float k0=sp*sp;k0*=k0;k0*=k0;
            c+=V{.78f,.73f,.64f}*(.18f*k0*k0);
            uint8_t rgb[3];camera_response.put(rgb,c);
            return Node{x,{float(rgb[0]),float(rgb[1]),float(rgb[2])}};
        });
    }
    if(reveal>.001f){
        for(int j=0;j<4;j++)for(int i=1;i<8;i++){
            const V A=P(i,j),B=P(i+1,j);const float seed=hash(i,j+170),phi=hash(i,j+163);
            const float a=smooth(reveal*1.66f-seed*.65f);
            if(cement){
                if(seed>.74f&&i!=4)continue;
                V p0=lerp(A,B,.51f)+V{0,.044f+.06f*phi,.011f};
                // Grain contact is a bridge from each interior to the other.
                pebble(g,p0,{.094f*a+.003f,.071f*a,.103f*a},{190,156,102},321+i+j*44,8,14,.14f,phi*.13f);
                if(i==4&&j==0)s.mark(0,p0+V{0,.029f,-.06f});
            }else{
                for(int n=0;n<5;n++){
                    float d=.011f+.005f*n,phase=phi*2.f+n*.821f;
                    const V C=V{0,.217f+.014f*n,-.104f+.042f*n};
                    auto T=[&](float x){return lerp(A,B,x)+C+V{0,.038f*sinf(x*PI+phase)+.013f*sinf(x*11.f+phase),d*cosf(x*9.f+phase)};};
                    V p0=T(0);
                    for(int m=1;m<=12;m++){
                        V q=T(a*m/12);g.line(p0,q,sousa?V{163,156,90}:V{105,186,158},a*.56f,1.23f);p0=q;
                    }
                    if(i==4&&j==0&&n==2)s.mark(0,T(.58f)+V{0,.009f,-.04f});
                }
            }
        }
    }
    // Fine particles have a broad focus range and low opacity; no uniform grid.
    s.specks(884+k,64,{.06f,.33f,1.0f},{3.22f,.61f,2.4f},cement?V{147,143,126}:V{119,166,158},.049f);
}
}
