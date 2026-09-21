# Firmware architecture

## Stock SPI dump

Canonical binary:
`files:P25D80SH@SOP8.BIN`

Size: 1,048,576 bytes  
SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`

The image is a Sunplus firmware container. It should not be treated as one raw executable.

## STK observations

Canonical tool archive:
`files:STK Sunplus Tool Kits 0.2.3 .zip`

The rev-8203R STK executable successfully recognizes and unpacks the image.

Observed GUI metadata:
- version: `02R-D-02`
- ROM required: `1M`
- customer ID: `SUNPLUS`
- SoC profile displayed: `SPHE8203R`
- SDRAM: `32M`
- SDRAM bus: 16-bit, non-shared
- Host USB 2.0: supported
- module slots: 18
- password shown by STK: `5168`

The displayed SPHE8203R profile conflicts with the physical SPHE8202R marking and remains unresolved.

## Extracted modules

Canonical extraction archive:
`files:modules.tar`

Archive SHA-256:
`542012b5b31ba01ab260e6f75a3f2dcfd8362e89b2143e0eca15279ccd23d98a`

| Module | Bytes | SHA-256 | Current classification |
|---|---:|---|---|
| ap1.bin | 684192 | 3ccee96ffeb5a8668f055ce97b59fe65084d4f28d47286ee63dd21c4bd96047b | main MIPS32 LE application |
| drv_other.bin | 301072 | e9463f81093a43990c39ca39555d2742f29ebb2fe7fc7ca7e8eac0b694de6451 | MIPS32 LE driver/auxiliary code |
| rom12.bin | 82528 | 6747dadb731d13fdd17ba29121e9267ccc221fdfd7f7337df19d6f6c89c4e52f | container/config/resource-like; not linear MIPS |
| cdrom.bin | 63264 | 476368446103ddeb3e067ec556472e7d2e18d68e6da2ce7911a539661f6f3b61 | MIPS32 LE module |
| wma.bin | 51308 | 8fd9d673b847b6764e8bd52888a86f42f040c0c07a141b9c3384f503eae8f26f | MIPS32 LE WMA-related module |
| jpeg.bin | 38816 | 466487578636c97949f1abf6a752279df98a80c51f3a8c38645db6181bc0a9ee | JPEG tables/resources |
| iop.bin | 1424 | f2bc8ee705fb723710998a452617facc12a7d044626cdce45a0e18c7f8afffca | IOP/special microcode candidate |
| srvdsp.bin | 1128 | f1c1cd85a647e3669f8bd39ccb75e53ec84a7d6951d17565207155d3e0457d12 | servo/DSP microcode candidate |
| iop_rst.bin | 712 | b1e9ecc0240a767f12b1f8cb544f1747d5fe85a8d0e11a5caf7bec1990a0e373 | IOP reset microcode candidate |

Zero-length module slots:
`dvd.bin`, `dvd_ipod.bin`, `free.bin`, `mp4.bin`, `mpeg.bin`, `rom3.bin`, `ap2.bin`, `ap3.bin`, `dvb.bin`.

## Load-address work

Confirmed:
- `ap1.bin` -> `0x8067B000`

Provisional, to be validated by multiple internal references:
- `wma.bin` -> `0x8073F000`
- `cdrom.bin` -> `0x80754000`
- `drv_other.bin` -> `0x80782000`

## Feature strings found in ap1

Examples include:
- `SPDIF/OFF`
- `SPDIF/RAW`
- `SPDIF/PCM`
- `SPDIF IN`
- `AUDIO OUT`
- `AUDIO SETUP`
- `DTS`
- `PCM`
- `AC3`
- USB/SD status strings

These are useful reverse anchors, not proof of board routing.
