.syntax unified
.cpu cortex-m7
.thumb
.fpu fpv5-d16
.section .text.throw_hooks,"ax",%progbits
/* Save every live register and both status registers. Total192 bytes,
   preserving the native8-byte stack alignment at both C calls. */
.macro SAVE_ALL
 push {r0-r12,lr}
 vpush {d0-d15}
 mrs r2,APSR
 vmrs r3,FPSCR
 push {r2,r3}
.endm
.macro RESTORE_ALL
 pop {r2,r3}
 msr APSR_nzcvqg,r2
 vmsr FPSCR,r3
 vpop {d0-d15}
 pop {r0-r12,lr}
.endm
.global throw_time_hook
.type throw_time_hook,%function
.thumb_func
throw_time_hook:
 /* Original call still runs with original r0=0; save its final register
    effects, then change only S0. The caller's original return address lives
    outside the preservation frame. */
 push {r12,lr}
 ldr r12,=0x0800a4c1
 blx r12
 SAVE_ALL
 bl throw_control_time
 vstr s0,[sp,#8]
 RESTORE_ALL
 pop {r12,lr}
 bx lr
.global throw_late_hook
.type throw_late_hook,%function
.thumb_func
throw_late_hook:
 SAVE_ALL
 mov r0,r5
 mov r1,r11
 bl throw_control_late
 RESTORE_ALL
 ldr.w r6,[r5,#0x208]
 ldr pc,=0x0801b6ed
