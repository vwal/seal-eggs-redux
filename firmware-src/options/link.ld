ENTRY(options_dispatch)
SECTIONS {
 . = 0x0805e000;
 .text : { *(.text*) *(.rodata*) }
 .ARM.exidx : { *(.ARM.exidx*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.eh_frame*) }
 ASSERT(. <= 0x08062000, "options exceeds reservation")
}
