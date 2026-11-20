// Perspective, depth-tested software rasterization for the original geological sets.
#pragma once
#include <cstring>
#include <functional>
#include <map>

namespace feature {
using namespace atl;

struct Texture {
    int w=0,h=0;
    std::vector<uint32_t> rgb;
    Texture()=default;
    explicit Texture(const Grid& g,const Render& r,int look){
        w=g.w;h=g.h;rgb.resize(g.data.size());
        const V key=unit(look==2?V{-.48f,.72f,.51f}:look==1?V{-.76f,.42f,-.48f}:V{.60f,.42f,-.65f});
        #pragma omp parallel for schedule(static)
        for(size_t i=0;i<g.data.size();i++){
            const auto& s=g.data[i];V n=unit({-s.gx,1,-s.gy});
            const float l=clamp(dot(n,key)),shade=clamp(.77f-.29f*s.m+.26f*n.y);
            V c=s.rgb()*(V{.289f,.381f,.420f}*shade+V{1.32f,1.10f,.83f}*l)*1.49f;
            c+=V{.092f,.061f,.029f}*s.k*l*.6f;
            c+=V{.013f,.019f,.021f}*(1-n.y)*.43f;
            rgb[i]=uint32_t(r.byte(c.x))|(uint32_t(r.byte(c.y))<<8)|(uint32_t(r.byte(c.z))<<16);
        }
    }
    uint32_t at(float u,float v)const{
        int x=int(clamp(u*w,0.f,w-1.0001f)),y=int(clamp(v*h,0.f,h-1.0001f));return rgb[y*w+x];
    }
};

struct Node {V p,c;float s=0.f,t=0.f;};
struct Proj {float x,y,q,sq,tq;V c;};
struct Raster {
    int w,h;std::vector<uint8_t> rgb;std::vector<float> z;
    Camera cam{{0,2,-5},{0,0,0},40,16.f/9.f};
    explicit Raster(int x,int y):w(x),h(y),rgb(size_t(w)*h*3),z(size_t(w)*h){}
    void begin(const Camera& view,int env,float t){
        cam=view;
        const V A=env==1?V{9,27,35}:env==2?V{14,19,26}:V{13,24,28};
        const V B=env==1?V{31,93,103}:env==2?V{51,40,32}:V{35,56,62};
        #pragma omp parallel for schedule(static)
        for(int y=0;y<h;y++){
            float v=(y+.5f)/h;float beam=env==1?0.17f*sinf(t*.38f+v*1.2f):0;
            for(int x=0;x<w;x++){
                float u=(x+.5f)/w,r=sq((u-.68f)*1.65f)+sq((v-.33f)*1.22f);
                float l=1-clamp(r);l=l*l*(.85f+.15f*v);
                if(env==1){float d=(u-.71f+v*.25f+beam);float caust=.64f+.19f*sinf(35*d+3.6f*t)+.16f*cosf(54*d-2.7f*t);
                    l=clamp(l*.76f+caust*caust*(1-v)*.26f);}
                const V c=lerp(A,B,l);int k=y*w+x;z[k]=0;
                rgb[k*3]=uint8_t(c.x);rgb[k*3+1]=uint8_t(c.y);rgb[k*3+2]=uint8_t(c.z);
            }
        }
    }
    Proj project(const Node& a)const{
        V c=cam.project(a.p);const float q=c.z>.06f?1.f/c.z:0.f;
        return{c.x*w,c.y*h,q,a.s*q,a.t*q,a.c};
    }
    static uint8_t byte(float x){return uint8_t(clamp(x,0.f,255.f));}
    void put(int x,int y,float q,V c,float a=1.f,bool keep=false){
        if(unsigned(x)>=unsigned(w)||unsigned(y)>=unsigned(h)||q<=0)return;
        const int k=y*w+x;if(z[k]>q)return;
        if(!keep)z[k]=q;
        uint8_t* p=&rgb[k*3];
        p[0]=byte(lerp(p[0],c.x,a));p[1]=byte(lerp(p[1],c.y,a));p[2]=byte(lerp(p[2],c.z,a));
    }
    void tri(Proj a,Proj b,Proj c,const Texture* tex=nullptr,float alpha=1.f){
        if(a.q<=0||b.q<=0||c.q<=0)return;
        const float area=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y);
        if(fabsf(area)<.015f)return;
        const int x0=std::max(0,int(floorf(std::min({a.x,b.x,c.x})))),x1=std::min(w-1,int(ceilf(std::max({a.x,b.x,c.x}))));
        const int y0=std::max(0,int(floorf(std::min({a.y,b.y,c.y})))),y1=std::min(h-1,int(ceilf(std::max({a.y,b.y,c.y}))));
        if(x1<x0||y1<y0)return;
        const float inv=1/area,ax=(b.y-c.y)*inv,ay=(c.x-b.x)*inv,bx=(c.y-a.y)*inv,by=(a.x-c.x)*inv;
        const float dx=x0+.5f-c.x,dy=y0+.5f-c.y;
        const float aw=ax*dx+ay*dy,bw=bx*dx+by*dy;
        const V ca=a.c-c.c,cb=b.c-c.c; const float aq=a.q-c.q,bq=b.q-c.q,as=a.sq-c.sq,bs=b.sq-c.sq,at=a.tq-c.tq,bt=b.tq-c.tq;
        for(int y=y0;y<=y1;y++){
            float l=aw+ay*(y-y0),m=bw+by*(y-y0);int k=y*w+x0;
            for(int x=x0;x<=x1;x++,k++,l+=ax,m+=bx){
                if(l<-.00006f||m<-.00006f||l+m>1.00006f)continue;
                const float q=c.q+l*aq+m*bq;if(q<=z[k])continue;
                V v=c.c+ca*l+cb*m;
                if(tex){
                    float o=1.f/q;
                    auto t=tex->at((c.sq+as*l+bs*m)*o,(c.tq+at*l+bt*m)*o);
                    v={v.x*(t&255),v.y*((t>>8)&255),v.z*(t>>16)};
                }
                if(alpha>=.999f){
                    z[k]=q;rgb[3*k]=byte(v.x);rgb[3*k+1]=byte(v.y);rgb[3*k+2]=byte(v.z);
                } else {
                    rgb[3*k]=byte(lerp(rgb[3*k],v.x,alpha));rgb[3*k+1]=byte(lerp(rgb[3*k+1],v.y,alpha));rgb[3*k+2]=byte(lerp(rgb[3*k+2],v.z,alpha));
                }
            }
        }
    }
    void face(V a,V b,V c,V d,V col,float alpha=1.f){
        auto P=[&](V p){return project({p,col});};Proj A=P(a),B=P(b),C=P(c),D=P(d);tri(A,B,C,nullptr,alpha);tri(A,C,D,nullptr,alpha);
    }
    void line(V a,V b,V col,float alpha=1.f,float width=1.f){
        const auto A=project({a,col}),B=project({b,col});if(A.q<=0||B.q<=0||alpha<.002f)return;
        const float length=std::max(fabsf(A.x-B.x),fabsf(A.y-B.y));const int n=int(clamp(length*1.2f+1.f,1.f,2300.f));
        const float g=1.f/n;
        for(int j=0;j<=n;j++){
            float u=j*g,x=lerp(A.x,B.x,u),y=lerp(A.y,B.y,u),q=lerp(A.q,B.q,u)+.00072f;
            if(width<1.9f){
                int X=int(floorf(x)),Y=int(floorf(y));x-=X;y-=Y;
                put(X,Y,q,col,alpha*(1-x)*(1-y),true);put(X+1,Y,q,col,alpha*x*(1-y),true);
                put(X,Y+1,q,col,alpha*(1-x)*y,true);put(X+1,Y+1,q,col,alpha*x*y,true);
            }else{
                const int X=int(x),Y=int(y),rt=int(width*.5f);
                for(int d=-rt;d<=rt;d++)for(int e=-rt;e<=rt;e++)if(e*e+d*d<=rt*rt+1)put(X+d,Y+e,q,col,alpha,true);
            }
        }
    }
    void dust(V p,float rad,V col,float a){
        V P=cam.project(p);if(P.z<.17f)return;
        const float r=clamp(rad/P.z/cam.focal*h*.5f,.65f,17.f);
        int x=int(P.x*w),y=int(P.y*h),d=int(2*r)+1;
        if(x+d<0||x-d>=w||y+d<0||y-d>=h)return;
        const float pressure=1/P.z;
        for(int j=-d;j<=d;j++)for(int i=-d;i<=d;i++){
            float l=(sq(i)+sq(j))/sq(r);if(l<4.3f)put(x+i,y+j,pressure,col,a*expf(-1.18f*l),true);
        }
    }
    template<class Fn> void lattice(int a,int b,Fn fun,const Texture* tex=nullptr,float alpha=1.f){
        std::vector<Proj> pts(size_t(a+1)*(b+1));
        for(int j=0;j<=b;j++)for(int i=0;i<=a;i++)pts[j*(a+1)+i]=project(fun(i/float(a),j/float(b)));
        for(int j=0;j<b;j++)for(int i=0;i<a;i++){
            const int k=j*(a+1)+i;const auto &p=pts[k],&q=pts[k+1],&r=pts[k+a+1],&s=pts[k+a+2];
            tri(p,q,s,tex,alpha);tri(p,s,r,tex,alpha);
        }
    }
};

