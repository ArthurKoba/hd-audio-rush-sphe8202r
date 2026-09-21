# Firmware artifact manifest

## Canonical stock dump

Path:
`firmware/stock/P25D80SH@SOP8.BIN`

Properties:
- size: `1048576` bytes
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`
- source device: Puya P25D80SH SPI NOR from the target board
- status: immutable stock evidence

## Extracted Sunplus module corpus

Archive:
`firmware/extracted/modules.tar`

Materialized modules:
`firmware/extracted/modules/`

Archive properties:
- size: `1237504` bytes
- SHA-256: `542012b5b31ba01ab260e6f75a3f2dcfd8362e89b2143e0eca15279ccd23d98a`
- contains all 18 STK module slots

| File | Size | SHA-256 |
|---|---:|---|
| ap1.bin | 684192 | 3ccee96ffeb5a8668f055ce97b59fe65084d4f28d47286ee63dd21c4bd96047b |
| drv_other.bin | 301072 | e9463f81093a43990c39ca39555d2742f29ebb2fe7fc7ca7e8eac0b694de6451 |
| rom12.bin | 82528 | 6747dadb731d13fdd17ba29121e9267ccc221fdfd7f7337df19d6f6c89c4e52f |
| cdrom.bin | 63264 | 476368446103ddeb3e067ec556472e7d2e18d68e6da2ce7911a539661f6f3b61 |
| wma.bin | 51308 | 8fd9d673b847b6764e8bd52888a86f42f040c0c07a141b9c3384f503eae8f26f |
| jpeg.bin | 38816 | 466487578636c97949f1abf6a752279df98a80c51f3a8c38645db6181bc0a9ee |
| iop.bin | 1424 | f2bc8ee705fb723710998a452617facc12a7d044626cdce45a0e18c7f8afffca |
| srvdsp.bin | 1128 | f1c1cd85a647e3669f8bd39ccb75e53ec84a7d6951d17565207155d3e0457d12 |
| iop_rst.bin | 712 | b1e9ecc0240a767f12b1f8cb544f1747d5fe85a8d0e11a5caf7bec1990a0e373 |

Zero-length STK module slots:
- `dvd.bin`
- `dvd_ipod.bin`
- `free.bin`
- `mp4.bin`
- `mpeg.bin`
- `rom3.bin`
- `ap2.bin`
- `ap3.bin`
- `dvb.bin`

## Policy

Do not modify stock or extracted evidence in place. Derived/patched images belong under a separate future path and must carry explicit provenance back to the stock hash.
