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
- S/PDIF output selection is now instruction-level confirmed through the control-descriptor layer. `ResolveControlIdToGroupSlot(0x71)` resolves group 2 / slot 1; its 13-byte descriptor at `0x80707FA3` is `03 71 12 75 77 00 00 00 00 00 00 0B 00`, where option IDs `0x12/0x75/0x77` map through the corrected translation table to `SPDIF/OFF`, `SPDIF/RAW`, `SPDIF/PCM`. `DispatchControlOption(controlId, optionId, sideEffects)` dispatches control `0x71` to `ApplySpdifOutputOption(optionId)`.
- `ApplySpdifOutputOption` at `0x807759E0` has explicit branches for OFF/RAW/PCM. RAW (`0x75`) selects internal mode 2; PCM (`0x77`) selects internal mode 1; OFF (`0x12`) clears/reconfigures the path. `IsSpdifPcmSelected` at `0x8077C21C` tests the selected descriptor option against `0x77`.
- Control `0x71` descriptor state slot is `0x0B`, so its selection index is mirrored through `DAT_80006810[0x0B] = 0x8000681B`. `LoadControlSelectionsFromStateSlots` and `SaveControlSelectionsToStateSlots` synchronize these state slots with the generic selection table at `0x800066B0 + group*9 + slot`. Ghidra type `ControlOptionDescriptor` (13 bytes) is applied to `0x80707FA3` with only evidence-backed fields named.
- The interactive OFF/RAW/PCM commit path is now instruction-level complete. `HandleControlMenuInputEvent` dispatches browse/edit states through `HandleControlMenuBrowseInput` and `HandleControlMenuEditInput`. Browse-state code around `0x8077AD20..0x8077AD44` copies the current runtime selection from `0x800066B0 + group*9 + slot` into `DAT_80002B2B` and enters edit state 3. Edit-state commit at `0x8077B244..0x8077B270` reads the descriptor `+0x0B` state-slot index, writes `DAT_80002B2B` to both `DAT_80006810[stateIndex]` and the runtime selection table, then calls `ApplyCurrentControlSelection` (`0x80777578`) and `SaveCurrentControlSelection` (`0x807774EC`).
- `ApplyCurrentControlSelection` handles descriptor type 3 by calling `DispatchControlOption(controlId, optionId, 1)`, so `AUDIO OUT` commits reach `ApplySpdifOutputOption` with side effects enabled. `SaveCurrentControlSelection` mirrors the runtime position back to `DAT_80006810[stateIndex]` and persists the byte through the generic NVRAM/config writer; `SaveAllControlSelections` (`0x8077C0D0`) writes the full `0x41`-byte selection blob and checksum path. This closes the static setter/getter/persistence contract for OFF/RAW/PCM.
- S/PDIF input selection is now statically recovered. AP1 external-input subsource selector `0x800032FA` maps `1 -> AUXIN`, `2 -> SPDIF IN`, and the non-AUX/non-SPDIF branch to `TUNER`; the mapping is instruction-backed by the source-status renderer at `0x8071E428..0x8071E4EC` using strings `AUXIN` (`0x8070B4D4`), `SPDIF IN` (`0x8070B4A0`), and `TUNER` (`0x8070B4AC`).
- `ToggleTunerSpdifInput` at `0x806FB920` toggles selector `0x800032FA` strictly `0 <-> 2`, giving a concrete TUNER/SPDIF setter. `FUN_806FED18` also writes selector `1` or `2` in a broader external-input transition path; its broader semantics remain unnamed.
- Source dispatcher state `gp+0x7A5 = 0x800032A5` indexes a 9-entry handler table at `0x8070B4E0`; handler table analysis is in progress. Index 1 is confirmed USB because its handler path reaches the `USB` string at `0x8070B504`.
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
- Board init, volume/mute, USB and the SPHE <-> secondary transport. S/PDIF input selection and S/PDIF OFF/RAW/PCM output selection are statically recovered; hardware behavior remains unvalidated.
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

## Coverage snapshot — 2026-09-21

