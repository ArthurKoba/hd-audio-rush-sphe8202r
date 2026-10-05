# AGENTS.md

Mandatory local map for the HD Audio Rush behavior-analysis repository.

## Read first

1. `README.md`.
2. `docs/analyze-status.md`.
3. `docs/hardware.md` or `docs/firmware.md` for the active task.
4. `ArthurKoba/ai-agent-workflow/skills/hardware-reverse/README.md`.
5. For behavior-analysis tasks, also load the universal `behavior-analysis.md` and `analysis-project-lifecycle.md` modules routed by that skill.

Universal behavior-analysis terminology, evidence states, validation/proof levels and persistent analysis-project lifecycle are owned by `ArthurKoba/ai-agent-workflow`. Do not duplicate those rules here.

## Project objective

The primary milestone is an independently maintainable Sunplus firmware implementation that reproduces the original board's useful audio behavior before product-specific modifications are added. Reaching that milestone requires control-complete behavior analysis of the original audio path, preservation of both firmware domains, recovery of relevant hardware/inter-chip contracts, and a proven rebuild/flash/recovery path.

The secondary-controller domain remains part of whole-board completion, but it does not block beginning a Sunplus replacement implementation once its external contract is sufficiently isolated. Do not substitute exhaustive action-node naming for this acceptance contract.

## Canonical artifacts

- raw SPI dump: `firmware/P25D80SH@SOP8.BIN`;
- STK-extracted modules: `firmware/modules/`;
- STK archive: `tools/STK_0.2.3.zip`;
- UART excerpt: `evidence/ac695n-boot-excerpt.log`;
- module/load map: `analysis/modules.csv`.

Hashes are documented in the root `README.md`; do not add parallel checksum manifests unless a real automation need appears.

## Target-specific analysis rules

- Never modify the raw dump or extracted module files in place.
- Do not analyze the 1 MiB dump as one flat executable; unpacked CPU modules are the correct static-analysis inputs.
- Main Sunplus CPU modules are MIPS32 little-endian.
- SCORE7 is not a dependency of this board project unless a specific target binary is later proven to use it.
- Secondary BR23/AC695N-family firmware should be treated as JieLi pi32v2.
- Keep load-address assumptions explicit before analysis.
- Prioritize boot/update/control/audio/inter-chip contracts over unrelated library code.
- No modified flash writes until recovery, packing/integrity and rollback are proven.

## Repository workflow

Use the universal GitHub writer/reviewer identity contract from `ArthurKoba/ai-agent-workflow`. The writer owns working branches/PR revisions; the independent reviewer owns merge into `main`.

Analysis-project semantic mutations are separate from Git branch policy.

## Local working rules

- Do not use issues as a running analysis notebook. Use them for concrete trackable work items, blockers, contradictions or explicit user-requested tasks that need an independent lifecycle. Stable findings belong in the canonical analysis project and, in batches, in Git documentation.
- Preserve canonical artifacts. Never edit the raw SPI dump or extracted firmware modules in place.
- Keep analysis invokes narrow and bounded. For the current workflow, where timeout is configurable, use at most one second; if that is insufficient, switch to a narrower evidence path rather than blindly retrying.
- Do not revive legacy target/control checklist counters unless the user explicitly asks for them.

## Repository policy

Keep the tree small. Prefer updating `README.md`, `docs/hardware.md`, `docs/firmware.md`, `docs/analyze-status.md`, or the issue tracker over creating another narrow README/status/plan file.

## Canonical Analysis project

The persistent Analysis project for this device is historically named `sphe8202r_decoder_p25d80` at `/projects/sphe8202r_decoder_p25d80.gpr`. Treat it as the canonical Audio Rush device project until a deliberate native project migration/rename is performed.

The historical processor/flash-oriented name does not limit the project to one architecture; it contains CPU, runtime, DSP, loader/stub and other device artifacts.

Session/program recovery semantics follow the universal `analysis-project-lifecycle.md` module. Worker index is not part of the project's identity.
