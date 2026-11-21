#pragma once
#include "portrait.hpp"
#include <unordered_map>

namespace portrait {
inline const V key=unit({-.72f,.66f,.35f});
inline const V amber{1.24f,1.06f,.81f},skylight{.225f,.291f,.338f};

// Diffuse + a bounded GGX dielectric lobe. Wetness changes roughness and
// reflectance independently of the geometric amount of sediment displaced.
inline V lit(V p,V N,V eye,V base,float rough,float wet,float ao,float sun,float exposure=1){
    V n=unit(N),v=unit(eye-p),h=unit(key+v);
    float nl=cl(dot(n,key)),nv=cl(dot(n,v),.065f,1),nh=cl(dot(n,h)),vh=cl(dot(v,h));
    float b=rough*rough,a2=b*b,d=a2/(PI*sq(nh*nh*(a2-1)+1));
    float k=sq(rough+1)*.125f,g=(nl/(nl*(1-k)+k))*(nv/(nv*(1-k)+k));
    float f0=mix(.030f,.060f,wet),f=f0+(1-f0)*pow4(1-vh)*(1-vh);
    float spec=cl(d*g*f/(4*std::max(.12f,nl)*nv),0,1.15f);
    float rim=pow4(1-nv),fill=.64f+.36f*cl(n.y);
    const V c=base*(skylight*(ao*fill)+amber*(1.18f*nl*sun))*ao
        +amber*(spec*nl*sun*(.85f+wet*.29f))+V{.032f,.062f,.079f}*(rim*(.17f+.66f*wet)*ao);
    return film.grade(c,exposure);
}

struct Blob {
    V c,side,u,axis,r;
    Blob(V a,V b,float w,float h,float extra):c((a+b)*.5f),axis(unit(b-a)),r{w,h,length(b-a)*.5f+extra}{
        side=unit(cross(axis,{0,1,.017f}));u=cross(side,axis);
    }
    float sdf(V p)const{p=p-c;V q{dot(p,side)/r.x,dot(p,u)/r.y,dot(p,axis)/r.z};return (length(q)-1)*std::min({r.x,r.y,r.z});}
};
inline float union_s(float a,float b,float k){float h=cl(.5f+.5f*(b-a)/k);return mix(b,a,h)-k*h*(1-h);}

struct Foot {
    std::vector<Blob> skin,claw;
    std::vector<std::pair<V,V>> sole;
    std::vector<float> widths;
    struct BoneVert{V p,n;float claw,scale;};
    std::vector<BoneVert> orig;
    std::vector<Face> faces;
    Foot(){
        auto b=[&](V a,V c,float rx,float ry,float fall){skin.emplace_back(a,c,rx,ry,fall);};
        b({-.24f,3.58f,-.96f},{-.13f,2.14f,-.74f},.263f,.251f,.263f);
        b({-.16f,2.39f,-.79f},{-.087f,1.08f,-.58f},.218f,.200f,.205f);
        b({-.087f,1.14f,-.59f},{-.024f,.344f,-.394f},.163f,.176f,.195f);
        b({-.026f,.38f,-.41f},{0,.195f,-.273f},.205f,.17f,.148f);
        b({0,.160f,-.327f},{0,.126f,.10f},.246f,.153f,.114f);
        sole.push_back({{0,0,-.314f},{0,0,.09f}});widths.push_back(.218f);
        const V a[]={{-.132f,.133f,-.03f},{.002f,.140f,.017f},{.146f,.131f,-.02f}};
        const V mid[]={{-.374f,.108f,.284f},{.024f,.108f,.402f},{.369f,.101f,.214f}};
        const V end[]={{-.643f,.080f,.55f},{.036f,.075f,.79f},{.610f,.078f,.465f}};
        const V tip[]={{-.764f,.015f,.612f},{.060f,.022f,1.005f},{.716f,.016f,.552f}};
        for(int i=0;i<3;++i){
            float r=i==1?.122f:.103f;
            b(a[i],mid[i],r,.108f,.079f);b(mid[i],end[i],r*.77f,.078f,.053f);
            V q=mix(end[i],tip[i],.36f);b(mix(mid[i],end[i],.87f),q,r*.585f,.056f,.029f);
            claw.emplace_back(mix(mid[i],end[i],.93f),mix(end[i],tip[i],.64f),r*.51f,.048f,.026f);
            claw.emplace_back(mix(end[i],tip[i],.53f),tip[i],r*.285f,.025f,.014f);
            sole.push_back({a[i],mid[i]});widths.push_back(r*.98f);
            sole.push_back({mid[i],end[i]});widths.push_back(r*.748f);
            sole.push_back({end[i],tip[i]});widths.push_back(r*.435f);
        }
        build();
    }
    float print(float x,float z)const{
        float d=3;
        for(size_t i=0;i<sole.size();i++){
            V a=sole[i].first,b=sole[i].second;V v={b.x-a.x,0,b.z-a.z},q={x-a.x,0,z-a.z};
            float u=cl(dot(v,q)/dot(v,v));q=q-v*u;
            float w=widths[i]*(1-.16f*u);
            d=union_s(d,length(q)-w,.039f);
        }
        return d;
    }
    float surface(V p,float* nail=nullptr)const{
        float a=4,b=4;
        for(const auto& e:skin)a=union_s(a,e.sdf(p),.049f);
        for(const auto& e:claw)b=std::min(b,e.sdf(p));
        if(nail)*nail=smooth(-.018f,.038f,a-b);
        return union_s(a,b,.019f);
    }
    void build(){
        // Marching tetrahedra, sharing every interpolated edge. The leg and toes
        // are one watertight isosurface instead of overlapping visible capsules.
        constexpr int X=81,Y=183,Z=94;constexpr float D=.024f;
        const V o={-.972f,-.192f,-1.161f};
        std::vector<float> v(X*Y*Z);
        auto point=[&](int k){return o+V{float(k%X),float((k/X)%Y),float(k/(X*Y))}*D;};
        #pragma omp parallel for schedule(static)
        for(int i=0;i<int(v.size());++i)v[i]=surface(point(i));
        std::unordered_map<uint64_t,int> edges;edges.reserve(58000);
        auto edge=[&](int a,int b){
            if(a>b)std::swap(a,b);
            uint64_t id=(uint64_t(a)<<32)|uint32_t(b);
            auto it=edges.find(id);if(it!=edges.end())return it->second;
            V p=mix(point(a),point(b),cl(v[a]/(v[a]-v[b])));constexpr float d=.0024f;
            float c;surface(p,&c);
            V n=unit({surface(p+V{d,0,0})-surface(p-V{d,0,0}),surface(p+V{0,d,0})-surface(p-V{0,d,0}),surface(p+V{0,0,d})-surface(p-V{0,0,d})});
            float l=.78f+.33f*mineral(p.x*8.1f+p.y*1.74f,p.z*6.9f-p.y*2.3f);
            const int i=int(orig.size());orig.push_back({p,n,c,l});edges.emplace(id,i);return i;
        };
        auto face=[&](int a,int b,int c){if(dot(cross(orig[b].p-orig[a].p,orig[c].p-orig[a].p),orig[a].n+orig[b].n+orig[c].n)<0)std::swap(b,c);faces.push_back({a,b,c});};
        constexpr int tets[6][4]={{0,1,3,7},{0,3,2,7},{0,2,6,7},{0,6,4,7},{0,4,5,7},{0,5,1,7}};
        for(int k=0;k<Z-1;++k)for(int j=0;j<Y-1;++j)for(int i=0;i<X-1;++i){
            int a=(k*Y+j)*X+i;int cube[]={a,a+1,a+X,a+X+1,a+X*Y,a+X*Y+1,a+X*Y+X,a+X*Y+X+1};
            int signs=0;for(int x:cube)signs+=int(v[x]<0);if(signs==0||signs==8)continue;
            for(auto t:tets){int in[4],out[4],n=0,m=0;for(int j0=0;j0<4;++j0){int p=cube[t[j0]];if(v[p]<0)in[n++]=p;else out[m++]=p;}
                if(n==1)face(edge(in[0],out[0]),edge(in[0],out[1]),edge(in[0],out[2]));
                else if(n==3)face(edge(out[0],in[0]),edge(out[0],in[1]),edge(out[0],in[2]));
                else if(n==2){int p=edge(in[0],out[0]),q=edge(in[0],out[1]),r=edge(in[1],out[0]),s=edge(in[1],out[1]);face(p,q,s);face(p,s,r);}
            }
        }
    }
};

struct Motion {
    float t,contact,release,press,lift,slump,y,pitch,x,z;
    bool wet;
    Motion(float local,bool soft,bool hero):t(local),contact(hero?.16666667f:.33333333f),release(hero?.90f:1.1333333f),wet(soft){
        const float a=cl((t-(contact-.29f))/.29f),travel=a*a*(2.08f-1.08f*a);
        const float w=cl((t-contact)/.25f),D=wet?.171f:.157f;
        const float compression=D*ease(w)+.25f*1.52f*w*sq(1-w);
        float load=smooth(contact,contact+.275f,t);
        lift=smooth(release,release+.80f,t);press=load;
        // Foot-tip contact first, heel follows. The heel rolls up first on exit;
        // lateral travel resumes only after the toes have cleared the bed.
        y=mix(.513f,.034f,travel)-compression+(2.46f+(wet?.03f:0))*lift;
        pitch=.094f*(1-travel)+.026f*(1-lift)+.017f*load-.055f*lift+.37f*smooth(release,release+.33f,t)*(1-lift);
        x=-.115f*(1-travel)+.27f*smooth(release+.31f,release+1.02f,t);
        z=-.118f*(1-travel)-.27f*smooth(release+.24f,release+.95f,t);
        slump=wet?mix(.80f*smooth(release+.33f,release+.92f,t),1.f,smooth(release+.88f,release+1.45f,t)):0;
        // The last moist bank fails well after the first toe releases. The
        // continuous close-up observes it rather than restarting the stamp.
        if(wet&&!hero)slump=.84f*slump+.16f*smooth(4.38f,4.93f,t);
    }
    V turn(V p)const{float c=cosf(pitch),s=sinf(pitch);return{p.x,c*p.y-s*p.z,s*p.y+c*p.z};}
    V pose(V p)const{
        const float side=cl(.5f+p.x),bias=.043f*side;
        float flex=smooth(.088f,.94f-.15f*fabsf(p.x),p.z),curl=.121f*smooth(release+.046f+bias,release+.41f+bias,t)*(1-lift);
        p.x+=p.x*.033f*flex*(smooth(contact,contact+.21f,t)*(1-lift));
        p.y-=curl*flex;p.z-=curl*flex*flex*.40f;
        return turn(p)+V{x,y,z};
    }
};

struct Shadow {
    static constexpr int N=544;static constexpr float Z=7.8f;
    V a=unit(cross(key,{0,1,0})),b=unit(cross(key,a));
    std::vector<float> z;
    Shadow():z(N*N,-20.f){}
    V pr(V v)const{return{(dot(v,a)/Z+.50f)*N,(dot(v,b)/Z+.50f)*N,dot(v,key)};}
    template<class F> void build(const Foot& foot,F fn){
        std::vector<V> p(foot.orig.size());
        for(size_t i=0;i<p.size();++i)p[i]=pr(fn(foot.orig[i].p));
        for(auto f:foot.faces){
            V A=p[f[0]],B=p[f[1]],C=p[f[2]];float area=(B.y-C.y)*(A.x-C.x)+(C.x-B.x)*(A.y-C.y);if(fabsf(area)<.028f)continue;
            int x0=std::max(0,int(floorf(std::min({A.x,B.x,C.x})))),x1=std::min(N-1,int(ceilf(std::max({A.x,B.x,C.x}))));
            int y0=std::max(0,int(floorf(std::min({A.y,B.y,C.y})))),y1=std::min(N-1,int(ceilf(std::max({A.y,B.y,C.y}))));
            for(int y=y0;y<=y1;++y)for(int x=x0;x<=x1;++x){
                float u=((B.y-C.y)*(x+.5f-C.x)+(C.x-B.x)*(y+.5f-C.y))/area,v=((C.y-A.y)*(x+.5f-C.x)+(A.x-C.x)*(y+.5f-C.y))/area;
                if(u>=0&&v>=0&&u+v<=1){float d=C.z+u*(A.z-C.z)+v*(B.z-C.z);z[y*N+x]=std::max(z[y*N+x],d);}
            }
        }
    }
    float cast(V p,float softness)const{
        auto v=pr(p);int x=int(v.x),y=int(v.y);if(x<7||x>=N-7||y<7||y>=N-7)return 1;
        const int k=y*N+x;float d=v.z+.017f,dist=std::max(0.f,z[k]-d);
        const int a=int(cl(softness+dist*1.36f,1,6)),b=a*N;
        float s0=(z[k]<=d?2.f:0.f)+float(int(z[k+a]<=d)+int(z[k-a]<=d)+int(z[k+b]<=d)+int(z[k-b]<=d));
        s0+=.67f*float(int(z[k+a+b]<=d)+int(z[k+a-b]<=d)+int(z[k-a+b]<=d)+int(z[k-a-b]<=d));
        return 1-(.69f-.20f*smooth(.41f,3.40f,dist))*(1-s0/8.68f);
    }
};

inline float cracks(float x,float z,float grain){
    x+=.27f*grain;z-=.18f*grain;int X=int(floorf(x)),Z=int(floorf(z));float a=20,b=20;
    for(int j=-1;j<=1;++j)for(int i=-1;i<=1;++i){int u=X+i,v=Z+j;float d=sq(u+.22f+.56f*hash(u,v)-x)+sq(v+.22f+.56f*hash(u+305,v-31)-z);if(d<a){b=a;a=d;}else if(d<b)b=d;}
    return 1-smooth(.004f,.062f,b-a);
}

struct Sediment {
    static constexpr int G=203;
    struct Cell {float base,dent,settle,lift;V mud;float cr,wet;};
    std::vector<Cell> s;std::vector<float> ax,az,mesh_y;
    std::vector<Face> faces=gridfaces(G,G);
    bool wet;
    double relaxation_relative_error=0;
    Sediment(const Foot& foot,bool soft):s(G*G),ax(G),az(G),mesh_y(G*G),wet(soft){
        for(int i=0;i<G;i++){float q=2*i/float(G-1)-1;ax[i]=q*(1.11f+3.73f*q*q+7.6f*sq(q*q)*q*q);az[i]=.11f+q*(1.29f+4.17f*q*q+9.12f*sq(q*q)*q*q);}
        std::vector<float> neg(G*G),rim(G*G),area(G*G);
        double bite=0,line=0;
        #pragma omp parallel for schedule(static) reduction(+:bite,line)
        for(int j=0;j<G;++j)for(int i=0;i<G;++i){
            const int k=j*G+i;const float x=ax[i],z=az[j];
            float g=mineral(x*3.3f+28,z*4.2f-1.3f),q=mineral(x*15.6f+3,z*16.3f-11),r=noise(x*59,z*54);
            float d=foot.print(x,z),clear=smooth(-.085f,.29f,d);
            float fracture=soft?.17f*cracks(x*4.4f+5,z*6.7f,g):cracks(x*6.35f+4,z*6.14f-2,g);
            fracture*=.62f+.38f*q;
            float rib=.50f+.50f*sinf(z*34+x*8+2.1f*g+.4f*q);
            float h=.063f*(g-.50f)+.016f*(q-.5f)+.006f*(r-.5f)-.030f*fracture+(.016f*sq(rib))*(.24f+.76f*clear);
            h+=.022f*sinf(x*.77f+z*.64f)+.009f*x;
            h*=.52f+.48f*clear;
            float f=(.63f*smooth(.004f,.113f,-d)+.37f*smooth(-.002f,.038f,-d));
            neg[k]=-.171f*f*(.87f+.13f*q);
            rim[k]=expf(-sq((d-.027f)/(.037f+.013f*g)))*(.68f+.61f*q)*smooth(-.018f,.024f,d);
            // Integrate using the non-uniform mesh cell area.
            float a=cell_area(i,j);area[k]=a;bite-=a*neg[k];line+=a*rim[k];
            V base=mix(soft?V{.076f,.067f,.046f}:V{.155f,.083f,.040f},soft?V{.271f,.185f,.102f}:V{.39f,.251f,.118f},cl(.33f+.46f*g+.24f*q));
            base=mix(base,soft?V{.084f,.116f,.104f}:V{.383f,.288f,.171f},soft?.22f*smooth(.44f,.68f,g):.20f*rib);
            base=base*(1-.33f*fracture)*( .82f+.27f*q );
            s[k]={h,neg[k],0,0,base,fracture,soft?cl(.63f+.35f*g+.19f*rib):.08f+.20f*g};
        }
        // Some volume is compacted; the remainder forms a raised contact rim.
        // The slump solver below transfers material pairwise without creating it.
        float rscale=float((soft?.57:.43)*bite/line);
        std::vector<float> mass(G*G);double in=0;
        for(int i=0;i<G*G;++i){s[i].lift=rim[i]*rscale;s[i].dent+=s[i].lift;mass[i]=s[i].dent;in+=mass[i]*area[i];}
        if(soft){
            std::vector<float> flow(G*G);
            for(int it=0;it<94;++it){
                std::fill(flow.begin(),flow.end(),0);
                for(int j=1;j<G-2;j++)for(int i=1;i<G-2;i++){
                    int k=j*G+i;if(ax[i]<-1.12f||ax[i]>1.12f||az[j]<-.68f||az[j]>1.31f)continue;
                    auto flux=[&](int l,float width){
                        float h=(s[k].base+mass[k])-(s[l].base+mass[l]);
                        // Cohesion: no flow at small gradients; soft oversteep toe
                        // edges feed the depression when the stamp no longer holds them.
                        float side=1+.50f*smooth(.07f,.72f,-ax[i])*smooth(0,.51f,az[j]);
                        float delta=cl(fabsf(h)-width*.11f,0.f,.083f),weight=.123f*std::min(area[k],area[l])*side;
                        float v=std::copysign(delta*weight,h);flow[k]-=v;flow[l]+=v;
                    };
                    flux(k+1,ax[i+1]-ax[i]);flux(k+G,az[j+1]-az[j]);
                }
                for(int n=0;n<G*G;++n)mass[n]+=flow[n]/area[n];
            }
            double out=0;
            for(int i=0;i<G*G;++i){s[i].settle=mass[i]-s[i].dent;out+=mass[i]*area[i];}
            relaxation_relative_error=std::abs(out-in)/std::max(1e-5,std::abs(in));
            if(relaxation_relative_error>.001)throw std::runtime_error("sediment mass balance failed");
        }
    }
    float cell_area(int i,int j)const{return (ax[std::min(G-1,i+1)]-ax[std::max(0,i-1)])*(az[std::min(G-1,j+1)]-az[std::max(0,j-1)])*.25f;}
    float surface(float x,float z,const Motion& m)const{
        int i=int(std::lower_bound(ax.begin(),ax.end(),x)-ax.begin()),j=int(std::lower_bound(az.begin(),az.end(),z)-az.begin());
        i=std::clamp(i,1,G-1);j=std::clamp(j,1,G-1);
        float u=cl((x-ax[i-1])/(ax[i]-ax[i-1])),v=cl((z-az[j-1])/(az[j]-az[j-1]));
        const auto h=[&](int k){return s[k].base+m.press*s[k].dent+m.slump*s[k].settle;};
        return mix(mix(h((j-1)*G+i-1),h((j-1)*G+i),u),mix(h(j*G+i-1),h(j*G+i),u),v);
    }
    void draw(Raster& r,const Motion& m,const Tex& tex,const Shadow* cast,V cam){
        std::vector<Vertex> mesh(G*G);
        #pragma omp parallel for schedule(static)
        for(int k=0;k<G*G;++k)mesh_y[k]=s[k].base+m.press*s[k].dent+m.slump*s[k].settle;
        #pragma omp parallel for schedule(static)
        for(int j=0;j<G;++j)for(int i=0;i<G;++i){
            int k=j*G+i,l=std::max(0,i-1),t=std::min(G-1,i+1),d=std::max(0,j-1),u=std::min(G-1,j+1);
            V p={ax[i],mesh_y[k],az[j]};
            V n={(mesh_y[j*G+l]-mesh_y[j*G+t])/(ax[t]-ax[l]),1,(mesh_y[d*G+i]-mesh_y[u*G+i])/(az[u]-az[d])};
            float light=cast?mix(cast->cast(p,1.15f+2.1f*m.lift),1,smooth(.68f,1.f,m.lift)):1;
            float bowl=cl(-s[k].dent*6.f*m.press),oc=1-.40f*bowl-.080f*s[k].cr;
            float fresh=cl(m.press*(bowl*.66f+s[k].lift*4.1f)+8.f*m.slump*std::max(0.f,s[k].settle));
            float sheen=wet?smooth(.09f,.27f,s[k].base+.16f*s[k].wet+.09f*s[k].lift):0;
            float w=cl(s[k].wet+.32f*fresh+.15f*sheen),rough=mix(.85f,.285f,w);
            V al=s[k].mud*(1-(wet?.37f:.21f)*fresh)*(wet?.68f:1.06f);
            al=mix(al,wet?V{.076f,.051f,.034f}:V{.203f,.115f,.053f},.20f*fresh);
            // Low, broad sheen on freshly exposed soft edges without plastic white.
            V c=lit(p,n,cam,al,rough,w,oc,light,1.12f);
            mesh[k]={p,c,p.x*.78f,p.z*.77f};
        }
        r.mesh(mesh,faces,&tex,wet?.39f:.98f);
    }
};

inline void skin(Raster& r,const Foot& f,const Motion& m,const Tex& tex){
    std::vector<Vertex> mesh(f.orig.size());
    #pragma omp parallel for schedule(static)
    for(size_t i=0;i<mesh.size();i++){
        const auto& v=f.orig[i];V p=m.pose(v.p),n=m.turn(v.n);
        float underside=smooth(.03f,.31f,v.p.y),mud=(1-underside)*m.press;
        float noise=v.scale;
        V base=mix({.039f,.047f,.031f},{.142f,.139f,.088f},cl(.46f+(noise-.79f)*2.0f+.17f*cl(n.y)));
        base=mix(base,V{.165f,.092f,.047f},.23f*smooth(.98f,1.08f,noise));
        // Transitions in the keratin claws stay fixed on the articulated mesh.
        base=mix(mix(base,{.161f,.079f,.035f},mud*.77f),V{.025f,.019f,.016f}*(.79f+.42f*noise),v.claw*.95f);
        float ao=1-.29f*m.press*expf(-std::max(0.f,p.y+.09f)*8.f);
        V c=lit(p,n,r.cam.pos,base,.56f-.27f*mud,.21f+.61f*mud,ao,1,1.27f);
        // Triplanar material coordinates are in the bind pose. Scales
        // follow the limb without stretching down the curved sides of a toe.
        V w={pow4(v.n.x),pow4(v.n.y),pow4(v.n.z)};w=w/(w.x+w.y+w.z);
        mesh[i]={p,c,v.p.x*.78f,v.p.y*.85f,v.p.z*.77f,w};
    }
    // Exclude triangles facing away before projection; the shape remains fully 3D.
    std::vector<Face> faces;faces.reserve(f.faces.size()/2);
    for(auto k:f.faces){const auto &a=mesh[k[0]].p,&b=mesh[k[1]].p,&c=mesh[k[2]].p;if(dot(cross(b-a,c-a),r.cam.pos-a)>-.000003f)faces.push_back(k);}
    r.mesh(mesh,faces,&tex,-1.20f);
}

inline void chip(Raster& r,V p,V radii,V base,int tag,bool mud){
    // Closed jagged solid, not a 2D particle. A separate foreground can cross
    // and correctly occlude the rear toe, then return to the shot's bed.
    constexpr int U=7,T=4;
    std::array<P,(U+1)*(T+1)> v{};
    for(int j=0;j<=T;++j)for(int i=0;i<=U;++i){
        float a=i*2*PI/U,b=(j/float(T)-.5f)*PI,f=.82f+.29f*hash(tag+i%U,173+j);
        V n={cosf(a)*cosf(b),sinf(b),sinf(a)*cosf(b)};V e=p+n*radii*f;
        v[j*(U+1)+i]=r.proj({e,lit(e,n,r.cam.pos,base,.68f-.30f*int(mud),mud?.68f:.17f,.96f,1.f,1.10f)});
    }
    for(int j=0;j<T;++j)for(int i=0;i<U;++i){int k=j*(U+1)+i;r.tri(v[k],v[k+1],v[k+U+2]);r.tri(v[k],v[k+U+2],v[k+U+1]);}
}

inline void particles(Raster& r,const Motion& m,int seed){
    float t=m.t-m.contact;if(t<0||t>.69f)return;
    for(int i=0;i<(m.wet?78:46);++i){
        float a=hash(i,seed+28)*2*PI,delay=hash(i,seed+9)*.138f;
        float dt=t-delay;if(dt<0)continue;
        float speed=.19f+.84f*sq(hash(i,seed+77)),rise=.43f+1.39f*sq(hash(i,seed+51));
        float y=rise*dt-3.36f*dt*dt;if(y<.0f)continue;
        float u=cosf(a),v=sinf(a),e=.0084f+.0125f*sq(hash(i,seed+81));
        V p={u*(.37f+speed*dt)+.018f,y-.015f,.22f+v*(.43f+speed*.82f*dt)};
        chip(r,p,{e*1.08f,e*.61f,e*.71f},m.wet?V{.213f,.140f,.073f}:V{.295f,.180f,.081f},i+29*seed,m.wet);
    }
}
}
