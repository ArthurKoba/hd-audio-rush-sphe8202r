# Analysis status

## Current authority — 2026-10-02 late pass

This file is the current behavior-analysis status for the Sunplus audio path. Older percentages, action-count snapshots and pre-codec processor limitations are historical where they conflict with this section and `evidence/ap1-music-mode-20261002.md`.

Validation levels remain separate:
- **implementation proof** — static/native behavior recovered from target firmware or the saved Analysis project;
- **execution proof** — the path has been observed executing;
- **board proof** — target PCB ownership/routing is physically established;
- **integration proof** — modified/rebuilt firmware has been accepted on the target with rollback/recovery available.

### Progress metrics

- AP1 current live Analysis snapshot: **3853 action nodes**, **147 non-generic/semantic names (~3.82%)** by the current naming rule, **62 forwarders**. This includes thousands of unrelated legacy-media nodes and is not audio completion.
- `srvdsp.bin`: **117/117 local executable words**, **9/9 action nodes**, **9/9 high-level behavior views**, **21/21 named/typed/documented DM state/config slots**. The local wrapper is closed at implementation-proof level.
- Codec-profile processor coverage: **AUX 5451/5451**, **PCM 7787/7787**, **AC-3 10339/10339**, **DTS 9651/9651** vector-seeded reachable words decoded with zero gaps.
- Working estimate for the **CPU-side audio control/loader contract only**: approximately **90–95% implementation-proof**. The denominator is source/input transitions, decoder state/profile loading, ring transport, service parameters, volume/mute, speaker topology/delay, digital controls, EQ/SRND/KEY and the common hardware-action dispatcher. It excludes physical output ownership, DSP cycle/resource budget, rebuild/repack and hardware acceptance.
- The previous `97–98%` whole-audio estimate is retired.

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

`SetMasterVolumeLevel` dispatches action 2. The logical hardware route is split by imperfect action boundaries: `ApplyMasterVolumeHardwareState @ 0x806FFBBC` contains the prologue and `FUN_806FFBC8` contains the main worker.

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

`drv_other:0x8077C29C` proves CENTER delay `kind=1,value=selection-2` from slot `0x80006828`, and REAR delay `kind=2,value=selection*3-6` from slot `0x80006829`. Documentation semantic alias: `ReapplyDigitalAndSpeakerDelayControls`; the saved symbol may still be generic.

## External source / AUX / S/PDIF input

State: current hardware mode `gp+0x12B`, previous mode `gp+0x12C`, external subsource `gp+0x7FA`, higher source state `gp+0x7A5`.

Source transition at `0x806FED0C`:
- unchanged mode returns early;
- modes `0..2` -> subsource 2, transient state `0x0D`, S/PDIF-input route;
- mode `3` -> subsource 1, transient state `0x0B`, AUX route;
- transitions involving AUX use `0x806FABA0` anti-pop preparation before committing the new mode.

`0x806FABA0` first applies master volume 0 and invokes the runtime busy-wait helper with outer count `0x1F4` (500 iterations, not a proved duration). A later nonzero-subsource branch performs another volume-zero step and `0x64`-iteration wait before source state `0x0A`.

Mode 3 is confirmed AUX. Modes 0..2 program distinct SPHE bit patterns and are all S/PDIF-input-side configurations, but they remain physically unnamed; do not infer optical/coax ownership.

AUX transition `0x8071E4F0`: volume 0 -> source/status refresh -> current decoder reapply -> audio-format mode 2 -> decoder state `0x40000` -> ECHO profile `(0,0)` -> decoder reapply -> `ClearMuteAndRestoreVolume` -> transient state `0x0B` -> service/transition loop.

S/PDIF-input transition `0x8071EE94`: gated by subsource 2 -> S/PDIF decoder preparation -> transient state `0x0D` -> transition loop -> restore previous downsample selection.

