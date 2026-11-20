// Evidence atlas. Both epochs are sampled from the locked geographic fields.
// The wipe exposes two separate maps; there is no plate/coastline interpolation.
#pragma once
#include "../step-6/feature.hpp"

namespace evidence {
using namespace feature;
constexpr V HONEY{239,184,111}, JADE{139,227,206}, PAPER{232,224,201};

struct MapWindow {
    float lon,lat,span;
    float x0=.035f,x1=.965f,y0=.172f,y1=.944f;
};

struct Atlas {
    std::array<Texture,2> maps;
    static constexpr float xmin=-111, xmax=100, north=68, south=-70;
    static constexpr float coord[2][2][2]={{{-6.7342701f,-38.2620659f},{8.2916667f,14.5166667f}},
      {{-5.942546594f,-5.730008929f},{-5.688025016f,5.056435421f}}};
    const Texture& bake(const Render& model,bool old){
        auto& out=maps[old];if(out.w)return out;
        const auto& g=old?model.ancient:model.modern;
        out.w=2688;out.h=1696;out.rgb.resize(size_t(out.w)*out.h);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<out.h;y++){
            float lat=lerp(north,south,(y+.5f)/out.h);
            for(int x=0;x<out.w;x++){
                float lon=lerp(xmin,xmax,(x+.5f)/out.w);
                auto s=Grid::all(g.map(lon/360+.5f,.5f-lat/180,true));
                const float shelf=ramp(-.139f,-.012f,s.h), altitude=ramp(.000f,.125f,s.h);
                const float l=clamp(.52f+.61f*(s.gx+s.gy*.63f)),coast=1-sq(2*s.m-1);
                const float depth=1-ramp(-.12f,-.006f,s.h),b=s.h*81.f;
                const float bath=(1-ramp(.066f,.22f,fabsf(b-roundf(b))))*ramp(.04f,.20f,fabsf(s.gx)+fabsf(s.gy));
                V sea=lerp({19,39,58},{31,73,80},shelf*.83f)+V{7,13,13}*(bath*(.29f+.58f*depth));
                V land=lerp(old?V{85,116,91}:V{91,122,98},old?V{213,182,123}:V{197,173,128},clamp(.10f+.71f*altitude+.20f*s.k));
                const float grain=.91f+.105f*hash(x/2,y/2)+.05f*fnoise(lon*2.f,lat*2.f);
                V c=lerp(sea,land*(.62f+.60f*l)*grain,ramp(.15f,.81f,s.m));
                c+=V{35,56,46}*(coast*.45f)+V{9,22,18}*(s.m*bath);
                const float t=std::max(1-ramp(.034f,.115f,fabsf(lat-10.f*roundf(lat*.1f))),1-ramp(.034f,.115f,fabsf(lon-10.f*roundf(lon*.1f))));
                c+=V{13,26,24}*t;
                out.rgb[y*out.w+x]=uint32_t(Raster::byte(c.x))|(uint32_t(Raster::byte(c.y))<<8)|(uint32_t(Raster::byte(c.z))<<16);
            }
        }
        return out;
    }
    static float vspan(const Raster& g,const MapWindow& m){return m.span*((m.y1-m.y0)*g.h)/((m.x1-m.x0)*g.w);}
    static V pt(const Raster& g,const MapWindow& m,float lat,float lon){
        return {lerp(m.x0,m.x1,.5f+(lon-m.lon)/m.span),lerp(m.y0,m.y1,.5f-(lat-m.lat)/vspan(g,m)),1};
    }
    static V loc(const Raster& g,const MapWindow& m,bool old,int i){return pt(g,m,coord[old][i][0],coord[old][i][1]);}
    void draw(Studio& s,MapWindow m,int k,float wipe=-1,float focus=0){
        auto& g=s.g;
        const bool old=(k==3||k==46||k==48||k==51||k==53||k==59||k==54||k==57);
        const auto& live=bake(s.earth,old);
        const Texture* past=NULL;
        if(wipe>=0)past=&bake(s.earth,false);
        const float hspan=vspan(g,m),cx=m.lon,cy=m.lat;
        const int x0=int(m.x0*g.w),x1=int(m.x1*g.w),y0=int(m.y0*g.h),y1=int(m.y1*g.h);
        #pragma omp parallel for schedule(static)
        for(int y=0;y<g.h;y++){
            float yy=(y+.5f-y0)/(y1-y0),lat=lerp(cy+.5f*hspan,cy-.5f*hspan,yy),v=(north-lat)/(north-south);
            for(int x=0;x<g.w;x++){
                const float xx=(x+.5f-x0)/(x1-x0),lon=lerp(cx-.5f*m.span,cx+.5f*m.span,xx);const int q=y*g.w+x;
                V c;
                if(xx>=0&&xx<1&&yy>=0&&yy<1){
                    const float u=(lon-xmin)/(xmax-xmin);
                    const float cut=xx-(wipe*1.176f-.08f)+(yy-.5f)*.142f;
                    const uint32_t p=(past&&cut>0?*past:live).at(u,v);
                    c={float(p&255),float((p>>8)&255),float(p>>16)};
                    c=c*(1-.19f*clamp(sq((xx-.5f)*1.66f)+sq((yy-.53f)*1.58f)));
                    if(past)c+=V{105,159,143}*(1-ramp(.0016f,.021f,fabsf(cut)))*ramp(0.f,.08f,wipe)*(1-ramp(.85f,1.f,wipe));
                    if(focus>.001f){
                        const float R0=sq((lon+.39f)/11.8f)+sq((lat+5.2f)/5.5f);
                        const float a=(1-ramp(.22f,1.90f,R0))*focus;
                        // Only a softly bounded context area, never a migration line.
                        c=lerp(c,c*1.13f+V{16,35,9},a*ramp(70.f,138.f,c.x+c.y*.55f));
                    }
                }else{
                    const float b=1-clamp(sq((float(x)/g.w-.45f)*1.9f)+sq((float(y)/g.h-.13f)*.91f));
                    c=lerp({10,16,21},{21,32,36},b*b);
                }
                g.rgb[3*q]=Raster::byte(c.x);g.rgb[3*q+1]=Raster::byte(c.y);g.rgb[3*q+2]=Raster::byte(c.z);
                g.z[q]=0;
            }
        }
        const V a=loc(g,m,old,0),b=loc(g,m,old,1);s.marks[0]=a;s.marks[1]=b;
        s.marks[2]=loc(g,m,false,0);s.marks[3]=loc(g,m,false,1);
        s.marks[4]={m.x0,m.y0,1};s.marks[5]={m.x1,m.y1,1};
        for(int i=0;i<6;i++){
            const float t=i/5.f;
            s.marks[6+i]=lerp(a,b,t)+V{0,.033f*sinf(PI*t),0};
        }
    }
    void chapter(Studio& s,int k){
        MapWindow m={-12.8f,1.15f,89.f};const float q=s.q;
        float wipe=-1,focus=0;
        switch(k){
            case 2:break;
            case 3:wipe=s.at(K_REWIND_SCAN,.96f);break;
            case 5:m={lerp(-12.8f,14.57f,q),lerp(1.15f,8.1f,q),lerp(89.f,24.4f,q)};break;
            case 34:m={lerp(-12.8f,-38.12f,q),lerp(1.15f,-6.7f,q),lerp(89.f,27.4f,q)};break;
            case 46:m={lerp(-12.8f,-.61f,q),lerp(1.15f,-5.1f,q),lerp(89.f,57.5f,q)};break;
            case 48:m={-8.3f,2.0f,lerp(84.f,72.0f,q)};break;
            case 51:m={-6.4f,1.3f,lerp(71.f,58.f,q)};focus=.30f;break;
            case 53:m={-6.8f,1.15f,lerp(81.f,65.f,q)};focus=s.at(K_RANGE,.74f);break;
            case 54:m={-.55f,-5.3f,39.0f};focus=.63f;break;
            case 57:m={-7.4f,1.2f,80.0f};break;
            case 59:m={lerp(-7.4f,-12.8f,q),1.15f,lerp(71.f,89.f,q)};focus=.72f*(1-ramp(.32f,.88f,q));break;
            case 61:m={-12.8f,1.15f,89.f};break;
            case 62:m={-12.8f,1.15f,89.f};break;
            default:break;
        }
        draw(s,m,k,wipe,focus);
    }
};
}
