# AGENTS.md

Mandatory local map for this reverse-engineering repository.

## Read first

1. `README.md`
2. `docs/reverse-status.md`
3. `docs/hardware.md` or `docs/firmware.md` for the active task
4. the universal hardware-reverse skill from `ArthurKoba/ai-agent-workflow`

## Evidence rules

Use explicit evidence states:
- **CONFIRMED** — target dump/disassembly, package marking, archived UART/runtime output, continuity/scope measurement, or another reproducible target result.
- **LIKELY** — multiple clues support it but target proof is incomplete.
- **UNKNOWN** — insufficient evidence.
- **CONTRADICTION** — authoritative observations disagree.

Datasheet capability is not PCB routing proof.

## Canonical artifacts

- raw SPI dump: `firmware/P25D80SH@SOP8.BIN`
- STK-extracted modules: `firmware/modules/`
- STK archive: `tools/STK_0.2.3.zip`
- UART excerpt: `evidence/ac695n-boot-excerpt.log`
- module/load map: `reverse/modules.csv`

Hashes are documented in the root `README.md`; do not add parallel checksum manifests unless a real automation need appears.

## Reverse rules

- Never modify the raw dump or extracted module files in place.
- Do not analyze the 1 MiB dump as one flat executable; unpacked CPU modules are the correct static-analysis inputs.
- Main CPU modules are currently MIPS32 little-endian; SCORE7 is not the active assumption for `ap1/cdrom/drv_other/wma`.
- Keep load-address assumptions explicit before analysis.
- Critical conclusions require instruction-level or runtime/physical evidence, not decompiler output alone.
- Preserve known-good state; no modified flash writes until recovery, packing/integrity and rollback are proven.

## Repository policy

Keep the tree small. Prefer updating `README.md`, `docs/hardware.md`, `docs/firmware.md`, `docs/reverse-status.md`, or the issue tracker over creating another narrow README/status/plan file.
