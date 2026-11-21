#pragma once
// Perspective and shaded 3D plates for the portrait edition. No movie pixels in.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace portrait {
constexpr float PI=3.14159265358979f, RAD=PI/180.f;
struct V {
    float x=0,y=0,z=0;
    V operator+(V a)const{return{x+a.x,y+a.y,z+a.z};}
    V operator-(V a)const{return{x-a.x,y-a.y,z-a.z};}
    V operator-()const{return{-x,-y,-z};}
    V operator*(V a)const{return{x*a.x,y*a.y,z*a.z};}
    V operator*(float a)const{return{x*a,y*a,z*a};}
    V operator/(float a)const{return *this*(1.f/a);}
    V& operator+=(V a){return *this=*this+a;}
};
inline float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline float sq(float x){return x*x;}
inline float length(V p){return sqrtf(dot(p,p));}
inline V unit(V p){return p/std::max(1e-8f,length(p));}
inline float cl(float v,float l=0,float h=1){return std::clamp(v,l,h);}
inline float mix(float a,float b,float t){return a+(b-a)*t;}
inline V mix(V a,V b,float t){return a+(b-a)*t;}
inline float ease(float t){t=cl(t);return t*t*(3-2*t);}
inline float smooth(float a,float b,float t){return ease((t-a)/(b-a));}
inline float quint(float t){t=cl(t);return t*t*t*(t*(6*t-15)+10);}
inline float pow4(float x){return sq(sq(x));}
inline V bounce(V ray,V n){return ray-n*(2*dot(ray,n));}
inline V geo(float lat,float lon){lat*=RAD;lon*=RAD;return {cosf(lat)*sinf(lon),sinf(lat),cosf(lat)*cosf(lon)};}
inline float hash(int x,int y){uint32_t h=(uint32_t(x)*0x9E3779B9u)^(uint32_t(y)*0x85EBCA6Bu);h^=h>>16;h*=0x21f0aaadu;h^=h>>15;h*=0x735a2d97u;return ((h^(h>>15))>>8)*0x1p-24f;}
inline float noise(float x,float y){int i=int(floorf(x)),j=int(floorf(y));float t=ease(x-i),u=ease(y-j);return mix(mix(hash(i,j),hash(i+1,j),t),mix(hash(i,j+1),hash(i+1,j+1),t),u);}
inline float mineral(float x,float y){return .59f*noise(x,y)+.275f*noise(x*2.11f+9,y*2.02f-4)+.135f*noise(x*4.43f-4,y*4.22f+6);}
inline V spin(V p,float a){float c=cosf(a),s=sinf(a);return{c*p.x+s*p.z,p.y,c*p.z-s*p.x};}

struct Cam {
    V pos, f, r, u; float lens, ar;
    Cam(V p,V aim,float fov,float aspect,float roll=0):pos(p),f(unit(aim-p)),lens(tanf(.5f*RAD*fov)),ar(aspect){
        V x=unit(cross(f,{0,1,0})),y=cross(x,f);
        r=x*cosf(roll)+y*sinf(roll);u=y*cosf(roll)-x*sinf(roll);
    }
    V project(V p)const{p=p-pos;const float z=dot(p,f),lf=lens*std::max(.0004f,z);return{.5f+.5f*dot(p,r)/(lf*ar),.5f-.5f*dot(p,u)/lf,z};}
    V ray(float x,float y)const{return unit(f+r*((2*x-1)*lens*ar)+u*((1-2*y)*lens));}
};

struct Filmic {
    std::array<uint8_t,4096> t;
    Filmic(){for(size_t i=0;i<t.size();++i){float v=i/4095.f;t[i]=uint8_t(255.0f*(v<.0031308f?12.92f*v:1.055f*powf(v,1/2.4f)-.055f)+.5f);}}
    V grade(V c,float ev=1)const{
        c=c*ev;float p=std::max({c.x,c.y,c.z}),ex=std::max(0.f,p-.52f);
        if(ex>0){float peak=.52f+.475f*ex/(.475f+ex);c=mix(c*(peak/p),V{peak,peak,peak},.22f*ex/(1.15f+ex));}
        return {float(get(c.x)),float(get(c.y)),float(get(c.z))};
    }
    uint8_t get(float x)const{return t[size_t(cl(x)*4095.f+.5f)];}
};
inline const Filmic film;

