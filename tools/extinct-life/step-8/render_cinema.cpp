// Animation and composite inputs on the unchanged 24 fps grid.
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main archive_opening_main
#include "../step-5/cinema-v2/render_cinema.cpp"
#undef main
#pragma GCC diagnostic pop
#include "timeline.hpp"
#include "../step-7/finale_v3.hpp"
#include "globe.hpp"
#ifndef ATL_MAP_ONLY
#include "plates.hpp"
#endif

int main(int argc,char** argv){
    using namespace cinema;
    if(argc!=7){std::fprintf(stderr,"cinema FIELDS WIDTH HEIGHT FIRST END TRACE (or --samples FRAME_LIST for FIRST END)\n");return 2;}
    try{
        const int w=std::stoi(argv[2]),h=std::stoi(argv[3]);std::vector<int> frames;
        if(std::string(argv[4])=="--samples"){
            std::ifstream in(argv[5]);int f;
            while(in>>f)frames.push_back(f);
            if(!in.eof())throw std::runtime_error("invalid sample list");
        }else{
            const int first=std::stoi(argv[4]),end=std::stoi(argv[5]);
            if(first<0||first>=end||end>END_FRAME)throw std::runtime_error("invalid frame range");
            for(int f=first;f<end;f++)frames.push_back(f);
        }
        if(w<32||w%2||w>1920||h<18||h>1080||frames.empty()||frames.front()<0||frames.back()>=END_FRAME||
          std::adjacent_find(frames.begin(),frames.end(),std::greater_equal<int>())!=frames.end())throw std::runtime_error("invalid frame selection");
#ifdef ATL_MAP_ONLY
        CutSet s(argv[1],w,h);
#else
        Cinema s(argv[1],w,h);
#endif
        GlobeStudio globe;std::ofstream trace(argv[6]);trace.precision(9);if(!trace)throw std::runtime_error("invalid trace path");
        int k=0;
        for(int f:frames){
            while(f>=TAKES[k].b)++k;
            s.t=f/24.f;s.f=f;s.shot=k;s.marks={};
            const float u=clamp((f-TAKES[k].a)/float(TAKES[k].b-TAKES[k].a-1));
            s.q=u*.19f+.81f*smoother(u);
            if(mapshot(k,f))globe.draw(s);
            else{
#ifdef ATL_MAP_ONLY
                throw std::runtime_error("non-map frame requested in globe-only pass");
#else
                s.draw(k);
#endif
            }
            trace<<f<<','<<k;for(auto m:s.marks)trace<<','<<m.x<<','<<m.y<<','<<m.z;
            trace<<'\n';trace.flush();
            const auto& rgb=s.g.rgb;
            if(std::fwrite(rgb.data(),1,rgb.size(),stdout)!=rgb.size())throw std::runtime_error("short frame write");
        }
    }catch(const std::exception& e){std::fprintf(stderr,"cinema: %s\n",e.what());return 2;}
    return 0;
}
