# AGENTS.md

Mandatory local map for work in this repository.

## Authority

This repository is the durable source of truth for the HD Audio Rush / SPHE8202R reverse-engineering effort. Chat history is not authoritative when repository evidence exists.

Read, in order:
1. `README.md`
2. `docs/reverse-status.md`
3. the task-specific document under `docs/`
4. the universal hardware-reverse skill from `ArthurKoba/ai-agent-workflow`

## Repository roles

- `main`: canonical reviewed documentation, reverse-engineering source, and preserved binary evidence.
- normal working branches: implementation/reverse/documentation changes before review.
- Binary evidence is stored in-tree at the paths documented below; do not maintain a parallel evidence branch.

Artifact identity is defined by exact path, byte size and SHA-256.

## Evidence rules

Use these states explicitly:
- **CONFIRMED** — directly supported by a dump, disassembly, continuity measurement, UART/runtime output, silkscreen/marking, or reproducible tool result.
- **LIKELY** — supported by multiple clues but not yet directly proven on this board.
- **UNKNOWN** — material question with insufficient evidence.
- **CONTRADICTION** — two authoritative observations disagree; do not silently pick one.

Do not promote SoC capability into board implementation. A datasheet saying a block exists is not proof that this PCB routes or uses it.

## Reverse workflow

- Preserve stock artifacts byte-for-byte. Record SHA-256 before analysis.
- Prefer one canonical Ghidra project per binary/module set.
- Critical conclusions require instruction-level or runtime/physical evidence, not decompiler output alone.
- Keep module load addresses and ISA assumptions documented before auto-analysis.
- Never auto-analyze the packed 1 MiB stock image as one flat executable.
- Preserve known-good firmware and keep write/erase experiments separate from read-only analysis.
- Hardware experiments follow: baseline -> action -> observation -> rollback -> postcondition.

## Repository policy

- Changes go through a working branch and review for substantial updates.
- Do not commit credentials, machine-specific paths, or private infrastructure details.
- Target firmware artifacts belong under `firmware/stock/` and `firmware/extracted/`.
- Preserved third-party reverse-engineering tools belong under `tools/vendor/` with provenance and hashes.
- Ghidra project databases are not source files; commit scripts, maps, notes and reproducible import parameters instead.
- Record unresolved contradictions in `docs/reverse-status.md`.

## Current canonical targets

- Board: `SPHE8202RD_SPDIF_V02`
- Primary stock dump: `firmware/stock/P25D80SH@SOP8.BIN`
- STK extraction archive: `firmware/extracted/modules.tar`
- Extracted modules: `firmware/extracted/modules/`
- Main application module: `firmware/extracted/modules/ap1.bin`
- Sunplus STK archive: `tools/vendor/sunplus-stk/STK Sunplus Tool Kits 0.2.3.zip`
