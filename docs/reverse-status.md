# Reverse status

## Project direction

Target state: **control-complete reverse engineering of the entire board**.

Both firmware domains are required for the overall objective, but the active issue #9 work is Sunplus-only. The missing secondary dump does not block independent Sunplus static analysis.

## Active decision boundary — 2026-09-21

**AP1 placement has been corrected to `0x8067B800` in the canonical Ghidra project.** The former `0x8067B000` claim is withdrawn. `reverse/modules.csv` records the corrected base as confirmed/rebased. Function-boundary cleanup and stale-flow-reference cleanup remain separate gates; the rebase does not by itself validate every pre-existing AP1 symbol/caller.

Separately, a read-only audit found 43 stale direct-flow references across `wma`, `cdrom` and `drv_other`. These make decompiler call targets and caller lists unreliable even where module placement is correct. The repair source is preserved, but its execution was blocked by the tool safety layer. No repair is claimed applied. See `docs/firmware.md` for reproducible examples, scope and remaining gates.

Do not stack broad auto-analysis or hardware-control conclusions on this inconsistent state.

## Confirmed

- Product family: HD Audio Rush 5.1; PCB: `SPHE8202RD_SPDIF_V02`; main package: Sunplus `SPHE8202R`.
- Raw external flash: Puya `P25D80SH`, 1 MiB dump preserved at `firmware/P25D80SH@SOP8.BIN`.
- STK rev-8203R opens the dump and extracts 18 module slots.
- Main application modules `ap1`, `cdrom`, `drv_other`, `wma` are coherent MIPS32 little-endian.
- `wma.bin` base `0x8073F000`, `cdrom.bin` base `0x8074C800`, and `drv_other.bin` base `0x80775800` retain their established module-map status. Correct bases do not imply correct stored Ghidra references.
- Shared MIPS GP is `0x80002B00`. Independent WMA pairs give `0x800035D8 - 0xAD8` and `0x80003684 - 0xB84`, both exactly `0x80002B00`. The AP1 base contradiction does not change these equations.
- AP1 at `0x806D96F8` executes `lui gp,0x8801; lw gp,0x2200(gp)`, proving the runtime GP restore slot is absolute `0x88012200`. The current Ghidra auxiliary block named `runtime_gp_slot` at `0x88012A00` is stale metadata shifted by the `+0x800` rebase; creation of a replacement block at `0x88012200` was blocked by the tool safety layer, so that metadata defect remains explicitly open.
- Shared helpers identified in `drv_other.bin`: byte-wise `memcmp` at `0x80783F08`, `memcpy` at `0x80783F3C`, and `memset` at `0x80783F64`.
- AP1 canonical module bytes were rechecked against the README SHA-256 during the address-model investigation; they were unchanged.
- Additional raw-pointer evidence strengthens the `0x8067B800` candidate and invalidates one old UI-table interpretation: word at file `+0x615D0` is `0x806DA5C8`, which resolves exactly to `SPDIF/OFF` at file `+0x5EDC8` only with the candidate base. The old base resolves it into unrelated bytes.
- RAW/PCM strings are at stable file offsets `+0x5F0AC/+0x5F0B8`, candidate runtime `0x806DA8AC/0x806DA8B8`. Those candidate addresses recur in localized pointer blocks at file `+0x6175C/+0x61764`, `+0x61F64/+0x61F6C`, `+0x62368/+0x62370`, `+0x6276C/+0x62774`, and `+0x62B70/+0x62B78`. By contrast, the old-listing chain through file `+0x61180` and `+0x62964` stores old absolute addresses; under the candidate base its targets are unrelated language text, so that earlier chain must not be used as the RAW/PCM setter path.
- The corrected AP1 translation table is recoverable directly from raw bytes: base `0x806DCD88` (file `+0x61588`), language stride `0x404 = 257*4`; item `113` is `AUDIO OUT`, item `117` is `SPDIF/RAW`, and item `119` is `SPDIF/PCM`.
- Command mailbox primitives are instruction-confirmed: `WriteCommandMailboxByte` at `0x8069B070` writes a 16-bit key to `s6+0xE80`, a byte value to `s6+0xE84`, and uses the `0x8000` handshake; `ReadCommandMailboxByte` at `0x8069B268` reads the response byte via `s6+0xE88` with the same handshake.
- Raw initialization code beginning at `0x8069D4F8` maps command key `0x4627 -> 0x75` and `0x4628 -> 0x77`; the pair repeats identically in four initialization clusters. A runtime branch at `0x80684AA0..0x80684940` produces `WriteCommandMailboxByte(0x401A,0x75)` through helper `0x8069E1A4`. This links RAW item ID `0x75` to a runtime command path, but the matching PCM `0x77` runtime path and the semantic meaning of key `0x401A` remain unresolved.
- AP1 contains S/PDIF/audio-status strings. Stable file offsets include `SPDIF/OFF` at `0x5EDC8`, `SPDIF/RAW` at `0x5F0AC`, `SPDIF/PCM` at `0x5F0B8`, and `SPDIF IN` at `0x8FCA0`. Their old Ghidra listing addresses are not confirmed runtime addresses.
- CDROM `0x8074C800` maps a byte subtype as `0 -> 2`, `1..5 -> 1`, `6..10 -> 2`, `>=11 -> 4`, with encoded calls to `0x80701A44` and conditionally `0x807017A8`. Its shared state access is `gp+0x774 = 0x80003274`; stored call references at `0x8074C838/0x8074C850` are wrong.
- CDROM classifier `0x8074C868` has an AC3-syncword branch returning `0xAC3`. Its caller at `0x8074CB2C`, now named `InitializeCdromPackedStream`, stores internal mode `3` for that result, mode `0` for `-1`, and modes `1/2` for the other two classifier results. The initializer returns the original classifier result, not the stored byte mode.
- STK program `/tools/stk.exe` contains a word-sum helper at `0x00401B56`, now named `CalculateContainerWordSum`. X86 instructions prove a wrapping 32-bit sum of unsigned little-endian 16-bit words. Parser call sites use expected fields at `+0x20` and, after an unresolved intermediate routine, `+0x40`. This is static tool-code evidence, not a reproduced target checksum or repack path.
- Secondary-side UART excerpt contains AC695N/BR23 build/runtime strings.
- HCF4052-family device function is analog multiplexing; 74HC04D is a hex inverter; 4558-family devices are dual op-amps.

