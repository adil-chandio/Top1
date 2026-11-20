// Native renderer for the production cut after the opening minute.
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main opening_v2_unused
#include "../step-5/cinema-v2/render_cinema.cpp"
#undef main
#pragma GCC diagnostic pop
#include "timeline.hpp"
#include "feature.hpp"

int main(int argc,char** argv){
    using namespace feature;
    if(argc!=7){std::fprintf(stderr,"render-film FIELDS WIDTH HEIGHT FIRST_FRAME END_FRAME PICKS_CSV\n");return 2;}
    try{
        const int w=std::stoi(argv[2]),h=std::stoi(argv[3]),first=std::stoi(argv[4]),end=std::stoi(argv[5]);
        if(w<8||h<8||w>1920||h>1080||first<TAKES[12].a||end>END_FRAME||first>=end)throw std::runtime_error("bad film range");
        std::ofstream trace(argv[6]);trace.precision(8);if(!trace)throw std::runtime_error("trace unavailable");
        Studio s(argv[1],w,h);int i=12;
        for(int f=first;f<end;f++){
            while(f>=TAKES[i].b)++i;
            const Take p=TAKES[i];s.t=f/24.f;s.f=f;
            const float U=clamp((f-p.a)/float(p.b-p.a));s.q=U*.27f+smooth(U)*.73f;s.marks={};
            switch(p.rig){
                case 1:s.floor_scene(p.v);break;
                case 2:s.slab_scene(p.v);break;
                case 3:s.survey(p.v);break;
                case 4:s.grain_scene(p.v);break;
                case 5:world(s,p.v);break;
                case 6:s.valley(p.v);break;
                case 7:strata(s,p.v);break;
                case 8:fault(s,p.v);break;
                case 9:haven(s,p.v);break;
                case 10:fish(s,p.v);break;
                case 11:
                    s.g.begin(s.camera({-.1f,1.28f,-5.6f},{.32f,1.6f,-4.9f},{.41f,.0f,.2f},47),0,s.t);
                    s.specks(871,104,{0,.27f,1.08f},{6.78f,3.04f,3.50f},GOLD,.089f);break;
                default:throw std::runtime_error("unsupported shot rig");
            }
            trace<<f<<','<<i;
            for(auto m:s.marks)trace<<','<<m.x<<','<<m.y<<','<<m.z;
            trace<<'\n';trace.flush();
            if(std::fwrite(s.g.rgb.data(),1,s.g.rgb.size(),stdout)!=s.g.rgb.size())throw std::runtime_error("short frame write");
        }
    }catch(const std::exception& e){std::fprintf(stderr,"film: %s\n",e.what());return 2;}
    return 0;
}
