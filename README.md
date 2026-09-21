# HD Audio Rush 5.1 / SPHE8202R

Reverse engineering of the HD Audio Rush 5.1 decoder board revision `SPHE8202RD_SPDIF_V02`.

The repository keeps the canonical firmware/tool artifacts, reproducible analysis helpers, one UART excerpt, and reverse-engineering notes.

## Project objective

The goal is **control-complete reverse engineering** of the whole board, not merely disassembling one firmware image.

The project is complete when we can preserve firmware from both processors, explain the important hardware and inter-chip contracts, rebuild or patch each firmware through a known path, recover after a bad firmware experiment, flash modified firmware safely, and programmatically control the useful system functions without treating either processor as an unexplained black box.

For this project, "fully reversed" does **not** mean every internal function must be renamed. It means the boot/update paths, hardware contracts, audio routing, control state, inter-chip protocol and firmware modification path are understood well enough to make intentional changes and validate them on hardware.

Before claiming reverse-complete, all of the following must be true:

- Sunplus raw dump preserved and its container/module layout understood;
- secondary-controller firmware dumped and preserved;
- both CPU architectures have a usable static-analysis path;
- SPHE <-> secondary-controller data/control links are mapped;
- S/PDIF input, AC3/DTS handling, volume/mute and six-channel output ownership are identified;
- USB/service interfaces and their boot/update roles are identified;
- packing/checksum/integrity requirements are reproduced;
- at least one safe recovery method is proven for each writable firmware domain;
- at least one intentional firmware modification is flashed and hardware-validated;
- a documented control path exists for source/mode, volume/mute, status and any later USB/Bluetooth extensions.

USB Audio Class, new Bluetooth behavior and similar additions are post-reverse features, not prerequisites for understanding the original board.

## Analysis toolchain decision

**Ghidra stays. SCORE7 does not belong to this project's dependency set.**

- The extracted Sunplus application modules are coherent **MIPS32 little-endian**, so normal Ghidra MIPS support is the correct path for `ap1.bin`, `drv_other.bin`, `cdrom.bin` and `wma.bin`.
- The custom SCORE7 backend came from the early, incorrect assumption that the packed 1 MiB Sunplus container itself was SCORE7 code. Correct STK extraction disproved that assumption for the primary modules.
- No current target binary on this board has been proven to require SCORE7. Auxiliary `iop` / DSP images remain unidentified and must not be labelled SCORE7 without evidence.
- SCORE7 is useful general Ghidra work and should be maintained/contributed separately from this board project rather than treated as required infrastructure here.
- The secondary BR23 / AC695N-family side uses JieLi's **pi32v2** architecture. Once its flash is dumped, the intended static-analysis path is a pi32v2 Ghidra processor definition, cross-checked against the JieLi toolchain/objdump and available AC695N SDK sources.

## Work order

1. **Acquire the missing secondary-controller dump.** Until both firmware domains are preserved, the whole-system model is incomplete. This does not block independent Sunplus work.
2. **Finish the physical board map.** Determine SDRAM identity, USB/UART pin ownership, TOSLINK path, six-channel analog path and the SPHE <-> secondary-controller buses.
3. **Reverse the Sunplus control surfaces, not random functions.** First resolve the reopened AP1 address-model gate and stale Ghidra call references, then trace S/PDIF, AC3/DTS, USB, volume/mute, board init and inter-chip calls. Shared GP is established, but the current analysis is not yet a clean call model.
4. **Reverse the secondary firmware.** Match the dump to BR23/AC695N SDK code, identify its audio/control responsibilities and inter-chip protocol.
5. **Recover packing, flashing and rollback for both sides.**
6. **Implement a minimal control plane and a controlled firmware modification.**
7. Only then add new features such as USB audio, alternate Bluetooth behavior or a richer external control interface.

The current issue #9 focus is Sunplus-only. The issue tracker is the task backlog; umbrella issue #15 defines the end-to-end reverse/reflash/recovery/control acceptance.

## Hardware platform

| Part | Identification | Current understanding |
|---|---|---|
| Main multimedia SoC | Sunplus `SPHE8202R` | Main decoder / multimedia processor |
| External RAM | marking reported as `PMS3064 / 16BTR-60N`; transcription still needs a clean photo | External SDRAM. STK reports `32M`, 16-bit, non-shared; exact vendor/capacity is not yet proven |
| SPI NOR | Puya `P25D80SH` | 8 Mbit / 1 MiB, contains the Sunplus firmware container |
| Secondary controller | marking `AK24BP24230` | Runs JieLi AC695N/BR23-family firmware according to UART log; exact public SKU unresolved |
| Analog switch | `HCF4052` / HCF4052B-family marking reported | Dual 4-channel analog multiplexer/demultiplexer; exact board routing still to be traced |
| Logic | `74HC04D` marking reported | Hex inverter; exact role on this board still to be traced |
| Analog output stage | `4558D`-marked 8-pin ICs near the outputs | 4558-family parts are dual op-amps; likely channel buffering/filtering/preamplification, exact topology not yet traced |

Physical/interface observations:
- the UART jumper/header used for the captured boot log routes to the secondary controller side; TX output is confirmed, an interactive RX shell is not;
- the four-pad USB/service footprint is reported to route to the main Sunplus side; exact D+/D-/VBUS/GND pin mapping is not yet archived as continuity evidence;
- board I/O includes optical/coaxial S/PDIF, AUX and six analog outputs (FL/FR/SL/SR/CEN/SUB).

