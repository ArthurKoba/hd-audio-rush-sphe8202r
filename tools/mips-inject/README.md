# Experimental MIPS compiler / AP1 extension probe

This directory validates the independent compiler path without replacing the
original Sunplus startup/runtime.

Confirmed build ABI used by the probe:
- MIPS32 little-endian;
- o32 ABI;
- soft-float;
- freestanding / no PIC / no ABICALLS;
- `-G0`, avoiding the original small-data `$gp` layout.

The current AP1 image occupies `0x8067B800..0x8072289F`.  The next confirmed
MIPS module, WMA, begins at `0x8073F000`.  Static target references do not
identify executable/data targets in the small extension used by this probe.

The probe therefore:
1. compiles a behavior-preserving implementation of
   `ApplySurroundModeIndex` at `0x80723000`;
2. extends AP1 with zero fill through that address;
3. writes the 44-byte compiled wrapper there;
4. replaces the first 8 bytes of the original action at `0x80702D0C` with
   `j 0x80723000; nop`.

The injected C wrapper still performs exactly
`DispatchAudioHardwareAction(5, index & 0xff, 0)`.  It adds no user-visible
feature.  Its purpose is to validate compiler ABI, module growth and container
repacking before any new audio control is introduced.

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

Static end-to-end validation has already reproduced this route in-memory:
the modified AP1 re-opened exactly after container reconstruction and all other
26 payloads remained byte-identical.  This is **not hardware acceptance** and
the generated image must not be described as boot-tested until a controlled
flash/recovery experiment is performed.
