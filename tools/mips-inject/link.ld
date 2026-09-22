OUTPUT_ARCH(mips)
ENTRY(sphe_probe_add)

PHDRS
{
  load PT_LOAD FLAGS(5);
}

SECTIONS
{
  . = INJECT_BASE;

  .text : ALIGN(4)
  {
    *(.text .text.*)
  } :load

  .rodata : ALIGN(4)
  {
    *(.rodata .rodata.*)
  } :load

  .data : ALIGN(4)
  {
    *(.data .data.*)
  } :load

  .bss (NOLOAD) : ALIGN(4)
  {
    *(.bss .bss.* COMMON)
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
