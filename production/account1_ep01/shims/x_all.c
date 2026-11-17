/* Headless X11 / XFixes / XInput / xkbcommon shims. */
#include <stddef.h>
#define R0 { return NULL; }
#define I0 { return 0; }
#define V0 { }
/* XFixes */
void XFixesShowCursor(void){V0}
void XFixesHideCursor(void){V0}
void *XFixesCreateCursor(void){R0}
void XFixesDestroyCursor(void){V0}
int XFixesQueryExtension(void*d,int*a,int*b){(void)d;*a=0;*b=0;I0}
void XFixesSelectCursorInput(void){V0}
void XFixesGetCursorImage(void){V0}
void *XFixesGetCursorImageAndName(void){R0}
/* XRender */
void *XRenderCreatePicture(void){R0}
void XRenderFreePicture(void){V0}
void *XRenderFindVisualFormat(void){R0}
int XRenderQueryExtension(void*d,int*a,int*b){(void)d;*a=0;*b=0;I0}
void XRenderComposite(void){V0}
void XRenderFillRectangle(void){V0}
void XRenderSetPictureFilter(void){V0}
/* XInput */
void XCloseDevice(void){V0}
void XFreeDeviceList(void){V0}
void XFreeDeviceState(void){V0}
void *XGetExtensionVersion(void){R0}
void *XListInputDevices(void){R0}
void *XOpenDevice(void){R0}
void *XQueryDeviceState(void){R0}
void XSelectExtensionEvent(void){V0}
void *_XiGetDevicePresenceNotifyEvent(void){R0}
/* Xlib core bits the GUI backend imports */
void *XOpenDisplay(const char*n){(void)n;R0}
int XCloseDisplay(void*d){(void)d;I0}
int XInitThreads(void){return 0;}
void XFree(void*p){(void)p;V0}
void *XSetErrorHandler(void*h){(void)h;R0}
void *XSetIOErrorHandler(void*h){(void)h;R0}
