#include "throw_control.h"
#include "throw_audio.h"
#include "options_abi.h"
#include <stddef.h>
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define F32(a) (*(volatile float *)(uintptr_t)(a))
#define OWNER 0x24000000u
#define LEFT 0x2402f5fcu
#define RIGHT 0x2402f750u
#define STEP 96u
#define SETTLE 9375u
#define QUALIFY 1875u

typedef struct {
 uint32_t magic, enabled, eligible, last_active;
 float raw_previous, virtual_time, held, settle_anchor, gesture_anchor;
 uint32_t clutch, pickup, armed, settled, qualified;
 int32_t sign, pending;
 uint32_t launches, ticks;
} Control;
_Static_assert(sizeof(Control)<=512,"throw control state allocation exceeded");
#define S ((Control *)(uintptr_t)THROW_CONTROL_STATE)
static float absf(float x) { return x<0?-x:x; }
static int finite(float f) {
 union {float f;uint32_t u;} x={f};return (x.u&0x7f800000u)!=0x7f800000u;
}
static int ui(void) {
 return U32(OPTIONS_UI_STATE)==OPTIONS_UI_MAGIC && U8(OPTIONS_UI_STATE+OPTIONS_UI_LAYER_OFFSET)!=0;
}
static int reverse(void) {
 return U32(0x24030100u) || U32(0x24030110u) || U32(0x2403012cu) ||
        U32(0x24030148u) || U32(0x24030164u);
}
/* Recharge applies to all three modified Digi responses. Store the exact
   preference in Control.enabled so every response change discards pickup. */
