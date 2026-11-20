// The investigation cut: evidence-sized macro sets and staged proof beats.
#pragma once
#include "atlas.hpp"

namespace evidence {
struct CutSet : Studio {
    Atlas atlas;
    Raster half;
    std::vector<uint8_t> left;
    int shot=0;
    CutSet(const std::string& path,int w,int h):Studio(path,w,h),half(w/2,h),left(size_t(w/2)*h*3){}
    float sec()const{return (f-TAKES[shot].a)/24.f;}
    void view(V p,V a,float angle,int room=0,float roll=0){g.begin(Camera(p,a,angle,g.w/float(g.h),roll),room,t);}
    float here(float a,float b)const{return ramp(a,b,sec());}
    void save_half(){left=half.rgb;}
    void pair_out(){
        for(int y=0;y<g.h;y++){
            auto* d=&g.rgb[3*y*g.w];
            std::memcpy(d,&left[3*y*half.w],3*half.w);
            std::memcpy(d+3*half.w,&half.rgb[3*y*half.w],3*half.w);
        }
    }

    void relief(const Grid& m,float extent,V position,float lift=0,float contrast=1,bool wet=false){
        const auto& tex0=tex(m);
        g.lattice(116,108,[&](float u,float v){
            auto side=[&](float s){float q=2*s-1;return extent*(.68f*q+.32f*q*q*q);};
            float X=side(u),Z=side(v);auto a=Grid::all(m.local(X,Z));
            float h=m.height(X,Z,lift)*1.28f;
            float shade=(.98f+.13f*expf(-.10f*(sq(X-.55f)+sq(Z+.55f)))-.22f*sq(a.m)*(1-lift*.87f))*contrast;
            const float spill=wet?.069f*ramp(.35f,.83f,a.k)*(.63f+.37f*sinf(X*17+Z*23+t*2)):0;
            return Node{{X+position.x,h+position.y,Z+position.z},V{shade+spill,shade+spill*1.28f,shade+spill*1.40f},Grid::mirror(X/m.span+.5f),Grid::mirror(Z/m.span+.5f)};
        },&tex0);
    }

    void contour(const Grid& b,V c,float decay,V color,float alpha=1,float sx=1,float sz=1,float dy=.013f){
        // Trace the actual procedural signed-depth mask, not a drawn footprint glyph.
        if(alpha<.004f)return;
        constexpr int n=48;constexpr float E=1.25f;const float d=2*E/n;float v[n+1][n+1];
        auto P=[&](float x,float z){return V{c.x+x*sx,c.y+b.height(x,z)*1.28f+dy,c.z+z*sz};};
        for(int z=0;z<=n;z++)for(int x=0;x<=n;x++)v[z][x]=Grid::take(b.local(x*d-E,z*d-E),&Sample::m)-decay;
        for(int j=0;j<n;j++)for(int i=0;i<n;i++){
            float vals[4]={v[j][i],v[j][i+1],v[j+1][i+1],v[j+1][i]};
            float x=i*d-E,z=j*d-E,px[4]={x,x+d,x+d,x},pz[4]={z,z,z+d,z+d};
            V p[4];int k=0;
            for(int a=0;a<4;a++){int r=(a+1)&3;if((vals[a]>=0)==(vals[r]>=0))continue;float q=vals[a]/(vals[a]-vals[r]);p[k++]=P(lerp(px[a],px[r],q),lerp(pz[a],pz[r],q));}
            if(k>=2)g.line(p[0],p[1],color,alpha,2.12f);
            if(k==4)g.line(p[2],p[3],color,alpha,1.94f);
        }
    }

    void open_macro(bool koum,float u){
        auto& field0=koum?earth.koum:earth.brazil;
        const float lift=.18f*(1-u),split=g.w*16<g.h*20;
        const V p=split?V{.13f+.08f*u,3.48f,-.80f}:V{-.16f+.54f*u,2.82f,-1.63f};
        view(p,{.11f,.02f,.18f},split?48.f:37.2f,2,.018f*(1-2*u));
        relief(field0,6.1f,{0,0,0},0,koum?1.10f:1.05f,true);
        float on=koum?at(K_KOUM_OPEN,.39f):at(K_SOUSA_OPEN,.71f);
        float fade=split?.64f:.38f*(1-ramp(1.88f,2.46f,sec()));
        contour(field0,{0,0,0},.56f,koum?JADE:HONEY,fade*on,.997f,1.001f,.016f+lift*.015f);
        mark(0,{.10f,.0f,.25f});
    }
    void intro(int k){
        if(k==0){open_macro(false,q);return;}
        std::swap(g,half);open_macro(false,1-.17f*q);std::swap(g,half);save_half();
        std::swap(g,half);open_macro(true,q);std::swap(g,half);pair_out();
        marks[0]={.24f,.53f,1};marks[1]={.74f,.53f,1};
        // Fit the second print into the cut, not a full-screen white flash.
        const float cut=k==62?1:here(0,.22f);const int edge=int(g.w*.50f);
        if(cut<.998f){
            for(int y=0;y<g.h;y++)for(int x=edge;x<g.w;x++){
                const float v=ramp(.0f,.08f,cut-(x-edge)/float(g.w-edge));
                if(v<.999f){const int i=3*(y*g.w+x);for(int c=0;c<3;c++)g.rgb[i+c]=Raster::byte(g.rgb[i+c]*(.28f+.72f*v));}
            }
        }
    }

