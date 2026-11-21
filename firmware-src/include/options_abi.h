#ifndef SEAL_OPTIONS_ABI_H
#define SEAL_OPTIONS_ABI_H
#include <stdint.h>

/* Zeroed at boot by the extended AXI initialization. Persist only preferences. */
#define OPTIONS_BASE 0x24070400u
#define OPTIONS_MAGIC 0x53454f31u
#define DOPPLER_STOCK 0u
#define DOPPLER_SMOOTH 1u
#define DOPPLER_STEPPED 2u
#define DOPPLER_THROW 3u
#define BEADS_DIGITAL 0u
#define BEADS_SUNNY 1u
#define BEADS_COLD 2u
typedef struct {
  uint32_t magic;
  uint8_t doppler;
  uint8_t beads_quality;
  uint8_t character_bits;
  uint8_t tape_pickup;
  uint8_t bbd_light;
  uint8_t tape_bright;
  uint8_t reserved[54];
} SealOptions;
#define SEAL_OPTIONS (*(volatile SealOptions *)OPTIONS_BASE)
#define OPTIONS_UI_STATE 0x24070440u
#define OPTIONS_UI_MAGIC 0x4f505431u
#define OPTIONS_UI_LAYER_OFFSET 18u
#define SUNNY_STATE 0x24070800u
#define DOPPLER_STATE 0x24070a00u
#define NATIVE_OPTIONS_STATE 0x24070b00u
#define COLD_STATE 0x24071000u
#define OPTIONS_RAM_END 0x24072000u

/* Flash reservations, checked by build tool before insertion. */
#define DOPPLER_FLASH 0x08058000u /* 8 KiB */
#define SUNNY_FLASH 0x0805a000u   /* 16 KiB */
#define OPTIONS_FLASH 0x0805e000u /* 16 KiB */
#define NATIVE_FLASH 0x08062000u  /* 16 KiB */
#endif
