#include "world.hpp"
#include <memory>

namespace portrait {
constexpr int FPS=30,LAST=1020;
constexpr std::array<int,11> cuts={0,82,169,282,365,442,501,574,810,947,LAST};

struct Director {
    Raster r;Tex clay,hide;
    Foot foot;
    Sediment crisp{foot,false},slip{foot,true};
    const std::string fields;
    std::unique_ptr<Globe> earth;
    std::unique_ptr<Field> brazil,cameroon;
    std::unique_ptr<Outcrop> silt,shale;
    std::array<V,4> pins{};
    float contact=0,drop=0,angle=0;
    Director(int w,int h,std::string f,const std::string& mats):r(w,h),clay(mats+"/silt.u8"),hide(mats+"/scales.u8"),fields(std::move(f)){}
    void sites(){if(!brazil){brazil=std::make_unique<Field>(fields+"/brazil.field");cameroon=std::make_unique<Field>(fields+"/koum.field");silt=std::make_unique<Outcrop>(*brazil,true);shale=std::make_unique<Outcrop>(*cameroon,false);}}
    Cam macro_cam(int k,float t){
        const float ar=float(r.w)/r.h;
        if(k==1||k==2)return Cam({-.26f,3.64f,2.20f},{0,.018f,.231f},47.1f,ar,.037f);
        if(k==3){float a=quint(t/2.76f);
            return Cam(mix(V{-1.40f,1.79f,2.26f},V{-1.02f,1.51f,2.10f},a),mix(V{-.32f,-.038f,.42f},V{-.44f,-.050f,.49f},a),38.4f,ar,mix(.092f,-.025f,a));}
        V p0={-.72f,2.14f,2.80f},a0={-.052f,.085f,.230f};
        if(t<0){float a=quint((t+(LAST-cuts[9])/float(FPS))/((LAST-cuts[9])/float(FPS)-.17f));
            return Cam(mix(V{-1.61f,2.03f,3.04f},p0,a),mix(V{-.22f,.016f,.40f},a0,a),mix(44.6f,49.2f,a),ar,mix(.102f,.028f,a));}
        float d=cl((t-.167f)/2.7f),f=quint(d),impact=t<.166f?0.f:.023f*expf(-(t-.166f)*14.f)*sinf((t-.166f)*23.f);
        return Cam(mix(p0,V{-.52f,2.15f,2.59f},f)+V{impact*.26f,-impact,0},mix(a0,V{.025f,-.034f,.27f},f),49.2f,ar,mix(.028f,-.045f,f));
    }
    void mud(int k,float t){
        const bool firm=k==1,hero=k==0||k==9;
        float local=k==3?float(cuts[3]-cuts[2])/FPS+t:t;
        Motion m(local,!firm,hero);
        if(local<-.124f){const float a=quint((-local-.124f)/((LAST-cuts[9])/float(FPS)-.124f));m.y+=1.40f*a;m.x-=.35f*a;m.z-=.27f*a;}
        contact=m.press;drop=m.slump;angle=m.y;
        const auto c=macro_cam(k,t);r.begin(c);r.sky({.024f,.036f,.027f},{.015f,.038f,.052f});
        const bool within=m.y<2.29f||local<0;
        Shadow s;if(within)s.build(foot,[&](V p){return m.pose(p);});
        auto& bed=firm?crisp:slip;
        bed.draw(r,m,clay,within?&s:nullptr,r.cam.pos);
        if(within)skin(r,foot,m,hide);
        particles(r,m,k==1?194:k==2?319:418);
        for(int i=0;i<97;++i){
            float x=4.1f*(hash(i,473)-.5f),z=3.9f*(hash(i,65)-.45f);
            if(foot.print(x,z)<.15f||sq(x*.65f)+sq(z-.21f)<.22f)continue;
            const float b=.011f+.048f*pow4(hash(i,668));
            V p={x,bed.surface(x,z,m)+.06f*b,z};
            V al=mix(m.wet?V{.088f,.071f,.053f}:V{.16f,.089f,.041f},V{.29f,.195f,.113f},hash(i,41)*.74f);
            chip(r,p,{b,b*.51f,b*.84f},al,i+306,m.wet);
        }
        if(m.wet){
            // One distinct release at the lip and several smaller grains that
            // settle into the already formed lateral toe, not another impact.
            float start=k==3?24.f/FPS:m.release+.40f;
            float dt=(k==3?t:local)-start;
            for(int i=0;i<20;++i){float q=dt-(i==0?0:.31f*hash(i,22));if(q<0||q>.61f)continue;
                float e=smooth(.0f,.6f,q),x=-.66f+.069f*hash(i,61)+.138f*e,z=.49f+.105f*hash(i,75)+.031f*e;
                const float b=(i==0?.033f:.009f)+.024f*sq(hash(i,151));
                float y=bed.surface(x,z,m)+(.71f*b+.015f)*(1-e)+.049f*sinf(PI*e);
                chip(r,{x,y,z},{b,b*.54f,b*.84f},{.144f,.088f,.046f},i+184,true);
            }
        }
        r.flush();r.optics(c.project({0,0,.28f}).z,k==3?.37f:.91f,k==1||k==2?.080f:.145f);
    }
    void rock(int k,float t){
        sites();float a=quint(t/(float(cuts[k+1]-cuts[k])/FPS));
        const bool w=k==4;
        const V p=w?mix(V{.10f,2.54f,2.52f},V{-.44f,2.63f,2.22f},a):mix(V{-.35f,2.43f,2.17f},V{.67f,3.17f,2.12f},a);
        const V q=w?mix(V{.024f,.012f,.142f},V{.014f,-.035f,.168f},a):mix(V{.065f,-.01f,.10f},V{.07f,.018f,.185f},a);
        Cam c(p,q,w?46.3f:46.9f,float(r.w)/r.h,mix(w?-.039f:.057f,w?-.093f:-.090f,a));
        r.begin(c);r.sky({.033f,.041f,.047f},{.028f,.050f,.067f});
        (w?silt:shale)->draw(r,clay,t);r.flush();r.optics(c.project(q).z,.83f,.173f);
    }
    void layer(float t){
        sites();float a=quint(t/(float(cuts[9]-cuts[8])/FPS));
        V p=mix(V{-1.14f,1.61f,3.58f},V{.53f,.84f,3.13f},a),q=mix(V{-.13f,-.30f,.86f},V{.050f,-.36f,1.12f},a);
        Cam c(p,q,mix(47.6f,48.3f,a),float(r.w)/r.h,mix(-.076f,.010f,a));
        r.begin(c);r.sky({.048f,.068f,.079f},{.012f,.023f,.041f});
        stratigraphy(r,*brazil,clay,t);r.flush();r.optics(c.project(q).z,.93f,.16f);
    }
    int frame(int n){
        int k=int(std::upper_bound(cuts.begin(),cuts.end(),n)-cuts.begin())-1;
        float t=(n-cuts[k])/float(FPS);pins={};contact=drop=angle=0;
        if(k<=3||k==9)mud(k,k==9?(n-LAST)/float(FPS):t);
        if(k==4||k==5)rock(k,t);
        if(k==6||k==7){
            if(!earth)earth=std::make_unique<Globe>(fields);
            float x=n/float(FPS);earth->image(r,x,quint((x-20.45f)/1.39f),pins);
        }
        if(k==8)layer(t);
        return k;
    }
};
}