    void scenic(int variant,V p,V aim,float lens,float tint){
        const auto cam=Camera(p,aim,lens,g.w/float(g.h),.012f);g.cam=cam;
        const Plan plan{variant,cam,24.f,0,t};const Stamp nofoot(t,false);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
            float u=(x+.5f)/g.w,v=(y+.5f)/g.h;float dep;
            V c=earth.earth(plan,nofoot,cam.ray(u,v),dep);float vign=1-.14f*clamp(sq((u-.52f)*1.41f)+sq((v-.49f)*1.28f));
            c=c*lerp(V{.85f,1.02f,1.14f},V{1.18f,.965f,.78f},tint)*vign;
            const int px=y*g.w+x;g.rgb[3*px]=earth.byte(c.x);g.rgb[3*px+1]=earth.byte(c.y);g.rgb[3*px+2]=earth.byte(c.z);g.z[px]=dep>115.f?0.f:1/dep;
        }
        const auto& h=earth.local(variant);
        for(int j=0;j<510;j++){
            float x=-21+46*hash(j,2257),z=-26+57*hash(j,418);Sample r=Grid::all(h.local(x,z));
            if(r.h<.19f||r.h>1.44f||fabsf(r.gx)+fabsf(r.gy)>.72f)continue;
            const V C={x,r.h+.008f,z};V col=lerp(V{102,142,102},V{177,155,82},tint);float len=.125f+.25f*hash(j,45);
            for(int b=0;b<5;b++){
                const float u=.95f*b+j*.7f;
                g.line(C,C+V{sinf(u)*.16f+.025f*sinf(t*1.46f+x+b*.3f),len*(.64f+.34f*hash(j,b+17)),cosf(u)*.18f},col,.47f,1.03f);
            }
        }
    }
    void terrain(int k){
        if(k==40){
            std::swap(g,half);
            float u=q*.66f+.34f*here(4,9);
            if(sec()<4.87f)scenic(4,lerp(V{1.83f,3.04f,-11.9f},V{3.58f,2.75f,-10.6f},u),{-3.46f,.25f,11.12f},57.f,.85f);
            else scenic(4,lerp(V{2.43f,1.12f,-10.8f},V{3.66f,1.76f,-8.89f},here(4.87f,10.96f)),{-2.55f,.04f,11.66f},49.f,.85f);
            std::swap(g,half);save_half();std::swap(g,half);
            if(sec()<4.87f)scenic(7,lerp(V{-2.84f,5.50f,-11.93f},V{-1.23f,4.26f,-9.97f},u),{6.1f,.15f,8.32f},54.f,.21f);
            else scenic(7,lerp(V{-.48f,1.58f,-8.61f},V{2.26f,1.69f,-7.1f},here(4.87f,10.96f)),{5.20f,.07f,10.97f},49.f,.21f);
            std::swap(g,half);pair_out();return;
        }
        if(k==4){
            if(sec()<2.97f)scenic(4,lerp(V{-15.55f,6.05f,-23.61f},V{-10.41f,4.88f,-21.54f},here(0,3.0f)),{5.8f,.76f,9.2f},41.4f,.85f);
            else scenic(4,lerp(V{-9.10f,3.23f,-19.4f},V{-6.7f,2.0f,-16.9f},here(2.97f,6.8f)),{4.9f,.73f,10.4f},41.6f,.52f);
        }else if(k==52){
            if(f<K_VALLEY_WATER)scenic(7,lerp(V{-10.10f,11.84f,-16.32f},V{-9.10f,10.38f,-15.1f},here(0,2.8f)),{3.85f,.21f,10.9f},47.f,.21f);
            else scenic(7,lerp(V{-.31f,3.56f,-15.3f},V{3.10f,2.77f,-11.33f},here(2.8f,10.2f)),{7.13f,.48f,11.4f},42.3f,.32f);
        }else if(k==64)scenic(4,lerp(V{-4.38f,3.21f,-16.99f},V{-6.57f,4.69f,-18.59f},here(5.54f,9.3f)),{6.4f,.47f,10.8f},43.f,.80f);
    }

