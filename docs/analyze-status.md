# Analysis status

## Current authority — 2026-10-04 firmware-reconstruction phase

This file is the current behavior-analysis status for the Sunplus audio path. Older percentages, action-count snapshots and pre-codec processor limitations are historical where they conflict with this section and `evidence/ap1-music-mode-20261002.md`.

Secondary-controller checkpoint/handoff: `docs/jieli-secondary-controller-handoff-20261004.md`; UART capture evidence: `evidence/jieli-uart-probes-20261004.md`. The exact JieLi silicon model is UNKNOWN; AC695N/BR23 is software-lineage evidence only.

## Live authority / documentation policy — 2026-10-06

The saved Analysis project is now the only live semantic authority while behavior recovery is active. This file is a synchronized checkpoint and planning/status document, not a continuously updated mirror of every Analysis mutation.

- New detailed semantic findings are committed to saved Analysis first.
- Normal drift between Analysis and Markdown is expected and is not migration debt.
- Update this file only for major milestones, acceptance/gate changes, planning-relevant contradictions, or an explicit synchronization/materialization pass.
- Shared C contracts/source receive stable recovered semantics when they are needed by implementation, not merely because a new Analysis label exists.
- After the required recovery scope is closed, perform one dedicated materialization audit from Analysis into canonical docs and maintainable C/source, validate agreement, then preserve an immutable Analysis archive before retiring any live mutable project.

The previously completed 100% transfer/refactor checkpoint means the already-documented corpus was synchronized at that cutoff; it does **not** require future Markdown to stay lockstep with ongoing Analysis work.

Validation levels remain separate:
- **implementation proof** — static/native behavior recovered from target firmware or the saved Analysis project;
- **execution proof** — the path has been observed executing;
- **board proof** — target PCB ownership/routing is physically established;
- **integration proof** — modified/rebuilt firmware has been accepted on the target with rollback/recovery available.

### Live Analysis inventory — 2026-10-06

Object counts are inventory, not completion percentages.

| Program | Action nodes | Custom names | Named globals |
|---|---:|---:|---:|
| AP1 | 3862 | 176 | 83 |
| drv_other | 183 | 50 | 38 |
| WMA | 51 | 5 | 13 |
| CDROM | 93 | 5 | 20 |
| rom12 runtime | 35 | 13 | 5 |
| srvdsp | 9 | 9 | 26 |

Primary CPU/runtime/srvdsp total: **4233 action nodes / 258 custom names**. Two AP1 custom names are still technical `caseD_*` labels, so the current semantic-name count is **256**. This is deliberately not used as analysis coverage because thousands of AP1 nodes are unrelated DVD/media/UI code.

Across AP1/DRV/WMA/CDROM/runtime there are **159 named-global instances** representing **85 unique absolute CPU/runtime addresses** after cross-program deduplication. `srvdsp` adds 26 named DSP globals; 21 of those are confirmed DM state/config slots.

Codec-profile action inventory is tracked separately: AUX 51/15 custom, PCM 4/4, AC-3 25/24, DTS 98/4. Codec-profile naming is not a completion gate; reachable instruction coverage is.

### Analysis completion denominator — 2026-10-06

Each checklist item below is one required behavior/firmware-analysis contract. Percentages are calculated only as `closed / total`; they are not confidence estimates.

| Analysis domain | Closed / total | Coverage | Why it is not 100% |
|---|---:|---:|---|
| Sunplus CPU audio control/loader | **9 / 9** | **100%** | Closed at implementation proof. |
| Sunplus DSP target-corpus processor/decoder | **6 / 6** | **100%** | Closed for the current srvdsp + AUX/PCM/AC-3/DTS corpus. |
| Container/repack/build static contract | **5 / 5** | **100%** | Byte-exact stock roundtrip, changed-module structural repack, build ABI and loader constraints are recovered. |
| SPHE ROM-loader software contract | **4 / 4** | **100%** | Software protocol is recovered; target execution/recovery acceptance is a later validation level. |
| USB host software contract | **4 / 4** | **100%** | Controller/root reset, EP0 requests, descriptor parsing and MSC/SCSI path are recovered; hardware execution is later. |
| Resident runtime/backend semantics | **5 / 5** | **100%** | Resident input/output block transfer, mailbox acknowledgement and multiblock handoff are closed at implementation proof; physical speaker-pin ownership is board proof. |
| DSP resources (program/data memory, clock, compute headroom) | **4 / 7** | **57%** | Visible PM/DM window geometry is now closed. Remaining: occupied/free map, DSP core clock and cycle/headroom. |
| SPHE <-> JieLi integration boundary | **2 / 4** | **50%** | Exact three-wire electrical roles/pins and the separate control/status transport/framing remain open. |
| JieLi firmware/control domain | **1 / 5** | **20%** | Exact chip/flash geometry, verified dump, pi32v2 static-analysis corpus and required control/Bluetooth/audio ownership remain open. |

