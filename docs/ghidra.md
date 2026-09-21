# Ghidra workflow

## Canonical project

Current MCP-side project:
`sphe8202r_decoder_p25d80`

Do not create competing mutable projects for the same stock corpus without documenting why.

## Correct import model

Do **not** auto-analyze the packed 1 MiB flash as one executable.

Workflow:
1. preserve/hash stock dump;
2. unpack with Sunplus STK;
3. classify modules;
4. import CPU modules separately;
5. assign/validate image base;
6. only then run analysis.

## Main application

`ap1.bin`
- language: `MIPS:LE:32:default`
- image base: `0x8067B000`
- analysis produces coherent MIPS functions and call flow.

The beginning contains clean MIPS patterns such as stack adjustment, register stores, conditional branches, `jal`, and `jr ra`.

## SCORE7 note

A custom `SCORE7:LE:32:default` backend has been integrated and acceptance-tested in the Ghidra service. It was useful to test the initial Sunplus hypothesis, but the correctly unpacked primary application modules are MIPS32 LE.

Keep SCORE7 available for any later auxiliary firmware that evidence actually identifies as SCORE7. Do not apply it to `ap1/cdrom/drv_other/wma` merely because Sunplus also used S+CORE/SCORE products.

## Next Ghidra tasks

- validate GP/base relationships across `ap1`;
- define string/data regions so firmware anchors receive xrefs;
- resolve module-to-module calls;
- confirm provisional module bases;
- identify USB host stack;
- identify S/PDIF mode/config handlers;
- locate AC3/DTS routing and volume/mute path;
- locate board init, GPIO, UART and inter-chip control paths;
- document each renamed function with evidence and confidence.
