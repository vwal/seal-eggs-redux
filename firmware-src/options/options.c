#include <stdint.h>
#include <stddef.h>
#include "../include/options_abi.h"
#include "../diagnostics/diagnostics_abi.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define NATIVE_CHARACTER 0x24030500u
#define SAVE_PENDING 0x24030590u
#define BUTTONS 0x200043dcu
#define SAMPLE_PENDING 0x20004580u
#define SAMPLE_MASK 0x20004584u
#define UI_MAGIC 0x4f505431u
#define LAYER_ENTRY 1u
#define LAYER_READY 2u
#define LAYER_DRAIN 3u
#define COL_OFF 0x01000000u
#define COL_BLUE 0x00400000u
#define COL_AMBER 0x000060b0u
#define COL_CYAN 0x00909000u
#define COL_GREEN 0x00008000u
#define COL_MAGENTA 0x00900090u

typedef struct {
  uint32_t magic;
  uint32_t ticks;
  uint16_t committed_flags;
  uint16_t entry_flags;
  uint16_t desired_save_flags;
  uint16_t ack_remaining;
  uint16_t press_ticks;
  uint8_t layer;
  uint8_t edit_model;
  uint8_t startup_released;
  uint8_t entry_allowed;
  uint8_t previous_mod;
  uint8_t histories[4];
  uint8_t debounced;
  uint8_t press_mask;
  uint8_t press_invalid;
  uint8_t save_waiting;
  uint8_t last_model;
  uint8_t reserved[3];
} OptionsUi;
#define UI (*(volatile OptionsUi *)OPTIONS_UI_STATE)
_Static_assert(sizeof(OptionsUi) <= 0x3c0, "options UI allocation exceeded");
_Static_assert(offsetof(OptionsUi,layer)==OPTIONS_UI_LAYER_OFFSET, "options layer ABI changed");

