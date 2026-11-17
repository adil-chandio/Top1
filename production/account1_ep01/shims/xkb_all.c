/* Headless xkbcommon shims. No key is ever read during a render. */
#include <stddef.h>
#define R0 { return NULL; }
#define I0 { return 0; }
#define V0 { }
void *xkb_context_new(int f){(void)f;R0}
void xkb_context_unref(void*c){(void)c;V0}
void *xkb_context_ref(void*c){(void)c;R0}
void *xkb_keymap_new_from_string(void*c,const char*s,int a,int b){(void)c;(void)s;(void)a;(void)b;R0}
void *xkb_keymap_new_from_names(void*c,const void*n,int f){(void)c;(void)n;(void)f;R0}
void xkb_keymap_unref(void*k){(void)k;V0}
void *xkb_keymap_ref(void*k){(void)k;R0}
int xkb_keymap_key_repeats(void*k,unsigned int key){(void)k;(void)key;I0}
int xkb_keymap_mod_get_index(void*k,const char*n){(void)k;(void)n;I0}
int xkb_keymap_min_keycode(void*k){(void)k;I0}
int xkb_keymap_max_keycode(void*k){(void)k;I0}
void *xkb_state_new(void*k){(void)k;R0}
void xkb_state_unref(void*s){(void)s;V0}
void *xkb_state_ref(void*s){(void)s;R0}
void *xkb_state_get_keymap(void*s){(void)s;R0}
int xkb_state_key_get_one_sym(void*s,unsigned int k){(void)s;(void)k;I0}
int xkb_state_key_get_utf8(void*s,unsigned int k,char*b,size_t n){(void)s;(void)k;(void)b;(void)n;I0}
int xkb_state_key_get_syms(void*s,unsigned int k,const void**sym){(void)s;(void)k;(void)sym;I0}
int xkb_state_serialize_mods(void*s,int c){(void)s;(void)c;I0}
unsigned int xkb_state_serialize_layout(void*s,int c){(void)s;(void)c;return 0;}
int xkb_state_update_mask(void*s,int a,int b,int c,int d,int e,int f){(void)s;(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;I0}
int xkb_state_update_key(void*s,unsigned int k,int d){(void)s;(void)k;(void)d;I0}
int xkb_state_mod_name_is_active(void*s,const char*n,int t){(void)s;(void)n;(void)t;I0}
int xkb_state_mod_index_is_active(void*s,unsigned int i,int t){(void)s;(void)i;(void)t;I0}
int xkb_state_layout_index_is_active(void*s,unsigned int i,int t){(void)s;(void)i;(void)t;I0}
void *xkb_compose_table_new_from_locale(void*c,const char*l,int f){(void)c;(void)l;(void)f;R0}
void xkb_compose_table_unref(void*t){(void)t;V0}
void *xkb_compose_state_new(void*t,int f){(void)t;(void)f;R0}
void xkb_compose_state_unref(void*s){(void)s;V0}
int xkb_compose_state_feed(void*s,unsigned int k){(void)s;(void)k;I0}
int xkb_compose_state_get_status(void*s){(void)s;I0}
int xkb_compose_state_get_utf8(void*s,char*b,size_t n){(void)s;(void)b;(void)n;I0}
void xkb_compose_state_reset(void*s){(void)s;V0}