    void layers(){
        const bool intro0=shot==6;
        const float reveal=intro0?here(.19f,2.62f):at(K_STRATA_0,3.06f);
        const float peel=intro0?1:here(3.13f,8.87f);
        const V eye=intro0?lerp(V{-1.98f,3.94f,-5.94f},V{-.67f,4.57f,-5.53f},q):
            sec()<4.83f?lerp(V{-1.69f,2.90f,-6.10f},V{.1f,3.88f,-5.80f},here(0,4.83f)):
                lerp(V{1.39f,5.63f,-5.0f},V{.69f,5.74f,-4.69f},here(4.83f,10.7f));
        view(eye*1.14f,{.07f,.12f+.13f*reveal,.16f},41.f,0);stage(.45f);
        const int hits[]={K_STRATA_0,K_STRATA_1,K_STRATA_2,K_STRATA_3};
        for(int i=0;i<4;i++){
            const float a=intro0?at(K_SURFACES+i*9,.71f):at(hits[i],.62f);
            const float index=i-1.5f;
            const auto& stone=i==0?earth.koum:i==1?weather:i==2?earth.steps:pressure;
            const V p={index*reveal*.43f,-.55f+.34f*i+.32f*a*i,index*.69f*a-.16f*index*peel};
            slab(stone,p,{2.30f,.26f,1.29f},25+i,0,0,.052f*(3-i));
            mark(i,p+V{2.09f,.052f,-1.08f});
            if(!intro0&&a>.007f&&i!=2)contour(stone,p,.64f,i%2?JADE:HONEY,.48f*a*(1-here(8.8f,10.6f)),1.19f,.72f,.038f);
        }
        specks(459,23,{.20f,.12f,.04f},{2.32f,.97f,2.34f},PAPER,.14f);
    }

    void edge_scene(){
        const bool erosion=shot==14;
        const int impact=erosion?K_EROSION_POP:K_EDGE_CHIP;
        float u=at(impact,.76f),decay=at(impact,1.86f),tail=at(impact+47,.85f);
        V center{.16f,.18f,.17f};
        const V a=erosion?(sec()<4.71f?lerp(V{-1.72f,2.56f,-4.32f},V{-1.12f,2.23f,-4.09f},here(0,4.71f)):lerp(V{1.68f,4.22f,-4.66f},V{1.08f,4.96f,-4.39f},here(4.71f,8.96f))):lerp(V{-1.77f,3.97f,-5.41f},V{-.77f,3.29f,-5.06f},q);
        view(a,{.34f,.15f,.13f},41.f,2);stage();
        const Grid& material=erosion?earth.koum:weather;
        slab(material,center,{2.12f,.77f,1.58f},47,.075f+(erosion?1.04f:.62f)*u,erosion?.57f*decay:0);
        mark(0,center+V{1.89f-u*.77f,.081f,-.58f});
        mark(1,center+V{-.07f,.063f,.40f});
        if(erosion&&tail>.001f)contour(material,center,.56f,JADE,.67f*tail*(1-here(7.8f,8.94f)),2.12f/1.77f,1.58f/1.78f,.168f);
        for(int i=0;i<49;i++){
            float T=(f-impact)/24.f-hash(i,977)*.76f;if(T<0||T>2.9f)continue;
            float x=2.29f-(.57f+.17f*hash(i,991))*u+(.49f+.65f*hash(i,49))*T;
            float y=.16f+(.37f+1.13f*hash(i,256))*T-2.09f*T*T;
            float z=-.46f+(.89f*hash(i,63)-.45f)-.23f*T;
            float r=.017f+.073f*sq(hash(i,110));
            pebble(g,{x,std::max(-1.87f,y),z},{r*1.2f,r*.73f,r},lerp({137,123,89},{208,191,155},hash(i,119)),i*17+611,5,8,.26f,T*.85f+i*.97f);
        }
    }