**Sunplus-side firmware-analysis coverage:** **37 / 40 = 93%**. This uses the first seven domains and excludes the secondary-controller domain.

**Whole-device firmware-analysis coverage:** **40 / 49 = 82%**. This includes both processors and their integration boundary.

The denominator intentionally excludes:
- hardware/board/integration acceptance;
- USB Device/UAC, which is a future feature rather than stock-behavior analysis;
- residual LED/front-panel cosmetics unless they become necessary to the replacement-firmware acceptance contract;
- exhaustive semantic naming of unrelated DVD/media/UI library code.

#### Closed-domain checklists

CPU audio control/loader 9/9:
1. source/input transitions;
2. decoder state/profile selection and loading;
3. decoder input-ring transport;
4. runtime service parameters;
5. master volume/mute;
6. speaker topology/delay;
7. S/PDIF/digital output controls;
8. EQ/SRND/KEY/ECHO control paths;
9. common hardware-action dispatcher.

DSP target-corpus 6/6:
1. `srvdsp` executable/action behavior;
2. `srvdsp` DM state/config map;
3. AUX reachable-code decode;
4. PCM reachable-code decode;
5. AC-3 reachable-code decode;
6. DTS reachable-code decode.

Container/repack/build 5/5:
1. container/module table + transform/checksum contract;
2. byte-exact no-change 1 MiB reconstruction;
3. changed-module repack/reopen/extract validation;
4. independent MIPS32-LE/o32/soft-float build ABI;
5. loader/module size and fixed-address constraints.

ROM-loader software 4/4:
1. UART framing/baud/session contract;
2. RAM-code loading/execution route;
3. memory read/write transactions;
4. flash-read + stock-recovery software path.

USB-host software 4/4:
1. controller/base initialization + root reset;
2. EP0 standard request construction;
3. configuration/interface/endpoint descriptor parsing;
4. mass-storage/SCSI class route.

#### Open-domain checklists

Resident runtime/backend 5/5 is closed at implementation proof:
1. service mailbox/acknowledgement semantics;
2. decoder input-ring transport;
3. 24-bit DSP parameter-bank access;
4. start/stop/pause/reconfigure lifecycle;
5. resident block-transfer interface: command `0x63` transfers resident -> DSP, command `0x62` transfers DSP -> resident, and the recovered AUX/PCM paths expose the common multiblock output contract. AUX GM5 uses six 32-word primary output lanes plus two additional/mirrored 32-word buses. Exact FL/FR/C/SUB/SL/SR physical pin assignment is board proof and is intentionally outside this firmware-analysis item.

DSP resources 4/7:
1. local `srvdsp` PM layout — closed;
2. local `srvdsp` DM state/config map — closed;
3. visible PM window — closed at `0x0000..0x3FFF`, 16K x 24-bit = 48 KiB for the current corpus; PCM performs real PM reads at `PM:3F4D`, and no PM overlay switching is observed;
4. visible DM window — closed at `0x0000..0x3FFF`, 16K x 16-bit = 32 KiB; current profiles write as high as `DM:3FFD`;
5. profile/resident PM/DM occupancy and genuinely free map — open; PCM reads resident/shared coefficient tables in high PM outside its loaded profile, so free PM cannot be computed as window size minus profile size;
6. DSP core clock — open; available board/service material proves the SoC input clock, not the internal audio-DSP core clock;
7. cycle/headroom budget — open and depends on the core clock plus scheduling/runtime measurements.

SPHE <-> JieLi boundary 2/4 has JieLi-side ALINK/runtime activity and the SPHE-side resident capture/AUX route established. Open: exact three-wire clock/frame/data roles/pins and the separate control/status transport/framing.

JieLi firmware/control 1/5 currently has only software-family/runtime evidence from UART. Open: exact chip/flash geometry, verified raw firmware dump, pi32v2 static analysis, and the required control/Bluetooth/audio responsibility map.

### Explicit register/action materialization checkpoint — 2026-10-06

This checkpoint was requested explicitly so ongoing register recovery does not leave semantic state only in chat. Evidence states are mandatory here: **CONFIRMED**, **LIKELY**, **UNKNOWN**, or **WITHDRAWN**. Stable constants are mirrored in `sphe_soc_contract.h` / `sphe_audio_contract.h`; uncertain items use conservative candidate names instead of pretending vendor semantics are known.

#### External-input GPIO / route action ledger

