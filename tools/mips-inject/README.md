# Experimental MIPS compiler/ABI probe

This directory validates the independent compiler path against one
already-understood AP1 action. It does **not** establish hardware acceptance.

The current probe replaces `ApplySurroundModeIndex @ 0x80702D0C`. The stock
wrapper is 44 bytes and implements:

`DispatchAudioHardwareAction(5, index & 0xff, 0)`.

The replacement is independently compiled from C using:
- MIPS32 little-endian;
- o32 ABI;
- soft-float;
- freestanding / no PIC / no ABICALLS;
- `-G0`, avoiding dependence on the original small-data `$gp` layout.

The linker binds `DispatchAudioHardwareAction = 0x806FFD1C`, so the generated
function uses a direct MIPS `jal` rather than an indirect absolute-call
sequence. The compiled function is 36 bytes. The build script appends the two
stock epilogue instructions as unreachable 8-byte padding, preserving the exact
44-byte wrapper window.

With zlib 1.3.1 using the recovered vendor parameters (raw DEFLATE, level 9,
`windowBits=-15`, `memLevel=8`, `Z_FIXED`), the patched AP1 compresses to
`0x54078` bytes versus the stock AP1 packed slot size `0x5407A`. Therefore
the first probe can keep every module offset and the decoded container extent
unchanged; the two remaining packed-slot bytes can be preserved from stock.

Run:

```sh
./build-surround-probe.sh
python3 patch_ap1.py ../../firmware/modules/ap1.bin \
  build/surround_probe.bin build/ap1.compiler-probe.bin
```

The patcher verifies the exact original 44 bytes and keeps AP1 at `0xA70A0`
bytes. The resulting AP1 still has to pass full Sunplus container repack/reopen
validation before hardware use.