    void scan_scene(){
        bool viewcards=shot==15;
        const Grid& field0=earth.koum;const V origin{.0f,.12f,.28f},ext{2.06f,.55f,1.61f};
        const V loc[]={{2.1f,3.4f,-4.1f},{-2.f,3.3f,-3.9f},{.23f,5.3f,-1.72f}};
        if(viewcards&&captures[0].w==0){
            Raster tile(338,194);std::swap(tile,g);
            for(int i=0;i<3;i++){
                view(loc[i],origin,37.f,2,i*.081f-.08f);slab(field0,origin,ext,47,.95f,.57f);
                auto& out=captures[i];out.w=g.w;out.h=g.h;out.rgb.resize(size_t(g.w)*g.h);
                for(size_t j=0;j<out.rgb.size();j++)out.rgb[j]=uint32_t(g.rgb[3*j])|(uint32_t(g.rgb[3*j+1])<<8)|(uint32_t(g.rgb[3*j+2])<<16);
            }
            std::swap(tile,g);
        }
        const float u=q;
        V p=viewcards?lerp(V{.2f,4.44f,-5.40f},V{-.73f,4.80f,-5.23f},q):lerp(V{-2.58f,3.76f,-4.75f},V{.55f,4.59f,-4.31f},q);
        view(p,{.05f,viewcards?.73f:.12f,.05f},39.2f,0);stage(.47f);slab(field0,origin,ext,47,.95f,.57f,viewcards?.01f:.17f);
        auto P=[&](float a,float b){return slab_top(field0,origin,ext,47,.95f,.57f,0,a,b).p+V{0,.024f,0};};
        if(viewcards){
            const V panels[]={{1.87f,1.25f,-.12f},{-1.87f,1.27f,-.10f},{.04f,1.96f,.30f}};
            const int cue[]={K_SCAN_READ,K_SCAN_SIDE,K_PHOTOS};
            for(int i=0;i<3;i++){
                float a=at(cue[i],.32f);if(a<.003f)continue;
                const V C=panels[i]+g.cam.u*(1-a)*.22f;const V col=i==1?JADE:HONEY;
                const V A=g.cam.r*(.78f+.08f*i)+g.cam.f*.09f*(i-1),B=g.cam.u*.453f;
                auto Card=[&](float u,float v){return C+A*(u*2-1)+B*(1-v*2);};
                g.lattice(3,3,[&](float u,float v){return Node{Card(u,v),{1.06f,1.04f,1.01f},u,v};},&captures[i],a);
                g.line(Card(0,0),Card(1,0),col,a*.87f,2.14f);g.line(Card(0,1),Card(1,1),col,a*.56f,1.f);
                g.line(Card(0,0),Card(0,1),col,a*.68f,1.55f);g.line(Card(1,0),Card(1,1),col,a*.63f,1.55f);
                g.line(Card(i==1?0.f:1.f,1),P(.26f+i*.22f,.50f),col,a*.61f,1.4f);mark(i,C);
            }
        }else{
            const float scan=at(K_RECONSTRUCTION,2.31f);
            for(int i=0;i<34;i++)for(int j=0;j<28;j++){
                float a=(i+.5f)/34.f,b=(j+.5f)/28.f;if(a>scan)continue;
                const float h=(.65f+.27f*expf(-sq((a-scan)*15.f)))*(.45f+.55f*(1-u*.35f));
                V x=P(a,b),c=P(a+.027f,b),d=P(a,b+.033f);
                g.line(x,c,JADE,h,1.08f);g.line(x,d,JADE,h,1.08f);
                if((i+j)%2==0)g.line(c,d,JADE,h*.47f,1.f);
            }
            if(scan<.999f)for(int j=0;j<40;j++)g.line(P(scan,j*.025f),P(scan,(j+1)*.025f),PAPER,.87f,2.1f);
            contour(field0,origin,.52f,JADE,.79f*at(K_RECONSTRUCTION+50,.62f),ext.x/1.77f,ext.z/1.78f,.057f);
            mark(0,P(.5f,.50f));
        }
    }

    void measure(){
        if(shot==64&&sec()>=5.54f){terrain(64);return;}
        const Grid& b=shot==64?earth.brazil:shot==22?weather:shot==37?rim:shot==33?earth.koum:blur;
        V p{.0f,3.8f,-2.2f},a{.1f,.0f,.15f};float lens=37.f;
        if(shot==17)p=lerp(V{-1.22f,1.86f,-2.64f},V{-.53f,2.22f,-2.49f},q);
        if(shot==18){p=lerp(V{-.03f,3.89f,-1.02f},V{.12f,4.14f,-.87f},q);a={-.17f,.0f,.17f};}
        if(shot==19){if(sec()<4.09f){p=lerp(V{1.87f,2.20f,-2.30f},V{1.43f,1.97f,-2.18f},q);}
            else{p=lerp(V{-1.83f,1.15f,-1.16f},V{-1.24f,1.08f,-1.68f},here(4.09f,10.2f));a={-.10f,-.025f,.13f};lens=34.f;}}
        if(shot==22){p=lerp(V{-.91f,3.28f,-3.54f},V{-1.19f,3.68f,-1.64f},q);a.z=lerp(-.76f,1.17f,q);lens=40.f;}
        if(shot==33){p=lerp(V{-.63f,1.69f,-1.43f},V{-.79f,2.48f,-2.02f},q);lens=42.f;}
        if(shot==37){p=lerp(V{1.53f,1.99f,-2.37f},V{.86f,1.42f,-2.08f},q);lens=39.f;}
        if(shot==64){p=lerp(V{-.16f,2.82f,-1.63f},V{-.86f,3.94f,-2.79f},here(0,5.54f));lens=37.2f;}
        view(p,a,lens,2,.013f*(1-2*q));relief(b,7.f,{0,0,0},0,shot==64?1.05f:1.12f,true);
        mark(0,{.09f,b.height(.09f,.18f),.18f});
        if(shot==18){
            const float u=at(K_LENGTH,.49f);V l{-1.14f,.104f,-.66f},r{-1.14f,.104f,1.04f};
            const V tip=lerp(l,r,u);g.line(l,tip,PAPER,.94f,3.2f);
            for(int i=0;i<=12;i++)if(i/12.f<u+.026f){V P=lerp(l,r,i/12.f);g.line(P+V{-.1f,0,0},P+V{i%3==0?.19f:.095f,0,0},HONEY,u*.95f,2.2f);}
            g.line(l,{-0.23f,.10f,-.66f},PAPER,.63f*u,1.2f);g.line(r,{-0.20f,.10f,1.04f},PAPER,.63f*u,1.2f);
            mark(1,l);mark(2,r);contour(b,{0,0,0},.46f,HONEY,.49f*u,.997f,1.002f,.019f);
        }
        if(shot==19)contour(b,{0,0,0},lerp(.38f,.64f,here(3.32f,8.18f)),HONEY,.70f*at(K_SOFT_OUTLINE,.48f),1,1,.030f);
        if(shot==37){contour(b,{0,0,0},.38f,HONEY,.74f*at(K_RIM,.48f),1,1,.039f);mark(1,{.44f,.079f,.23f});}
        if(shot==22){
            const float mix=at(K_LESS_CLEAR,.68f);const V p0={-.24f,.16f,-2.04f},p1={-.24f,.13f,2.65f};
            mark(1,p0);mark(2,p1);if(mix>.001f){g.dust({p0.x,.19f,p0.z},.063f,JADE,.56f*mix);g.dust({p1.x,.16f,p1.z},.068f,HONEY,.46f*mix);}
        }
        if(shot==64)contour(b,{0,0,0},.56f,HONEY,.60f*at(K_GENTLE_CLOSE,.31f)*(1-here(4.3f,5.54f)),1,1,.024f);
    }

