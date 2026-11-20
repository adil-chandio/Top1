#include "world.hpp"
#include "look.hpp"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <set>
#include <sstream>
extern "C" {
void glBlitFramebuffer(int,int,int,int,int,int,int,int,unsigned,unsigned);
void glBlendFunc(unsigned,unsigned);
void glScissor(int,int,int,int);
}
using namespace cinema;
struct Shot{int lo,hi,mode,cam;float from,to;std::string tag;std::vector<std::pair<int,float>> pins;};
struct Job{int w=1280,h=720,start=0,end=-1;std::string cache=".cache/monarch-ant-v2",plan,stillDir,trace;std::set<int> still;};
constexpr unsigned RFB=0x8ca8,DFB=0x8ca9,BLEND=0xbe2;
struct Render{
 Device device;World world;Program form{meshV,meshF},fill{fillV,fillF},shade{shadeV,shadeF};
 int w,h,plateKey=-1;
 unsigned soil,forest,shell,staticF,staticC,staticD,blankVA,shadowVA,shadowBuf,liveFb,liveC,liveD;
 std::vector<unsigned char> image;
 std::vector<V> patch;
 Render(const Job&j):device(j.w,j.h),w(j.w),h(j.h),image(w*h*4){
   auto load=[&](const char*n,int sw,int sh,bool mip,bool repeat){auto b=bytes(j.cache+"/assets/"+n+".rgba",sw*sh*4);return texture(sw,sh,RGBA8,RGBA,UB,b.data(),mip,repeat);};
   soil=load("fine-quartz",1024,1024,true,true);forest=load("fern-light",1024,576,false,false);shell=load("chitin-micro",768,768,true,true);
   auto target=[&](unsigned& fb,unsigned& c,unsigned& d){
     c=texture(w,h,RGBA8,RGBA,UB,nullptr,false,false,true);d=texture(w,h,DEPTH24,DEPTH,UINT,nullptr,false,false,true);
     glGenFramebuffers(1,&fb);glBindFramebuffer(FB,fb);glFramebufferTexture2D(FB,ATTACH,TEX2D,c,0);glFramebufferTexture2D(FB,DEPTH_ATT,TEX2D,d,0);
     if(glCheckFramebufferStatus(FB)!=0x8cd5)throw std::runtime_error("cinema framebuffer was incomplete");
   };
   target(staticF,staticC,staticD);target(liveFb,liveC,liveD);
   glGenVertexArrays(1,&blankVA);glGenVertexArrays(1,&shadowVA);
   glBindVertexArray(shadowVA);glGenBuffers(1,&shadowBuf);glBindBuffer(ARRAY,shadowBuf);
   glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,FLOAT,0,sizeof(V),nullptr);
   patch.reserve(10000);
   glBindFramebuffer(FB,0);glViewport(0,0,w,h);glDepthFunc(0x0203);glBlendFunc(0x0302,0x0303);
 }
 void uniforms(const Lens&k,const M&vp,const M&view){
  form.use();form.m("uVP",vp);form.m("uView",view);form.v("uEye",k.eye);form.v4("optics",{k.focus,k.stop,k.grade},k.stage?1:0);
  unit(0,soil);unit(1,shell);form.i("sand",0);form.i("cuticle",1);
 }
 void base(unsigned fb,const Lens&k,const M&vp,const M&view,int mode){
  glBindFramebuffer(FB,fb);glDepthMask(1);glClear(CLEAR_DEPTH);glDisable(DEPTH_TEST);glDepthMask(0);
  fill.use();glBindVertexArray(blankVA);unit(0,forest);fill.i("forest",0);
  fill.v4("look",{.021f*sinf(k.eye.x),std::clamp((k.eye.y-k.aim.y)*.011f,-.055f,.064f),k.stage?1.f:0.f},k.grade);
  glDrawArrays(4,0,3);glEnable(DEPTH_TEST);glDepthMask(1);
  uniforms(k,vp,view);world.staticScene(mode,k,vp);
  for(auto m:world.list)m->draw(true);
 }
 void shadows(const Motion&a,const Lens&k,const M&vp){
  if(k.stage||world.shadowCasts.empty())return;
  V p=a.p;float h0=std::max(.04f,p.y-ground(p.x,p.z));
  // Blend on the same triangles as the cached floor, avoiding floating
  // contact-shadow fragments. Scissor bounds the soft shadow raster work.
  V o=point(a.h,{.26f,.06f,0}),b=point(a.torso,{-.93f,0.f,0.f});
  std::array<V,3> centers={p,o,b};float f=std::max(.05f,h0-.32f);
  float xMin=1.f,yMin=1.f,xMax=-1.f,yMax=-1.f;
  float left=100.f,right=-100.f,back=100.f,front=-100.f;
  auto screen=[&](V z){const float *m=vp.a;float w0=m[3]*z.x+m[7]*z.y+m[11]*z.z+m[15];
    if(w0<=.1f){xMin=yMin=-1;xMax=yMax=1;return;}
    float x=(m[0]*z.x+m[4]*z.y+m[8]*z.z+m[12])/w0,y=(m[1]*z.x+m[5]*z.y+m[9]*z.z+m[13])/w0;
    xMin=std::min(xMin,x);xMax=std::max(xMax,x);yMin=std::min(yMin,y);yMax=std::max(yMax,y);
  };
  shade.use();shade.m("uVP",vp);
  for(int i=0;i<3;i++){
    V x=centers[i];float y=std::max(0.f,x.y-ground(x.x,x.z)), rad=.57f+f*.23f;
    x.x+=y*.52f;x.z+=y*.46f;
    char name[20];snprintf(name,sizeof name,"uShade[%d]",i);
    shade.v4(name,{x.x,x.z,rad},.45f*expf(-f*.68f));
    left=std::min(left,x.x-1.35f*rad);right=std::max(right,x.x+1.35f*rad);
    back=std::min(back,x.z-1.35f*rad);front=std::max(front,x.z+1.35f*rad);
    for(float u:{-1.f,1.f})for(float v:{-1.f,1.f}){float x0=x.x+u*rad*1.48f,z0=x.z+v*rad*1.48f;screen({x0,ground(x0,z0),z0});}
  }
  const int sx=std::clamp(int((xMin*.5f+.5f)*w)-4,0,w),sy=std::clamp(int((yMin*.5f+.5f)*h)-4,0,h);
  const int sw=std::clamp(int((xMax*.5f+.5f)*w)+4,0,w)-sx,sh=std::clamp(int((yMax*.5f+.5f)*h)+4,0,h)-sy;
  if(sw<=0||sh<=0)return;
  const auto&mesh=world.soil;patch.clear();
  for(size_t i=0;i<mesh.idx.size();i+=3){
    const V &a0=mesh.v[mesh.idx[i]].p,&b0=mesh.v[mesh.idx[i+1]].p,&c0=mesh.v[mesh.idx[i+2]].p;
    if(a0.x<left-.34f||a0.x>right+.34f||a0.z<back-.34f||a0.z>front+.34f)continue;
    patch.push_back(a0);patch.push_back(b0);patch.push_back(c0);
  }
  if(patch.empty())return;
  glEnable(0xc11);glScissor(sx,sy,sw,sh);glEnable(BLEND);glDepthMask(0);
  glBindVertexArray(shadowVA);glBindBuffer(ARRAY,shadowBuf);glBufferData(ARRAY,patch.size()*sizeof(V),patch.data(),STREAM);
  glDrawArrays(4,0,patch.size());
  glDepthMask(1);glDisable(BLEND);glDisable(0xc11);
 }
 void frame(int n,const Shot&s,int id,const Job&j,std::ofstream&tr){
  const float q=float(n-s.lo)/std::max(1,s.hi-s.lo-1);
  int a0=s.lo,b0=s.hi-1;float u=s.from,v=s.to;
  for(auto [f,z]:s.pins){if(n<f){b0=f;v=z;break;}a0=f;u=z;}
  // An exact contact frame enters the native sample grid, not a repeated stock frame.
  const float t=mix(u,v,float(n-a0)/std::max(1,b0-a0));Motion a=pose(s.mode,t);
  // A fixed lens cannot silently depend on a noise sample or the animated performer.
  Lens k=lens(s.cam,t,q,a,s.mode);if(k.fixed)k=lens(s.cam,s.from,0,pose(s.mode,s.from),s.mode);
  auto view=look(k.eye,k.aim,k.up),vp=mul(persp(k.lens,float(w)/h,.035f,42.f),view);
  if(k.fixed){
   if(plateKey!=id){base(staticF,k,vp,view,s.mode);plateKey=id;}
   glBindFramebuffer(RFB,staticF);glBindFramebuffer(DFB,liveFb);glBlitFramebuffer(0,0,w,h,0,0,w,h,CLEAR_COLOR|CLEAR_DEPTH,NEAREST);
   glBindFramebuffer(FB,liveFb);
  }else base(liveFb,k,vp,view,s.mode);
  world.detail=std::min(1.f,4.15f/k.focus);world.actors(s.mode,t,a,vp);shadows(a,k,vp);
  uniforms(k,vp,view);
  for(auto m:world.list)m->draw(true);
  glReadPixels(0,0,w,h,RGBA,UB,image.data());
  if(tr.is_open())tr<<n<<','<<t<<','<<s.cam<<','<<s.mode<<','<<s.tag<<','<<a.p.x<<','<<a.p.y<<','<<a.p.z<<','<<a.clear<<','<<a.support<<','<<a.fly<<'\n';
  (void)j;
 }
 void ppm(const std::string&path){
  std::ofstream out(path,std::ios::binary);out<<"P6\n"<<w<<' '<<h<<"\n255\n";
  std::vector<unsigned char> line(w*3);for(int i=h-1;i>=0;i--){const auto *row=&image[i*w*4];for(int x=0;x<w;x++)std::memcpy(line.data()+x*3,row+x*4,3);out.write(reinterpret_cast<char*>(line.data()),line.size());}
 }
};
int main(int argc,char**argv){try {
 Job j;
 for(int i=1;i<argc;i++){
   const std::string a=argv[i];if(++i==argc)throw std::runtime_error("missing argument value");const std::string v=argv[i];
   if(a=="--cache")j.cache=v;else if(a=="--plan")j.plan=v;else if(a=="--width")j.w=std::stoi(v);else if(a=="--height")j.h=std::stoi(v);
   else if(a=="--first")j.start=std::stoi(v);else if(a=="--end")j.end=std::stoi(v);else if(a=="--stills"){std::istringstream r(v);std::string x;while(std::getline(r,x,','))j.still.insert(std::stoi(x));}
   else if(a=="--ppm")j.stillDir=v;else if(a=="--trace")j.trace=v;else throw std::runtime_error("unknown argument "+a);
 }
 if(j.w<128||j.h<72||j.w>1920||j.h>1080||j.w%2||j.h%2)throw std::runtime_error("invalid delivery raster");
 if(!j.still.empty()&&j.stillDir.empty())throw std::runtime_error("need --ppm when using --stills");
 std::ifstream plan(j.plan);std::vector<Shot> shots;Shot s;
 std::string line;
 while(std::getline(plan,line)){
   if(line.empty())continue;
   std::istringstream row(line);s.pins.clear();
   if(!(row>>s.lo>>s.hi>>s.mode>>s.cam>>s.from>>s.to>>s.tag)||
      s.lo!=(shots.empty()?0:shots.back().hi)||s.hi<=s.lo||s.mode<0||s.mode>16||s.cam<0||s.cam>40||!(s.from<s.to))throw std::runtime_error("inconsistent shot plan");
   int f,prior=s.lo;float z,prev=s.from;
   while(row>>f){
     if(!(row>>z)||f<=prior||f>=s.hi-1||!(z>prev&&z<s.to))throw std::runtime_error("inconsistent motion pin");
     s.pins.push_back({f,z});prior=f;prev=z;
   }
   shots.push_back(s);
 }
 if(shots.empty())throw std::runtime_error("missing plan");
 if(j.end<0)j.end=shots.back().hi;
 if(j.start<0||j.end>shots.back().hi||j.start>=j.end)throw std::runtime_error("range outside plan");
 std::ofstream tr;if(!j.trace.empty()){tr.open(j.trace);tr<<"frame,motion_s,camera,set,subject,body_x,body_y,body_z,jaw_tip_gap,support,airborne\n";}
 if(!j.stillDir.empty())std::filesystem::create_directories(j.stillDir);
 Render r(j);int rendered=0;auto bt=std::chrono::steady_clock::now();
 for(size_t id=0;id<shots.size();id++){auto &s0=shots[id];auto start=std::chrono::steady_clock::now();int prior=rendered;for(int f=std::max(s0.lo,j.start);f<std::min(s0.hi,j.end);f++){
  if(!j.still.empty()&&!j.still.count(f))continue;
  r.frame(f,s0,id,j,tr);rendered++;
  if(!j.stillDir.empty()){std::string n=std::to_string(f);n=std::string(6-std::min<int>(6,n.size()),'0')+n;r.ppm(j.stillDir+"/frame-"+n+".ppm");}
  else if(fwrite(r.image.data(),1,r.image.size(),stdout)!=r.image.size())throw std::runtime_error("frame pipe closed early");
  if(rendered%300==0)fprintf(stderr,"Native %d / %d frames · %.1f fps · %s\n",f+1,j.end,rendered/std::chrono::duration<double>(std::chrono::steady_clock::now()-bt).count(),s0.tag.c_str());
 }
  if(rendered>prior)fprintf(stderr,"Take %02zu · %s · %d native frames · %.2f s\n",id+1,s0.tag.c_str(),rendered-prior,std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());
 }
 if(glGetError())throw std::runtime_error("GLES operation failed");
 const double dur=std::chrono::duration<double>(std::chrono::steady_clock::now()-bt).count();
 fprintf(stderr,"Rendered %d distinct native evaluations in %.3f s (%.2f fps)\n",rendered,dur,rendered/dur);return rendered?0:1;
 }catch(const std::exception&e){fprintf(stderr,"cinema renderer: %s\n",e.what());return 1;}}