int main(int argc,char** argv){
    using namespace portrait;
    if(argc!=8){std::fprintf(stderr,"portrait FIELDS WIDTH HEIGHT BEGIN END TRACE MATERIALS (or --frames INPUT instead of BEGIN END)\n");return 2;}
    try{
        const int w=std::stoi(argv[2]),h=std::stoi(argv[3]);std::vector<int> frames;
        if(w<180||h<320||w>1296||h>2304||w*16!=h*9)throw std::runtime_error("renderer needs portrait 9:16");
        if(std::string(argv[4])=="--frames"){std::ifstream f(argv[5]);int n;while(f>>n)frames.push_back(n);if(!f.eof())throw std::runtime_error("frame list");}
        else{int a=std::stoi(argv[4]),b=std::stoi(argv[5]);if(a<0||b>LAST||a>=b)throw std::runtime_error("invalid frame interval");for(int j=a;j<b;++j)frames.push_back(j);}
        if(frames.empty()||frames.front()<0||frames.back()>=LAST||std::adjacent_find(frames.begin(),frames.end(),std::greater_equal<int>())!=frames.end())throw std::runtime_error("invalid frame sequence");
        Director s(w,h,argv[1],argv[7]);std::ofstream trace(argv[6]);trace.precision(9);
        if(!trace)throw std::runtime_error("could not write trace");
        std::fprintf(stderr,"PORTRAIT 3D · %zu articulated vertices, %zu welded triangles · slump mass delta %.10f\n",s.foot.orig.size(),s.foot.faces.size(),s.slip.relaxation_relative_error);
        for(int f:frames){
            int k=s.frame(f);trace<<f<<','<<k<<','<<s.contact<<','<<s.drop<<','<<s.angle;
            for(auto p:s.pins)trace<<','<<p.x<<','<<p.y<<','<<p.z;
            trace<<'\n';trace.flush();
            if(std::fwrite(s.r.rgb.data(),1,s.r.rgb.size(),stdout)!=s.r.rgb.size())throw std::runtime_error("closed RGB stream");
            std::fflush(stdout);
        }
    }catch(const std::exception& e){std::fprintf(stderr,"%s\n",e.what());return 1;}
}