    static float pad(float x,float z,float fx,float fz,float tx,float tz,float w,float e){
        const float u=clamp(((x-fx)*(tx-fx)+(z-fz)*(tz-fz))/(sq(tx-fx)+sq(tz-fz)+.0001f));
        const float r=sqrtf(sq(x-lerp(fx,tx,u))+sq(z-lerp(fz,tz,u)));
        return 1-ramp(w*.44f,w+e,r);
    }
    static float toes(float x,float z,float spread){
        float m=pad(x,z,0,-.40f,0,.15f,.28f,spread);
        for(int i=-1;i<=1;i++){
            float a=float(i);
            m=std::max(m,pad(x,z,.104f*a,.02f,.65f*a,.91f-.27f*fabsf(a),i==0?.131f:.114f,spread));
        }
        return m;
    }
    void mud_plate(V C,bool wet,float pressure0,float slump,float foot,float lift){
        constexpr float eX=1.45f,eZ=1.24f,under=.59f;
        auto h=[&](float x,float z){
            float n=(fnoise(x*8.1f+13.5f,z*8.6f+58.f)-.5f)*(wet?.024f:.053f)+(fnoise(24*x+11,20*z+41)-.5f)*(wet?.015f:.037f);
            float p=toes(x,z,wet?.045f+.080f*slump:.027f),r=std::max(0.f,toes(x,z,wet?.139f:.084f)-p);
            return n+pressure0*(-(wet?.245f:.167f)*p*(1-(wet?.76f*slump:0))+(wet?.095f:.069f)*r*(1-.83f*slump));
        };
        const V key=unit({-.46f,.79f,.48f});
        auto param=[&](float u,float v){
            const float z=(2*v-1)*eZ+.017f*sinf(u*26.2f),x=(2*u-1)*eX+.019f*cosf(v*18.f);
            return V{x,h(x,z),z};
        };
        for(int side=0;side<4;side++)for(int j=0;j<9;j++)for(int i=0;i<34;i++){
            auto verts=[&](float u,float d){V S=param(side==0?u:side==1?1.f:side==2?1-u:0.f,side==0?0.f:side==1?u:side==2?1.f:1-u);
                return C+V{S.x+d*.03f*sinf(u*37),S.y-under*d,S.z+d*.021f*cosf(u*49)};};
            float a=i/34.f,b=(i+1)/34.f,l=j/9.f,r=(j+1)/9.f;
            float shade=.67f+.21f*hash(i+31,317+j)+.092f*sinf(j*2.7f+side*.4f);
            const V sky=wet?V{63,113,103}:V{164,118,73},deep=wet?V{51,77,73}:V{107,80,54};
            V c=lerp(sky,deep,l)*shade;
            g.face(verts(a,l),verts(b,l),verts(b,r),verts(a,r),c);
        }
        g.lattice(120,112,[&](float u,float v){
            V p=param(u,v);float x=p.x,z=p.z;const float e=.014f;
            const V n=unit({h(x-e,z)-h(x+e,z),2*e,h(x,z-e)-h(x,z+e)});
            const float D=clamp(dot(n,key)),O=pressure0*toes(x,z,.025f+.064f*slump),H=wet?clamp(dot(reflect(unit(C+p-g.cam.p),n),key)):0;
            float granular=wet?.74f+.28f*fnoise(x*15.f,z*11.f):.70f+.32f*fnoise(x*28.f+11,z*28.f+.17f);
            V c=lerp(wet?V{69,99,88}:V{166,122,82},wet?V{110,139,120}:V{218,181,132},granular*.82f);
            c=c*(.39f+.69f*D)*(.99f-.47f*O*(1-(wet?.63f*slump:0)))+V{117,152,139}*(H*H*H*H*H*H*.85f);
            return Node{C+p,c};
        });
        if(!wet){
            for(int i=0;i<139;i++){
                float x=(2*hash(i,911)-1)*eX*.96f,z=(2*hash(i,924)-1)*eZ*.95f;
                float r=.008f+.030f*sq(hash(i,330));if(pressure0>.1f&&toes(x,z,.051f)>.22f)continue;
                V pos=C+V{x,h(x,z)+.23f*r,z};
                pebble(g,pos,{r*1.08f,r*.53f,r*.87f},lerp({128,92,56},{214,173,121},hash(i,674)),i+48,4,6,.16f);
            }
        }
        if(foot<2.5f){
            // A common rig drives both patches; the dry and wet materials differ,
            // but the stamp's scale, pose and descent are held identical.
            const V base=C+V{0,foot,0};
            // Carved three-toe tool: a single continuous shape, exactly the
            // same horizontal mask that pushes the impression into both beds.
            const auto X=[&](float x,float z,float h){return base+V{x,h,z};};
            constexpr int N=66;const float E=1.13f,step=2*E/N;
            float mask[N+1][N+1];
            V metal{148,148,136},ledge{106,121,120};
            for(int z=0;z<=N;z++)for(int x=0;x<=N;x++)mask[z][x]=toes(x*step-E,z*step-E,.027f)-.53f;
            for(int z=0;z<N;z++)for(int x=0;x<N;x++){
                const float u=x*step-E,v=z*step-E;
                const float U[]={u,u+step,u+step,u},W[]={v,v,v+step,v+step};
                const float depth[]={mask[z][x],mask[z][x+1],mask[z+1][x+1],mask[z+1][x]};
                V points[8],seam[4];int n=0,m=0;
                for(int j=0;j<4;j++){
                    int k=(j+1)%4;
                    if(depth[j]>=0)points[n++]=X(U[j],W[j],.145f);
                    if((depth[j]>=0)!=(depth[k]>=0)){
                        const float a=depth[j]/(depth[j]-depth[k]);
                        points[n]=X(lerp(U[j],U[k],a),lerp(W[j],W[k],a),.145f);seam[m++]=points[n++];
                    }
                }
                const V cap=metal*(.88f+.073f*hash(x,z/3)+.077f*fnoise(u*11.0f,v*11.f));
                for(int j=1;j<n-1;j++)g.tri(g.project({points[0],cap}),g.project({points[j],cap}),g.project({points[j+1],cap}));
                for(int j=0;j+1<m;j+=2){
                    V A=seam[j],B=seam[j+1],D=unit(B-A);
                    g.face(A,B,B-V{0,.145f,0},A-V{0,.145f,0},light({-D.z,.0f,D.x},ledge,1.30f));
                }
            }
            const auto shaft=[&](float u,float v){
                float a=u*2*PI,thick=.092f+.070f*(1-ramp(.0f,.18f,v));V normal={cosf(a),0,sinf(a)};
                V p=base+V{normal.x*thick,lerp(.135f,2.25f,v),-.235f+normal.z*thick};
                const float edge0=.21f*expf(-sq((a-3.75f)*2.6f));
                return Node{p,light(normal,metal,1.17f)+V{84,93,89}*edge0};
            };
            g.lattice(32,11,shaft);
            if(wet&&lift>.006f&&lift<.61f){
                for(int j=0;j<18;j++){
                    const float u=hash(j,661),z=.42f+.36f*u,x=(hash(j,678)-.5f)*.89f,amp=.74f*(1-lift/.61f);
                    if(toes(x,z,.031f)>.42f){
                        V A=C+V{x,h(x,z),z},B=base+V{x*.98f,.024f,z*.98f};
                        g.line(A,lerp(A,B,.68f),{135,169,147},amp,1.35f);g.dust(lerp(A,B,.72f),.013f,JADE,.52f*amp);
                    }
                }
            }
        }
        if(!wet&&shot==20){
            float T=(f-K_TEST_DOWN)/24.f;
            if(T>=0&&T<.86f)for(int i=0;i<29;i++){
                float d=T-.13f*hash(i,994);if(d<0)continue;
                float a=2*PI*hash(i,311),v=.49f+.61f*hash(i,870),r=.36f+v*d;
                V c=C+V{r*cosf(a),std::max(0.f,.13f+.85f*d-2.4f*d*d),.26f+r*sinf(a)};
                g.dust(c,.019f+.016f*hash(i,63),HONEY,.67f*(1-d));
            }
        }
        if(wet&&shot==20){
            float T=(f-K_SLUMP)/24.f;
            if(T>=0&&T<1.31f)for(int i=0;i<27;i++){
                const float d=T-hash(i,1008)*.41f;if(d<0)continue;
                float a=2*PI*hash(i,191),r=.31f+.29f*hash(i,187),x=r*cosf(a)*(1-.64f*d),z=.26f+r*sinf(a);
                const float h0=std::max(h(x,z),.086f+.10f*d-.9f*d*d),s0=.014f+hash(i,963)*.037f;
                pebble(g,C+V{x,h0,z},{s0,s0*.60f,s0*.75f},{119,163,133},151+i,5,8,.19f,d*2.3f);
            }
        }
    }

