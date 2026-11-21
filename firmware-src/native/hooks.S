.syntax unified
.cpu cortex-m7
.fpu fpv5-sp-d16
.thumb

.section .text.hooks,"ax",%progbits
.align 2
.global tape_audio_hook
.thumb_func
tape_audio_hook:
  push {r0-r3,r12,lr}
  vpush {d0-d7}
  bl native_tape_update
  vpop {d0-d7}
  pop {r0-r3,r12,lr}
  ldr.w pc, =0x08070047

.global bbd_control_hook
.thumb_func
bbd_control_hook:
  push {r0-r3,r12,lr}
  vpush {d0-d7}
  bl native_bbd_update
  vpop {d0-d7}
  pop {r0-r3,r12,lr}
  ldr.w pc, =0x0801136d

/* Literal substitutions do not change the original instruction's registers
 * or APSR flags. Scratch registers and stack are restored before resuming. */
.macro PICKUP name, destination, table, resume
.global \name
.thumb_func
\name:
  push {r0,r1}
  mrs r0, APSR
  push {r0}
  ldr r0, =0x24070407
  ldrb r1, [r0]
  and.w r1, r1, #1
  ldr r0, =\table
  add.w r0, r0, r1, lsl #2
  vldr \destination, [r0]
  pop {r0}
  msr APSR_nzcvq, r0
  pop {r0,r1}
  ldr.w pc, =\resume+1
.endm

PICKUP pickup_left_slow, s7, pickup_slow, 0x08018e46
PICKUP pickup_left_fast, s8, pickup_fast, 0x08018e4a
PICKUP pickup_right_a, s17, pickup_slow, 0x08019ff4
PICKUP pickup_right_b, s18, pickup_fast, 0x0801a004
PICKUP pickup_right_c, s12, pickup_slow, 0x0801a18a
PICKUP pickup_right_d, s0, pickup_fast, 0x0801a196

.macro BBD name, destination, address, resume
.global \name
.thumb_func
\name:
  push {r0}
  ldr r0, =\address
  vldr \destination, [r0]
  pop {r0}
  ldr.w pc, =\resume+1
.endm

BBD bbd_threshold_left, s0, 0x24070b08, 0x080113d6
BBD bbd_threshold_right, s3, 0x24070b08, 0x080115b4
BBD bbd_cap_left_a, s5, 0x24070b0c, 0x080114fc
BBD bbd_cap_right_a, s16, 0x24070b0c, 0x08011660
BBD bbd_cap_left_b, s17, 0x24070b0c, 0x0801188a
BBD bbd_cap_right_b, s16, 0x24070b0c, 0x08011896

.align 2
pickup_slow: .float 0.0015, 0.0075
pickup_fast: .float 0.015, 0.075
.ltorg
