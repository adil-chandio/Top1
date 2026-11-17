/* Complete headless GL/GLX shim. Background rendering never creates a
   context, so every entry point here is unreachable at runtime. */
#include <stddef.h>
#define R0 { return NULL; }
#define I0 { return 0; }
#define V0 { }
void *glXGetProcAddress(const unsigned char*n){(void)n;R0}
void *glXGetProcAddressARB(const unsigned char*n){(void)n;R0}
void *glXChooseVisual(void*d,int s,int*a){(void)d;(void)s;(void)a;R0}
void *glXChooseFBConfig(void*d,int s,const int*a,int*n){(void)d;(void)s;(void)a;*n=0;R0}
void *glXGetFBConfigs(void*d,int s,int*n){(void)d;(void)s;*n=0;R0}
int glXGetFBConfigAttrib(void*d,void*c,int a,int*v){(void)d;(void)c;(void)a;*v=0;I0}
void *glXGetVisualFromFBConfig(void*d,void*c){(void)d;(void)c;R0}
void *glXCreateContext(void*d,void*v,void*s,int x){(void)d;(void)v;(void)s;(void)x;R0}
void *glXCreateNewContext(void*d,void*c,int t,void*s,int x){(void)d;(void)c;(void)t;(void)s;(void)x;R0}
void glXDestroyContext(void*d,void*c){(void)d;(void)c;V0}
int glXMakeCurrent(void*d,unsigned long w,void*c){(void)d;(void)w;(void)c;I0}
int glXMakeContextCurrent(void*d,unsigned long a,unsigned long b,void*c){(void)d;(void)a;(void)b;(void)c;I0}
void *glXGetCurrentContext(void){R0}
void *glXGetCurrentDisplay(void){R0}
void *glXGetCurrentDrawable(void){R0}
void *glXGetCurrentReadDrawable(void){R0}
void glXSwapBuffers(void*d,unsigned long w){(void)d;(void)w;V0}
int glXQueryVersion(void*d,int*a,int*b){(void)d;*a=1;*b=4;return 1;}
int glXQueryContext(void*d,void*c,int a,int*v){(void)d;(void)c;(void)a;*v=0;I0}
int glXQueryExtension(void*d,int*a,int*b){(void)d;(void)a;*a=0;*b=0;I0}
unsigned long glXCreateWindow(void*d,void*c,unsigned long w,const int*a){(void)d;(void)c;(void)w;(void)a;return 0;}
void glXDestroyWindow(void*d,unsigned long w){(void)d;(void)w;V0}
void *glXCreatePbuffer(void*d,void*c,const int*a){(void)d;(void)c;(void)a;R0}
void glXDestroyPbuffer(void*d,unsigned long p){(void)d;(void)p;V0}
void *glXCreateGLXPixmap(void*d,void*v,unsigned long p){(void)d;(void)v;(void)p;R0}
void glXDestroyGLXPixmap(void*d,void*p){(void)d;(void)p;V0}
void glFinish(void){V0}
void glFlush(void){V0}