static uint32_t control_mode(uint32_t panel) {
 uint32_t mode=SEAL_OPTIONS.doppler;
 return SEAL_OPTIONS.magic==OPTIONS_MAGIC && mode>=1u && mode<=3u &&
        panel==2u && U32(OWNER+0x268u)==2u && U32(0x24070004u)==0 && !ui() ? mode:0u;
}
static int enabled(uint32_t panel) { return control_mode(panel)==3u; }
static int eligible(void) {
 return !ui() && !reverse() && !U8(LEFT+0x30u) && !U8(RIGHT+0x30u) &&
        !U32(OWNER+0x2b0u) && !(U32(OWNER+0x20cu)&8u);
}
static void rebase(float raw) {
 S->settle_anchor=raw;S->gesture_anchor=raw;S->armed=0;S->settled=0;
 S->qualified=0;S->sign=0;S->pending=0;
}
static void initialize(float raw) {
 volatile uint32_t *p=(volatile uint32_t *)S;
 for(unsigned i=0;i<sizeof(Control)/4u;++i)p[i]=0;
 S->magic=THROW_CONTROL_MAGIC;S->raw_previous=raw;S->virtual_time=raw;S->held=raw;
 rebase(raw);
}
float throw_control_time(float raw) {
 if(!finite(raw) || raw<0 || raw>1) {
  if(S->magic==THROW_CONTROL_MAGIC){rebase(S->raw_previous);S->enabled=0;}
  throw_cancel();return raw;
 }
 if(S->magic!=THROW_CONTROL_MAGIC)initialize(raw);
 ++S->ticks;
 /* Read the same current physical MODEL getter used later in this callback;
    the copied owner snapshot still describes the previous control block. */
 uint32_t panel=((uint32_t(*)(void))0x0800abc9u)();
 uint32_t en=control_mode(panel),active=throw_active();
 S->pending=0; /* A launch never survives a callback which skipped late mix. */
 if(!en) {
  if(U32(0x24070004u))throw_reset();else if(active)throw_cancel();
  S->enabled=0;S->eligible=0;S->last_active=active;
  S->clutch=0;S->pickup=0;S->raw_previous=raw;S->virtual_time=raw;S->held=raw;
  rebase(raw);return raw;
 }
 if(S->enabled!=en) {
  S->enabled=en;S->clutch=0;S->pickup=0;S->virtual_time=raw;S->held=raw;
  S->raw_previous=raw;rebase(raw);
 }
 uint32_t buttons=U32(0x20004584u)&15u;
 uint32_t clutch=(buttons&1u) && !ui();
 if(clutch) {
  if(!S->clutch)S->held=S->virtual_time;
  S->pickup=1;S->virtual_time=S->held;
 } else {
  if(S->pickup) {
   float a=S->raw_previous-S->held,b=raw-S->held;
   if(absf(b)<=.003f || (a<0 && b>=0) || (a>0 && b<=0))S->pickup=0;
  }
  S->virtual_time=S->pickup?S->held:raw;
 }
 S->clutch=clutch;S->raw_previous=raw;
 /* Legacy Smooth/Stepped share pickup only; never arm or launch a throw. */
 uint32_t ok=en==3u && eligible();
 if(ok!=S->eligible || (S->last_active && !active))rebase(raw);
 S->eligible=ok;S->last_active=active;
 if(!ok || buttons || active) {
  if((!ok || (buttons&4u)) && active)throw_cancel();
  rebase(raw);return S->virtual_time;
 }
 if(!S->armed) {
  if(absf(raw-S->settle_anchor)>.003f){S->settle_anchor=raw;S->settled=0;}
  else if(S->settled<SETTLE)S->settled+=STEP;
  if(S->settled>=SETTLE) {
   S->armed=1;S->gesture_anchor=raw;S->qualified=0;S->sign=0;
  }
 } else {
  float d=raw-S->gesture_anchor;
  int32_t sign=d>=.02f?1:d<=-.02f?-1:0;
  if(!sign){S->qualified=0;S->sign=0;}
  else {
   if(S->sign!=sign){S->qualified=0;S->sign=sign;}
   S->qualified+=STEP;
   if(S->qualified>=QUALIFY) {
    S->pending=-sign;S->armed=0;S->settled=0;S->qualified=0;
   }
  }
 }
 return S->virtual_time;
}
static float wet_gain(float m) {
 if(!finite(m) || m<=0)return 0;
 if(m>=1)return 1;
 float x=1.5707963705062866f*m,z=x*x;
 return x*(24948000.f+z*(-3643920.f+z*(126210.f-1331.f*z)))/
           (24948000.f+z*(514080.f+3990.f*z));
}
void throw_control_late(void *owner,void *output) {
 if(S->magic!=THROW_CONTROL_MAGIC)return;
 uint32_t active=throw_active();int direction=S->pending;S->pending=0;
 uint32_t ok=enabled(U32(OWNER+0x200u)) && eligible();
 if(!ok) {
  direction=0;rebase(S->raw_previous);S->eligible=0;
  if(U32(0x24070004u)){throw_reset();return;}
  if(active)throw_cancel();
 }
 if(!active && !direction)return;
 uintptr_t o=(uintptr_t)output;
 if((uintptr_t)owner!=OWNER || !o || (o&3u) ||
    U32(LEFT+0x10u)!=0xc0800000u || U32(RIGHT+0x10u)!=0xc0c00000u ||
    F32(LEFT+0x1cu)!=93750.f || F32(RIGHT+0x1cu)!=93750.f ||
    U32(LEFT+0x20u)!=96u || U32(RIGHT+0x20u)!=96u ||
    U32(o+12u)!=96u || U32(o+20u)!=96u) {
  throw_reset();rebase(S->raw_previous);return;
 }
 ThrowBlock b={
  (float *)(uintptr_t)U32(o+8u),(float *)(uintptr_t)U32(o+16u),
  (const float *)(uintptr_t)U32(LEFT+0x10u),(const float *)(uintptr_t)U32(RIGHT+0x10u),
  U32(LEFT+0x14u),U32(RIGHT+0x14u),96u,U32(LEFT+0x24u),U32(RIGHT+0x24u),
  wet_gain(F32(OWNER+0x254u))
 };
 throw_process(&b,direction);
 if(direction && throw_active())++S->launches;
 S->last_active=throw_active();
}
