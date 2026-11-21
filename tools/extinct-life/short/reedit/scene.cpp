#include "../world.hpp"
#include "recut_clock.hpp"
#include <memory>

namespace recut {
using namespace portrait;
using namespace recut_clock;

// March the actual generated outcrop rim; these coordinates never trace a
// specimen or cross the globe. Tone at the edge blends into the same bed.
struct Survey {
    struct Segment{V a,b,bank;float az;};
    std::vector<Segment> geometry;
    explicit Survey(const Outcrop& o){
        constexpr int N=Outcrop::N;
        for(int j=1;j<N-1;++j)for(int i=1;i<N-1;++i){
            int a=j*N+i;const V c=o.xyz[a];
            if(fabsf(c.x)>1.35f||fabsf(c.z)>1.33f)continue;
            std::array<V,4> p{};int z=0,dir[4]={a,a+1,a+1+N,a+N};
            for(int e=0;e<4;++e){int l=dir[e],r=dir[(e+1)%4];float u=o.geom[l].mark-.40f,v=o.geom[r].mark-.40f;
                if((u>=0)!=(v>=0))p[z++]=mix(o.xyz[l],o.xyz[r],u/(u-v));}
            for(int e=0;e+1<z;e+=2){
                if(length(p[e+1]-p[e])<.0004f)continue;
                V base=o.geom[a].rgb()*1.02f;
                float ang=atan2f(c.x,c.z-.1f);if(ang<0)ang+=2*PI;
                geometry.push_back({p[e],p[e+1],base,ang});
            }
        }
    }
    void draw(Raster& r,bool warm,float t)const{
        for(const auto& s:geometry){
            float q=t-s.az*.122f,alpha=smooth(.02f,.20f,q)*(1-.83f*smooth(.52f,1.16f,q));
            if(alpha<.012f)continue;
            float width=mix(.0035f,.0080f,alpha);
            V e=unit(cross(s.b-s.a,{0,1,0}))*width,dy={0,.009f,0};
            V a=s.a+dy,b=s.b+dy;
            V c=film.grade(mix(s.bank,warm?V{.94f,.574f,.182f}:V{.24f,.66f,.53f},.27f+.59f*alpha));
            P aa=r.proj({a-e,c}),ab=r.proj({a+e,c}),ba=r.proj({b-e,c}),bb=r.proj({b+e,c});
            r.tri(aa,ba,bb);r.tri(aa,bb,ab);
        }
    }
};

struct Edit {
    Raster r;
    Tex clay,skin_tex;
    Foot foot;
    Sediment crisp{foot,false},slip{foot,true};
    std::unique_ptr<Field> brazil,cameroon;
    std::unique_ptr<Outcrop> silt,shale;
    std::unique_ptr<Survey> warm_survey,cool_survey;
    std::unique_ptr<Globe> earth;
    const std::string fields;
    std::array<V,4> pins{};
    float contact=0,slump=0,ankle=0,phase=0;

