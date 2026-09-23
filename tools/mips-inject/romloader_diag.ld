OUTPUT_ARCH(mips)
ENTRY(romloader_diag_main)

PHDRS
{
  load PT_LOAD FLAGS(5);
}

SECTIONS
{
  . = 0x80019000;

  .text : ALIGN(4)
  {
    *(.text .text.*)
  } :load

  .rodata : ALIGN(4)
  {
    *(.rodata .rodata.*)
  } :load

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
