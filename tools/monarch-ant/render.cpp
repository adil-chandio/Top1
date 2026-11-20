#include "scene.hpp"
#include "shaders.hpp"
#include <filesystem>
#include <sstream>
#include <chrono>
#include <iostream>
#include <limits>
#include <set>
namespace fs=std::filesystem;
using namespace ant;
struct Shot { int first,last,mode,cam; float from,to; std::string overlay; float dark=0; };
struct Job{
 int w=960,h=540,fps=24,start=0,end=-1,shadows=1,draft=0;std::string dir,plan,trace,ppmdir;std::set<int> stills;
};
struct Pipeline{
 Device device;Set world;Program geo{geoVS,geoFS},shadow{shadowVS,shadowFS},sky{fullVS,skyFS},post{fullVS,postFS};
 unsigned sand,matte,plate,depth,lightDepth,over,sceneF,lightF,fsvao;int w,h,shadowSize=640;
 M lp;V sun=norm({-.58f,.75f,-.38f});std::string prev;
 std::vector<unsigned char> pixels;
 Pipeline(int w,int h,const std::string&root):device(w,h),w(w),h(h),pixels(w*h*4){
   sand=load(root+"/assets/sand.rgba",768,768,true,true);matte=load(root+"/assets/matte.rgba",768,432,false,false);
   plate=texture(w,h,RGBA8,RGBA,UB,nullptr);
   depth=texture(w,h,DEPTH24,DEPTH,UINT,nullptr,false,false,true);
   lightDepth=texture(shadowSize,shadowSize,DEPTH24,DEPTH,UINT,nullptr,false,false,true);
   unsigned char zero[4]={}; over=texture(1,1,RGBA8,RGBA,UB,zero);
   glGenFramebuffers(1,&sceneF);glBindFramebuffer(FB,sceneF);glFramebufferTexture2D(FB,ATTACH,TEX2D,plate,0);glFramebufferTexture2D(FB,DEPTH_ATT,TEX2D,depth,0); check();
   glGenFramebuffers(1,&lightF);glBindFramebuffer(FB,lightF);glFramebufferTexture2D(FB,DEPTH_ATT,TEX2D,lightDepth,0);
   const unsigned n=0;glDrawBuffers(1,&n);glReadBuffer(0);check();glBindFramebuffer(FB,0);
   glGenVertexArrays(1,&fsvao);lp=mul(ortho(7.4f,.1f,40.f),look(sun*15,V{0,-.4f,0}));
 }
 void check(){auto code=glCheckFramebufferStatus(FB);if(code!=0x8cd5)throw std::runtime_error("incomplete framebuffer: "+std::to_string(code));}
 unsigned load(const std::string&f,int w,int h,bool mip,bool loop){auto b=bytes(f,w*h*4);return texture(w,h,RGBA8,RGBA,UB,b.data(),mip,loop);}
 void overlay(std::string key,const Job&j){
   if(key==prev)return;
   prev=key;glDeleteTextures(1,&over);
   if(key=="-"||key.empty()){unsigned char z[4]={};over=texture(1,1,RGBA8,RGBA,UB,z);}
   else over=load(j.dir+"/work/overlays/"+key+".rgba",w,h,false,false);
 }
 void frame(const Shot&s,int f,const Job&j,std::ofstream*trace){
   float q=float(f-s.first)/std::max(1,s.last-s.first-1),t=mix(s.from,s.to,q);
   Motion a=(s.mode>=5&&s.mode<=7)?study(t,s.mode!=5):s.mode==9?action(land+.13f+std::min(t,1.6f)):s.mode==1?planted(std::min(t,3.21f)):s.mode==11?climb(t):action(t,s.mode==4);
   auto c=camera(s.cam,t,q,a);c.dark=std::max(c.dark,s.dark);
   auto view=look(c.eye,c.target,c.up);auto vp=mul(persp(c.fov,float(w)/h,.035f,42.f),view);
   overlay(s.overlay,j);world.set(s.mode,t,vp,c.focus>7.f?1.f:0.f);
   if(trace && trace->good()){
     *trace<<f<<","<<t<<","<<s.mode<<","<<s.cam<<","<<a.p.x<<","<<a.p.y<<","<<a.p.z<<","<<a.support<<","<<a.clear<<","<<a.jaw<<","<<a.head<<","<<a.fly;
     for(V p:a.tips)*trace<<","<<p.x<<","<<p.y<<","<<p.z;
     for(V p:a.toes)*trace<<","<<p.y-ground(p.x,p.z);
     *trace<<"\n";
   }
   glEnable(DEPTH_TEST);glDepthMask(1);glDepthFunc(0x0203);
   glBindFramebuffer(FB,lightF);glViewport(0,0,shadowSize,shadowSize);glClear(CLEAR_DEPTH);
   if(j.shadows){shadow.use();shadow.m("uVP",lp);for(auto m:world.list)if(m->shadow)m->draw(true);}
   glBindFramebuffer(FB,sceneF);glViewport(0,0,w,h);glClear(CLEAR_DEPTH);
   glDisable(DEPTH_TEST);glDepthMask(0);glBindVertexArray(fsvao);sky.use();unit(0,matte);sky.i("uMatte",0);sky.v4("uSky",{.028f*sinf(t*.28f+c.eye.x*.4f),std::min(.051f,.013f*(c.eye.y-c.target.y)),c.diagram},0.f);glDrawArrays(4,0,3);
   glEnable(DEPTH_TEST);glDepthMask(1);geo.use();geo.m("uVP",vp);geo.m("uView",view);geo.m("uLight",lp);geo.v("uEye",c.eye);geo.v("uSun",sun);geo.v("uAnt",world.antPosition);geo.v("uLarva",world.larvaPosition);geo.v4("uLook",{c.key,c.sky,c.diagram},c.exposure);unit(0,sand);unit(1,lightDepth);geo.i("uSand",0);geo.i("uShadow",1);
   for(auto m:world.list)m->draw(!m->shadow||!j.shadows);
   glBindFramebuffer(FB,0);glDisable(DEPTH_TEST);glDepthMask(0);glBindVertexArray(fsvao);post.use();unit(0,plate);unit(1,over);post.i("uPicture",0);post.i("uOverlay",1);
   post.v2("uPix",1.f/w,1.f/h);post.v4("uLens",{c.focus,c.blur,c.dark},1.f);post.f("uFade",s.overlay=="-"?0.f:s.overlay=="title"||s.overlay=="end"||s.overlay=="sources"?ramp(0,.24f,q):1.f);glDrawArrays(4,0,3);
   glReadPixels(0,0,w,h,RGBA,UB,pixels.data());
   unsigned er=glGetError();if(er)throw std::runtime_error("OpenGL ES error: "+std::to_string(er));
 }
 void ppm(const std::string&file){std::ofstream out(file,std::ios::binary);out<<"P6\n"<<w<<" "<<h<<"\n255\n";
  std::vector<unsigned char> row(w*3);for(int y=h-1;y>=0;y--){const unsigned char* p=pixels.data()+y*w*4;for(int i=0;i<w;i++)memcpy(row.data()+3*i,p+4*i,3);out.write((const char*)row.data(),row.size());}
 }
};
static int parse(const char*b,int lo,int hi){int v=std::stoi(b);if(v<lo||v>hi)throw std::runtime_error("argument out of range");return v;}
int main(int argc,char**argv){try {
 Job j;j.dir=".cache/monarch-cam-ant-film";
 for(int n=1;n<argc;n++){
  std::string k=argv[n];if(++n>=argc)throw std::runtime_error("missing option value");
  if(k=="--width")j.w=parse(argv[n],128,1920);else if(k=="--height")j.h=parse(argv[n],72,1080);
  else if(k=="--dir")j.dir=argv[n];else if(k=="--plan")j.plan=argv[n];else if(k=="--trace")j.trace=argv[n];
  else if(k=="--first")j.start=parse(argv[n],0,100000);else if(k=="--end")j.end=parse(argv[n],0,100000);
  else if(k=="--draft")j.draft=parse(argv[n],0,1);
  else if(k=="--ppm")j.ppmdir=argv[n];else if(k=="--shadows")j.shadows=parse(argv[n],0,1);
  else if(k=="--still"){std::istringstream ss(argv[n]);std::string tok;while(std::getline(ss,tok,','))j.stills.insert(parse(tok.c_str(),0,100000));}
  else throw std::runtime_error("unknown option "+k);
 }
 if(!j.stills.empty() && j.ppmdir.empty())throw std::runtime_error("--still requires --ppm");
 std::vector<Shot> shots;
 if(j.plan.empty())shots={{0,178,0,0,0.f,7.375f,"-"}};
 else{
  std::ifstream a(j.plan);Shot s;while(a>>s.first>>s.last>>s.mode>>s.cam>>s.from>>s.to>>s.overlay>>s.dark){
   if(s.first!=(shots.empty()?0:shots.back().last)||s.last<=s.first)throw std::runtime_error("non-contiguous shot plan");
   shots.push_back(s);
  }
 }
 if(shots.empty())throw std::runtime_error("missing shot plan");
 if(j.end<0)j.end=shots.back().last;
 if(j.start>=j.end||j.end>shots.back().last)throw std::runtime_error("frame range is outside complete plan");
 std::ofstream trace;
 if(!j.trace.empty()){trace.open(j.trace);trace<<"frame,motion_s,scene,camera,body_x,body_y,body_z,support,jaw_tip_gap,jaw_open,head_pitch,airborne,jaw_lx,jaw_ly,jaw_lz,jaw_rx,jaw_ry,jaw_rz,toe_0_gap,toe_1_gap,toe_2_gap,toe_3_gap,toe_4_gap,toe_5_gap\n";}
 if(!j.ppmdir.empty())fs::create_directories(j.ppmdir);
 Pipeline r(j.w,j.h,j.dir);
 auto start=std::chrono::steady_clock::now();int done=0;
 int rendered=0;
 std::vector<unsigned char> pre, blend(r.pixels.size());
 auto output=[&](int frame,const std::vector<unsigned char>& rgba){
  if(fwrite(rgba.data(),1,rgba.size(),stdout)!=rgba.size())throw std::runtime_error("raw frame write failed");
  done++;
  if(done%288==0){float d=std::chrono::duration<float>(std::chrono::steady_clock::now()-start).count();fprintf(stderr,"frame %d / %d · %d native frames · %.1f timeline fps\n",frame+1,j.end,rendered,done/d);}
 };
 for(auto s:shots){
  int lo=std::max(j.start,s.first),hi=std::min(j.end,s.last);
  if(lo>=hi)continue;
  float speed=fabsf(s.to-s.from)*24/(s.last-s.first);
  bool closeAction=(s.cam==0||s.cam==12)&&s.from<3.93f&&s.to>3.17f;
  bool wideAction=(s.cam==1||s.cam==14)&&s.from<5.54f&&s.to>3.17f;
  bool hero=(s.mode==0&&(closeAction||wideAction))||s.mode==4;
  bool quiet=(s.mode>=5&&s.mode<=7)||s.mode==2||s.mode==8||s.mode==12;
  int step=1;
  if(j.draft&&j.stills.empty()&&j.ppmdir.empty()&&!hero)step=speed>.88f?2:quiet?5:4;
  if(step==1){
   for(int f=lo;f<hi;f++){
    if(!j.stills.empty()&&!j.stills.count(f))continue;
    r.frame(s,f,j,j.trace.empty()?nullptr:&trace);rendered++;
    if(j.ppmdir.empty())output(f,r.pixels);
    else{auto k=std::to_string(f);r.ppm(j.ppmdir+"/frame-"+std::string(6-std::min<int>(6,k.size()),'0')+k+".ppm");done++;}
   }
  }else{
   r.frame(s,lo,j,j.trace.empty()?nullptr:&trace);rendered++;pre=r.pixels;output(lo,pre);
   for(int old=lo;old+1<hi;){
    int f=std::min(hi-1,old+step),n=f-old;
    r.frame(s,f,j,j.trace.empty()?nullptr:&trace);rendered++;
    for(int k=1;k<n;k++){
     for(size_t i=0;i<blend.size();i++)blend[i]=(pre[i]*(n-k)+r.pixels[i]*k+n/2)/n;
     output(old+k,blend);
    }
    output(f,r.pixels);pre.swap(r.pixels);old=f;
   }
  }
 }
 float delta=std::chrono::duration<float>(std::chrono::steady_clock::now()-start).count();fprintf(stderr,"Rendered %d native -> %d timeline frames in %.2f s (%.2f timeline fps)\n",rendered,done,delta,done/delta);return done?0:1;
 }catch(const std::exception&e){fprintf(stderr,"ant film: %s\n",e.what());return 1;}}
