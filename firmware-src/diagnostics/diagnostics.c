#include "diagnostics_abi.h"
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(a))
static uint32_t tag(void) {
  uint32_t shell=U32(0x24070004u);
  if(shell) {
    if(shell!=3u)return DIAGNOSTICS_TRANSITION;
    return U32(0x240700e0u)==1u?DIAGNOSTICS_MICROLOOPS:DIAGNOSTICS_BEADS;
  }
  if(U32(0x240002b0u))return DIAGNOSTICS_TRANSITION;
  uint32_t m=U32(0x24000268u);
  return m<3u?m:DIAGNOSTICS_TRANSITION;
}
static void increment(volatile uint32_t *value) {
  if(*value!=0xffffffffu)++*value;
}
/* Called after the unchanged original meter has sampled elapsed cycles.
   No audio buffer, preference, native DSP state, FP register or FPSCR is written. */
void diagnostics_collect(void) {
  if(DIAGNOSTICS.magic!=DIAGNOSTICS_MAGIC) {
    volatile uint32_t *p=(volatile uint32_t *)(uintptr_t)DIAGNOSTICS_RAM;
    for(unsigned i=0;i<sizeof(Diagnostics)/4u;++i)p[i]=0;
    DIAGNOSTICS.version=DIAGNOSTICS_VERSION;
    DIAGNOSTICS.magic=DIAGNOSTICS_MAGIC;
  }
  uint32_t t=tag(),elapsed=U32(0x24030568u),budget=U32(0x24030570u);
  uint32_t start=U32(0x24030564u),ctrl=U32(0xe0001000u);
  uint32_t valid=budget && elapsed && (ctrl&1u) && !(ctrl&(1u<<25));
  DIAGNOSTICS.last_tag=t;DIAGNOSTICS.last_budget=budget;
  DIAGNOSTICS.last_elapsed=elapsed;DIAGNOSTICS.last_start=start;
  DIAGNOSTICS.last_valid=valid;
  increment(&DIAGNOSTICS.callbacks);
  volatile DiagnosticBucket *b=&DIAGNOSTICS.bucket[t];
  if(valid) {
    increment(&b->observations);b->last_elapsed=elapsed;
    if(!b->max_budget || (uint64_t)elapsed*b->max_budget>(uint64_t)b->max_elapsed*budget) {
      b->max_elapsed=elapsed;b->max_budget=budget;
    }
    if((uint64_t)elapsed*100u>=(uint64_t)budget*99u)increment(&b->near_deadline_count);
    /* An interval belongs to the callback which began it. This preserves late
       Digi evidence when the next callback has already escaped to BBD. It is
       scheduling evidence, not proof all interval time was spent in Digi. */
    if(DIAGNOSTICS.previous_valid && DIAGNOSTICS.previous_tag<DIAGNOSTICS_BUCKETS) {
      volatile DiagnosticBucket *previous=&DIAGNOSTICS.bucket[DIAGNOSTICS.previous_tag];
      uint32_t gap=start-DIAGNOSTICS.previous_start;
      if(gap>previous->max_start_gap)previous->max_start_gap=gap;
      uint32_t previous_budget=DIAGNOSTICS.previous_budget;
      if(DIAGNOSTICS.callbacks>4u &&
         (uint64_t)gap*4u>(uint64_t)previous_budget*5u)increment(&previous->late_start_count);
    }
  } else {
    increment(&DIAGNOSTICS.invalid_samples);increment(&b->unavailable_count);
  }
  DIAGNOSTICS.previous_start=start;DIAGNOSTICS.previous_tag=t;
  DIAGNOSTICS.previous_budget=budget;DIAGNOSTICS.previous_valid=valid;
}
