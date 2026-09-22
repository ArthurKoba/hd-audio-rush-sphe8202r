# Experimental MIPS injection harness

This directory is a build probe for the SPHE8202R firmware. It does **not**
patch or flash firmware.

Current candidate ABI:
- MIPS32 little-endian;
- o32 ABI;
- freestanding / no PIC / no ABICALLS;
- soft-float;
- `-G0` so new code does not depend on the original small-data `$gp` layout.

Default candidate injection base is `0x80723000`. Static analysis shows the
current AP1 image ending near `0x807228A0` and the next confirmed MIPS image
(WMA) beginning at `0x8073F000`. This does **not** yet prove that the entire
gap is runtime-safe; hardware use requires additional loader/layout validation.

Build:

```sh
./build.sh
```

Override the candidate base with `BASE=0x... ./build.sh`.

The current `probe.c` is intentionally side-effect free. It exists only to
validate the compiler/linker/raw-binary path before any firmware redirection is
attempted.
