# Research plan

## Phase 1 — preserve and map stock firmware

Acceptance:
- stock dump hash recorded;
- STK extraction reproducible;
- all modules classified;
- CPU ISA and load addresses established;
- canonical Ghidra imports documented.

Status: in progress. Main application MIPS32 LE and `ap1` base are established.

## Phase 2 — recover board contracts

Targets:
- USB block ownership and mode;
- S/PDIF input path;
- AC3/DTS decode path;
- six-channel output generation;
- volume/mute implementation;
- SPHE <-> secondary-controller transport;
- SDRAM identity and map.

Acceptance requires static evidence plus continuity/runtime evidence where routing is involved.

## Phase 3 — controllable stock firmware

Goal:
- reproduce stock behavior from a controlled build/patch path;
- add a minimal external control channel without regressing decode/output behavior.

No flash write should be attempted until the stock image is recoverable and the write/rollback path is proven.

## Phase 4 — open firmware direction

Possible target:
- USB / Bluetooth / S/PDIF multichannel audio endpoint using the existing hardware.

This remains a research goal, not a current capability claim.
