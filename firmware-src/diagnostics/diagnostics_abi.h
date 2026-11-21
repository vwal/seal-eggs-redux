#ifndef SEAL_DIAGNOSTICS_ABI_H
#define SEAL_DIAGNOSTICS_ABI_H
#include <stdint.h>
#define DIAGNOSTICS_RAM 0x24070c00u
#define DIAGNOSTICS_MAGIC 0x44494134u
#define DIAGNOSTICS_VERSION 1u
#define DIAGNOSTICS_TAPE 0u
#define DIAGNOSTICS_BBD 1u
#define DIAGNOSTICS_DIGI 2u
#define DIAGNOSTICS_MICROLOOPS 3u
#define DIAGNOSTICS_BEADS 4u
#define DIAGNOSTICS_TRANSITION 5u
#define DIAGNOSTICS_BUCKETS 6u
/* All statistics are volatile, reset at power-on, and never persisted. */
typedef struct {
  uint32_t observations;
  uint32_t max_elapsed;
  uint32_t max_budget;
  uint32_t max_start_gap;
  uint32_t near_deadline_count;
  uint32_t late_start_count;
  uint32_t unavailable_count;
  uint32_t last_elapsed;
} DiagnosticBucket;
typedef struct {
  uint32_t magic;
  uint32_t version;
  uint32_t callbacks;
  uint32_t last_tag;
  uint32_t last_budget;
  uint32_t last_elapsed;
  uint32_t last_start;
  uint32_t previous_start;
  uint32_t previous_tag;
  uint32_t previous_budget;
  uint32_t previous_valid;
  uint32_t invalid_samples;
  uint32_t last_valid;
  DiagnosticBucket bucket[DIAGNOSTICS_BUCKETS];
} Diagnostics;
#define DIAGNOSTICS (*(volatile Diagnostics *)(uintptr_t)DIAGNOSTICS_RAM)
_Static_assert(sizeof(Diagnostics)<=256,"diagnostics allocation exceeded");
/* Integer comparisons avoid both overflow and hardware floating-point changes. */
static inline uint32_t diagnostics_peak_color(uint32_t elapsed,uint32_t budget) {
  if(!budget)return 0x00ff00ffu;
  uint64_t e=(uint64_t)elapsed*100u;
  if(e>=(uint64_t)budget*99u)return 0x000000ffu;
  if(e>=(uint64_t)budget*95u)return 0x000040ffu;
  if(e>=(uint64_t)budget*90u)return 0x0000ffffu;
  return 0x0000ff00u;
}
/* Called by options after its own overlay/acknowledgement handling.
   Hold FREEZE/ALT alone: FREEZE=live meter, DELAY=worst native Digi callback,
   MOD=latched native Digi deadline status, even after MODEL escape.
   Beads/Microloops own their existing display; TAP keeps native AUX indication.
   Return zero means this diagnostic does not own that LED. */
static inline uint32_t diagnostics_led_color(uint32_t id) {
  if(*(volatile uint32_t *)(uintptr_t)0x20004874u!=1u ||
     *(volatile uint32_t *)(uintptr_t)0x20004db0u!=0u ||
     *(volatile uint32_t *)(uintptr_t)0x24070004u!=0u || id==1u)return 0;
  if(id>3u)return 0;
  if(DIAGNOSTICS.magic!=DIAGNOSTICS_MAGIC || !DIAGNOSTICS.last_valid)
    return 0x00ff00ffu;
  if(id==0u)return *(volatile uint32_t *)(uintptr_t)0x2403057cu;
  volatile DiagnosticBucket *d=&DIAGNOSTICS.bucket[DIAGNOSTICS_DIGI];
  if(id==3u && (d->near_deadline_count || d->late_start_count))return 0x000000ffu;
  if(d->unavailable_count)return 0x00ff00ffu;
  if(!d->observations)return 0x00400000u;
  if(id==2u)return diagnostics_peak_color(d->max_elapsed,d->max_budget);
  return 0x0000ff00u;
}
#endif
