#pragma once
#include "terrain.hpp"
#include "strata.hpp"
#include "swimmer.hpp"
#include "microscope.hpp"
namespace cinema {

struct Cinema : CutSet {
    std::vector<uint8_t> buffer;
    explicit Cinema(const std::string& p,int w,int h):CutSet(p,w,h){}

    void side_copy(bool first){
        for(int y=0;y<g.h;y++){
            int offset=y*g.w+(first?0:half.w),row=y*half.w;
            std::memcpy(&g.rgb[3*offset],&half.rgb[3*row],half.w*3);
            std::copy_n(half.z.data()+row,half.w,g.z.data()+offset);
        }
    }
    void finish_look(bool field=false,bool water=false,float distance=0,bool split=false){
        // Depth-tested contact shade and limited circle-of-confusion. This reads
        // raster depth, never a mask tied to the display or the subtitle layer.
        const auto& z=g.z;const int w=g.w,h=g.h,k=shot;const bool subsurface=k==31||k==36||k==55;
        const bool warm=k==0||k==26||k==32||k==37||k==38||k==43||k==64;
        const V cast=water?V{1.021f,1.021f,1.025f}:warm?V{1.092f,1.034f,.966f}:V{1.035f,1.055f,1.066f};
        buffer=g.rgb;
        #pragma omp parallel for schedule(static)
        for(int y=0;y<h;y++)for(int x=0;x<w;x++){
            const int i=y*w+x;const float u=(x+.5f)/w,v=(y+.5f)/h,q=z[i];
            const float p=q>.001f?1/q:0;
            const float X=split?2*u-std::floor(2*u):u;
            const float v0=sq((X-.49f)*(field?1.4f:1.31f))+sq((v-.47f)*1.39f);
            const float autoex=(1-(water?.15f:field?.24f:.153f)*clamp(v0));
            const int xlo=split&&x>=w/2?w/2:0,xhi=split&&x<w/2?w/2-1:w-1;
            auto j=[&](int dx,int dy){return std::clamp(y+dy,0,h-1)*w+std::clamp(x+dx,xlo,xhi);};
            V c={float(buffer[3*i]),float(buffer[3*i+1]),float(buffer[3*i+2])};
            float AO=0,blade=0;
            if(q>.001f&&!water){
                float ortho=static_cast<float>(h)/540.f;
                int r0=field?int(9.0f*ortho):int(13.0f*ortho);
                const float left=z[j(-r0,0)],right=z[j(r0,0)],above=z[j(-r0/2,-r0/2)],below=z[j(r0/2,r0/2)];
                float crease=std::max(0.f,(left+right+above+below)*.25f-q);
                float cavity=ramp(.008f,.27f,crease/(q+.0001f))*(1-ramp(.51f,1.55f,crease/(q+.0001f)));
                const float close=std::max({fabsf(left-q),fabsf(right-q),fabsf(above-q),fabsf(below-q)})/(q+.001f);
                AO=(field?.13f:.25f)*cavity*(1-ramp(.21f,.60f,close));
                const int d=int(3*ortho);
                blade=clamp((z[j(d,-d)]-z[j(-d,d)])/(q+.001f),-.11f,.11f)*(1-ramp(.14f,.61f,close));
            }
            if(distance>0&&p>0){
                float c0=ramp(.26f,2.45f,fabsf(p-distance));
                if(c0>.005f){
                    int r=c0>.60f?3:1;
                    V soft=c*2.f;float n=2;
                    const int taps[]={j(-r,0),j(0,r),j(r,0),j(0,-r)};
                    for(int a:taps){
                        if(fabsf(z[a]-q)<.078f*q+.001f){soft+=V{float(buffer[3*a]),float(buffer[3*a+1]),float(buffer[3*a+2])};n+=1;}
                    }
                    c=lerp(c,soft/n,c0*.70f);
                }
            }
            if(!field&&!water&&q<.072f){
                const float spread=1-ramp(.03f,1.f,sq((X-.49f)*1.57f)+sq((v-.49f)*1.52f));
                const float light0=ramp(.08f,.59f,spread)*(.58f+.42f*(1-v));
                const V fog=subsurface?V{18,57,67}:warm?V{40,34,33}:V{21,38,48};
                c=lerp(c,lerp(c,fog,.66f)+fog*(light0*.36f),1-ramp(.002f,.072f,q));
            }
            float l=luminance(c)/255.f;
            V hi=cast;hi=lerp(hi,V{1.035f,1.031f,1.027f},ramp(.71f,.97f,l));
            const float feet=1-.32f*AO+.28f*blade;
            if(l<.32f&&!water)c+=V{1.8f,2.4f,4.2f}*(1-ramp(.08f,.34f,l));
            const float energy=.94f+.135f*ramp(.09f,.64f,l);
            c=c*hi*(autoex*feet*energy*(1-AO));
            const float dither=.63f*(hash(x&63,y&63)-.50f);
            uint8_t* out=&g.rgb[3*i];out[0]=Raster::byte(c.x+dither);out[1]=Raster::byte(c.y+dither);out[2]=Raster::byte(c.z+dither);
        }
    }
    void story_terrain(int k){
        if(k==40){
            for(int i=0;i<2;i++){
                std::swap(g,half);
                if(i==0){
                    float u=here(4.87f,10.96f);
                    V eye=sec()<4.87f?lerp(V{1.85f,4.25f,-13.9f},V{3.0f,3.2f,-11.5f},here(0,4.87f)):
                                         lerp(V{3.68f,1.64f,-9.86f},V{4.12f,1.87f,-8.26f},u);
                    valley_view(*this,2,eye,{-2.56f,.48f,10.21f},54.f);
                }else{
                    V eye=sec()<4.87f?lerp(V{-2.63f,5.23f,-14.86f},V{-1.12f,4.15f,-12.27f},here(0,4.87f)):
                                         lerp(V{-.42f,1.69f,-8.61f},V{2.03f,1.95f,-7.9f},here(4.87f,10.96f));
                    valley_view(*this,1,eye,{5.68f,.33f,10.58f},52.f);
                }
                std::swap(g,half);side_copy(i==0);
            }
            return;
        }
        if(k==4){
            V p=spline({-11.68f,4.71f,-24.84f},{-10.31f,3.05f,-21.74f},{-7.70f,3.13f,-19.36f},{-5.92f,4.37f,-17.55f},q);
            valley_view(*this,0,p,{5.10f,.82f,9.82f},40.7f);
        }else if(k==7){
            V p=spline({-3.96f,4.23f,-18.61f},{-2.56f,3.64f,-15.17f},{1.44f,2.58f,-11.48f},{3.42f,2.36f,-9.39f},q);
            valley_view(*this,1,p,{6.48f,.52f,9.28f},43.1f);
        }else if(k==35){
            V p=lerp(V{1.33f,2.57f,-15.36f},V{3.97f,2.18f,-11.60f},q);
            valley_view(*this,2,p,{-2.89f,.44f,11.3f},40.6f);
        }else if(k==52){
            V p;
            if(f<K_VALLEY_WATER)p=lerp(V{-9.89f,11.32f,-18.4f},V{-8.86f,10.42f,-16.75f},here(0,2.79f));
            else p=spline({-.43f,4.34f,-17.f},{-.03f,3.05f,-14.07f},{2.96f,2.97f,-10.86f},{4.09f,2.69f,-9.32f},here(2.79f,10.33f));
            valley_view(*this,3,p,{7.78f,.67f,12.03f},f<K_VALLEY_WATER?48.6f:41.6f);
        }else if(k==64){
            valley_view(*this,0,lerp(V{-4.21f,3.09f,-17.27f},V{-5.91f,4.73f,-20.09f},here(5.54f,9.3f)),{5.29f,.74f,10.60f},43.f);
        }
    }
    void print_half(bool b,float u,bool pair){
        const V p=pair?(b?lerp(V{-.51f,3.43f,-1.51f},V{-.18f,3.63f,-1.24f},u):lerp(V{.41f,3.48f,-1.48f},V{.22f,3.71f,-1.21f},u)):
            spline({-1.42f,2.63f,-1.89f},{-.81f,2.47f,-1.79f},{-.43f,2.74f,-1.31f},{.28f,3.32f,-1.01f},u);
        const auto& h=b?earth.koum:earth.brazil;
        view(p,{.08f,-.05f,.19f},pair?50.0f:37.5f,2,.024f*(1-2*u));
        macro_ground(*this,h);
        if(!b&&!pair){auto room=daylight(2);room.sun=unit({-.51f,.70f,-.44f});shallow(*this,h,-.125f,room,false,0,-100,.72f);}
        const float pulse=shot==62?.40f:pair?lerp(.29f,.71f,here(.18f,1.03f)):.55f*at(K_SOUSA_OPEN,.64f)*(1-here(1.72f,2.58f));
        contour(h,{0,0,0},.557f,b?JADE:HONEY,pulse,1,1,.015f);
        mark(0,{.10f,.002f,.22f});
    }
    void prints(int k){
        if(k==0){print_half(false,q,false);return;}
        // Cut on the comparison; both images maintain scale and orientation.
        for(int i=0;i<2;i++){
            std::swap(g,half);print_half(i==1,k==62?1-q*.42f:q,true);std::swap(g,half);side_copy(i==0);
        }
        marks[0]={.249f,.509f,1};marks[1]={.751f,.512f,1};
    }
    void near_tracks(int k){
        const float d=(k==8)?here(0,4.6f):q;
        const auto& m=earth.steps;V eye,aim;float lens;
        if(k==8){eye=spline({-2.67f,3.22f,-4.35f},{-2.10f,2.93f,-3.85f},{-1.52f,2.64f,-3.10f},{-1.34f,2.76f,-2.55f},d);aim={-.08f,.03f,-.18f};lens=42.2f;}
        else if(k==10){eye=lerp(V{1.9f,2.90f,-3.93f},V{1.15f,3.25f,-2.43f},q);aim={.10f,.03f,.17f+.63f*q};lens=41.4f;}
        else{eye=lerp(V{1.92f,5.64f,-5.26f},V{.98f,6.71f,-4.90f},q);aim={.02f,.07f,.70f};lens=44.9f;}
        view(eye,aim,lens,2,.014f*(1-q));macro_ground(*this,m,0,1.38f,k==11?16.0f:9.2f);
        const float xx[]={-.32f,.29f,-.25f,.29f,-.23f,.26f},zz[]={-2.58f,-1.30f,-.05f,1.19f,2.44f,3.67f};
        for(int i=0;i<6;i++){
            V p={xx[i],m.height(xx[i],zz[i])*1.38f+.061f,zz[i]};mark(i,p);
            if(k==11){float dt=(f-(K_SMALL_STEP_0+8*i))/24.f;
                float a=ramp(-.12f,.19f,dt)*(1-ramp(.42f,1.65f,dt));
                if(a>.003f)g.dust(p,.031f,JADE,.47f*a);
            }
        }
    }
    void footprint_step(){
        V p=spline({-1.62f,1.73f,-1.91f},{-1.48f,1.61f,-1.79f},{-1.30f,1.75f,-1.73f},{-1.06f,1.96f,-1.47f},q);
        const float d=(f-K_STAMP_DOWN)/24.f;
        float j=d<0?0:expf(-d*10.f)*sinf(d*12.f)*.033f;
        p.y-=j;view(p,{.09f,-.012f,.20f},41.f,2,.008f*(1-2*q));
        const Plan a{9,g.cam,2.75f,.55f,t};Stamp st(t,true);
        const float load=ramp(.0f,.17f,d)*(1-ramp(.54f,.92f,d));
        const float heel=ramp(.0f,.31f,(f-K_STAMP_UP)/24.f);
        for(size_t i=0;i<st.foot.size();i++){
            auto& bone=st.foot[i];
            if(i<2){bone.center.z+=.066f*load;bone.center.y-=.025f*load;}
            if(i>=3){bone.center.x+=.019f*load*(int((i-3)/4)-1);bone.center.y+=.016f*heel*(1+(i-3)%4);}
        }
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=0;x<g.w;x++){
            const V ray=g.cam.ray((x+.5f)/g.w,(y+.5f)/g.h);float distance;
            V c=earth.earth(a,st,ray,distance);
            c=c*V{1.24f,1.16f,.98f};int i=y*g.w+x;
            g.z[i]=distance>120.f?0.f:1.f/(distance*dot(g.cam.f,ray));
            camera_response.put(&g.rgb[3*i],c);
        }
        if(d>=0&&d<1.37f){
            for(int i=0;i<44;i++){
                float dt=d-hash(i,130)*.112f;if(dt<=0)continue;
                const float angle=hash(i,151)*2*PI,r=.43f+(.49f+.84f*hash(i,277))*dt;
                float x=r*cosf(angle)+.08f,z=r*sinf(angle)+.17f;
                float ground=earth.stamp.height(x,z);
                float y=ground+std::max(.005f,.023f+(.30f+.71f*hash(i,441))*dt-1.52f*dt*dt);
                float rad=.007f+.038f*sq(hash(i,651));
                pebble(g,{x,y,z},{rad,rad*.59f,rad*.83f},lerp({95,91,62},{171,151,99},hash(i,177)),i+612,4,7,.22f,5.f*dt);
            }
        }
    }
    void surface_detail(int k){
        const Grid& b=k==25?ripples:k==26?dried:earth.stamp;V eye,aim{.11f,-.01f,.28f};float fov,restore=0;
        if(k==25){eye=lerp(V{-1.67f,1.25f,-2.07f},V{-.86f,1.76f,-1.83f},q);aim={.23f,-.03f,.35f};fov=37.f;}
        else if(k==26){eye=lerp(V{1.27f,1.57f,-2.f},V{.81f,2.16f,-1.69f},q);fov=38.f;}
        else if(k==28){eye=lerp(V{-1.57f,2.37f,-2.42f},V{-.96f,2.24f,-2.02f},q);fov=42.f;restore=1-at(K_IMPACT_BANK,.43f);}
        else{eye=lerp(V{.66f,2.21f,-2.38f},V{-.02f,2.49f,-2.23f},q);fov=39.4f;restore=at(K_EROSION_WASH,2.21f)*.91f;}
        view(eye,aim,fov,2);macro_ground(*this,b,restore);
        const auto room=daylight(k==25?1:3);
        if(k==25)shallow(*this,b,-.026f,room,false,0,1.19f,.61f);
        if(k==28){float u=at(K_DRAIN,2.90f);shallow(*this,b,lerp(.22f,-.39f,u),room,false,restore,lerp(-4.9f,3.9f,u),.94f*(1-u*.42f));}
        if(k==29){float u=at(K_EROSION_WASH,1.58f);shallow(*this,b,lerp(-.14f,.14f,u),room,false,restore,lerp(4.39f,-.62f,u),.89f*u);}
        if(k==28&&f>=K_IMPACT_BANK-12&&f<K_IMPACT_BANK+14){
            float h=1.05f*(1-at(K_IMPACT_BANK-12,.50f))+.70f*at(K_IMPACT_BANK,.45f);
            stamp_rig({.045f,.005f,.058f},h);
        }
    }
    void stamp_test(){
        const bool after=shot==21;
        const float w=at(K_TEST_DOWN,.33f),load=after?1:w;
        const float reach=after?1:at(K_TEST_UP,1.08f),settle=after?1:at(K_SLUMP,.86f);
        const float descent=smoother((f-(K_TEST_DOWN-38))/38.f);
        float tool=after||sec()<1.01f?3.1f:2.19f*(1-descent)+.028f-.087f*load+2.85f*reach;
        V p=after?lerp(V{-.06f,4.76f,-3.33f},V{.06f,5.85f,-1.21f},q):
            spline({.10f,3.72f,-4.94f},{-.28f,3.29f,-4.85f},{-.07f,3.86f,-4.12f},{.19f,4.78f,-3.71f},q);
        view(p,{.0f,after?.053f:.29f,.096f},40.4f,0,.005f);stage(.47f);
        for(int i=0;i<2;i++){
            const V C={i?-1.56f:1.56f,.088f,.085f};
            mud_plate(C,i==1,load,settle,tool,reach);mark(i,C+V{0,.161f,-1.23f});mark(i+2,C+V{.0f,.038f,.31f});
        }
        // The identical tool remains neutral; only saturation in the right-hand material changes.
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++)for(int x=g.w/2;x<g.w;x++){
            auto* t0=&g.rgb[3*(y*g.w+x)];float r=t0[0],gr=t0[1],b=t0[2];
            const float use=ramp(8.f,31.f,gr-r)*ramp(38.f,81.f,gr),l=luminance({r,gr,b});
            t0[0]=Raster::byte(lerp(r,l*.78f+9.5f,use*.82f));t0[1]=Raster::byte(lerp(gr,l*.89f,use*.79f));
            t0[2]=Raster::byte(lerp(b,l*.792f,use*.77f));
        }
    }
    void edge_rebuild(){
        const bool ero=shot==14;const int event=ero?K_EROSION_POP:K_EDGE_CHIP;
        const float chip=at(event,ero?.91f:.51f),cut=at(event,1.51f);
        auto p=spline({-1.68f,2.98f,-5.01f},{-1.12f,2.49f,-4.28f},{.68f,3.40f,-4.22f},{1.61f,4.14f,-4.50f},q);
        view(p,{.12f,.071f,.05f},40.7f,2);stage(.51f);
        const Grid& b=ero?earth.koum:weather;
        material(*this,b);V O{.08f,.13f,.17f};
        slab(b,O,{2.13f,.79f,1.49f},47,.055f+chip*(ero?.96f:.67f),ero?.49f*cut:0,.027f);
        mark(0,O+V{1.83f-.83f*chip,.106f,-.63f});mark(1,O+V{-.09f,.051f,.44f});
        if(ero)contour(b,O,.59f,JADE,.56f*at(event+38,1.42f),2.13f/1.77f,1.49f/1.78f,.112f);
        for(int i=0;i<52;i++){
            float dt=(f-event)/24.f-hash(i,560)*.58f;if(dt<0)continue;
            const float x0=2.05f-.44f*hash(i,61),y0=.12f-.18f*hash(i,297),z0=-.46f+(hash(i,41)-.5f)*.92f;
            const float a0=.21f+.57f*hash(i,116),stop=.54f+.33f*hash(i,188);
            float travel=std::min(dt,stop),floor=-1.85f,ex=y0+travel*a0-3.79f*travel*travel;
            if(ex<=floor||dt>stop){const float bounce=(dt-stop);ex=floor+.16f*expf(-std::max(0.f,bounce)*6.9f)*sq(sinf(std::max(0.f,bounce)*12.2f));}
            const float rad=.013f+.065f*sq(hash(i,884));
            pebble(g,{x0+(.38f+.73f*hash(i,240))*travel,std::max(floor+rad*.4f,ex),z0-.32f*travel},{rad*1.48f,rad*.64f,rad},
                   lerp({108,93,73},{210,188,146},hash(i,19)),i+417,5,8,.24f,travel*6.6f+i*.6f);
        }
    }
    void prime(int k){
        const bool start=base_shot!=k; if(!start)return;base_shot=k;
        // Plate textures are colour-managed once, then reused in material coordinates.
        if(k==6||k==13){for(const Grid* b:{&earth.koum,&weather,&earth.steps,&pressure})material(*this,*b);}
        if(k==15||k==16||k==32||k==33||k==41||k==42||k==44||k==45||k>=54){material(*this,earth.koum);}
        if(k==23||k==24||k==38||k==39||k==37||k==41||k==42||k==44||k==45||k==58){material(*this,earth.koum);material(*this,rim);}
        if(k==27||k==32||k==44||k==56||k==58)material(*this,dried);
        if(k==27||k==32||k==54||k==55||k==56||k==57||k==58)material(*this,ripples);
        if(k==32)material(*this,pressure);
        if(k==17||k==18||k==19)material(*this,blur);
        if(k==22)material(*this,weather);
        if(k==57||k==64)material(*this,earth.brazil);
        // The comparison banks have different sunlight; dedicated material
        // prepared at first view instead of inheriting the previous profile.
    }
    void draw(int k){
        prime(k);bool field=false,water=false,split=false;float focus=0;
        switch(k){
        case 0:case 1:case 62:prints(k);field=true;split=k!=0;focus=k==0?3.22f:3.71f;break;
        case 4:case 7:case 35:case 40:case 52:story_terrain(k);field=true;water=true;split=k==40;break;
        case 6:case 13:layers();focus=6.0f;break;
        case 8:case 10:case 11:near_tracks(k);field=true;focus=k==11?7.65f:4.33f;break;
        case 9:footprint_step();field=true;focus=2.58f;break;
        case 12:case 14:edge_rebuild();focus=5.31f;break;
        case 15:case 16:scan_scene();break;
        case 17:case 18:case 19:case 22:case 33:case 37:
            measure();field=true;focus=k==18?4.04f:k==19?2.5f:3.2f;break;
        case 20:case 21:stamp_test();focus=5.45f;break;
        case 23:case 24:case 27:case 38:case 39:compare();break;
        case 25:case 26:case 28:case 29:surface_detail(k);field=true;water=k!=26;focus=3.64f;break;
        case 30:case 31:case 36:microscope(*this);focus=k==30?4.33f:4.6f;break;
        case 32:burial();focus=5.49f;break;
        case 41:case 44:age_columns(*this);break;
        case 42:case 45:age_stage(*this);break;
        case 43:pollen_detail(*this);focus=4.41f;break;
        case 47:case 49:case 50:case 60:rift_stage(*this);break;
        case 54:habitats(*this);break;
        case 55:if(sec()<8.50f){swimmer(*this);focus=5.99f;}else fossil_match(*this);break;
        case 56:fossil(*this);break;
        case 57:independent_clues(*this);std::fill(g.z.begin(),g.z.end(),0);split=true;field=true;break;
        case 58:if(f<K_BETTER_FOSSILS)age_columns(*this);else fossil(*this,true);break;
        case 63:rock_answer(*this);break;
        case 64:if(sec()>=5.54f){story_terrain(k);water=true;}else measure();field=true;focus=3.75f;break;
        case 65:
            view({-.31f,2.20f,-6.91f},{.12f,.00f,.21f},46,0);
            specks(63,48,{.18f,.28f,1.5f},{5.48f,2.17f,2.64f},PAPER,.082f);break;
        default:throw std::runtime_error("visual shot not mapped");
        }
        finish_look(field,water,focus,split);
    }
private:
    int base_shot=-1;
};
}
