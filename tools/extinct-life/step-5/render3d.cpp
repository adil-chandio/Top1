// Atlantic Tracks: every frame cast through a perspective lens into an original 3D set.
// CPU renderer: world displacement, signed-depth prints and strata, real parallax,
// lens-depth matte, water plane with specular/sediment, and articulated foot contact.
// No animation libraries or prior-cut frames are required.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace atl {
constexpr float PI=3.14159265358979f, RAD=PI/180.f, R=6.371f;
constexpr int FPS=24, FIRST[]={0,63,99,245,470,629,765,869,1040,1154,1267,1353,1457};
struct V {
    float x=0,y=0,z=0;
    V operator+(V b)const{return{x+b.x,y+b.y,z+b.z};} V operator-(V b)const{return{x-b.x,y-b.y,z-b.z};}
    V operator*(float k)const{return{x*k,y*k,z*k};} V operator/(float k)const{return*this*(1.f/k);}
    V operator*(V b)const{return{x*b.x,y*b.y,z*b.z};} V& operator+=(V b){return *this=*this+b;}
};
float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
float len(V a){return sqrtf(dot(a,a));}
V unit(V a){return a/std::max(.00001f,len(a));}
float clamp(float x,float a=0,float b=1){return std::clamp(x,a,b);}
float lerp(float a,float b,float k){return a+(b-a)*k;}
V lerp(V a,V b,float u){return a+(b-a)*u;}
float smooth(float u){u=clamp(u);return u*u*(3-2*u);}
float ramp(float a,float b,float x){return smooth((x-a)/(b-a));}
float sq(float x){return x*x;}
V geo(float lat,float lon){lat*=RAD;lon*=RAD;return{cosf(lat)*sinf(lon),sinf(lat),cosf(lat)*cosf(lon)};}
V reflect(V d,V n){return d-n*(2.f*dot(d,n));}
float hash(int x,int y){uint32_t h=(uint32_t(x)*374761393u+uint32_t(y)*668265263u)^0x5ccaf29fu;h=(h^(h>>13))*1274126177u;return float((h^(h>>16))>>8)*0x1p-24f;}
struct Sample{float h,r,g,b,gx,gy,m,k;V rgb()const{return{r,g,b};}};
static_assert(sizeof(Sample)==32);
struct Grid {
    int w=0,h=0; float span=0; std::vector<Sample> data;
    Grid(const std::string& file,float units):span(units){
        std::ifstream in(file,std::ios::binary);char magic[4];uint32_t dim[3];
        in.read(magic,4);in.read(reinterpret_cast<char*>(dim),12);
        if(!in||std::string(magic,4)!="GEO8"||dim[2]!=8||dim[0]<2||dim[1]<2||dim[0]>4096||dim[1]>4096)throw std::runtime_error("bad field: "+file);
        w=int(dim[0]);h=int(dim[1]);data.resize(size_t(w)*size_t(h));
        in.read(reinterpret_cast<char*>(data.data()),data.size()*sizeof(Sample));
        if(!in)throw std::runtime_error("short field: "+file);
    }
    struct Tex {const Sample *a,*b,*c,*d;float u,v;};
    Tex map(float x,float y,bool wrap)const{
        float j=x*w-.5f,k=clamp(y*h-.5f,0.f,float(h-1));
        j=wrap?j:clamp(j,0.f,float(w-1));
        int bx=(int)floorf(j),iy=(int)k,iy2=std::min(h-1,iy+1);
        int ix=wrap?(bx+w)%w:bx,ix2=wrap?(ix+1)%w:std::min(w-1,ix+1);
        return{&data[iy*w+ix],&data[iy*w+ix2],&data[iy2*w+ix],&data[iy2*w+ix2],j-bx,k-iy};
    }
    static float take(const Tex& t,float Sample::*m){return lerp(lerp(t.a->*m,t.b->*m,t.u),lerp(t.c->*m,t.d->*m,t.u),t.v);}
    static Sample all(const Tex& t){return{take(t,&Sample::h),take(t,&Sample::r),take(t,&Sample::g),take(t,&Sample::b),
        take(t,&Sample::gx),take(t,&Sample::gy),take(t,&Sample::m),take(t,&Sample::k)};}
    bool inside(float x,float z)const{return fabsf(x)<span*.5f&&fabsf(z)<span*.5f;}
    static float mirror(float x){
        if(x>=0&&x<=1)return x;
        float mod=x-2*floorf(x*.5f);
        return mod<=1?mod:2-mod;
    }
    Tex local(float x,float z)const{return map(mirror(x/span+.5f),mirror(z/span+.5f),false);}
    float height(float x,float z,float restore=0.f)const{
        Tex t=local(x,z);
        float safe=inside(x,z)?restore:1.f;
        return take(t,&Sample::h)+(safe>0?safe*(.146f*take(t,&Sample::m)-.022f*take(t,&Sample::k)):0);
    }
    Sample at(V n)const{
        float lat=asinf(clamp(n.y,-1.f,1.f)),lon=atan2f(n.x,n.z);
        return all(map(lon/(2*PI)+.5f,.5f-lat/PI,true));
    }
};
struct Camera{
    V p,f,r,u;float focal,aspect;
    Camera(V eye,V aim,float angle,float asp,float roll=0):p(eye),f(unit(aim-eye)),focal(tanf(.5f*RAD*angle)),aspect(asp){
        V right=unit(cross(f,{0,1,0})),up=cross(right,f);r=right*cosf(roll)+up*sinf(roll);u=up*cosf(roll)-right*sinf(roll);
    }
    V ray(float x,float y)const{return unit(f+r*((2*x-1)*focal*aspect)+u*((1-2*y)*focal));}
    V project(V point)const{
        V d=point-p;float z=dot(d,f),s=focal*std::max(z,.001f);
        return{.5f+.5f*dot(d,r)/(s*aspect),.5f-.5f*dot(d,u)/s,z};
    }
};
struct Plan {int kind; Camera cam;float focus;float iris;float t;};
Plan plan(int frame,float aspect){
    int k=int(std::upper_bound(std::begin(FIRST),std::end(FIRST),frame)-FIRST)-1;
    float t=frame/float(FPS),u=smooth((frame-FIRST[k])/float(FIRST[k+1]-FIRST[k]));
    V p,a;float v=40,d=3,iris=0,roll=0;
    switch(k){
    case 0: p=lerp(V{-1.07f,2.42f,-1.66f},V{-.46f,1.94f,-1.47f},u);a={.26f,-.05f,.13f};v=34.5f;d=lerp(2.93f,2.46f,u);iris=.65f;roll=.02f;break;
    case 1: p=lerp(V{1.36f,2.48f,-1.60f},V{.98f,2.31f,-1.25f},u);a={.02f,-.08f,.16f};v=36;d=lerp(3.04f,2.67f,u);iris=.52f;roll=-.03f;break;
    case 2: case 3:{
        float a0=ramp(4.125f,19.583f,t),pivot=ramp(11.38f,18.70f,t);
        float enter=1-ramp(4.125f,7.42f,t);
        float lat=lerp(10.5f,12.3f,a0)-14.2f*pivot+7.8f*enter,lon=lerp(-20.6f,-14.8f,a0)+13.8f*pivot-7.4f*enter;
        // Same sphere and lens at the reveal; a slow later reframe centres the joined land.
        p=geo(lat,lon)*(lerp(14.83f,14.31f,a0)-.53f*pivot+1.55f*enter);
        a=geo(2.1f,-15.0f+14.4f*pivot)*1.05f + V{0,.50f-.42f*pivot,0};v=40.2f;
        roll=.074f+.026f*sinf(a0*2.4f)-.111f*pivot+.091f*enter;break;
    }
    case 4:p=lerp(V{-9.6f,7.85f,-26.0f},V{-4.0f,6.4f,-21.4f},u);a=lerp(V{5.5f,1.2f,2.7f},V{3.5f,1.05f,5.7f},u);v=47.8f;d=24;iris=.32f;break;
    case 5:{float lat=lerp(13.8f,10.5f,u),lon=lerp(4.f,13.4f,u);p=geo(lat,lon)*lerp(11.88f,8.28f,u);a=geo(8.292f,14.5167f)*(R-.07f);v=lerp(41,34,u);roll=lerp(-.086f,.095f,u);break;}
    case 6:p=lerp(V{-3.9f,6.58f,-7.5f},V{-2.65f,6.32f,-6.7f},u);a={.20f,1.55f,.32f};v=38;d=8.65f;iris=.22f;break;
    case 7:p=lerp(V{-4.7f,8.9f,-25.7f},V{.87f,6.4f,-15.1f},u);a=lerp(V{1.8f,.37f,.58f},V{4.6f,.14f,9.8f},u);v=46;d=20;iris=.10f;break;
    case 8:p=lerp(V{-2.4f,2.68f,-3.59f},V{-1.47f,2.64f,-2.75f},u);a=lerp(V{.13f,-.016f,-.57f},V{-.23f,-.04f,-.27f},u);v=43;d=3.7f;iris=.22f;break;
    case 9:p=lerp(V{-1.72f,1.61f,-1.80f},V{-1.52f,1.84f,-1.56f},u);a={.10f,.079f,.24f};v=40;d=2.84f;iris=.56f;break;
    case 10:p=lerp(V{1.91f,2.45f,-3.43f},V{1.68f,2.07f,-1.87f},u);a=lerp(V{-.10f,-.065f,-.43f},V{.09f,-.04f,.95f},u);v=40;d=3.55f;iris=.27f;break;
    case 11:p=lerp(V{2.92f,4.71f,-4.57f},V{1.91f,5.45f,-4.21f},u);a=lerp(V{-.12f,-.07f,.45f},V{.07f,-.04f,.71f},u);v=43;d=6.3f;iris=.18f;break;
    default:throw std::runtime_error("invalid shot");
    }
    return{k,Camera(p,a,v,aspect,roll),d,iris,t};
}
struct Pick{float t;V p,n,albedo;float deep,rim;};
struct El{
    V center,fwd,right,up,scale;float kind;
    El(V a,V b,float rx,float rz,float grow,float mat){
        center=(a+b)*.5f;fwd=unit(b-a);right=unit(cross(fwd,{0,1,.013f}));up=cross(right,fwd);
        scale={rx,len(b-a)*.5f+grow,rz};kind=mat;
    }
    bool hit(V p,V d,float& best,V& n,float& material)const{
        V oc=p-center;
        V o={dot(oc,right)/scale.x,dot(oc,fwd)/scale.y,dot(oc,up)/scale.z};
        V v={dot(d,right)/scale.x,dot(d,fwd)/scale.y,dot(d,up)/scale.z};
        float a=dot(v,v),b=dot(o,v),c=dot(o,o)-1,m=b*b-a*c;
        if(m<=0) return false;
        float t=(-b-sqrtf(m))/a;
        if(t<=.018f||t>=best)return false;
        V h=o+v*t; n=unit(right*(h.x/scale.x)+fwd*(h.y/scale.y)+up*(h.z/scale.z));best=t;material=kind;return true;
    }
};
struct Stamp {
    std::vector<El> foot;
    float press=1,restore=0,offset=0;
    V shadow;
    explicit Stamp(float t,bool enable){
        if(!enable)return;
        float down=ramp(48.33f,49.36f,t),lift=ramp(49.99f,51.39f,t);
        press=ramp(49.14f,49.63f,t);restore=1-press;
        offset=1.59f*(1-down)+1.84f*lift-.076f*press*(1-lift);
        float drift=lerp(-.145f,0,down)+.22f*lift;
        auto q=[&](float x,float y,float z){return V{x+drift+.06f,y+offset,z+.17f-.23f*(1-down)+.37f*lift};};
        shadow=q(0,.10f,-.13f);
        if(t>51.5f||t<48.20f)return;
        auto el=[&](V a,V b,float rx,float rz,float grow,float kind=0){foot.emplace_back(a,b,rx,rz,grow,kind);};
        el(q(-.27f,1.67f,-.70f),q(-.08f,.47f,-.42f),.216f,.225f,.155f);
        el(q(-.10f,.60f,-.43f),q(0,.16f,-.26f),.217f,.199f,.121f);
        el(q(.0f,.17f,-.34f),q(0,.124f,.03f),.253f,.147f,.089f);
        const V a[]={q(-.108f,.134f,.012f),q(-.010f,.129f,.02f),q(.129f,.13f,.006f)};
        const V b[]={q(-.35f,.089f,.123f),q(-.001f,.091f,.32f),q(.345f,.089f,.194f)};
        const V c[]={q(-.51f,.063f,.260f),q(.014f,.078f,.591f),q(.49f,.064f,.386f)};
        const V tip[]={q(-.58f,.025f,.319f),q(.021f,.032f,.724f),q(.556f,.026f,.441f)};
        for(int i=0;i<3;i++){
            const float w=i==1?.117f:.101f;
            el(a[i],b[i],w,.093f,.081f);el(b[i],c[i],w*.77f,.069f,.054f);el(c[i],tip[i],w*.56f,.054f,.029f,1);
        }
    }
};

