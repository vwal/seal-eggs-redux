#include "throw_audio.h"
#include <stddef.h>

#define RING_MASK (THROW_RING_SAMPLES - 1u)
#define ATTACK 3000u
#define END_TAPER 9375u
#define YOUNGEST 37500u
#define MIN_AGE 96u
#define MAX_AGE 937404u
#define UP_DELTA 0.3348398541700344f
#define DOWN_DELTA (-0.2508464615616592f)
#define PEAK 1.2f

typedef struct {
  uint32_t active;
  uint32_t elapsed;
  uint32_t cursor[2];
  float fraction[2]; /* distance consumed below cursor: actual phase=cursor-f */
  const float *ring[2];
  float delta;
  uint32_t cancel_total;
  uint32_t cancel_remaining;
  float cancel_gain;
  uint32_t anchor[2]; /* retained for diagnostics, not used to chase TIME */
} ThrowState;
_Static_assert(sizeof(ThrowState) <= 256, "throw audio state allocation exceeded");
_Static_assert(sizeof(ThrowBlock) == 40, "throw block ARM ABI changed");
#define STATE ((ThrowState *)(uintptr_t)THROW_AUDIO_STATE)

static int finite(float f) {
  union { float f; uint32_t u; } x = {f};
  return (x.u & 0x7f800000u) != 0x7f800000u;
}
static uint32_t clamp_age(uint32_t age) {
  if (age < MIN_AGE) return MIN_AGE;
  if (age > 937500u) return 937500u;
  return age;
}
static float smooth(float x) { return x*x*(3.0f-2.0f*x); }
static float envelope(uint32_t elapsed) {
  if (elapsed >= THROW_DURATION_SAMPLES) return 0.0f;
  if (elapsed < ATTACK) return PEAK*smooth((float)elapsed*(1.0f/ATTACK));
  uint32_t remain = THROW_DURATION_SAMPLES-elapsed;
  float q;
  if (remain < END_TAPER) {
    float x = (float)remain*(1.0f/END_TAPER);
    q = (END_TAPER/(float)(THROW_DURATION_SAMPLES-ATTACK))*(2.0f*x*x-x*x*x);
  } else q = (float)remain*(1.0f/(THROW_DURATION_SAMPLES-ATTACK));
  /* Fuller quadratic decay: 1-u^2, where u is elapsed release time.
   * Its slope is zero at the attack junction. Softening the final remaining
   * time above also makes the endpoint slope zero, with bounded block work. */
  return PEAK*q*(2.0f-q);
}

uint32_t throw_active(void) { return STATE->active; }
void throw_reset(void) {
  /* Never touch adjacent control state at 24070e00. */
  volatile uint32_t *p=(volatile uint32_t *)STATE;
  for(unsigned i=0;i<sizeof(ThrowState)/4u;++i)p[i]=0;
}
void throw_cancel(void) {
  ThrowState *s=STATE;
  if(!s->active || s->cancel_total)return;
  uint32_t n=THROW_DURATION_SAMPLES-s->elapsed;
  if(n>ATTACK)n=ATTACK;
  s->cancel_total=n;s->cancel_remaining=n;s->cancel_gain=envelope(s->elapsed);
}

static int launch(const ThrowBlock *b, int direction) {
  ThrowState *s=STATE;
  uint32_t left=clamp_age(b->delay_left),right=clamp_age(b->delay_right);
  uint32_t younger=left<right?left:right,older=left>right?left:right;
  /* A common age bias preserves the (clamped) native stereo delay difference.
   * +5 semitones consumes 31,391.237 samples; -5 adds 23,516.856. The 400 ms
   * younger reserve covers the up bend. Reserve the down bend at the old end.
   * If two baselines cannot fit together, decline the launch rather than
   * silently collapsing WIDTH or touching the native delay. */
  int32_t lower=(int32_t)YOUNGEST-(int32_t)younger;
  int32_t ceiling=(int32_t)MAX_AGE-(direction<0?23517:0);
  int32_t upper=ceiling-(int32_t)older;
  if(lower>upper)return 0;
  int32_t bias=lower>0?lower:0;
  if(bias>upper)bias=upper;
  uint32_t age_left=(uint32_t)((int32_t)left+bias);
  uint32_t age_right=(uint32_t)((int32_t)right+bias);
  s->anchor[0]=age_left;s->anchor[1]=age_right;
  s->cursor[0]=(b->postcursor_left+b->frames+age_left)&RING_MASK;
  s->cursor[1]=(b->postcursor_right+b->frames+age_right)&RING_MASK;
  s->fraction[0]=s->fraction[1]=0.0f;
  s->ring[0]=b->ring_left;s->ring[1]=b->ring_right;
  s->delta=direction>0?UP_DELTA:DOWN_DELTA;
  s->elapsed=0;s->cancel_total=0;s->cancel_remaining=0;s->cancel_gain=0.0f;
  s->active=1;
  return 1;
}

