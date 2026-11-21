#include "../include/options_abi.h"

typedef struct {
  uint32_t magic;
  uintptr_t bbd_owner;
  float bbd_threshold;
  float bbd_cap;
} NativeState;
#define STATE (*(volatile NativeState *)NATIVE_OPTIONS_STATE)
#define NATIVE_MAGIC 0x4e415431u

static float approach(float value, float target, float step) {
  if (value < target) return target - value <= step ? target : value + step;
  if (value > target) return value - target <= step ? target : value - step;
  return target;
}

/* Called immediately before the original BBD coefficient update, at its
 * existing audio-control boundary. Settled values are exact stock/mod floats. */
void native_bbd_update(void *owner) {
  float threshold = SEAL_OPTIONS.bbd_light ? 36.0f : 12.6f;
  float cap = SEAL_OPTIONS.bbd_light ? 12000.0f : 4200.0f;
  if (STATE.magic != NATIVE_MAGIC || STATE.bbd_owner != (uintptr_t)owner) {
    STATE.bbd_threshold = threshold;
    STATE.bbd_cap = cap;
    STATE.bbd_owner = (uintptr_t)owner;
    STATE.magic = NATIVE_MAGIC;
  } else {
    STATE.bbd_threshold = approach(STATE.bbd_threshold, threshold, 23.4f / 48.0f);
    STATE.bbd_cap = approach(STATE.bbd_cap, cap, 7800.0f / 48.0f);
  }
}

static void shelf(void *owner, unsigned gain_offset, unsigned dirty_offset,
                  float target, float step) {
  volatile float *gain = (volatile float *)((uintptr_t)owner + gain_offset);
  float next = approach(*gain, target, step);
  if (next != *gain) {
    *gain = next;
    *(volatile uint8_t *)((uintptr_t)owner + dirty_offset) = 1;
  }
}

/* Preserve histories; the native shelf code recomputes coefficients when dirty.
 * Move gains over ~49 ms at the nominal 96-frame host block, then snap exactly. */
void native_tape_update(void *owner) {
  float positive = SEAL_OPTIONS.tape_bright ? 0.0f : 3.0f;
  float negative = SEAL_OPTIONS.tape_bright ? 0.0f : -6.1f;
  shelf(owner, 0x78, 0x68, positive, 3.0f / 48.0f);
  shelf(owner, 0xcc, 0xbc, positive, 3.0f / 48.0f);
  shelf(owner, 0x120, 0x110, negative, 6.1f / 48.0f);
  shelf(owner, 0x174, 0x164, negative, 6.1f / 48.0f);
}
