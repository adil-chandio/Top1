// Atlantic Tracks v2: shaded worlds, contact grit, an atmospheric scan, and lens-sampled light.
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
#include "marks.hpp"

namespace atl {
constexpr float PI=3.14159265358979f, RAD=PI/180.f, R=6.371f;
constexpr int FPS=24;
constexpr const auto& FIRST=FIRST_FRAMES;
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
float fnoise(float x,float z){
    int X=(int)floorf(x),Z=(int)floorf(z);
    float a=smooth(x-X),b=smooth(z-Z);
    return lerp(lerp(hash(X,Z),hash(X+1,Z),a),lerp(hash(X,Z+1),hash(X+1,Z+1),a),b);
}
struct Sample{float h,r,g,b,gx,gy,m,k;V rgb()const{return{r,g,b};}};
static_assert(sizeof(Sample)==32);
struct Grid {
    int w=0,h=0; float span=0, invspan=0, bottom=0, top=0;
    std::vector<Sample> data;std::vector<float> H;
    Grid(const std::string& file,float units):span(units){
        std::ifstream in(file,std::ios::binary);char magic[4];uint32_t dim[3];
        in.read(magic,4);in.read(reinterpret_cast<char*>(dim),12);
        if(!in||std::string(magic,4)!="GEO8"||dim[2]!=8||dim[0]<2||dim[1]<2||dim[0]>4096||dim[1]>4096)throw std::runtime_error("bad field: "+file);
        w=int(dim[0]);h=int(dim[1]);data.resize(size_t(w)*size_t(h));
        in.read(reinterpret_cast<char*>(data.data()),data.size()*sizeof(Sample));
        if(!in)throw std::runtime_error("short field: "+file);
        if(span>0){
            invspan=1.f/span;H.resize(data.size());bottom=10.f;top=-10.f;
            for(size_t i=0;i<data.size();++i){H[i]=data[i].h;bottom=std::min(bottom,H[i]);top=std::max(top,H[i]);}
        }
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
    Tex local(float x,float z)const{return map(mirror(x*invspan+.5f),mirror(z*invspan+.5f),false);}
    float height(float x,float z,float restore=0.f)const{
        float i=x*invspan+.5f,j=z*invspan+.5f;
        if(restore>0.f||i<0.f||i>1.f||j<0.f||j>1.f){
            Tex a=local(x,z);
            float safe=inside(x,z)?restore:1.f;
            return take(a,&Sample::h)+safe*(.146f*take(a,&Sample::m)-.022f*take(a,&Sample::k));
        }
        i=clamp(i*w-.5f,0.f,w-1.0001f);j=clamp(j*h-.5f,0.f,h-1.0001f);
        int x0=int(i),y0=int(j);i-=x0;j-=y0;const float* p=&H[y0*w+x0];
        return lerp(lerp(p[0],p[1],i),lerp(p[w],p[w+1],i),j);
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
    case 0:p=lerp(V{-1.79f,2.15f,-1.67f},V{-.66f,1.86f,-1.43f},u);a=lerp(V{.23f,-.073f,.20f},V{.17f,-.068f,.222f},u);v=35.5f;d=lerp(3.48f,2.42f,u);iris=.83f;roll=lerp(.038f,-.022f,u);break;
    case 1:p=lerp(V{1.87f,2.20f,-1.47f},V{.94f,2.11f,-1.20f},u);a={.05f,-.07f,.20f};v=36.5f;d=lerp(3.42f,2.56f,u);iris=.76f;roll=lerp(-.062f,.011f,u);break;
    case 2: case 3:{
        float a0=ramp(4.125f,19.583f,t),pivot=ramp(11.38f,18.70f,t);
        float enter=1-ramp(4.125f,7.42f,t);
        float lat=lerp(10.5f,12.3f,a0)-14.2f*pivot+7.8f*enter,lon=lerp(-20.6f,-14.8f,a0)+13.8f*pivot-7.4f*enter;
        // Same sphere and lens at the reveal; a slow later reframe centres the joined land.
        p=geo(lat,lon)*(lerp(14.83f,14.31f,a0)-.53f*pivot+1.55f*enter);
        a=geo(2.1f,-15.0f+14.4f*pivot)*1.05f + V{0,.50f-.42f*pivot,0};v=40.2f;
        roll=.074f+.026f*sinf(a0*2.4f)-.111f*pivot+.091f*enter;break;
    }
    case 4:p=lerp(V{-13.2f,4.83f,-26.8f},V{-7.75f,3.94f,-21.6f},u);a=lerp(V{5.0f,.77f,4.0f},V{5.95f,.61f,7.9f},u);v=43.8f;d=24;iris=.29f;roll=lerp(.017f,-.014f,u);break;
    case 5:{float lat=lerp(13.8f,10.5f,u),lon=lerp(4.f,13.4f,u);p=geo(lat,lon)*lerp(11.88f,8.28f,u);a=geo(8.292f,14.5167f)*(R-.07f);v=lerp(41,34,u);roll=lerp(-.086f,.095f,u);break;}
    case 6:p=lerp(V{-3.9f,6.58f,-7.5f},V{-2.65f,6.32f,-6.7f},u);a={.20f,1.55f,.32f};v=38;d=8.65f;iris=.22f;break;
    case 7:p=lerp(V{-.25f,3.44f,-17.8f},V{2.61f,2.55f,-10.7f},u);a=lerp(V{4.2f,.56f,7.2f},V{6.84f,.33f,10.63f},u);v=43.5f;d=19;iris=.31f;roll=lerp(.018f,-.011f,u);break;
    case 8:p=lerp(V{-2.4f,2.68f,-3.59f},V{-1.47f,2.64f,-2.75f},u);a=lerp(V{.13f,-.016f,-.57f},V{-.23f,-.04f,-.27f},u);v=43;d=3.7f;iris=.22f;break;
    case 9:{float j=expf(-std::max(0.f,t-MUD_CONTACT/24.f)*13.f)*(t>=MUD_CONTACT/24.f?.020f:0.f);p=lerp(V{-1.60f,1.44f,-1.83f},V{-1.25f,1.71f,-1.60f},u)+V{0,-j,0};a={.095f,.057f,.26f};v=39;d=2.70f;iris=.74f;break;}
    case 10:p=lerp(V{1.91f,2.45f,-3.43f},V{1.68f,2.07f,-1.87f},u);a=lerp(V{-.10f,-.065f,-.43f},V{.09f,-.04f,.95f},u);v=40;d=3.55f;iris=.27f;break;
    case 11:p=lerp(V{2.62f,5.39f,-5.22f},V{1.77f,6.37f,-4.57f},u);a=lerp(V{-.13f,-.05f,.60f},V{.01f,-.05f,.81f},u);v=43.5f;d=6.65f;iris=.25f;break;
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
        float contact=MUD_CONTACT/float(FPS),release=MUD_RELEASE/float(FPS);
        float down=ramp(48.28f,contact+.052f,t),lift=ramp(release,release+.92f,t);
        press=ramp(contact,contact+.31f,t);restore=1-press;
        offset=1.53f*(1-down)+1.96f*lift-.087f*press*(1-lift);
        float drift=lerp(-.145f,0,down)+.22f*lift;
        auto q=[&](float x,float y,float z){return V{x+drift+.06f,y+offset,z+.17f-.23f*(1-down)+.37f*lift};};
        shadow=q(0,.10f,-.13f);
        if(t>51.42f||t<48.16f)return;
        auto el=[&](V a,V b,float rx,float rz,float grow,float kind=0){foot.emplace_back(a,b,rx,rz,grow,kind);};
        el(q(-.37f,1.68f,-.62f),q(-.10f,.54f,-.41f),.203f,.227f,.167f);
        el(q(-.10f,.58f,-.43f),q(0,.16f,-.26f),.195f,.191f,.131f);
        el(q(.0f,.17f,-.34f),q(0,.124f,.03f),.253f,.147f,.089f);
        const V a[]={q(-.108f,.134f,.012f),q(-.010f,.129f,.02f),q(.129f,.13f,.006f)};
        const V b[]={q(-.35f,.089f,.123f),q(-.001f,.091f,.32f),q(.345f,.089f,.194f)};
        const V c[]={q(-.51f,.063f,.260f),q(.014f,.078f,.591f),q(.49f,.064f,.386f)};
        const V tip[]={q(-.58f,.025f,.319f),q(.021f,.032f,.724f),q(.556f,.026f,.441f)};
        for(int i=0;i<3;i++){
            const float w=i==1?.117f:.101f;
            V curve={0,.042f*lift,.038f*lift};
            el(a[i],b[i]+curve,w,.097f,.086f);el(b[i]+curve,c[i]+curve,w*.79f,.071f,.055f);
            el(c[i]+curve,tip[i]+curve,w*.57f,.058f,.029f);
            el(tip[i]+curve+(c[i]-tip[i])*.22f,tip[i]+curve+V{0,-.018f,.042f},w*.395f,.038f,.023f,1);
        }
    }
};

struct Render {
    Grid modern,ancient,brazil,koum,stamp,steps,river,flood,shelves;
    const V sunmap=unit({-.54f,.61f,.81f});
    std::array<unsigned char,32768> tone{};
    Render(const std::string& f):modern(f+"/modern.field",0),ancient(f+"/ancient.field",0),brazil(f+"/brazil.field",9.6f),koum(f+"/koum.field",9.6f),
       stamp(f+"/stamp.field",9.6f),steps(f+"/steps.field",9.6f),river(f+"/river.field",96),flood(f+"/floodplain.field",96),shelves(f+"/shelves.field",14){
        for(size_t i=0;i<tone.size();i++){
            float x=i/(tone.size()-1.f)*3.0f;
            float m=(x*(1.65f*x+.142f))/(x*(1.85f*x+.74f)+.141f); // toe and shoulder
            float g=powf(clamp(m),1.f/2.19f);
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
    V sphere(const Grid& fld,V o,V d,float t,float px,bool old,float scan=0.f)const{
        const float b=dot(o,d),rad=dot(o,o)-b*b,disc=R*R-rad;
        float sigma=expf(-std::max(0.f,-disc)*1.28f);
        if(disc<=0){
            V tangent=unit(o-d*b);
            float facing=.32f+.74f*ramp(-.1f,.95f,dot(tangent,sunmap));
            float veil=expf(-std::max(0.f,-disc)*4.0f)*facing;
            float horizon=expf(-std::max(0.f,-disc)*.50f);
            return V{.0029f,.0053f,.0124f}+V{.012f,.056f,.102f}*(.53f*sigma*facing+.14f*horizon)+V{.027f,.103f,.144f}*(veil*.74f);
        }
        float tr=-b-sqrtf(disc);
        V p=o+d*tr,n0=unit(p);Sample s=fld.at(n0),s0=s;
        float cosview=std::max(.17f,-dot(n0,d));
        if(s.h>.014f){
            tr-=s.h/cosview;
            p=o+d*tr;s=fld.at(unit(p));
            if(s.m<.2f)s=s0;
        }
        V east=unit({n0.z,0,-n0.x}),north=cross(n0,east);
        V N=unit(n0-east*(s.gx*.93f)+north*(s.gy*.93f));
        V sun=old?unit({-.83f,.49f,.70f}):sunmap;
        const float di=clamp(dot(N,sun)),fade=clamp(-dot(n0,d));
        const float rim=powf(1-fade,3.95f), air=powf(1-fade,8.7f);
        const float glo=clamp(dot(reflect(d,n0),sun));
        const float cor=1-sq(2.f*s.m-1.f);
        const float height=ramp(.013f,.117f,s.h);
        V al=s.rgb();
        // Same data, contrasting editorial lighting on each epoch. Cavity and
        // shoreline highlights depend on real terrain derivatives and masks.
        V ocean=al*(old?V{.73f,.96f,1.05f}:V{.69f,.94f,1.26f})+V{.0025f,.0090f,.0155f};
        V land=al*(old?V{1.26f,1.01f,.70f}:V{1.11f,1.11f,.91f});
        land+=V{.116f,.071f,.034f}*(height*.35f*di);
        V c=lerp(ocean,land,s.m)*(.34f+.94f*di);
        c+=V{.030f,.089f,.100f}*(cor*cor*cor*(.27f+.49f*di));
        c+=V{.070f,.102f,.142f}*(powf(glo,18.f)*(1-s.m)*(.15f+.14f*s.k));
        c+=V{.032f,.098f,.154f}*(rim*.89f+air*.31f);
        // Very sparse elevated atmospheric detail. No cloud covers a location pin.
        float wind=.035f*t;V at=n0+V{wind,0,0}*.010f;
        float strand=sinf(at.x*12.2f+at.y*7.5f+s.k*3.1f+.36f*sinf(at.z*29.f))*cosf(at.z*16.7f+at.y*13.f);
        float cloud=ramp(.58f,1.0f,strand)*ramp(-.52f,.68f,s.k)*(.030f+.019f*(1-px))*(.62f+.38f*di);
        c=lerp(c,old?V{.42f,.348f,.236f}:V{.55f,.68f,.71f},cloud);
        if(scan>.0028f){
            float la=asinf(n0.y)/RAD,lo=atan2f(n0.x,n0.z)/RAD;
            float lati=1-ramp(.062f,.170f,fabsf(la-8.f*roundf(la/8.f)));
            float loni=1-ramp(.063f,.185f,fabsf(lo-8.f*roundf(lo/8.f)));
            float ht=s.h*.83f/.0065f,contour=1-ramp(.041f,.184f,fabsf(ht-roundf(ht)));
            c+=V{.092f,.236f,.196f}*(scan*(.42f*fade*std::max(lati,loni)+.44f*contour*s.m+.48f*cor));
        }
        return c;
    }
    V world(const Plan& p,V d,float x)const{
        if(p.kind!=3) return sphere(modern,p.cam.p,d,p.t,x,false);
        const float start=EARTH_REWIND/float(FPS), stop=EARTH_LOCK/float(FPS);
        if(p.t>=stop)return sphere(ancient,p.cam.p,d,p.t,x,true);
        const float u=ramp(start,stop,p.t);
        const float b=dot(p.cam.p,d),disc=b*b-(dot(p.cam.p,p.cam.p)-R*R);
        if(disc<=0)return sphere(modern,p.cam.p,d,p.t,x,false);
        V N=(p.cam.p+d*(-b-sqrtf(disc)))/R;
        // A genuine world-coordinate sweep. The gleaming edge and the delayed
        // rings both bend around the sphere; the two endpoint data models do not morph.
        V plane=unit({.906f,-.245f,.317f});
        float phi=dot(N,plane)-lerp(1.19f,-1.16f,u);
        float w=ramp(-.024f,.028f,phi),g=expf(-sq(phi/.14f));
        V c;
        if(w<.002f)c=sphere(modern,p.cam.p,d,p.t,x,false,g);
        else if(w>.998f)c=sphere(ancient,p.cam.p,d,p.t,x,true,g);
        else c=lerp(sphere(modern,p.cam.p,d,p.t,x,false,g),sphere(ancient,p.cam.p,d,p.t,x,true,g),w);
        float pulse=(.85f+.15f*cosf(21.f*N.y-3.1f*p.t));
        const float broad=expf(-sq(phi/.042f)),thin=expf(-sq(phi/.0104f)),echo=expf(-sq((phi-.098f)/.010f));
        c+=V{.14f,.290f,.249f}*(pulse*(broad*.29f+thin*1.02f+echo*.17f));
        return c;
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
        float ymin=g.bottom-.040f,ymax=g.top+((stage==9)?.103f:.012f);
        if(!bound(o.x,d.x,-m,m)||!bound(o.z,d.z,-m,m)||!bound(o.y,d.y,ymin,ymax))return false;
        float t=lo,prev=lo,err=0;
        float denom=fabsf(d.y)+(water?.74f:shelf?.67f:.40f)*sqrtf(d.x*d.x+d.z*d.z)+.009f;
        for(int k=0;k<(water?96:59)&&t<=hi;k++){
            V q=o+d*t;
            float h=g.height(q.x,q.z,restore);err=q.y-h;
            if(err<.0011f){
                for(int j=0;j<4;j++){
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
            t+=clamp(err/denom*.96f,water?.047f:shelf?.016f:.0090f,water?4.4f:.96f);
        }
        return false;
    }
    V sky(V d,V sun,bool dawn)const{
        float horizon=ramp(-.095f,.31f,d.y),mu=clamp(dot(d,sun));
        float white=powf(mu,34.f),bloom=powf(mu,6.f);
        V deep=dawn?V{.049f,.121f,.183f}:V{.033f,.105f,.178f};
        V warm=dawn?V{.71f,.414f,.230f}:V{.44f,.49f,.49f};
        V air=lerp(warm,deep,horizon);
        if(d.y>-.045f){
            // Layered directional cloud banks: warped, irregular and stretched
            // toward the horizon, not a repeating pattern on a screen plane.
            float mx=7.4f*d.x+2.7f*d.z,my=d.y*24.f+1.9f*d.z;
            float warp=fnoise(mx*.54f+4.f,my*.31f-9.8f);
            float rain=.66f*fnoise(mx+1.3f*warp,my+.83f*warp)+.23f*fnoise(mx*2.4f,my*2.3f-4.f)+.11f*fnoise(mx*4.6f+2.f,my*4.9f);
            float h=ramp(-.036f,.065f,d.y)*(1-.44f*ramp(.21f,.58f,d.y));
            float cloud=ramp(.514f,.729f,rain)*h;
            air=lerp(air,dawn?V{.81f,.589f,.381f}:V{.479f,.519f,.522f},cloud*(dawn?.49f:.36f));
            air+=V{.086f,.069f,.054f}*((1-ramp(.020f,.097f,d.y))*warp*.59f);
        }
        air+=V{.85f,.52f,.28f}*((dawn?.51f:.19f)*bloom+white*(dawn?.44f:.18f));
        return air;
    }
    V shade_rock(const Grid& g,const Pick& hit,V v,V sun,float t, bool valley,bool shelf,const Stamp& st)const{
        const V p=hit.p,n=hit.n;float wet=clamp(.20f+.68f*hit.deep+.17f*hit.rim);
        float oc=.0f;
        if(!valley){
            for(float q:{.038f,.102f,.228f,.54f}){
                V s=p+sun*q;
                oc=std::max(oc,ramp(-.006f,.027f+q*.07f,g.height(s.x,s.z,st.restore)-s.y));
            }
        } else {
            for(float q:{.65f,2.2f,6.5f}){
                V s=p+sun*q;oc=std::max(oc,ramp(-.06f,.35f+q*.075f,g.height(s.x,s.z)-s.y));
            }
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
        float ao=1-.36f*hit.deep-.22f*oc;
        V fill=valley?V{.213f,.348f,.376f}:V{.231f,.360f,.377f};
        V albedo=hit.albedo;
        float side=ramp(.24f,.85f,1.f-n.y);
        if(side>.01f){
            // Sidewall mineral banding resolves in world Y, not stretched XY texture.
            float phase=(53.f*p.y+.89f*sinf(p.z*4.5f+p.x*3.3f));
            float layer=.84f+.10f*sinf(phase)+.08f*sinf(phase*2.47f+.9f*sinf(14*p.x-6*p.z));
            V sediment=valley?V{.228f,.124f,.060f}:shelf?V{.216f,.136f,.078f}:V{.128f,.114f,.080f};
            albedo=lerp(albedo,sediment*layer,side*.83f);
        }
        float glimmer=.87f+.13f*sin(p.x*14.36f+p.z*25.18f);
        V key=valley?V{1.81f,1.26f,.73f}:V{1.63f,1.27f,.84f};
        V col=albedo*(fill*(ao*(1-.46f*local_shadow))+key*(nd*.89f));
        col=col*(1-.34f*hit.deep);
        float f=clamp(dot(unit(sun+v),n));
        float f4=f*f;f4*=f4;
        float rimlight=powf(1-clamp(dot(n,v)),2.7f)*(1-oc)*(.12f+.26f*hit.rim)*nd;
        col+=V{.89f,.64f,.38f}*(f4*f4*f4*(.038f+.158f*wet)*(1-.84f*oc)*glimmer+rimlight*.15f);
        if(!valley&&!shelf){
            float halo=expf(-.122f*(sq(p.x+.68f)+sq(p.z-.75f)));
            col=col*(.70f+.39f*halo);
            // Subtle sky reflected in the cavity; an amber raking edge.
            col+=V{.107f,.072f,.036f}*(hit.rim*.42f*nd);
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
        V sun=unit(old?V{.53f,.24f,.95f}:river_mode?V{-.40f,.45f,.79f}:a.kind==1?V{.75f,.36f,.57f}:a.kind==9?V{-.57f,.48f,.71f}:V{.69f,.35f,-.53f});
        const auto& g=local(a.kind);V o=a.cam.p;Pick hit{};
        bool got=rayfield(g,o,ray,a.kind,st.restore,hit);depth=got?hit.t:130.f;
        V col=got?shade_rock(g,hit,ray*(-1),sun,a.t,river_mode,shelf,st):sky(ray,sun,old);
        if(river_mode&&ray.y<-.012f){
            float tw=-o.y/ray.y;V p=o+ray*tw;
            if(tw<depth&&fabsf(p.x)<47.8f&&fabsf(p.z)<47.8f){
                float h=g.height(p.x,p.z);
                if(h<0){
                    // Break up the shallow-water normals into intersecting groups.
                    float turb=2.31f*sinf(p.z*.78f-p.x*.42f+a.t*.72f)+1.12f*sinf(p.x*.39f+p.z*.66f);
                    float ws=sinf(p.x*2.8f+p.z*3.74f+a.t*2.06f+turb);
                    float wp=cosf(p.x*5.3f-p.z*2.63f-a.t*1.83f+turb*1.7f);
                    float mic=sinf(p.z*14.6f+p.x*13.7f-a.t*5.3f+2.2f*ws+.9f*wp);
                    float m2=sinf(p.z*21.7f-p.x*8.3f-a.t*6.23f+3.3f*wp);
                    float gain=1.f/(1+tw*.021f);
                    V n=unit({gain*(.020f*ws+.022f*wp+.016f*mic-.0081f*m2),1.f,gain*(.024f*wp-.019f*ws+.011f*mic+.013f*m2)});
                    float mu=clamp(-dot(ray,n)),k=1-mu;k=k*k*k*k;
                    V re=reflect(ray,n);V refl=sky(re,sun,old);
                    // Subsurface colour from the same ray, with path-length and
                    // actual bank/sky reflection. Foam lives only at the margins.
                    float dark=ramp(.035f,.62f,-h),F=.074f+.69f*k;
                    V ink=lerp({.132f,.165f,.109f},{.012f,.105f,.099f},dark);
                    if(got)ink=lerp(ink,col,std::max(0.f,1-dark)*.40f);
                    for(float q:{2.2f,5.1f,9.3f}){
                        V w=p+re*q;
                        float occ=ramp(-.06f,.47f,g.height(w.x,w.z)-w.y);
                        if(occ>.19f){refl=lerp(refl,{.094f,.105f,.069f},occ*.64f);break;}
                    }
                    col=lerp(ink,refl,F);
                    float gl=clamp(dot(re,sun));
                    col+=V{.95f,.571f,.272f}*(powf(gl,19.f)*(.48f+.13f*mic)+powf(gl,46.f)*.28f);
                    float lace=(1-ramp(.018f,.135f,-h))*ramp(.02f,.94f,ws*.53f+wp*.45f+mic*.15f);
                    col+=V{.147f,.136f,.096f}*(lace*.46f);
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
                float A=(p.y-st.offset)*109.f+12.4f*p.z, B=p.z*111.f+p.x*79.f;
                float j=fnoise(p.x*29.1f+p.z*13.f,(p.y-st.offset)*26.f);
                float crease1=cosf(A+1.18f*sinf(B*.70f)+1.7f*j),crease2=cosf(B+.92f*cosf(A*.42f)+2.4f*j);
                float scale=ramp(.13f,.72f,crease1*.54f+crease2*.47f);
                float shade=clamp(.32f+.29f*scale+.21f*j+.12f*cosf(A*.072f+B*.09f));
                n=unit(n+V{.061f*crease2,.022f*crease1,.049f*crease1}*(kind>.5f?.19f:.88f));
                V diffuse=lerp({.038f,.054f,.048f},{.157f,.118f,.071f},shade);
                if(kind>.5f)diffuse=lerp(diffuse,{.187f,.129f,.078f},.46f);
                float diffuse_key=clamp(dot(n,sun));float highlight=clamp(dot(unit(sun-ray),n));
                float spec=powf(highlight,kind>.5f?26.f:12.4f), edge=powf(1-clamp(dot(n,ray*(-1))),2.61f);
                float foot_ao=ramp(.009f,.28f,p.y+.11f);
                col=diffuse*(.32f+1.16f*diffuse_key)*(.78f+.22f*foot_ao)+V{.77f,.49f,.23f}*(spec*(.061f+.076f*scale)+.079f*edge*diffuse_key);
                depth=a1;
            }
        }
        if(river_mode){
            float distant=std::max(0.f,depth-8.f),f=clamp(1-expf(-distant*(old?.018f:.013f)));
            if(depth>120.f)f=0.f;
            const float h=o.y+ray.y*(depth*.56f);
            float extra=expf(-sq((h-1.6f)/3.3f))*.22f*(1-expf(-distant*.035f));
            V air=old?V{.399f,.305f,.194f}:V{.143f,.214f,.253f};
            return lerp(col,air,f*(.71f+.16f*ramp(-.31f,.08f,ray.y))+extra);
        }
        float fog=depth>110.f?0.f:ramp(5.1f,20.f,depth)*.23f;
        return lerp(col,{.078f,.136f,.133f},fog);
    }
    void particle_image(const Plan& p,const Grid& g,int w,int h,std::vector<uint8_t>& rgb,const std::vector<float>& zbuf)const{
        const auto mix_pixel=[&](int ix,int iy,float z,V tint,float alpha,float blur){
            if(ix<0||iy<0||ix>=w||iy>=h||alpha<.007f)return;
            size_t i=size_t(iy)*w+ix;float slack=.038f+.005f*z;
            if(z>zbuf[i]+slack)return;
            uint8_t* pix=rgb.data()+i*4;
            const float a=alpha*(1.f-ramp(zbuf[i]-.055f,zbuf[i]+slack,z));
            pix[0]=uint8_t(lerp(pix[0],tint.x,a));pix[1]=uint8_t(lerp(pix[1],tint.y,a));pix[2]=uint8_t(lerp(pix[2],tint.z,a));
            if(blur>.01f)pix[3]=std::max(pix[3],uint8_t(blur*a*255.f));
        };
        const auto spherelet=[&](V pos,float size,V c,float a0){
            V tr=p.cam.project(pos);if(tr.z<.19f||tr.x<-.02f||tr.x>1.02f||tr.y<-.03f||tr.y>1.03f)return;
            float x=tr.x*w,y=tr.y*h,z=len(pos-p.cam.p);
            float k=ramp(.12f,.83f,fabsf(z-p.focus)/p.focus)*p.iris;
            float r=clamp((size/tr.z/p.cam.focal)*h*.5f + k*1.6f,.54f,10.f);
            const int m=int(r*2.2f)+1;
            for(int j=int(y)-m;j<=int(y)+m;j++)for(int i=int(x)-m;i<=int(x)+m;i++){
                float d=sq((i+.5f-x)/r)+sq((j+.5f-y)/(r*.79f+.35f));
                if(d>4.5f)continue;
                float L=.74f+.26f*clamp(.75f-(j-y)/r);
                mix_pixel(i,j,z,c*L,a0*expf(-1.24f*d),k*.78f);
            }
        };
        if(p.kind==9){
            float dt=p.t-MUD_CONTACT/float(FPS);
            if(dt>=0.f&&dt<1.51f){
                for(int j=0;j<103;j++){
                    float q=(dt-hash(j,330)*.118f);if(q<0)continue;
                    float a=PI*2*hash(j,241),sp=.15f+1.24f*hash(j,398),y=q*(.23f+1.28f*hash(j,288))-1.58f*q*q;
                    float x=cosf(a)*(.32f+q*sp)+.06f,z=sinf(a)*(.41f+q*sp)+.20f;
                    y=std::max(0.f,y);
                    const float r=.0042f+.018f*sq(hash(j,46));
                    const V c=lerp({119,109,81},{249,201,133},hash(j,70));
                    const float a0=(.17f+.56f*hash(j,433))*ramp(0.f,.03f,q)*(1.f-ramp(.30f,1.27f,dt));
                    spherelet({x,.037f+y+g.height(x,z),z},r,c,a0);
                }
            }
        } else if(p.kind==0||p.kind==1){
            for(int j=0;j<37;j++){
                float x=(-.5f+hash(j,721))*3.4f+.06f*sinf(j+p.t*.44f),z=(-.5f+hash(j,722))*3.3f +p.t*.013f;
                float y=g.height(x,z)+.07f+.39f*hash(j,723)+.015f*sinf(p.t*1.7f+j*2.1f);
                float dim=(.17f+.22f*hash(j,359))*ramp(.18f,.70f,hash(j,857));
                spherelet({x,y,z},.0037f+hash(j,719)*.0068f,p.kind==0?V{226,166,103}:V{173,215,194},dim);
            }
        } else if(p.kind==4||p.kind==7){
            // Model short, wind-bent blades with actual 3D bases; the Z test is the
            // same terrain and water depth used for the reflections. No plant photo.
            for(int j=0;j<570;j++){
                float z=-32.f+54.f*hash(j,7770),x=-16.4f+35.2f*hash(j,7871);
                Sample soil=Grid::all(g.local(x,z));
                if(soil.h<.16f||soil.h>1.6f||fabsf(soil.gx)+fabsf(soil.gy)>.97f)continue;
                float s=.12f+.43f*sq(hash(j,7866));
                for(int k=0;k<4;k++){
                    float an=6.283f*hash(j,1192+k);V dir={cosf(an),0,sinf(an)};
                    V base={x,soil.h+.008f,z},b=base+dir*(.024f*k);
                    float shift=.045f*sinf(p.t*1.75f+x*.6f+z*.41f+j*.12f);
                    V tip=b+dir*(.12f+.18f*hash(j,k+567))+V{shift,s*(.69f+.31f*hash(j,8165+k)),0};
                    V h0=p.cam.project(b),h1=p.cam.project(tip);
                    if(h0.z<.71f||h1.z<.70f||std::max(h0.x,h1.x)<-.01f||std::min(h0.x,h1.x)>1.01f||std::max(h0.y,h1.y)<-.01f||std::min(h0.y,h1.y)>1.01f)continue;
                    h0.x*=w;h1.x*=w;h0.y*=h;h1.y*=h;
                    int stepsize=int(clamp(len(h1-h0)*1.23f,2.f,71.f));
                    float z0=len(b-p.cam.p),z1=len(tip-p.cam.p);
                    for(int m=0;m<stepsize;m++){
                        float f=m/float(stepsize-1),cx=lerp(h0.x,h1.x,f),cy=lerp(h0.y,h1.y,f);
                        V col=lerp({42,63,52},p.kind==4?V{164,159,80}:V{152,135,70},f);
                        float r=clamp((1-f)*h/z0*.012f,.33f,1.9f);
                        for(int ii=int(cx)-2;ii<=int(cx)+2;ii++){
                            float kx=expf(-sq((ii+.5f-cx)/r))*.73f;
                            mix_pixel(ii,int(cy),lerp(z0,z1,f),col,kx,0);
                        }
                    }
                }
            }
        }
    }
    void frame(const Plan& p,int w,int h,std::vector<uint8_t>& out)const{
        bool map=(p.kind==2||p.kind==3||p.kind==5);Stamp s(p.t,p.kind==9);
        bool details=p.kind==0||p.kind==1||p.kind==4||p.kind==7||p.kind==9;
        std::vector<float> dpt(details?size_t(w)*h:0);
        const float jitterX=(hash(int(p.t*FPS+.5f),261)-.50f)*.32f;
        const float jitterY=(hash(int(p.t*FPS+.5f),262)-.50f)*.32f;
        #pragma omp parallel for schedule(static)
        for(int y=0;y<h;y++){
            for(int x=0;x<w;x++){
                float u=(x+.5f+jitterX)/w,v=(y+.5f+jitterY)/h,depth=1;V ray=p.cam.ray(u,v);
                V c=map?world(p,ray,u):earth(p,s,ray,depth);
                float vignette=1-.30f*clamp(sq((u-.52f)*1.53f)+sq((v-.46f)*1.54f));
                float L=p.kind==0?1.33f:p.kind==1?1.39f:p.kind==9?1.20f:p.kind==4?1.16f:1.10f;
                c=c*(vignette*L);
                size_t pix=size_t(y)*w+x, offset=pix*4;
                out[offset]=byte(c.x);out[offset+1]=byte(c.y);out[offset+2]=byte(c.z);
                float coc=map?0:ramp(.14f,.72f,fabsf(depth-p.focus)/p.focus)*p.iris;
                out[offset+3]=uint8_t(coc*255);
                if(details)dpt[pix]=depth;
            }
        }
        if(details)particle_image(p,local(p.kind),w,h,out,dpt);
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
        for(int i=0;i<6;i++){
            const float x[]={-.32f,.29f,-.25f,.29f,-.23f,.26f},z[]={-2.58f,-1.30f,-.05f,1.19f,2.44f,3.67f};
            V q=p.cam.project({x[i],steps.height(x[i],z[i])+.10f,z[i]});csv<<','<<q.x<<','<<q.y;
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
