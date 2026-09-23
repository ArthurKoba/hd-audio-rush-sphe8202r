OUTPUT_ARCH(mips)
ENTRY(_start)

SECTIONS
{
  . = 0x80019000;

  .text : ALIGN(4)
  {
    KEEP(*(.text.entry))
    *(.text .text.*)
  }

  .rodata : ALIGN(4)
  {
    *(.rodata .rodata.*)
  }

  .data : ALIGN(4)
  {
    *(.data .data.*)
  }

  .bss (NOLOAD) : ALIGN(4)
  {
    *(.bss .bss.* COMMON)
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