## Likely / provisional

- AP1 base `0x8067B800` is applied in canonical Ghidra. Independent initial-delay call, absolute/relative branch convergence, cross-module entry and pointer-table evidence support the placement. Function-boundary cleanup is still pending.
- `CdromPackedStreamState` is a 24-byte analytical structure for the state beginning at `0x80003704`; its type and six state/signature labels are saved in Ghidra. The type has not been applied over invented RAM contents, and it is not claimed to be an original source declaration.
- The two non-AC3 CDROM formats use different converters (`0x8074D538` and `0x8074D030`). Their codec identities are not established; do not label them DTS merely from packing patterns.
- Secondary `AK24BP24230` is a JieLi/JL-family controller executing the observed AC695N/BR23 firmware.
- 4558D output-stage devices participate in analog buffering/filtering/preamplification.
- External SDRAM marking is close to reported `PMS3064 / 16BTR-60N`, but exact transcription is not yet reliable.

## Retained findings requiring address-model revalidation

Earlier notes identified shared audio-mode writes through `gp+0x774` and `gp+0x76C`, numeric modes `1/2/4/0x1000/0x2000/0x4000`, and field values `0x600/0x700/0x800/0x300/0x400/0x500`. These remain useful instruction anchors, but the AP1 listing locations `0x807012C8` and `0x806FFD9C` must not be described as validated function entries/runtime addresses. The old base split at least one real routine into false function fragments. Exact AC3/DTS/PCM mapping of these audio-core numbers remains unknown and is distinct from the CDROM classifier-to-mode mapping above.

## Unknown / remaining validation

- Corrected AP1 analysis, clean direct-flow references, remaining indirect/data references and module import/export tables.
- Board init, complete S/PDIF RAW/PCM control chain, volume/mute, USB and the SPHE <-> secondary transport.
- Exact SDRAM part/vendor/density and STK `32M` unit; public SKU behind `AK24BP24230`.
- Secondary flash ID/size, physical USB download route and safe recovery path.
- Exact TOSLINK/coax -> decode -> six-channel analog signal path; HCF4052/74HC04D routing and USB pad pinout.
- Identity/hash of the already-imported `/tools/stk.exe` versus the three archived revisions, complete container module-table schema, intermediate transform, checksum reproduction, writer/repack and rollback validation.

## Contradictions

### AP1 base and stored Ghidra references

The old `0x8067B000` confirmation is withdrawn. Corrected base `0x8067B800` and the still-unrepaired analysis state are explicitly separated. A zero mismatch count between encoded J/JAL targets and stored references in AP1 does **not** prove its image base.

### Physical SPHE8202R vs STK SPHE8203R

Physical package marking is `SPHE8202R`; STK displays `SPHE8203R`. Do not resolve this by assumption.

### SCORE7 vs MIPS

Correct STK extraction shows the main application modules are MIPS32 LE. SCORE7 is not the active assumption or a dependency for `ap1/cdrom/drv_other/wma`.

## Tooling and persistence

- Canonical Ghidra project: `sphe8202r_decoder_p25d80`; extracted MIPS modules plus the existing STK analysis program. Earlier flat imports of the 1 MiB container remain removed.
- Saved this pass: AP1 address-model warning/bookmark; CDROM initializer name/comment, state type and labels; STK sum-helper name/prototype/comment.
- `tools/ghidra/RepairMipsDirectFlow.java` is a guarded metadata-repair source, audit-only by default. Source commit `3688a523` is recoverable; execution/application validation is absent. The audit snapshot is not a promise that parallel analysis cannot change counts.
- Decompile calls used a five-second timeout. Inline read-only audit loops had a four-second execution budget; most MCP methods expose no caller-controlled transport timeout. No full auto-analysis was launched in this pass.
- No firmware bytes patched, no flash writes, no PR, no secondary-controller reverse expansion.

## Active work

The issue tracker remains the task backlog:
- #9 — Sunplus application and container reverse;
- #10 — physical board map;
- #11 — identify/dump secondary controller;
- #15 — end-to-end reverse/reflash/recovery/control acceptance.