inline V light(V n,V base,float height=1.f){
    const V key=unit({-.63f,.60f,-.34f}),rim=unit({.47f,.32f,.78f});
    const float d=clamp(dot(n,key)),b=clamp(dot(n,rim));
    return base*V{.33f+.72f*d+.17f*b,.39f+.64f*d+.19f*b,.45f+.47f*d+.22f*b}*height;
}

inline void pebble(Raster& g,V p,V scale,V col,int seed,int rings=8,int sides=12,float ruffle=.073f,float swing=0){
    const float co=cosf(swing),si=sinf(swing);
    g.lattice(sides,rings,[&](float u,float v){
        float a=u*2*PI,b=(v-.5f)*PI;
        V N={cosf(b)*cosf(a),sinf(b),cosf(b)*sinf(a)};
        const float q=1+ruffle*(.65f*sinf(seed*.77f+6.f*a+4.f*b)*cosf(5.f*b)+.38f*cosf(9*a-3*b));
        V Q=N*scale*q;float k=.83f+.27f*hash(int(u*sides+.04f)+seed,int(v*rings+.06f)+831);
        V o={Q.x*co+Q.z*si,Q.y,-Q.x*si+Q.z*co};
        return Node{p+o,light(unit({N.x*co+N.z*si,N.y,-N.x*si+N.z*co}),col,k)};
    });
}
}