| Action / sequence | Evidence state | Current behavior contract | Materialization state |
|---|---|---|---|
| `ApplyExternalInputHardwareMode` | **CONFIRMED** | Reads external mode `0..3` and programs the confirmed GPIO output-value family: bank0 low bits plus bank4 bit15 and bank5 bit0. Exact bank0 values are `0->0x3`, `1->0x5`, `2->0x6`, `3->0x7`. | Saved semantic action already exists; GPIO constants mirrored in source. |
| Analysis action currently named `InitializeSerialAudioRuntimeFlags @ 0x88000EF4` | **CONFIRMED body / WITHDRAWN semantic name and old plate comment** | Early ROM startup sets bank4 bit3 and bank5 bit6 across GPIO families A-D, then returns. The body contains no dedicated serial-audio receiver operation. | Source name is now `SPHE_ADDR_INITIALIZE_GPIO_MATRIX_STARTUP_FLAGS`; Analysis rename/comment repair is pending worker availability. |
| ROM-called AP1 entry at `0x806D23BC` | **CONFIRMED action boundary and native sequence** | Initializes the external-input GPIO/pad matrix, applies source-mode GPIO defaults, and programs the separate `0x18xx` route/clock/pad candidate cluster. | Source name `SPHE_ADDR_INITIALIZE_EXTERNAL_INPUT_GPIO_AND_ROUTE_HARDWARE`; semantic Analysis rename/comment is pending worker availability. |
| `ReadFrontPanelSourceKeyLevel` | **CONFIRMED** | Configures the relevant shared setup bits, then returns status bit 13 from `s6+0x09F0`. Input is active-low at the higher key-state layer. | Saved semantic action + source constants. |
| `ReadFrontPanelSpatialKeyLevel` | **CONFIRMED** | Same pattern for status bit 14. | Saved semantic action + source constants. |
| dual-key chord sequence inside the higher source handler | **CONFIRMED behavior, not a separate proved action boundary** | When both SOURCE and SPATIAL readers report asserted/low, sets the front-panel inhibit state and clears external-input GPIO output-value bank0 bits `2:0`. | Keep as an inline behavior contract until a native action boundary is proved. |
| old interpretation “no audio signal -> disable RX” | **WITHDRAWN** | Raw AP1 proves this path is driven by simultaneous SOURCE+SPATIAL key state, not audio-signal loss. | Must not be reused by later analysis. |

#### GPIO/pad + synchronous-input register ledger

The generic AP1 GPIO helpers now close the ordinary-GPIO register contract at implementation proof. Pin IDs use `bank = pin >> 4`, `bit = pin & 0x0F`, and each family uses `base + bank*4`. A native input-sampling action at `0x80682700` sets the selected bit in the two GPIO control families, clears the same bit in output-enable, reads the input-value family, and restores the previous state.

| Semantic name | Address / layout | Evidence state | Proven behavior | Still unknown |
|---|---|---|---|---|
| GPIO control family A | `s6+0x14C0 + bank*4` | **CONFIRMED GPIO control family** | Generic GPIO helpers set the selected bit before ordinary GPIO access. | Exact vendor role/name relative to control family B. |
| GPIO control family B | `s6+0x0980 + bank*4` | **CONFIRMED GPIO control family** | Same bank/bit formula; generic helpers set selected bits before GPIO access. | Exact vendor role/name relative to control family A. |
| GPIO output enable | `s6+0x09A0 + bank*4` | **CONFIRMED** | Generic input helper clears the pin bit; generic output paths set it. | Vendor spelling/name only. |
| GPIO output value | `s6+0x09C0 + bank*4` | **CONFIRMED** | Generic output paths set/clear the pin bit. External-input mode writes persistent source-selection patterns here. | Physical destination of each source-select output bit. |
| GPIO input value | `s6+0x09E0 + bank*4` | **CONFIRMED** | Generic input helper reads the selected bit; SOURCE/SPATIAL sample bank4 bits13/14 here. | Vendor spelling/name only. |
| old “serial RX block at `0x09C0..0x09D4`” | GPIO output-value family | **WITHDRAWN** | Generic GPIO helpers prove this range is ordinary GPIO output state, not a standalone receiver peripheral. | Actual synchronous receiver core remains open. |

GPIO19/20/21 are therefore exactly `bank1 bits3/4/5`, combined mask `0x38`. The fixed boot initializer touches second-bank bits10..12 (`0x1C00`) in the ordinary GPIO matrix, not bits3..5. Runtime-configured generic GPIO pin IDs recovered from ROM include `0x43`, `0x4A`, `0x4E`, `0x56`; the startup pin-state set does not assign `0x13/0x14/0x15`. This is **static negative evidence**: ordinary GPIO code does not prove ownership of the provisional three audio nets, while an alternate peripheral function may bypass ordinary GPIO OE/OUT programming.

External-input mode writes are now classified as **CONFIRMED source-selection GPIO behavior**, not receiver-format programming: mode `0` -> bank0 output bits `0x3`, mode `1` -> `0x5`, mode `2` -> `0x6`, mode `3/AUX` -> `0x7`; bank4 bit15 is set for modes `0/1` and clear for `2/3`; bank5 bit0 is clear for `0/3` and set for `1/2`.

