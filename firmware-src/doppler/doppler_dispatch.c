#include <stdint.h>
#include <stddef.h>
#include "options_abi.h"

/* State is private, per-channel, and never persisted. Input, output, and
 * modulation descriptors are the firmware's {float*, uint32_t length}. */
typedef struct { float *data; uint32_t size; } Buffer;
typedef struct {
  uint32_t seen, engine;
  float last_sample, fade_from;
  uint32_t fade_remaining;
} ChannelState;
_Static_assert(sizeof(ChannelState)*2<=256,"Doppler state reservation");
_Static_assert(offsetof(SealOptions,doppler)==4,"Shared preference ABI");
#define CHANNELS ((volatile ChannelState *)DOPPLER_STATE)
#define WORD(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define FLOAT(a) (*(volatile float *)(uintptr_t)(a))
#define FADE_SAMPLES 256u

typedef void (*Reader)(void *, Buffer *, Buffer *, Buffer *);

/* Preserve parameters, memory, write position, and native-freeze flag.
 * Discard stale crossfade/read-head instances; the original scheduler creates
 * fresh heads using its retained size/rate/envelope configuration. */
static void restart_stock_heads(uint8_t *o) {
  WORD(o+0x28)=WORD(o+0x24);
  WORD(o+0x34)=WORD(o+0x14);
  WORD(o+0x40)=WORD(o+0x24)-WORD(o+0x20);
  FLOAT(o+0x48)=0.0f; FLOAT(o+0x4c)=0.0f; FLOAT(o+0x50)=0.0f;
  WORD(o+0x58)=0; WORD(o+0x60)=0; WORD(o+0x68)=0;
  BYTE(o+0x70)=0; BYTE(o+0x94)=0;
  BYTE(o+0xe4)=0; BYTE(o+0x108)=0;
  FLOAT(o+0xc0)=1.0f; FLOAT(o+0x134)=1.0f;
}

__attribute__((section(".text.doppler_dispatch")))
void doppler_dispatch(void *object, Buffer *input, Buffer *output, Buffer *mod) {
  uint8_t *o=(uint8_t *)object;
  uint32_t channel=(uintptr_t)object==0x2402f750u;
  volatile ChannelState *s=&CHANNELS[channel];
  uint32_t reverse_state=0x24030108u+channel*0x38u;
  uint32_t preference=SEAL_OPTIONS.doppler;
  uint32_t forced=WORD(0x24030100u)!=0 || WORD(reverse_state+8)!=0 ||
                  WORD(reverse_state+0x24)!=0;
  /* Throw overlays the original Stock delay; it is not a Doppler reader. */
  uint32_t engine=(preference==DOPPLER_SMOOTH || preference==DOPPLER_STEPPED)||forced;
  /* Native Freeze already uses the original fallback within Doppler. Do not
   * rebuild its captured read heads while it is frozen. Preference is kept. */
  if (s->seen && BYTE(o+0x30) && !forced) engine=s->engine;
  if (!s->seen) {
    s->seen=1; s->engine=engine; s->fade_remaining=0;
  } else if (s->engine!=engine) {
    WORD(0x24030180u+channel*0x10u)=0;
    WORD(0x240305a0u+channel*0x10u)=0;
    WORD(0x240305a8u+channel*0x10u)=0;
    if (!engine) restart_stock_heads(o);
    s->engine=engine;
    s->fade_from=s->last_sample;
    s->fade_remaining=FADE_SAMPLES;
  }
  if (engine) {
    ((Reader)0x08070579u)(object,input,output,mod);
  } else {
    ((Reader)0x08071e61u)(object,input,output,mod);
    /* Stock writes the main delay ring, not the acceleration mirror. */
    WORD(0x240305a0u+channel*0x10u)=0;
    WORD(0x240305a8u+channel*0x10u)=0;
    WORD(0x24030180u+channel*0x10u)=0;
    uint32_t n=WORD(o+0x20);
    if (n>96) n=96;
    for (uint32_t i=0;i<n;i++) FLOAT(0x240301a0u+channel*0x180u+i*4u)=1.0f;
  }
  uint32_t n=WORD(o+0x20);
  if (n>output->size) n=output->size;
  if (n && output->data) {
    uint32_t remain=s->fade_remaining;
    if (remain) {
      float from=s->fade_from;
      uint32_t count=n<remain?n:remain;
      for (uint32_t i=0;i<count;i++) {
        float a=(float)(FADE_SAMPLES-remain+1u)*(1.0f/(float)FADE_SAMPLES);
        output->data[i]=from+(output->data[i]-from)*a;
        --remain;
      }
      s->fade_remaining=remain;
    }
    s->last_sample=output->data[n-1];
  }
}
