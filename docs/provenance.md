# Evidence and provenance

## Primary target evidence

Highest-priority evidence for this board:

1. physical package/PCB markings;
2. continuity / oscilloscope / logic-analyzer measurements;
3. exact stock flash dumps and hashes;
4. runtime UART logs from the target;
5. disassembly of exact extracted target modules;
6. STK metadata from the exact target image.

## Reference evidence

Datasheets, related Sunplus devices, JieLi SDK sources and other HD Audio Rush revisions are useful reference material, but do not override contradictory target evidence.

## Binary evidence branch

Canonical large/binary artifacts are stored on repository branch `files`.

### Sunplus SPI dump

- branch/path: `files:P25D80SH@SOP8.BIN`
- size: 1,048,576 bytes
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`
- source: Puya P25D80SH removed/read from the target board
- status: immutable stock evidence

### STK-extracted corpus

- branch/path: `files:modules.tar`
- archive size: 1,237,504 bytes
- SHA-256: `542012b5b31ba01ab260e6f75a3f2dcfd8362e89b2143e0eca15279ccd23d98a`
- contains: all 18 STK module slots from the exact stock image
- contained module hashes: `firmware/MANIFEST.md`

### Sunplus STK tool archive

- branch/path: `files:STK Sunplus Tool Kits 0.2.3 .zip`
- size: 1,420,979 bytes
- SHA-256: `cba31e5d7d7345078d3178290a4578f0484b3eaa7bea4a7ea303b3db0da01c3a`

The archive contains exactly:

| Executable | Size | SHA-256 |
|---|---:|---|
| `STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe` | 1,057,792 | `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89` |
| `STK Sunplus Tool Kit 0.2.3 (rev 090811) English.exe` | 1,057,280 | `c55483e26c520467e953660b417a329014135213d7f0d3c5e1279bff5a71fb00` |
| `STK Sunplus Tool Kit 0.2.3 (rev 090824) English.exe` | 1,058,304 | `855cabb99b057a00236c88ccb81a09b73fdb2c69c33f78879e3c5e09199f2025` |

The rev-8203R executable is the build confirmed to recognize and unpack this target image.

### UART evidence

- capture: `evidence/uart/ac695n-boot.log`
- contains AC695N/BR23 build-path and runtime audio/volume/SPDIF messages

## Derived state

Ghidra names, types, comments and inferred load addresses are derived evidence. They should remain reproducible from the primary binaries and documented import parameters.