The ROM-called initializer also configures `s6+0x184C`, `+0x186C`, `+0x1870`, `+0x187C` and shared `+0x1848`. Ownership analysis has excluded nearby `0x1800` (USB-related) and `0x1834` (broader mode/system state) from the synchronous-audio candidate set. The four AP1-only registers remain **LIKELY synchronous-audio route/clock/pad candidates**; `0x1848` remains shared system route state. Exact writes are named in `sphe_soc_contract.h`.

No `drv_other`, WMA, or CDROM access to the four AP1-only candidate registers was found. Physical GPIO19/20/21 ownership and DATA/BCLK/LRCLK assignment remain **UNKNOWN**.

#### Shared DSP resident-state materialization

| Semantic item | Evidence state | Proven behavior |
|---|---|---|
| `SPHE_RESIDENT_DM_READY_FLAG` (`DM:3F25`) | **CONFIRMED** | Repeated codec-profile paths read it, compute `value-1`, and loop while nonzero; accepted ready/completion value is `1`. |
| `SPHE_RESIDENT_DM_REQUEST_PENDING` (`DM:3F26`) | **CONFIRMED** | Common helper writes `1`; poll paths test the value against zero and wait until it is cleared. |
| `SPHE_RESIDENT_DM_REQUEST_VALUE` (`DM:3F27`) | **CONFIRMED** | Common helper writes the caller value before asserting `DM:3F26=1`. Identical four-instruction helper exists in AUX/PCM/AC-3/DTS/fallback. |
| PCM shared PM setup sources `3F1A/3F4C/3F4D/3DB3` | **CONFIRMED reads / UNKNOWN table identity** | PCM loads these addresses through `I4`, performs PM reads, and copies results into local setup DM. They prove resident/shared PM occupancy outside the PCM profile image. |
| common direct high-DM footprint | **CONFIRMED lower-bound occupancy** | Five decoded profiles share 79 direct-access addresses in `DM:3C00..3FFF`; 85 direct DM addresses are common overall. |
| “unreferenced PM/DM is free” | **UNKNOWN / prohibited inference** | Resident/shared content exists outside individual profile images, so free space cannot be computed as `window size - profile size`. |

The reproducible offline scan artifacts are retained in the durable `audio-profile-evidence-20261002` workspace (`scan_profile_occupancy.py`, `occupancy-lower-bound.json`, `scan_resident_shared_state.py`, `resident-shared-state.json`). They are supporting evidence, not a second semantic authority.

Closed domains stay closed unless a real contradiction appears. Do not reopen them merely to increase naming coverage.

### Refactor authority and paused side investigation### Refactor authority and paused side investigation — 2026-10-05

- **Canonical semantic authority for the recovered target firmware is the saved Analysis project.** A recovered target-firmware fact is considered fully migrated only when its action/state/type/comment exists there. Markdown documentation is evidence, rationale and handoff context; replacement-source contract headers mirror confirmed semantics for code reuse but do not replace the Analysis project as the semantic source of truth.
- **Current documented-semantics transfer/refactor is closed at 100% for its defined denominator.** All already-recovered target-firmware actions/states/types/comments identified by this pass are represented in saved Analysis or explicitly classified as non-semantic/future behavior-recovery work. Unknown shared-state candidates are no longer counted as refactor debt.
- At the completed refactor checkpoint, documentation-only semantics were reconciled into Analysis. From this point forward, newer Analysis-only findings are expected during active recovery and are not documentation/refactor debt until an explicit materialization pass.
- The recent shared-media `$gp` scan is **paused as an incomplete side investigation**, but the already-closed state package from that pass is now transferred into the saved Analysis project. Shared media labels/comments are synchronized for AP1 **11/11**, `drv_other` **11/11**, CDROM **9/9**, and WMA **8/8** applicable states/callback slots. Unresolved value meanings and new candidates remain outside the active refactor denominator.
- Do not continue broad unknown-shared-state discovery until the already-understood documentation/source vocabulary has been reconciled into Analysis. New reverse work is allowed only when it is necessary to disambiguate an already-known item being migrated.

### Migration debt exposed by the refactor — 2026-10-05

The previously exposed migration items are now either reconciled in saved Analysis or explicitly deferred as future behavior-recovery work. No already-documented semantic item remains blocked in the active transfer/refactor denominator.