    Edit(int w,int h,const std::string& dir,const std::string& mats):r(w,h),clay(mats+"/silt.u8"),skin_tex(mats+"/scales.u8"),fields(dir){}
    void sites(){
        if(brazil)return;
        brazil=std::make_unique<Field>(fields+"/brazil.field");cameroon=std::make_unique<Field>(fields+"/koum.field");
        silt=std::make_unique<Outcrop>(*brazil,true);shale=std::make_unique<Outcrop>(*cameroon,false);
        warm_survey=std::make_unique<Survey>(*silt);cool_survey=std::make_unique<Survey>(*shale);
    }
    float ar()const{return float(r.w)/r.h;}
    static float impulse(float t,float a){return t<0?0.f:a*expf(-t*15.7f)*sinf(30.f*t);}
    Cam wet_cam(int k,float t){
        // Firm and soft are a genuine match, including the dolly move. The
        // next closer view continues soft time and tracks the failing lip.
        if(k==1||k==2){float f=quint(t/1.75f),p=impulse(t-5.f/fps,.030f);
            return Cam(mix(V{-.29f,3.78f,2.37f},V{-.09f,3.47f,2.13f},f)+V{-.27f*p,-p,0},
                       mix(V{.027f,.012f,.202f},V{.004f,.008f,.258f},f),47.f,ar(),mix(.053f,.018f,f));}
        if(k==3){float a=quint((t+.045f)/1.43f),impact=impulse(t-(lip_chip-cuts[3])/float(fps),.011f);
            return Cam(mix(V{-1.60f,1.64f,2.19f},V{-1.45f,1.23f,1.85f},a)+V{0,-impact,impact*.2f},
                       mix(V{-.28f,-.035f,.475f},V{-.43f,-.049f,.517f},a),mix(43.f,41.1f,a),ar(),mix(.065f,-.053f,a));}
        const V p0={-.74f,2.22f,2.90f},a0={-.054f,.09f,.238f};
        if(t<0){float a=smooth(-(last-returning)/float(fps),-.020f,t);
            return Cam(mix(V{-1.14f,2.47f,3.13f},p0,a),mix(V{-.127f,.041f,.312f},a0,a),mix(46.2f,48.4f,a),ar(),mix(.104f,.021f,a));}
        float f=quint((t-.175f)/1.65f),j=impulse(t-5.f/fps,.083f);
        return Cam(mix(p0,V{-.28f,2.41f,2.48f},f)+V{-.24f*j,-j,j*.20f},
                   mix(a0,V{.036f,-.023f,.26f},f),mix(48.4f,48.1f,f),ar(),mix(.021f,-.063f,f)+j*.14f);
    }
    void grit(Sediment& bed,const Motion& m,int seed){
        for(int i=0;i<102;++i){
            float x=4.14f*(hash(i,473)-.5f),z=4.02f*(hash(i,65)-.44f);
            if(foot.print(x,z)<.15f||sq(x*.65f)+sq(z-.21f)<.22f)continue;
            const float b=.011f+.048f*pow4(hash(i,668));
            V p={x,bed.surface(x,z,m)+.08f*b,z};
            V c=mix(m.wet?V{.072f,.064f,.051f}:V{.14f,.091f,.040f},V{.32f,.221f,.138f},hash(i,41)*.79f);
            chip(r,p,{b,b*.49f,b*.84f},c,i+seed,m.wet);
        }
    }
    void tumble(Sediment& bed,const Motion& m,float dt,bool macro){
        const float fade=1-smooth(.38f,.76f,dt);
        for(int i=0;i<(macro?35:20);++i){
            float t=dt-(i==0?0.f:hash(i,116)*.26f);if(t<0||t>.76f)continue;
            float w=smooth(.0f,.46f,t),k=hash(i,32),j=hash(i,44);
            float x=-.713f+.118f*k+(.115f+.12f*j)*w,z=.428f+.224f*j+.066f*w;
            const float size=(i==0&&macro?.039f:.009f)+.030f*pow4(hash(i,81));
            const float b=size*mix(.82f,1.f,fade);
            const float y0=bed.surface(-.713f+.118f*k,.428f+.224f*j,m)+.27f*b;
            // Fragments start half-buried at the crest and fall toward the
            // bowl. Collide with the evolving bed; no rising pebble pops.
            const float ground=bed.surface(x,z,m)+(.23f+.22f*(1-w))*b;
            const float y=std::max(ground,y0-.69f*t*t+.24f*b*sinf(PI*w));
            chip(r,{x,y,z},{b,b*(.35f+.29f*k),b*.81f},{.159f,.089f,.040f},i+184,true);
        }
    }
    void mud(int k,float t,int n){
        // Motion is expressed in physical seconds; attach camera cut and late
        // chip tangent to the exact same continually relaxing soft surface.
        const bool firm=k==1,hero=k==0||k==10;
        float s=hero?t:(n-cuts[firm?1:2]+5)/float(fps);
        if(!hero)s+=(2.f/fps)*smooth(.32f,1.05f,s);
        if(k==3)s+=.93f*smooth(.00f,1.46f,t);
        if(hero&&s>=0){
            // Short, motion-continuous launch slightly earlier than V1.
            s+=.036f*smooth(.235f,.86f,s);
        }
        Motion m(s,!firm,hero);
        if(m.wet&&!hero){
            // Cohesive secondary edge failure is explicitly keyed to the chip.
            float after=(n-lip_chip)/float(fps);
            m.slump=std::min(.84f,m.slump)+.16f*smooth(-.023f,.43f,after);
        }
        if(s<-.124f){float a=quint((-s-.124f)/((last-returning)/float(fps)-.124f));m.y+=.84f*a;m.x-=.32f*a;m.z-=.25f*a;}
        contact=m.press;slump=m.slump;ankle=m.y;
        auto c=wet_cam(k,t);r.begin(c);r.sky({.024f,.034f,.029f},{.015f,.038f,.054f});
        const bool in=m.y<2.29f||s<0;
        Shadow shadow;if(in)shadow.build(foot,[&](V v){return m.pose(v);});
        auto& bed=firm?crisp:slip;
        bed.draw(r,m,clay,in?&shadow:nullptr,c.pos);
        if(in)skin(r,foot,m,skin_tex);
        particles(r,m,firm?194:k==2?319:418);
        grit(bed,m,306);
        if(m.wet){
            float dt=k==3?(n-lip_chip)/float(fps):s-m.release-.33f;
            if(dt>=0&&dt<.77f)tumble(bed,m,dt,k==3);
        }
        r.flush();r.optics(c.project(k==3?V{-.486f,0,.51f}:V{0,0,.28f}).z,k==3?.21f:.94f,k==3?.114f:.107f);
    }
    void comparison(float t){
        // End points of the same simulation, equal scale and projection.
        // The texture and angles are unmodified; two central crops move as one.
        float k=quint(t/1.39f);
        Cam cam(mix(V{.19f,5.26f,1.89f},V{-.12f,5.04f,2.13f},k),{.020f,-.011f,.235f},51.3f,ar(),mix(.024f,-.041f,k));
        int h0=int(r.h*.43f),yTop=(r.h-h0)/2,yBottom=h0/2+int(r.h*.126f);
        const size_t stride=3*r.w;
        Motion a(2.42f,false,false),b(4.97f,true,false);
        r.begin(cam);r.sky({.026f,.034f,.03f},{.021f,.035f,.047f});crisp.draw(r,a,clay,nullptr,cam.pos);grit(crisp,a,306);r.flush();
        std::vector<uint8_t> slice(r.rgb.begin()+yTop*stride,r.rgb.begin()+(yTop+h0)*stride);
        r.begin(cam);r.sky({.026f,.034f,.03f},{.021f,.035f,.047f});slip.draw(r,b,clay,nullptr,cam.pos);grit(slip,b,306);r.flush();
        std::memmove(r.rgb.data()+h0*stride,r.rgb.data()+yBottom*stride,(r.h-h0)*stride);
        std::copy(slice.begin(),slice.end(),r.rgb.begin());contact=1;slump=b.slump;ankle=b.y;
    }
    void fossil(int k,float t){
        sites();const bool br=k==5;float d=(cuts[k+1]-cuts[k])/float(fps),a=quint(t/d),kick=smooth(0,.37f,t);
        const V p=br?mix(V{-.36f,2.89f,2.83f},V{.42f,2.72f,2.33f},.63f*a+.37f*kick):mix(V{.29f,2.91f,2.52f},V{-.52f,2.62f,2.27f},.71f*a+.29f*kick);
        const V q=mix(V{.032f,.013f,.164f},V{.052f,-.03f,.211f},a);
        Cam c(p,q,mix(44.4f,45.3f,a),ar(),br?mix(-.083f,-.016f,a):mix(.063f,-.042f,a));
        r.begin(c);r.sky({.035f,.038f,.037f},{.027f,.047f,.061f});
        (br?silt:shale)->draw(r,clay,t);(br?warm_survey:cool_survey)->draw(r,br,t);
        r.flush();r.optics(c.project(q).z,.59f,.13f);
    }
    void globe(int n){
        if(!earth)earth=std::make_unique<Globe>(fields);
        float t=(n-today)/float(fps),a=quint(t*.47f),u=cl((n-wipe_begin)/float(wipe_end-wipe_begin));
        phase=quint(u);float end=quint((n-wipe_end)/float(strata-wipe_end));
        // Drift on entry, then push in under the map rewind. Before/after
        // textures stay independent; the camera and viewport never jump.
        float lat=mix(8.8f,5.4f,a)-3.2f*end,lon=mix(-19.3f,-15.3f,a)+4.30f*end;
        float take=1.f-quint(t/.81f),breath=sin(PI*u);
        V p=geo(lat,lon)*(4.13f+.25f*take-.23f*end+.14f*breath),z=unit(p),x=unit(cross(-z,{0,1,0})),y=cross(x,-z);
        Cam c(p,x*.048f-y*.076f,55.f,ar(),mix(.103f,.022f,a)-.088f*end+.05f*breath);
        earth->image(r,n/float(fps),phase,pins,c,true);
    }
    void rock_layers(float t){
        sites();float a=quint(t/((returning-strata)/float(fps))),x=impulse(t-14.f/fps,.028f);
        V p=mix(V{-1.20f,1.67f,3.78f},V{.38f,.87f,3.16f},a)+V{x*.24f,-x,0},q=mix(V{-.10f,-.33f,.89f},V{.06f,-.38f,1.09f},a);
        Cam c(p,q,mix(48.1f,46.4f,a),ar(),mix(-.103f,.046f,a));
        r.begin(c);r.sky({.044f,.065f,.079f},{.012f,.023f,.041f});
        stratigraphy(r,*brazil,clay,t);r.flush();r.optics(c.project(q).z,.76f,.127f);
    }
    int draw(int n){
        int k=int(std::upper_bound(cuts.begin(),cuts.end(),n)-cuts.begin())-1;
        float t=(n-cuts[k])/float(fps);pins={};contact=slump=ankle=phase=0;
        if(k<=3||k==10)mud(k,k==10?(n-last)/float(fps):t,n);
        else if(k==4)comparison(t);
        else if(k==5||k==6)fossil(k,t);
        else if(k==7||k==8)globe(n);
        else if(k==9)rock_layers(t);
        return k;
    }
};
}

