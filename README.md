# HD Audio Rush SPHE8202R

Reverse engineering and open-firmware research for an HD Audio Rush 5.1 decoder board built around a Sunplus SPHE8202R-class multimedia SoC.

The immediate goal is to recover the hardware/firmware architecture accurately enough to modify or replace the stock firmware without losing the board's existing multichannel decode functionality.

## Identified hardware

- Board silkscreen: **SPHE8202RD_SPDIF_V02**
- Main Sunplus device marking: **SPHE8202R**
- External SPI NOR: **Puya P25D80SH**, 8 Mbit / 1 MiB
- Secondary controller marking: **AK24BP24230**
- Product family: **HD Audio Rush 5.1**

See `docs/hardware.md` for evidence level and unresolved routing questions.

## Binary evidence

Canonical target/tool artifacts live directly in the repository:

- `firmware/stock/P25D80SH@SOP8.BIN` — exact 1 MiB target SPI dump
- `firmware/extracted/modules.tar` — all 18 STK module slots exported from that dump
- `firmware/extracted/modules/` — the same 18 modules materialized individually for direct reverse work
- `tools/vendor/sunplus-stk/STK Sunplus Tool Kits 0.2.3.zip` — historical STK archive containing the three known 0.2.3 executables

Exact sizes and SHA-256 hashes are recorded beside the artifacts and in `docs/provenance.md` / `firmware/MANIFEST.md`.

## Stock firmware

The 1 MiB SPI dump is a Sunplus firmware container, not one flat executable. Sunplus STK successfully recognizes and unpacks it.

Observed STK metadata includes:
- firmware version `02R-D-02`
- ROM requirement `1M`
- customer ID `SUNPLUS`
- 18 module slots
- SDRAM profile shown as `32M`, 16-bit, non-shared
- `Host USB 2.0 supported`

STK reports SoC `SPHE8203R` while the physical package is marked `SPHE8202R`. This is a tracked contradiction, not a resolved fact.

## CPU / code finding

The main extracted application modules are **MIPS32 little-endian**.

Confirmed clean MIPS code:
- `ap1.bin`
- `cdrom.bin`
- `drv_other.bin`
- `wma.bin`

The packed flash image must not be analyzed as a single SCORE7 or MIPS executable. The container has to be unpacked first.

Current main-module base:
- `ap1.bin` -> **0x8067B000**

Provisional bases:
- `wma.bin` -> ~`0x8073F000`
- `cdrom.bin` -> ~`0x80754000`
- `drv_other.bin` -> ~`0x80782000`

See `docs/firmware.md` and `docs/ghidra.md`.

## Interesting firmware anchors

The stock application contains strings for:
- `SPDIF/OFF`
- `SPDIF/RAW`
- `SPDIF/PCM`
- `SPDIF IN`
- AC3
- DTS
- PCM
- USB / SD
- audio setup/output modes

These prove those concepts exist in the software image; they do not by themselves prove the exact physical signal path on this PCB.

## Repository layout

- `docs/` — hardware, firmware and evidence ledger
- `evidence/` — captured runtime/tool evidence
- `firmware/stock/` — immutable stock firmware dumps
- `firmware/extracted/` — extraction archives and byte-exact extracted modules
- `reverse/` — Ghidra/import notes and reverse scripts
- `hardware/` — board/photo/pinout evidence
- `tools/vendor/` — preserved third-party reverse tools with provenance
- `tools/` — project-owned tool notes/scripts

## Working discipline

The repository distinguishes confirmed evidence from hypotheses. See `AGENTS.md` and `docs/reverse-status.md` before making architecture claims.

No production-ready or hardware-safe custom firmware exists yet.
