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
1. preserve the raw dump as container evidence; do not import it as one executable;
2. use the extracted module files;
3. import CPU modules separately as `MIPS:LE:32:default`;
4. establish the image base and shared GP;
5. then run analysis.

The canonical project no longer contains the earlier flat imports of the 1 MiB container.

Current module map is in `reverse/modules.csv`.

Confirmed:
- `ap1.bin` base `0x8067B000`
- `wma.bin` base `0x8073F000`
- `cdrom.bin` base `0x8074C800`
- `drv_other.bin` base `0x80775800`
- coherent MIPS function/call flow after rebase
- shared `$gp = 0x80002B00`

The GP value has instruction-level support from two independent WMA pairs:
- absolute `0x800035D8` matches `gp + 0xAD8`;
- absolute `0x80003684` matches `gp + 0xB84`.

Both equations give `0x80002B00`. Setting this value as the MIPS GP context resolves concrete `0x8000xxxx` globals in all four modules.

Cross-module utility code already identified in `drv_other.bin`:
- `0x80783F08` — byte-wise `memcmp`;
- `0x80783F3C` — byte-wise `memcpy`;
- `0x80783F64` — byte-wise `memset`.

The old provisional `cdrom=0x80754000` and `drv_other=0x80782000` candidates are rejected.

The earlier SCORE7 experiment was useful for rejecting a flat-image interpretation; it is not the active ISA for the primary application modules and is not a dependency of this board project.

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

## Secondary BR23 / AC695N side

The board's secondary package is marked `AK24BP24230`. The UART log proves that running firmware contains AC695N/BR23 soundbox SDK paths and runtime messages, but the exact public SKU is still unresolved.

BR23 / AC695N uses JieLi's `pi32v2` architecture, not MIPS and not SCORE7.

### Public references / pinout

Working public pinout candidate for the secondary LQFP48 device:

- AC6951C datasheet V1.3 mirror: https://opendevices.ru/wp-content/uploads/2021/08/AC6951C-Datasheet-V1.3.pdf
- alternate rendered datasheet: https://manuals.plus/m/f01af517c489b4b9a7162705aa1868219f1b5cd871d130e08f0c0d601858c359

For AC6951C LQFP48:
- pin 23 = `USBDM`
- pin 24 = `USBDP`
- pin 25 = `PA10` (also has `SPDIF_IN_B`)
- pin 26 = `PA9` (also has `SPDIF_IN_A`)

The physical package marking on this board is `AK24BP24230`; the exact mapping of that marking to AC6951C is still unproven. Use pins 23/24 only after continuity/visual package orientation confirms that this board's secondary device matches the AC6951C LQFP48 pinout.

Boot/dump references:

- jl-uboot-tool: https://github.com/kagaimiq/jl-uboot-tool
- enter UBOOT / USB_KEY: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/how-to-enter-uboot.md
- UBOOT model: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/what-is-uboot.md
- JieLi architecture/chip notes: https://github.com/kagaimiq/jielie
- pi32v2 Ghidra processor: https://github.com/kagaimiq/ghidra-jieli

### Read-only dump plan

The next major acquisition task is to preserve this firmware before doing deeper two-chip reverse work.

1. Identify the secondary chip's own USB D+/D- route or accessible test pads. Do not reuse the four-pad SPHE USB footprint by assumption.
2. Confirm the chip enters BR23/AC695N-family Boot ROM / UBOOT, or determine the exact hardware action needed to reach ROM download mode.
3. Use a read-only BR23-capable dumper path. The open-source `jl-uboot-tool` explicitly lists BR23 / AC695N/AC635N as working and can read flash through its RAM loader.
4. Query the online flash/device ID first and derive the real flash size. The runtime log's `disk capacity 1024 KB` is a strong clue, not the dump-size authority.
5. Read the full flash at least twice, compare byte-for-byte and record SHA-256.
6. Only after verified preservation should any write/erase/update experiment be attempted.
7. Store the verified dump in this repository under `firmware/` using the proven chip family/part name.

### Safe first-session sequence

After identifying the secondary controller's own USB D+/D- pair:

1. power the board in the safest known configuration and share ground with the USB host;
2. do not feed an unknown USB VBUS rail into the board until its power topology is mapped;
3. enter BR23 ROM `UBOOT1.00` using the documented `USB_KEY` method or another non-destructive ROM-entry path;
4. start `jluboottool.py` and record the detected BR23/series and flash/device information;
5. determine flash size from the actual flash ID before selecting a dump length;
6. use only the `read <address> <length> <file>` command for the first session;
7. read the whole flash twice and compare the two files byte-for-byte and by SHA-256;
8. do not use `write`, `erase` or `erasechip` until a verified dump and recovery path exist.

The tool's own documentation marks BR23 / AC695N/AC635N as working and documents `read <address> <length> <file>` as the flash-dump command.

### Static-analysis path

After the dump exists:

- use a pi32v2 Ghidra processor implementation such as the open-source `ghidra-jieli` module;
- cross-check instruction decoding against the JieLi toolchain/objdump;
- use available AC695N/BR23 SDK source as a semantic oracle;
- recover board configuration, UART/service behavior, ALINK/I2S/SPDIF use, volume state and the SPHE inter-chip protocol.

### Current runtime anchors


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


## Firmware-control acceptance

Firmware work is not complete merely because both dumps decompile.

We need to prove:
- repeatable extraction/dump;
- repeatable packing or image construction;
- integrity/checksum rules;
- a safe flash/update method;
- rollback/recovery;
- one intentional modification that survives reboot and produces the expected hardware behavior.

Only after that should the project implement new product behavior.
