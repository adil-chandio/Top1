#pragma once
// Minimal EGL/GLES ABI used by the offline renderer. No window or network server.
#include <array>
#include <vector>
#include <string>
#include <fstream>
#include <stdexcept>
#include <cmath>
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <algorithm>
#include <cstring>
extern "C" {
void *eglGetProcAddress(const char*); int eglGetError();
unsigned eglInitialize(void*,int*,int*); unsigned eglBindAPI(unsigned); unsigned eglChooseConfig(void*,const int*,void**,int,int*);
void *eglCreateContext(void*,void*,void*,const int*); void *eglCreatePbufferSurface(void*,void*,const int*); unsigned eglMakeCurrent(void*,void*,void*,void*);
unsigned eglDestroySurface(void*,void*); unsigned eglDestroyContext(void*,void*); unsigned eglTerminate(void*);
const unsigned char *glGetString(unsigned); unsigned glGetError();
void glClearColor(float,float,float,float); void glClear(unsigned); void glReadPixels(int,int,int,int,unsigned,unsigned,void*);
void glViewport(int,int,int,int); void glEnable(unsigned); void glDisable(unsigned); void glDepthMask(unsigned char); void glDepthFunc(unsigned);
void glColorMask(unsigned char,unsigned char,unsigned char,unsigned char); void glPolygonOffset(float,float);
unsigned glCreateShader(unsigned);void glShaderSource(unsigned,int,const char*const*,const int*);void glCompileShader(unsigned);void glGetShaderiv(unsigned,unsigned,int*);void glGetShaderInfoLog(unsigned,int,int*,char*);
unsigned glCreateProgram();void glAttachShader(unsigned,unsigned);void glLinkProgram(unsigned);void glGetProgramiv(unsigned,unsigned,int*);void glGetProgramInfoLog(unsigned,int,int*,char*);void glUseProgram(unsigned);void glDeleteShader(unsigned);
int glGetUniformLocation(unsigned,const char*);void glUniform1f(int,float);void glUniform1i(int,int);void glUniform2f(int,float,float);void glUniform3f(int,float,float,float);void glUniform4f(int,float,float,float,float);void glUniformMatrix4fv(int,int,unsigned char,const float*);
void glGenBuffers(int,unsigned*);void glBindBuffer(unsigned,unsigned);void glBufferData(unsigned,ptrdiff_t,const void*,unsigned);void glBufferSubData(unsigned,ptrdiff_t,ptrdiff_t,const void*);
void glGenVertexArrays(int,unsigned*);void glBindVertexArray(unsigned);void glEnableVertexAttribArray(unsigned);void glVertexAttribPointer(unsigned,int,unsigned,unsigned char,int,const void*);void glVertexAttribDivisor(unsigned,unsigned);
void glDrawArrays(unsigned,int,int);void glDrawElementsInstanced(unsigned,int,unsigned,const void*,int);
void glGenTextures(int,unsigned*);void glDeleteTextures(int,const unsigned*);void glBindTexture(unsigned,unsigned);void glTexParameteri(unsigned,unsigned,int);void glTexImage2D(unsigned,int,int,int,int,int,unsigned,unsigned,const void*);void glGenerateMipmap(unsigned);void glActiveTexture(unsigned);void glPixelStorei(unsigned,int);
void glGenFramebuffers(int,unsigned*);void glBindFramebuffer(unsigned,unsigned);void glFramebufferTexture2D(unsigned,unsigned,unsigned,unsigned,int);unsigned glCheckFramebufferStatus(unsigned);void glDrawBuffers(int,const unsigned*);void glReadBuffer(unsigned);
}
namespace ant {
constexpr float pi=3.14159265358979323846f, tau=2*pi;
struct V2{float x=0,y=0;};
struct V{float x=0,y=0,z=0;V operator+(V a)const{return{x+a.x,y+a.y,z+a.z};}V operator-(V a)const{return{x-a.x,y-a.y,z-a.z};}V operator*(float k)const{return{x*k,y*k,z*k};}V operator/(float k)const{return *this*(1/k);}V& operator+=(V a){*this=*this+a;return *this;}};
inline float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;} inline V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline float len(V a){return std::sqrt(dot(a,a));}inline V norm(V a){return a/std::max(.000001f,len(a));}inline float sat(float t){return std::clamp(t,0.f,1.f);}inline float mix(float a,float b,float t){return a+(b-a)*t;}inline V mix(V a,V b,float t){return a+(b-a)*t;}
inline float ease(float t){t=sat(t);return t*t*(3-2*t);}inline float ramp(float a,float b,float t){return ease((t-a)/(b-a));} inline float pulse(float a,float b,float c,float t){return ramp(a,b,t)*(1-ramp(b,c,t));}
struct M{float a[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};};
inline M mul(const M&a,const M&b){M r;for(int c=0;c<4;c++)for(int j=0;j<4;j++){r.a[c*4+j]=0;for(int k=0;k<4;k++)r.a[c*4+j]+=a.a[k*4+j]*b.a[c*4+k];}return r;}
inline M basis(V x,V y,V z,V p){return M{{x.x,x.y,x.z,0, y.x,y.y,y.z,0, z.x,z.y,z.z,0, p.x,p.y,p.z,1}};}
inline M loc(V p){return basis({1,0,0},{0,1,0},{0,0,1},p);}inline M size(V s){return basis({s.x,0,0},{0,s.y,0},{0,0,s.z},{});}
inline M ry(float r){float c=cosf(r),s=sinf(r);return basis({c,0,s},{0,1,0},{-s,0,c},{});}inline M rz(float r){float c=cosf(r),s=sinf(r);return basis({c,s,0},{-s,c,0},{0,0,1},{});}inline M rx(float r){float c=cosf(r),s=sinf(r);return basis({1,0,0},{0,c,s},{0,-s,c},{});}
inline V point(const M&m,V p){return{m.a[0]*p.x+m.a[4]*p.y+m.a[8]*p.z+m.a[12],m.a[1]*p.x+m.a[5]*p.y+m.a[9]*p.z+m.a[13],m.a[2]*p.x+m.a[6]*p.y+m.a[10]*p.z+m.a[14]};}
inline M tr(const M&m,V p,V s){return mul(m,mul(loc(p),size(s)));}
inline M look(V eye,V target,V up={0,1,0}){V f=norm(target-eye),r=norm(cross(f,up)),u=cross(r,f);return M{{r.x,u.x,-f.x,0,r.y,u.y,-f.y,0,r.z,u.z,-f.z,0,-dot(r,eye),-dot(u,eye),dot(f,eye),1}};}
inline M persp(float f,float asp,float n,float z){float t=1/tanf(f*pi/360);return M{{t/asp,0,0,0,0,t,0,0,0,0,(z+n)/(n-z),-1,0,0,2*z*n/(n-z),0}};}
inline M ortho(float span,float n,float f){return M{{1/span,0,0,0,0,1/span,0,0,0,0,2/(n-f),0,0,0,(f+n)/(n-f),1}};}
struct Rng{uint32_t n;float f(){n^=n<<13;n^=n>>17;n^=n<<5;return (n>>8)*0x1p-24f;}float r(float a,float b){return mix(a,b,f());}};
inline V rgb(int c){auto f=[](float v){return powf(v/255,2.15f);};return{f((c>>16)&255),f((c>>8)&255),f(c&255)};}
constexpr unsigned ARRAY=0x8892,ELEM=0x8893,FLOAT=0x1406,UINT=0x1405,UB=0x1401,STATIC=0x88e4,STREAM=0x88e0,TEX2D=0xde1,RGBA=0x1908,RGB=0x1907,RGBA8=0x8058,TEXTURE0=0x84c0,FB=0x8d40, ATTACH=0x8ce0,DEPTH_ATT=0x8d00,DEPTH=0x1902,DEPTH24=0x81a6,CLEAR_COLOR=0x4000,CLEAR_DEPTH=0x100,DEPTH_TEST=0xb71,LINEAR=0x2601,NEAREST=0x2600,CLAMP=0x812f,REPEAT=0x2901;
struct Device{
 void *d=nullptr,*ctx=nullptr,*surface=nullptr;
 Device(int w,int h){
  using PF=void*(*)(unsigned,void*,const int*);auto fn=(PF)eglGetProcAddress("eglGetPlatformDisplayEXT");
  const int attr[]={0x3203,0x3450,0x3209,0x3487,0x3038};d=fn?fn(0x3202,nullptr,attr):nullptr;
  int a,b,c;void*cfg;
  if(!d||!eglInitialize(d,&a,&b)||!eglBindAPI(0x30a0))throw std::runtime_error("ANGLE/SwiftShader EGL initialization failed");
  int conf[]={0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3025,24,0x3033,1,0x3040,0x40,0x3038};
  int p[]={0x3057,w,0x3056,h,0x3038}, cs[]={0x3098,3,0x3038};
  if(!eglChooseConfig(d,conf,&cfg,1,&c)||!c)throw std::runtime_error("no GLES3 config");
  surface=eglCreatePbufferSurface(d,cfg,p);ctx=eglCreateContext(d,cfg,nullptr,cs);
  if(!surface||!ctx||!eglMakeCurrent(d,surface,surface,ctx))throw std::runtime_error("EGL PBuffer failed");
  fprintf(stderr,"Renderer: %s\n",glGetString(0x1f01)); glPixelStorei(0xd05,1);glPixelStorei(0xcf5,1);
 }
 ~Device(){eglMakeCurrent(d,nullptr,nullptr,nullptr);eglDestroyContext(d,ctx);eglDestroySurface(d,surface);eglTerminate(d);}
};
struct Program{unsigned id;Program(const char*vs,const char*fs){auto sh=[](unsigned type,const char*src){unsigned p=glCreateShader(type);glShaderSource(p,1,&src,nullptr);glCompileShader(p);int ok;glGetShaderiv(p,0x8b81,&ok);if(!ok){char log[8192];glGetShaderInfoLog(p,8192,nullptr,log);throw std::runtime_error(log);}return p;};unsigned v=sh(0x8b31,vs),f=sh(0x8b30,fs);id=glCreateProgram();glAttachShader(id,v);glAttachShader(id,f);glLinkProgram(id);int ok;glGetProgramiv(id,0x8b82,&ok);if(!ok){char log[8192];glGetProgramInfoLog(id,8192,nullptr,log);throw std::runtime_error(log);}glDeleteShader(v);glDeleteShader(f);}
 void use()const{glUseProgram(id);}int u(const char*k)const{return glGetUniformLocation(id,k);}void f(const char*k,float v)const{glUniform1f(u(k),v);}void i(const char*k,int v)const{glUniform1i(u(k),v);}void v2(const char*k,float x,float y)const{glUniform2f(u(k),x,y);}void v(const char*k,V v)const{glUniform3f(u(k),v.x,v.y,v.z);}void v4(const char*k,V v,float a)const{glUniform4f(u(k),v.x,v.y,v.z,a);}void m(const char*k,const M&m)const{glUniformMatrix4fv(u(k),1,0,m.a);}
};
struct Vertex{V p,n;V2 uv;};struct Instance{M mat;float color[4];};
struct Mesh{std::vector<Vertex> v;std::vector<unsigned> idx;unsigned vao=0,b[3];std::vector<Instance> live;bool shadow=true;
 void bind(){glGenVertexArrays(1,&vao);glBindVertexArray(vao);glGenBuffers(3,b);glBindBuffer(ARRAY,b[0]);glBufferData(ARRAY,v.size()*sizeof(Vertex),v.data(),STATIC);for(int i=0;i<3;i++){glEnableVertexAttribArray(i);glVertexAttribPointer(i,i==2?2:3,FLOAT,0,sizeof(Vertex),(void*)(uintptr_t)(i*12));}glBindBuffer(ELEM,b[1]);glBufferData(ELEM,idx.size()*sizeof(unsigned),idx.data(),STATIC);glBindBuffer(ARRAY,b[2]);for(int i=0;i<5;i++){glEnableVertexAttribArray(3+i);glVertexAttribPointer(3+i,4,FLOAT,0,sizeof(Instance),(void*)(uintptr_t)(i*16));glVertexAttribDivisor(3+i,1);}glBindVertexArray(0);}
 void add(M m,V c,float k){live.push_back({m,{c.x,c.y,c.z,k}});}void draw(bool upload){if(live.empty())return;glBindVertexArray(vao);if(upload){glBindBuffer(ARRAY,b[2]);glBufferData(ARRAY,live.size()*sizeof(Instance),live.data(),STREAM);}glDrawElementsInstanced(4,idx.size(),UINT,nullptr,live.size());}
};
inline unsigned texture(int w,int h,int internal,unsigned fmt,unsigned type,const void*data,bool mip=false,bool tile=false,bool near=false){unsigned t;glGenTextures(1,&t);glBindTexture(TEX2D,t);glTexImage2D(TEX2D,0,internal,w,h,0,fmt,type,data);glTexParameteri(TEX2D,0x2800,near?NEAREST:LINEAR);glTexParameteri(TEX2D,0x2801,mip?0x2703:near?NEAREST:LINEAR);glTexParameteri(TEX2D,0x2802,tile?REPEAT:CLAMP);glTexParameteri(TEX2D,0x2803,tile?REPEAT:CLAMP);if(mip)glGenerateMipmap(TEX2D);return t;}
inline void unit(int u,unsigned tex){glActiveTexture(TEXTURE0+u);glBindTexture(TEX2D,tex);}
inline std::vector<unsigned char> bytes(const std::string&f,size_t n){std::ifstream r(f,std::ios::binary);std::vector<unsigned char> b(n);r.read((char*)b.data(),n);if(r.gcount()!=(ptrdiff_t)n)throw std::runtime_error("bad asset: "+f);return b;}
}