struct GeoSample{float h,r,g,b,dx,dz,mark,rim; V rgb()const{return{r,g,b};}};
static_assert(sizeof(GeoSample)==32);
struct Field {
    int w=0,h=0;std::vector<GeoSample> s;
    Field(const std::string& filename){
        std::ifstream f(filename,std::ios::binary);char kind[4];uint32_t d[3];
        f.read(kind,4);f.read(reinterpret_cast<char*>(d),12);
        if(!f||std::memcmp(kind,"GEO8",4)||d[2]!=8||d[0]<2||d[1]<2||d[0]>4096||d[1]>4096) throw std::runtime_error("bad GEO8: "+filename);
        w=int(d[0]);h=int(d[1]);s.resize(size_t(w)*h);
        f.read(reinterpret_cast<char*>(s.data()),s.size()*sizeof(GeoSample));
        if(!f)throw std::runtime_error("short GEO8: "+filename);
    }
    GeoSample get(float u,float v,bool wrap=false)const{
        float x=u*w-.5f,y=cl(v*h-.5f,0,h-1.0001f);
        if(!wrap)x=cl(x,0,w-1.0001f);
        const int i=int(floorf(x)),j=int(y),a=wrap?(i+w)%w:i,b=wrap?(a+1)%w:a+1;
        const auto *p=&s[j*w+a],*q=&s[j*w+b];
        x-=i;y-=j;
        auto m=[&](float GeoSample::*e){return mix(mix(p->*e,q->*e,x),mix(p[w].*e,q[w].*e,x),y);};
        return{m(&GeoSample::h),m(&GeoSample::r),m(&GeoSample::g),m(&GeoSample::b),m(&GeoSample::dx),m(&GeoSample::dz),m(&GeoSample::mark),m(&GeoSample::rim)};
    }
    GeoSample spherical(V n)const{return get(.5f+atan2f(n.x,n.z)/(2*PI),.5f-asinf(cl(n.y,-1,1))/PI,true);}
};

struct Tex{
    static constexpr int N=512;
    std::vector<uint8_t> pix;
    explicit Tex(const std::string& file):pix(N*N){
        std::ifstream f(file,std::ios::binary);f.read(reinterpret_cast<char*>(pix.data()),pix.size());
        if(!f||f.peek()!=EOF)throw std::runtime_error("bad material tile: "+file);
    }
    template<class F> explicit Tex(F f):pix(N*N){
        #pragma omp parallel for schedule(static)
        for(int j=0;j<N;++j)for(int i=0;i<N;++i)pix[j*N+i]=uint8_t(cl(f(i/float(N),j/float(N)),0,1)*255+.5f);
    }
    float get(float u,float v)const{
        const float a=u*N,b=v*N;
        const int x=int(floorf(a)),y=int(floorf(b)),i=x&(N-1),j=y&(N-1),I=(x+1)&(N-1),J=(y+1)&(N-1);
        return (1.f/255)*mix(mix(pix[j*N+i],pix[j*N+I],a-x),mix(pix[J*N+i],pix[J*N+I],a-x),b-y);
    }
};
struct Vertex {V p,c;float u=0,v=0,w=0;V texwt{};};
using Face=std::array<int,3>;
struct P {float x,y,q,u,v;V c;float w;V texwt;};
struct Tri{P a,b,c;int x0,x1,y0,y1;const Tex* tex;float strength;};

