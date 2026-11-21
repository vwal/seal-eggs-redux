.syntax unified
.cpu cortex-m7
.thumb
.fpu fpv5-d16
.section .text.hooks,"ax",%progbits
.macro FUNC name
.global \name
.type \name,%function
.thumb_func
\name:
.endm
FUNC options_character_hook
 push {r0-r3,r12,lr}
 bl options_character_toggle
 pop {r0-r3,r12,lr}
 ldr pc,=0x080732a3
FUNC options_write_hook
 push {r0-r3,r12,lr}
 bl options_record_write
 pop {r0-r3,r12,lr}
 ldr pc,=0x08076047
FUNC options_load_hook
 push {r0-r3,r12,lr}
 bl options_load
 pop {r0-r3,r12,lr}
 ldr pc,=0x08076061
/* Displaces CMP/BNE at0801dca6. Keep0801dcac intact: failures jump there. */
FUNC options_save_done_hook
 cmp r0,#0
 bne 1f
 push {r0-r3,r12,lr}
 bl options_save_complete
 pop {r0-r3,r12,lr}
 ldr pc,=0x0801dcab
1:
 ldr pc,=0x0801dd4b
.macro LED name,id,literal,resume
 FUNC \name
 push {r0-r3,r12,lr}
 movs r1,#\id
 bl options_led
 str r0,[sp]
 pop {r0-r3,r12,lr}
 sub sp,#8
 ldr r3,=\literal
 vldr s14,[r3]
 ldr pc,=(\resume + 1)
.endm
LED options_led_freeze,0,0x0800c170,0x0800bf8e
LED options_led_tap,1,0x0800c35c,0x0800c182
LED options_led_delay,2,0x0800c54c,0x0800c36e
LED options_led_mod,3,0x0800c740,0x0800c55e
FUNC options_led_tap_secondary
 push {r0-r3,r12,lr}
 mov r0,r1
 movs r1,#1
 bl options_led
 str r0,[sp,#4]
 pop {r0-r3,r12,lr}
 push {r4,r5,lr}
 sub sp,#28
 str r1,[sp,#4]
 ldr pc,=0x0800ceb7
/* Displaced LDR/CMP, after native pulse bookkeeping but before PWM selection. */
FUNC options_led_tap_pulse
 push {r0-r3,r12,lr}
 ldr r0,[r4,#36]
 bl options_tap_pulse
 mov r4,r0
 pop {r0-r3,r12,lr}
 cmp r4,#0
 ldr pc,=0x0800cec3
