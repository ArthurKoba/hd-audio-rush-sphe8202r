# Firmware

## Raw SPI dump

`firmware/P25D80SH@SOP8.BIN` is a **raw byte-for-byte dump** of the Puya P25D80SH SPI NOR from the target board.

- size: 1,048,576 bytes
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`

It is a Sunplus firmware container, not one flat CPU executable.

## Sunplus STK

Tool archive: `tools/STK_0.2.3.zip`

The rev-8203R build successfully opens the dump and extracts the firmware modules.

Observed metadata:
- version: `02R-D-02`
- ROM required: `1M`
- customer ID: `SUNPLUS`
- displayed SoC profile: `SPHE8203R`
- SDRAM: `32M`
- SDRAM bus: 16-bit, non-shared
- Host USB 2.0: supported
- module slots: 18
- password: `5168`

The displayed `SPHE8203R` conflicts with the physical `SPHE8202R` package marking. Keep this contradiction open.

## Extracted modules

The already-extracted files are stored directly in `firmware/modules/`; there is intentionally no duplicate tar archive.

CPU/code classification:
- `ap1.bin` — main MIPS32 LE application
- `drv_other.bin` — MIPS32 LE driver/auxiliary code
- `cdrom.bin` — MIPS32 LE module
- `wma.bin` — MIPS32 LE WMA-related module
- `rom12.bin` — container/config/resource-like, not a linear MIPS image
- `jpeg.bin` — data/tables
- `iop.bin`, `iop_rst.bin`, `srvdsp.bin` — auxiliary microcode/specialized image candidates

Zero-length module slots are retained because STK produced an 18-slot set.

Exact sizes and SHA-256 values are kept once, in the root `README.md`.

## Ghidra

Canonical MCP-side project used during initial analysis: `sphe8202r_decoder_p25d80`.

Correct workflow:
1. preserve the raw dump;
2. use the extracted module files;
3. import CPU modules separately as `MIPS:LE:32:default`;
4. establish image base / GP assumptions;
5. then run analysis.

Current module map is in `reverse/modules.csv`.

Confirmed:
- `ap1.bin` base `0x8067B000`
- coherent MIPS function/call flow after rebase

Provisional:
- `wma.bin` ~`0x8073F000`
- `cdrom.bin` ~`0x80754000`
- `drv_other.bin` ~`0x80782000`

The earlier SCORE7 experiment was useful for rejecting a flat-image interpretation; it is not the active ISA for the primary application modules.

## Firmware anchors

`ap1.bin` contains strings for:
- `SPDIF/OFF`
- `SPDIF/RAW`
- `SPDIF/PCM`
- `SPDIF IN`
- `AUDIO OUT`
- `AUDIO SETUP`
- AC3
- DTS
- PCM
- USB / SD status

These are static firmware anchors, not PCB-routing proof.

## Secondary controller evidence

`evidence/ac695n-boot-excerpt.log` is a curated excerpt from the UART output of the secondary-controller side.

It contains:
- `AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS`
- BR23 / `board_ac695x_demo`
- `jl_soundbox_lihui`
- `audio_enc_init`
- `audio_dec_init`
- `audio_dac_init`
- `ALINK_SR = 44100`
- `spdif_dec_start`
- max/default volume configuration and `VOL_SAVE`

This strongly ties the secondary side to JieLi AC695N/BR23 software, but the exact public SKU behind `AK24BP24230`, its internal-flash dump path and the inter-chip protocol remain open.
