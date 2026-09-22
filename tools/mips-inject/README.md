# Experimental MIPS compiler / in-place AP1 probe

This directory validates the independent MIPS compiler path without changing
the AP1 size, loader range, startup code or runtime layout.

Confirmed build ABI:
- MIPS32 little-endian;
- o32 ABI;
- soft-float;
- freestanding / no PIC / no ABICALLS;
- `-G0`, avoiding the original small-data `$gp` layout.

The first hardware probe uses the already-understood
`ApplySurroundModeIndex @ 0x80702D0C`.

The stock wrapper is exactly 44 bytes and implements:

`DispatchAudioHardwareAction(5, index & 0xff, 0)`.

The replacement is independently compiled C implementing the same contract.
It is linked directly at `0x80702D0C` and must remain exactly 44 bytes.
`patch_ap1.py` verifies the exact original wrapper bytes before replacing
them, and refuses any patch that changes the AP1 size.

Build and patch:

```sh
./build-surround-probe.sh

python3 patch_ap1.py \
  ../../firmware/modules/ap1.bin \
  build/surround_probe.bin \
  build/ap1.compiler-probe.bin

python3 ../sunplus_container.py repack \
  ../../firmware/P25D80SH@SOP8.BIN \
  -o build/P25D80SH.compiler-probe.bin \
  --replace ap1=build/ap1.compiler-probe.bin
```

This is deliberately behavior-preserving. Its purpose is to validate:
1. the independent compiler/ABI;
2. AP1 module replacement;
3. Sunplus container repacking;
4. actual execution on hardware.

It does **not** depend on the previously tested AP1-extension gap. The
extension path remains useful for later larger features, but is not required
for the first hardware acceptance test.

No generated image is boot-tested until it has actually been flashed under a
proven recovery procedure and the expected audio behavior is observed.
