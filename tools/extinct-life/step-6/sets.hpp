// Original sets for the geology, preservation, and survey sequences.
#pragma once
#include "raster.hpp"

namespace feature {
constexpr V MINT{154,222,198}, GOLD{225,172,105}, INK{24,37,40}, WHITE{239,227,194};

struct Studio {
    Render earth;
    Grid blur,pressure,weather,rim,ripples,dried;
    std::map<const Grid*,Texture> tiles;
    std::array<Texture,3> captures;
    Raster g;
    float t=0,q=0;int f=0;
    std::array<V,12> marks{};
    Studio(const std::string& path,int w,int h):earth(path),blur(path+"/diffuse.field",9.6),pressure(path+"/pressure.field",9.6),
      weather(path+"/weather.field",9.6),rim(path+"/rim.field",9.6),ripples(path+"/ripples.field",9.6),dried(path+"/dried.field",9.6),g(w,h){}
    const Texture& tex(const Grid& gr){
        auto it=tiles.find(&gr);
        if(it==tiles.end())it=tiles.emplace(std::piecewise_construct,std::forward_as_tuple(&gr),std::forward_as_tuple(gr,earth,(&gr==&blur||&gr==&rim)?1:(&gr==&earth.river||&gr==&earth.flood)?2:0)).first;
        return it->second;
    }
    float at(int a,float s)const{return smooth((f-a)/(s*24.f));}
    Camera camera(V x,V y,V aim,float lens=42,float roll=0)const{return Camera(lerp(x,y,q),aim,lens,g.w/float(g.h),roll);}
    void mark(int i,V p){marks.at(i)=g.cam.project(p);}
    void stage(float glow=.42f){
        // An unbounded virtual stage with inverse-camera soft falloff and a
        // broad area-light shadow under the evidence. No visible modelled edge.
        const Camera c=g.cam;
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
            const float u=(x+.5f)/g.w,v=(y+.5f)/g.h;
            V d=c.f+c.r*((2*u-1)*c.focal*c.aspect)+c.u*((1-2*v)*c.focal);
            if(d.y>=-.020f)continue;
            const float t0=(-1.90f-c.p.y)/d.y;const V p=c.p+d*t0;
            const float R=std::max(0.f,std::sqrt(p.x*p.x+p.z*p.z));
            const float mask=(1-ramp(7.f,21.f,R))*ramp(.14f,.64f,-d.y);
            if(mask<.001f)continue;
            const float lit=.24f+.68f*expf(-.052f*(sq(p.x+2.8f)+sq(p.z+1.83f)));
            const float shade=expf(-sq(p.x/3.24f)*sq(p.x/3.24f)-sq((p.z-.1f)/1.56f))*glow;
            const V B=lerp({17,27,33},{53,66,64},lit)*(1-.70f*shade);
            int k=y*g.w+x;g.z[k]=1/t0;
            g.rgb[k*3]=Raster::byte(lerp(g.rgb[k*3],B.x,mask));
            g.rgb[k*3+1]=Raster::byte(lerp(g.rgb[k*3+1],B.y,mask));
            g.rgb[k*3+2]=Raster::byte(lerp(g.rgb[k*3+2],B.z,mask));
        }
        for(int i=-8;i<=8;i++){
            float q0=.090f*(1-fabsf(i)/10.f);g.line({float(i),-1.899f,-8},{float(i),-1.899f,8},{81,106,102},q0);
            g.line({-8,-1.897f,float(i)},{8,-1.897f,float(i)},{82,103,101},q0);
        }
    }
    void specks(int seed,int count,V centre,V half,V tone,float motion=.1f){
        for(int i=0;i<count;i++){
            float u=hash(i,seed),v=hash(i,seed+71),d=hash(i,seed+193);
            V p=centre+half*V{u*2.f-1,v*2.f-1,d*2.f-1}+V{motion*sinf(.46f*t+i),motion*.7f*cosf(.65f*t+i*.4f),motion*.6f*sinf(.31f*t+i*.7f)};
            g.dust(p,.004f+.023f*sq(hash(i,seed+24)),tone,.16f+.32f*hash(i,seed+59));
        }
    }
    void field(const Grid& field,float extent,float blend=0.f,float x=0.f,float z=0.f,float amp=1.f){
        const auto& texture=tex(field);
        g.lattice(126,108,[&](float u,float v){
            auto distance=[&](float w){float q=2*w-1;return .39f*extent*q+.075f*extent*q*q*q*q*q*q*q*4.3f+.11f*extent*q*q*q;};
            float X=x+distance(u),Z=z+distance(v);
            const auto s=Grid::all(field.local(X,Z));float h=s.h+(field.inside(X,Z)?blend:1.f)*(.146f*s.m-.022f*s.k);
            float light=amp*(.88f+.14f*expf(-.23f*(sq(X-.34f)+sq(Z-.30f))));
            return Node{{X,h,Z},{light,light,light},Grid::mirror(X/field.span+.5f),Grid::mirror(Z/field.span+.5f)};
        },&texture);
    }
    Node slab_top(const Grid& field,V center,V extent,int seed,float d,float blend,float fog,float u,float v)const{
            const float r0=seed*.842f;
            const float x=2*u-1,z=2*v-1,wrap=.022f*sinf(11*z+r0)+.014f*sinf(29*z-r0);
            const float chip=d*expf(-sq((z+.38f)/.39f))*ramp(.18f,.88f,x);
            const float xp=x*(1+wrap)-chip;
            const float zp=z*(1+.026f*sinf(x*13-r0)+.014f*cosf(33*x+r0));
            const float X=xp*1.77f,Z=zp*1.78f;
            const auto s=Grid::all(field.local(X,Z));
            const float y=center.y+(s.h+blend*(.146f*s.m-.022f*s.k))*1.36f;
            return Node{{center.x+xp*extent.x,y,center.z+zp*extent.z},{1-fog,1-fog*.8f,1-fog*.5f},X/field.span+.5f,Z/field.span+.5f};
    }
    void slab(const Grid& field,V center,V extent,int seed,float d=.0f,float blend=0.f,float fog=0.f){
        // Jagged top and sidewalls meet along the same world edge.
        const auto& texture=tex(field);float r0=seed*.842f;
        auto P=[&](float u,float v){return slab_top(field,center,extent,seed,d,blend,fog,u,v);};
        for(int side=0;side<4;side++){
            const auto C=[&](float z){return P(side==0?z:side==1?1.f:side==2?1-z:0.f, side==0?0.f:side==1?z:side==2?1.f:1-z).p;};
            const auto h=[&](float a,float b){V m=C(a);const float y=m.y-b*extent.y;const float tilt=sin(a*10.3f+r0)*.009f+sin(a*37.f-r0)*.006f;
                m.y=y+tilt*sin(PI*b);return m;};
            for(int j=0;j<15;j++)for(int i=0;i<38;i++){
                const float a=float(i)/38,b=float(i+1)/38,c=j/15.f,e=(j+1)/15.f;
                V n=side==0?V{0,0,-1}:side==2?V{0,0,1}:side==1?V{1,0,0}:V{-1,0,0};
                const bool warm=(&field==&earth.brazil||&field==&dried||&field==&rim);
                V brown=warm?V{157,107,62}:V{128,128,99}; V pale=warm?V{185,145,101}:V{162,155,121};
                V col=lerp(brown,pale,.48f+.40f*sinf(j*1.68f+seed*.44f+side*.13f));
                const float mineral=.79f+.11f*fnoise(i*.39f+seed,j*.87f+side*.4f)+.09f*fnoise(i*1.56f+seed,j*.96f);
                col=light(n,col,mineral*(.84f+.23f*(1-c)));
                g.face(h(a,c),h(b,c),h(b,e),h(a,e),col);
            }
        }
        g.lattice(58,55,P,&texture);
    }
    void water(float cx,float cz,float rx,float rz,float y,int variant,float alpha=1.f,float shore=0.f){
        const auto surface=[&](float x,float z){
            return y+shore*(z+.90f*sinf(.64f*x+.36f*z)+.29f*cosf(2.34f*x-.37f*z));
        };
        Texture rip;const int W=rx>6?540:286,H=rz>6?512:251;rip.w=W;rip.h=H;rip.rgb.resize(size_t(W)*H);
        const V sun=unit(variant==2?V{.41f,.48f,.92f}:V{-.25f,.48f,.83f});
        #pragma omp parallel for schedule(static)
        for(int j=0;j<H;j++)for(int i=0;i<W;i++){
            const float X=cx+rx*(2*(i+.5f)/W-1.f),Z=cz+rz*(2*(j+.5f)/H-1.f);
            const V P={X,surface(X,Z),Z},view=unit(g.cam.p-P);
            const float warp=1.37f*sinf(.57f*X+.81f*Z+.34f*t)+.68f*cosf(1.11f*X-.38f*Z);
            const float a=sinf(3.72f*X+6.15f*Z+2.19f*t+warp),b=cosf(6.66f*X-2.71f*Z-1.78f*t+1.74f*warp);
            const float e=sinf(12.07f*Z+13.36f*X-4.6f*t+.93f*a+1.43f*b);
            const float specGain=rx>6.f?.84f:1.f;
            const V n=unit({specGain*(.064f*a+.042f*b+.016f*e),1.f,specGain*(.049f*b-.049f*a+.017f*e)});
            float k=1-clamp(dot(view,n)),l=clamp(dot(reflect(view*(-1),n),sun));
            const float v0=l*l*l*l;float gleam=v0*v0*(.22f+.58f*v0*v0);
            V deep=variant==2?V{35,77,74}:V{21,94,114};
            V sky=variant==2?V{131,143,109}:V{118,161,172};
            V c=lerp(deep,sky,.16f+.60f*k*k+.07f*a+.037f*b+.030f*e);
            c+=V{90,71,43}*(gleam*(.75f+.21f*e));
            rip.rgb[j*W+i]=uint32_t(Raster::byte(c.x))|(uint32_t(Raster::byte(c.y))<<8)|(uint32_t(Raster::byte(c.z))<<16);
        }
        g.lattice(34,29,[&](float u,float v){float X=cx+rx*(2*u-1),Z=cz+rz*(2*v-1);
            const float Y=surface(X,Z);float dist=len(g.cam.p-V{X,Y,Z});float haze=rx>6.f&&shore==0.f?ramp(17.f,54.f,dist):0.f;
            return Node{{X,Y,Z},{1+.22f*haze,1+.11f*haze,1+.06f*haze},u,v};
        },&rip,alpha);
    }
    void stamp_rig(V center,float h){
        const V body{137,138,120},lower{112,119,98},accent{192,156,110};
        pebble(g,center+V{-.017f,.80f+h,-.09f},{.21f,.82f,.23f},lower,87,12,23,.013f);
        pebble(g,center+V{0,.105f+h,0},{.42f,.17f,.40f},body,112,10,21,.025f);
        for(int i=-1;i<=1;i++){
            const float d=float(i);
            pebble(g,center+V{d*.45f,.053f+h,.36f-fabsf(d)*.083f},{.132f,.094f,.55f-fabsf(d)*.056f},body,119+i,11,22,.019f,-d*.63f);
            pebble(g,center+V{d*.68f,.025f+h,.72f-fabsf(d)*.10f},{.067f,.040f,.111f},accent,90+i,7,12,.019f,-d*.63f);
        }
    }
    void floor_scene(int v){
        const Grid* gr=&blur;V a{-.55f,2.72f,-2.9f},b{.92f,2.55f,-2.20f},aim{.20f,.05f,.28f};float lens=41,restore=0;
        switch(v){
        case 0:a={-2.8f,1.55f,-2.2f};b={-2.13f,1.84f,-1.85f};lens=32;break;
        case 1:a={-.80f,4.07f,-2.15f};b={.91f,4.36f,-1.93f};aim.x=-.11f;lens=38;break;
        case 2:a={2.35f,1.60f,-2.03f};b={1.54f,1.53f,-2.22f};lens=33;break;
        case 3:gr=&weather;a={-2.15f,4.16f,-3.82f};b={-1.45f,4.35f,-2.00f};aim={.12f,-.02f,.72f};lens=43;break;
        case 4:gr=&ripples;a={-1.58f,1.27f,-2.18f};b={-.92f,1.67f,-1.82f};lens=36;break;
        case 5:gr=&dried;a={1.46f,2.24f,-1.58f};b={1.10f,2.02f,-1.69f};lens=35;break;
        case 6:gr=&earth.stamp;a={-1.64f,2.34f,-2.19f};b={-.94f,2.44f,-1.86f};restore=1-at(K_IMPACT_BANK,.43f);lens=42;break;
        case 7:gr=&earth.stamp;a={.57f,2.54f,-2.62f};b={-.19f,2.40f,-2.32f};restore=at(K_EROSION_WASH,2.1f);lens=38;break;
        case 8:gr=&earth.koum;a={2.31f,2.17f,-2.51f};b={1.64f,2.04f,-1.69f};lens=38;break;
        case 9:gr=&rim;a={1.69f,1.76f,-2.07f};b={.98f,2.61f,-1.87f};lens=36;break;
        case 10:gr=&earth.brazil;a={-1.77f,2.34f,-1.94f};b={-.49f,2.78f,-1.65f};lens=40;break;
        default:break;
        }
        g.begin(camera(a,b,aim,lens,.018f*(1-2*q)),2,t);
        field(*gr,12.10f,restore,0,0,v==10?1.06f:1.f);
        if(v==1){
            float A=at(K_LENGTH,.48f);float Z=-.67f+1.69f*A;
            const float x=-1.19f;
            if(A>.0001f||f==K_LENGTH){
                g.line({x,.16f,-.67f},{x,.16f,std::max(-.63f,Z)},INK,.89f,5.2f);
                g.line({x,.17f,-.67f},{x,.17f,std::max(-.63f,Z)},WHITE,.99f,2.9f);
                for(int i=0;i<=12;i++)if(i/12.f<=A+.04f){float z=-.67f+i/12.f*1.69f;float j=i%3==0?.117f:.063f;
                    g.line({x-j,.166f,z},{x+j,.166f,z},WHITE,1,2.f);}
            }
        }
        if(v==6||v==7){
            float u=v==6?1-at(K_DRAIN,2.9f):at(K_EROSION_WASH,1.4f);
            // Let the water intersect the real height field on a wandering
            // bank; never cut it off at the straight edge of a rectangle.
            if(u>.01f){
                const float sign=v==6?1.f:-1.f;
                water(0,0,7.6f,9.4f,lerp(-.43f,.117f,u),1,.48f+.26f*u,.092f*sign);
            }
            if(v==6&&f>=K_IMPACT_BANK-10&&f<K_IMPACT_BANK+11)stamp_rig({.05f,0,.02f},.91f*(1-at(K_IMPACT_BANK-10,.42f))+.67f*at(K_IMPACT_BANK,.49f));
        }
        if(v==9){const float a0=at(K_RIM,.72f)*(1-ramp(0,3.7f,(f-K_RIM)/24.f));
            float prev=0;V x0;
            for(int i=0;i<=64;i++){float a=i/64.f*2*PI;V x={.10f+.77f*cosf(a),.095f,.20f+.90f*sinf(a)};
                if(i&&a0>.01f&&i%7<4&&prev/64.f<a0*2.f)g.line(x0,x,GOLD,.38f*a0,1.f);
                prev=float(i);x0=x;}
        }
        float dust=v==10?.071f:.12f;
        specks(v*11+23,v==10?77:37,{0,.50f,.04f},{3.0f,.34f,2.0f},v==10?GOLD:WHITE,dust);
        mark(0,{.07f,.085f,.20f});
    }
    void slab_scene(int v){
        const float c=.45f;
        V eye0{-.12f,3.65f,-7.78f},eye1{1.63f,4.45f,-7.23f},aim{c,.27f,.01f};float lens=42;
        if(v==3||v==4||v==5||v==10||v==6){eye0={.32f,5.55f,-8.45f};eye1={-.72f,5.01f,-8.02f};aim={0,.0f,.09f};lens=38;}
        if(v==1){eye0={-2.18f,4.14f,-8.57f};eye1={.93f,4.89f,-7.93f};aim={.51f,.51f,.12f};lens=37;}
        if(v==8||v==9){eye0={-1.52f,2.16f,-6.30f};eye1={1.39f,2.66f,-6.28f};aim={.41f,.05f,0};lens=36;}
        g.begin(camera(eye0,eye1,aim,lens),v==8||v==9?2:0,t);stage();
        if(v==1){
            const int hits[]={K_STRATA_0,K_STRATA_1,K_STRATA_2,K_STRATA_3};
            for(int i=0;i<4;i++){
                float a=at(hits[i],1.11f),y=-.77f+.38f*i+.33f*a*i;
                V p={c+(i-1.5f)*.24f*a,y,.10f+(i-1.5f)*a*.40f};
                slab(i%3==2?earth.steps:earth.koum,p,{2.1f,.25f,1.24f},3+i,0,0,.062f*(3-i));
                mark(i,p+V{1.88f,.05f,-.87f});
                if(a>.001f)g.dust(p+V{1.97f,.11f,-.88f},.032f,GOLD,a*.73f);
            }
        } else if(v==3||v==4||v==5||v==6||v==7||v==10){
            for(int i=0;i<2;i++){
                const Grid* gr=i?&pressure:&earth.stamp;float height=.012f-.13f*i;
                if(v==5){gr=i?&blur:&earth.brazil;height=.025f;}
                if(v==6||v==10){gr=i?&earth.koum:&rim;height=.034f-.27f*i;}
                if(v==7){gr=i?&ripples:&dried;height=i?-.82f:.31f;}
                float h=1.4f;float restore=v==3?1-at(K_TEST_DOWN,.38f):v==4&&i?.22f:0;
                if(v==3){const auto f0=K_TEST_DOWN-34;h=1.30f*(1-at(f0,(K_TEST_DOWN-f0)/24.f))+.09f+1.45f*at(K_TEST_UP,1.25f);
                    if(i&&f>K_TEST_UP)restore=.22f*at(K_SLUMP,.82f);
                }
                const float x=(i?1.85f:-1.85f)*(v==3||v==4?-1.f:1.f);
                V p={x,height,i?-.024f:.18f};float body=v==10?.62f:v==7?.43f:.49f;
                if(v==6)p.z+=i*.54f;
                slab(*gr,p,{1.58f,body,1.55f},41+i,.07f,restore);
                if(v==3 && f>=K_TEST_DOWN-34 && f<K_TEST_UP+39)stamp_rig(p,h-.05f);
                if(v==3&&f>=K_SLUMP&&f<K_SLUMP+56){float T=(f-K_SLUMP)/24.f;
                    for(int j=0;j<27;j++){float a=hash(j,86)*2*PI,r=.28f+.18f*T+.65f*hash(j,227);
                        V m={r*cosf(a),.11f+std::max(0.f,(1.08f-.55f*j/28.f)*T-1.37f*T*T),r*sinf(a)};
                        g.dust(p+m,.012f+hash(j,69)*.018f,GOLD,.65f*(1-smooth(T/1.7f)));}}
                mark(i,p);
            }
        } else if(v==8||v==9){
            const float cover=v==8?at(K_BURY,2.94f):0.f;
            V p={c,-.02f,0};slab(v==8?earth.koum:rim,p,{2.64f,1.11f,1.49f},17,.10f);
            if(v==8&&cover>.001f){
                // The new layer grows across the old top with its base keyed
                // below the former surface; the two masses cannot hang apart.
                V P=p+V{-2.55f+2.60f*cover,.22f,.0f};
                slab(ripples,P,{std::max(.09f,2.57f*cover),.52f,1.55f},39,.137f);
                for(int j=0;j<74;j++){
                    float T=(f-K_BURY)/24.f-hash(j,735)*1.74f;if(T<0||T>1.0f)continue;
                    const float x=lerp(-1.35f,2.46f,hash(j,741));
                    V r={x+(1-T)*.28f,lerp(1.71f,.37f,T),-.70f+hash(j,229)*1.69f};
                    g.dust(r,.016f+hash(j,396)*.025f,GOLD,.79f*(1-ramp(.65f,1.0f,T)));}
            } else if(v==9){
                int steps=45;for(int i=1;i<=steps;i++){
                    auto ledge=[&](float j){float x=-.85f+2.51f*j;return V{c+x,.06f+.26f*expf(-sq((x+.62f)/.16f))+.22f*expf(-sq((x-.71f)/.19f)),-1.488f};};
                    g.line(ledge((i-1)/float(steps)),ledge(i/float(steps)),GOLD,.75f,2.f);
                }
            }
        } else {
            const float chip=v==2?.22f+.34f*at(K_EROSION_POP,1.31f):.22f;
            slab(v==0?weather:earth.koum,{.42f,.14f,.18f},{2.31f,.81f,1.92f},24,chip);
            int event=v==0?K_EDGE_CHIP:K_EROSION_POP;
            for(int j=0;j<19;j++){
                float T=(f-event)/24.f-hash(j,32)*.6f;
                if(T<0)continue;
                float push=.37f+.53f*hash(j,92),y=.122f+.43f*T-1.66f*T*T;
                float z=-.55f+.55f*(hash(j,82)-.5f);V p={2.33f+T*push,std::max(-1.85f,y),z-.4f*T};
                if(T<4.0f)pebble(g,p,{.046f,.049f,.038f},WHITE*(.59f+.26f*hash(j,96)),j+490,4,7,.25f,T*1.3f);
            }
        }
        specks(v+952,47,{0,.71f,-.17f},{3.33f,.89f,1.93f},WHITE,.085f);
    }
    void survey(int v){
        const V center{.70f,0,0},extent{2.21f,.47f,1.54f};
        const V eyes[]={{3.51f,4.24f,-3.79f},{-2.92f,3.25f,-4.25f},{.57f,5.20f,.32f}};
        if(v==0&&captures[0].rgb.empty()){
            // Actual renders of the same sample from three virtual photograph
            // positions. No study image, screenshot or field mesh is reused.
            Raster nested(264,165);std::swap(g,nested);
            for(int i=0;i<3;i++){
                g.begin(Camera(eyes[i],center,45,g.w/float(g.h),i*.08f-.08f),0,0);stage(.33f);
                slab(earth.koum,center,extent,570,.12f);
                auto& im=captures[i];im.w=g.w;im.h=g.h;im.rgb.resize(size_t(im.w)*im.h);
                for(size_t k=0;k<im.rgb.size();k++)im.rgb[k]=uint32_t(g.rgb[k*3])|(uint32_t(g.rgb[k*3+1])<<8)|(uint32_t(g.rgb[k*3+2])<<16);
            }
            std::swap(g,nested);
        }
        g.begin(camera(v?V{-2.42f,4.11f,-6.54f}:V{.59f,4.68f,-8.03f},v?V{.94f,4.15f,-6.47f}:V{-1.22f,4.98f,-8.23f},{.41f,v?.06f:.71f,.0f},40),0,t);
        stage(.33f);slab(earth.koum,center,extent,570,.12f,0,v?.19f:.06f);
        auto p=[&](float x,float z){return slab_top(earth.koum,center,extent,570,.12f,0,0,(x+1)*.5f,(z+1)*.5f).p+V{0,.027f,0};};
        if(v==0){
            const V lenses[]={{3.04f,2.13f,-1.45f},{-2.21f,1.92f,-1.35f},{.34f,2.87f,.73f}};
            const int hits[]={K_SCAN_READ,K_SCAN_SIDE,K_PHOTOS};
            for(int i=0;i<3;i++){
                float on=at(hits[i],.51f);if(on<.001f)continue;
                const V l=lenses[i]+V{0,lerp(.30f,0.f,on)+.082f*sinf(q*PI),.085f*cosf(q*PI)};
                const V col=i==0?GOLD:MINT;
                const V frame[4]={p(-.68f,-.66f),p(.72f,-.67f),p(.68f,.64f),p(-.61f,.61f)};
                const float fading=.36f+.50f*expf(-sq(float(f-hits[i])*.020f));
                for(int j=0;j<4;j++){
                    g.line(l,frame[j],col,fading*on*.74f,1.1f);g.line(frame[j],frame[(j+1)%4],col,fading*on*.54f,1.15f);
                }
                const V X=g.cam.r*.875f+g.cam.f*(i==0?-.13f:.132f),Y=g.cam.u*.525f+g.cam.r*(i==0?-.072f:.036f);
                auto tile=[&](float x,float y){return l+X*(2*x-1)+Y*(1-2*y);};
                g.lattice(2,2,[&](float x,float y){return Node{tile(x,y),{1.f,1.01f,1.06f},x,y};},&captures[i],on);
                const V A=tile(0,0),B=tile(1,0),C=tile(1,1),D=tile(0,1);
                g.line(A,B,col,.78f*on,1.8f);g.line(B,C,col,.73f*on,1.8f);
                g.line(C,D,col,.73f*on,1.8f);g.line(D,A,col,.73f*on,1.8f);
            }
        }else{
            float sweep=lerp(-1.01f,1.0f,at(K_RECONSTRUCTION,2.97f));
            for(int i=0;i<=22;i++)for(int j=0;j<=17;j++){
                float x=i/11.f-1,z=j/8.5f-1;
                if(x>sweep)continue;
                float a=.49f+.41f*expf(-sq((x-sweep)/.144f)),p0=smooth((sweep+1)*.61f);
                const V col=lerp(MINT,WHITE,.36f*a);V o=p(x,z);
                if(i)g.line(p(x-1/11.f,z),o,col,a,1.0f);
                if(j)g.line(p(x,z-1/8.5f),o,col,a,1.0f);
                if(i&&j)g.line(p(x-1/11.f,z-1/8.5f),o,col,a*.74f,1.0f);
                if(i%2==0&&j%3==0)g.dust(o,.017f,WHITE,(.44f+.22f*p0)*a);
            }
            for(int i=1;i<40;i++)g.line(p(sweep,(i-1)/20.f-1),p(sweep,i/20.f-1),WHITE,.67f,2.4f);
        }
        specks(778,41,{.5f,1.36f,0},{3.3f,1.15f,2.55f},MINT,.12f);
    }
    void grain_scene(int v){
        const bool pollen=v==3;const V a=pollen?V{.59f,1.52f,-5.02f}:V{-.69f,1.18f,-4.85f};
        const V b=pollen?V{1.58f,1.78f,-4.81f}:V{.91f,1.80f,-4.79f};
        g.begin(camera(a,b,{.35f,.05f,0},38),v==1||v==2?1:2,t);
        if(pollen){
            const V pos{.66f,.11f,.05f};
            pebble(g,pos,{1.01f,.91f,1.03f},{156,116,57},444,32,66,.077f,-q*.78f);
            for(int i=0;i<162;i++){
                float a0=6.283f*hash(i,991),y=2*hash(i,994)-1,k=sqrtf(1-y*y);a0-=q*.78f;
                V n={cosf(a0)*k,y,sinf(a0)*k};V off=pos+n*V{1.01f,.93f,1.01f};
                float s=.026f+.041f*hash(i,1001);pebble(g,off,{s,s*.95f,s},GOLD*.81f,i+668,5,7,.12f);
            }
            specks(384,68,{.87f,.06f,.19f},{3.49f,2.20f,1.57f},GOLD,.23f);
        }else{
            const V palette[]={{152,144,104},{96,134,117},{134,117,93},{169,150,118},{114,132,111},{179,169,128},{87,108,103}};
            const float revealed=v?1.f:at(K_CEMENT,.95f);
            for(int j=0;j<6;j++)for(int i=0;i<16;i++){
                int k=j*44+i+v*817;float x=(i-7.5f)*.50f,y=-.35f-.23f*j+.13f*hash(i,171+j),z=(j-2)*.37f;
                x+=(hash(k,57)-.5f)*.31f;z+=(hash(k,81)-.5f)*.38f;
                float r=.14f+.180f*hash(k,131);V p={x,y,z};
                pebble(g,p,{r*(1.2f+.23f*hash(k,818)),r*.72f,r*.89f},palette[k%7]*(v==2?V{1.12f,.86f,.72f}:V{1,1,1}),k,7,12,.26f);
                if((i+j)%3!=0&&revealed>.001f){
                    float p0=1.f-ramp(.21f,2.8f,1.f+q*.97f);V C=p+V{.23f,.02f,.11f};
                    pebble(g,C,{.17f*revealed,.089f,.10f},(v?V{153,151,99}:V{224,184,112})*(.78f+p0*.37f),k*3,5,9,.21f);
                }
            }
            if(v){
                float reveal=v==1?at(K_MAT,.93f):at(K_SOUSA_FIBRES,1.1f);
                g.lattice(68,39,[&](float u,float w){float x=lerp(-3.49f,3.49f,u),z=lerp(-.19f,1.58f,w);
                    const float y=-.13f+.063f*sinf(x*1.57f+z*.75f)+.046f*cosf(z*7.15f+x*.93f);
                    float fleck=.66f+.27f*sinf(33*x+13*z+.65f*sin(8*x))+.13f*cosf(28*z+.42f*x);
                    return Node{{x,y,z},lerp(v==1?V{45,89,69}:V{82,87,48},v==1?V{141,181,122}:V{172,142,80},clamp(fleck))};
                },nullptr,.47f*reveal);
                for(int i=0;i<28;i++){
                    float x=lerp(-3.32f,3.32f,hash(i,478));V a0={x,-.118f+.063f*sinf(x*1.57f),.5f+hash(i,493)*.62f};
                    g.line(a0,a0+V{.21f,.037f,.18f},v==1?MINT:GOLD,reveal*.47f,1.2f);
                }
            }
            specks(v+498,53,{.45f,.46f,.4f},{3.31f,.53f,1.62f},v==2?GOLD:MINT,.12f);
        }
    }
    void valley(int v){
        // Landscape ray intersections, mirrored glints and distance-dependent
        // haze are the same physical shaders as the opening, not repeated 2D
        // water textures. Distinct cameras are illustrations, not locations.
        const bool dawn=v!=1;const auto& r=dawn?earth.flood:earth.river;
        V a,b,aim;float lens;
        if(v==0){a={4.30f,3.38f,-18.1f};b={2.22f,3.70f,-14.7f};aim={-3.51f,.34f,11.83f};lens=37.5f;}
        else if(v==1){a={-6.48f,13.37f,-12.28f};b={-7.10f,11.31f,-9.58f};aim={4.72f,.07f,6.46f};lens=40.1f;}
        else {a={-11.90f,6.01f,-26.8f};b={-7.87f,4.25f,-22.7f};aim={6.48f,.82f,18.27f};lens=44.0f;}
        const auto cam=camera(a,b,aim,lens,.017f*(1-2*q));g.cam=cam;
        const Plan plan{dawn?4:7,cam,27.f,0,t};const Stamp stamp(t,false);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
            const float X=(x+.5f)/g.w,Y=(y+.5f)/g.h;const V d=cam.ray(X,Y);float z;
            V c=earth.earth(plan,stamp,d,z);
            if(v==0)c=c*V{1.081f,.905f,.784f};
            else if(v==2)c=c*V{.879f,.964f,1.076f};
            const float vignette=1-.17f*clamp(sq((X-.51f)*1.64f)+sq((Y-.50f)*1.43f));
            int k=y*g.w+x;g.rgb[k*3]=earth.byte(c.x*vignette);g.rgb[k*3+1]=earth.byte(c.y*vignette);g.rgb[k*3+2]=earth.byte(c.z*vignette);
            g.z[k]=z>120.f?0:1.f/(z*dot(d,cam.f));
        }
        for(int j=0;j<530;j++){
            float X=-22+44*hash(j,553),Z=-23+55*hash(j,354);const auto a=Grid::all(r.local(X,Z));
            if(a.h<.19f||a.h>1.46f||fabsf(a.gx)+fabsf(a.gy)>.59f)continue;
            const float stem=.11f+.33f*hash(j,945);const V p={X,a.h+.015f,Z};
            const V col=dawn?V{128,138,78}:V{131,149,77};
            for(int i=0;i<5;i++){
                const float angle=i*PI*.4f+hash(j,924);V b=p+V{.13f*sinf(angle),stem,.15f*cosf(angle)};
                b.x+=.045f*sinf(t*1.32f+j*.23f);g.line(p,b,col,.42f,1.05f);
            }
        }
        if(dawn)specks(164,41,{2.26f,3.2f,1.5f},{10.55f,1.67f,15.f},GOLD,.25f);
    }

};
}