- Ghidra function inventory across `ap1/wma/cdrom/drv_other`: **4011 functions**.
- Functions still carrying default `FUN_*` names: **3975**; semantic/non-`FUN_*` naming coverage is therefore **36/4011 = 0.90%**. This measures naming coverage only, not understanding of every analyzed function.
- Issue #9 checklist coverage after static S/PDIF input + RAW/PCM recovery: **7/22 = 31.8%** overall. By scope: address model **3/7 = 42.9%**, control surfaces **3/8 = 37.5%**, firmware construction **1/7 = 14.3%**.
- Validation level remains static/source analysis. No hardware acceptance is implied by these percentages.

## Agent handoff — continue here

Do **not** restart address/base discovery or S/PDIF OFF/RAW/PCM tracing. The current Sunplus state is already preserved in canonical Ghidra and in this document.

Immediate continuation order:

1. Continue the **AP1 source-dispatcher map** from `gp+0x7A5 = 0x800032A5` and the 9-entry handler table at `0x8070B4E0`. Entry 1 is already confirmed USB. Recover the remaining source indices and name only handlers proven by instruction/data evidence.
2. Finish the broader external-input transition routine around `0x806FED18`. It writes external-input subsource selector `gp+0x7FA = 0x800032FA` to values `1=AUXIN` and `2=SPDIF IN`; `ToggleTunerSpdifInput` at `0x806FB920` already proves the `0<->2` TUNER/SPDIF toggle. Determine caller/event semantics rather than rediscovering the selector mapping.
3. Then move to **volume/mute**. Start from confirmed control-descriptor/dispatcher infrastructure in `drv_other` instead of string hunting: `ResolveControlIdToGroupSlot`, `DispatchControlOption`, runtime selection table `0x800066B0`, persistent selection blob `DAT_80006810[0..0x40]`, and apply/save helpers already named in Ghidra.
4. After volume/mute, map USB/service init and then SPHE<->secondary-controller calls. Board-init tracing can proceed in parallel only where it does not depend on unresolved hardware routing.
5. STK/repack remains a separate lane: continue from `CalculateContainerWordSum @ 0x00401B56`, parser fields `+0x20/+0x40`, and unresolved intermediate routine `0x00401ED2`. Do not claim repack until a byte-exact no-change round trip is reproduced.

Known analysis hazards / do not repeat:
- AP1 base is **`0x8067B800` and already rebased in Ghidra**. The old `0x8067B000` model is invalid.
- `wma/cdrom/drv_other` still have **43 stale DEFAULT direct-flow refs** from old rebases. Treat caller/decompiler output cautiously until repaired through an authorized path.
- Runtime GP restore slot is instruction-proven **`0x88012200`**. The auxiliary Ghidra block currently at `0x88012A00` is stale metadata shifted by the AP1 rebase.
- The tool safety layer intermittently blocks even read-only Ghidra calls on specific ranges. Do not loop/retry the same blocked action. Prefer narrow single-address queries; when blocked, use canonical module bytes for raw instruction evidence and return to Ghidra only for confirmed semantic markup.
- Do not infer PCB routing from SoC/software capability. Current S/PDIF results are firmware-control evidence only.
- Work directly in `main`; no PRs. Do not modify the canonical dump or extracted module bytes.

Current coverage snapshot to carry forward:
- semantic/non-`FUN_*` function naming: **36/4011 = 0.90%**;
- issue #9 checklist: **7/22 = 31.8%** overall;
- address-model scope: **3/7 = 42.9%**;
- control-surface scope: **3/8 = 37.5%**;
- firmware-construction scope: **1/7 = 14.3%**;
- S/PDIF OFF/RAW/PCM static getter/setter/persistence contract: effectively closed for static analysis; hardware validation remains;
- S/PDIF input static selector contract: recovered; remaining work is higher-level source-dispatcher/caller semantics and hardware validation.

## Active work

The issue tracker remains the task backlog:
- #9 — Sunplus application and container reverse;
- #10 — physical board map;
- #11 — identify/dump secondary controller;
- #15 — end-to-end reverse/reflash/recovery/control acceptance.
