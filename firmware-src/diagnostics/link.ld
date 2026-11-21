ENTRY(diagnostics_meter_hook)
SECTIONS {
 . = 0x08066000;
 .text : { *(.text*) *(.rodata*) }
 .ARM.exidx : { *(.ARM.exidx*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.eh_frame*) }
 ASSERT(. <= 0x08068000, "diagnostics exceeds reservation")
}
