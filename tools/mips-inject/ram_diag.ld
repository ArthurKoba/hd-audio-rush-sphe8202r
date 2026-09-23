OUTPUT_ARCH(mips)
ENTRY(_start)

SECTIONS
{
  . = 0x80019000;

  .text : SUBALIGN(4)
  {
    *(.text.start)
    *(.text .text.*)
  }

  .rodata : SUBALIGN(4)
  {
    *(.rodata .rodata.*)
  }

  .data : SUBALIGN(4)
  {
    *(.data .data.*)
  }

  .bss (NOLOAD) : SUBALIGN(4)
  {
    *(.bss .bss.*)
    *(COMMON)
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