struct Raster {
    const int w,h;
    std::vector<float> z;
    std::vector<uint8_t> rgb,tmp;
    std::vector<Tri> tris;
    Cam cam{{-1,2,3},{0,0,0},42,9.f/16};
    explicit Raster(int w_,int h_):w(w_),h(h_),z(size_t(w)*h),rgb(z.size()*3),tmp(rgb.size()){tris.reserve(180000);}
    void begin(Cam c){cam=c;std::fill(z.begin(),z.end(),0.f);tris.clear();}
    static uint8_t byte(float v){return uint8_t(cl(v,0,255)+.5f);}
    void poke(int i,V c){rgb[3*i]=byte(c.x);rgb[3*i+1]=byte(c.y);rgb[3*i+2]=byte(c.z);}
    void sky(V low,V high){
        #pragma omp parallel for schedule(static)
        for(int j=0;j<h;++j)for(int i=0;i<w;++i){float t=j/float(h),u=i/float(w);
            V c=mix(high,low,ease(t))*(.88f+.16f*(1-sq(2*u-1)));
            poke(j*w+i,film.grade(c));}
    }
    P proj(const Vertex& v)const{
        V p=cam.project(v.p);float q=p.z>.06f?1/p.z:0;
        return{p.x*w,p.y*h,q,v.u*q,v.v*q,v.c*q,v.w*q,v.texwt*q};
    }
    void tri(P a,P b,P c,const Tex* tx=nullptr,float e=0){
        if(a.q<=0||b.q<=0||c.q<=0)return;
        int x0=std::max(0,int(floorf(std::min({a.x,b.x,c.x})))),y0=std::max(0,int(floorf(std::min({a.y,b.y,c.y}))));
        int x1=std::min(w-1,int(ceilf(std::max({a.x,b.x,c.x})))),y1=std::min(h-1,int(ceilf(std::max({a.y,b.y,c.y}))));
        if(x0>x1||y0>y1)return;
        tris.push_back({a,b,c,x0,x1,y0,y1,tx,e});
    }
    void mesh(const std::vector<Vertex>& v,const std::vector<Face>& f,const Tex* tex=nullptr,float amount=0){
        std::vector<P> p(v.size());
        #pragma omp parallel for schedule(static)
        for(size_t i=0;i<v.size();++i)p[i]=proj(v[i]);
        for(auto a:f)tri(p[a[0]],p[a[1]],p[a[2]],tex,amount);
    }
    void scan(const Tri& tr,int ylo,int yhi){
        const P a=tr.a,b=tr.b,c=tr.c;
        const float area=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y);
        if(fabsf(area)<.007f)return;
        const float ir=1/area,ax=(b.y-c.y)*ir,ay=(c.x-b.x)*ir,bx=(c.y-a.y)*ir,by=(a.x-c.x)*ir;
        const V u=a.c-c.c,v=b.c-c.c,XW=a.texwt-c.texwt,YW=b.texwt-c.texwt;
        const float w0=a.q-c.q,w1=b.q-c.q,s0=a.u-c.u,s1=b.u-c.u,t0=a.v-c.v,t1=b.v-c.v,r0=a.w-c.w,r1=b.w-c.w;
        const float X=tr.x0+.5f-c.x;
        for(int y=ylo;y<=yhi;++y){
            const float Y=y+.5f-c.y;float l=ax*X+ay*Y,m=bx*X+by*Y;int k=y*w+tr.x0;
            for(int x=tr.x0;x<=tr.x1;++x,++k,l+=ax,m+=bx){
                if(l<-.00009f||m<-.00009f||l+m>1.00009f)continue;
                const float q=c.q+w0*l+w1*m;if(q<=z[k])continue;
                const float iq=1/q;
                float shade=1;
                if(tr.tex){const float X=(c.u+s0*l+s1*m)*iq,Y=(c.v+t0*l+t1*m)*iq;
                    if(tr.strength>=0)shade+=tr.strength*(tr.tex->get(X,Y)-.52f);
                    else{
                        const float Z=(c.w+r0*l+r1*m)*iq;V wt=(c.texwt+XW*l+YW*m)*iq;
                        float tex=wt.x*tr.tex->get(Z+.154f,Y-.116f)+wt.y*tr.tex->get(X+.30f,Z)+wt.z*tr.tex->get(X,Y+.37f);
                        shade+=-tr.strength*(tex-.52f);
                    }
                }
                poke(k,(c.c+u*l+v*m)*(iq*shade));z[k]=q;
            }
        }
    }
    void flush(){
        constexpr int B=48;std::vector<std::vector<int>> bins((h+B-1)/B);
        for(int j=0;j<int(tris.size());++j)for(int b=tris[j].y0/B;b<=tris[j].y1/B;++b)bins[b].push_back(j);
        #pragma omp parallel for schedule(dynamic,1)
        for(int b=0;b<int(bins.size());++b)for(int n:bins[b]){
            const auto& tr=tris[n];scan(tr,std::max(tr.y0,b*B),std::min(tr.y1,(b+1)*B-1));
        }
        tris.clear();
    }
    // Very restrained lens softness for areas behind the action plane. A
    // depth check prevents bright background bleeding across the hero silhouette.
    void optics(float focus,float fall,float corner){
        tmp=rgb;
        #pragma omp parallel for schedule(static)
        for(int y=0;y<h;++y){
            float v=(2.f*y/h-1);
            for(int x=0;x<w;++x){
                int k=y*w+x;float u=(2.f*x/w-1),vign=1-corner*(.57f*u*u+.43f*v*v);
                float d=z[k]>1e-6f?1/z[k]:focus+8;
                int r=int(cl((d-focus-fall)*h*.0015f,0,3.75f));
                if(!r){for(int j=0;j<3;++j)rgb[3*k+j]=byte(tmp[3*k+j]*vign);continue;}
                int tl=std::max(0,y-r),br=std::min(h-1,y+r),left=std::max(0,x-r),right=std::min(w-1,x+r);
                const int ns[]={tl*w+left,tl*w+right,br*w+left,br*w+right};int count=4;
                int s[]={4*tmp[3*k],4*tmp[3*k+1],4*tmp[3*k+2]};
                for(int p:ns)if(fabsf(z[p]-z[k])<.058f){++count;for(int j=0;j<3;++j)s[j]+=tmp[3*p+j];}
                for(int j=0;j<3;++j)rgb[3*k+j]=byte(s[j]*(vign/count));
            }
        }
    }
};

inline std::vector<Face> gridfaces(int x,int y){
    std::vector<Face> f;f.reserve(2*(x-1)*(y-1));
    for(int j=0;j<y-1;++j)for(int i=0;i<x-1;++i){int a=j*x+i,b=a+1,c=a+x,d=c+1;f.push_back({a,b,d});f.push_back({a,d,c});}
    return f;
}
}
