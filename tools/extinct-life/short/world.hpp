#pragma once
#include "sediment.hpp"

namespace portrait {

// Two independently sculpted three-toed impressions. They are not tracings,
// photogrammetry, identified specimens, or the stamp used in the mud demo.
inline GeoSample site(const Field& f,float x,float z,bool warm){
    const float mineral_g=mineral(x*26.1f+81,z*22.9f-14),n0=mineral(x*7.2f+13,z*7.78f);
    GeoSample q=f.get(.5f+x/9.6f,.5f+z/9.6f);
    q.h+=.146f*q.mark-.022f*q.rim;
    const float clear=1/std::max(.83f,1-.14f*q.mark+.11f*q.rim);
    q.r*=clear;q.g*=clear;q.b*=clear;
    V p=spin({x-(warm?.043f:.051f),0,z-(warm?.13f:.03f)},warm?-.22f:.46f);
    p.x+=.042f*(n0-.5f);p.z+=.039f*(mineral_g-.5f);
    float sd=2;
    auto toe=[&](V a,V b,float R,float taper){V v=b-a,q=p-a;float a0=cl(dot(v,q)/dot(v,v));sd=union_s(sd,length(q-v*a0)-R*(1-a0*taper),warm?.052f:.081f);};
    if(warm){
        toe({-.06f,0,-.488f},{0,0,.05f},.145f,.05f);
        toe({-.042f,0,-.02f},{-.255f,0,.166f},.104f,.14f);
        toe({-.24f,0,.151f},{-.627f,0,.487f},.105f,.64f);
        toe({.006f,0,.011f},{-.012f,0,.726f},.108f,.28f);
        toe({-.013f,0,.601f},{-.04f,0,.875f},.070f,.76f);
        toe({.039f,0,-.023f},{.306f,0,.207f},.111f,.04f);
        toe({.285f,0,.183f},{.449f,0,.596f},.117f,.67f);
    }else{
        toe({.01f,0,-.458f},{-.049f,0,.04f},.186f,.22f);
        toe({-.10f,0,.013f},{-.43f,0,.397f},.127f,.42f);
        toe({-.034f,0,.019f},{.017f,0,.368f},.143f,.23f);
        toe({.017f,0,.334f},{.111f,0,.762f},.119f,.52f);
        toe({.07f,0,-.016f},{.462f,0,.228f},.157f,.55f);
        toe({.391f,0,.172f},{.546f,0,.315f},.094f,.54f);
    }
    sd+=.025f*(mineral_g-.48f)+.018f*(n0-.49f);
    const float dent=smooth(warm?-.015f:-.038f,warm?.089f:.117f,-sd);
    float wall=expf(-sq((sd-.032f)/(warm?.030f:.042f)))*(.48f+.40f*n0);
    q.h-=dent*(warm?.159f:.132f)*(.87f+.19f*mineral_g);
    q.h+=wall*.025f;q.mark=dent;q.rim=wall;
    return q;
}

struct Outcrop {
    static constexpr int N=194;
    struct Peb { V p,r,c;int k; };
    std::vector<GeoSample> geom;
    std::vector<V> xyz,normal;
    std::vector<Face> triangles=gridfaces(N,N);
    std::vector<Peb> grit;
    Outcrop(const Field& f,bool w):geom(N*N),xyz(N*N),normal(N*N){
        auto curve=[](int i){float u=2*i/float(N-1)-1;return u*(1.28f+3.0f*u*u);};
        #pragma omp parallel for schedule(static)
        for(int q=0;q<N*N;++q){
            float x=curve(q%N),z=curve(q/N);
            float a=mineral(7.67f*x+22,9.25f*z),b=mineral(x*27.3f+55,z*26.77f-9);
            auto p=site(f,x,z,w);
            float cuts=cracks(x*(w?5.2f:7.1f)+56,z*(w?5.3f:5.8f)-12,a);
            float layer=.5f+.5f*sinf((z*(w?33.f:42.f)-8.72f*x)+4*a+2*b+23*p.h);
            float scale=1.32f;float y=p.h*scale+.027f*(a-.5f)+.014f*(b-.5f)+.0077f*layer-.016f*cuts;
            float pat=.74f+.23f*b+.18f*layer+.18f*a-.16f*cuts;
            V base=p.rgb()*pat;
            base=mix(base,w?V{.39f,.195f,.066f}:V{.19f,.227f,.172f},.15f*smooth(.18f,.67f,a));
            if(!w)base=mix(base,V{.124f,.188f,.168f},.27f*smooth(.24f,.80f,b));
            p.r=base.x;p.g=base.y;p.b=base.z;p.h=y;geom[q]=p;xyz[q]={x,y,z};
        }
        #pragma omp parallel for schedule(static)
        for(int q=0;q<N*N;++q){int i=q%N,j=q/N;const int l=j*N+std::max(0,i-1),r=j*N+std::min(N-1,i+1),t=std::max(0,j-1)*N+i,b=std::min(N-1,j+1)*N+i;
            normal[q]=unit(cross(xyz[b]-xyz[t],xyz[r]-xyz[l]));
        }
        for(int k=0;k<152;++k){
            float a=hash(k,w?300:501),b=hash(k,41),x=(a-.5f)*5.75f,z=(b-.5f)*5.7f;
            auto s=site(f,x,z,w);
            if(s.mark>.11f||s.rim>.23f||sq(x*.76f)+sq(z)<.77f)continue;
            float E=.012f+.055f*pow4(hash(k,83));
            V col=s.rgb()*(.78f+.55f*hash(k,129));
            grit.push_back({{x,s.h*1.32f+E*.13f,z},{E*(1.03f+.65f*a),E*.55f,E*(.66f+.58f*b)},col,k});
        }
    }
    void draw(Raster& r,const Tex& tex,float)const{
        std::vector<Vertex> v(geom.size());
        #pragma omp parallel for schedule(static)
        for(size_t i=0;i<geom.size();++i){
            auto s=geom[i];V p=xyz[i];float cavity=cl(s.mark),ao=1-.44f*cavity;
            float puddle=smooth(.41f,.66f,s.rim)*.28f+.13f;
            V al=s.rgb(),col=lit(p,normal[i],r.cam.pos,al,.74f-.19f*puddle,puddle,ao,.95f,1.24f);
            v[i]={p,col,p.x*.78f,p.z*.76f};
        }
        r.mesh(v,triangles,&tex,.81f);
        for(auto p:grit)chip(r,p.p,p.r,p.c,p.k,false);
    }
};

struct Globe {
    static constexpr int S=512;
    struct Tile { std::array<std::vector<GeoSample>,6>a; } now,old;
    static constexpr float p[2][2][2]={{{-6.734270096f,-38.262065887f},{8.291666667f,14.516666667f}},{{-5.942546594f,-5.730008929f},{-5.688025016f,5.056435421f}}};
    static const V sun;
    static V dir(int i,float u,float v){switch(i){case 0:return unit({1,v,u});case 1:return unit({-1,v,u});case 2:return unit({u,1,v});case 3:return unit({u,-1,v});case 4:return unit({u,v,1});default:return unit({u,v,-1});}}
    Globe(const std::string& d){prep(now,Field(d+"/modern.field"));prep(old,Field(d+"/ancient.field"));}
    static void prep(Tile& t,const Field& a){
        for(auto& q:t.a)q.resize(S*S);
        #pragma omp parallel for schedule(static)
        for(int k=0;k<6*S;++k){int f=k/S,y=k%S;
            for(int x=0;x<S;++x)t.a[f][y*S+x]=a.spherical(dir(f,x*(2.f/(S-1))-1,y*(2.f/(S-1))-1));
        }
    }
    static GeoSample get(const Tile& a,V n){
        float x=fabsf(n.x),y=fabsf(n.y),z=fabsf(n.z),u,v;int f;
        if(z>=x&&z>=y){f=n.z>0?4:5;u=n.x/z;v=n.y/z;}
        else if(x>=y){f=n.x>0?0:1;u=n.z/x;v=n.y/x;}
        else{f=n.y>0?2:3;u=n.x/y;v=n.z/y;}
        u=cl((u+1)*(.5f*(S-1)),0,S-1.0001f);v=cl((v+1)*(.5f*(S-1)),0,S-1.0001f);
        int j=int(u),i=int(v);const GeoSample* s=&a.a[f][i*S+j];u-=j;v-=i;
        auto e=[&](float GeoSample::*m){return mix(mix(s[0].*m,s[1].*m,u),mix(s[S].*m,s[S+1].*m,u),v);};
        return {e(&GeoSample::h),e(&GeoSample::r),e(&GeoSample::g),e(&GeoSample::b),e(&GeoSample::dx),e(&GeoSample::dz),e(&GeoSample::mark),e(&GeoSample::rim)};
    }
    V surface(const Tile& m,V n,V dir,bool past,float t)const{
        const auto q=get(m,n);const V ew=unit({n.z,0,-n.x}),ns=cross(n,ew);
        V normal=unit(n-ew*q.dx*.93f+ns*q.dz*.93f);
        float incidence=cl(dot(n,sun)),local=cl(dot(normal,sun)),see=cl(dot(n,-dir)),coast=1-sq(2*cl(q.mark)-1);
        const V al=q.rgb();
        V sea=al*V{.53f,1.09f,1.49f}*(.34f+.71f*incidence)+V{.0013f,.0065f,.020f};
        float gloss=pow4(pow4(cl(dot(bounce(dir,n),sun))));
        sea+=V{.10f,.165f,.194f}*(gloss*.85f);
        float height=smooth(.01f,.21f,q.h);
        V land=al*(past?V{1.38f,1.085f,.718f}:V{1.08f,1.12f,.80f});
        land=mix(land,past?V{.415f,.261f,.115f}:V{.288f,.246f,.144f},.14f+.32f*height);
        land=land*(V{.27f,.36f,.46f}+V{1.16f,1.04f,.78f}*(.19f*incidence+.77f*local));
        V c=mix(sea,land,cl(q.mark))+V{.014f,.057f,.050f}*(sq(coast)*(.34f+.66f*incidence));
        if(!past&&see>.19f){
            float a=n.x*18.5f+n.z*4.46f+.012f*t,b=n.y*22.42f-n.z*6.51f;
            float clouds=smooth(.588f,.84f,mineral(a,b));
            c=mix(c,V{.53f,.62f,.63f},clouds*.16f*(.29f+.71f*incidence));
        }
        float limb=pow4(1-see),term=.27f+.73f*incidence;
        c+=V{.033f,.105f,.196f}*(limb*term);
        return mix(c,V{.027f,.102f,.196f}*term,1-smooth(0,.041f,see));
    }
    void image(Raster& r,float t,float reveal,std::array<V,4>& pins)const{
        // One continuous camera, two real, independently sourced epochs.
        float h=quint((t-16.70f)/10.3f),push=quint((t-21.64f)/5.39f),lat=mix(6.8f,1.5f,h),lon=mix(-16.6f,-11.9f,h);
        V pos=geo(lat,lon)*mix(4.08f,3.82f,push),z=unit(pos),ax=unit(cross(-z,{0,1,0})),up=cross(ax,-z);
        Cam c(pos,-up*.051f+ax*.047f,55.f,float(r.w)/r.h,mix(.045f,-.042f,h));
        image(r,t,reveal,pins,c,false);
    }
    void image(Raster& r,float t,float reveal,std::array<V,4>& pins,const Cam& c,bool atlas)const{
        r.begin(c);const V pos=c.pos;
        const float d0=dot(pos,pos);V plane=unit({.96f,.28f,.032f});
        #pragma omp parallel for schedule(static)
        for(int j=0;j<r.h;++j)for(int i=0;i<r.w;++i){
            float u=(i+.5f)/r.w,v=(j+.5f)/r.h;
            V rd=c.ray(u,v);float b=dot(pos,rd),q=1-d0+b*b;
            float edge=cl(.96f-.53f*sq(2*u-1)-.45f*sq(2*v-1));V out;
            if(q<0){
                float halo=1/(1+(-q)*15.f);halo=halo*halo*halo*halo;
                float sunlight=.25f+.75f*cl(dot(unit(pos-rd*b),sun));
                float speck=hash(i,j)>.99983f?hash(j,i+7)*.029f:0;
                out=V{.0031f,.0086f,.019f}+V{.005f,.014f,.022f}*edge*edge+V{.052f,.184f,.377f}*(halo*sunlight)+V{speck,speck,speck};
            }else{
                V n=unit(pos+rd*(-b-sqrtf(q)));
                float sweep=dot(n,plane)-mix(1.07f,-1.07f,reveal);
                float v0=reveal==0?0:reveal==1?1:smooth(-.02f,.024f,sweep);
                if(v0<.9999f)out=surface(now,n,rd,false,t);
                if(v0>0){V b0=surface(old,n,rd,true,t);out=v0>=.9999f?b0:mix(out,b0,v0);}
                if(atlas){
                    // Faint engraved latitude/longitude; map coordinates, not a connection diagram.
                    const float yh=asinf(cl(n.y,-1.f,1.f))*6.3661977f,xh=atan2f(n.x,n.z)*6.3661977f;
                    const float grid=1-smooth(.007f,.028f,std::min(fabsf(yh-roundf(yh)),fabsf(xh-roundf(xh))));
                    out+=V{.033f,.077f,.074f}*(grid*(.17f+.56f*cl(-dot(rd,n))));
                }
                if(reveal>0&&reveal<1){
                    float ring=1-smooth(.004f,.028f,fabsf(sweep));out+=V{.070f,.218f,.184f}*(ring*.90f);
                    if(atlas){float detail=1-smooth(.0015f,.0065f,fabsf(sweep));
                        out+=V{.20f,.28f,.134f}*detail*cl(.19f+3.2f*reveal)*cl(.19f+3.2f*(1-reveal));}
                }
            }
            r.poke(j*r.w+i,film.grade(out*(.92f+.08f*edge),1.06f));
        }
        for(int e=0;e<2;++e)for(int j=0;j<2;++j){const auto* a=p[e][j];V G=geo(a[0],a[1]);pins[e*2+j]=c.project(G*1.0015f);if(dot(G,pos-G)<=0)pins[e*2+j].z=-1;}
    }
};
inline const V Globe::sun=unit({-.39f,.54f,.95f});

// A weathered bed with original sloping laminations on a genuine exposed
// cutface. The top retains the old footprint; the sides reveal separate beds.
inline void stratigraphy(Raster& r,const Field& f,const Tex& tex,float t){
    constexpr int X=196,Y=116;
    const float A=-2.83f,B=2.83f;
    auto top=[&](float x,float z){auto q=site(f,x,z,true);
        return .16f+1.26f*q.h+.018f*sinf(x*13+z*27)+.075f*smooth(.20f,1.26f,fabsf(x));};
    auto edge=[](float x){return 1.18f+.044f*sinf(3.31f*x)+.013f*sinf(9.7f*x+2.3f)+.0091f*sinf(22*x-2);};
    std::vector<Vertex> v(X*Y);
    #pragma omp parallel for schedule(static)
    for(int j=0;j<Y;++j)for(int i=0;i<X;++i){float u=i/float(X-1),s=j/float(Y-1),x=mix(A,B,u),z=mix(-4.51f,edge(x),s),y=top(x,z);
        auto q=f.get(.5f+x/9.6f,.5f+z/9.6f);V p={x,y,z};V n=unit({-.97f*q.dx,1,-.97f*q.dz});
        V base=mix(q.rgb(),{.348f,.192f,.092f},.28f);v[j*X+i]={p,lit(p,n,r.cam.pos,base,.79f,.14f,1-.36f*q.mark,1,1.04f),x*.72f,z*.72f};}
    r.mesh(v,gridfaces(X,Y),&tex,.41f);
    constexpr int H=180;v.resize(X*H);
    auto position=[&](float x,float a){
        const float g=mineral(x*6.2f,-19*a+x*.42f);const float bed=a+.027f*sinf(1.91f*x+.72f*a);
        const float step=(.036f+.03f*g)*sinf(53.7f*bed+.91f*g)*smooth(0,.13f,a);
        const float z=edge(x)*(1-.10f*a)+step+.19f*a+.099f*(g-.5f)*smooth(0,.09f,a);
        const float y=top(x,edge(x))*(1-.72f*smooth(0,.6f,a))-a*(3.44f+.063f*sinf(x*2.1f));return V{x,y,z};};
    #pragma omp parallel for schedule(static)
    for(int j=0;j<H;++j)for(int i=0;i<X;++i){float x=mix(A,B,i/float(X-1)),a=j/float(H-1);V p=position(x,a);
        V U=position(x+.006f,a)-position(x-.006f,a),D=position(x,a+.002f)-position(x,a-.002f);
        V n=unit(cross(D,U));
        float n0=mineral(7.7f*x,21.9f*a),n1=mineral(15.3f*x+33,57*a+4);
        float bed=a+.020f*sinf(x*1.54f+.75f*a)+.009f*(n0-.50f);
        float bands=.5f+.5f*cosf(114.2f*bed+1.1f*n0),fine=.5f+.5f*sinf(339.f*bed+1.3f*n1);
        float strip=.95f*expf(-sq((bed-.17f)/.036f))+.87f*expf(-sq((bed-.37f)/.037f))+.58f*expf(-sq((bed-.65f)/.093f));
        V tone=mix({.289f,.195f,.115f},{.111f,.134f,.128f},cl(strip*(.75f+.37f*n0)));
        tone=tone*(.72f+.29f*fine+.24f*bands+.14f*n1)*(1-.36f*pow4(1-bands));
        // In a grazing cutaway, a soft north fill lifts the vertical face.
        V col=lit(p,n,r.cam.pos,tone*1.29f,.86f-.12f*bands,.15f,.86f+.12f*bands,1,1.13f);
        v[j*X+i]={p,col,x*.83f,(p.y+.027f*p.z)*.74f};}
    r.mesh(v,gridfaces(X,H),&tex,.85f);
    // A few detaching silt chips continue the motion below the upper lip.
    for(int i=0;i<18;++i){float s=t-14.f/30.f-(i==0?0:.96f*hash(i,971));if(s<0||s>.89f)continue;
        float x=i==0?-.21f:(hash(i,918)-.50f)*2.f,dd=.019f+.032f*sq(hash(i,37)),a=s*s*.91f;
        V p=position(x,a)+V{.05f*s,0,.015f+.24f*s};
        chip(r,p,{dd,dd*.55f,dd*.77f},{.223f,.145f,.081f},i+19,false);}
}
}
