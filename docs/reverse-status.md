# Reverse status

## Project direction

Target state: **control-complete reverse engineering of the entire board**.

Both firmware domains are required for the overall objective, but the active issue #9 work is Sunplus-only. The missing secondary dump does not block independent Sunplus static analysis.

## Active decision boundary — 2026-09-21

**AP1 placement has been corrected to `0x8067B800` in the canonical Ghidra project.** The former `0x8067B000` claim is withdrawn. `reverse/modules.csv` records the corrected base as confirmed/rebased. Function-boundary cleanup and stale-flow-reference cleanup remain separate gates; the rebase does not by itself validate every pre-existing AP1 symbol/caller.

Separately, a read-only audit found 43 stale direct-flow references across `wma`, `cdrom` and `drv_other`. The earlier AP1 row reporting zero mismatches is now withdrawn as a current-safety claim: targeted raw checks on 2026-09-22 found at least four AP1 stored flow references shifted by exactly `+0x800` after the rebase. Confirmed examples are `0x8071EC9C` raw `j 0x8071EC4C` but stored xref `0x8071F44C`, `0x8071F548` raw `jal 0x806ED604` but stored xref `0x806EDE04`, `0x8071F550` raw `j 0x8071F50C` but stored xref `0x8071FD0C`, and `0x8067D514` raw `jal 0x806ED604` but stored xref `0x806EDE04`. Therefore AP1 caller/decompiler data also requires raw-instruction validation in affected regions. No broad repair is claimed applied. See `docs/firmware.md` for reproducible examples, scope and remaining gates.

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
- `wma/cdrom/drv_other` still have **43 stale DEFAULT direct-flow refs** from old rebases. AP1 is also now proven to contain at least four `+0x800` stale stored flow refs in the currently investigated source/media/audio region. Treat caller/decompiler output as provisional across all four modules and validate critical edges from raw instructions until repaired through an authorized path.
- Runtime GP restore slot is instruction-proven **`0x88012200`**. The auxiliary Ghidra block currently at `0x88012A00` is stale metadata shifted by the AP1 rebase.
- The tool safety layer intermittently blocks even read-only Ghidra calls on specific ranges. Do not loop/retry the same blocked action. Prefer narrow single-address queries; when blocked, use canonical module bytes for raw instruction evidence and return to Ghidra only for confirmed semantic markup.
- Do not infer PCB routing from SoC/software capability. Current S/PDIF results are firmware-control evidence only.
- Work directly in `main`; no PRs. Do not modify the canonical dump or extracted module bytes.

Current coverage snapshot to carry forward:
- semantic/non-`FUN_*` function naming in the live canonical project: **67/4059 = 1.65%**; function-inventory growth is not itself a completion metric;
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


## Behavior-analysis handoff — 2026-09-22 (latest)

This snapshot records the current behavior map after the latest USB/audio pass. It is a handoff, not a project-complete claim.

### Coverage

- Strict semantic/action-node coverage across the four loaded MIPS modules: **151 / 4145 = 3.64%** (live snapshot; parallel semantic work may continue changing both numerator and inventory).
- This percentage counts only action nodes with stable human semantic names. It does not measure byte coverage, instruction coverage, route coverage, hardware acceptance or project completion.
- Route understanding is substantially ahead of the naming percentage because many large actions, transitions, state tables and callback contracts are already understood without being split into separately named nodes.

### USB host and Mass Storage behavior

The USB path is now closed from controller presence through SCSI block I/O and into the media state machine.

Confirmed route:

`PollUsbControllerPresence`
-> `ResetUsbHostControllerState` / `ClearUsbDeviceContext`
-> `InitializeUsbDeviceContext`
-> `HandleUsbDeviceTreeEvent`
-> `InitializeUsbDeviceTreeContexts`
-> `CreateMediaChildContexts`
-> primary MSC context `0x80002E24`
-> `ProbeUsbMediaUnits`
-> `CheckUsbMediaDeviceReady`
-> `NormalizeUsbMediaState`
-> `HandleUsbMediaRuntimeState`
-> `HandleUsbMediaActivation`
-> `InitializeUsbMediaRoute`.

USB class behavior is now explicit:
- child class `0x08` is USB Mass Storage and creates the SCSI/MSC context;
- child class `0x09` is USB Hub and uses the separate hub context `0x80002E2C`;
- the unsupported hub branch emits `[Hubs Not Supported]`;
- `ReleaseMediaChildContexts` / `ReleaseUsbDeviceTreeContexts` release the matching contexts and clear primary/secondary pointers.

