# Analysis status

## Current authority — 2026-10-04 firmware-reconstruction phase

This file is the current behavior-analysis status for the Sunplus audio path. Older percentages, action-count snapshots and pre-codec processor limitations are historical where they conflict with this section and `evidence/ap1-music-mode-20261002.md`.

Secondary-controller continuation authority: `docs/jieli-secondary-controller-handoff-20261004.md`; UART capture evidence: `evidence/jieli-uart-probes-20261004.md`. The exact JieLi silicon model is UNKNOWN; AC695N/BR23 is software-lineage evidence only.\n\nValidation levels remain separate:
- **implementation proof** — static/native behavior recovered from target firmware or the saved Analysis project;
- **execution proof** — the path has been observed executing;
- **board proof** — target PCB ownership/routing is physically established;
- **integration proof** — modified/rebuilt firmware has been accepted on the target with rollback/recovery available.

### Progress metrics

- AP1 current live Analysis snapshot: **3862 action nodes**, **176 custom-named action nodes (~4.56%)**. The action count increased as missing real boundaries were recovered; custom-name count is a refactor/naming metric, not audio completion. Thousands of unrelated legacy-media nodes remain in the denominator.
- Runtime current live Analysis snapshot: **35 action nodes / 13 custom-named**, with the documented loader, service-wait, input-ring and busy-wait helpers synchronized into the saved project.
- `srvdsp.bin`: **117/117 local executable words**, **9/9 action nodes**, **9/9 high-level behavior views**, **21/21 named/typed/documented DM state/config slots**. The local wrapper is closed at implementation-proof level.
- Codec-profile processor coverage: **AUX 5451/5451**, **PCM 7787/7787**, **AC-3 10339/10339**, **DTS 9651/9651** vector-seeded reachable words decoded with zero gaps.
- Working estimate for the **CPU-side audio control/loader contract only**: approximately **90–95% implementation-proof**. The denominator is source/input transitions, decoder state/profile loading, ring transport, service parameters, volume/mute, speaker topology/delay, digital controls, EQ/SRND/KEY and the common hardware-action dispatcher. It excludes physical output ownership, DSP cycle/resource budget, rebuild/repack and hardware acceptance.
- The previous `97–98%` whole-audio estimate is retired.

### Refactor authority and paused side investigation — 2026-10-05

- **Canonical semantic authority for the recovered target firmware is the saved Analysis project.** A recovered target-firmware fact is considered fully migrated only when its action/state/type/comment exists there. Markdown documentation is evidence, rationale and handoff context; replacement-source contract headers mirror confirmed semantics for code reuse but do not replace the Analysis project as the semantic source of truth.
- **Current documented-semantics transfer/refactor is closed at 100% for its defined denominator.** All already-recovered target-firmware actions/states/types/comments identified by this pass are represented in saved Analysis or explicitly classified as non-semantic/future behavior-recovery work. Unknown shared-state candidates are no longer counted as refactor debt.
- Documentation-only names, raw `FUN_*`/`DAT_*` identifiers and confirmed state meanings that are not represented in Analysis are migration debt and belong to the active refactor queue.
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

Current approximate behavior/reconstruction coverage:

| Area | Current | Active status |
|---|---:|---|
| USB host bring-up / EP0 contract | **93%** | **PAUSED at hardware boundary** — controller init, root reset, EP0 enumeration and descriptors are recovered; next meaningful proof is target execution |
| SPHE UART / ROM-loader software | **90%** | **PAUSED at hardware boundary** — software contract is recovered; physical target access/execution proof remains |
| DAC / six-channel output behavior | **90%** | **PAUSED where only board continuity/levels remain** |
| AUX / stereo ingress | **87%** | Active only through the missing SPHE-side receiver / inter-chip contract |
| Resident audio services | **93%** | Low priority unless required by replacement-source architecture |
| Clock / sample-format contract | **80%** | Active where firmware can still resolve real clock/rate families; board-only validation is deferred |
| SPHE <-> JieLi audio/control boundary | **90%** | **HIGH PRIORITY**; source-side common-mixer ALINK TX and SPHE resident capture pair 0x10/0x11 are recovered; exact physical pin ownership remains unproven |
| JieLi firmware/control domain | **45%** | **HIGH PRIORITY**; full dump/static analysis would materially increase coverage |
| DSP resources / PM/DM/cycle headroom | **55%** | **HIGH PRIORITY** |
| ECHO processing engine | **70%** | Medium priority; recover if needed for original behavior parity |
| USB device / UAC capability | **48%** | Deferred while original firmware reconstruction has larger gaps; not required for stock behavior parity |
| Front-panel SOURCE / 2.0-5.1 behavior | **93%** | Paused; remaining work is mainly board/GPIO detail |
| LED / residual front-panel ownership | **38%** | Low priority unless firmware analysis exposes its owner |
| Rebuild / repack / integrity contract | **65%** | **HIGH PRIORITY** for replacement firmware |
| Recovery / rollback software path | **70%** | Static/software work may continue; hardware acceptance remains deferred |

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