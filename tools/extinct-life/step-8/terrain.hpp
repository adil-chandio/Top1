#pragma once
#include "look.hpp"
namespace cinema {
struct SunRoom {V sun,zenith,air,dust;float extinction,depth;};
inline SunRoom daylight(int story){
    if(story==0)return {unit({.63f,.29f,.80f}),{.076f,.202f,.351f},{.54f,.38f,.242f},{.26f,.174f,.103f},.021f,.37f};
    if(story==1)return {unit({-.74f,.47f,.69f}),{.092f,.240f,.430f},{.42f,.552f,.60f},{.192f,.252f,.25f},.018f,.20f};
    if(story==2)return {unit({-.52f,.28f,.94f}),{.120f,.245f,.39f},{.67f,.532f,.415f},{.30f,.227f,.164f},.022f,.21f};
    return {unit({-.71f,.48f,.78f}),{.077f,.233f,.389f},{.39f,.534f,.599f},{.19f,.245f,.256f},.016f,.30f};
}
inline V analytic_sky(V d,const SunRoom& s,float t,bool cloud=true){
    const float h=ramp(-.08f,.57f,d.y),e=clamp(dot(d,s.sun));float a=e*e*e;
    V col=lerp(s.air,s.zenith,h)+V{.47f,.253f,.123f}*(a*a*.19f+a*a*a*a*.18f);
    if(cloud&&d.y>-.08f){
        const float y=3.8f/(.29f+std::max(.03f,d.y));
        float x=(d.x+.24f*d.z)*y+.0042f*t,z=d.z*y*.77f+6.3f;
        const float n=fnoise(x*.58f,z*.4f);
        float m=.68f*fnoise(x+1.24f*n,z)+.23f*fnoise(x*2.15f,z*2.3f)+.09f*fnoise(x*4.7f,z*4.3f+6.f);
        float w=ramp(.47f,.79f,m)*ramp(-.08f,.09f,d.y);
        col=lerp(col,lerp(s.dust,s.air+V{.25f,.236f,.189f}*(.36f+.61f*e),ramp(.35f,.85f,m)),w*.76f);
    }
    return col;
}

inline const Texture& material(CutSet& s,const Grid& b,int profile=0){
    if(auto i=s.tiles.find(&b);i!=s.tiles.end())return i->second;
    Texture a; a.w=std::min(1320,b.w);a.h=std::min(1320,b.h);a.rgb.resize(size_t(a.w)*a.h);
    const bool wide=b.span>55;
    const bool warm=(&b==&s.earth.brazil||&b==&s.rim||&b==&s.dried);
    const V key=wide?daylight(profile).sun:unit(warm?V{-.67f,.49f,-.47f}:V{.51f,.553f,-.653f});
    const V kelvin=wide?(profile==0?V{1.42f,1.04f,.77f}:profile==2?V{1.36f,1.11f,.89f}:V{1.29f,1.18f,1.01f}):
        (warm?V{1.31f,1.13f,.99f}:V{1.12f,1.18f,1.11f});
    #pragma omp parallel for schedule(static)
    for(int j=0;j<a.h;j++)for(int i=0;i<a.w;i++){
        float u=(i+.5f)/a.w,v=(j+.5f)/a.h;
        const Sample p=Grid::all(b.map(u,v,false));const float x=(u-.5f)*b.span,z=(v-.5f)*b.span;
        const V n=unit({-p.gx,1,-p.gy});
        float f0=.64f*fnoise(x*(wide?1.89f:23.6f),z*(wide?2.33f:29.5f))+.36f*fnoise(x*(wide?5.1f:51.8f)+7,z*(wide?6.7f:56.4f)+4);
        const float seam=.5f+.5f*sinf(x*.62f+z*.91f+p.h*(wide?13.0f:146.f)+f0*2.63f);
        const float micro=wide?.80f+.32f*f0:.77f+.34f*f0+.09f*seam;
        const float edge=clamp(dot(n,key));
        const float l0=wide?(profile==1?.59f:.61f):.65f;
        float oc=(1.f-(wide?.24f:.46f)*p.m)*(.76f+.24f*std::max(0.f,n.y));
        V al=p.rgb();float g=luminance(al);
        al=lerp(al,V{g*1.10f,g*.97f,g*.79f},wide?.28f:warm?.18f:.43f);
        if(wide){
            const float veg=ramp(.48f,.71f,.59f*fnoise(x*.29f+6,z*.41f)+.41f*f0)*ramp(.06f,.62f,p.h)*(1-ramp(3.5f,4.9f,p.h));
            al=lerp(al,V{.069f,.101f,.056f}*(.72f+.63f*f0),veg*.86f);
            const float on=ramp(.018f,.70f,p.h);
            al=al*(.63f+.37f*on)+V{.038f,.046f,.037f}*(1-on);
            constexpr float horizons[]={.58f,1.56f,2.78f};
            const float escarpment=ramp(.08f,.45f,1-n.y);
            for(float h:horizons){float l=p.h-h-.20f*sinf(x*.21f+z*.32f);al=al*(1-.21f*escarpment/(1+sq(l/.091f)));}
        }
        V env=wide?V{.263f,.337f,.417f}:V{.24f,.264f,.31f};
        V linear=al*(env*oc+kelvin*(edge*l0*oc))*micro;
        const float rim=clamp(p.k)*(.42f+.58f*edge);
        linear+=(warm?V{.035f,.022f,.009f}:V{.025f,.031f,.028f})*rim;
        if(!wide)linear+=V{.019f,.020f,.027f}*(1-n.y)*(.71f+.29f*f0);
        a.rgb[j*a.w+i]=camera_response.pack(linear);
    }
    return s.tiles.emplace(&b,std::move(a)).first->second;
}

inline void macro_ground(CutSet& s,const Grid& b,float restore=0,float depth=1.26f,float extent=6.8f){
    auto& g=s.g;const Texture& col=material(s,b);
    g.lattice(154,138,[&](float u,float v){
        auto xy=[&](float t){float q=2*t-1;return extent*(.51f*q+.49f*q*q*q);};
        const float x=xy(u),z=xy(v);const auto p=Grid::all(b.local(x,z));
        const float y=depth*b.height(x,z,restore);
        float k=(.89f+.12f/(1+.67f*(sq(x-.17f)+sq(z-.40f))))*(1-.15f*p.m*(1-restore));
        if(restore>.005f)k=lerp(k,std::min(1.18f,k+.34f*p.m),restore);
        return Node{{x,y,z},{k,k,k},Grid::mirror(x/b.span+.5f),Grid::mirror(z/b.span+.5f)};
    },&col);
}

inline void shallow(CutSet& s,const Grid& b,float level,const SunRoom& room,bool wide,float restore=0,float bank=-100,float intensity=1){
    if(intensity<.0005f)return;
    auto& g=s.g;const Camera cam=g.cam;
    const auto original=g.rgb;
    const float t=s.t;
    #pragma omp parallel for schedule(static)
    for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
        const int i=y*g.w+x;float u=(x+.5f)/g.w,v=(y+.5f)/g.h;
        V d=cam.f+cam.r*((2*u-1)*cam.focal*cam.aspect)+cam.u*((1-2*v)*cam.focal);
        if(d.y>=-.009f)continue;
        const float q=(level-cam.p.y)/d.y;
        if(q<.06f||1.f/q<=g.z[i])continue;
        V p=cam.p+d*q;
        if(!b.inside(p.x,p.z))continue;
        float height=b.height(p.x,p.z,restore)*(wide?1.f:1.26f);
        if(p.z<=bank+.17f*sinf(p.x*(wide?.3f:5.2f)+t*.52f)||height>level)continue;
        const float depth=level-height;
        float a0=wide?p.x:p.x*5.9f,b0=wide?p.z:p.z*6.8f;
        const float ph=2.25f*sinf(a0*.82f+b0*.58f+.77f*t)+1.80f*cosf(a0*.43f-b0*.61f);
        const float P=sinf(2.27f*a0+5.62f*b0-2.44f*t+ph),Q=cosf(5.91f*a0-4.65f*b0+2.86f*t-ph*.74f);
        const float R0=sinf(a0*17.3f+b0*13.2f-4.72f*t+P*1.72f+Q*2.6f);
        const float H=wide?1/(1+.016f*q):.79f;
        const float chop=H/(1+.021f*q);
        const float fan=sinf(11.61f*a0-19.17f*b0-3.62f*t+2.4f*Q);
        const V n=unit({(.017f*P+.026f*Q)*H+(.018f*R0+.009f*fan)*chop,1,(.025f*P-.016f*Q)*H+(.021f*R0-.014f*fan)*chop});
        const V ray=unit(d),r=reflect(ray,n);
        const float c=clamp(-dot(ray,n));float fr=1-c,fr2=fr*fr;
        const float F=.021f+.979f*fr2*fr2*fr;
        const int ax=int(clamp(x+(n.x-.018f*P)*g.w*(wide?.031f:.055f),0,g.w-1.f)),ay=int(clamp(y+n.z*g.h*.061f,0,g.h-1.f));
        const uint8_t* src=&original[(ay*g.w+ax)*3];
        const V sub={sq(src[0]/255.f),sq(src[1]/255.f),sq(src[2]/255.f)};
        const float path=depth/std::max(.19f,c),a=1/(1+(wide?3.1f:6.9f)*path);
        const V medium=wide?V{.026f,.099f,.101f}:V{.052f,.084f,.073f};
        V transmission=sub*V{a*a,a,a*(.72f+.28f*a)}+medium*(1-a);
        const float fx=clamp(dot(r,room.sun));float d0=fx*fx;d0*=d0;float d1=d0*d0;d1*=d1;
        const float gl=d1*d1*(.25f+.17f*P+.11f*R0);
        V reflected=analytic_sky(r,room,t,false);
        if(wide){
            V test=p+r*2.60f;
            if(b.inside(test.x,test.z))reflected=lerp(reflected,room.dust*.65f,ramp(-.12f,.51f,b.height(test.x,test.z)-test.y)*.80f);
        }
        const float lace=(1-ramp(.018f,wide?.24f:.080f,depth))*ramp(.78f,1.31f,P*.48f+Q*.58f+.22f*R0);
        V water=lerp(transmission,reflected,F)+V{.91f,.72f,.51f}*(gl*.83f+F*d1*.16f)+V{.225f,.245f,.197f}*(.61f*lace);
        water+=V{.09f,.11f,.096f}*(.11f+.08f*P+.047f*Q+.042f*R0)*(1-ramp(.09f,.60f,depth));
        if(wide)water=lerp(water,room.air*.78f,ramp(14.f,72.f,q)*.28f);
        auto* out=&g.rgb[i*3]; uint8_t px[3];camera_response.put(px,water);
        const float mix=intensity*ramp(-.003f,wide?.061f:.019f,depth);
        for(int channel=0;channel<3;channel++)out[channel]=Raster::byte(lerp(out[channel],px[channel],mix));
        g.z[i]=lerp(g.z[i],1/q,mix);
    }
}

