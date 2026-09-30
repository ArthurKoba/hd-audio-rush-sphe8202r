# AGENTS.md

Mandatory local map for this behavior-analysis repository.

## Read first

1. `README.md`
2. `docs/analyze-status.md`
3. `docs/hardware.md` or `docs/firmware.md` for the active task
4. the universal hardware-analysis skill from `ArthurKoba/ai-agent-workflow`

## Project objective

The target is control-complete behavior analysis: preserve both firmware domains, recover the hardware/inter-chip contracts, prove safe rebuild/flash/recovery, and reach intentional programmatic control of the board.

Do not substitute exhaustive action node naming for this acceptance contract.

## Evidence rules

Use explicit evidence states:
- **CONFIRMED** — target dump/low-level action view, package marking, archived UART/runtime output, continuity/scope measurement, or another reproducible target result.
- **LIKELY** — multiple clues support it but target proof is incomplete.
- **UNKNOWN** — insufficient evidence.
- **CONTRADICTION** — authoritative observations disagree.

Datasheet capability is not PCB routing proof.

## Canonical artifacts

- raw SPI dump: `firmware/P25D80SH@SOP8.BIN`
- STK-extracted modules: `firmware/modules/`
- STK archive: `tools/STK_0.2.3.zip`
- UART excerpt: `evidence/ac695n-boot-excerpt.log`
- module/load map: `analysis/modules.csv`

Hashes are documented in the root `README.md`; do not add parallel checksum manifests unless a real automation need appears.

## analysis rules

- Never modify the raw dump or extracted module files in place.
- Do not analyze the 1 MiB dump as one flat executable; unpacked CPU modules are the correct static-analysis inputs.
- Main Sunplus CPU modules are MIPS32 little-endian.
- SCORE7 is not a dependency of this board project unless a specific target binary is later proven to use it.
- Secondary BR23/AC695N-family firmware should be treated as JieLi pi32v2.
- Keep load-address assumptions explicit before analysis.
- Critical conclusions require instruction-level or runtime/physical evidence, not high-level behavior engine output alone.
- Prioritize boot/update/control/audio/inter-chip contracts over unrelated library code.
- Preserve known-good state; no modified flash writes until recovery, packing/integrity and rollback are proven.

## Repository workflow

For this repository, routine behavior-analysis, research notes, issue maintenance, and documentation changes may be committed directly to `main`.

Do not create pull requests for ordinary work unless the user explicitly asks for one or the change is genuinely high-risk/destructive enough to justify an independent merge gate.

## Mandatory working rules

These rules are mandatory for ongoing behavior analysis in this repository:

- Work directly on `main` for ordinary analysis notes, semantic naming and documentation. Do not create pull requests unless the user explicitly asks or the operation is genuinely destructive/high-risk.
- Do not create or maintain issues as a running notebook. Use issues only for a real blocker, contradiction or explicit user request. Stable findings belong in the canonical analysis project and, in batches, in Git documentation.
- Preserve canonical artifacts. Never edit the raw SPI dump or extracted firmware modules in place.
- Prefer narrow, read-only evidence queries. Avoid broad re-analysis and giant speculative batches. Keep invokes small and bounded; where an analysis timeout is configurable, use at most one second for the current workflow. If that budget is insufficient, switch to a narrower evidence path instead of blindly retrying.
- If one exact query/address/path is rejected or blocked, do not hammer the identical request. Switch to another permitted evidence path: a nearby range, a different inspection API, inbound action/outbound action context, string/data evidence, or another module.
- If a tooling/safety layer blocks or rejects a transition during analysis, immediately surface that event in the next user-facing progress update with a visible `❗` marker. State briefly what class of operation was blocked (for example: broad query, batch read, mutation, script execution), and state the alternative evidence path being used next. Do not silently retry, hide the block, or leave the user guessing whether work stalled.
- Do not mix evidence collection and mutation in one speculative step. Semantic mutations should be small and attributable: one name/comment/type change at a time, then save a stable batch.
- Raw instruction behavior is authoritative when higher-level representations disagree. Static analysis, execution proof, board proof and integration proof are separate validation levels and must never be silently promoted into one another.
- Keep contradictions explicit. If an observation conflicts with the current behavior map, record the contradiction and stop relying on the affected edge until independently resolved.
- Do not infer PCB routing, pin ownership or physical output behavior from firmware capability alone.
- Preserve known-good state. Do not stack speculative repairs on top of a broken analysis state.
- User-facing progress updates should report the overall semantic/action-node coverage and substantive route progress. Do not revive legacy target/control checklist counters unless the user explicitly asks for them.\n- In ordinary user-facing progress, refer to actions by semantic names and omit raw numeric addresses unless the user explicitly asks for them. Exact addresses remain valid evidence in repository documentation and tool arguments.\n- Do not narrate routine tool latency or connection behavior. Report substantive results and real blockers; actual safety/tooling blocks still require the visible `❗` rule above.
- Do not mask, alternate route or game safety/tooling controls. The terminology policy below exists for communication clarity only, never to evade a restriction.

## Required project vocabulary

Use only the project vocabulary below in user-facing updates, handoffs and explanatory documentation:

- **behavior analysis** and **behavior recovery** for the overall activity;
- **action node**, **action boundary**, **action map** and **action route** for code structure;
- **transition**, **action link**, **inbound action** and **outbound action** for control flow;
- **high-level behavior view** and **low-level action view** for code inspection;
- **behavior contract** and **control contract** for recovered semantics;
- **semantic coverage** or **behavior coverage** for progress;
- **implementation proof**, **execution proof**, **board proof** and **integration proof** for validation levels;
- **state**, **handler**, **dispatcher**, **chain**, **route** and **evidence point** as the default core nouns.

Exact architecture names, instruction mnemonics, registers, control IDs, protocol fields and API identifiers remain valid evidence and should stay exact.

## Repository policy

Keep the tree small. Prefer updating `README.md`, `docs/hardware.md`, `docs/firmware.md`, `docs/analyze-status.md`, or the issue tracker over creating another narrow README/status/plan file.
