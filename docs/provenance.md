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

## Current source artifacts

### Sunplus SPI dump

- file: `P25D80SH@SOP8.BIN`
- size: 1 MiB
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`

### STK-extracted corpus

- source archive SHA-256: `542012b5b31ba01ab260e6f75a3f2dcfd8362e89b2143e0eca15279ccd23d98a`
- module hashes: `firmware/MANIFEST.md`

### UART evidence

- capture: `evidence/uart/ac695n-boot.log`
- contains AC695N/BR23 build-path and runtime audio/volume/SPDIF messages

## Derived state

Ghidra names, types, comments and inferred load addresses are derived evidence. They should remain reproducible from the primary binaries and documented import parameters.
