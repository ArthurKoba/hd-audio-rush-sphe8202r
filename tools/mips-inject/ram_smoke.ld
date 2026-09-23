OUTPUT_ARCH(mips)
ENTRY(_start)

SECTIONS
{
  . = 0x80019000;

  .text : ALIGN(4)
  {
    *(.text.startup .text.startup.*)
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

  . = ALIGN(4);

  /DISCARD/ :
  {
    *(.comment)
    *(.note*)
    *(.MIPS.abiflags)
    *(.reginfo)
    *(.got)
    *(.got.plt)
    *(.pdr)
    *(.mdebug*)
  }
}