    void mud(){
        const bool res=shot==21;
        const float attack=res?1:at(K_TEST_DOWN,.39f),lift=res?1:at(K_TEST_UP,.80f),collapse=res?1:at(K_SLUMP,.75f);
        float foot=res?3.0f:1.91f*(1-at(K_TEST_DOWN-41,41/24.f))+.037f-.073f*attack+1.73f*lift;
        if(!res&&f>=K_TEST_UP)foot+=1.16f*lift;
        if(!res&&sec()<1.14f)foot=2.6f;
        V p;
        if(res)p=lerp(V{-.11f,4.72f,-3.56f},V{-.09f,5.78f,-1.16f},q);
        else if(f<K_TEST_DOWN+16)p=lerp(V{.0f,3.62f,-4.64f},V{-.03f,3.45f,-4.71f},here(0,4.16f));
        else if(f<K_TEST_UP)p=lerp(V{-.1f,2.31f,-4.43f},V{.10f,2.74f,-4.19f},here(4.17f,8.16f));
        else p=lerp(V{-.09f,4.90f,-3.39f},V{.04f,4.72f,-3.56f},here(8.17f,11.2f));
        view(p,{.0f,res?.045f:.34f,.06f},39.f,0,.002f);stage(.32f);
        for(int i=0;i<2;i++){
            V C={i?-1.56f:1.56f,.091f,.08f};mud_plate(C,i,attack,collapse,foot,lift);mark(i,C+V{0,.16f,-1.23f});
            mark(i+2,C+V{.0f,.038f,.31f});
        }
    }

