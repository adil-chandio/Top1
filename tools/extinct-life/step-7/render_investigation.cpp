// Render the visual recut without modifying the previous shot cache or binary.
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main opening_v2_unused
#include "../step-5/cinema-v2/render_cinema.cpp"
#undef main
#pragma GCC diagnostic pop
#include "timeline.hpp"
#include "finale_v3.hpp"

int main(int argc,char** argv){
    using namespace evidence;
    if(argc!=7){std::fprintf(stderr,"render-investigation FIELDS WIDTH HEIGHT FIRST END TRACE\n"
        "                     FIELDS WIDTH HEIGHT --samples FRAME_FILE TRACE\n");return 2;}
    try{
        const int w=std::stoi(argv[2]),h=std::stoi(argv[3]);std::vector<int> frames;
        if(std::string(argv[4])=="--samples"){
            std::ifstream input(argv[5]);int f;
            while(input>>f)frames.push_back(f);
            if(!input.eof())throw std::runtime_error("invalid sample list");
        }else{
            const int first=std::stoi(argv[4]),end=std::stoi(argv[5]);
            if(first<0||first>=end||end>END_FRAME)throw std::runtime_error("invalid range");
            for(int f=first;f<end;f++)frames.push_back(f);
        }
        if(w<16||w%2||h<8||frames.empty()||frames.front()<0||frames.back()>=END_FRAME||
           std::adjacent_find(frames.begin(),frames.end(),std::greater_equal<int>())!=frames.end())
            throw std::runtime_error("invalid or unsorted render samples");
        CutSet s(argv[1],w,h);std::ofstream trace(argv[6]);trace.precision(8);
        if(!trace)throw std::runtime_error("could not open trace");
        int k=0;
        for(int f:frames){
            while(f>=TAKES[k].b)++k;
            s.t=f/24.f;s.f=f;s.shot=k;s.marks={};
            const float q=clamp((f-TAKES[k].a)/float(TAKES[k].b-TAKES[k].a-1));
            s.q=q*.28f+.72f*smooth(q);
            switch(k){
                case 0:case 1:case 62:s.intro(k);break;
                case 2:case 3:case 5:case 34:case 46:case 48:case 51:case 53:case 59:case 61:s.atlas.chapter(s,k);break;
                case 4:case 40:case 52:s.terrain(k);break;
                case 6:case 13:s.layers();break;
                case 12:case 14:s.edge_scene();break;
                case 15:case 16:s.scan_scene();break;
                case 17:case 18:case 19:case 22:case 33:case 37:case 64:s.measure();break;
                case 20:case 21:s.mud();break;
                case 23:case 24:case 27:case 38:case 39:s.compare();break;
                case 30:case 31:case 36:s.micro();break;
                case 32:s.burial();break;
                case 41:case 42:case 44:case 45:age_columns(s);break;
                case 43:pollen_detail(s);break;
                case 47:case 49:case 50:case 60:fracture(s);break;
                case 54:pools(s);break;
                case 55:if(s.sec()<8.5f)fish_pass(s);else fossil_match(s);break;
                case 56:
                    if(s.sec()<5.54f)fossil(s);
                    else s.atlas.chapter(s,57);
                    break;
                case 57:independent_clues(s);break;
                case 58:
                    if(f<K_BETTER_DATES)s.atlas.chapter(s,57);
                    else if(f<K_BETTER_FOSSILS)age_columns(s);
                    else fossil(s,true);
                    break;
                case 63:answer(s);break;
                case 65:
                    s.view({-.15f,1.30f,-5.51f},{.31f,.0f,.26f},46.f,0);
                    s.specks(178,51,{0,.34f,1.05f},{5.79f,3.01f,3.40f},HONEY,.032f);break;
                default:throw std::runtime_error("requested shot is intentionally retained");
            }
            trace<<f<<','<<k;for(auto v:s.marks)trace<<','<<v.x<<','<<v.y<<','<<v.z;
            trace<<'\n';trace.flush();
            const auto& pix=s.g.rgb;
            if(std::fwrite(pix.data(),1,pix.size(),stdout)!=pix.size())throw std::runtime_error("short raw frame");
        }
    }catch(const std::exception& e){std::fprintf(stderr,"investigation render: %s\n",e.what());return 2;}
    return 0;
}
