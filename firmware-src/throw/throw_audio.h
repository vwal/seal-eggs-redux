#ifndef SEAL_THROW_AUDIO_H
#define SEAL_THROW_AUDIO_H
#include <stdint.h>

#define THROW_AUDIO_STATE 0x24070d00u
#define THROW_SAMPLE_RATE 93750u
#define THROW_RING_SAMPLES 1048576u
#define THROW_MAX_BLOCK 96u
#define THROW_DURATION_SAMPLES 187500u

/* Call after the native writer has completed BOTH channel blocks. Cursors
 * identify the next write (the writer decrements). Baselines are sample ages,
 * not absolute read positions. This helper only reads the native rings.
 * wet_gain is the native wet-mix gain, excluding any post-mix processors. */
typedef struct {
  float *left;
  float *right;
  const float *ring_left;
  const float *ring_right;
  uint32_t postcursor_left;
  uint32_t postcursor_right;
  uint32_t frames;
  uint32_t delay_left;
  uint32_t delay_right;
  float wet_gain;
} ThrowBlock;

/* direction: 0=no new launch, +1=pitch up, -1=pitch down. Active launches are
 * ignored. Call once per native stereo block, never once per sample.
 * Invalid descriptors fail closed. No button or preference processing here. */
void throw_process(const ThrowBlock *block, int direction);
uint32_t throw_active(void);
/* Audio-context cancellation: continue the cursor, fade for <=32 ms, reset
 * after an exact-zero final voice sample. Repeated cancellation is idempotent. */
void throw_cancel(void);
/* Hard reset is only for boot, an already-muted path, or a silent inactive
 * voice. An audible normal exit should use throw_cancel instead. */
void throw_reset(void);

#endif
