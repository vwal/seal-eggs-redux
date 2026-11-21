#include "../include/options_abi.h"
#include <stdint.h>

typedef void (*ConfigureFn)(void *, unsigned, unsigned);
typedef void (*InitFn)(void *, const uint32_t *, void *);
typedef void (*ProcessFn)(void *, unsigned, const void *, const void *, const void *, const void *, const void *, const void *, void *, unsigned);
#define CONFIGURE ((ConfigureFn)0x08040b3du)
#define INITIALIZE ((InitFn)0x08042a3du)
#define PROCESS ((ProcessFn)0x0804f945u)

/* These are shell overrides measured in full-core samples, not seconds.
 * Clean media consumes half as many samples through its existing FIR SRC.
 * Cold consumes two thirds through the added rational FIR adapter.
 * Amplitude normalization, pitch and stereo controls remain dimensionless.
 */
static const uint32_t sample_overrides[5] = {
    0x2403b62cu, /* voice-stealing fade */
    0x2403b638u, /* clock/spray quantization grid */
    0x2403b63cu, /* spray extent */
    0x2403b640u, /* lookback */
    0x2403b644u, /* grain duration including overlap */
};

void cold_reset(void);
void cold_process(void *, unsigned, const void *, const void *, const void *, const void *, const void *, const void *, void *, unsigned);

typedef struct { uint8_t active_quality, valid; } SunnyState;
#define STATE (*(volatile SunnyState *)SUNNY_STATE)

/* Called only at the existing engine-entry Configure site, after the shell's
 * incremental zero-fill has completed and with its skip-clear flag set.
 * Both12-bit media, like Digital PCM, correctly encode silence with zero bytes.
 * Preferences are deliberately not consulted from the live Process hook.
 */
__attribute__((used,noinline))
void sunny_configure(void *processor, unsigned original_media, unsigned mono) {
    unsigned quality = SEAL_OPTIONS.magic == OPTIONS_MAGIC ? SEAL_OPTIONS.beads_quality : 0;
    if (quality > BEADS_COLD) quality = 0;
    if (quality) {
        /* Configure alone does not reset all FIR histories or feedback
         * state. Reinitialize the retained processor while the shell is
         * already silent/cleared, preserving its physical buffer bindings.
         * Init's synchronous SDRAM clear remains disabled by the caller.
         */
        uint32_t banks[3];
        volatile uint32_t *p = (volatile uint32_t *)processor;
        banks[0] = p[0x17a0 / 4];
        banks[1] = p[0x17a4 / 4];
        banks[2] = p[0x17a8 / 4];
        INITIALIZE(processor, banks, (void *)(uintptr_t)p[0x6cf0 / 4]);
        CONFIGURE(processor, quality == BEADS_COLD ? 2 : 1, mono);
        if (quality == BEADS_COLD) cold_reset();
    } else {
        CONFIGURE(processor, original_media, mono);
    }
    STATE.active_quality = (uint8_t)quality;
    STATE.valid = 1;
}

/* Full AAPCS signature of beads::Processor::Process. The original callsite
 * passes ten integer/pointer arguments; feedback is within MixParameters.
 */
__attribute__((used,noinline))
void sunny_process(void *processor, unsigned seed, const void *gates,
                   const void *freeze, const void *density, const void *params,
                   const void *mix, const void *input, void *output, unsigned n) {
    unsigned media = ((volatile uint8_t *)processor)[0x6898];
    if (media != 1 && media != 2) {
        PROCESS(processor, seed, gates, freeze, density, params, mix, input, output, n);
        return;
    }
    float scale = media == 2 ? (2.0f / 3.0f) : 0.5f;
    float saved[5];
    for (unsigned i = 0; i < 5; ++i) {
        volatile float *p = (volatile float *)(uintptr_t)sample_overrides[i];
        saved[i] = *p;
        *p = saved[i] * scale;
    }
    if (media == 2) cold_process(processor, seed, gates, freeze, density, params, mix, input, output, n);
    else PROCESS(processor, seed, gates, freeze, density, params, mix, input, output, n);
    for (unsigned i = 0; i < 5; ++i)
        *(volatile float *)(uintptr_t)sample_overrides[i] = saved[i];
}
