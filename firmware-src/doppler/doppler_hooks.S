/* Runtime Smooth mode for the published Seal Eggs image.
 * ABI: doppler_mode_address points to one byte:
 *   0 = Stock (entry dispatch is owned by the integrator),
 *   1 = Smooth, 2 = Stepped. Values other than 1 retain published behavior.
 * These hooks execute only after the original finite-rate clamps.
 * They preserve all GPRs, stack balance and every FP register except the
 * original result register. The stepped path replays displaced VCMP so
 * the following original VMRS sees identical FPSCR/APSR flags.
 */
.syntax unified
.cpu cortex-m7
.fpu fpv5-sp-d16
.thumb
.section .text.doppler_hooks,"ax",%progbits
.balign 4
.global doppler_forward_hook
.type doppler_forward_hook,%function
.thumb_func
doppler_forward_hook:
    push {r0, r1}
    ldr r0, =doppler_mode_address
    ldrb r0, [r0]
    cmp r0, #1
    pop {r0, r1}
    beq .Lforward_smooth
    vcmp.f32 s3, s14
    ldr.w pc, =0x0807088b
.Lforward_smooth:
    vmov.f32 s5, s3
    ldr.w pc, =0x0807097f
.size doppler_forward_hook, .-doppler_forward_hook

.balign 4
.global doppler_reverse_hook
.type doppler_reverse_hook,%function
.thumb_func
doppler_reverse_hook:
    push {r0, r1}
    ldr r0, =doppler_mode_address
    ldrb r0, [r0]
    cmp r0, #1
    pop {r0, r1}
    beq .Lreverse_smooth
    vcmp.f32 s22, s11
    ldr.w pc, =0x0807a675
.Lreverse_smooth:
    vmov.f32 s24, s22
    ldr.w pc, =0x0807a68d
.size doppler_reverse_hook, .-doppler_reverse_hook
.ltorg
