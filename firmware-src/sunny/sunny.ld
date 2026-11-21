ENTRY(sunny_configure)
SECTIONS {
 . = 0x0805a000;
 .text : { *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) *(.ARM.extab*) }
}