- MUSIC MODE table metadata is reconciled: `audio_preset_menu_page_table @ 0x8070B35C` is labeled/documented and `g_abSevenBandEqFixedPresetBank @ 0x8070B388` is typed as 35 bytes (5 x 7). The misleading historical primary symbol `seven_band_eq_preset_bank @ 0x8070B37A` has been removed; the remaining `eq_preset_index_arithmetic_origin` label records that address only as the index-arithmetic origin inside the preceding page table.
- Runtime GP restore metadata is reconciled in the saved project: `g_pRuntimeGpRestoreWord @ 0x88012200` is the confirmed restore pointer and is fully documented. Historical shifted address `0x88012A00` no longer carries the stale symbol and is explicitly annotated as known-bad.
- External-input split continuation `ContinueExternalInputSourceTransition @ 0x806FED18` is now named and saved as the continuation of `ApplyExternalInputSourceTransition @ 0x806FED0C`; its plate comment keeps the split-boundary caveat explicit.
- DSP parameter-write wrapper metadata is reconciled. `SetDspParameterWord24ViaRuntime @ 0x807028D0` now covers the complete 32-byte prologue/call/epilogue through `0x807028EF`, has prototype `void (uint index, uint value)`, and forwards to runtime `SetDspParameterWord24 @ 0x88001358`. The stale split action at `0x807028D4` is removed.
- Shared-media runtime candidates produced by the paused GP scan remain a later behavior-recovery queue unless their meaning was already closed during the refactor. The already-closed shared-state package is no longer migration debt. The two previously tooling-blocked filter implementations are now installed/named in Analysis as `FilterMediaStateForContext @ 0x806E45D0` and `IdentityMediaStateFilter @ 0x806F4938`.

### Audio vocabulary/refactor checkpoint — 2026-10-05

- Shared media-state transfer checkpoint: the documented stream-buffer base/end/cursor, media-state word, trick-play state, runtime flags/substate/mode and applicable continuation/filter callback slots are labeled and commented in every primary MIPS module that references them. This is transfer of already-recovered semantics, not renewed behavior recovery.
- Final documented-action synchronization audit is closed for the established semantic map. The media-filter actions, external-input continuation and DSP parameter-write wrapper are now saved under semantic names with their repaired boundaries. No known documented target action remains intentionally generic because of migration debt.
- A doc-only absolute-state/address audit now leaves only intentionally unresolved or non-semantic locations: the known-bad shifted runtime address `0x88012A00`, broad context pointer `0x8000343C`, two GP-relative addresses with no recovered role beyond address equivalence, and reset-only state words without a closed semantic identity. These are not missing transfer items.
- The replacement-source audio/control layer now uses shared canonical contracts instead of local magic-value copies: `sphe_audio_contract.h`, `sphe_control_protocol.h` and `sphe_soc_contract.h`.
- Live Analysis vocabulary is shared across AP1, `drv_other`, WMA and CDROM where the same recovered state is actually shared. Current `drv_other` snapshot: **183 action nodes / 50 custom-named**.
- New cross-module state recovered through the refactor: `SPHE_STATE_MEDIA_STATE_WORD @ 0x80003254`, with **148 AP1**, **21 CDROM** and **2 drv_other** direct GP-relative references in the current scanner. Low 14 bits carry the media code; high bits are transition flags.
- Persistent state is now modeled as namespace + byte offsets + sizes rather than unrelated record IDs. Namespace `0xA0` covers the recovered firmware signature, 65-byte control-selection block, checksum, auxiliary control state, external-input mode and one still-unmapped block at offset `0x102`.
- Recovered action boundaries added during this pass include `ReadPersistentRecord`, `WritePersistentRecord`, `HandlePlaybackStatusSourceState` and `HandleMic1LevelIncrease`; adjacent generic actions were renamed only when their native behavior contract closed. `DispatchSpecialControlSelection` is now installed at its previously blocked 640-byte boundary; unknown special control IDs remain explicitly unnamed.
- `SPHE_STATE_AUDIO_PRESET_WORKING_VALUE` (`0x80002B22`) was corrected from the too-narrow historical name `CustomEqBandGainCode` to `AudioPresetWorkingValue`: it is a general MUSIC MODE working value and acts as an EQ-band gain code only inside USER EQ editing.
- Runtime RAM addresses without backing data blocks are not fabricated as typed data units. Those are represented through canonical labels/comments plus the shared C enum/address vocabulary until the project contains a real RAM backing block.


## Current project stage — firmware reconstruction first

The active stage is **maximum firmware reconstruction without new board work**. Static/native analysis, source-level behavior recovery, firmware-domain mapping and rebuild understanding take priority over hardware acceptance.

A direction that has reached a hardware-only boundary is **paused**, not treated as unfinished priority work. It is resumed only when:
- static evidence exposes a new meaningful branch;
- another firmware-domain dependency requires it; or
- the project deliberately enters hardware-acceptance phase.

Current analysis progress is defined by the exact acceptance ledger above. Previous per-area confidence estimates are retired because they mixed implementation proof, hardware proof, future features and subjective confidence.

