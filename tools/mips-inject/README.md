# Experimental MIPS compiler/ABI probe

This directory validates the independent compiler path against one
already-understood AP1 action. It does **not** flash firmware.

The current probe replaces `ApplySurroundModeIndex @ 0x80702D0C`. The
original wrapper is 44 bytes and implements:

`DispatchAudioHardwareAction(5, index & 0xff, 0)`.

`surround_probe.c` independently compiles the same external contract using:
- MIPS32 little-endian;
- o32 ABI;
- soft-float;
- freestanding / no PIC / no ABICALLS;
- `-G0`, avoiding dependence on the original small-data `$gp` layout.

Run:

```sh
./build.sh
python3 patch_ap1.py ../../firmware/modules/ap1.bin \
  build/surround_probe.bin build/ap1.compiler-probe.bin
```

The patcher checks the exact original 44 bytes before modifying anything and
keeps AP1 size unchanged. This is deliberately a behavior-preserving compiler
probe, not a feature patch.

The modified AP1 must still pass the separate Sunplus container no-change /
repack validation before any hardware use.
