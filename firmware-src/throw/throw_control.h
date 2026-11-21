#ifndef SEAL_THROW_CONTROL_H
#define SEAL_THROW_CONTROL_H
#include <stdint.h>
#define THROW_CONTROL_STATE 0x24070e00u
#define THROW_CONTROL_MAGIC 0x54485235u
/* Audio callback context only. TIME is calibrated physical position before CV. */
float throw_control_time(float physical);
void throw_control_late(void *owner, void *output);
#endif
