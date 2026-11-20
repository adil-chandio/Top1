#include "feature.hpp"
#include "light.hpp"
#include "short/view.hpp"
#include "../monarch-ant-v2/look.hpp"
#include <chrono>
#include <filesystem>
#include <set>
#include <sstream>
#include <utility>
extern "C" {void glBlitFramebuffer(int,int,int,int,int,int,int,int,unsigned,unsigned);void glColorMask(unsigned char,unsigned char,unsigned char,unsigned char);void glBlendFunc(unsigned,unsigned);void glScissor(int,int,int,int);}
using namespace opening;
struct Shot{int lo,hi,mode,cam;float from,to;std::string tag;std::vector<std::pair<int,float>> keys;};
struct Options{int w=1280,h=720,first=0,end=-1;std::string cache=".cache/monarch-ant-v3",plan="tools/monarch-ant-v3/opening.plan",trace,stillsDir,guides,marks;bool feature=false,portrait=false;std::set<int> stills;};
constexpr unsigned RFBO=0x8ca8,DFBO=0x8ca9,DEPTH_OFFSET=0x8037;
// For longer editorial segments use two optical samples per axis and stable
// dither. Static color/depth is still cached; actors/shadows are fresh per frame.
const char* featureFinish(){
 static const std::string s=[](){
  std::string p=finishFragment;
  auto lo=p.find("   if(defocus>.73)"), hi=p.find("   if(state.x",lo);
  p.replace(lo,hi-lo,R"(   if(defocus>1.10){
     vec2 k=vec2(defocus)/lens.xy;
     vec4 g=grab(uv+k*vec2(.78,.44))+grab(uv+k*vec2(-.70,-.58));
     c=mix(c,g*.5,.61*smoothstep(1.,4.7,defocus));
   }
)");
  auto grain=p.find("float dust=");auto end=p.find(';',grain);
  p.replace(grain,end-grain,"float dust=0.");
  return p;
 }();return s.c_str();
}

const char* featureSurface(){
 static const std::string s=[](){
  std::string p=surfaceFragment;
  p.replace(p.find("uniform vec3 sun;"),17,"uniform vec3 sun; uniform vec2 raster;");
  auto pos=p.find("outColor=vec4(film(p),");
  p.replace(pos,std::string("outColor=vec4(film(p),").size(),"vec2 v2=(gl_FragCoord.xy/raster-vec2(.51,.53))*vec2(1.22,1.);\n outColor=vec4(film(p)*(1.-.23*smoothstep(.26,.80,length(v2))),");
  return p;
 }();return s.c_str();
}
struct Target{unsigned fb,c,d;};

// Monotone cubic remapping around physical beats. A pin has a continuous
// derivative on either side, rather than a hard cut in simulation speed.
float clock(const Shot&s,int f){
 size_t i=0;const auto &k=s.keys;
 while(i+2<k.size() && f>k[i+1].first)i++;
 auto delta=[&](size_t j){return (k[j+1].second-k[j].second)/(k[j+1].first-k[j].first);};
 auto tangent=[&](size_t j){if(j==0)return delta(0);if(j+1==k.size())return delta(j-1);
  float a=delta(j-1),b=delta(j);float l=k[j].first-k[j-1].first,r=k[j+1].first-k[j].first;
  return 3*(l+r)/((l+2*r)/a+(2*l+r)/b);};
 float d=k[i+1].first-k[i].first,u=(f-k[i].first)/d,w=u*u,ww=w*u;
 if(f==k[i].first)return k[i].second;
 if(f==k[i+1].first)return k[i+1].second;
 return (2*ww-3*w+1)*k[i].second+(ww-2*w+u)*d*tangent(i)+(-2*ww+3*w)*k[i+1].second+(ww-w)*d*tangent(i+1);
}