The Mass Storage readiness sequence is standard SCSI:
- `RunUsbScsiInquiry`: opcode `0x12`, up to 3 attempts, returns the 36-byte inquiry payload;
- `CheckUsbScsiUnitReady`: opcode `0x00` TEST UNIT READY;
- `ReadUsbScsiCapacity`: opcode `0x25` READ CAPACITY(10), up to 2 attempts, converts both 32-bit big-endian response fields;
- `ReadUsbScsiSense`: opcode `0x03` REQUEST SENSE, up to 3 attempts;
- `ReadUsbBlocksWithRetry`: READ(10), opcode `0x28`;
- WRITE path at action start `0x806AAB8C`: WRITE(10), opcode `0x2A`.

READ/WRITE behavior:
- requests are clamped so `LBA + count - 1` does not pass the last reported LBA;
- READ retries up to four attempts;
- WRITE retries up to three attempts;
- result `-4` has a dedicated path instead of ordinary retry/failure handling;
- `ExecuteUsbMassStorageScsiCommand` drives command/data/status phases;
- CBW/CSW handling is separated into `BuildUsbMassStorageCbw`, `ProcessUsbMassStorageCsw`, and `ValidateUsbMassStorageCsw`;
- CSW signature `0x53425355` and matching command tag are validated.

REQUEST SENSE handling is now mapped:
- sense key 0 NO SENSE -> internal `0x1FE`;
- key 1 RECOVERED ERROR -> `0x1FF`;
- key 2 NOT READY uses ASC mapping: `0x04 -> 0x200`, `0x06 -> 0x201`, `0x08/0x54 -> 0x202`, `0x3A` medium-not-present -> `0x203`, other -> `0x207`;
- key 3 MEDIUM ERROR -> `0x208`;
- key 4 HARDWARE ERROR -> `0x209`;
- key 5 ILLEGAL REQUEST -> `0x20A`;
- key 6 UNIT ATTENTION: `ASC/ASCQ 0x28/0x00` -> `0x212`, other -> `0x20B`;
- key 7 DATA PROTECT -> `0x20C`;
- key 11 ABORTED COMMAND -> `0x20D`;
- key 13 VOLUME OVERFLOW -> `0x20E`.

The readiness probe maintains an availability bitmask at context `+0x54`, stores the selected unit index at `+0x5A`, and records per-unit last-LBA/block-size data. Block size `>= 0x1000` enters the firmware's oversized-sector error route rendered as `[BYTE/SECTOR >2048]`. For ready polling, the firmware uses a larger attempt budget for one/two-unit devices and a shorter budget for devices exposing more units.

### USB media to playback and decoder handoff

USB source activation is multi-state, not a one-value source enum.

`InitializeUsbMediaRoute` installs startup media callback `0x8075A850` and enters media state 7. `HandleMediaEventTransition` executes the active callback, decodes the normalized event word as `class = event & 0xC000` and `payload = event & 0x3FFF`, then either advances to state 9 or replaces the startup callback with a general playback handler:
- `0x80719B70`;
- `HandlePlaybackNavigationEvent @ 0x8071A624/0x8071A628`.

State 9 is `HandleMediaAudioTransitionState`. For ordinary media payloads it advances to state 3 and calls `InitializeMediaAudioPlaybackRoute`, whose sole audio-preparation child is `PreparePackedMediaAudioRoute`. State 3 is then a post-start/session state rather than a decoder-selection state.

The selected-stream path is separately confirmed:
`ParseMediaContainerStreamMetadata`
-> `ProcessSelectedMediaStreamState`
-> stream/session selection actions
-> `ConfigureSelectedMediaStreamAudio`.

`ConfigureSelectedMediaStreamAudio` directly performs:
1. stream/profile field extraction;
2. `SetAudioDecoderState`;
3. `ApplyDecoderOutputProfile`;
4. `CommitAudioFormatMode`;
5. `ConfigureSecondaryAudioFromStreamHeader` for header-derived service parameters.

`ConfigureSecondaryAudioFromStreamHeader` fills the shared stream descriptor around `0x8000A860`, writes the changed header-derived fields, calls `ApplyDecoderServiceConfig`, and that route ultimately reaches `StartConfiguredAudioPipeline`. The pipeline-start path conditionally restores effective master volume.

### Codec and decoder state map

`HandleStreamTypeDecoderConfig` is a WAVE-format dispatcher. The first 16-bit field is the `WAVEFORMATEX.wFormatTag` value.