inline void plants(CutSet& s,const Grid& b,int story){
    auto& g=s.g;
    for(int j=0;j<960;j++){
        float x=-34.f+68.f*hash(j,18),z=-31+66.f*hash(j,981);const auto p=Grid::all(b.local(x,z));
        if(p.h<.12f||p.h>3.5f||fabsf(p.gx)+fabsf(p.gy)>.92f||fnoise(x*.62f,z*.53f)<.40f)continue;
        V C={x,p.h-.005f,z};V screen=g.cam.project(C);
        if(screen.z<.64f||screen.z>46.f||screen.x<-.10f||screen.x>1.10f||screen.y>1.14f||screen.y<-.08f)continue;
        float len=.15f+.63f*sq(hash(j,51));
        const V base=story==0||story==2?V{76,85,48}:V{62,84,55},tip=base+V{47,44,19};
        const float swing=.050f*sinf(s.t*1.83f+z*.62f+x*.17f);
        for(int a=0;a<5;a++){
            float ang=2*PI*(a/5.f+.23f*hash(j,31));V d={cosf(ang),0,sinf(ang)}, n={-d.z,0,d.x};
            auto p0=[&](float f){return C+d*(len*f*.82f)+V{swing*f*f,len*(f*(2.13f-1.30f*f)),0.f};};
            auto A=p0(0);
            for(int k=1;k<5;k++){
                float f=k/4.f; auto B=p0(f);
                g.line(A,B,lerp(base,tip,f*.71f),.84f,1.3f);
                if(screen.z<23.f)for(float dir:{-1.f,1.f}){
                    const float q=len*.19f*(1-.83f*f)*dir;
                    V Y=A+(B-A)*.51f, Z=Y+n*q+(B-A)*.65f;
                    g.tri(g.project({A,base}),g.project({Z,lerp(base,tip,.47f+.29f*f)}),g.project({B,tip}));
                }
                A=B;
            }
        }
    }
}

