#include "../include/options_abi.h"
#include <stdint.h>
#include <stddef.h>
#include "cold_coefficients.h"

typedef struct { float l, r; } Frame;
typedef struct {
    uint32_t down_head, up_head;
    uint8_t pending_edges, pending_freeze;
    uint8_t padding[2];
    Frame down_history[130]; /* mirrored 65-sample ring */
    Frame up_history[86];    /* mirrored 43-sample ring */
    Frame input[8], output[8];
    uint8_t gates[8], freeze[8];
} ColdState;
_Static_assert(sizeof(ColdState) <= 4096, "Cold SRC state reservation exceeded");
#define CS (*(ColdState *)COLD_STATE)
__attribute__((used)) const uint32_t cold_layout[] = {
 sizeof(ColdState), offsetof(ColdState,input), offsetof(ColdState,output),
 offsetof(ColdState,gates), offsetof(ColdState,freeze)
};

__attribute__((used,noinline)) void cold_reset(void) {
    volatile uint32_t *p = (volatile uint32_t *)COLD_STATE;
    for (unsigned i = 0; i < sizeof(ColdState) / 4; ++i) p[i] = 0;
}

/* Causal polyphase rational SRC. The two filters operate on the same high-rate
 * grid: 2*host rate = 3*Cold rate. Each contributes 32 host samples group delay.
 * Mirrored rings avoid modulus inside the FIR multiply/accumulate loops.
 */
static Frame filter(const Frame *current, const float *h, unsigned taps) {
    Frame y = {0, 0};
    for (unsigned k = 0; k < taps; ++k) {
        float c = *h++;
        y.l += current->l * c;
        y.r += current->r * c;
        --current;
    }
    return y;
}

__attribute__((used,noinline))
unsigned cold_downsample(const Frame *in, const uint8_t *gates,
                         const uint8_t *freeze, unsigned n) {
    unsigned out = 0;
    for (unsigned i = 0; i < n; ++i) {
        unsigned head = CS.down_head;
        CS.down_history[head] = CS.down_history[head + 65] = in[i];
        CS.down_head = head == 64 ? 0 : head + 1;
        CS.pending_edges |= gates[i] & 6u; /* retain rising/falling edges */
        CS.pending_freeze |= freeze[i] != 0;
        unsigned phase = i % 3;
        if (phase < 2) {
            CS.input[out] = filter(&CS.down_history[head + 65], cold_down_coeff[phase], 65);
            /* A pulse wholly inside a decimation interval must still trigger.
             * The pending event is delayed by at most one host sample.
             */
            CS.gates[out] = CS.pending_edges | (gates[i] & 1u) |
                ((CS.pending_edges & 2u) ? 1u : 0u);
            CS.freeze[out] = CS.pending_freeze;
            CS.pending_edges = CS.pending_freeze = 0;
            ++out;
        }
    }
    return out;
}

__attribute__((used,noinline))
void cold_upsample(const Frame *in, Frame *out, unsigned n) {
    unsigned previous = ~0u, head = 0;
    for (unsigned i = 0; i < n; ++i) {
        unsigned index = (2 * i) / 3;
        if (index != previous) {
            head = CS.up_head;
            CS.up_history[head] = CS.up_history[head + 43] = in[index];
            CS.up_head = head == 42 ? 0 : head + 1;
            previous = index;
        }
        out[i] = filter(&CS.up_history[head + 43], cold_up_coeff[(2*i)%3], 43);
    }
}

__attribute__((used,noinline))
void cold_process(void *processor, unsigned seed, const void *gates,
                  const void *freeze, const void *density, const void *params,
                  const void *mix, const void *input, void *output, unsigned n) {
    typedef void (*ProcessFn)(void *, unsigned, const void *, const void *,
        const void *, const void *, const void *, const void *, void *, unsigned);
    /* The installed callsite always supplies12. Other whole3-frame groups up
     * to12 are supported; reject malformed blocks without overrunning state.
     */
    if (!n || n > 12 || n % 3) {
        if (n <= 12) for (unsigned i = 0; i < n; ++i) ((Frame *)output)[i] = (Frame){0,0};
        return;
    }
    unsigned count = cold_downsample(input, gates, freeze, n);
    ((ProcessFn)0x0804f945u)(processor, seed, CS.gates, CS.freeze, density,
        params, mix, CS.input, CS.output, count);
    cold_upsample(CS.output, output, n);
}