Confirmed mappings:
- `0x0001` PCM -> decoder state `0x10`, generic service mode `0x40`;
- `0x0002` MS ADPCM -> state `0x04000000`, legacy WAVE codec route;
- `0x0006` A-law -> state `0x04000000`, same legacy route;
- `0x0007` mu-law -> state `0x04000000`, same legacy route;
- `0x0011` IMA/DVI ADPCM -> state `0x10`, generic service mode `0x80`;
- `0x0050` MPEG-1 audio -> state `0x100`;
- `0x0055` MP3 -> state `0x100`;
- `0x0161` WMA Standard -> state `0x4000`, WMA route.

The legacy WAVE codec action at `0x80702004` is used for MS ADPCM/A-law/mu-law. It writes secondary audio registers `0x40`, `0x41`, `0x43`, and `0x48`, then calls `StartConfiguredAudioPipeline`.

WMA is a separate route:
`state 0x4000`
-> `InitializeWmaDecoderConfig`
-> `InitializeWmaModule @ 0x8073F000`
-> secondary registers `0x40..0x49`
-> backend commit/delay command `0x50`
-> `StartConfiguredAudioPipeline`.

The decoder/hardware status machine is distinct from stream-format states:
- status type 0 PCM -> state `0x8000`;
- status type 1 AC3 -> `0x10000`;
- status type 2/3 DTS -> `0x20000`.

Packed-media classification is also distinct:
- classifier result `0xAC3` -> packed AC3 route -> state `0x200`;
- positive non-AC3 results `1/2` -> `ConfigurePackedNonAc3AudioRoute` -> state `0x2000`.

Do not collapse hardware-status states, WAVE codec states and packed-media states into one enum.

### Sample-rate and audio-service profiles

The action beginning at `0x807019BC` classifies sample-rate families before codec dispatch:
- ranges around 8, 16 and 32 kHz select audio-format mode 1;
- other rates, including the explicit bands around 11.025 and 22.05 kHz, select mode 2.

`CommitAudioFormatMode` maintains a separate audio-service profile layer. Confirmed encodings in service field bits `[11:8]` include:
- mode `1 -> 0x600`;
- mode `2 -> 0x700`;
- mode `4 -> 0x800`;
- mode `0x1000 -> 0x300`;
- mode `0x2000 -> 0x400`;
- mode `0x4000 -> 0x500`.

These service profiles are not the same thing as decoder states.

### Hardware audio-action dispatcher and controls

`DispatchAudioHardwareAction` accepts action IDs `0..0x1A` and writes command families through the common backend command area before issuing a synchronous backend commit.

Confirmed action contracts include:
- action 1 -> downmix command family `0x0300 | value`;
- action 2 -> master-volume hardware path;
- action 3 -> KEY command family `0x0500 | value`;
- action 4 -> command family `0x0600 | value`;
- action 5 -> `0x0700 | value`;
- action 6 -> `0x0800 | value`;
- action 7 -> S/PDIF/output mode family `0x0900 | value`;
- action 8 -> `0x0A00 | value`;
- action 9 -> `0x0D00 | value`;
- action 0x0B -> `0x0C00 | value`;
- action 0x17 -> speaker topology `0x2300 | topology`;
- action 0x19 -> `0x2800 | value`.

`ApplySpeakerConfiguration` builds a packed speaker topology from FRONT/CENTER/REAR/SUB state and applies it through action `0x17`.

The control descriptors now identify the main setup groups:
- **AUDIO SETUP**: `AUDIO OUT`, `DOWN SAMPLE`, `GM5`, `KEY`;
- **SPEAKER SETUP**: `DOWNMIX`, `SUBWOOFER`, `CENTER DELAY`, `REAR DELAY`, `FRONT`, `CENTER`, `REAR`;
- **DIGITAL SETUP**: `OP MODE`, `DYNAMIC RANGE`, `DUAL MONO`.

The separate VIDEO SETUP group contains BRIGHTNESS/CONTRAST/HUE/SATURATION/SHARPNESS and must not be mixed into audio control interpretation.

### Master volume and mute

Master volume remains a runtime control:
- `master_volume_level = 0x80003332`;
- `master_mute_flag = 0x800032B5`.

VOL+/VOL- update the runtime level, conditionally apply it through `SetMasterVolumeLevel`, and update UI/status. No direct save/NVRAM action is present in the confirmed VOL+/VOL- path. `ToggleMasterMute` is also runtime: mute sets the flag and applies effective level 0; unmute clears the flag and, at normal playback speed, calls `ClearMuteAndRestoreVolume`.

The confirmed rule is therefore:
`effective_volume = master_mute_flag ? 0 : master_volume_level`.

