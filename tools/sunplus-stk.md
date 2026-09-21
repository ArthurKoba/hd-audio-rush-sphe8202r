# Sunplus STK

Sunplus STK was used successfully to recognize and unpack the target stock SPI image.

## Canonical tool archive

Repository path:

`tools/vendor/sunplus-stk/STK Sunplus Tool Kits 0.2.3.zip`

Archive properties:
- size: 1,420,979 bytes
- SHA-256: `cba31e5d7d7345078d3178290a4578f0484b3eaa7bea4a7ea303b3db0da01c3a`

Verified archive contents:

| Executable | Size | SHA-256 |
|---|---:|---|
| `STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe` | 1,057,792 | `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89` |
| `STK Sunplus Tool Kit 0.2.3 (rev 090811) English.exe` | 1,057,280 | `c55483e26c520467e953660b417a329014135213d7f0d3c5e1279bff5a71fb00` |
| `STK Sunplus Tool Kit 0.2.3 (rev 090824) English.exe` | 1,058,304 | `855cabb99b057a00236c88ccb81a09b73fdb2c69c33f78879e3c5e09199f2025` |

The archive itself is preserved to avoid storing a second redundant copy of the three vendor executables. Extract it into an untracked scratch directory when needed.

## Confirmed working build

`STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe` successfully recognizes `firmware/stock/P25D80SH@SOP8.BIN` and exports all 18 module slots.

Observed target metadata:
- version: `02R-D-02`
- ROM required: `1M`
- customer ID: `SUNPLUS`
- SoC profile: `SPHE8203R`
- SDRAM: `32M`
- SDRAM bus: `16 BITS`
- shared SDRAM: no
- Host USB 2.0: supported
- password shown: `5168`
- module slots: 18

The displayed `SPHE8203R` profile conflicts with the physical `SPHE8202R` package marking and is tracked as a contradiction.

## Tool policy

Do not modify the preserved archive in place. New tool versions should be added as new immutable artifacts with source/provenance and SHA-256.
