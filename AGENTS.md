# AGENTS.md

Mandatory local map for this behavior-analysis repository.

## Read first

1. `README.md`
2. `docs/analyze-status.md`
3. `docs/hardware.md` or `docs/firmware.md` for the active task
4. the universal hardware-analysis skill from `ArthurKoba/ai-agent-workflow`

## Project objective

The primary milestone is an independently maintainable Sunplus firmware implementation that reproduces the original board's useful audio behavior before product-specific modifications are added. Reaching that milestone requires control-complete behavior analysis of the original audio path, preservation of both firmware domains, recovery of relevant hardware/inter-chip contracts, and a proven rebuild/flash/recovery path.

The secondary-controller domain remains part of whole-board completion, but it does not block beginning a Sunplus replacement implementation once its external contract is sufficiently isolated. Do not substitute exhaustive action node naming for this acceptance contract.

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

Use the universal GitHub writer/reviewer identity contract from `ArthurKoba/ai-agent-workflow`.

- `koba-ai-agent` owns working branches, commits, issue/PR creation and requested revisions.
- `koba-ai-reviewer` independently reviews and is the only identity that merges pull requests into `main`.
- Do not mutate reserved/default `main` directly and do not let the writer merge its own PR.

## Mandatory working rules

These rules are mandatory for ongoing behavior analysis in this repository:

- Persist Git documentation through a writer branch and pull request; the reviewer performs independent review and merge. Analysis-project semantic mutations remain separate from Git branch policy.
- Do not create or maintain issues as a running notebook. Use issues only for a real blocker, contradiction or explicit user request. During active behavior recovery, stable detailed semantics belong in the canonical Analysis project first; Git documentation is updated only for project policy, major milestones, acceptance boundaries, contradictions that affect planning, or an explicit synchronization/materialization pass.
- Preserve canonical artifacts. Never edit the raw SPI dump or extracted firmware modules in place.
- Prefer narrow, read-only evidence queries. Avoid broad re-analysis and giant speculative batches. Keep invokes small and bounded; where an analysis timeout is configurable, use at most one second for the current workflow. If that budget is insufficient, switch to a narrower evidence path instead of blindly retrying.
- If one exact query/address/path is rejected or blocked, do not hammer the identical request. Switch to another permitted evidence path: a nearby range, a different inspection API, inbound action/outbound action context, string/data evidence, or another module.
- Classify failures explicitly in user-facing progress. Use `❗` only for an external provider/safety/pre-tool classification block where the requested call did not reach the intended backend. Use `🟠` for MCP, connector, transport, schema, runtime, session, or backend defects. For `❗`, state the blocked operation class and the permitted alternative evidence path. For `🟠`, diagnose and repair the engineering defect through the owning repository/runtime when access is available; do not mislabel it as a provider safety block.
- Do not mix evidence collection and mutation in one speculative step. Semantic mutations should be small and attributable: one name/comment/type change at a time, then save a stable batch.
- Raw instruction behavior is authoritative when higher-level representations disagree. Static analysis, execution proof, board proof and integration proof are separate validation levels and must never be silently promoted into one another.
- Keep contradictions explicit. If an observation conflicts with the current behavior map, record the contradiction and stop relying on the affected edge until independently resolved.
- Do not infer PCB routing, pin ownership or physical output behavior from firmware capability alone.
- Preserve known-good state. Do not stack speculative repairs on top of a broken analysis state.
- User-facing progress updates should report the overall semantic/action-node coverage and substantive route progress. Do not revive legacy target/control checklist counters unless the user explicitly asks for them.\n- In ordinary user-facing progress, refer to actions by semantic names and omit raw numeric addresses unless the user explicitly asks for them. Exact addresses remain valid evidence in repository documentation and tool arguments.\n- Do not narrate routine tool latency or connection behavior. Report substantive results and real blockers; actual safety/tooling blocks still require the visible `❗` rule above.
- Do not mask, alternate route or game safety/tooling controls. The terminology policy below exists for communication clarity only, never to evade a restriction.

## Live semantic authority and documentation cadence

During active behavior recovery, the persistent Analysis project `sphe8202r_decoder_p25d80` is the **only live semantic authority** for recovered target-firmware details.

- New action names, boundaries, types, globals, enums, comments, transitions and behavior/control contracts are saved in Analysis first.
- Repository Markdown is a checkpoint/handoff/evidence surface and may intentionally lag the live Analysis project. Do not treat ordinary documentation lag as a contradiction or migration defect.
- Do not update README/status/firmware prose after every Analysis mutation. Synchronize Git documentation only for project policy, major milestones, acceptance changes, planning-relevant contradictions, or an explicit materialization checkpoint.
- `sphe_*_contract.h` and replacement-source code mirror only stable contracts that are already needed by implementation. They are not required to track every new reverse finding immediately.
- When the required behavior-recovery scope is complete, run a dedicated materialization phase: audit saved Analysis -> consolidate canonical documentation -> export stable contracts/types/constants into maintainable C/source -> validate agreement.
- After materialization and validation, preserve an immutable Analysis archive/export before considering the live mutable project disposable. Do not delete the only analysis evidence merely because C/docs have become the maintained authority.

This policy intentionally avoids continuous `Analysis -> Markdown -> headers -> Analysis` churn while reverse work is still moving.

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

## Canonical Analysis project lifecycle

The current persistent Analysis project for the HD Audio Rush 5.1 device is historically named `sphe8202r_decoder_p25d80` at `/projects/sphe8202r_decoder_p25d80.gpr`. Treat it as the canonical AudioRush device project until a deliberate native project migration/rename is performed. The historical processor/flash-oriented name does not mean the project is limited to one architecture; it contains CPU, runtime, DSP, loader/stub, and other device artifacts.

Project state and open-program state are different:

- the project and saved analysis persist on disk even when its worker session is idle-released;
- open programs are session-local handles and may disappear after idle release, worker restart, reassignment, or explicit close;
- `Program not found`, an empty `list_open_programs`, or a missing current program is therefore not evidence that analysis was lost;
- first check `project_session_info` and `list_project_files`; if the project is available, reacquire/open the project session and reopen only the required program from its project path;
- use `load_program_from_project` / `open_program` for saved project programs rather than re-importing the binary;
- only treat a program as missing/corrupt after the project file itself is absent or fails to open with a concrete backend diagnostic;
- do not abandon the active behavior route merely because a program handle was released. Recover the handle and continue from the saved project state.

Worker pool capacity is shared infrastructure, not permanent project ownership. A project normally stays sticky to one worker while its session is active, but an idle-released project may later reopen on another eligible worker. Do not assume worker index is part of the project's identity.

