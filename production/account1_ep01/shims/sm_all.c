/* Headless ICE/SM shims (session management is never used). */
#include <stddef.h>
void *SmcOpenConnection(void){return NULL;}
void SmcCloseConnection(void){}
void *IceOpenConnection(void){return NULL;}
void IceCloseConnection(void){}