void throw_process(const ThrowBlock *b,int direction) {
  ThrowState *s=STATE;
  if(!s->active && direction==0)return;
  if(!b || !b->left || !b->right || !b->ring_left || !b->ring_right ||
     b->frames>THROW_MAX_BLOCK || !finite(b->wet_gain) ||
     ((uintptr_t)b->left&3u) || ((uintptr_t)b->right&3u) ||
     ((uintptr_t)b->ring_left&3u) || ((uintptr_t)b->ring_right&3u)) {
    throw_reset();return;
  }
  if(!b->frames)return;
  if(!s->active) {
    if(direction!=1 && direction!=-1)return;
    if(!launch(b,direction))return;
  }
  if(b->ring_left!=s->ring[0] || b->ring_right!=s->ring[1]) {
    /* An engine/ring replacement invalidates the history; fail closed. */
    throw_reset();return;
  }
  uint32_t remain=THROW_DURATION_SAMPLES-s->elapsed;
  if(s->cancel_total && s->cancel_remaining<remain)remain=s->cancel_remaining;
  uint32_t n=b->frames<remain?b->frames:remain;
  if(!n){throw_reset();return;}
  float wet=b->wet_gain;
  if(wet<0.0f)wet=0.0f;
  if(wet>1.0f)wet=1.0f;
  float g0,g1;
  if(s->cancel_total) {
    float scale=1.0f/(float)s->cancel_total;
    g0=s->cancel_gain*smooth((float)s->cancel_remaining*scale);
    g1=s->cancel_gain*smooth((float)(s->cancel_remaining-n)*scale);
  } else {
    g0=envelope(s->elapsed);g1=envelope(s->elapsed+n);
  }
  float gain=g0*wet;
  float gain_step=(g1-g0)*wet/(float)n;
  float rate=1.0f+s->delta*((float)s->elapsed+0.5f)*(1.0f/THROW_DURATION_SAMPLES);
  float rate_step=s->delta*(1.0f/THROW_DURATION_SAMPLES);
  uint32_t il=s->cursor[0],ir=s->cursor[1];
  float fl=s->fraction[0],fr=s->fraction[1];
  const float *rl=s->ring[0],*rr=s->ring[1];
  uint32_t last=remain==n;
  /* One compiled block loop; helpers and transcendental operations never run
   * per sample. A zero wet gain does not even store the original output, so
   * negative zero and NaN payloads in the base stream remain bit exact. */
  for(uint32_t i=0;i<n;++i) {
    if(wet!=0.0f && !(last && i+1u==n)) {
      float l0=rl[il],r0=rr[ir];
      float l=l0+(rl[(il-1u)&RING_MASK]-l0)*fl;
      float r=r0+(rr[(ir-1u)&RING_MASK]-r0)*fr;
      b->left[i]+=l*gain;b->right[i]+=r*gain;
    }
    fl+=rate;fr+=rate;
    uint32_t al=(uint32_t)fl,ar=(uint32_t)fr;
    il=(il-al)&RING_MASK;ir=(ir-ar)&RING_MASK;
    fl-=(float)al;fr-=(float)ar;
    rate+=rate_step;gain+=gain_step;
  }
  s->cursor[0]=il;s->cursor[1]=ir;s->fraction[0]=fl;s->fraction[1]=fr;
  s->elapsed+=n;
  if(s->cancel_total)s->cancel_remaining-=n;
  /* The final voice sample above is explicitly zero before state is reset. */
  if(last)throw_reset();
}