S/PDIF preparation `0x8071E1B0`: reapply decoder, save downsample at `gp+0x584`, temporarily apply downsample mode 1, reset/update/copy decoder status, reapply decoder, conditionally render status, restore mute/volume.

Source-state table `0x8070B4E0` dispatches states 1..9 to `0x8071E6F4, 0x8071E704, 0x8071E714, 0x8071E724, 0x8071E734, 0x8071E61C, 0x8071E744, 0x8071E61C, 0x8071E754`. States 6 and 8 deliberately share the common handler. Product-level names for every state remain open.

## Decoder audio-status block

Block `0x800022E4` is 16 bytes. `0x80700558` copies all 16 bytes; `0x80700590` writes the first word; parser `0x8070059C` consumes the hardware decoder/status word.

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

`a2` is written to `s6+0x4C4` before range validation; accepted routes stage `s6+0x4C0` then normally enter runtime `0x88001C78(1,0,0,100000)`. A `gp+0x698 & 0x800` gate can return 1 without staging a new command.

## ECHO control correction

Control ID `0x57` is confirmed **ECHO**. Its apply branch computes `index=selection-2`, stores it at `gp+0x83A`, and calls saved `ApplyEchoProfileIndex @ 0x80702C8C`.

The historical REGION name was wrong. `ApplyEchoProfileIndex` reads runtime table `0x88012CC0` and dispatches action 4. Entries: index 0 `(mode=0,aux=0)`; indices 1..7 modes `7,15,23,31,39,47,55`, aux `10000`.

Saved `ApplyEchoHardwareProfile @ 0x80702CC8` dispatches action 4 from explicit `(mode,aux)` and AUX uses it with `(0,0)`.

Other established wrappers:
- KEY accepts 1..15 and dispatches action 3 / `0x0500`;
- `ApplySpdifHardwareOutputMode` saves mode at `gp+0x17B3` and dispatches action 7 / `0x0900`;
- `ApplyDecoderOutputMode(mode,aux)` dispatches action 1 / `0x0300`;
- GM5 decoder-service slot is `0x23`; AC-3 DOWNMIX slot is `0x21`.

## Known metadata hazards

1. AP1 was rebased to `0x8067B800` after older analysis state existed. Stored high-level links may still be shifted by `+0x800`, even when the wrong target is itself a valid action node.
2. Several logical routes are split into artificial adjacent action boundaries, notably decoder profile loading and master-volume apply.
3. Raw/native transitions win whenever high-level behavior disagrees.
4. Historical `ApplyRegionCodeProfile` metadata was corrected in canonical Analysis to `ApplyEchoProfileIndex`; action 4 is ECHO.
5. Historical evidence may retain older names, but current authority and canonical Analysis use the corrected ECHO names.

## Readiness for custom firmware

Source-level replacement implementation can begin now for isolated, recovered CPU-side behavior. A complete replacement image is **not yet safe to flash or product-ready**.

Remaining gates:
1. reproduce container/module reconstruction, integrity/checksum and write path;
2. prove safe recovery/rollback on hardware;
3. finish resident runtime/backend ownership below the service mailbox and map six physical output lanes;
4. obtain DSP clock/free-cycle/free-memory budget evidence;
5. finish product-level names for remaining source-state handlers and any command families needed by the planned feature;
6. perform at least one intentional modified-firmware hardware acceptance cycle.

## Immediate continuation

1. Resolve product-level meaning of remaining `gp+0x7A5` source-state handlers.
2. Reopen saved `/runtime/rom12-runtime.bin` when a session-local runtime handle is needed and continue below the service mailbox.
3. Connect recovered command families and codec parameters to resident high-DM/backend consumers.
4. Close physical six-channel output ownership with board/runtime evidence.
5. In parallel, turn the recovered behavior contracts into maintainable replacement-source modules while rebuild/repack/recovery acceptance is completed.

Safety/provider incident reproduction belongs to `ArthurKoba/mcp-bridge` issues and is not duplicated here.