The runtime gain table at `0x88012CA0` is shared by multiple audio command families, not only master volume. All references found in the loaded modules are reads. Its initialization/source is outside the currently loaded code/runtime image, so exact gain bytes remain open.

### Remaining high-value gaps

The most important unresolved items after this pass are:
- origin/initialization of runtime gain table `0x88012CA0`;
- startup/persistence source of `master_volume_level` if one exists outside the runtime button path;
- exact semantic identities of private stream tags `0x2000/0x2001`;
- exact meaning of two standalone runtime step controls driven through hardware action IDs 4 and 0x0A;
- physical board validation of S/PDIF/analog routing and channel ownership;
- execution/hardware proof for the statically recovered USB/audio routes.


### Speaker / digital controls to SPHE audio-service contract — 2026-09-22

A focused instruction-level pass now separates menu semantics from the common low-level audio command transport.

- `DispatchAudioHardwareAction @ 0x806FFD1C` writes the command word at `0xBFFE84C0`, optional/auxiliary value at `0xBFFE84C4`, then normally commits synchronously through runtime entry `0x88001C78(1,0,0,100000)`.
- Action 1 is a generic decoder/output-mode transport, not a DOWNMIX-only command. Its base family is `0x0300 | mode`, with a 16-bit auxiliary payload. Confirmed users include DOWNMIX, S/PDIF/output handling, GM5, DIGITAL SETUP OP MODE, DUAL MONO and DYNAMIC RANGE.
- Speaker-specific families are separate: action 6 -> `0x0800 | subwoofer_state`; action `0x0B` -> `0x0C00 | delay_selector` with the delay value in the auxiliary word; action `0x17` -> `0x2300 | packed_topology`.
- `SetSpeakerChannelState` selectors are instruction-confirmed as `0=FRONT`, `1=CENTER`, `2=REAR`, `3=SUBWOOFER`. FRONT/CENTER/REAR feed the packed topology; SUBWOOFER also emits its dedicated action-6 command before topology reapply.
- Descriptor-backed control IDs are now pinned: AUDIO SETUP `0x71 AUDIO OUT`, `0x5B DOWN SAMPLE`, `0x9E GM5`, `0x5C KEY`; SPEAKER SETUP `0xF5 DOWNMIX`, `0x8B SUBWOOFER`, `0xD1 CENTER DELAY`, `0xD2 REAR DELAY`, `0xD3 FRONT`, `0xCD CENTER`, `0xCE REAR`; DIGITAL SETUP `0xF9 OP MODE`, `0x6A DYNAMIC RANGE`, `0xFC DUAL MONO`.
- OP MODE maps its two choices into generic output-mode payloads `0x20` and `0x10`. DUAL MONO maps its four choices into `0x90..0x93`. DYNAMIC RANGE uses mode selector `0x80`; its auxiliary payload is zero for state zero, otherwise `((state * 0x101) << 5) - 0x101` truncated to 16 bits.
- `ApplyDownsampleRateMode @ 0x80701B80` maps selections `0..2` through the halfword table `0x80702F40` to internal masks `0x0007 / 0x0067 / 0x0667`, stores the changed mask at `gp+0x744`, then reuses `CommitAudioFormatMode`.
- `ReapplyDigitalAndSpeakerDelayControls @ 0x8077C29C` is now named in the canonical project. It reapplies OP MODE, conditionally DYNAMIC RANGE, DUAL MONO, then CENTER and REAR delay values from the persistent selection state.

The static proof currently ends at the SPHE service mailbox and runtime commit entry. `0x88001C78` is not present as an analyzable action node in the loaded modules, so DAC/channel/PCB routing below that boundary remains a board/runtime-proof task rather than a static conclusion.

Master-volume persistence remains open. Direct stores to `gp+0x832 = 0x80003332` are confined to the VOL+/VOL- update paths found in the loaded AP1 code; those writers contain no direct NVRAM/save transition. This does not exclude a deferred/global persistence mechanism elsewhere.

### Speaker/digital hardware-control continuation — 2026-09-22