inline void valley_view(CutSet& s,int story,V eye,V aim,float lens){
    auto& g=s.g;const auto room=daylight(story);const auto& b=(story==0||story==2)?s.earth.flood:s.earth.river;
    const Texture& cols=material(s,b,story);Camera cam(eye,aim,lens,g.w/float(g.h),.006f*cosf(s.q*PI));g.cam=cam;
    #pragma omp parallel for schedule(static)
    for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
        const V d=cam.ray((x+.5f)/g.w,(y+.5f)/g.h);
        V col=analytic_sky(d,room,s.t);
        const float q=d.x/(std::max(.18f,d.z));
        // Distant topography, behind the ray's nearer 3D terrain. Two
        // different smoothness scales convey valley depth without a flat card.
        const float horizon=.017f+.070f*fnoise(q*4.1f+.18f*story,1.12f)+.018f*fnoise(q*19.8f+12.7f,51.1f);
        const float band=1-ramp(horizon-.004f,horizon+.004f,d.y);
        if(d.z>.16f)col=lerp(col,room.air*.43f+room.dust*.44f,band*.74f);
        const int i=y*g.w+x;g.z[i]=0;camera_response.put(&g.rgb[3*i],col);
    }
    g.lattice(192,191,[&](float u,float v){
        float x=lerp(-47.95f,47.95f,u),z=lerp(std::max(-47.9f,eye.z-1.8f),47.9f,v);
        float h=b.height(x,z);return Node{{x,h,z},{1,1,1},x/b.span+.5f,z/b.span+.5f};
    },&cols);
    shallow(s,b,.002f,room,true);
    plants(s,b,story);
    #pragma omp parallel for schedule(static)
    for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
        const int i=y*g.w+x;if(g.z[i]<=.001f)continue;
        const float z=1.f/g.z[i];
        const float fog=1.f-1.f/(1.f+std::max(0.f,z-5.f)*room.extinction);
        const float v=(y+.5f)/g.h,w=(x+.5f)/g.w;
        const float mist=fog*(.50f+.36f*ramp(.65f,.22f,v))+.13f*ramp(20.f,62.f,z)*room.depth;
        uint8_t C[3];camera_response.put(C,room.air*(.66f+.12f*w));
        for(int c=0;c<3;c++)g.rgb[3*i+c]=Raster::byte(lerp(g.rgb[3*i+c],C[c],mist));
    }
}
}
