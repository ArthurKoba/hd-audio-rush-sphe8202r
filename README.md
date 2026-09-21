# HD Audio Rush 5.1 / SPHE8202R

Reverse engineering of the HD Audio Rush 5.1 decoder board revision `SPHE8202RD_SPDIF_V02`.

The repository keeps only the artifacts needed for the work: the raw SPI dump, the already-extracted firmware modules, the STK tool archive, one UART excerpt, and reverse-engineering notes.

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

The primary application modules `ap1.bin`, `cdrom.bin`, `drv_other.bin` and `wma.bin` contain coherent **MIPS32 little-endian** code. Current load map:
- `ap1.bin` -> `0x8067B000` confirmed
- `wma.bin` -> ~`0x8073F000` provisional
- `cdrom.bin` -> ~`0x80754000` provisional
- `drv_other.bin` -> ~`0x80782000` provisional

The application contains anchors for `SPDIF/OFF`, `SPDIF/RAW`, `SPDIF/PCM`, `SPDIF IN`, AC3, DTS, PCM, USB/SD and audio setup/output modes.

## Layout

```
firmware/
  P25D80SH@SOP8.BIN
  modules/
tools/
  STK_0.2.3.zip
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