- Speaker channel-state contract is instruction-backed: selector 0=FRONT, 1=CENTER, 2=REAR, 3=SUBWOOFER. FRONT uses LARGE=0/SMALL=1; CENTER and REAR use LARGE=0/SMALL=1/OFF=2; SUBWOOFER uses OFF=0/ON=1. Applying SUBWOOFER sends audio action 6 and then reapplies the packed full speaker topology through action 0x17 / command family 0x2300.
- Speaker-delay controls are now tied to their runtime state slots and hardware wrapper. Control 0xD1 uses state slot 0x18 (DAT_80006828) and reapplies CENTER delay as selection-2. Control 0xD2 uses state slot 0x19 (DAT_80006829) and reapplies REAR delay as selection*3-6. Both reach audio action 0x0B, command family 0x0C00|channel, with the signed 16-bit delay in the auxiliary parameter slot.
- DIGITAL SETUP is instruction-linked into the common output-mode command path. OP MODE control 0xF9 maps option 0xFA to mode 0x20 and option 0xFB to mode 0x10. DUAL MONO control 0xFC maps STEREO/MONO L/MONO R/MIX MONO options to modes 0x90/0x91/0x92/0x93. DYNAMIC RANGE computes a 16-bit auxiliary value from its runtime state and uses generic decoder/output mode 0x80. ReapplyDigitalAndSpeakerDelayControls reapplies OP MODE, conditional DYNAMIC RANGE, DUAL MONO, then CENTER and REAR delay in one runtime reconfiguration route.
- DispatchAudioHardwareAction writes the internal SPHE audio-service command word at s6+0x4C0 (0xBFFE84C0) and auxiliary value at s6+0x4C4, then normally commits through a direct raw JAL to runtime entry 0x88001C78 with arguments (1,0,0,100000). Raw instructions are authoritative here; they also distinguish gain-table command families 0x1A00 and 0x1B00 on the relevant action branches.
- The loaded modules do not map executable/readable bytes for 0x88001C78, and the runtime gain table at 0x88012CA0 is likewise not available as ordinary module memory. Therefore the current implementation proof ends at the internal SPHE audio-service contract. It does not prove which downstream DAC/interface block, PCB trace, 4558 stage, TOSLINK/coax path or six-channel connector is driven by each command. Closing that edge requires another retained firmware/runtime provider or board-level observation; no physical routing is inferred from command semantics alone.
- Master volume remains a runtime state at 0x80003332 with mute at 0x800032B5. Narrow reference review continues to show volume adjustment/reapply paths, but no direct generic control-selection/NVRAM write from the VOL+/VOL- handlers. Persistence is still open rather than assumed absent, because several affected regions have imperfect action boundaries and helper calls still need independent validation.



### UART ROM-loader / RAM diagnostics — 2026-09-23

Implementation-level behavior recovery now covers the target SPHE UART ROM-loader path far enough to support a headless read/execute workflow:

- canonical STK analysis program is now `stk`, backed by the verified rev-8203R executable SHA-256 `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89`;
- serial framing is 8N1 at 57600 / 115200 / 230400 with recovered UART-divisor values `0x74 / 0x3A / 0x1D`;
- Boot-ROM/session handshake is `A/A`, followed by the target system/SDRAM register script and `C/C`;
- target profile is `8202 Non Share Mode`, 16-bit SDRAM bus;
- canonical embedded helper for this profile is STK VA `0x004E5960`, size `0x2878`; the earlier `0x004E4960` value belonged to a different legacy analysis copy and is invalid for canonical rev-8203R;
- `W + addr32le + value32le` and lower-case streaming `w + dword` are recovered; `R + addr32le` is confirmed in the post-`S` transition sequence but is not exposed pre-start without separate proof;
- READ mode is produced by patching the common embedded flash-service helper. For the target branch it uses memory-mapped flash at `0xA8000000`, stages data at `0x8001E000`, emits a NUL ready marker, then transfers `size32 + image` with one host flow-control byte per 16-byte block;
- standalone UART MMIO is recovered as data `0xBFFE8900`, status `0xBFFE8904`, TX-ready bit 0 and RX-ready bit 1;
- `tools/sphe_romloader.py` now implements `info`, `probe`, `write32`, `upload-ram`, `read-flash`, `run-ram` and `monitor`; `read-flash` prints SHA-256 and can enforce an expected digest;
- `tools/mips-inject/sphe_rom_uart.h` plus the standalone RAM diagnostic image provide a flash-independent execution/logging path.

The vendor SPI-write helper issues JEDEC command `0x9F`, performs chip erase and word programming, but no mandatory full-image post-write readback comparison is present in the recovered route. Flash write therefore remains intentionally unexposed until recovery/rollback is proven and post-write readback+SHA verification is mandatory.

Current validation level is implementation proof only. The remaining immediate board gate is locating/confirming the physical SPHE UART path; the known captured UART header belongs to the secondary controller. The likely SPHE UART pin candidates from reference-design evidence remain package pins 11/12 and 33/45 until continuity/execution evidence resolves them.

Debugger feasibility improved: AP1 contains a common exception frame that saves CP0 EPC and restores context through `rfe`, but a dedicated BREAK/debug route has not yet been proven.
