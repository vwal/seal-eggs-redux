ENTRY(tape_audio_hook)
SECTIONS {
 . = 0x08062000;
 .text : { *(.text.hooks) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
ASSERT(SIZEOF(.text) <= 0x4000, "native options flash reservation exceeded")
