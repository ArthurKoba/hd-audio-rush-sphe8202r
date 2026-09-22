# Firmware

## Raw SPI dump

`firmware/P25D80SH@SOP8.BIN` is a **raw byte-for-byte dump** of the Puya P25D80SH SPI NOR from the target board.

- size: 1,048,576 bytes
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`

It is a Sunplus firmware container, not one flat CPU executable. Do not modify the canonical dump or extracted modules in place.

## Sunplus STK

Tool archive: `tools/STK_0.2.3.zip`.

The rev-8203R build successfully opens the dump and extracts the firmware modules. Observed metadata:
- version: `02R-D-02`;
- ROM required: `1M`;
- customer ID: `SUNPLUS`;
- displayed SoC profile: `SPHE8203R`;
- SDRAM: `32M`, 16-bit, non-shared;
- Host USB 2.0: supported;
- module slots: 18;
- password: `5168`.

The displayed `SPHE8203R` conflicts with the physical `SPHE8202R` package marking. Keep this contradiction open.

## Extracted modules

The already-extracted files are stored directly in `firmware/modules/`; there is intentionally no duplicate tar archive.

CPU/code classification:
- `ap1.bin` — main MIPS32 LE application;
- `drv_other.bin` — MIPS32 LE driver/auxiliary code;
- `cdrom.bin` — MIPS32 LE module;
- `wma.bin` — MIPS32 LE WMA-related module;
- `rom12.bin` — container/config/resource-like, not a linear MIPS image;
- `jpeg.bin` — data/tables;
- `iop.bin`, `iop_rst.bin`, `srvdsp.bin` — auxiliary microcode/specialized image candidates.

Zero-length module slots are retained because STK produced an 18-slot set. Exact sizes and SHA-256 values are kept in the root `README.md`.

## Ghidra and address model

Canonical project: `sphe8202r_decoder_p25d80`. CPU programs live under `/modules_mipsle/`; the existing STK tool analysis lives at `/tools/stk.exe`. Earlier flat executable imports of the 1 MiB container have been removed.

Correct workflow: preserve the container, use extracted CPU modules as `MIPS:LE:32:default`, establish placement and shared GP, and validate instruction flow before relying on decompilation.

### Current map and reopened gate

`reverse/modules.csv` now distinguishes the AP1 static candidate from completed analysis:

| Module | Working base | Validation state |
|---|---|---|
| ap1 | `0x8067B800` | Corrected base applied in canonical Ghidra; function-boundary and stale-reference cleanup still pending |
| wma | `0x8073F000` | Established base; stale direct-flow refs remain |
| cdrom | `0x8074C800` | Established base; stale direct-flow refs remain |
| drv_other | `0x80775800` | Established base; stale direct-flow refs remain |

The former claim that AP1 `0x8067B000` was confirmed is withdrawn. The old provisional `cdrom=0x80754000` and `drv_other=0x80782000` candidates remain rejected. SCORE7 is not the active ISA or a project dependency.

### AP1 +0x800 contradiction: reproducible target evidence

The 684,192 original AP1 bytes in Ghidra were hashed again and match the canonical module checksum in README. The following observations concern the unchanged bytes, not a patched firmware:

| Evidence | File offset / instruction | Observation |
|---|---|---|
| Initial delay call | `ap1+0x78`, word `0x0C19EE00` | Encodes `jal 0x8067B800`, after loading `a0=10`; file offset zero is an `a0` countdown/delay leaf. Candidate base resolves the call to that leaf. |
| Cross-module entry | `cdrom+0x38`, word `0x0C1C0691` | Encodes `jal 0x80701A44`. With candidate AP1 base, this maps to `ap1+0x86244`, a routine starting with `lhu a1,0x744(gp)`, stack allocation and saved registers. At the old base the same target lands inside unrelated-looking partial state/epilogue code. |
| Absolute/relative join | `ap1+0x8632C` and `ap1+0x86350` | The absolute jump targets `0x80701AFC`; a nearby relative branch targets file offset `0x862FC`. Base `0x8067B800` makes both enter the same MMIO-update/return block. |
| String pointer | pointer at `ap1+0x615D0`, string at `ap1+0x5EDC8` | The stored pointer agrees with `0x8067B800 + 0x5EDC8` for `SPDIF/OFF`, not the old base. RAW/PCM pointer tables provide additional supporting matches. |

The cross-module entry offset is **`0x86244`**, correcting `0x85A44` in an earlier issue comment. Individual literal-pointer matches alone are not proof. Independent code evidence supports the candidate, but a corrected Ghidra model, remaining layout/loader checks and recovered function boundaries are still required.

Further raw-pointer checks:
- corrected translation table base is `0x806DCD88` (file `+0x61588`) with language stride `0x404 = 257*4`; raw item `113` is `AUDIO OUT`, item `117` is `SPDIF/RAW`, item `119` is `SPDIF/PCM`;
- file `+0x615D0` stores `0x806DA5C8`; with base `0x8067B800` this points exactly to `SPDIF/OFF` at file `+0x5EDC8`, while `0x8067B000` points into unrelated bytes;
- `SPDIF/RAW`/`SPDIF/PCM` candidate addresses `0x806DA8AC/0x806DA8B8` are referenced repeatedly from localized pointer blocks at file offsets `+0x6175C/+0x61764`, `+0x61F64/+0x61F6C`, `+0x62368/+0x62370`, `+0x6276C/+0x62774`, and `+0x62B70/+0x62B78`;
- the old Ghidra interpretation using file `+0x61180` (`0x806DA0AC/0x806DA0B8`) and outer file `+0x62964` is invalid under the candidate placement: those targets resolve into unrelated language-text data. Any prior RAW/PCM menu-setter conclusions based on that old address chain are withdrawn pending corrected placement/relocation analysis.

AP1 is now rebased to `0x8067B800` in the canonical Ghidra project. This corrects placement but does not automatically repair pre-existing function boundaries or stale references; current symbols/callers still require evidence-level validation.

### Stale direct-flow reference audit

The read-only audit derives each currently defined MIPS J/JAL destination from its raw word:

`target = ((PC + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)`.

Snapshot from 2026-09-21:

| Program | Instructions scanned | Defined J/JAL | Wrong stored flow refs | Error delta |
|---|---:|---:|---:|---|
| ap1 | 95,906 | 8,910 | 0 | none in this audit scope |
| wma | 10,225 | 742 | 2 | `+0x0073F000` |
| cdrom | 6,944 | 660 | 17 | `+0x0074C800` |
| drv_other | 12,184 | 962 | 24 | `+0x00775800` |

No missing flow references were found in that 2026-09-21 audit scope. All 43 wrong references in `wma/cdrom/drv_other` had source `DEFAULT`; their deltas match the low parts of their module bases, consistent with stale references after rebasing. The AP1 `0` row is now historical only: targeted raw checks on 2026-09-22 found at least four AP1 stored flow refs shifted by exactly `+0x800`, including `0x8071EC9C` raw `j 0x8071EC4C` vs stored `0x8071F44C`, `0x8071F548` raw `jal 0x806ED604` vs stored `0x806EDE04`, `0x8071F550` raw `j 0x8071F50C` vs stored `0x8071FD0C`, and `0x8067D514` raw `jal 0x806ED604` vs stored `0x806EDE04`. Therefore critical AP1 caller/decompiler edges must also be checked against raw instructions. No broad AP1 repair is claimed.

Examples:
- CDROM `0x8074C838`: encoded target `0x80701A44`, stored target `0x80E4E244`.
- CDROM `0x8074C850`: encoded target `0x807017A8`, stored target `0x80E4DFA8`.
- CDROM `0x8074CB7C`: encoded target `0x8074C868`, stored target `0x80E99068`. This hides the initializer's call to `DetectCdromStreamType` from normal caller queries.
- WMA `0x8073F090` and `0x8073F0A4`: encoded `memset` target `0x80783F64`, stored `0x80EC2F64`.

`tools/ghidra/RepairMipsDirectFlow.java` preserves a guarded repair implementation at commit `3688a523`. It defaults to audit, checks exact module hashes/bases and expected mismatch counts, and proposes only reference/comment changes inside a transaction. It does not patch bytes, rebase or run broad analysis. Its application was blocked by the tool safety layer: **no compile/application validation or repaired-reference count is claimed**. Do not bypass the block or treat source presence as completion. A later authorized execution must repeat the audit because shared project state can change.

### Shared GP and helper contracts

The shared GP remains `$gp = 0x80002B00`, independently supported by WMA absolute/gp-relative pairs:
- `0x800035D8 = gp + 0xAD8`;
- `0x80003684 = gp + 0xB84`.

AP1 instruction pair `0x806D96F8: lui gp,0x8801` / `0x806D96FC: lw gp,0x2200(gp)` proves the runtime GP restore word is at absolute `0x88012200`. The canonical Ghidra project currently also contains a stale auxiliary block `runtime_gp_slot` at `0x88012A00`, shifted by the AP1 rebase; an attempt to create a corrected replacement block was blocked by the tool safety layer. Treat `0x88012200` as the instruction-backed address and the shifted block as known-bad metadata.

Cross-module helpers identified in `drv_other.bin`:
- `0x80783F08` — byte-wise `memcmp`;
- `0x80783F3C` — byte-wise `memcpy`;
- `0x80783F64` — byte-wise `memset`.

## Firmware anchors and audio state

### Command mailbox path

Instruction-level AP1 analysis now identifies a paired command mailbox interface:
- `WriteCommandMailboxByte` at `0x8069B070`: writes a 16-bit key to `s6+0xE80`, byte value to `s6+0xE84`, polls handshake bit `0x8000`, then performs the `0x454B` completion transaction;
- `ReadCommandMailboxByte` at `0x8069B268`: writes the key to `s6+0xE80`, polls `s6+0xE88` bit `0x8000`, and returns the low response byte;
- raw initialization body beginning at `0x8069D4F8` programs `0x4627 -> 0x75` and `0x4628 -> 0x77`; identical pairs recur in four initialization clusters;
- helper `0x8069E1A4(param1,param2)` writes mailbox key `0x4000 | param1`. One runtime control-flow branch at `0x80684AA0..0x80684940` therefore issues exact transaction `0x401A <- 0x75`.

`0x75` is the confirmed translation-table item ID for `SPDIF/RAW`; `0x77` is the item ID for `SPDIF/PCM`. The standalone mailbox key `0x401A` remains semantically unresolved, but the higher-level OFF/RAW/PCM setter contract is now recovered independently through the control-descriptor/dispatcher path.

### S/PDIF OFF / RAW / PCM control contract

`ResolveControlIdToGroupSlot(0x71)` resolves S/PDIF output control to group 2 / slot 1. The descriptor at `0x80707FA3` is 13 bytes: `03 71 12 75 77 00 00 00 00 00 00 0B 00`. A working analytical type `ControlOptionDescriptor` is applied there; proven fields are packed ID/meta, control-ID low byte, eight option-ID bytes, state-slot byte at `+0x0B`, and two still-unknown metadata bytes.

The corrected translation table identifies descriptor options:
- `0x12` -> `SPDIF/OFF`;
- `0x75` -> `SPDIF/RAW`;
- `0x77` -> `SPDIF/PCM`.

`DispatchControlOption` at `0x80776210` masks the first argument as control ID and second as option ID. Its jump-table entry for control `0x71` calls `ApplySpdifOutputOption` at `0x807759E0` with that option ID. Instruction/decompiler behavior in `ApplySpdifOutputOption` is explicit: RAW `0x75` selects internal mode 2, PCM `0x77` selects internal mode 1, and OFF `0x12` follows the clear/reconfigure path. `IsSpdifPcmSelected` at `0x8077C21C` returns whether the currently selected descriptor option is `0x77`.

The descriptor's state-slot field is `0x0B`, mapping its current option index to `DAT_80006810[0x0B] = 0x8000681B`. `LoadControlSelectionsFromStateSlots` (`0x80777C0C`) copies indexed state slots into the generic selection table at `0x800066B0 + group*9 + slot`; `SaveControlSelectionsToStateSlots` (`0x80777C94`) performs the inverse copy. This closes the static state/persistence path for OFF/RAW/PCM selection. It does **not** by itself prove physical PCB routing or hardware-observed output behavior.

The interactive commit path is also recovered. `HandleControlMenuInputEvent` routes menu-state 2 to `HandleControlMenuBrowseInput` and state 3 to `HandleControlMenuEditInput`. Browse-state code at `0x8077AD20..0x8077AD44` reads the current selection position from `0x800066B0 + group*9 + slot`, places it in `DAT_80002B2B`, and switches the UI into edit state 3. The edit commit at `0x8077B244..0x8077B270` reads descriptor byte `+0x0B` as the state-slot index, writes the edited position to both `DAT_80006810[stateIndex]` and the runtime selection table, then calls `ApplyCurrentControlSelection` (`0x80777578`) followed by `SaveCurrentControlSelection` (`0x807774EC`).

For descriptor type 3, `ApplyCurrentControlSelection` loads the control ID and selected option ID from the descriptor and calls `DispatchControlOption(controlId, optionId, 1)`. Therefore AUDIO OUT commits dispatch `0x71` with `0x12`, `0x75`, or `0x77` directly into `ApplySpdifOutputOption` with side effects enabled. `SaveCurrentControlSelection` persists the state byte through the generic NVRAM/config writer, while `SaveAllControlSelections` (`0x8077C0D0`) persists the full `0x41`-byte selection blob and its checksum path. This completes the static OFF/RAW/PCM getter/setter/persistence contract; hardware-observed S/PDIF behavior is still a separate acceptance level.


AP1 contains `SPDIF/OFF`, `SPDIF/RAW`, `SPDIF/PCM`, `SPDIF IN`, audio setup/output, AC3, DTS, PCM and USB/SD strings. Prefer stable file offsets until the address model is repaired:

| Anchor | AP1 file offset | Old Ghidra listing address, NOT validated runtime address |
|---|---|---|
| SPDIF/OFF | `0x5EDC8` | `0x806D9DC8` |
| SPDIF/RAW | `0x5F0AC` | `0x806DA0AC` |
| SPDIF/PCM | `0x5F0B8` | `0x806DA0B8` |
| SPDIF IN | `0x8FCA0` | `0x8070ACA0` |

Earlier work also recorded a status pool at old listing `0x8070AC00..0x8070AD07` containing DTS/PCM/AC3/no-signal and DVD/SPDIF/TUNER/AUXIN/MIC/USB labels. These are static firmware anchors, not PCB-routing evidence.

### S/PDIF input selection contract

AP1 contains a separate external-input subsource selector at `0x800032FA` (`gp+0x7FA`). Corrected instruction flow in the status/source display path at `0x8071E428..0x8071E4EC` proves:
- selector `1` enters the AUX branch and displays `AUXIN` (`0x8070B4D4`), with a related 2CH->2.1CH / 2CH->5.1CH status line;
- selector `2` displays `SPDIF IN` (`0x8070B4A0`);
- the other branch displays `TUNER` (`0x8070B4AC`).

`ToggleTunerSpdifInput` at `0x806FB920` is the concrete static setter: after its common setup helper it reads `0x800032FA` and toggles exactly `0 -> 2` or nonzero -> `0`, while updating source-state byte `0x800032A5`. This establishes a TUNER <-> S/PDIF input-selection path. `FUN_806FED18` additionally writes selector `1` or `2` from a broader external-input transition path; its complete higher-level contract is not yet named.

The higher source dispatcher uses `gp+0x7A5 = 0x800032A5` as an index `1..9` into the handler table at `0x8070B4E0`. Table entry 1 is confirmed as USB because its handler reaches the `USB` string at `0x8070B504`. The remaining source-handler mapping is still being resolved. These findings identify firmware source state and control; they do not establish the physical TOSLINK/coax routing on the PCB.

### Audio-state, volume and USB media behavior — 2026-09-22

Target-instruction checks now show that `gp+0x7A5 = 0x800032A5` is a source/media **state-machine state**, not a simple one-value-per-source enum. The 9-entry table at `0x8070B4E0` dispatches states 1..9 using `state-1`; states 6 and 8 share the common path. USB activation uses multiple states rather than one fixed source value.

The external-input transition action begins at raw entry `0x806FED0C`. It compares current mode code `gp+0x12B` with previous code `gp+0x12C`. Mode `3` selects AUX (`gp+0x7FA=1`, state `0x0B`); modes `0..2` select the S/PDIF-input path (`gp+0x7FA=2`, state `0x0D`). `PollExternalInputModeCode @ 0x8071DAC8` validates the current code to range 0..3. Ghidra currently splits the logical action around `0x806FED18`; raw fallthrough is authoritative.

Master volume and mute are a separate runtime-control route rather than ordinary setup-menu descriptors. `master_volume_level = gp+0x832 = 0x80003332`; `master_mute_flag = gp+0x7B5 = 0x800032B5`. `SetMasterVolumeLevel @ 0x8070129C` forwards action ID 2 into the common audio-action dispatcher, which reaches `ApplyMasterVolumeHardwareState @ 0x806FFBBC`. Mute is a separate flag, not merely volume zero: `ToggleMasterMute` sets/clears the flag, while unmute and several resume/reinit routes reapply `mute ? 0 : master_volume_level`. The hardware apply path indexes runtime table `0x88012CA0[level]`; exact level-to-coefficient bytes remain open because that runtime table is not mapped as readable memory in the canonical project. Persistence of `master_volume_level` is also not yet closed.

The decoder audio-status block is 16 bytes at `0x800022E4`. `UpdateDecoderAudioStatus @ 0x8070059C` extracts the decoder type from bits 2:0 of the decoder/hardware word and updates that block; `CopyDecoderAudioStatus @ 0x80700558` copies it to callers; `RenderDecoderAudioStatus @ 0x8071E008` renders it. Instruction-backed type mapping is:
- type `0` -> PCM;
- type `1` -> AC3;
- type `2/3` -> DTS;
- type `>=4` -> NO SIGNAL.

Codec changes feed the global decoder state `gp+0x698 = 0x80003198` through `SetAudioDecoderState`, `ReapplyAudioDecoderState`, and `ApplyAudioDecoderState`. Confirmed transitions are PCM type 0 -> state `0x8000`, AC3 type 1 -> `0x10000`, DTS type 2/3 -> `0x20000`; no-signal also falls back to baseline `0x8000` while forcing effective volume zero/status reset. State `0x4000` is independently tied to the WMA route because its profile action `0x807026F0` directly calls `InitializeWmaModule @ 0x8073F000`. Other states including `0x10`, `0x100`, `0x200`, `0x2000`, `0x40000` and `0x04000000` remain behaviorally distinct but are not all assigned codec names yet.

The USB/removable-media path is now separated into controller, context and source-state layers:
- `PollUsbControllerPresence` polls/reset-handles MMIO `0xBC0202A0` presence bits;
- `InitializeUsbDeviceContext` creates the active USB device context and handles controller subtype state from `0xBC0202A8`;
- `CreateMediaChildContexts` / `ReleaseMediaChildContexts` maintain child media contexts; unsupported hub handling prints `[Hubs Not Supported]`;
- primary context `0x80002E24` is selected by `SelectPrimaryMediaContext`;
- `ProbeUsbMediaUnits` is the sole lower-level probe used by `CheckUsbMediaDeviceReady` and includes an `APPLE` signature special case;
- `ProcessUsbMediaDetection` and `NormalizeUsbMediaState` normalize device/media state into `gp+0x82D`; bit 0 is the instruction-backed USB-vs-SD discriminator used by `RenderUsbSdMediaStatus`;
- `HandleUsbMediaRuntimeState` reports `[NO USB]` or `[BYTE/SECTOR >2048]` on failure and enters `HandleUsbMediaActivation` on success;
- `InitializeUsbMediaRoute` installs media callback `0x8075A850` in `gp+0x6DC` and sets state 7;
- `HandleMediaStreamCallbackState` is the state-7 action that executes `gp+0x6DC` through `jalr` and may transition onward to state 9.

Callback `0x8075A850` lives in `cdrom.bin` and is a shared media-stream initialization action rather than proven USB-exclusive behavior. Its raw path reaches `ReapplyAudioDecoderState` under one media-context condition, providing a concrete bridge from media initialization into the common audio decoder state. The lower USB transport layer is separate: `ProgramUsbHostTransfer @ 0x806A9AA8` programs `0xBC0201xx/0xBC0202xx` transaction registers and should not be conflated with media/source activation.

### Audio-core findings retained with address caveats

CDROM `0x8074C800`, previously named `ApplyCdromAudioModeFromSubtype`, maps a byte subtype as `0 -> 2`, `1..5 -> 1`, `6..10 -> 2`, `>=11 -> 4`. Its encoded calls are `0x80701A44` and conditionally `0x807017A8`. It reads `gp+0x774 = 0x80003274`, first as a byte and later as a halfword; the exact storage contract should be retained rather than simplified silently.

Earlier AP1 notes at old listing `0x807012C8` record writes to `gp+0x76C` and `gp+0x774`, modes `1/2/4/0x1000/0x2000/0x4000`, and MMIO-field values `0x600/0x700/0x800/0x300/0x400/0x500`. Old listing `0x806FFD9C` records a classifier/update path with values `1/2/4/0x40`. Preserve these as code anchors, not confirmed function entries: the AP1 base issue splits at least one routine incorrectly. The full status-string-to-mode chain and exact AC3/DTS/PCM numeric mapping remain unproven.

### CDROM classifier and packed-stream initializer

`DetectCdromStreamType` at `0x8074C868` contains the repeated `0x0B77` syncword/equal-spacing branch returning `0xAC3`; the other two signatures return `1` or `2`, and failure returns `-1`.

`InitializeCdromPackedStream` at `0x8074CB2C` is now named and commented in Ghidra. It clears the packing state, then normally invokes the classifier through the raw JAL at `0x8074CB7C`. A context word `*( *(uint32_t*)0x8000343C + 0x284 ) == 0x01050B44` bypasses the scan and selects result `1`; that context-field meaning is unknown.

| Classifier result | Stored byte at `0x80003718` | Action |
|---|---:|---|
| `1` | 1 | Set flag `0x80003719`; signature table `0x80002D64`; call `0x8074CEB8`, then converter `0x8074D538` |
| `2` | 2 | Set flag `0x8000371A`; signature table `0x80002D60`; call `0x8074CEB8`, then converter `0x8074D030` |
| `-1` | 0 | Call `0x8074CD90` |
| `0xAC3` | 3 | Call `0x8074CD90` |

The initializer returns the original classifier result, not the byte mode. Instruction proof includes the comparison at `0x8074CBBC..0x8074CBC4`, store at `0x8074CBE4`, failure store at `0x8074CBF8`, and dispatch calls at `0x8074CC28/CC30/CC50/CC58`.

The two converters show different word/bit packing behavior. Do not assign them DTS format names without signature-table or equivalent target proof. This CDROM classifier state is not automatically the audio-core enum, S/PDIF receiver state, or the inter-chip protocol.

The created Ghidra type `CdromPackedStreamState` is a 24-byte working layout for the state beginning at `0x80003704`: four-byte shift/count fields at offsets 0/4, four carry bytes at 8..11, four-byte cursor/count fields at 12/16, and mode/signature-A/signature-B/sync-loss bytes at 20..23. It has 12 fields; read-back confirmed size and offsets. Six labels identify the state, mode, flags and signature tables. The type is not an original source declaration and has not been applied over fabricated RAM bytes.


### Current USB/SCSI and audio behavior contracts — 2026-09-22

The latest behavior pass closes several implementation-level contracts that are useful independently of the broader project status. The full handoff and current coverage are in `docs/reverse-status.md`.

#### USB Mass Storage implementation

USB child class `0x08` is confirmed as Mass Storage and class `0x09` as Hub. The class-8 path owns the primary SCSI/MSC context at `0x80002E24`; the class-9 path uses the separate hub context `0x80002E2C`.

The SCSI command layer is now explicit:
- INQUIRY `0x12`;
- TEST UNIT READY `0x00`;
- REQUEST SENSE `0x03`;
- READ CAPACITY(10) `0x25`;
- READ(10) `0x28`;
- WRITE(10) `0x2A`.

`ExecuteUsbMassStorageScsiCommand` owns command/data/status sequencing. CBW/CSW construction and validation are split into named actions, and the CSW signature `0x53425355` plus tag matching are checked. READ/WRITE requests are clamped to the reported medium boundary; READ retries up to four attempts and WRITE up to three.

`ReadUsbScsiSense` maps standard sense keys into firmware status codes. In particular, NOT READY key 2 distinguishes ASC `0x04`, `0x06`, `0x08/0x54`, and `0x3A` (medium not present), while UNIT ATTENTION key 6 recognizes `ASC/ASCQ 0x28/0x00` as the media-change/ready-transition case.

#### WAVE codec routing

`HandleStreamTypeDecoderConfig` reads the first 16-bit `WAVEFORMATEX.wFormatTag` field. Confirmed tags and routes are:
- `0x0001` PCM -> state `0x10`, generic service mode `0x40`;
- `0x0002` MS ADPCM -> state `0x04000000`, legacy WAVE service path;
- `0x0006` A-law -> same legacy route;
- `0x0007` mu-law -> same legacy route;
- `0x0011` IMA/DVI ADPCM -> state `0x10`, generic service mode `0x80`;
- `0x0050` MPEG-1 audio -> state `0x100`;
- `0x0055` MP3 -> state `0x100`;
- `0x0161` WMA Standard -> state `0x4000`.

The legacy WAVE route beginning at `0x80702004` writes secondary registers `0x40/0x41/0x43/0x48` and starts the configured pipeline. The WMA route writes `0x40..0x49`, then uses backend commit/delay command `0x50`, then starts the same pipeline.

A separate pre-codec action at `0x807019BC` classifies sample-rate families before codec dispatch. Nominal 8/16/32-kHz bands select audio-format mode 1; other rates, including explicit bands around 11.025/22.05 kHz, select mode 2.

#### Decoder state versus service profile

Keep these layers separate:
- decoder/hardware status states: PCM `0x8000`, AC3 `0x10000`, DTS `0x20000`;
- packed-media states: classifier `0xAC3 -> 0x200`, positive non-AC3 packed signatures `1/2 -> 0x2000`;
- WAVE/service states: e.g. `0x10`, `0x100`, `0x4000`, `0x04000000`;
- audio-service format profiles committed by `CommitAudioFormatMode`.

`ConfigureSelectedMediaStreamAudio` is the confirmed selected-stream bridge into the audio path: it derives stream fields, calls `SetAudioDecoderState`, applies the decoder output profile, commits the audio-format mode, and passes stream-header-derived parameters into the secondary audio service. `StartConfiguredAudioPipeline` is the common start/apply action and conditionally restores effective master volume.

#### Hardware audio command layer

`DispatchAudioHardwareAction` is the central hardware-command dispatcher for action IDs `0..0x1A`. Confirmed user-facing associations include:
- action 1: DOWNMIX;
- action 2: master volume;
- action 3: KEY;
- action 7: S/PDIF/output mode;
- action `0x17`: packed speaker topology.

`ApplySpeakerConfiguration` builds the topology from FRONT/CENTER/REAR/SUB state and sends command family `0x2300 | topology`.

Descriptor-backed audio groups are now decoded:
- AUDIO SETUP: AUDIO OUT, DOWN SAMPLE, GM5, KEY;
- SPEAKER SETUP: DOWNMIX, SUBWOOFER, CENTER DELAY, REAR DELAY, FRONT, CENTER, REAR;
- DIGITAL SETUP: OP MODE, DYNAMIC RANGE, DUAL MONO.

Master volume and mute are not ordinary setup descriptors. Their confirmed runtime rule remains `effective_volume = mute ? 0 : master_volume_level`. The VOL+/VOL- and mute-toggle routes contain no direct save/NVRAM action. The shared runtime gain table at `0x88012CA0` is read by several audio command families; no writer for that table exists in the currently loaded modules.

## STK rev-8203R container and repack contract

The target-authoritative tool is now identified exactly as **STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe**, SHA-256 `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89`, size 1,057,792 bytes. It is imported separately in the canonical analysis project.

The older program named simply `/tools/stk.exe` is a **different STK revision**. Earlier construction notes derived from that executable (including its 0x80-byte transform and addresses around `0x00401B56/0x00401ED2`) are not authoritative for this target and are superseded by this section.

### Checksums and physical container extent

`FUN_00401BF6` in rev-8203R is the additive checksum primitive. It sums unsigned little-endian 16-bit words into a wrapping 32-bit accumulator; an odd final byte is ignored.

The physical-open path is:

`FUN_00402E0A`
-> outer checksum/extent recovery
-> `FUN_00402DAA`
-> transform decode
-> `FUN_00402D16`
-> inner checksum/logical-end recovery
-> `FUN_00402A88`
-> loader/layout parsing.

For the preserved 1 MiB target dump:
- outer stored checksum at `+0x20`: `0x02A3F129`;
- effective encoded firmware-container extent: **`0xBC800`**;
- mode after signature detection: **4**;
- inner stored checksum at decoded `+0x40`: `0xD331A8F6`;
- decoded logical extent: **`0xBC508`**.

Both checksums were reproduced against the preserved target bytes in the correct stage/order.

Bytes after `0xBC800` remain physically present in the 1 MiB SPI image and contain non-`0xFF` data. They are **outside the firmware-container outer checksum**. A full-flash builder must preserve this post-container region unless/until its ownership is separately recovered.

### rev-8203R transform modes

`FUN_00401FC8` selects the transform mode before parsing:
- mode 1: `dword +0x70 == 0`, no transform;
- mode 2: `dword +0x68 == 0xA5A5A5A5`;
- mode 3: `dword +0x70 == 0xF5F5F5F5`;
- mode 4: `dword +0x70 == 0xB1B1B1B1`.

The preserved target has `+0x70 = 0xB1B1B1B1`, so it is unequivocally **mode 4**.

Transform implementations:
- mode 2, `FUN_00401E8C`: 0x20-byte blocks beginning at `+0x40`, XOR `0xA5`, swap the two 4-byte halves of every 8-byte group, then swap the two 16-byte halves;
- mode 3, `FUN_00401F1E`: repeating 0x80-byte XOR key at STK `0x004F2200`, with the first `0x28` bytes restored unchanged;
- mode 4, `FUN_00401F70`: repeating 0x200-byte XOR key at STK `0x004F2000`, with the first `0x28` bytes restored unchanged.

The corresponding save finalizer is `FUN_004030DE`.

### Loader/header and module-offset table

`FUN_00402A88` derives layout metadata from MIPS loader code. On the target:
- decoded loader/header length: **`0x14260`** (82,528 bytes);
- module-offset table length: **`0x6C`** (108 bytes);
- table entries: **27 dwords**;
- packed payload start: **`0x142CC`**.

The first `0x14260` decoded bytes match the repository's `rom12.bin` **byte-for-byte**. Therefore `rom12.bin` is the decoded loader/header image, not an ordinary compressed module payload.

The 27-entry offset table describes payload starts. STK's normal module UI/parser exposes only the first 17 entries:
0 dvd, 1 mpeg, 2 jpeg, 3 ap1, 4 cdrom, 5 iop, 6 iop_rst, 7 drv_other, 8 srvdsp, 9 ap2, 10 ap3, 11 free, 12 rom3, 13 mp4, 14 wma, 15 dvb, 16 dvd_ipod.

Entries 17..26 are hidden/reserved payload slots in this target. All ten currently contain the same empty packed stream.

The previously documented phrase "18 identical module slots" is therefore misleading. The preserved extraction directory contains 18 files because `rom12.bin` is also exported, but the decoded layout is **rom12/header + a 27-entry payload table**, of which STK exposes 17 ordinary payload slots.

### Module compression contract

Extraction is performed by `FUN_00402938`; ordinary payloads are inflated by `FUN_0040289A`. Save/repack uses `FUN_00403218` and compressor `FUN_00402FEE`.

Ordinary payload compression is:
- DEFLATE level 9;
- method 8;
- `windowBits=-15` (raw DEFLATE);
- `memLevel=8`;
- strategy 4 / `Z_FIXED`.

There is **no CRC32/ISIZE trailer** after a non-empty module. Each ordinary payload is only the raw DEFLATE stream. The earlier trailer interpretation came from analysis of the wrong STK revision and is withdrawn.

For an empty ordinary module, rev-8203R has an explicit special case and emits exactly 10 bytes:

`03 00 00 00 00 00 00 00 00 00`.

The first two bytes are a valid empty raw-DEFLATE stream; the remaining eight zero bytes are part of the vendor empty-module representation, not a generic CRC/ISIZE trailer.

Payload slot `0x0C` is special: it bypasses ordinary DEFLATE packing and is copied raw. It is empty in the preserved target, so its two neighboring offsets are equal.

The vendor tool contains zlib **1.2.3**. Recompressing non-empty modules with native zlib 1.3.1 and the same parameters produces valid but generally different DEFLATE byte streams and often slightly smaller packed sizes. Empty modules remain byte-identical. Therefore:
- unchanged modules should be preserved in their original packed form;
- a changed module can be repacked with a current compatible raw-DEFLATE implementation;
- byte-identical recompression of changed non-empty modules requires reproducing zlib 1.2.3 behavior, but byte identity is not required by the recovered container parser.

### Repack strategy and validation

The stock vendor image contains encoded bytes between decoded logical end `0xBC508` and container end `0xBC800`, plus a separate physical SPI region after `0xBC800`. Both are preserved unless an intentional change requires rewriting the meaningful prefix.

The target-specific rebuild strategy is:
1. preserve the decoded `rom12` loader/header unless intentionally changing it;
2. preserve unchanged packed modules byte-for-byte;
3. repack only intentionally replaced visible modules;
4. preserve all hidden/reserved payload slots;
5. recompute all 27 offsets and the decoded inner checksum;
6. re-encode the meaningful mode-4 prefix;
7. preserve untouched stock encoded suffix bytes;
8. recompute the outer checksum over the effective encoded extent;
9. preserve the physical SPI region after the recovered container extent.

`tools/sunplus_container.py` implements this rev-8203R contract with `inspect`, `roundtrip`, and `repack --replace NAME=FILE`. It validates every one of the 27 payloads after reopening a rebuilt image and refuses a repack that would extend into the currently-unclassified post-container flash region.

Two different validation levels have now been demonstrated:

- **No-change reconstruction:** reusing the original 27 packed payload streams reproduces the complete preserved 1 MiB flash image byte-for-byte. `diff_count=0`; rebuilt SHA-256 is the canonical `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`. This closes the container/table/transform/checksum reconstruction for the stock image.
- **Changed-module structural reconstruction:** rebuilding with zlib 1.3.1 reopens successfully and every unpacked payload matches the expected bytes. The compressed streams need not be vendor-byte-identical because the original tool uses zlib 1.2.3.

### Independent MIPS build path

The extracted CPU modules are flat MIPS32 little-endian load images with established bases:
- `ap1.bin @ 0x8067B800`;
- `wma.bin @ 0x8073F000`;
- `cdrom.bin @ 0x8074C800`;
- `drv_other.bin @ 0x80775800`.

A normal LLVM MIPS toolchain is sufficient for new freestanding code. The validated compile model is MIPS32 little-endian, o32, soft-float, no PIC/no ABICALLS, and `-G0` to avoid depending on the original small-data `$gp` layout.

`tools/mips-inject/` now uses an **in-place** behavior-preserving compiler/ABI probe for the first hardware acceptance test:
- the stock `ApplySurroundModeIndex @ 0x80702D0C` wrapper is exactly 44 bytes;
- an independently compiled C implementation is linked directly at `0x80702D0C`;
- it implements the same contract, `DispatchAudioHardwareAction(5, index & 0xff, 0)`;
- `patch_ap1.py` verifies the exact original 44 bytes and replaces them in place;
- AP1 remains exactly `0xA70A0` bytes, so the first compiler/ABI test does not change the loader range or runtime memory layout.

This is the preferred first hardware probe because it isolates the variables to compiler ABI + module replacement + container repack + execution.

A separate AP1-extension experiment was also statically reconstructed successfully before the in-place probe was adopted. That experiment extended AP1 through `0x8072302C`; its modified AP1 reopened exactly and all other 26 payloads remained unchanged after repack. The extension result is retained as evidence for later larger features, not as the first hardware test.

The currently established static/tool chain is:

`C -> MIPS32-LE object -> fixed-address raw code -> in-place AP1 replacement -> Sunplus repack -> reopen/extract validation`.

It does **not** establish successful boot or hardware behavior. Those remain hardware-acceptance gates.


### AP1 loader-size proof

The decoded `rom12.bin` loader has now been checked directly at runtime base `0x88000000`.

`LoadPackedModuleToAddress @ 0x88000D34` takes a module slot in `a0` and a destination address in `a1`. It reads the slot's packed-payload offset from the 27-entry table at `0x88014260`, adds payload base `0x880142CC`, and passes the resulting packed-stream pointer together with the unchanged destination address into the raw-DEFLATE loader.

`LoadModuleSlot @ 0x88000D9C` supplies the fixed destination addresses. Confirmed mappings relevant to the active CPU modules are:
- slot 3 -> `0x8067B800` (AP1);
- slot 4 -> `0x8074C800` (CDROM);
- slot 7 -> `0x80775800` (drv_other);
- slot 14 -> `0x8073F000` (WMA).

The actual inflater is size-driven rather than old-end-address-driven. `InflateRawDeflateStream @ 0x88001D9C` begins with an output allowance of `0x7FFFFFFF`, advances the destination as bytes are emitted, and stops on the DEFLATE final-block marker. `0x88001E8C` writes literals/back-references to `destination + bytes_written` and only checks against the remaining output allowance; no hard-coded AP1 end address is present in this path.

Therefore the loader will emit an enlarged AP1 according to the rebuilt DEFLATE stream, provided that the destination range remains free.

For the current compiler probe:
- stock AP1 end: `0x807228A0`;
- enlarged AP1 end: `0x8072302C`;
- next confirmed fixed module destination: WMA at `0x8073F000`;
- remaining gap after the enlarged AP1: `0x1BFD4` bytes.

No other fixed module destination selected by the loader lies inside `0x8072302C..0x8073EFFF`. This closes the **loader-size / fixed-module-overlap** part of the AP1-extension gate. It does **not** yet prove that no dynamic runtime allocation, scratch buffer, overlay, or later copy uses that address interval; that remains the next static/runtime-memory check before hardware execution.


### Startup module set and removal boundary

The decoded ROM loader's main initialization action is now identified as
`InitializeRuntimeAndLoadCoreModules @ 0x88000890`.

Its startup module requests are:

- slot 7 -> `drv_other` (non-empty);
- slot 3 -> `ap1` (non-empty);
- slot 11 -> `free` (empty in the preserved image);
- slot 4 -> `cdrom` (non-empty);
- later slot 1 -> `mpeg` (empty);
- later slot 9 -> `ap2` (empty).

Therefore the stock boot path only adds one substantial CPU payload beyond
AP1/drv_other at startup: `cdrom.bin`. The nominal DVD/MPEG/AP2 calls in this
target are currently empty payload slots.

However, `cdrom.bin` is not removable from the stock AP1 by merely zeroing its
payload. A raw-instruction scan of the preserved AP1 finds **113 direct JAL
instructions** into the CDROM address range `0x8074C800..0x8075BF1F`, targeting
**42 distinct CDROM entry points**. Many callers are in the recovered
media/USB/navigation paths, but the dependency is structurally broad.

This changes the minimization strategy:

1. do not try to shrink the stock application by deleting CDROM first;
2. keep the known-good loader/runtime/DSP modules while validating independent
   C execution;
3. build a new minimal audio control plane that calls the recovered AP1/runtime
   audio ABI;
4. bypass or replace legacy media/UI dispatch paths;
5. only then remove `cdrom.bin` after no remaining live route requires its
   entry points.

The empty DVD/MPEG/AP2/etc. payload slots are not the main source of product
complexity in this image. Most legacy DVD/UI/media behavior resides in AP1 and
the non-empty CDROM module.

## Secondary BR23 / AC695N side

The board's secondary package is marked `AK24BP24230`. The UART log proves that running firmware contains AC695N/BR23 soundbox SDK paths and runtime messages, but the exact public SKU is still unresolved.

BR23 / AC695N uses JieLi's `pi32v2` architecture, not MIPS and not SCORE7.

### Public references / pinout

Working public pinout candidate for the secondary LQFP48 device:

- AC6951C datasheet V1.3 mirror: https://opendevices.ru/wp-content/uploads/2021/08/AC6951C-Datasheet-V1.3.pdf
- alternate rendered datasheet: https://manuals.plus/m/f01af517c489b4b9a7162705aa1868219f1b5cd871d130e08f0c0d601858c359

For AC6951C LQFP48:
- pin 23 = `USBDM`
- pin 24 = `USBDP`
- pin 25 = `PA10` (also has `SPDIF_IN_B`)
- pin 26 = `PA9` (also has `SPDIF_IN_A`)

The physical package marking on this board is `AK24BP24230`; the exact mapping of that marking to AC6951C is still unproven. Use pins 23/24 only after continuity/visual package orientation confirms that this board's secondary device matches the AC6951C LQFP48 pinout.

Boot/dump references:

- jl-uboot-tool: https://github.com/kagaimiq/jl-uboot-tool
- enter UBOOT / USB_KEY: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/how-to-enter-uboot.md
- UBOOT model: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/what-is-uboot.md
- JieLi architecture/chip notes: https://github.com/kagaimiq/jielie
- pi32v2 Ghidra processor: https://github.com/kagaimiq/ghidra-jieli

### Read-only dump plan

The next major acquisition task is to preserve this firmware before doing deeper two-chip reverse work.

1. Identify the secondary chip's own USB D+/D- route or accessible test pads. Do not reuse the four-pad SPHE USB footprint by assumption.
2. Confirm the chip enters BR23/AC695N-family Boot ROM / UBOOT, or determine the exact hardware action needed to reach ROM download mode.
3. Use a read-only BR23-capable dumper path. The open-source `jl-uboot-tool` explicitly lists BR23 / AC695N/AC635N as working and can read flash through its RAM loader.
4. Query the online flash/device ID first and derive the real flash size. The runtime log's `disk capacity 1024 KB` is a strong clue, not the dump-size authority.
5. Read the full flash at least twice, compare byte-for-byte and record SHA-256.
6. Only after verified preservation should any write/erase/update experiment be attempted.
7. Store the verified dump in this repository under `firmware/` using the proven chip family/part name.

### Safe first-session sequence

After identifying the secondary controller's own USB D+/D- pair:

1. power the board in the safest known configuration and share ground with the USB host;
2. do not feed an unknown USB VBUS rail into the board until its power topology is mapped;
3. enter BR23 ROM `UBOOT1.00` using the documented `USB_KEY` method or another non-destructive ROM-entry path;
4. start `jluboottool.py` and record the detected BR23/series and flash/device information;
5. determine flash size from the actual flash ID before selecting a dump length;
6. use only the `read <address> <length> <file>` command for the first session;
7. read the whole flash twice and compare the two files byte-for-byte and by SHA-256;
8. do not use `write`, `erase` or `erasechip` until a verified dump and recovery path exist.

The tool's own documentation marks BR23 / AC695N/AC635N as working and documents `read <address> <length> <file>` as the flash-dump command.

### Static-analysis path

After the dump exists:

- use a pi32v2 Ghidra processor implementation such as the open-source `ghidra-jieli` module;
- cross-check instruction decoding against the JieLi toolchain/objdump;
- use available AC695N/BR23 SDK source as a semantic oracle;
- recover board configuration, UART/service behavior, ALINK/I2S/SPDIF use, volume state and the SPHE inter-chip protocol.

### Current runtime anchors

`evidence/ac695n-boot-excerpt.log` is a curated excerpt from the UART output of the secondary-controller side.

It contains:
- `AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS`
- BR23 / `board_ac695x_demo`
- `jl_soundbox_lihui`
- `audio_enc_init`
- `audio_dec_init`
- `audio_dac_init`
- `ALINK_SR = 44100`
- `spdif_dec_start`
- max/default volume configuration and `VOL_SAVE`

This strongly ties the secondary side to JieLi AC695N/BR23 software, but the exact public SKU behind `AK24BP24230`, its internal-flash dump path and the inter-chip protocol remain open.

## Firmware-control acceptance

Firmware work is not complete merely because dumps decompile or a checksum helper has been named.

We need to prove repeatable extraction/dump, coherent address and call models, repeatable packing/image construction, integrity rules, a safe flash/update method, rollback/recovery, and one intentional modification that survives reboot and produces the expected hardware behavior.

Only after that should the project implement new product behavior.