static uint32_t irq_lock(void) { uint32_t p; __asm volatile("mrs %0, primask\ncpsid i":"=r"(p)::"memory"); return p; }
static void irq_restore(uint32_t p) { __asm volatile("msr primask, %0"::"r"(p):"memory"); }
static uint32_t model(void) { uint32_t m=U32(0x24000200u); return m<3?m:0; }
static uint16_t pack(void) {
  return (uint16_t)(SEAL_OPTIONS.doppler | (SEAL_OPTIONS.beads_quality<<2)
    | ((SEAL_OPTIONS.character_bits&7u)<<4) | ((SEAL_OPTIONS.tape_bright&1u)<<7)
    | ((SEAL_OPTIONS.bbd_light&1u)<<8) | ((SEAL_OPTIONS.tape_pickup&1u)<<9));
}
static void unpack(uint16_t f) {
  SEAL_OPTIONS.doppler=f&3u; SEAL_OPTIONS.beads_quality=(f>>2)&3u;
  SEAL_OPTIONS.character_bits=(f>>4)&7u; SEAL_OPTIONS.tape_bright=(f>>7)&1u;
  SEAL_OPTIONS.bbd_light=(f>>8)&1u; SEAL_OPTIONS.tape_pickup=(f>>9)&1u;
}
static void ensure(void) {
  if (SEAL_OPTIONS.magic!=OPTIONS_MAGIC) { unpack(0); SEAL_OPTIONS.magic=OPTIONS_MAGIC; }
  if (UI.magic!=UI_MAGIC) {
    volatile uint8_t *p=(volatile uint8_t *)OPTIONS_UI_STATE;
    for(unsigned i=0;i<sizeof(OptionsUi);++i)p[i]=0;
    UI.committed_flags=pack(); UI.last_model=(uint8_t)model(); UI.magic=UI_MAGIC;
  }
}
void options_sync_character(uint32_t m) {
  if (m>2)m=0;
  U32(NATIVE_CHARACTER)=SEAL_OPTIONS.magic==OPTIONS_MAGIC ? ((SEAL_OPTIONS.character_bits>>m)&1u):0;
}
static void commit(void) {
  uint16_t f=pack();
  if(f==UI.committed_flags)return;
  UI.committed_flags=f; UI.desired_save_flags=f; UI.save_waiting=1;
  U8(SAVE_PENDING)=1;
}
/* Called only at the existing character long-hold success site. */
void options_character_toggle(void) {
  ensure();
  SEAL_OPTIONS.character_bits^=(uint8_t)(1u<<model());
  options_sync_character(model());
  commit();
}
/* Called after stock settings checksum validation, before native deserialization. */
void options_load(void) {
  uint16_t f=0;
  uint32_t r=U32(0x20005fc8u);
  if((r&0xffffu)==0x01a7u) {
    uint16_t candidate=(uint16_t)(r>>16);
    if(!(candidate&~0x3ffu) && ((candidate>>2)&3u)<=BEADS_COLD) {
      f=candidate;
    }
  } else if((r&0xffu)==0x5au) {
    if(r&0x100u)f=7u<<4; /* Existing global character choice becomes three identical choices. */
  }
  unpack(f); SEAL_OPTIONS.magic=OPTIONS_MAGIC; ensure();
  UI.committed_flags=f; UI.save_waiting=0; UI.layer=0;
  options_sync_character(model());
}
/* Existing write path computes stock checksum immediately after this insertion. */
void options_record_write(void) {
  ensure();
  U32(0x200057d0u)=0x01a7u | ((uint32_t)UI.committed_flags<<16);
}
/* Reached only after the original header and full settings writes both return success. */
void options_save_complete(void) {
  if(UI.magic==UI_MAGIC && UI.save_waiting &&
     U32(0x200057d0u)==(0x01a7u|((uint32_t)UI.desired_save_flags<<16))) {
    UI.save_waiting=0; UI.ack_remaining=200;
  }
}
static void reset_native_buttons(void) {
  for(unsigned i=0;i<4;++i) {
    uintptr_t b=BUTTONS+0x68u*i;
    U8(b)=0;U8(b+1)=0;U32(b+4)=0;U8(b+8)=0;U8(b+9)=0;U8(b+10)=0;
    U8(b+100)=0;U8(b+101)=0;
  }
  U8(0x200043b9u)=0;
  U32(0x2403017cu)=0;U32(0x24030504u)=0;
  /* No ALT was active on entry. Leave audio freeze/reverse/sync flags untouched. */
}
static uint8_t read_buttons(void) {
  uint8_t m=0;
  for(unsigned i=0;i<4;++i)if(U8(BUTTONS+0x68u*i))m|=(uint8_t)(1u<<i);
  return m;
}
static void close_layer(void) {
  commit();UI.layer=LAYER_DRAIN;UI.press_mask=0;UI.press_invalid=1;
}
static void action(uint8_t button) {
  uint8_t m=UI.edit_model;
  if(button==1)SEAL_OPTIONS.character_bits^=(uint8_t)(1u<<m);
  else if(button==2) {
    if(m==0)SEAL_OPTIONS.tape_bright^=1;
    else if(m==1)SEAL_OPTIONS.bbd_light^=1;
    else {
      /* Preserve the persisted codes: Digital0, Sunny1, Cold2. */
      uint8_t q=SEAL_OPTIONS.beads_quality;
      SEAL_OPTIONS.beads_quality=q==BEADS_DIGITAL?BEADS_COLD:q==BEADS_COLD?BEADS_SUNNY:BEADS_DIGITAL;
    }
  } else if(button==4) {
    if(m==0)SEAL_OPTIONS.tape_pickup^=1;
    else if(m==2)SEAL_OPTIONS.doppler=(uint8_t)((SEAL_OPTIONS.doppler+1u)%4u);
  } else if(button==8)close_layer();
  options_sync_character(model());
}
static uint8_t debounce(uint8_t raw) {
  uint8_t stable=UI.debounced;
  for(unsigned i=0;i<4;++i) {
    uint8_t h=(uint8_t)((UI.histories[i]<<1)|((raw>>i)&1u));
    UI.histories[i]=h;
    if((h&0x7fu)==0x7fu)stable|=(uint8_t)(1u<<i);
    else if(!(h&0x7fu))stable&=(uint8_t)~(1u<<i);
  }
  UI.debounced=stable;return stable;
}
static void layer_sample(uint8_t raw) {
  uint8_t now=debounce(raw);
  if(UI.layer==LAYER_ENTRY || UI.layer==LAYER_DRAIN) {
    if(now==0 && raw==0) {
      if(UI.layer==LAYER_ENTRY)UI.layer=LAYER_READY;
      else {reset_native_buttons();UI.layer=0;UI.previous_mod=0;UI.entry_allowed=0;}
      UI.press_mask=0;UI.press_invalid=0;UI.press_ticks=0;
    }
    return;
  }
  if(UI.layer!=LAYER_READY)return;
  if(now) {
    if(!UI.press_mask) {UI.press_mask=now;UI.press_ticks=0;UI.press_invalid=(now&(now-1u))!=0;}
    else if(now!=UI.press_mask)UI.press_invalid=1;
    if(UI.press_ticks<65535)++UI.press_ticks;
    /* A second physical contact cancels even before its debounce completes. */
    if(raw&~UI.press_mask)UI.press_invalid=1;
    /* Exit is safe on a standalone MOD hold as well as a short release.
       At 500 samples enter DRAIN immediately; continued holding/release cannot
       toggle native sync, re-enter options, or save the same edit twice. */
    if(UI.press_ticks>=500) {
      if(UI.press_mask==8u) {
        if(!UI.press_invalid && raw==8u)close_layer();
      } else UI.press_invalid=1;
    }
  } else if(UI.press_mask) {
    uint8_t pressed=UI.press_mask;
    uint8_t valid=!UI.press_invalid;
    UI.press_mask=0;UI.press_ticks=0;UI.press_invalid=0;
    if(valid)action(pressed);
  }
}
/* Replace dispatcher entry. Native path and callbacks remain intact outside options. */
uint32_t options_dispatch(void) {
  ensure();
  uint32_t m=model();
  options_sync_character(m);
  if(UI.layer && m!=UI.edit_model && UI.layer!=LAYER_DRAIN)close_layer();
  if(UI.layer) {
    uint32_t p=irq_lock();
    uint8_t pending=U8(SAMPLE_PENDING);
    uint8_t raw=(uint8_t)U32(SAMPLE_MASK)&15u;
    if(pending)U8(SAMPLE_PENDING)=0;
    irq_restore(p);
    if(pending){++UI.ticks;if(UI.ack_remaining)--UI.ack_remaining;layer_sample(raw);}
    return pending?1u:0u;
  }
  uint8_t raw=(uint8_t)U32(SAMPLE_MASK)&15u;
  uint32_t processed=((uint32_t(*)(void))0x080731bdu)();
  options_sync_character(m);
  if(processed) {
    ++UI.ticks;if(UI.ack_remaining)--UI.ack_remaining;
    uint8_t buttons=read_buttons();
    if(raw==0 && buttons==0)UI.startup_released=1;
    if(!(buttons&8u)){UI.previous_mod=0;UI.entry_allowed=0;}
    else {
      if(!UI.previous_mod){UI.previous_mod=1;UI.entry_allowed=UI.startup_released;}
      if(buttons!=8u || raw!=8u || U32(0x20004874u)!=0 || U32(0x20004db0u)!=0)UI.entry_allowed=0;
      if(UI.entry_allowed && U32(0x20004518u)>=1000u) {
        UI.layer=LAYER_ENTRY;UI.edit_model=(uint8_t)m;UI.entry_flags=pack();
        UI.press_mask=0;UI.press_invalid=1;UI.press_ticks=0;
        UI.debounced=8;for(unsigned i=0;i<4;++i)UI.histories[i]=(i==3)?255:0;
        uint32_t p=irq_lock();reset_native_buttons();irq_restore(p);
      }
    }
  }
  UI.last_model=(uint8_t)m;
  return processed;
}
static uint32_t scale_rgb(uint32_t rgb,uint32_t level) {
  uint32_t r=((rgb&255u)*level)>>8;
  uint32_t g=(((rgb>>8)&255u)*level)>>8;
  uint32_t b=(((rgb>>16)&255u)*level)>>8;
  return r|(g<<8)|(b<<16);
}
uint32_t options_led(uint32_t original,uint32_t id) {
  if(UI.magic==UI_MAGIC) {
    if(UI.layer==LAYER_ENTRY || UI.layer==LAYER_READY) {
      unsigned m=UI.edit_model;
      if(id==0)return ((SEAL_OPTIONS.character_bits>>m)&1u)?COL_AMBER:COL_BLUE;
      if(id==1) {
        unsigned enabled=m==0?SEAL_OPTIONS.tape_bright:m==1?SEAL_OPTIONS.bbd_light:SEAL_OPTIONS.beads_quality;
        uint32_t c=(m==2 && enabled==BEADS_COLD)?COL_GREEN:enabled?COL_AMBER:COL_BLUE;
        /* Desired Beads quality applies on next entry. Active-quality ABI supplied by Sunny component. */
        if(m==2 && U32(0x24070004u)==3 && U32(0x240700e0u)!=1 &&
           U8(SUNNY_STATE+1u)==1 && U8(SUNNY_STATE)!=SEAL_OPTIONS.beads_quality && ((UI.ticks/250u)&1u))return COL_OFF;
        return c;
      }
      if(id==2) {
        if(m==1)return COL_OFF;
        if(m==0)return SEAL_OPTIONS.tape_pickup?COL_AMBER:COL_BLUE;
        return SEAL_OPTIONS.doppler==DOPPLER_THROW?COL_MAGENTA:
          SEAL_OPTIONS.doppler==0?COL_BLUE:SEAL_OPTIONS.doppler==1?COL_CYAN:COL_AMBER;
      }
      uint32_t t=UI.ticks%2000u;
      uint32_t triangle=t<1000?t:2000u-t;
      uint32_t strength=48u+triangle*100u/1000u;
      uint32_t c=0x00ffffffu;
      if(U32(0x24070004u)!=0 && t>=1000u)c=U32(0x240700e0u)==1?0x000080ffu:0x00d6ff00u;
      return scale_rgb(c,strength);
    }
    if(id==3 && UI.ack_remaining)return 0x0000b000u;
  }
  uint32_t diagnostic=diagnostics_led_color(id);
  if(diagnostic)return diagnostic;
  uint32_t override=U32(0x24070100u+4u*id);
  return override?override:original;
}

/* The secondary TAP renderer normally gives a clock pulse priority over RGB.
   Mask only that local colour decision while options owns the LED. The native
   clock countdown and queued pulse state have already advanced and stay intact. */
uint32_t options_tap_pulse(uint32_t pulse) {
  return UI.magic==UI_MAGIC &&
    (UI.layer==LAYER_ENTRY || UI.layer==LAYER_READY) ? 0u : pulse;
}