Hardware-gated items are tracked as later validation work and do not reduce firmware-analysis coverage. In particular, target USB execution, physical SPHE UART access, six-channel continuity/levels and rebuilt-image hardware acceptance belong to execution/board/integration proof, not the current analysis denominator.

### Active priority order
### Active priority order

1. **Close the provisional three-wire JieLi -> SPHE audio ingress.** Record the exact three PCB nets, determine their clock/frame/data roles, and identify the SPHE receiver contract. Current evidence supports a permanently connected synchronous stereo stream into the dedicated AUX backend.
2. **Treat JieLi firmware acquisition as secondary unless the three-wire contract remains ambiguous.** Preserve/dump it when practical, but do not block SPHE-side replacement work on exact JieLi SKU identification.
3. **Finish firmware-only DSP resource recovery.** Establish PM/DM ownership, resident allocation, cycle/headroom constraints and the limits relevant to a replacement implementation.
4. **Finish replacement-image construction.** Reproduce module/container rebuild, packing, integrity/checksum rules and the software side of rollback/recovery.
5. **Close remaining firmware-only Sunplus gaps.** Finish clock/sample-rate semantics, backend ownership and any still-unexplained live source/control routes that materially affect original behavior.
6. **Only after the firmware reconstruction stage is exhausted, enter hardware acceptance.** Then run the prepared USB RAM probe, prove SPHE UART access, close board continuity/output levels and validate a rebuilt image.

Do **not** spend analysis time increasing already-high percentages by re-proving established behavior. Closed or hardware-gated areas stay frozen unless they become dependencies of an active gap.

## Toolchain and canonical project

- Canonical project: `sphe8202r_decoder_p25d80`.
- AP1: `/modules_mipsle/ap1.bin`, MIPS32 LE, base `0x8067B800`, shared `$gp=0x80002B00`.
- Runtime reconstruction: `/runtime/rom12-runtime.bin`, base `0x88000000`, saved project file version 21. Open-program handles are session-local and may need reacquisition after worker restart.
- DSP wrapper: `/dsp_sunplus/srvdsp.bin`, `SunplusSPHEAudioDSP:BE:16:default`, PM base `0x1800`.
- Codec programs: `/dsp_sunplus/codec_profiles/{aux,pcm,ac3,dts}-profile.bin`.
- Deployed processor implementation: `ArthurKoba/ghidra-mcp` main commit `5570d8c` at this checkpoint; production Analysis smoke confirmed the extension after deployment.

## Sunplus audio-DSP processor state

The processor-model blocker is closed for the current target corpus.

Confirmed model properties:
- fixed 24-bit big-endian instruction words;
- PM word-addressing with `wordsize=3` and `alignment=3`;
- separate PM/DM/IO spaces with 16-bit DM/IO modeled for observed forms;
- generic codec flow separated from `srvdsp`-only resident-handoff context;
- RTI kept distinct from RTS through explicit status-restoration semantics;
- real CNTR-controlled `DO PM:186C UNTIL CE` for the proven wrapper sequence;
- reachable arithmetic/MAC, PM/DM memory, shifter, stack/mode, direct/indirect flow and register-move forms required by AUX/PCM/AC-3/DTS are implemented.

This is target-corpus completeness, not a full ADSP-218x compatibility claim and not evidence of Sunplus DSP clock, cycle budget, total PM/DM capacity or peripheral routing.

## srvdsp current closed contract

`srvdsp.bin` was audited again after the processor extension. All nine action boundaries and native routes remained consistent. All 21 proven DM state/config slots are named, typed and documented. Two high-level presentation artifacts around the weighted path and `DO ... UNTIL CE` are annotated; native low-level behavior is authoritative.

Local actions:
- `InitializeAndDelegateSrvdsp`;
- `ProcessLevelWindowExtrema`;
- `ProcessWeightedDspAccumulation`;
- `ClearDspDataWindow`;
- `ProcessCountdownRouting`;
- `ProcessThresholdStateAndIo`;
- `SetThresholdStateFromM0AndDelegate`;
- `HandleConditionalReturnOrDelegate`;
- `SetStoredArAndClearState`.

PM data structure:
- `PM:1895` default/reserved vector landing;
- `PM:1896..1905` parameter/coefficient bank;
- `PM:1906..1939` four 13-word preset records;
- `PM:193E..195C` exact 31-point Q13 sine window;
- `PM:195F..1975` exact 23-point Q13 sine window.

The sine tables are not FIR kernels. Exact resident consumer/effect semantics remain outside the local wrapper.

## Decoder profile load route

Saved semantic entry points:
- `SelectDecoderProfileByStateMask @ 0x80700410`;
- `LoadDecoderDspProfile @ 0x807002FC`;
- `ValidateDecoderProfileInputRingCapacity @ 0x80700168`.

