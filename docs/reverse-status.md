# Reverse status

## Project direction

Target state: **control-complete reverse engineering of the entire board**.

Current work is incomplete because only the Sunplus external flash is preserved. The highest-value missing artifact is the secondary BR23/AC695N-side firmware dump.


## Confirmed

- Product family: HD Audio Rush 5.1.
- PCB: `SPHE8202RD_SPDIF_V02`.
- Main package: Sunplus `SPHE8202R`.
- Raw external flash: Puya `P25D80SH`, 1 MiB dump preserved at `firmware/P25D80SH@SOP8.BIN`.
- STK rev-8203R opens the dump and extracts 18 module slots.
- Main application modules `ap1`, `cdrom`, `drv_other`, `wma` are coherent MIPS32 little-endian.
- `ap1.bin` base `0x8067B000` is confirmed by internal absolute references.
- `wma.bin` base `0x8073F000` is confirmed; `ap1` directly calls the exact entry at `0x8073F000`.
- `cdrom.bin` base `0x8074C800` is confirmed by direct `ap1` call targets mapping to coherent code/function starts throughout the module.
- `drv_other.bin` base `0x80775800` is confirmed by direct `ap1`/`wma` call targets mapping to coherent shared helper code throughout the module.
- Shared MIPS GP is `0x80002B00`. Two independent `wma` instruction pairs give `0x800035D8 - 0xAD8` and `0x80003684 - 0xB84`, both exactly `0x80002B00`; applying this GP resolves concrete globals across all four MIPS modules.
- Cross-module utility code in `drv_other.bin` includes confirmed byte-wise `memcmp` at `0x80783F08`, `memcpy` at `0x80783F3C` and `memset` at `0x80783F64`.
- Secondary-side UART excerpt contains AC695N/BR23 build/runtime strings.
- HCF4052-family device function is analog multiplexing; 74HC04D is a hex inverter; 4558-family devices are dual op-amps.

## Likely / provisional

- Secondary `AK24BP24230` is a JieLi/JL-family controller executing the observed AC695N/BR23 firmware.
- 4558D devices near the six-channel outputs participate in analog buffering/filtering/preamplification.
- External SDRAM marking is close to the reported `PMS3064 / 16BTR-60N`, but exact transcription is not yet reliable.

## Unknown

- Exact SDRAM part, vendor and density; STK's `32M` unit is not resolved.
- Exact public SKU behind `AK24BP24230`.
- Exact secondary flash ID/size and physical USB boot/download route.
- Exact SPHE <-> secondary-controller control/audio transport.
- Exact TOSLINK/coax -> decode -> six-channel analog signal path.
- Exact role of HCF4052 and 74HC04D on this PCB.
- Exact USB pad pinout and whether device/UAC mode is feasible.
- Safe recovery/flash path for the secondary controller.
- Reproducible Sunplus repack/update path.

## Contradictions

### Physical SPHE8202R vs STK SPHE8203R

Physical package marking is `SPHE8202R`; STK displays `SPHE8203R`. Do not resolve this by assumption.

### SCORE7 vs MIPS

Correct STK extraction shows the main application modules are MIPS32 LE. SCORE7 is not the current assumption for `ap1/cdrom/drv_other/wma`.

## Tooling decision

- **Ghidra: required.**
- **SCORE7 processor: not required for this board on current evidence.**
- Sunplus application reverse uses Ghidra MIPS32 LE support.
- The canonical Ghidra project contains extracted modules as programs; flat imports of the 1 MiB Sunplus container have been removed.
- Secondary firmware reverse should use JieLi pi32v2 support after the dump is acquired.
- SCORE7 support should be treated as separate/general Ghidra work and not as a dependency or acceptance gate for this repository.

## Active work

The issue tracker is the task backlog:
- #9 — Sunplus application reverse: module map, S/PDIF, USB, AC3/DTS, volume
- #10 — physical board map: audio path, SDRAM, USB/service pads
- #11 — identify/dump secondary `AK24BP24230` / AC695N side