See `docs/hardware.md` for evidence levels and open measurements.

## Repository artifacts

| Path | Size | SHA-256 |
|---|---:|---|
| `firmware/P25D80SH@SOP8.BIN` | 1,048,576 | `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e` |
| `tools/STK_0.2.3.zip` | 1,420,979 | `cba31e5d7d7345078d3178290a4578f0484b3eaa7bea4a7ea303b3db0da01c3a` |

`firmware/P25D80SH@SOP8.BIN` is the raw byte-for-byte SPI NOR dump from the target board. It is not a rebuilt image.

The STK ZIP contains exactly:
- `STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe` — 1,057,792 bytes — SHA-256 `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89`
- `STK Sunplus Tool Kit 0.2.3 (rev 090811) English.exe` — 1,057,280 bytes — SHA-256 `c55483e26c520467e953660b417a329014135213d7f0d3c5e1279bff5a71fb00`
- `STK Sunplus Tool Kit 0.2.3 (rev 090824) English.exe` — 1,058,304 bytes — SHA-256 `855cabb99b057a00236c88ccb81a09b73fdb2c69c33f78879e3c5e09199f2025`

The rev-8203R build is confirmed to open the target dump and extract the module set.

## Extracted modules

The extracted files live directly in `firmware/modules/`. The redundant `modules.tar` archive is intentionally not kept.

| Module | Bytes | SHA-256 |
|---|---:|---|
| `ap1.bin` | 684192 | `3ccee96ffeb5a8668f055ce97b59fe65084d4f28d47286ee63dd21c4bd96047b` |
| `drv_other.bin` | 301072 | `e9463f81093a43990c39ca39555d2742f29ebb2fe7fc7ca7e8eac0b694de6451` |
| `rom12.bin` | 82528 | `6747dadb731d13fdd17ba29121e9267ccc221fdfd7f7337df19d6f6c89c4e52f` |
| `cdrom.bin` | 63264 | `476368446103ddeb3e067ec556472e7d2e18d68e6da2ce7911a539661f6f3b61` |
| `wma.bin` | 51308 | `8fd9d673b847b6764e8bd52888a86f42f040c0c07a141b9c3384f503eae8f26f` |
| `jpeg.bin` | 38816 | `466487578636c97949f1abf6a752279df98a80c51f3a8c38645db6181bc0a9ee` |
| `iop.bin` | 1424 | `f2bc8ee705fb723710998a452617facc12a7d044626cdce45a0e18c7f8afffca` |
| `srvdsp.bin` | 1128 | `f1c1cd85a647e3669f8bd39ccb75e53ec84a7d6951d17565207155d3e0457d12` |
| `iop_rst.bin` | 712 | `b1e9ecc0240a767f12b1f8cb544f1747d5fe85a8d0e11a5caf7bec1990a0e373` |

The remaining STK slots (`ap2`, `ap3`, `dvb`, `dvd`, `dvd_ipod`, `free`, `mp4`, `mpeg`, `rom3`) are zero-length files and are retained because they are part of the exact 18-slot extraction.

## Firmware findings

STK identifies the dump as:
- version `02R-D-02`
- ROM requirement `1M`
- customer `SUNPLUS`
- `SDRAM 32M`, 16-bit, non-shared
- `Host USB 2.0 supported`
- 18 module slots
- password `5168`

STK displays `SPHE8203R` while the physical package is marked `SPHE8202R`; this remains an explicit contradiction.

The primary application modules `ap1.bin`, `cdrom.bin`, `drv_other.bin` and `wma.bin` contain coherent **MIPS32 little-endian** code. Working module map:
- `ap1.bin` -> `0x8067B800`, corrected base applied in canonical Ghidra; remaining function-boundary/reference cleanup is tracked separately;
- `wma.bin` -> `0x8073F000` established;
- `cdrom.bin` -> `0x8074C800` established;
- `drv_other.bin` -> `0x80775800` established.

The shared MIPS small-data/global pointer is confirmed as `$gp = 0x80002B00`. In `wma.bin`, independent absolute/gp-relative pairs resolve both `0x800035D8 - 0xAD8` and `0x80003684 - 0xB84` to the same GP.

A 2026-09-21 raw-instruction audit found 43 stale Ghidra direct-flow references in the three non-AP1 modules. The encoded targets and stored xrefs disagree; a repair source is saved but its application was blocked and is not claimed complete. Separately, AP1 initial-delay calls, absolute/relative branch joins and string pointers contradict its old base. See `docs/firmware.md` before using existing function addresses or caller lists.

The application contains S/PDIF/AC3/DTS/PCM/USB anchors. CDROM stream initialization now has a documented classifier-result-to-mode mapping, including `0xAC3 -> 3`, and a working state type in Ghidra. STK's additive word-sum helper is identified, but target checksum reproduction, container reconstruction and safe repack are still open.

The canonical Ghidra project contains extracted CPU modules and the STK tool analysis. Flat imports of the 1 MiB Sunplus container remain removed; the raw dump is preserved as container evidence. No modified firmware image or hardware acceptance is claimed.

## Layout

```
firmware/
  P25D80SH@SOP8.BIN
  modules/
tools/
  STK_0.2.3.zip
  ghidra/RepairMipsDirectFlow.java
evidence/
  ac695n-boot-excerpt.log
reverse/
  modules.csv
docs/
  hardware.md
  firmware.md
  reverse-status.md
```

The GitHub issues are the task backlog; avoid creating extra planning documents for the same work.
