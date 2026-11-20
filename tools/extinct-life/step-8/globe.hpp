#pragma once
#include "look.hpp"
namespace cinema {
// Project the two sourced terrain fields onto the same sphere. The hidden
// hemisphere remains hidden, and pins/length line follow the same camera.
inline bool mapshot(int k,int f){
    return k==2||k==3||k==5||k==34||k==46||k==48||k==51||k==53||k==59||k==61||
           (k==56&&f>=TAKES[k].a+133)||(k==58&&f<K_BETTER_DATES);
}
struct Orbit {float lat,lon,range,lens,roll,ax,ay;};
inline Orbit globe_orbit(const CutSet& s){
    const int k=s.shot;const float u=s.q,enter=smoother(s.sec()/3.1f);
    if(k==2)return {lerp(13.8f,5.2f,enter),lerp(-29.0f,-15.6f,enter),lerp(18.6f,17.5f,enter),40.6f,lerp(.135f,.05f,enter),.53f,.525f};
    if(k==3){
        float p=smoother(s.sec()/7.8f);return {lerp(5.2f,4.8f,p),lerp(-15.6f,.34f,p),lerp(17.5f,17.1f,p),40.6f,lerp(.05f,-.061f,p),.53f,.525f};
    }
    if(k==5||k==34){
        const bool bra=k==34;const float move=smoother(s.sec()/(bra?4.32f:5.17f));
        float lat=lerp(bra?7.9f:8.4f,bra?-4.7f:11.84f,move);
        float lon=lerp(bra?-18.0f:-12.9f,bra?-40.0f:15.8f,move);
        return {lat,lon,lerp(17.9f,9.54f,move),lerp(39.6f,39.0f,move),lerp(.045f,bra?-.135f:.135f,move),.57f,.55f};
    }
    if(k==61)return {lerp(8.5f,5.2f,u),lerp(-23.1f,-15.6f,u),lerp(18.1f,17.5f,u),40.6f,lerp(.084f,.05f,u),.53f,.525f};
    const float a=k==46?-6.f:k==48?8.0f:k==51?-9.f:k==53?-5.f:k==59?3.f:2.0f;
    return {lerp(k==46?15.3f:7.3f,-1.6f,u),a+lerp(-3.1f,3.1f,u),lerp(k==53?15.75f:18.35f,k==53?15.3f:16.91f,u),40.0f,
        lerp(.078f,-.029f,u),.54f,.545f};
}

struct GlobeStudio {
    // Cube map stores field samples, not pre-rendered pixels. It avoids a
    // longitude seam and repeated geodetic trig on every ray of every frame.
    static constexpr int Side=800;
    struct Cell{float h,r,g,b,dx,dy,k,m;};
    struct Pack {
        std::array<std::vector<Cell>,6> a;
        static V direction(int side,float u,float v){
            switch(side){case 0:return unit({1,v,u});case 1:return unit({-1,v,u});
                case 2:return unit({u,1,v});case 3:return unit({u,-1,v});case 4:return unit({u,v,1});default:return unit({u,v,-1});}
        }
        void prepare(const Grid& grid){
            if(!a[0].empty())return;
            for(int side=0;side<6;side++)a[side].resize(Side*Side);
            #pragma omp parallel for schedule(static)
            for(int n=0;n<6*Side;n++){
                int side=n/Side,y=n%Side;float v=2.f*y/(Side-1)-1;
                for(int x=0;x<Side;x++){
                    auto s=grid.at(direction(side,2.f*x/(Side-1)-1,v));
                    a[side][y*Side+x]={s.h,s.r,s.g,s.b,s.gx,s.gy,s.k,s.m};
                }
            }
        }
        Cell get(V p)const{
            float ax=fabsf(p.x),ay=fabsf(p.y),az=fabsf(p.z),u,v;int face;
            if(az>=ax&&az>=ay){u=p.x/az;v=p.y/az;face=p.z>0?4:5;}
            else if(ax>=ay){u=p.z/ax;v=p.y/ax;face=p.x>0?0:1;}
            else{u=p.x/ay;v=p.z/ay;face=p.y>0?2:3;}
            u=clamp((u+1)*(.5f*(Side-1)),0,Side-1.0001f);v=clamp((v+1)*(.5f*(Side-1)),0,Side-1.0001f);
            int x=int(u),y=int(v);u-=x;v-=y;
            const Cell *s=&a[face][y*Side+x];
            auto q=[&](float Cell::*p0){return lerp(lerp(s[0].*p0,s[1].*p0,u),lerp(s[Side].*p0,s[Side+1].*p0,u),v);};
            return {q(&Cell::h),q(&Cell::r),q(&Cell::g),q(&Cell::b),q(&Cell::dx),q(&Cell::dy),q(&Cell::k),q(&Cell::m)};
        }
    } modern,ancient;
    static float wave8(float x){const float z=x*x;const float z4=z*z;return z4*z4;}
    V surface(const Cell& c,V n,V d,V sun,bool old,float air,float t,float emphasis,V center)const{
        const float stay=clamp(-dot(n,d));
        const V E=unit({n.z,0,-n.x}),U=cross(n,E);
        const V N=unit(n-E*c.dx*.79f+U*c.dy*.79f);
        const float nw=clamp(dot(n,sun)),nl=clamp(dot(N,sun)),terrain=ramp(.002f,.13f,c.h),land=clamp(c.m);
        const float shallow=ramp(-.11f,-.007f,c.h),mid=ramp(-.40f,-.052f,c.h);
        V al={c.r,c.g,c.b};
        V sea=lerp({.0027f,.013f,.028f},{.0061f,.029f,.049f},mid);
        sea=lerp(sea,{.011f,.079f,.095f},shallow*shallow*.93f);
        const float shade=.46f+.63f*nw;
        sea=sea*shade+al*V{.13f,.28f,.43f};
        const float glint=wave8(clamp(dot(reflect(d,n),sun)));
        sea+=V{.061f,.089f,.105f}*(glint*(.37f+.53f*shallow));
        V clay=al*(old?V{1.30f,1.025f,.72f}:V{1.22f,1.14f,.88f});
        float y=luminance(clay);
        clay=lerp(clay,V{y,y,y},.19f);
        clay=lerp(clay,old?V{.278f,.167f,.062f}:V{.263f,.211f,.124f},.14f+.32f*terrain);
        clay=clay*(V{.30f,.385f,.46f}+V{1.16f,.999f,.804f}*(.16f*nw+.77f*nl));
        const float coast=1-sq(2*c.m-1),rim=wave8(1-stay);
        V base=lerp(sea,clay,land)+V{.036f,.066f,.061f}*coast*coast*(.41f+.48f*nw);
        const float edge=(1-stay)*(1-stay),dist=1-dot(n,center);
        const float field=(1-ramp(.002f,.049f,dist))*emphasis*land;
        base+=V{.035f,.093f,.050f}*field*(.70f+.30f*nl);
        // Low camera-position haze keeps the dark-side coast visible. Sparse high
        // clouds use coherent coordinates in the lit hemisphere, not zooming texture.
        if(!old&&stay>.13f&&air>.0001f){
            float x=n.x*10.2f+n.z*3.8f,y=n.y*24.9f-n.z*6.1f+.38f*sinf(n.x*17.f);
            float m=.64f*fnoise(x+.006f*t,y)+.28f*fnoise(x*2.17f-9,y*2.05f)+.08f*fnoise(x*4.1f,y*4.3f+8.f);
            float cl=ramp(.575f,.829f,m)*air*(.38f+.62f*nw);
            base=lerp(base,{.52f,.61f,.64f},cl);
        }
        return base+V{.021f,.066f,.119f}*(edge*(.36f+.63f*nw)+rim*(.39f+.61f*nw));
    }
    void draw(CutSet& s){
        const auto orbit=globe_orbit(s);const int k=s.shot;auto& g=s.g;const float t=s.t;
        const V pos=geo(orbit.lat,orbit.lon)*orbit.range;
        const V radial=unit(pos),back=radial*(-1.f),rr=unit(cross(back,{0,1,0})),up=cross(rr,back);
        const float aspect=g.w/float(g.h),focal=tanf(orbit.lens*.5f*RAD);
        const V aim=(rr*((.5f-orbit.ax)*2.f*orbit.range*focal*aspect)+up*((orbit.ay-.5f)*2.f*orbit.range*focal));
        const Camera cam(pos,aim,orbit.lens,aspect,orbit.roll);g.cam=cam;
        const bool flip=k==3;const bool old=flip||k==46||k==48||k==51||k==53||k==56||k==58||k==59;
        const auto& now=s.earth.modern;const auto& past=s.earth.ancient;
        if(!old||flip)modern.prepare(now);
        if(old)ancient.prepare(past);
        const float swipe=flip?smoother((s.f-K_REWIND_SCAN)/float(K_OLD_LOCK-K_REWIND_SCAN)):1;
        const float field=k==53?s.at(K_RANGE,.8f):k==59?.68f*(1-smoother(s.sec()/6.3f)):k==51?.26f:0.f;
        const V M=unit(s.earth.pin(true,0)+s.earth.pin(true,1)),plane=unit({.91f,-.25f,.31f}),sun=unit({-.52f,.64f,.81f});
        const float p2=dot(pos,pos);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
            float X=(x+.5f)/g.w,Y=(y+.5f)/g.h;
            const V d=cam.ray(X,Y);const float b=dot(pos,d),disc=R*R-p2+b*b;
            const float v=clamp(1-sq((X-.53f)*1.52f)-sq((Y-.48f)*1.64f));
            V c;
            if(disc<0){
                const V n=unit(pos-d*b);const float i=clamp(dot(n,sun));
                float glow=1/(1+(-disc)*4.6f);glow*=glow;
                const float z=hash(int(x*1920.f/g.w),int(y*1080.f/g.h));
                const float stars=(z>.9993f?.005f+hash(x-81,y+42)*.012f:0.f)*v*(1-glow);
                c=V{.0015f,.0042f,.0082f}+V{.0041f,.0088f,.0172f}*(v*v)+V{.092f,.219f,.391f}*(glow*(.20f+.78f*i))+V{stars,stars*.93f,stars*.73f};
            }else{
                V n=unit(pos+d*(-b-sqrtf(disc))); float w=1.f;
                float line=dot(n,plane)-lerp(1.015f,-1.015f,swipe);
                if(flip)w=swipe>=1?1.f:swipe<=0?0.f:ramp(-.023f,.027f,line);
                if((!old)||w<.9999f)c=surface(modern.get(n),n,d,sun,false,k==5||k==34?.032f:.175f,t,0,M);
                if(old&&w>.0001f){V z=surface(ancient.get(n),n,d,sun,true,0,t,field,M);c=w>.9999f?z:lerp(c,z,w);}
                if(flip&&swipe>0&&swipe<1){float z=1-ramp(.004f,.052f,fabsf(line));c+=V{.141f,.35f,.29f}*(z*z*.60f);}
                // Sparse latitude rings provide a scale reference and conform to the limb.
                if(old&&!flip){
                    float u=n.y*6.f,l=fabsf(u-roundf(u));
                    c+=V{.028f,.059f,.063f}*((1-ramp(.004f,.015f,l))*clamp(-dot(n,d))*.53f);
                }
                // Blend the ground into the same atmosphere as the outer limb.
                c=lerp(c,V{.038f,.107f,.192f}*(.49f+.51f*clamp(dot(n,sun))),1-ramp(.000f,.048f,-dot(n,d)));
            }
            const int px=y*g.w+x;
            camera_response.put(&g.rgb[3*px],c*(.93f+.07f*v));g.z[px]=0;
        }
        const bool use_old=old&&(!flip||s.f>=K_OLD_LOCK);
        for(int i=0;i<2;i++){
            V P=s.earth.pin(use_old,i);s.marks[i]=cam.project(P);
            if(dot(unit(P),pos-P)<.19f)s.marks[i].z=-1.f;
        }
        auto A=unit(s.earth.pin(use_old,0)),B=unit(s.earth.pin(use_old,1));
        const float angle=acosf(clamp(dot(A,B),-.99999f,.99999f));
        for(int j=0;j<10;j++){
            float u=j/9.f; V P=unit(A*sinf((1-u)*angle)+B*sinf(u*angle));
            const float lift=(use_old?.075f:.214f)*sinf(u*PI);
            s.marks[2+j]=cam.project(P*(R+.037f+lift));
        }
    }
};
}