class Render{
 Device device;
 Stage stage;
 Program surface,rich{cinema::meshV,surfaceFragment},bg{cinema::fillV,plateFragment},shadow{shadowVertex,shadowFragment},finish,soft{cinema::shadeV,cinema::shadeF};
 int w,h,lightSize,plate=-1;bool longForm,vertical;
 Target live,still;
 unsigned qu,ct,back,fullscreen,shadowFB,shadowTex,outFB,outCol,patchVA,patchBuf;std::vector<V> patch;
 const V sun=norm(warmKey);
 void check(){if(glCheckFramebufferStatus(FB)!=0x8cd5)throw std::runtime_error("V3 framebuffer was incomplete");}
 Target target(){
  Target t{};t.c=texture(w,h,RGBA8,RGBA,UB,nullptr,false,false,false);t.d=texture(w,h,DEPTH24,DEPTH,UINT,nullptr,false,false,true);
  glGenFramebuffers(1,&t.fb);glBindFramebuffer(FB,t.fb);
  glFramebufferTexture2D(FB,ATTACH,TEX2D,t.c,0);glFramebufferTexture2D(FB,DEPTH_ATT,TEX2D,t.d,0);check();return t;
 }
 void material(const Optic&k,const M&view,const M&vp,float alpha,bool wide){
  auto &surface=wide?this->surface:rich;surface.use();surface.v2("raster",float(w),float(h));surface.m("uVP",vp);surface.m("uView",view);surface.v("eye",k.eye);surface.v("sun",sun);
  surface.v4("shot",{focusDistance(k),k.key,k.studio},alpha);
  unit(0,qu);unit(1,ct);surface.i("quartz",0);surface.i("chitin",1);
 }
 void world(unsigned fb,const Optic&k,const M&view,const M&vp,int take,int mode,bool wide){
  glBindFramebuffer(FB,fb);glViewport(0,0,w,h);glDepthMask(1);glClear(CLEAR_DEPTH);
  glDisable(DEPTH_TEST);glDepthMask(0);
  bg.use();unit(0,back);bg.i("canopy",0);glBindVertexArray(fullscreen);
  bg.v4("shape",{.04f*sinf(k.eye.x*.31f),std::clamp((k.eye.y-k.aim.y)*.014f,-.06f,.06f),k.studio},0);
  glDrawArrays(4,0,3);glEnable(DEPTH_TEST);glDepthMask(1);
  stage.dressed(k,vp,take,wide);if(longForm&&mode>=14&&mode<=15)stage.pads(mode);material(k,view,vp,0.f,wide);for(auto*m:stage.list)m->draw(true);
 }
 void softContact(const Motion&a,const M&vp,int mode){
  if(stage.shadowCasts.empty()&&mode!=3&&mode!=8)return;
  V p=mode==3||mode==8?stage.larvaPosition:a.p;
  V centers[3]={p,mode==3||mode==8?p+V{.15f,0,.03f}:point(a.h,{.24f,.024f,0}),
                     mode==3||mode==8?p+V{-.17f,0,0}:point(a.torso,{-.98f,0,0})};
  std::array<float,4> xy={100,100,-100,-100};const auto*m=vp.a;
  auto bounds=[&](V t){float w0=m[3]*t.x+m[7]*t.y+m[11]*t.z+m[15];
   if(w0<.07f){xy={-1,-1,1,1};return;}
   float x=(m[0]*t.x+m[4]*t.y+m[8]*t.z+m[12])/w0,y=(m[1]*t.x+m[5]*t.y+m[9]*t.z+m[13])/w0;
   xy[0]=std::min(xy[0],x);xy[1]=std::min(xy[1],y);xy[2]=std::max(xy[2],x);xy[3]=std::max(xy[3],y);};
  soft.use();soft.m("uVP",vp);float xl=100,xr=-100,zl=100,zr=-100;
  for(int i=0;i<3;i++){
   V c=centers[i];float alt=std::max(0.f,c.y-ground(c.x,c.z)),lift=std::max(0.f,alt-.31f);
   c.x+=alt*.59f;c.z+=alt*.56f;float rad=.50f+lift*.28f;
   char name[20];snprintf(name,sizeof name,"uShade[%d]",i);soft.v4(name,{c.x,c.z,rad},.51f*expf(-lift*.41f));
   rad*=1.42f;xl=std::min(xl,c.x-rad);xr=std::max(xr,c.x+rad);zl=std::min(zl,c.z-rad);zr=std::max(zr,c.z+rad);
   for(float u:{-1.f,1.f})for(float v:{-1.f,1.f}){float x=c.x+u*rad,z=c.z+v*rad;bounds({x,ground(x,z),z});}
  }
  int x=std::clamp(int((xy[0]*.5f+.5f)*w)-4,0,w),y=std::clamp(int((xy[1]*.5f+.5f)*h)-4,0,h);
  int sw=std::clamp(int((xy[2]*.5f+.5f)*w)+4,0,w)-x,sh=std::clamp(int((xy[3]*.5f+.5f)*h)+4,0,h)-y;
  if(sw<=0||sh<=0)return;
  const auto &g=stage.soil;patch.clear();
  for(size_t i=0;i<g.idx.size();i+=3){V t=g.v[g.idx[i]].p;
   if(t.x<xl-.32f||t.x>xr+.32f||t.z<zl-.32f||t.z>zr+.32f)continue;
   patch.insert(patch.end(),{t,g.v[g.idx[i+1]].p,g.v[g.idx[i+2]].p});}
  if(patch.empty())return;
  glEnable(0xc11);glScissor(x,y,sw,sh);glEnable(0xbe2);glColorMask(1,1,1,0);glDepthMask(0);
  glBindVertexArray(patchVA);glBindBuffer(ARRAY,patchBuf);glBufferData(ARRAY,patch.size()*sizeof(V),patch.data(),STREAM);
  glDrawArrays(4,0,patch.size());glDepthMask(1);glColorMask(1,1,1,1);glDisable(0xbe2);glDisable(0xc11);
 }
 M cast(V at){
  M v=mul(ortho(4.65f,.3f,18.f),look(at+sun*7.5f,at,{0,1,0}));
  glBindFramebuffer(FB,shadowFB);glViewport(0,0,lightSize,lightSize);glDepthMask(1);glClear(CLEAR_DEPTH);
  glEnable(DEPTH_TEST);glEnable(DEPTH_OFFSET);glPolygonOffset(1.f,1.f);shadow.use();shadow.m("lightMatrix",v);
  for(auto*g:stage.list){if(g==&stage.soil||g==&stage.grain||g==&stage.thread||g==&stage.rock)continue;g->draw(true);}
  glDisable(DEPTH_OFFSET);return v;
 }
 void grade(const Optic&k,const M&shadowVP,bool shadows,int n,int camera){
  V f=norm(k.aim-k.eye),r=norm(cross(f,k.up)),u=cross(r,f);float a=tanf(k.fov*pi/360.f);
  glBindFramebuffer(FB,outFB);glViewport(0,0,w,h);glDisable(DEPTH_TEST);glDepthMask(0);
  finish.use();glBindVertexArray(fullscreen);unit(0,live.c);unit(1,live.d);unit(2,shadowTex);
  finish.i("base",0);finish.i("depth",1);finish.i("lightmap",2);finish.m("lightMatrix",shadowVP);
  finish.v("eye",k.eye);finish.v("rayF",f);finish.v("rayX",r*(a*w/h));finish.v("rayY",u*a);
  finish.v4("lens",{float(w),float(h),focusDistance(k)},k.aperture*h/720.f);
  finish.v4("state",{shadows?1.f:0.f,camera==7?.24f:.30f,k.studio?0.f:.83f},float(n)*.619f);
  glDrawArrays(4,0,3);glReadPixels(0,0,w,h,RGBA,UB,pixels.data());glDepthMask(1);
 }
public:
 std::vector<unsigned char> pixels;
 Render(const Options&o):device(o.w,o.h),surface(cinema::meshV,featureSurface()),finish(cinema::fillV,o.feature?featureFinish():finishFragment),w(o.w),h(o.h),lightSize(o.feature?384:512),longForm(o.feature),vertical(o.portrait),pixels(size_t(w)*h*4){
  auto load=[&](const char*n,int sw,int sh,bool mip,bool repeat){const auto b=bytes(o.cache+"/assets/"+n+".rgba",size_t(sw)*sh*4);return texture(sw,sh,RGBA8,RGBA,UB,b.data(),mip,repeat);};
  qu=load("quartz",1024,1024,true,true);ct=load("cuticle",768,768,true,true);back=load("canopy",1024,576,false,false);
  live=target();still=target();glGenVertexArrays(1,&fullscreen);
  shadowTex=texture(lightSize,lightSize,DEPTH24,DEPTH,UINT,nullptr,false,false,true);
  glGenFramebuffers(1,&shadowFB);glBindFramebuffer(FB,shadowFB);glFramebufferTexture2D(FB,DEPTH_ATT,TEX2D,shadowTex,0);
  const unsigned noColor=0;glDrawBuffers(1,&noColor);glReadBuffer(noColor);check();
  outCol=texture(w,h,RGBA8,RGBA,UB,nullptr,false,false,true);
  glGenFramebuffers(1,&outFB);glBindFramebuffer(FB,outFB);glFramebufferTexture2D(FB,ATTACH,TEX2D,outCol,0);check();
  glDepthFunc(0x0203);glBlendFunc(0x0302,0x0303);
  glGenVertexArrays(1,&patchVA);glGenBuffers(1,&patchBuf);glBindVertexArray(patchVA);glBindBuffer(ARRAY,patchBuf);
  glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,FLOAT,0,sizeof(V),nullptr);patch.reserve(10000);

 }
 void frame(const Shot&s,int i,int n,std::ofstream&csv){
  float q=float(n-s.lo)/(s.hi-s.lo-1),t=clock(s,n);
  Motion a=longForm?feature::pose(s.mode,s.cam,t):openingPose(s.mode,s.cam,t);
  Optic k=longForm?feature::lens(s.cam,s.mode,t,q,a):opening::camera(s.cam,t,q,a);
  if(vertical)k=portrait::view(s.tag,k,t,q,a);
  M view=look(k.eye,k.aim,k.up),vp=mul(persp(k.fov,float(w)/h,hNear,hFar),view);
  bool hero=vertical?portrait::close(s.tag):(s.cam==69||s.cam==70||s.cam==73||s.cam==74||s.cam==79||s.cam==81||s.cam==83||s.cam==52||s.cam==54);
  const bool wide=longForm&&!hero;
  if(k.fixed){
    if(plate!=i){world(still.fb,k,view,vp,s.cam,s.mode,wide);plate=i;}
    glBindFramebuffer(RFBO,still.fb);glBindFramebuffer(DFBO,live.fb);glBlitFramebuffer(0,0,w,h,0,0,w,h,CLEAR_COLOR|CLEAR_DEPTH,NEAREST);
  }else world(live.fb,k,view,vp,s.cam,s.mode,wide);
  stage.detail=std::min(1.f,3.82f/focusDistance(k));stage.actionSet(s.mode,s.cam,t,q,a,vp,longForm);
  bool lighting=!k.studio&&(longForm?(s.mode!=2&&s.mode!=10&&s.mode<14):s.mode<=16&&s.mode!=10);
  M lit{};
  if(lighting&&!wide)lit=cast(s.mode==3?stage.larvaPosition:a.p);
  glBindFramebuffer(FB,live.fb);glViewport(0,0,w,h);glEnable(DEPTH_TEST);glDepthMask(1);
  if(lighting&&wide)softContact(a,vp,s.mode);
  material(k,view,vp,1,wide);
  for(auto*m:stage.list)m->draw(true);
  bool occlusion=!longForm&&stage.crossPincer(k,n);
  if(occlusion)stage.hook.draw(true);
  if(wide)glReadPixels(0,0,w,h,RGBA,UB,pixels.data());
  else grade(k,lit,lighting,n,s.cam);
  if(csv.is_open()){
    V j=(a.tips[0]+a.tips[1])*.5f;
    auto projected=[&vp](V p){auto *m=vp.a;float z=m[3]*p.x+m[7]*p.y+m[11]*p.z+m[15];return V{(m[0]*p.x+m[4]*p.y+m[8]*p.z+m[12])/z,(m[1]*p.x+m[5]*p.y+m[9]*p.z+m[13])/z,z};};
    V s0=projected(a.p),s1=projected(j);
    csv<<n<<','<<s.tag<<','<<s.cam<<','<<t<<','<<a.p.x<<','<<a.p.y<<','<<a.p.z<<','<<a.clear<<','<<a.support<<','<<a.fly<<','<<s0.x<<','<<s0.y<<','<<s1.x<<','<<s1.y<<','<<occlusion<<'\n';
  }
 }
 void stillImage(const std::string&name){
   // PPM is only for rapid visual checks; raw pipeline also retains actor alpha.
   std::ofstream out(name,std::ios::binary);out<<"P6\n"<<w<<' '<<h<<"\n255\n";
   std::vector<unsigned char> line(w*3);
   for(int y=h-1;y>=0;y--){const auto*r=pixels.data()+y*w*4;for(int x=0;x<w;x++)std::memcpy(&line[x*3],r+x*4,3);out.write(reinterpret_cast<const char*>(line.data()),line.size());}
 }
};
std::vector<Shot> script(const std::string&f,bool longForm){
 std::ifstream p(f);std::string line;std::vector<Shot> shots;
 while(std::getline(p,line)){
  if(line.empty()||line[0]=='#')continue;
  std::istringstream row(line);Shot s{};
  if(!(row>>s.lo>>s.hi>>s.mode>>s.cam>>s.from>>s.to>>s.tag)||s.lo!=(shots.empty()?0:shots.back().hi)||
      s.hi-s.lo<2||s.cam<0||(s.cam>10&&(!longForm||(s.cam<50||s.cam>140||(s.cam>83&&s.cam<100))))||s.mode<0||s.mode>23||s.from>=s.to)throw std::runtime_error("invalid V3 storyboard row");
  s.keys={{s.lo,s.from}};int n;float v;
  while(row>>n){if(!(row>>v)||n<=s.keys.back().first||n>=s.hi-1||v<=s.keys.back().second||v>=s.to)throw std::runtime_error("invalid V3 time pin");s.keys.push_back({n,v});}
  s.keys.push_back({s.hi-1,s.to});shots.push_back(std::move(s));
 }
 if(shots.empty())throw std::runtime_error("no V3 shots found");
 return shots;
}
// Project the true 3D jaw sweep from the rig, independently of EGL.
void guides(const std::vector<Shot>&s,const Options&j){
 std::ofstream out(j.guides);if(!out)throw std::runtime_error("cannot write guide projection");
 out<<"frame,side,step,x,y,sweep\n";
 for(const auto& take:s){if(take.cam!=8)continue;
  for(int n=std::max(take.lo,j.first);n<std::min(take.hi,j.end);n++){
   float t=clock(take,n),q=float(n-take.lo)/(take.hi-take.lo-1);
   Motion a=openingPose(take.mode,take.cam,t);Optic k=opening::camera(take.cam,t,q,a);
   M vp=mul(persp(k.fov,float(j.w)/j.h,hNear,hFar),look(k.eye,k.aim,k.up));float *m=vp.a;
   for(int side:{-1,1}){
    V hinge=point(a.h,{.518f,-.062f,side*.153f});
    for(int i=0;i<=36;i++){
     V tip=jtip(a.h,side,mix(1.25f,.057f,i/36.f));
     V p=hinge+(tip-hinge)*1.065f;
     float z=m[3]*p.x+m[7]*p.y+m[11]*p.z+m[15];
     float x=(m[0]*p.x+m[4]*p.y+m[8]*p.z+m[12])/z,y=(m[1]*p.x+m[5]*p.y+m[9]*p.z+m[13])/z;
     out<<n<<','<<side<<','<<i<<','<<.5f+.5f*x<<','<<.5f-.5f*y<<','<<(1.25f-a.jaw)/1.193f<<'\n';
    }
   }
  }
 }
}
void marks(const std::vector<Shot>&s,const Options&j){
 std::ofstream out(j.marks);if(!out)throw std::runtime_error("cannot write feature projection");
 out<<"frame,body_x,body_y,tip_x,tip_y,hinge_x,hinge_y,shell_x,shell_y,attach_x,attach_y,toe_x,toe_y,pit_x,pit_y,jaw_angle\n";
 for(auto &z:s){for(int n=std::max(z.lo,j.first);n<std::min(z.hi,j.end);n++){
  float t=clock(z,n),q=float(n-z.lo)/(z.hi-z.lo-1);Motion a=feature::pose(z.mode,z.cam,t);Optic k=feature::lens(z.cam,z.mode,t,q,a);
  const M vp=mul(persp(k.fov,float(j.w)/j.h,hNear,hFar),look(k.eye,k.aim,k.up));const auto*m=vp.a;
  float load=ramp(.32f,2.935f,t)*(1-ramp(2.955f,3.218f,t)),rel=ramp(2.945f,3.233f,t);
  int side=k.eye.z>=0?1:-1;
  auto write=[&](V u){float w=m[3]*u.x+m[7]*u.y+m[11]*u.z+m[15];
   if(w<=.023f){out<<",-10,-10";return;}
   out<<','<<(1.f+(m[0]*u.x+m[4]*u.y+m[8]*u.z+m[12])/w)*.5f<<','<<(1.f-(m[1]*u.x+m[5]*u.y+m[9]*u.z+m[13])/w)*.5f;};
  out<<n;write(a.p);write((a.tips[0]+a.tips[1])*.5f);write(feature::hinge(a,side));
  write(point(a.h,{.40f+.07f*rel,-.016f,side*(.20f-.012f*rel+.017f*load)}));
  write(point(a.h,{.505f+.037f*rel,-.029f,side*(.119f+.036f*load)}));
  write(a.toes[1]);write({.215f,ground(.215f,.04f)+.145f,.04f});out<<','<<a.jaw<<'\n';
 }}
}
int main(int argc,char**argv){try{
 Options j;
 for(int i=1;i<argc;i++){
  std::string a=argv[i];if(++i==argc)throw std::runtime_error("expected argument value");std::string v=argv[i];
  if(a=="--width")j.w=std::stoi(v);else if(a=="--height")j.h=std::stoi(v);
  else if(a=="--feature")j.feature=v=="1";else if(a=="--marks")j.marks=v;else if(a=="--portrait")j.portrait=v=="1";
  else if(a=="--cache")j.cache=v;else if(a=="--plan")j.plan=v;else if(a=="--trace")j.trace=v;
  else if(a=="--first")j.first=std::stoi(v);else if(a=="--end")j.end=std::stoi(v);
  else if(a=="--ppm")j.stillsDir=v;else if(a=="--guides")j.guides=v;
  else if(a=="--stills"){std::istringstream q(v);std::string s;while(std::getline(q,s,','))j.stills.insert(std::stoi(s));}
  else throw std::runtime_error("unknown render option: "+a);
 }
 const int w=j.portrait?j.h:j.w,h=j.portrait?j.w:j.h;
 if(w<256||h<144||w>1920||h>1080||w*9!=h*16||w%2||h%2)throw std::runtime_error("invalid V3 raster for selected orientation");
 if(j.portrait&&(!j.feature||!j.guides.empty()||!j.marks.empty()))throw std::runtime_error("portrait uses feature rig and render traces only");
 auto s=script(j.plan,j.feature);if(j.end<0)j.end=s.back().hi;
 if(j.first<0||j.end<=j.first||j.end>s.back().hi)throw std::runtime_error("requested frames outside storyboard");
 if(!j.guides.empty()){guides(s,j);return 0;}
 if(!j.marks.empty()){marks(s,j);return 0;}
 if(!j.stills.empty()&&j.stillsDir.empty())throw std::runtime_error("stills require --ppm directory");
 if(!j.stillsDir.empty())std::filesystem::create_directories(j.stillsDir);
 std::ofstream trace;if(!j.trace.empty()){trace.open(j.trace);if(!trace)throw std::runtime_error("cannot write motion receipt");trace<<"frame,shot,lens,motion_s,x,y,z,jaw_gap,support,airborne,body_ndcx,body_ndcy,jaw_ndcx,jaw_ndcy,foreground_cut\n";}
 Render r(j);auto start=std::chrono::steady_clock::now();int count=0;
 for(size_t i=0;i<s.size();i++){
  int count0=count;const auto &shot=s[i];
  for(int n=std::max(shot.lo,j.first);n<std::min(shot.hi,j.end);n++){
   if(!j.stills.empty()&&!j.stills.count(n))continue;
   r.frame(shot,i,n,trace);count++;
   if(j.stillsDir.empty()){
    if(fwrite(r.pixels.data(),1,r.pixels.size(),stdout)!=r.pixels.size())throw std::runtime_error("V3 picture pipe closed");
   }else{char name[80];snprintf(name,sizeof name,"frame-%06d.ppm",n);r.stillImage(j.stillsDir+"/"+name);}
  }
  if(count!=count0)fprintf(stderr,"V3 scene %zu · %s · %d native frames\n",i+1,shot.tag.c_str(),count-count0);
 }
 unsigned err=glGetError();if(err)throw std::runtime_error("V3 GLES error "+std::to_string(err));
 fprintf(stderr,"V3 picture: %d frames in %.2f s\n",count,std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());
 return count?0:1;
}catch(const std::exception&e){fprintf(stderr,"V3 render error: %s\n",e.what());return 1;}}
