OUTPUT_ARCH(mips)
ENTRY(_start)

SECTIONS
{
  . = 0x80019000;

  .text : SUBALIGN(4)
  {
    KEEP(*(.text.start))
    *(.text .text.*)
    *(.rodata .rodata.*)
  }

  /DISCARD/ :
  {
    *(.comment)
    *(.note*)
    *(.MIPS.abiflags)
    *(.reginfo)
    *(.got)
    *(.got.plt)
  }
}
