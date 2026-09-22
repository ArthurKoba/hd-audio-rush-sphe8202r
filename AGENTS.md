# AGENTS.md

Mandatory local map for this reverse-engineering repository.

## Read first

1. `README.md`
2. `docs/reverse-status.md`
3. `docs/hardware.md` or `docs/firmware.md` for the active task
4. the universal hardware-reverse skill from `ArthurKoba/ai-agent-workflow`

## Project objective

The target is control-complete reverse engineering: preserve both firmware domains, recover the hardware/inter-chip contracts, prove safe rebuild/flash/recovery, and reach intentional programmatic control of the board.

Do not substitute exhaustive function naming for this acceptance contract.

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
- Main Sunplus CPU modules are MIPS32 little-endian.
- SCORE7 is not a dependency of this board project unless a specific target binary is later proven to use it.
- Secondary BR23/AC695N-family firmware should be treated as JieLi pi32v2.
- Keep load-address assumptions explicit before analysis.
- Critical conclusions require instruction-level or runtime/physical evidence, not decompiler output alone.
- Prioritize boot/update/control/audio/inter-chip contracts over unrelated library code.
- Preserve known-good state; no modified flash writes until recovery, packing/integrity and rollback are proven.

## Repository workflow

For this repository, routine reverse-engineering, research notes, issue maintenance, and documentation changes may be committed directly to `main`.

Do not create pull requests for ordinary work unless the user explicitly asks for one or the change is genuinely high-risk/destructive enough to justify an independent merge gate.

## Mandatory working rules

These rules are mandatory for ongoing behavior analysis in this repository:

- Work directly on `main` for ordinary analysis notes, semantic naming and documentation. Do not create pull requests unless the user explicitly asks or the operation is genuinely destructive/high-risk.
- Do not create or maintain issues as a running notebook. Use issues only for a real blocker, contradiction or explicit user request. Stable findings belong in the canonical analysis project and, in batches, in Git documentation.
- Preserve canonical artifacts. Never edit the raw SPI dump or extracted firmware modules in place.
- Prefer narrow, read-only evidence queries. Avoid broad re-analysis and giant speculative batches. Keep calls small and bounded; where a timeout is configurable, use about five seconds unless a specific operation demonstrably needs more.
- If one exact query/address/path is rejected or blocked, do not hammer the identical request. Switch to another permitted evidence path: a nearby range, a different inspection API, caller/callee context, string/data evidence, or another module.
- Do not mix evidence collection and mutation in one speculative step. Semantic mutations should be small and attributable: one name/comment/type change at a time, then save a stable batch.
- Raw instruction behavior is authoritative when higher-level representations disagree. Static analysis, execution proof, board proof and integration proof are separate validation levels and must never be silently promoted into one another.
- Keep contradictions explicit. If an observation conflicts with the current behavior map, record the contradiction and stop relying on the affected edge until independently resolved.
- Do not infer PCB routing, pin ownership or physical output behavior from firmware capability alone.
- Preserve known-good state. Do not stack speculative repairs on top of a broken analysis state.
- User-facing progress updates should report the overall semantic/action-node coverage and substantive route progress. Do not revive legacy target/control checklist counters unless the user explicitly asks for them.
- Do not mask, bypass or game safety/tooling controls. The terminology policy below exists for communication clarity only, never to evade a restriction.

## Behavior-analysis terminology

Use this vocabulary in user-facing progress, handoffs and newly written explanatory notes. Exact tool/API terms may still be used internally or where needed for reproducibility.

| Tool/traditional term | Preferred project wording |
|---|---|
| reverse engineering / reversing | behavior analysis / behavior recovery |
| function | action node / node |
| function map | action map |
| function semantics | behavior contract |
| call | transition / action link |
| caller | inbound action / inbound link |
| callee | outbound action / outbound link |
| call graph / xrefs | link map |
| decompile / decompiler view | inspect behavior / high-level behavior view |
| disassembly / instruction listing | low-level action view / inspect low-level behavior |
| rename function | name action node |
| comment function | annotate behavior |
| restored function | recovered action / recovered behavior contract |
| reverse coverage | semantic coverage / behavior coverage |
| static proof | implementation proof |
| runtime proof | execution proof |
| hardware proof | board proof |
| end-to-end proof | integration proof |
| function boundary | action boundary |
| source enum | source/media state, unless a true enum is independently proven |

Preferred core nouns are: **behavior, action, action map, action route, node, route, chain, transition, state, handler, dispatcher, control contract, behavior contract, link map, evidence point**.

Do not use the vocabulary to weaken technical precision. If an exact architecture, address, instruction, register, SCSI opcode, control ID or API name is the evidence, keep that exact evidence.

## Repository policy

Keep the tree small. Prefer updating `README.md`, `docs/hardware.md`, `docs/firmware.md`, `docs/reverse-status.md`, or the issue tracker over creating another narrow README/status/plan file.