    void compare(){
        const bool context=shot==39,section=shot==24||shot==38,clues=shot==27;
        V p=section?lerp(V{-.38f,2.02f,-4.99f},V{.63f,2.15f,-4.82f},q):lerp(V{-.42f,4.08f,-4.83f},V{.37f,3.69f,-4.60f},q);
        if(shot==23&&here(3.22f,3.43f)>.5f)p=lerp(V{.05f,5.66f,-1.27f},V{.0f,5.49f,-1.36f},here(3.44f,6.35f));
        view(p,{.06f,section?-.24f:.04f,.10f},40.6f,context?0:2);stage(.36f);
        for(int i=0;i<(shot==38?1:2);i++){
            const float h=clues?.23f-.46f*i:section?.032f-.06f*i:.08f;
            V P={shot==38?.0f:(i?-1.66f:1.66f),h,i?.12f:0.f};
            const auto& field0=clues?(i?dried:ripples):(i||shot==38?rim:earth.koum);
            const V extent={shot==38?2.5f:1.49f,section?1.10f:.66f,1.35f};
            slab(field0,P,extent,118+i,.094f,0,.025f);
            if(shot==23||context||shot==38)contour(field0,P,.57f,i||shot==38?HONEY:JADE,.58f*(context?at(K_BOTH,.61f):here(.43f,2.41f)),extent.x/1.77f,extent.z/1.78f,.046f);
            mark(i,P+V{0,.16f,-1.11f});
            if(section){
                for(int j=0;j<=32;j++){
                    const float x=-1.32f+2.64f*j/32.f,xx=x+.08f;
                    const V C=P+V{x,-.305f+(i?.127f:.18f)*sinf(x*2.3f)+.028f*cosf(j*.58f),-1.38f};
                    const V D=P+V{xx,-.305f+(i?.127f:.18f)*sinf(xx*2.3f)+.028f*cosf((j+1)*.58f),-1.38f};
                    g.line(C,D,i||shot==38?HONEY:JADE,.88f*here(.34f,3.03f),2.5f);
                }
            }
        }
    }