int main(int argc,char** argv){
    using namespace recut;
    if(argc!=7){std::fprintf(stderr,"usage: recut FIELDS MATERIALS WIDTH HEIGHT FRAME_LIST TRACE\n");return 2;}
    try{
        int w=std::stoi(argv[3]),h=std::stoi(argv[4]);
        if(w<180||h<320||w>1296||h>2304||w*16!=h*9)throw std::runtime_error("portrait 9:16 required");
        std::ifstream file(argv[5]);std::vector<int> frames;int n;while(file>>n)frames.push_back(n);
        if(frames.empty()||!file.eof()||frames.front()<0||frames.back()>=last||std::adjacent_find(frames.begin(),frames.end(),std::greater_equal<int>())!=frames.end())throw std::runtime_error("invalid frame list");
        std::ofstream trace(argv[6]);if(!trace)throw std::runtime_error("trace unavailable");trace.precision(9);
        Edit edit(w,h,argv[1],argv[2]);
        std::fprintf(stderr,"PORTRAIT RECUT · %zu articulated vertices, %zu triangles · slump mass delta %.10f\n",edit.foot.orig.size(),edit.foot.faces.size(),edit.slip.relaxation_relative_error);
        for(int f:frames){
            int k=edit.draw(f);trace<<f<<','<<k<<','<<edit.contact<<','<<edit.slump<<','<<edit.ankle<<','<<edit.phase;
            for(auto p:edit.pins)trace<<','<<p.x<<','<<p.y<<','<<p.z;
            trace<<'\n';trace.flush();
            if(std::fwrite(edit.r.rgb.data(),1,edit.r.rgb.size(),stdout)!=edit.r.rgb.size())throw std::runtime_error("closed RGB stream");
            std::fflush(stdout);
        }
    }catch(const std::exception& e){std::fprintf(stderr,"%s\n",e.what());return 1;}
}