Instruction-backed route:
1. Select descriptor by the least-significant set bit of the requested decoder-state mask; fallback index is 8.
2. Descriptor layout: packed-source pointer `+0`; field A `+4/+5`; field B `+6/+7`; field C `+8/+9`.
3. Derive page/bank selectors `0xF8`, `0xF8+A`, `0xF8+A+C`.
4. Internal worker `0x807002AC..0x807002F8` writes them into service state (`s6+0x4B0/0x4B8/0x4B4`) and runtime selectors (`gp+0x17AC/0x17AE/0x17B0`) and clears related service fields.
5. Runtime decoder-service initialization is **real target `0x88001584`**.
6. Validate descriptor capacity against configured input-ring capacity.
7. Packed profile transfer is **real target `0x88001AF8`** to `0xA0000000 + (u16[gp+0x17AC] << 10)`.

Known stale metadata: high-level views may show the runtime calls shifted by `+0x800` (`0x88001D84`, `0x880022F8`) and may show `SelectDecoderProfileByStateMask` calling `0x80700AFC` instead of raw `jal 0x807002FC`. Those displayed targets are not authoritative.

`ValidateDecoderProfileInputRingCapacity` has 57 native operations. For decoder states `0x8000` and `0x40000`, descriptor capacity is incremented by 3 before `<<10`; the result is compared with `u16[gp+0x71E]`. The old high-level extra-call interpretation on that branch is withdrawn.

## Decoder input ring and runtime service contract

The configured window is a CPU-fed input ring:
- base = `0x80000000 + (u16[gp+0x17AE] << 10)`;
- capacity bytes = `u16[gp+0x71E]`;
- CPU producer byte cursor = `u16[gp+0x730]`;
- service consumer byte cursor = `3 * u32[s6+0x4CC]`;
- producer position is published in three-byte units through `s6+0x4C8`.

`GetDecoderInputRingFreeBytes @ 0x88001CD0` and the adjacent queued-byte calculation establish ring arithmetic. This is transport capacity, not total/free DSP program memory.

`WaitForAudioServiceConditions @ 0x88001C78` is analyzable in the saved runtime program. Dispatcher use `(1,0,0,100000)` makes `100000` a poll-count budget, not a proved time unit. A state-mask gate can return success without issuing a command. Command acknowledgement and requested final state are separate.

## MUSIC MODE / EQ / SRND

Current mapping:
- page 0 SRND: OFF / CONCERT / CHURCH / PASSIVE / WIDE / LIVE;
- page 1 EQ: STANDARD / CLASSIC / ROCK / JAZZ / POP / USER;
- page 2 BAND;
- page 3 KEY.

There are five fixed EQ curves, not seven. The real fixed bank starts at `0x8070B388`; selection 7 is the runtime USER curve. Stored code 13 renders as 0 dB. Non-OFF SRND and non-STANDARD EQ are mutually exclusive by factory policy; this is not a silicon limitation and is distinct from GM5.

Seven-band payload bytes are written to selected DSP-visible bank indices 7..13 through runtime `SetDspParameterWord24 @ 0x88001358`, then action 8/value `0x10` stages command `0x0A10`. These indices are selected-bank addresses, not decoder-service vector IDs.

## Master volume / mute

`SetMasterVolumeLevel` dispatches action 2. The logical hardware route is split by imperfect action boundaries: `ApplyMasterVolumeHardwareState @ 0x806FFBBC` contains the prologue and the main worker continues at the adjacent action boundary `0x806FFBC8`.

Confirmed worker contract:
- master mute is separate state `gp+0x7B5`, not just level zero;
- level indexes runtime gain table `0x88012CA0`;
- staged command is `0x1100 | gainByte` at `s6+0x4C0`;
- cached gain byte is `gp+0x478`;
- `s6+0x4C4` carries special/mute state `0`, `1`, or `0xFFFF` according to route;
- `drv_other:0x8077C554` is exactly `return 0`, so the branch that requires return 1 is unreachable in this firmware revision.

## Speaker topology and delays

`SetSpeakerChannelState` mapping:
- selector 0 -> FRONT at `gp+0x827`;
- selector 1 -> CENTER at `gp+0x7DC`;
- selector 2 -> REAR at `gp+0x80E`;
- selector 3 -> SUBWOOFER at `gp+0x7D6`.

`ApplySpeakerConfiguration` packs `FRONT<<12 | CENTER<<8 | REAR<<4 | derived_low_nibble`, stores it at `gp+0x550`, then dispatches action `0x17` with topology in the auxiliary value. Service resolver ID `0x21` participates in policy and can force CENTER/REAR working values to 2.

`ApplySubwooferState` sends action 6 then immediately reapplies full topology.

`ApplySpeakerDelayParameter(kind,value)` is action `0x0B`, command family `0x0C00|kind`, delay value in the 16-bit auxiliary field.