    void micro(){
        const bool cement=shot==30,mat=shot==31;
        const int cue=cement?K_CEMENT:mat?K_MAT:K_SOUSA_FIBRES;
        const float pin=at(cue,.95f),a=here(.0f,3.60f);
        V p=cement?(sec()<3.96f?lerp(V{-1.23f,1.83f,-4.27f},V{-.65f,1.12f,-3.77f},a):lerp(V{-.31f,1.29f,-2.37f},V{.12f,1.42f,-2.25f},here(3.96f,10.8f))):
            lerp(V{-.74f,1.62f,-3.49f},V{.44f,1.36f,-2.86f},q);
        view(p,{0,-.088f,.40f},41.f,cement?2:1);const V palette[]={ {143,117,75},{112,127,101},{174,146,101},{159,131,100},{103,146,134},{201,161,113} };
        auto spot=[&](int i,int j){return V{(i-4)*.659f+.15f*(hash(i,j+101)-.5f),-.52f-.13f*j+.048f*sinf(i*2.4f+j),.04f+j*.50f+.141f*hash(i,j+126)};};
        for(int j=0;j<5;j++)for(int i=0;i<9;i++){
            const V loc=spot(i,j);float r=.264f+.111f*hash(i,j+217),y=.77f+.26f*hash(i,j+13);const V c=palette[(i+2*j)%6]*(shot==36?V{1.10f,.89f,.74f}:V{1,1.04f,1.06f});
            pebble(g,loc,{r*1.10f,r*y,r*.95f},c,442+i+j*17,12,20,.18f,i*.97f);
            if(cement&&pin>.002f&&i<8){
                float progress=clamp(pin*(1.27f+.18f*hash(i,j+16)));
                V S=loc+V{r*.7f,r*.16f,-r*.16f},E=spot(i+1,j)+V{-.13f,.011f,-.048f},P=lerp(S,E,.5f);
                pebble(g,P,{(.06f+.30f*len(E-S))*progress,.043f+.038f*progress,.042f+.032f*progress},HONEY,i+j*135+531,8,15,.12f,.24f*j);
                P.y+=.089f;g.dust(P,.024f,HONEY,.72f*progress);
            }
            if(!cement&&pin>.001f){
                // Contact net grows along the grains, never a floating flat sheet.
                for(int z=0;z<4;z++){
                    float k0=(z+.5f)/4.f;
                    auto Q=[&](float c){float x=loc.x-.36f+c*.73f;
                        return V{x,loc.y+.23f+.061f*sinf(c*PI)+.028f*sinf(i*2.1f+c*6.7f),loc.z+(k0-.45f)*.43f+.048f*cosf(c*6.f+k0*PI)};};
                    const float len0=pin*(.67f+.33f*hash(j*9+i,z+390));
                    V prev=Q(0);
                    for(int n=1;n<=10;n++){
                        V next=Q(n*.10f*len0);g.line(prev,next,shot==36?HONEY:JADE,.66f*pin,1.26f);prev=next;
                    }
                    g.dust(prev,.020f,shot==36?HONEY:JADE,.64f*pin);
                }
            }
        }
        if(cement)mark(0,(spot(4,0)+spot(5,0))*.5f+V{0,.19f,-.048f});
        else mark(0,spot(4,0)+V{.02f,.255f,.05f});
        specks(93+shot,29,{.10f,.4f,.72f},{2.44f,.72f,1.81f},cement?HONEY:JADE,.061f);
    }

    void burial(){
        const float cover=at(K_BURY,3.30f);
        view(lerp(V{-.17f,2.29f,-5.3f},V{.53f,2.54f,-4.86f},q),{.15f,-.16f,.14f},38.6f,2);stage();
        const V center{.02f,.17f,.06f};slab(earth.koum,center,{2.29f,.94f,1.39f},127,.10f);
        if(cover<.97f)contour(earth.koum,center,.54f,JADE,.74f*(1-cover),2.29f/1.77f,1.39f/1.78f,.04f);
        if(cover>.002f){
            for(int j=0;j<3;j++){
                float p=clamp(cover*1.46f-j*.225f);
                if(p<.001f)continue;
                float rx=2.26f*p;
                slab(j==2?ripples:j==1?dried:pressure,center+V{-2.29f+rx,.115f+j*.089f,0},{std::max(.02f,rx),.258f,1.375f},127,.084f,.88f,j==2?.20f:.055f);
            }
            for(int j=0;j<61;j++){
                float T=(f-K_BURY)/24.f-hash(j,485)*2.72f;
                if(T<0||T>.89f)continue;
                V P=center+V{std::min(2.23f,-2.31f+4.56f*cover)+.25f*(1-T),.34f+.73f*(1-T*T),-1.38f+2.6f*hash(j,93)};
                g.dust(P,.011f+.026f*hash(j,701),HONEY,.72f*(1-T));
            }
            const float seal=at(K_SEAL,.40f);
            if(seal>.001f)g.line({-2.18f,.085f,-1.39f},{lerp(-2.18f,2.29f,seal),.085f,-1.39f},JADE,.83f*seal,2.4f);
        }
        mark(0,{.12f,.075f,-1.46f});
    }
};
}