struct Render {
    Grid modern,ancient,brazil,koum,stamp,steps,river,flood,shelves;
    const V sunmap=unit({-.59f,.56f,.83f});
    std::array<unsigned char,32768> tone{};
    Render(const std::string& f):modern(f+"/modern.field",0),ancient(f+"/ancient.field",0),brazil(f+"/brazil.field",9.6f),koum(f+"/koum.field",9.6f),
       stamp(f+"/stamp.field",9.6f),steps(f+"/steps.field",9.6f),river(f+"/river.field",96),flood(f+"/floodplain.field",96),shelves(f+"/shelves.field",14){
        for(size_t i=0;i<tone.size();i++){
            float x=i/(tone.size()-1.f)*3.0f;
            float m=(x*(1.f+.51f*x))/(1.f+.78f*x+1.04f*x*x);  // soft film shoulder
            float g=powf(clamp(m),1.f/2.15f);
            tone[i]=uint8_t(std::lround(clamp(g)*255));
        }
    }
    uint8_t byte(float x)const{return tone[size_t(clamp(x,0.f,2.9999f)*(tone.size()-1)/3.f)];}
    const Grid& local(int k)const{switch(k){case 0:return brazil;case 1:return koum;case 4:return flood;case 6:return shelves;case 7:return river;case 9:return stamp;default:return steps;}}
    V pin(bool old,int i)const{
        constexpr float coord[2][2][2]={{{-6.7342701f,-38.2620659f},{8.2916667f,14.5166667f}},{{-5.9425466f,-5.7300089f},{-5.6880250f,5.0564354f}}};
        V n=geo(coord[old][i][0],coord[old][i][1]);
        return n*(R+(old?ancient:modern).at(n).h+.020f);
    }
    V sphere(const Grid& fld,V o,V d,float t,float sw,bool old,float scan=0.f)const{
        float b=dot(o,d),disc=b*b-(dot(o,o)-R*R);
        if(disc<=0){
            V tangent=unit(o-d*b);
            float halo=expf(-std::max(0.f,-disc)*.98f) * (.42f+.63f*clamp(dot(tangent,sunmap)));
            return V{.0037f,.0070f,.0130f}+V{.018f,.073f,.116f}*(.86f*halo);
        }
        float tr=-b-sqrtf(disc);
        V p=o+d*tr,n=unit(p); Sample s=fld.at(n);
        float view=std::max(.18f,-dot(n,d));
        if(s.h>.0045f){
            tr-=s.h/view;
            p=o+d*tr;n=unit(p);s=fld.at(n);
        }
        V east=unit({n.z,0,-n.x}),north=cross(n,east);
        V norm=unit(n-east*(s.gx*.70f)+north*(s.gy*.70f));
        float daylight=clamp(dot(norm,sunmap)),L=.39f+.81f*daylight;
        float glint=std::max(0.f,dot(reflect(d,n),sunmap));
        glint*=glint;glint*=glint;glint*=glint;
        float mist=powf(1-clamp(-dot(n,d)),3.65f);
        V col=s.rgb()*V{L*1.045f,L*1.00f,L*.92f};
        col+=V{.057f,.127f,.166f}*(mist*.93f+.026f);
        if(s.m<.95f){
            // Short-wavelength roughness, never a repetitive "current" drawn on the map.
            float w=.53f+.12f*s.k+.04f*sinf(p.x*39.4f+t*.60f+p.z*29.3f);
            col+=V{.089f,.115f,.117f}*(glint*(1-s.m)*w*(old?.18f:.30f));
        }
        // A very light cloud veil. Coastlines stay readable under it.
        float cloud=ramp(.75f,1.63f,s.k)*(.018f+.044f*(1-sw));
        if(!old)col=lerp(col,{.41f,.464f,.481f},cloud);
        if(scan>.003f){
            // The projected scan briefly exposes a graticule and contour relief.
            float lat=asinf(n.y)/RAD,lon=atan2f(n.x,n.z)/RAD;
            float latline=1-ramp(.054f,.175f,fabsf(lat-10.f*roundf(lat*.1f)));
            float lonline=1-ramp(.059f,.182f,fabsf(lon-10.f*roundf(lon*.1f)));
            float h=s.h*.64f/.006f,ring=1-ramp(.045f,.19f,fabsf(h-roundf(h)));
            col+=V{.112f,.289f,.254f}*(scan*(.33f*view*std::max(latline,lonline)+.25f*ring*s.m));
        }
        return col;
    }
    V world(const Plan& p,V d,float x)const{
        if(p.kind!=3) return sphere(modern,p.cam.p,d,p.t,x,false);
        if(p.t>=11.46f) return sphere(ancient,p.cam.p,d,p.t,x,true);
        float u=ramp(10.208333f,11.458333f,p.t);
        float b=dot(p.cam.p,d),disc=b*b-(dot(p.cam.p,p.cam.p)-R*R);
        if(disc<=0)return sphere(modern,p.cam.p,d,p.t,x,false);
        V normal=(p.cam.p+d*(-b-sqrtf(disc)))/R;
        // This is a moving plane across the 3D world, not an invented age interpolation.
        const V plane={.938f,-.139f,.314f};
        float dist=dot(normal,plane)-lerp(1.155f,-1.155f,u);
        float w=ramp(-.030f,.030f,dist);
        float scan=.86f*expf(-sq(dist/.18f));
        V col;
        if(w<.001f)col=sphere(modern,p.cam.p,d,p.t,x,false,scan);
        else if(w>.999f)col=sphere(ancient,p.cam.p,d,p.t,x,true,scan);
        else{
            V a=sphere(modern,p.cam.p,d,p.t,x,false,scan),z=sphere(ancient,p.cam.p,d,p.t,x,true,scan);
            float flash=expf(-sq(dist/.0105f));
            col=lerp(a,z,w)+V{.150f,.296f,.255f}*flash;
        }
        return col;
    }
    bool rayfield(const Grid& g,V o,V d,int stage,float restore,Pick& p)const{
        const bool water=(stage==4||stage==7),shelf=(stage==6);
        float lo=.024f,hi=water?101.f:29.f;
        // Conservative finite volume around the ground. Each ray intersects the actual displaced heightfield.
        float m=water?g.span*.5f-.02f:std::max(22.f,g.span*.5f);
        auto bound=[&](float o,float d,float a,float b){
            if(fabsf(d)<1e-5f)return a<=o&&o<=b;
            float u=(a-o)/d,v=(b-o)/d;if(v<u)std::swap(u,v);lo=std::max(lo,u);hi=std::min(hi,v);return lo<=hi;
        };
        if(!bound(o.x,d.x,-m,m)||!bound(o.z,d.z,-m,m)||!bound(o.y,d.y,water?-1.2f:-.55f,water?13.4f:shelf?3.24f:.41f))return false;
        float t=lo,prev=lo,err=0;
        float denom=fabsf(d.y)+(water?.70f:shelf?.72f:.46f)*sqrtf(d.x*d.x+d.z*d.z)+.024f;
        for(int k=0;k<(water?89:62)&&t<=hi;k++){
            V q=o+d*t;
            float h=g.height(q.x,q.z,restore);err=q.y-h;
            if(err<.0008f){
                for(int j=0;j<6;j++){
                    float mid=(prev+t)*.5f;V a=o+d*mid;
                    if(a.y>g.height(a.x,a.z,restore))prev=mid;else t=mid;
                }
                q=o+d*t;
                Sample s=Grid::all(g.local(q.x,q.z));
                bool origin=g.inside(q.x,q.z);
                if(restore>.001f||!origin){
                    float f=.017f;
                    s.gx=(g.height(q.x+f,q.z,restore)-g.height(q.x-f,q.z,restore))/(2*f);
                    s.gy=(g.height(q.x,q.z+f,restore)-g.height(q.x,q.z-f,restore))/(2*f);
                }
                p={t,q,unit({-s.gx,1.f,-s.gy}),s.rgb(),origin?s.m*(1-restore):0.f,origin?s.k*(1-restore):0.f};
                return true;
            }
            prev=t;
            t+=clamp(err/denom*.92f,water?.026f:shelf?.013f:.0075f,water?4.0f:.94f);
        }
        return false;
    }
    V sky(V d,V sun,bool high)const{
        float horizon=ramp(-.14f,.29f,d.y),a=clamp(dot(d,sun));
        float bloom=a*a*a*a*a*a;
        V air=lerp(high?V{.33f,.274f,.186f}:V{.283f,.334f,.335f},{.031f,.105f,.181f},horizon);
        float vapor=sinf(d.x*51.0f+6.2f*sinf(d.z*33.f)+11.2f*d.y)*sinf(d.y*113.f+5.4f*d.z);
        air+=V{.58f,.42f,.261f}*(.23f*bloom+.052f*ramp(.29f,.88f,vapor)*(1-.48f*horizon));
        return air;
    }
    V shade_rock(const Grid& g,const Pick& hit,V v,V sun,float t, bool valley,bool shelf,const Stamp& st)const{
        const V p=hit.p,n=hit.n;float wet=clamp(.20f+.68f*hit.deep+.17f*hit.rim);
        float oc=.0f;
        if(!valley){
            for(float q:{.062f,.158f,.31f}){
                V s=p+sun*q;
                oc=std::max(oc,ramp(-.004f,.032f,g.height(s.x,s.z,st.restore)-s.y));
            }
        } else {
            V s=p+sun*2.4f;oc=ramp(-.11f,.55f,g.height(s.x,s.z)-s.y)*.68f;
        }
        float local_shadow=0;
        if(!st.foot.empty()){
            float off=std::max(0.f,st.offset);
            V center=st.shadow-V{sun.x,0,sun.z}*(off+.25f)/sun.y;
            float band=(sq((p.x-center.x)/(.63f+.46f*off))+sq((p.z-center.z-.15f)/(.72f+.31f*off)));
            if(band<5.f){
                local_shadow=expf(-band*2.15f)*.48f/(1+.68f*off);
                V normal,tmp=p+n*.016f;float tt=5.f, mat=0;
                for(const auto& el:st.foot){
                    if(el.hit(tmp,sun,tt,normal,mat))local_shadow=std::max(local_shadow,.74f-.10f*ramp(.2f,1.6f,tt));
                }
            }
        }
        float nd=clamp(dot(n,sun))*((1.f-.61f*oc)*(1.f-local_shadow));
        float ao=1-.29f*hit.deep-.17f*oc;
        V fill=valley?V{.31f,.359f,.346f}:V{.30f,.367f,.355f};
        V albedo=hit.albedo;
        float side=ramp(.24f,.85f,1.f-n.y);
        if(side>.01f){
            // Sidewall mineral banding resolves in world Y, not stretched XY texture.
            float phase=(53.f*p.y+.89f*sinf(p.z*4.5f+p.x*3.3f));
            float layer=.84f+.10f*sinf(phase)+.08f*sinf(phase*2.47f+.9f*sinf(14*p.x-6*p.z));
            V sediment=valley?V{.228f,.124f,.060f}:shelf?V{.216f,.136f,.078f}:V{.128f,.114f,.080f};
            albedo=lerp(albedo,sediment*layer,side*.83f);
        }
        V col=albedo*(fill*(ao*(1-.39f*local_shadow))+V{1.55f,1.20f,.84f}*(nd*.93f));
        col=col*(1-.40f*hit.deep);
        float f=clamp(dot(unit(sun+v),n));
        float f4=f*f; f4*=f4;
        col+=V{1.0f,.80f,.51f}*(f4*f4*f4*(.031f+.163f*wet)*(1-.84f*oc));
        if(!valley&&!shelf){
            float halo=expf(-.122f*(sq(p.x+.68f)+sq(p.z-.75f)));
            col=col*(.79f+.22f*halo);
            // Subtle diffuse sky in the cavity; the wet rim receives warm reflected light.
            col+=V{.087f,.064f,.044f}*(hit.rim*.41f*nd);
        }
        if(shelf){
            float z=hit.p.z+.31f*sinf(hit.p.x*.7f),line=std::min({fabsf(z+3),fabsf(z+1.2f),fabsf(z-.75f),fabsf(z-2.84f)});
            float sweep=ramp(32.18f,33.0f,t)*(1-ramp(34.90f,36.18f,t));
            col+= V{.134f,.054f,.023f}*(expf(-line*13.f)*sweep*.58f);
        }
        return col;
    }
    V earth(const Plan& a,const Stamp& st,V ray,float& depth)const{
        bool river_mode=a.kind==7||a.kind==4,old=a.kind==4,shelf=a.kind==6;
        V sun=unit(old?V{.15f,.38f,.955f}:river_mode?V{-.43f,.47f,-.72f}:a.kind==1?V{.86f,.35f,.40f}:V{.61f,.46f,-.64f});
        const auto& g=local(a.kind);V o=a.cam.p;Pick hit{};
        bool got=rayfield(g,o,ray,a.kind,st.restore,hit);depth=got?hit.t:40.f;
        V col=got?shade_rock(g,hit,ray*(-1),sun,a.t,river_mode,shelf,st):sky(ray,sun,old);
        if(river_mode&&ray.y<-.012f){
            float tw=-o.y/ray.y;V p=o+ray*tw;
            if(tw<depth&&fabsf(p.x)<47.8f&&fabsf(p.z)<47.8f){
                float h=g.height(p.x,p.z);
                if(h<0){
                    float ws=sinf(p.x*3.39f+p.z*2.73f+a.t*2.1f+1.18f*sinf(p.z*1.31f-a.t*.54f));
                    float wp=cosf(p.x*5.3f+p.z*1.9f-a.t*1.5f+1.75f*sinf(p.x*2.2f+p.z*.27f));
                    V n=unit({.034f*ws+.016f*wp,1.f,.025f*wp-.019f*ws});
                    float mu=clamp(-dot(ray,n)),k=1-mu;k=k*k*k;
                    V re=reflect(ray,n);V refl=sky(re,sun,old);
                    float F=.065f+.54f*k,dark=clamp(-h/.62f);
                    V ink=lerp({.088f,.130f,.099f},{.015f,.115f,.111f},dark);
                    col=lerp(ink,refl,F);float gl=clamp(dot(re,sun));gl*=gl;gl*=gl;gl*=gl;gl*=gl;gl*=gl;
                    col+=V{.74f,.51f,.288f}*(gl*.29f);
                    col+=V{.043f,.056f,.033f}*(1-ramp(.012f,.11f,-h))*(.38f+.34f*ws);
                    depth=tw;
                }
            }
        }
        if(!river_mode&&!shelf&&a.kind<=1&&got&&ray.y<-.19f&&hit.deep>.32f){
            // Physically level shallow water only where the print surface lies below it.
            float level=a.kind==0?-.109f:-.097f;
            float wt=(level-o.y)/ray.y;
            V wp=o+ray*wt;
            auto wet=Grid::all(g.local(wp.x,wp.z));
            if(wt<depth&&wt>.03f&&wet.m>.49f&&wet.h<level-.005f){
                float wave=sinf(wp.x*61.0f+wp.z*41.2f+a.t*5.f);
                V wn=unit({wave*.034f,1.f,sinf(wp.z*43.3f-wp.x*63.7f-a.t*4.2f)*.028f});
                V reflected=reflect(ray,wn);
                float reflex=clamp(dot(reflected,sun));reflex*=reflex;reflex*=reflex;reflex*=reflex;
                float fr=1.f-clamp(-dot(ray,wn));
                V bottom=col*V{.67f,.77f,.71f};
                col=bottom+V{.017f,.038f,.037f}*(.66f+.62f*fr)+V{.27f,.193f,.104f}*reflex;
            }
        }
        if(!st.foot.empty()){
            float a1=depth;V n;float kind=0;bool hit_foot=false;
            // Bound the rig before testing its weighted three-digit geometry.
            V rel=o-V{.07f,.40f+st.offset,-.02f};float z=dot(rel,ray),di=z*z-(dot(rel,rel)-2.56f);
            if(di>0)for(const auto& el:st.foot)hit_foot=el.hit(o,ray,a1,n,kind)||hit_foot;
            if(hit_foot){
                V p=o+ray*a1;
                float cells=(.5f+.5f*cosf(61.f*p.z+1.63f*sinf(52.f*p.x)))*(.5f+.5f*cosf((p.y-st.offset)*76.1f+2.f*cosf(p.z*53.f)));
                float crease=ramp(.45f,.78f,cells);
                V diffuse=lerp({.044f,.043f,.032f},{.115f,.083f,.055f},.24f+.27f*crease);
                if(kind>.5f)diffuse=lerp(diffuse,{.195f,.142f,.089f},.56f);
                float li=clamp(dot(n,sun));float highlight=clamp(dot(unit(sun-ray),n));highlight*=highlight;highlight*=highlight;highlight*=highlight;highlight*=highlight;
                float foot_ao=ramp(.009f,.33f,p.y+.07f);
                col=diffuse*(.37f+.72f*li)*(.71f+.29f*foot_ao)+V{.58f,.44f,.23f}*(highlight*(.050f+.044f*crease));
                depth=a1;
            }
        }
        float fog=river_mode?clamp(1-expf(-std::max(0.f,depth-12.f)*(old?.017f:.016f))):ramp(5.8f,20.f,depth)*.32f;
        V air=river_mode?(old?V{.31f,.236f,.145f}:V{.130f,.192f,.204f}):V{.111f,.146f,.132f};
        return got||depth<40.f?lerp(col,air,fog*(.88f+.095f*clamp(ray.y+.6f))):col;
    }
    void frame(const Plan& p,int w,int h,std::vector<uint8_t>& out)const{
        bool map=(p.kind==2||p.kind==3||p.kind==5);Stamp s(p.t,p.kind==9);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<h;y++){
            for(int x=0;x<w;x++){
                float u=(x+.5f)/w,v=(y+.5f)/h,depth=1;V ray=p.cam.ray(u,v);
                V c=map?world(p,ray,u):earth(p,s,ray,depth);
                float vignette=1-.245f*clamp(sq((u-.50f)*1.6f)+sq((v-.48f)*1.54f));
                float L=p.kind==0?1.12f:p.kind==1?1.31f:p.kind==9?1.18f:1.04f;
                c=c*(vignette*L);
                size_t offset=(size_t(y)*w+x)*4;
                out[offset]=byte(c.x);out[offset+1]=byte(c.y);out[offset+2]=byte(c.z);
                float coc=map?0:ramp(.22f,1.1f,fabsf(depth-p.focus)/p.focus)*p.iris;
                out[offset+3]=uint8_t(coc*255);
            }
        }
    }
    void project(const Plan& p,std::ofstream& csv,int frame)const{
        csv<<frame<<','<<p.kind<<','<<p.cam.p.x<<','<<p.cam.p.y<<','<<p.cam.p.z;
        for(bool old:{false,true}){
            for(int i:{0,1}){
                V g=pin(old,i),s=p.cam.project(g),top=p.cam.project(g*1.018f);
                csv<<','<<s.x<<','<<s.y<<','<<top.x<<','<<top.y<<','<<(dot(g,p.cam.p-g)>0?1:0);
            }
            V a=unit(pin(old,0)),b=unit(pin(old,1));
            for(int j=0;j<17;j++){
                float u=j/16.f;
                V q=p.cam.project(unit(lerp(a,b,u))*(R+.066f+(old?.123f:.33f)*sinf(PI*u)));
                csv<<','<<q.x<<','<<q.y;
            }
        }
        for(int i=0;i<5;i++){
            const float x[]={-.32f,.29f,-.25f,.29f,-.23f},z[]={-2.58f,-1.30f,-.05f,1.19f,2.44f};
            V q=p.cam.project({x[i],steps.height(x[i],z[i])+.15f,z[i]});csv<<','<<q.x<<','<<q.y;
        }
        for(int i=0;i<4;i++){
            constexpr float zx[]={-1.91f,-.17f,1.89f,4.05f};
            float x=-1.15f,z=zx[i];V q=p.cam.project({x,shelves.height(x,z)+.15f,z});csv<<','<<q.x<<','<<q.y;
        }
        csv<<'\n';
    }
};
} // namespace atl

int main(int argc,char** argv){
    using namespace atl;
    if(argc!=7){std::fprintf(stderr,"render3d PACK WIDTH HEIGHT FIRST END TRACE\n");return 2;}
    try{
        int w=std::stoi(argv[2]),h=std::stoi(argv[3]),first=std::stoi(argv[4]),end=std::stoi(argv[5]);
        if(w<=0||h<=0||w>1920||h>1080||first<0||end>FIRST[12]||end<=first)throw std::runtime_error("bad render range");
        Render r(argv[1]);std::ofstream trace(argv[6]);if(!trace)throw std::runtime_error("trace path unavailable");
        trace.precision(9);std::vector<uint8_t> pix(size_t(w)*h*4);
        for(int f=first;f<end;f++){
            auto p=plan(f,w/float(h));
            r.frame(p,w,h,pix);
            r.project(p,trace,f);trace.flush();
            if(std::fwrite(pix.data(),1,pix.size(),stdout)!=pix.size())throw std::runtime_error("short frame write");
        }
    }catch(const std::exception& e){std::fprintf(stderr,"%s\n",e.what());return 2;}
}
