.syntax unified
.cpu cortex-m7
.thumb
.fpu fpv5-d16
.section .text.hooks,"ax",%progbits
.global diagnostics_meter_hook
.type diagnostics_meter_hook,%function
.thumb_func
diagnostics_meter_hook:
 push {r0-r3,r12,lr}
 bl diagnostics_native_meter
 bl diagnostics_collect
 pop {r0-r3,r12,lr}
 bx lr
/* Exact displaced prologue; body and original meter RAM remain unchanged. */
.type diagnostics_native_meter,%function
.thumb_func
diagnostics_native_meter:
 push {r4,r5,r6}
 ldr r12,=0xe0001000
 ldr pc,=0x08076207
