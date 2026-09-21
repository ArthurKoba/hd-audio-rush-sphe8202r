# Reverse status

## Confirmed

- Product family: HD Audio Rush 5.1.
- PCB: `SPHE8202RD_SPDIF_V02`.
- Main package: Sunplus `SPHE8202R`.
- Raw external flash: Puya `P25D80SH`, 1 MiB dump preserved at `firmware/P25D80SH@SOP8.BIN`.
- STK rev-8203R opens the dump and extracts 18 module slots.
- Main application modules `ap1`, `cdrom`, `drv_other`, `wma` are coherent MIPS32 little-endian.
- `ap1.bin` base `0x8067B000` is confirmed by internal absolute references.
- Secondary-side UART excerpt contains AC695N/BR23 build/runtime strings.
- HCF4052-family device function is analog multiplexing; 74HC04D is a hex inverter; 4558-family devices are dual op-amps.

## Likely / provisional

- Secondary `AK24BP24230` is a JieLi/JL-family controller executing the observed AC695N/BR23 firmware.
- `wma.bin` base ~`0x8073F000`.
- `cdrom.bin` base ~`0x80754000`.
- `drv_other.bin` base ~`0x80782000`.
- 4558D devices near the six-channel outputs participate in analog buffering/filtering/preamplification.
- External SDRAM marking is close to the reported `PMS3064 / 16BTR-60N`, but exact transcription is not yet reliable.

## Unknown

- Exact SDRAM part, vendor and density; STK's `32M` unit is not resolved.
- Exact public SKU behind `AK24BP24230`.
- Exact SPHE <-> secondary-controller control/audio transport.
- Exact TOSLINK/coax -> decode -> six-channel analog signal path.
- Exact role of HCF4052 and 74HC04D on this PCB.
- Exact USB pad pinout and whether device/UAC mode is feasible.
- Safe read-only dump method for the secondary controller's internal firmware.

## Contradictions

### Physical SPHE8202R vs STK SPHE8203R

Physical package marking is `SPHE8202R`; STK displays `SPHE8203R`. Do not resolve this by assumption.

### SCORE7 vs MIPS

Correct STK extraction shows the main application modules are MIPS32 LE. SCORE7 is not the current assumption for `ap1/cdrom/drv_other/wma`.

## Active work

The issue tracker is the task backlog:
- #9 — Sunplus application reverse: module map, S/PDIF, USB, AC3/DTS, volume
- #10 — physical board map: audio path, SDRAM, USB/service pads
- #11 — identify/dump secondary `AK24BP24230` / AC695N side
