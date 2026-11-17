/* Headless Chromium never opens the certificate dialog. These no-op stubs
   satisfy the dynamic linker; the renderer only needs WebGL + SwiftShader. */
#include <stddef.h>
#include <time.h>

typedef int SECStatus;
typedef void* pointer;

/* ---- NSPR ---- */
int  PR_GetError(void) { return 0; }
int  PR_GetOSError(void) { return 0; }
int  PR_GetErrorTextLength(void) { return 0; }
char *PR_GetErrorText(unsigned int a) { (void)a; return (char*)""; }
void PR_Init(int a, int b, int c) { (void)a; (void)b; (void)c; }
long long PR_Now(void) { return (long long)time(0) * 1000000LL; }

/* ---- NSS ---- */
SECStatus NSS_InitReadWrite(const char *d) { (void)d; return 0; }
SECStatus NSS_NoDB_Init(const char *d) { (void)d; return 0; }
SECStatus NSS_SetAlgorithmPolicy(unsigned int a, unsigned int b, unsigned int c, unsigned int e)
  { (void)a;(void)b;(void)c;(void)e; return 0; }
int NSS_VersionCheck(const char *v) { (void)v; return 1; }
int NSS_IsInitialized(void) { return 1; }
void NSS_Shutdown(void) {}

/* ---- certificates ---- */
void *CERT_CreateSubjectCertList(void *a, void *b, void *c, unsigned int d)
  { (void)a;(void)b;(void)c;(void)d; return NULL; }
void CERT_DestroyCertList(void *a) { (void)a; }
void CERT_DestroyCertificate(void *a) { (void)a; }
void *CERT_DupCertificate(void *a) { (void)a; return NULL; }
void *CERT_FindCertByDERCert(void *a, void *b) { (void)a;(void)b; return NULL; }
void *CERT_GetCertTrust(void *a, void *b) { (void)a;(void)b; return NULL; }
void *CERT_GetDefaultCertDB(void) { return NULL; }
int  CERT_IsUserCert(void *a) { (void)a; return 0; }

/* ---- PK11 slot / cert surface ---- */
void PK11_DestroyGenericObjects(void *a) { (void)a; }
void *PK11_FindCertInSlot(void *a, void *b) { (void)a;(void)b; return NULL; }
void *PK11_FindGenericObjects(void *a, void *b) { (void)a;(void)b; return NULL; }
void PK11_FreeSlot(void *a) { (void)a; }
void *PK11_GetInternalKeySlot(void) { return NULL; }
void *PK11_GetModule(void *a) { (void)a; return NULL; }
void *PK11_GetNextGenericObject(void *a) { (void)a; return NULL; }
char *PK11_GetTokenName(void *a) { (void)a; return (char*)""; }
int  PK11_HasAttributeSet(void *a, void *b, int c) { (void)a;(void)b;(void)c; return 0; }
int  PK11_HasRootCerts(void) { return 0; }
SECStatus PK11_InitPin(void *a, char *b, char *c) { (void)a;(void)b;(void)c; return 0; }
int  PK11_IsPresent(void *a) { (void)a; return 0; }
void *PK11_ListCerts(int a, void *b) { (void)a;(void)b; return NULL; }
void *PK11_ListCertsInSlot(void *a) { (void)a; return NULL; }
int  PK11_NeedUserInit(void *a) { (void)a; return 0; }
SECStatus PK11_ReadRawAttribute(void *a, void *b, void *c, void *d, unsigned int *e)
  { (void)a;(void)b;(void)c;(void)d;(void)e; return -1; }
void *PK11_ReferenceSlot(void *a) { (void)a; return NULL; }
void PK11_SetPasswordFunc(void *a) { (void)a; }

/* ---- SECITEM ---- */
void *SECITEM_AllocItem(void *a, void *b, unsigned int c) { (void)a;(void)b;(void)c; return NULL; }
void SECITEM_FreeItem(void *a, int b) { (void)a;(void)b; }

/* ---- SECMOD ---- */
void SECMOD_DestroyModule(void *a) { (void)a; }
void *SECMOD_GetDefaultModuleList(void) { return NULL; }
void *SECMOD_GetDefaultModuleListLock(void) { return NULL; }
void *SECMOD_GetReadLock(void) { return NULL; }
void *SECMOD_LoadUserModule(char *a, void *b, int c) { (void)a;(void)b;(void)c; return NULL; }
void SECMOD_ReleaseReadLock(void) { (void)0; }

/* ---- misc ---- */
int  strcasecmp(const char *a, const char *b) { (void)a;(void)b; return 0; }
int  strncasecmp(const char *a, const char *b, size_t n) { (void)a;(void)b;(void)n; return 0; }

/* ---- OPENSSL compatibility shims referenced by Chromium's NSS layer ---- */
void *OPENSSL_memory_alloc(size_t n) { (void)n; return NULL; }
void OPENSSL_memory_free(void *p) { (void)p; }
size_t OPENSSL_memory_get_size(void *p) { (void)p; return 0; }
