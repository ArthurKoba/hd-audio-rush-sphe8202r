OUTPUT_ARCH(mips)
ENTRY(injected_apply_surround)

DispatchAudioHardwareAction = 0x806FFD1C;

SECTIONS
{
  . = 0x80702D0C;

  .text : SUBALIGN(4)
  {
    *(.text .text.*)
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