`drv_other:0x8077C29C` proves CENTER delay `kind=1,value=selection-2` from `SPHE_STATE_SPEAKER_CENTER_DELAY_SELECTION_SLOT`, and REAR delay `kind=2,value=selection*3-6` from `SPHE_STATE_SPEAKER_REAR_DELAY_SELECTION_SLOT`. The saved Analysis action is now named `ReapplyDigitalAndSpeakerDelayControls`.

## External source / AUX / S/PDIF input

State: current hardware mode `gp+0x12B`, previous mode `gp+0x12C`, external subsource `gp+0x7FA`, higher source state `gp+0x7A5`.

Source transition at `0x806FED0C`:
- unchanged mode returns early;
- modes `0..2` -> subsource 2, transient state `0x0D`, S/PDIF-input route;
- mode `3` -> subsource 1, transient state `0x0B`, AUX route;
- transitions involving AUX use `0x806FABA0` anti-pop preparation before committing the new mode.

`0x806FABA0` first applies master volume 0 and invokes the runtime busy-wait helper with outer count `0x1F4` (500 iterations, not a proved duration). A later nonzero-subsource branch performs another volume-zero step and `0x64`-iteration wait before source state `0x0A`.

Mode 3 is confirmed AUX. Modes 0..2 program distinct SPHE bit patterns and are all S/PDIF-input-side configurations, but they remain physically unnamed; do not infer optical/coax ownership.

`HandleAuxInputTransition @ 0x8071E4F0`: volume 0 -> source/status refresh -> current decoder reapply -> audio-format mode 2 -> decoder state `0x40000` -> ECHO profile `(0,0)` -> decoder reapply -> `ClearMuteAndRestoreVolume` -> transient state `0x0B` -> service/transition loop.

`HandleSpdifInputTransition @ 0x8071EE94`: gated by subsource 2 -> S/PDIF decoder preparation -> transient state `0x0D` -> transition loop -> restore previous downsample selection.

`PrepareSpdifInputDecoder @ 0x8071E1B0`: reapply decoder, save downsample at `gp+0x584`, temporarily apply downsample mode 1, reset/update/copy decoder status, reapply decoder, conditionally render status, restore mute/volume.

Source-state table `0x8070B4E0` dispatches states 1..9 to `0x8071E6F4, 0x8071E704, 0x8071E714, 0x8071E724, 0x8071E734, 0x8071E61C, 0x8071E744, 0x8071E61C, 0x8071E754`. States 6 and 8 deliberately share the common handler. Product-level names for every state remain open.

## Decoder audio-status block

`SPHE_STATE_DECODER_AUDIO_STATUS` is a 16-byte block. `0x80700558` copies all 16 bytes; `0x80700590` writes the first word; parser `0x8070059C` consumes the hardware decoder/status word.

Confirmed fields:
- bits 2:0 select decoder type/path: 0=PCM, 1=AC-3, 2/3=DTS-family; values >=4 use fallback/reconfiguration;
- bits 5:3 are written to status block `+8`;
- bits 15:8 index an additional status table;
- type changes can mute, stop, change decoder state/profile and restart the pipeline.

## Common audio-action dispatcher

`DispatchAudioHardwareAction @ 0x806FFD1C` action IDs `0..26`:

| ID | Staged family / behavior |
|---:|---|
| 0 | `0x0200|value`, sub-value validation |
| 1 | `0x0300|value`, auxiliary forwarded |
| 2 | master-volume worker -> `0x1100|gainByte` |
| 3 | `0x0500|value` |
| 4 | `0x0600|value` — ECHO hardware profile |
| 5 | `0x0700|value` — SRND |
| 6 | `0x0800|value` — SUBWOOFER |
| 7 | `0x0900|value`, target-specific normalization |
| 8 | `0x0A00|value` |
| 9 | `0x0D00|value` |
| 10 | `0x1200|table2[index]`, aux `0xFFFF` for nonzero index |
| 11 | `0x0C00|value`, delay in aux |
| 12–13 | invalid/default |
| 14 | `0x0E00|value` — packed audio-mode control |
| 15 | gain-table family `0x1A00` |
| 16 | gain-table family `0x1B00` |
| 17 | gain-table family `0x1C00` |
| 18 | gain-table family `0x1D00` |
| 19 | gain-table family `0x1500` |
| 20 | gain-table family `0x1E00` |
| 21 | constant `0x0B01` |
| 22 | `0x1700|table2[0]` |
| 23 | `0x2300|value` — speaker topology |
| 24 | constant `0x2700` |
| 25 | `0x2800|value` |
| 26 | constant `0x2900` |

`a2` is written to `s6+0x4C4` before range validation; accepted routes stage `s6+0x4C0` then normally enter runtime `0x8